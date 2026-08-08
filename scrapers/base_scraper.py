"""
Base scraper class for the Doc Apocalypse.
All scrapers inherit from this. It handles:
  - Rate limiting
  - Retries with exponential backoff
  - Progress logging
  - Content deduplication via SHA256
  - Compression on write
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import zstandard as zstd

logger = logging.getLogger("doc-apocalypse")


class ScraperResult:
    """Represents a scraped document."""
    
    def __init__(self, source: str, url: str, content: str, content_type: str = "text/markdown",
                 metadata: Optional[dict] = None):
        self.source = source
        self.url = url
        self.content = content
        self.content_type = content_type
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "url": self.url,
            "content_type": self.content_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "sha256": self.sha256,
            "content_length": len(self.content),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class BaseScraper(ABC):
    """Abstract base scraper with rate limiting, retries, and storage."""
    
    def __init__(self, name: str, data_dir: str = "/home/natalie/projects/doc-apocalypse/data",
                 rate_limit: float = 1.0, max_retries: int = 3):
        self.name = name
        self.data_dir = Path(data_dir) / name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit  # seconds between requests
        self.max_retries = max_retries
        self._last_request = 0.0
        self._seen_hashes = set()
        self._stats = {"scraped": 0, "skipped": 0, "errors": 0, "bytes": 0}
        
        # Load seen hashes from previous runs
        self._load_seen()
    
    def _load_seen(self):
        hash_file = self.data_dir / ".seen_hashes.json"
        if hash_file.exists():
            try:
                with open(hash_file) as f:
                    self._seen_hashes = set(json.load(f))
                logger.info(f"[{self.name}] Loaded {len(self._seen_hashes)} seen hashes")
            except Exception as e:
                logger.warning(f"[{self.name}] Failed to load seen hashes: {e}")
    
    def _save_seen(self):
        hash_file = self.data_dir / ".seen_hashes.json"
        with open(hash_file, "w") as f:
            json.dump(list(self._seen_hashes), f)
    
    async def _rate_limit_wait(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request = time.time()
    
    async def fetch(self, session: aiohttp.ClientSession, url: str, 
                    headers: Optional[dict] = None) -> Optional[str]:
        """Fetch a URL with retry logic."""
        for attempt in range(self.max_retries):
            try:
                await self._rate_limit_wait()
                async with session.get(url, headers=headers, 
                                       timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", "60"))
                        logger.warning(f"[{self.name}] Rate limited on {url}, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    if resp.status == 404:
                        logger.debug(f"[{self.name}] 404: {url}")
                        return None
                    if resp.status != 200:
                        logger.warning(f"[{self.name}] HTTP {resp.status}: {url}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return None
                    text = await resp.text()
                    logger.info(f"[{self.name}] Fetched ({len(text)} bytes): {url}")
                    return text
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"[{self.name}] Attempt {attempt+1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    self._stats["errors"] += 1
                    return None
        return None
    
    def save_document(self, result: ScraperResult) -> Path:
        """Save a document with dedup, compressed storage."""
        if result.sha256 in self._seen_hashes:
            self._stats["skipped"] += 1
            return None
        
        self._seen_hashes.add(result.sha256)
        
        # Create date-based subdirectory
        date_dir = self.data_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # Save as compressed JSON
        doc_path = date_dir / f"{result.sha256[:16]}.json.zst"
        
        doc_data = result.to_dict()
        doc_data["content"] = result.content
        
        cctx = zstd.ZstdCompressor(level=3)
        compressed = cctx.compress(json.dumps(doc_data, ensure_ascii=False).encode("utf-8"))
        
        with open(doc_path, "wb") as f:
            f.write(compressed)
        
        self._stats["scraped"] += 1
        self._stats["bytes"] += len(compressed)
        
        return doc_path
    
    @abstractmethod
    async def run(self):
        """Main entry point for the scraper."""
        pass
    
    def print_stats(self):
        """Print current stats."""
        logger.info(f"[{self.name}] Stats: {self._stats['scraped']} scraped, "
                    f"{self._stats['skipped']} skipped, {self._stats['errors']} errors, "
                    f"{self._stats['bytes'] / 1024 / 1024:.1f} MB stored")
    
    def save_stats(self):
        """Save stats to log file."""
        stats_file = self.data_dir / ".stats.json"
        with open(stats_file, "w") as f:
            json.dump(self._stats, f, indent=2)
