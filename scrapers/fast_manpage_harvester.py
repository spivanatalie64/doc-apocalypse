#!/usr/bin/env python3
"""
Fast Man Page Harvester
- Uses find to locate all man pages
- Parallel processing with multiprocessing
- Uses groff to render to text
- Dedup via SHA256
- Zstandard compressed output

Run: python fast_manpage_harvester.py [--parallel N] [--dry-run]
"""

import gzip
import hashlib
import json
import logging
import multiprocessing
import os
import subprocess
import sys
import time
import zstandard as zstd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("manpages.fast")


MAN_DIRS = [
    "/usr/share/man",
]


def find_all_man_pages() -> list:
    """Find all man page files across the system."""
    pages = []
    for man_dir in MAN_DIRS:
        if os.path.exists(man_dir):
            for root, dirs, files in os.walk(man_dir):
                for f in files:
                    if f.endswith(".gz"):
                        pages.append(os.path.join(root, f))
    return sorted(pages)


def get_man_page_name(path: str) -> str:
    """Extract the man page name (e.g., bash.1 from bash.1.gz)."""
    base = os.path.basename(path)
    if base.endswith(".gz"):
        base = base[:-3]
    return base


def get_package_for_man_page(path: str) -> str:
    """Get the package that owns a man page."""
    try:
        result = subprocess.run(
            ["pacman", "-Qo", path],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # "file.pm is owned by perl 5.38.2-1"
            import re
            match = re.match(r".+ is owned by (\S+)", result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    return "unknown"


def render_man_page_groff(man_path: str) -> tuple:
    """Render a man page to text using groff."""
    try:
        # Decompress
        with gzip.open(man_path, 'rt', errors='replace') as f:
            groff_source = f.read()
        
        # Render to text
        result = subprocess.run(
            ["groff", "-mandoc", "-Tutf8", "-P-c"],
            input=groff_source,
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode != 0 or not result.stdout:
            return None, None
        
        text = result.stdout
        # Strip ANSI
        import re
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1b\[[0-9;]*', '', text)
        
        # Also get HTML
        html_result = subprocess.run(
            ["groff", "-mandoc", "-Thtml"],
            input=groff_source,
            capture_output=True, text=True, timeout=30
        )
        html = html_result.stdout if html_result.returncode == 0 else None
        
        return text, html
    except Exception as e:
        logger.debug(f"Error rendering {man_path}: {e}")
        return None, None


def process_man_page(path: str) -> dict:
    """Process a single man page and return compressed data."""
    result = {"path": path, "success": False, "error": None}
    
    try:
        name = get_man_page_name(path)
        pkg = get_package_for_man_page(path)
        
        text, html = render_man_page_groff(path)
        if not text:
            return result
        
        sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        
        doc_data = {
            "sha256": sha256,
            "source": f"manpages/{pkg}",
            "url": f"man:{name}",
            "content_type": "text/plain",
            "content": text,
            "content_length": len(text),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            "metadata": {
                "package": pkg,
                "name": name,
                "path": path,
                "format": "text"
            }
        }
        
        # Compress
        cctx = zstd.ZstdCompressor(level=3)
        compressed = cctx.compress(json.dumps(doc_data, ensure_ascii=False).encode("utf-8"))
        
        result.update({
            "success": True,
            "sha256": sha256,
            "compressed_data": compressed,
            "compressed_size": len(compressed),
            "text_len": len(text),
            "package": pkg,
            "name": name,
        })
        
        # Also save HTML if available
        if html:
            html_data = doc_data.copy()
            html_data.update({
                "url": f"man:{name}#html",
                "content_type": "text/html",
                "content": html,
                "content_length": len(html),
                "metadata": {
                    "package": pkg,
                    "name": name,
                    "path": path,
                    "format": "html"
                }
            })
            html_sha256 = hashlib.sha256(html.encode("utf-8")).hexdigest()
            html_data["sha256"] = html_sha256
            html_compressed = cctx.compress(json.dumps(html_data, ensure_ascii=False).encode("utf-8"))
            result["html_compressed"] = html_compressed
            result["html_sha256"] = html_sha256
        
        return result
        
    except Exception as e:
        result["error"] = str(e)
        return result


def save_result(result: dict, output_dir: Path, seen: set):
    """Save a processed man page to disk."""
    if not result["success"]:
        return False
    
    if result["sha256"] in seen:
        return False
    
    seen.add(result["sha256"])
    
    # Text version
    date_dir = output_dir / time.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    doc_path = date_dir / f"{result['sha256'][:16]}.json.zst"
    with open(doc_path, "wb") as f:
        f.write(result["compressed_data"])
    
    # HTML version
    if result.get("html_compressed"):
        html_path = date_dir / f"{result['html_sha256'][:16]}.json.zst"
        with open(html_path, "wb") as f:
            f.write(result["html_compressed"])
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast Man Page Harvester")
    parser.add_argument("--parallel", type=int, default=multiprocessing.cpu_count(),
                       help="Number of parallel processes")
    parser.add_argument("--dry-run", action="store_true", help="Just count pages")
    parser.add_argument("--limit", type=int, default=None, help="Limit pages to process")
    
    args = parser.parse_args()
    
    output_dir = Path("/home/natalie/projects/doc-apocalypse/data/manpages")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    seen_file = output_dir / ".seen_hashes.json"
    seen = set()
    if seen_file.exists():
        with open(seen_file) as f:
            seen = set(json.load(f))
        logger.info(f"Loaded {len(seen)} seen hashes")
    
    pages = find_all_man_pages()
    logger.info(f"Found {len(pages)} man pages total")
    
    if args.dry_run:
        print(f"\n📊 Man Page Harvest — Dry Run")
        print(f"{'='*50}")
        print(f"  Total man pages: {len(pages)}")
        
        # Count by section
        from collections import Counter
        section_counts = Counter()
        for p in pages:
            base = os.path.basename(p)
            if base.endswith('.gz'):
                base = base[:-3]
            parts = base.rsplit('.', 1)
            section = parts[-1] if len(parts) > 1 else '?'
            section_counts[section] += 1
        
        print(f"  Sections:")
        for section, count in sorted(section_counts.items()):
            print(f"    {section}: {count}")
        
        # Get unique packages faster (just from /var/lib/pacman/local)
        pkg_dirs = os.listdir('/var/lib/pacman/local/') if os.path.isdir('/var/lib/pacman/local/') else []
        print(f"\n  Unique packages: ~{len(pkg_dirs)}")
        
        # Size estimates
        sample_size = 0
        sample_count = 0
        for p in pages[:50]:
            if os.path.exists(p):
                stat = os.stat(p)
                sample_size += stat.st_size
                sample_count += 1
        
        avg_compressed = sample_size / max(sample_count, 1)
        avg_uncompressed = avg_compressed * 4  # rough estimate: gzip compresses ~4:1
        print(f"  Average compressed size: {avg_compressed/1024:.1f} KB")
        print(f"  Estimated total compressed: {len(pages) * avg_compressed / 1024**3:.2f} GB")
        print(f"  Estimated total uncompressed: {len(pages) * avg_uncompressed / 1024**3:.2f} GB")
        print(f"\n  After our ZSTD compression: ~{len(pages) * avg_compressed * 0.6 / 1024**3:.2f} GB (estimated)")
        return 0
    
    if args.limit:
        pages = pages[:args.limit]
        logger.info(f"Limited to {len(pages)} pages")
    
    logger.info(f"Processing {len(pages)} man pages with {args.parallel} workers...")
    
    start = time.time()
    scraped = 0
    skipped = 0
    errors = 0
    total_bytes = 0
    
    with multiprocessing.Pool(processes=args.parallel) as pool:
        for i, result in enumerate(pool.imap_unordered(process_man_page, pages, chunksize=10)):
            if result["success"]:
                if save_result(result, output_dir, seen):
                    scraped += 1
                    total_bytes += result["compressed_size"]
                    if result.get("html_compressed"):
                        total_bytes += len(result["html_compressed"])
                else:
                    skipped += 1
            else:
                errors += 1
            
            if (i + 1) % 500 == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                logger.info(f"[{i+1}/{len(pages)}] {scraped} scraped, {skipped} skipped, "
                           f"{errors} errors ({rate:.0f} pages/s)")
    
    elapsed = time.time() - start
    logger.info(f"\n{'='*50}")
    logger.info(f"Man Page Harvest Complete!")
    logger.info(f"  Total pages: {len(pages)}")
    logger.info(f"  Scraped: {scraped}")
    logger.info(f"  Skipped (dedup): {skipped}")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Total size: {total_bytes / 1024 / 1024:.1f} MB compressed")
    logger.info(f"  Time: {elapsed:.1f}s ({scraped/elapsed:.0f} docs/s)")
    
    # Save seen hashes
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)
    
    # Save stats
    stats = {
        "total": len(pages),
        "scraped": scraped,
        "skipped": skipped,
        "errors": errors,
        "bytes": total_bytes,
        "elapsed": elapsed,
    }
    with open(output_dir / ".stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    
    return scraped


if __name__ == "__main__":
    sys.exit(main())
