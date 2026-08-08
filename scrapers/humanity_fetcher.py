#!/usr/bin/env python3
"""
Humanity Archive Fetcher
Imports data from humanity_data.py and fetches all texts from Gutenberg.
Saves as Zstandard JSON with SHA256 dedup.
"""

import asyncio
import hashlib
import json
import logging
import time
import zstandard
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("humanity.fetcher")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/humanity")
OUTPUT.mkdir(parents=True, exist_ok=True)
seen_file = OUTPUT / ".seen_hashes.json"

seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))


def save(key, url, content, metadata=None):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    compressed = zstandard.ZstdCompressor(level=3).compress(
        json.dumps(doc, ensure_ascii=False).encode())
    d = OUTPUT / time.strftime("%Y-%m-%d")
    d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


def save_progress():
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


# Import data
import humanity_data

ALL_TEXTS = []
for category, items in humanity_data.ALL_SECTIONS:
    ALL_TEXTS.extend((category, key, name, url) for key, name, url in items)

total = len(ALL_TEXTS)


async def fetch_text(session, category, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        # Strip Gutenberg headers
                        for marker in [
                            "*** START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF THIS PROJECT GUTENBERG EBOOK",
                            "***START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl + 1:] if nl >= 0 else text[idx:]
                                break
                        for marker in [
                            "*** END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF THIS PROJECT GUTENBERG EBOOK",
                            "***END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        text = text.strip()
                        saved = save(key, url, text, {
                            "name": name, "category": category, "source": "gutenberg"
                        })
                        if saved:
                            logger.info(f"  ✅ {name[:70]}")
                        return True
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            logger.warning(f"  ❌ {name[:60]} — {type(e).__name__}")
    return False


async def main():
    logger.info(f"\n{'='*60}")
    logger.info(f"🧬 HUMANITY ARCHIVE: {total} texts across {len(humanity_data.ALL_SECTIONS)} sections")
    logger.info(f"{'='*60}\n")

    # Print sections
    for cat, items in humanity_data.ALL_SECTIONS:
        logger.info(f"  📚 {cat}: {len(items)} texts")

    logger.info(f"\nFetching...\n")

    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for category, key, name, url in ALL_TEXTS:
            tasks.append(fetch_text(session, category, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_progress()
                n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
                b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
                logger.info(f"   → {n} docs, {b/1024/1024:.1f} MB")
        if tasks:
            await asyncio.gather(*tasks)

    save_progress()

    n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
    b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
    logger.info(f"\n{'='*60}")
    logger.info(f"🧬 HUMANITY ARCHIVE COMPLETE")
    logger.info(f"   {n} docs, {b/1024/1024:.1f} MB")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
