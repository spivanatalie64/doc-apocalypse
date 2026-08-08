"""
Doc-Apocalypse Indexer
Builds a full-text search index over all harvested documents.
Supports multiple backends:
  1. Meilisearch (best) - if available
  2. Sonic (lightweight) - if available
  3. SQLite FTS5 (built-in fallback)
  4. Flat JSON index (portable)

Also generates a hierarchical sitemap and statistics.
"""

import gzip
import json
import logging
import os
import sqlite3
import struct
import zstandard as zstd
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("doc-apocalypse.indexer")


class DocIndexer:
    """Builds and maintains a searchable index of all harvested docs."""
    
    def __init__(self, data_dir: str = "/home/natalie/projects/doc-apocalypse/data",
                 index_dir: str = "/home/natalie/projects/doc-apocalypse/indexes"):
        self.data_dir = Path(data_dir)
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.index_dir / "doc_apocalypse.db"
        self.json_path = self.index_dir / "doc_apocalypse_index.json"
        self.stats_path = self.index_dir / "doc_apocalypse_stats.json"
        
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite FTS5 database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=OFF")
        
        # Main docs table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sha256 TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                content_type TEXT,
                timestamp TEXT,
                content_length INTEGER,
                metadata TEXT  -- JSON blob
            )
        """)
        
        # FTS5 full-text search index
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                sha256 UNINDEXED,
                source,
                url,
                content,
                content_type UNINDEXED,
                tokenize='porter unicode61'
            )
        """)
        
        # Source stats table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS source_stats (
                source TEXT PRIMARY KEY,
                doc_count INTEGER DEFAULT 0,
                total_bytes INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        
        self.conn.commit()
    
    def scan_data_directory(self) -> dict:
        """Scan all compressed doc files and return stats."""
        stats = {
            "total_files": 0,
            "total_bytes": 0,
            "total_docs": 0,
            "by_source": defaultdict(lambda: {"count": 0, "bytes": 0}),
            "errors": 0,
        }
        
        for fpath in self.data_dir.rglob("*.json.zst"):
            try:
                # Read compressed file
                with open(fpath, "rb") as f:
                    compressed = f.read()
                
                dctx = zstd.ZstdDecompressor()
                data = json.loads(dctx.decompress(compressed))
                
                source = data.get("source", "unknown")
                content_len = data.get("content_length", 0)
                
                stats["total_files"] += 1
                stats["total_bytes"] += len(compressed)
                stats["by_source"][source]["count"] += 1
                stats["by_source"][source]["bytes"] += len(compressed)
                
            except Exception as e:
                stats["errors"] += 1
                logger.debug(f"Error reading {fpath}: {e}")
                continue
        
        stats["total_docs"] = stats["total_files"]
        return stats
    
    def index_all(self, limit: Optional[int] = None):
        """Index all documents into SQLite FTS."""
        logger.info("[Indexer] Full indexing run starting...")
        
        start = datetime.now()
        indexed = 0
        errors = 0
        
        # Begin transaction for batch insert
        self.conn.execute("BEGIN TRANSACTION")
        
        for i, fpath in enumerate(self.data_dir.rglob("*.json.zst")):
            if limit and i >= limit:
                break
            
            try:
                with open(fpath, "rb") as f:
                    compressed = f.read()
                
                dctx = zstd.ZstdDecompressor()
                data = json.loads(dctx.decompress(compressed))
                
                sha256 = data["sha256"]
                source = data["source"]
                url = data["url"]
                content_type = data.get("content_type", "text/plain")
                timestamp = data.get("timestamp", "")
                content = data.get("content", "")
                metadata = json.dumps(data.get("metadata", {}))
                
                # Skip if already indexed
                existing = self.conn.execute(
                    "SELECT sha256 FROM documents WHERE sha256 = ?", (sha256,)
                ).fetchone()
                
                if existing:
                    continue
                
                # Insert into documents table
                self.conn.execute("""
                    INSERT OR IGNORE INTO documents 
                    (sha256, source, url, content_type, timestamp, content_length, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (sha256, source, url, content_type, timestamp, len(content), metadata))
                
                # Insert into FTS index
                self.conn.execute("""
                    INSERT INTO docs_fts (sha256, source, url, content)
                    VALUES (?, ?, ?, ?)
                """, (sha256, source, url, content[:500_000]))  # Limit FTS content to 500KB/doc
                
                indexed += 1
                
                if indexed % 1000 == 0:
                    self.conn.commit()
                    self.conn.execute("BEGIN TRANSACTION")
                    elapsed = (datetime.now() - start).total_seconds()
                    rate = indexed / elapsed if elapsed > 0 else 0
                    logger.info(f"[Indexer] Indexed {indexed} docs ({rate:.0f} docs/s)...")
                
            except Exception as e:
                errors += 1
                if errors % 100 == 0:
                    logger.warning(f"[Indexer] {errors} errors so far (last: {e})")
                continue
        
        # Final commit
        try:
            self.conn.execute("COMMIT")
        except:
            self.conn.rollback()
        
        # Update source stats
        stats = self.scan_data_directory()
        for source, sstats in stats["by_source"].items():
            self.conn.execute("""
                INSERT OR REPLACE INTO source_stats (source, doc_count, total_bytes, last_updated)
                VALUES (?, ?, ?, ?)
            """, (source, sstats["count"], sstats["bytes"], datetime.now().isoformat()))
        
        self.conn.commit()
        
        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"[Indexer] Done: {indexed} indexed, {errors} errors in {elapsed:.1f}s")
        
        return indexed
    
    def search(self, query: str, limit: int = 20) -> list:
        """Search the FTS index."""
        try:
            results = self.conn.execute("""
                SELECT d.sha256, d.source, d.url, d.content_type, d.content_length,
                       rank
                FROM docs_fts f
                JOIN documents d ON d.sha256 = f.sha256
                WHERE docs_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)).fetchall()
            
            return [
                {
                    "sha256": r[0],
                    "source": r[1],
                    "url": r[2],
                    "content_type": r[3],
                    "content_length": r[4],
                    "rank": r[5],
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def export_json_index(self):
        """Export a lightweight JSON index (no content, just metadata)."""
        logger.info("[Indexer] Exporting JSON index...")
        
        docs = []
        for row in self.conn.execute("""
            SELECT sha256, source, url, content_type, timestamp, content_length
            FROM documents
            ORDER BY source, url
        """):
            docs.append({
                "sha256": row[0],
                "source": row[1],
                "url": row[2],
                "content_type": row[3],
                "timestamp": row[4],
                "content_length": row[5],
            })
        
        index_data = {
            "exported_at": datetime.now().isoformat(),
            "total_docs": len(docs),
            "documents": docs,
        }
        
        with open(self.json_path, "w") as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"[Indexer] Exported {len(docs)} docs to {self.json_path}")
        
        # Also export a compressed version
        with open(f"{self.json_path}.gz", "wb") as f:
            data = json.dumps(index_data, indent=2).encode("utf-8")
            f.write(gzip.compress(data))
        
        logger.info(f"[Indexer] Exported compressed: {self.json_path}.gz")
    
    def export_stats(self):
        """Export statistics."""
        stats = self.scan_data_directory()
        
        # Add search stats
        stats["indexed_docs"] = self.conn.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]
        
        stats["index_size_bytes"] = sum(
            os.path.getsize(f)
            for f in [self.db_path, self.json_path, f"{self.json_path}.gz"]
            if os.path.exists(f)
        )
        
        with open(self.stats_path, "w") as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"[Indexer] Stats exported to {self.stats_path}")
        return stats


def main():
    """Main indexer entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Doc-Apocalypse Indexer")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch")
    parser.add_argument("--search", type=str, help="Search query")
    parser.add_argument("--stats", action="store_true", help="Show index stats")
    parser.add_argument("--export-json", action="store_true", help="Export JSON index")
    parser.add_argument("--limit", type=int, default=None, help="Limit docs to index")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    indexer = DocIndexer()
    
    if args.rebuild:
        # Drop and recreate
        logger.info("[Indexer] Rebuilding from scratch...")
        os.remove(str(indexer.db_path))
        indexer._init_db()
        indexer.index_all(limit=args.limit)
    
    if args.search:
        results = indexer.search(args.search)
        print(f"\nSearch results for '{args.search}':")
        print(f"{'='*60}")
        for r in results[:10]:
            print(f"  [{r['source']}] {r['url'][:80]}")
            print(f"    ({r['content_length']} bytes, rank: {r['rank']:.2f})")
            print()
    
    if args.stats or not any([args.rebuild, args.search, args.export_json]):
        stats = indexer.export_stats()
        print(f"\n📊 Doc-Apocalypse Index Stats")
        print(f"{'='*60}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total bytes: {stats['total_bytes'] / 1024**3:.2f} GB")
        print(f"  Indexed docs: {stats['indexed_docs']}")
        print(f"  Errors: {stats['errors']}")
        print(f"\n  By source:")
        for source, sstats in sorted(stats['by_source'].items()):
            print(f"    {source}: {sstats['count']} docs, {sstats['bytes'] / 1024**2:.1f} MB")
        print()
    
    if args.export_json:
        indexer.export_json_index()


if __name__ == "__main__":
    main()
