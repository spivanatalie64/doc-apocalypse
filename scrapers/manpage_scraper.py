"""
Man Page Harvester
Extracts EVERY man page from the system (installed packages).
Also fetches man pages from man.archlinux.org for all available packages.
Formats as text, HTML, and groff source.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from base_scraper import BaseScraper, ScraperResult

logger = logging.getLogger("doc-apocalypse.manpages")


class ManPageHarvester(BaseScraper):
    """
    Harvests all man pages from:
      1. Locally installed packages (pacman)
      2. man.archlinux.org (all official packages)
    """
    
    def __init__(self, data_dir: str = None):
        super().__init__("manpages", data_dir=data_dir, rate_limit=0.2)
        self.root_dir = Path("/home/natalie/projects/doc-apocalypse/data/manpages")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        self.man_sections = {
            "1": "User Commands",
            "2": "System Calls",
            "3": "Library Functions",
            "4": "Device Drivers / Special Files",
            "5": "File Formats",
            "6": "Games",
            "7": "Miscellaneous",
            "8": "System Administration",
            "9": "Kernel Interfaces",
        }
    
    def get_installed_packages(self) -> list:
        """Get all installed packages from pacman."""
        try:
            result = subprocess.run(
                ["pacman", "-Qq"],
                capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip().split("\n")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.error(f"Failed to get installed packages: {e}")
            return []
    
    def get_man_pages_for_package(self, pkg: str) -> list:
        """Get man pages for a specific package."""
        try:
            result = subprocess.run(
                ["pacman", "-Ql", pkg],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
            
            man_pages = []
            for line in result.stdout.strip().split("\n"):
                parts = line.split(" ", 1)
                if len(parts) < 2:
                    continue
                path = parts[1]
                if "usr/share/man/" in path:
                    man_pages.append(path)
            
            return man_pages
        except subprocess.TimeoutExpired:
            return []
    
    def render_man_page(self, man_path: str, fmt: str = "text") -> Optional[str]:
        """
        Render a man page to text, HTML, or groff source.
        fmt: 'text', 'html', 'groff' (raw)
        Uses groff directly since 'man' may not be installed.
        """
        if not os.path.exists(man_path):
            return None
        
        try:
            # Handle compressed man pages by decompressing to stdin
            import gzip
            
            if man_path.endswith(".gz"):
                with gzip.open(man_path, 'rt', errors='replace') as f:
                    groff_source = f.read()
            else:
                with open(man_path, 'r', errors='replace') as f:
                    groff_source = f.read()
            
            if fmt == "text":
                result = subprocess.run(
                    ["groff", "-mandoc", "-Tutf8", "-P-c"],
                    input=groff_source,
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode == 0 and result.stdout:
                    # Strip ANSI escape codes
                    text = result.stdout
                    import re as _re
                    text = _re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
                    text = _re.sub(r'\x1b\[[0-9;]*', '', text)
                    text = _re.sub(r'[_\x08]+', '', text)
                    return text
                return None
            
            elif fmt == "html":
                result = subprocess.run(
                    ["groff", "-mandoc", "-Thtml"],
                    input=groff_source,
                    capture_output=True, text=True, timeout=15
                )
                return result.stdout if result.returncode == 0 else None
            
            elif fmt == "groff":
                return groff_source
            
            return None
        except (subprocess.TimeoutExpired, OSError, ImportError) as e:
            logger.debug(f"Error rendering {man_path}: {e}")
            return None
    
    def parse_man_metadata(self, man_path: str) -> dict:
        """Extract metadata from a man page path."""
        path = Path(man_path)
        fname = path.name
        
        # Parse: command.section.gz or command.section
        match = re.match(r"(.+)\.(\d+)\.?(gz|bz2|xz)?$", fname)
        if match:
            name = match.group(1)
            section = match.group(2)
        else:
            name = fname
            section = "unknown"
        
        # Get package name from path
        # /usr/share/man/man1/foo.1.gz -> package is found via pacman -Qo
        pkg = None
        try:
            result = subprocess.run(
                ["pacman", "-Qo", man_path],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # "file.pm is owned by perl 5.38.2-1"
                match = re.match(r".+ is owned by (\S+)", result.stdout)
                if match:
                    pkg = match.group(1)
        except:
            pass
        
        return {
            "name": name,
            "section": section,
            "section_name": self.man_sections.get(section, "Unknown"),
            "package": pkg,
            "path": man_path,
        }
    
    def harvest_local_man_pages(self):
        """Harvest all man pages from installed packages."""
        logger.info("[ManPages] Harvesting local man pages...")
        
        packages = self.get_installed_packages()
        logger.info(f"[ManPages] Found {len(packages)} installed packages")
        
        total_pages = 0
        for i, pkg in enumerate(packages):
            if i % 100 == 0:
                logger.info(f"[ManPages] [{i}/{len(packages)}] Processing {pkg}...")
            
            man_paths = self.get_man_pages_for_package(pkg)
            
            for man_path in man_paths:
                if not os.path.exists(man_path) or not man_path.endswith((".gz", ".bz2", ".xz", "")):
                    continue
                
                # Handle compressed man pages
                try:
                    if man_path.endswith(".gz"):
                        rendered_path = man_path
                    else:
                        rendered_path = man_path
                    
                    # Render as text
                    text_content = self.render_man_page(man_path, "text")
                    if not text_content:
                        continue
                    
                    metadata = self.parse_man_metadata(man_path)
                    
                    # Also try HTML
                    html_content = self.render_man_page(man_path, "html")
                    
                    # Save text version
                    result = ScraperResult(
                        source=f"manpages/{pkg}",
                        url=f"man:{metadata['name']}({metadata['section']})",
                        content=text_content,
                        content_type="text/plain",
                        metadata={
                            **metadata,
                            "format": "text",
                            "package": pkg,
                        }
                    )
                    self.save_document(result)
                    
                    # Save HTML version if available
                    if html_content:
                        result_html = ScraperResult(
                            source=f"manpages/{pkg}",
                            url=f"man:{metadata['name']}({metadata['section']})#html",
                            content=html_content,
                            content_type="text/html",
                            metadata={
                                **metadata,
                                "format": "html",
                                "package": pkg,
                            }
                        )
                        self.save_document(result_html)
                    
                    total_pages += 1
                    
                except Exception as e:
                    logger.debug(f"Error processing {man_path}: {e}")
                    continue
        
        logger.info(f"[ManPages] Harvested {total_pages} man pages from installed packages")
        return total_pages
    
    async def fetch_man_from_web(self, page: str, section: str = "1"):
        """Fetch a man page from man.archlinux.org."""
        url = f"https://man.archlinux.org/man/{page}.{section}"
        
        async with aiohttp.ClientSession() as session:
            text = await self.fetch(session, url)
            if text:
                result = ScraperResult(
                    source="man.archlinux.org",
                    url=url,
                    content=text,
                    content_type="text/html",
                    metadata={
                        "name": page,
                        "section": section,
                        "source": "man.archlinux.org",
                    }
                )
                self.save_document(result)
                return True
        return False
    
    def get_all_package_man_page_list(self) -> list:
        """
        Get a list of all man pages from ALL packages in the repos (not just installed).
        This uses `pkgfile` which queries the pacman database for all available packages.
        Falls back to man-db's mandb which has a searchable index.
        """
        man_pages = []
        
        # Method 1: Use pkgfile if available
        try:
            result = subprocess.run(
                ["pkgfile", "--list"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if "/man/" in line:
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            pkg = parts[0]
                            path = parts[1]
                            man_pages.append((pkg, path))
                logger.info(f"[ManPages] Found {len(man_pages)} from pkgfile")
                return man_pages
        except FileNotFoundError:
            logger.warning("[ManPages] pkgfile not installed, falling back")
        except Exception as e:
            logger.warning(f"[ManPages] pkgfile error: {e}")
        
        # Method 2: Use man-db's whatis/mandb
        try:
            result = subprocess.run(
                ["man", "-k", "."],
                capture_output=True, text=True, timeout=60,
                env={"MANWIDTH": "120"}
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    # "page (section)   - description"
                    match = re.match(r"^(\S+)\s+\((\d+)\)", line)
                    if match:
                        man_pages.append((match.group(1), match.group(2)))
                logger.info(f"[ManPages] Found {len(man_pages)} from man -k .")
                return man_pages
        except Exception as e:
            logger.warning(f"[ManPages] mandb error: {e}")
        
        return man_pages
    
    async def run(self):
        """Run the man page harvester."""
        logger.info("[ManPages] === MAN PAGE APOCALYPSE ===")
        
        # Phase 1: Harvest local man pages
        logger.info("[ManPages] Phase 1: Local installed packages")
        local_count = self.harvest_local_man_pages()
        
        # Phase 2: Try to get all available man pages
        logger.info("[ManPages] Phase 2: All available man pages from repos")
        all_pages = self.get_all_package_man_page_list()
        
        if all_pages:
            logger.info(f"[ManPages] Fetching content for {len(all_pages)} man pages...")
            
            # For pkgfile-style results (pkg, path)
            if isinstance(all_pages[0], tuple) and len(all_pages[0]) == 2:
                pages_to_fetch = all_pages[5000:5500]  # Limit for demo
                for i, (pkg, path) in enumerate(pages_to_fetch):
                    if i % 50 == 0:
                        logger.info(f"[ManPages] Web fetch [{i}/{len(pages_to_fetch)}]")
                    
                    page_name = Path(path).stem
                    section_match = re.search(r"\.(\d)\.", path)
                    section = section_match.group(1) if section_match else "1"
                    
                    await self.fetch_man_from_web(page_name, section)
                    await asyncio.sleep(0.1)  # Be nice
        
        # Phase 3: Install pkgfile for the full listing
        logger.info("[ManPages] Phase 3: Installing pkgfile for full package list...")
        logger.info("[ManPages] Run: sudo pacman -S pkgfile && sudo pkgfile -u")
        logger.info("[ManPages] Then re-run for COMPLETE man page archive (~100k+ pages)")
        
        self.save_stats()
        self._save_seen()
        self.print_stats()
        logger.info(f"[ManPages] DONE. Local: {local_count}, Web fetched: {self._stats['scraped']}")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/manpages.log"),
            logging.StreamHandler()
        ]
    )
    
    harvester = ManPageHarvester()
    await harvester.run()


if __name__ == "__main__":
    asyncio.run(main())
