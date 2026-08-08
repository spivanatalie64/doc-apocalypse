#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                 DOC-APOCALYPSE v1.0                         ║
║        "The end of undocumented software."                  ║
║                                                             ║
║  Harvests all open source + corporate documentation         ║
║  from: GitHub, GitLab, man pages, ReadTheDocs,              ║
║        DevDocs, corporate docs, wikis                       ║
║                                                             ║
║  Storage: Zstandard-compressed JSON, deduped by SHA256      ║
║  Index:   Full-text searchable (Meilisearch planned)        ║
╚══════════════════════════════════════════════════════════════╝

Usage:
  python apocalypse.py                    # Run ALL scrapers
  python apocalypse.py --github           # GitHub only
  python apocalypse.py --manpages         # Man pages only
  python apocalypse.py --corporate        # Corporate docs only
  python apocalypse.py --all              # All (default)
  python apocalypse.py --dry-run          # Show what would be done
  python apocalypse.py --stats            # Show current stats
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


# Add scrapers to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scrapers"))


def setup_logging(verbose: bool = False):
    """Set up logging to both file and console."""
    log_dir = Path("/home/natalie/projects/doc-apocalypse/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / f"apocalypse_{timestamp}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("doc-apocalypse")


def print_banner():
    """Print the doc-apocalypse banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                   DOC-APOCALYPSE                         ║
    ║          "The end of undocumented software."              ║
    ║                                                          ║
    ║     ╻ ╻╺┳╸┏━╸┏━┓╻  ╻┏┓╻┏━╸┏┓╻┏━┓┏━┓┏━╸┏━╸               ║
    ║     ┃ ┃ ┃ ┣╸ ┣┳┛┃  ┃┃┗┫┣╸ ┃┃┃┣━┫┣━┫┣╸ ┣╸                ║
    ║     ┗━┛ ╹ ┗━╸╹┗╸┗━╸╹╹ ╹┗━╸╹┗┛╹ ╹╹ ╹┗━╸┗━╸               ║
    ║                                                          ║
    ║  Targets: GitHub (100+ orgs) | GitLab (7 instances)      ║
    ║           Man Pages (all packages) | ReadTheDocs          ║
    ║           DevDocs | Microsoft | Google | AWS             ║
    ║           Cloudflare | MDN | Arch Wiki | Docker          ║
    ║           K8s | Terraform | nginx | Python | Rust | Go   ║
    ║                                                          ║
    ║  Storage: Zstandard JSON | Dedup SHA256                  ║
    ║  ~/.natalie/projects/doc-apocalypse/                     ║
    ╚═══════════════════════════════════════════════════════════╝
    
    *awawawawawawawawa~* ❤️  — Eilatan
    
    """
    print(banner)


def check_dependencies() -> bool:
    """Check that required tools are installed."""
    required = {
        "git": "git --version",
        "python3": "python3 --version",
        "pacman": "pacman --version",
        "man": "man --version",
    }
    
    optional = {
        "pkgfile": "pkgfile --version",
        "parallel": "parallel --version",
        "pv": "pv --version",
    }
    
    all_good = True
    logger = logging.getLogger("doc-apocalypse")
    
    logger.info("Checking dependencies...")
    
    for name, cmd in required.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            version = result.stdout.strip().split("\n")[0][:50]
            logger.info(f"  ✅ {name}: {version}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.error(f"  ❌ {name}: NOT FOUND (required)")
            all_good = False
    
    for name, cmd in optional.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=5)
            version = result.stdout.strip().split("\n")[0][:50]
            logger.info(f"  ✅ {name}: {version}")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(f"  ⚠️  {name}: NOT FOUND (optional)")
    
    return all_good


def show_stats():
    """Show current archive statistics."""
    data_dir = Path("/home/natalie/projects/doc-apocalypse/data")
    
    if not data_dir.exists():
        print("No data directory found. Run the scraper first.")
        return
    
    print(f"\n📊 Doc-Apocalypse Archive Stats")
    print(f"{'='*60}")
    
    total_files = 0
    total_bytes = 0
    total_dedup = 0
    
    for source_dir in data_dir.iterdir():
        if not source_dir.is_dir() or source_dir.name.startswith("."):
            continue
        
        # Count compressed files
        n_files = sum(1 for _ in source_dir.rglob("*.json.zst"))
        n_bytes = sum(f.stat().st_size for f in source_dir.rglob("*.json.zst"))
        total_files += n_files
        total_bytes += n_bytes
        
        # Check dedup stats
        seen_file = source_dir / ".seen_hashes.json"
        if seen_file.exists():
            with open(seen_file) as f:
                hashes = json.load(f)
            total_dedup += len(hashes)
        
        # Check run stats
        stats_file = source_dir / ".stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                stats = json.load(f)
            dedup_ratio = stats.get("skipped", 0) / max(stats.get("scraped", 1), 1) * 100
            print(f"  {source_dir.name}:")
            print(f"    Documents: {stats.get('scraped', n_files)}")
            print(f"    Skipped (dedup): {stats.get('skipped', 0)} ({dedup_ratio:.1f}%)")
            print(f"    Errors: {stats.get('errors', 0)}")
            print(f"    Files on disk: {n_files}")
            print(f"    Size: {n_bytes / 1024 / 1024:.1f} MB")
            print(f"    Unique hashes: {len(hashes)}")
        else:
            print(f"  {source_dir.name}: {n_files} files, {n_bytes / 1024 /1024:.1f} MB")
        print()
    
    print(f"{'='*60}")
    print(f"  TOTAL: {total_files} files, {total_bytes / 1024 /1024 /1024:.2f} GB")
    print(f"  TOTAL unique docs: ~{total_dedup}")
    print()


async def run_scraper(scraper_module: str, scraper_class: str, logger):
    """Dynamically import and run a scraper."""
    try:
        module = __import__(f"scrapers.{scraper_module}", fromlist=[scraper_class])
        scraper_class_obj = getattr(module, scraper_class)
        scraper = scraper_class_obj()
        await scraper.run()
    except Exception as e:
        logger.error(f"Error running {scraper_module}.{scraper_class}: {e}")
        import traceback
        traceback.print_exc()


async def run_all(logger):
    """Run all scrapers sequentially."""
    scrapers = [
        ("github_scraper", "GitHubScraper"),
        ("gitlab_scraper", "GitLabScraper"),
        ("manpage_scraper", "ManPageHarvester"),
        ("corporate_scraper", "CorporateScraper"),
    ]
    
    total_start = time.time()
    
    for module_name, class_name in scrapers:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting: {module_name}.{class_name}")
        logger.info(f"{'='*60}\n")
        
        start = time.time()
        await run_scraper(module_name, class_name, logger)
        
        elapsed = time.time() - start
        logger.info(f"\n{'='*60}")
        logger.info(f"Finished: {module_name}.{class_name} ({elapsed:.1f}s)")
        logger.info(f"{'='*60}\n")
    
    total_elapsed = time.time() - total_start
    logger.info(f"\n{'='*60}")
    logger.info(f"DOC-APOCALYPSE COMPLETE ({total_elapsed:.1f}s)")
    logger.info(f"{'='*60}")


def install_pkgfile():
    """Install pkgfile for full man page listing."""
    logger = logging.getLogger("doc-apocalypse")
    logger.info("Installing pkgfile for complete man page listing...")
    try:
        subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "pkgfile"], 
                      capture_output=True, timeout=120)
        subprocess.run(["sudo", "pkgfile", "-u"], capture_output=True, timeout=300)
        logger.info("✅ pkgfile installed and updated")
    except Exception as e:
        logger.warning(f"Could not install pkgfile: {e}")
        logger.warning("Run manually: sudo pacman -S pkgfile && sudo pkgfile -u")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Doc-Apocalypse: Harvest all documentation everywhere",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python apocalypse.py --all              # Run everything
  python apocalypse.py --github           # GitHub docs only
  python apocalypse.py --corporate        # Corporate docs only
  python apocalypse.py --stats            # Show archive stats
  python apocalypse.py --install-pkgfile  # Install pkgfile for man pages
  python apocalypse.py --dry-run          # Print what would be done
        """
    )
    
    parser.add_argument("--all", action="store_true", help="Run all scrapers")
    parser.add_argument("--github", action="store_true", help="Scrape GitHub docs")
    parser.add_argument("--gitlab", action="store_true", help="Scrape GitLab docs")
    parser.add_argument("--manpages", action="store_true", help="Harvest man pages")
    parser.add_argument("--corporate", action="store_true", help="Scrape corporate docs")
    parser.add_argument("--index", action="store_true", help="Build/rebuild search index")
    parser.add_argument("--stats", action="store_true", help="Show archive statistics")
    parser.add_argument("--dry-run", action="store_true", help="Print configuration without scraping")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--install-pkgfile", action="store_true", help="Install pkgfile for man pages")
    
    args = parser.parse_args()
    
    print_banner()
    
    logger = setup_logging(args.verbose)
    
    if args.stats:
        show_stats()
        return 0
    
    if args.install_pkgfile:
        install_pkgfile()
        return 0
    
    if args.dry_run:
        logger.info("=== DRY RUN ===")
        from scrapers.github_scraper import TARGET_ORGS, EXTRA_REPOS
        logger.info(f"GitHub: {len(TARGET_ORGS)} orgs + {len(EXTRA_REPOS)} extra repos")
        logger.info(f"Man pages: All installed packages ({subprocess.run(['pacman', '-Qq'], capture_output=True, text=True).stdout.count(chr(10))} packages)")
        
        from scrapers.corporate_scraper import CORPORATE_TARGETS
        logger.info(f"Corporate: {len(CORPORATE_TARGETS)} targets")
        total_pages = sum(t.get("max_pages", 5000) for t in CORPORATE_TARGETS.values())
        logger.info(f"  Estimated pages: ~{total_pages}")
        
        logger.info(f"\nEstimated total documents: ~200k+ (conservative)")
        logger.info(f"Estimated storage: ~50-200GB (after compression)")
        logger.info(f"Data directory: /home/natalie/projects/doc-apocalypse/data/")
        return 0
    
    # Check deps
    if not check_dependencies():
        logger.warning("Some dependencies missing. Scraping may be limited.")
    
    # Determine what to run
    if args.github:
        asyncio.run(run_scraper("github_scraper", "GitHubScraper", logger))
    elif args.gitlab:
        asyncio.run(run_scraper("gitlab_scraper", "GitLabScraper", logger))
    elif args.manpages:
        asyncio.run(run_scraper("manpage_scraper", "ManPageHarvester", logger))
    elif args.corporate:
        asyncio.run(run_scraper("corporate_scraper", "CorporateScraper", logger))
    elif args.index:
        from scrapers.indexer import DocIndexer
        indexer = DocIndexer()
        indexer.index_all()
        indexer.export_json_index()
        indexer.export_stats()
    else:
        # Default (or --all): run all
        asyncio.run(run_all(logger))
    
    # Show final stats
    show_stats()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
