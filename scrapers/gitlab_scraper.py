"""
GitLab Documentation Scraper
Targets: gitlab.com, freedesktop.org, GNOME, KDE, Salsa (Debian), Arch Linux, Kitware
Clones repos and extracts documentation (README*, docs/, *.md, *.rst, etc.)
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from base_scraper import BaseScraper, ScraperResult

logger = logging.getLogger("doc-apocalypse.gitlab")

GITLAB_INSTANCES = {
    "gitlab.com": {
        "api_url": "https://gitlab.com/api/v4",
        "target_groups": [
            "gitlab-org",
            "gitlab-charts",
            "gnome",
            "KDE",
            "freedesktop",
            "libreoffice",
            "gstreamer",
            "GNOME",
            "xfce",
            "moodle",
            "debian",
            "torproject",
        ],
    },
    "gitlab.freedesktop.org": {
        "api_url": "https://gitlab.freedesktop.org/api/v4",
        "target_groups": [
            "wayland",
            "mesa",
            "drm",
            "pipewire",
            "pulseaudio",
            "dbus",
            "systemd",
            "poppler",
            "cairo",
            "pixman",
            "xorg",
            "libinput",
            "freetype",
            "fontconfig",
            "NetworkManager",
            "spice",
            "virtio",
        ],
    },
    "gitlab.gnome.org": {
        "api_url": "https://gitlab.gnome.org/api/v4",
        "target_groups": [
            "GNOME",
            "gtk",
            "glib",
            "gimp",
            "inkscape",
            "nautilus",
            "mutter",
            "gnome-shell",
            "libadwaita",
            "folks",
            "evolution",
            "gparted",
            "rhythmbox",
            "totem",
            "evince",
            "file-roller",
            "gnome-calendar",
            "gnome-software",
        ],
    },
    "gitlab.kitware.com": {
        "api_url": "https://gitlab.kitware.com/api/v4",
        "target_groups": [
            "cmake",
            "vtk",
            "itk",
            "paraview",
            "kwai",
        ],
    },
    "salsa.debian.org": {
        "api_url": "https://salsa.debian.org/api/v4",
        "target_groups": [
            "debian",
            "apt-team",
            "dpkg-team",
            "dbus-team",
            "glibc-team",
            "systemd-team",
            "gcc-team",
            "linux-kernel-team",
        ],
    },
    "gitlab.archlinux.org": {
        "api_url": "https://gitlab.archlinux.org/api/v4",
        "target_groups": [
            "archlinux",
            "pacman",
            "mkinitcpio",
            "archiso",
            "devtools",
            "dbscripts",
            "archivetools",
        ],
    },
}


class GitLabScraper(BaseScraper):
    """Scrapes documentation from GitLab instances."""
    
    def __init__(self, data_dir: str = None, max_concurrent: int = 3):
        super().__init__("gitlab", data_dir=data_dir, rate_limit=0.5)
        self.max_concurrent = max_concurrent
        self.root_dir = Path("/home/natalie/projects/doc-apocalypse/data/gitlab")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.repo_cache = self.root_dir / "_repos"
        self.repo_cache.mkdir(exist_ok=True)
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    def _get_headers(self, instance: str) -> dict:
        """Get auth headers for a GitLab instance if token is available."""
        headers = {}
        env_var = f"GITLAB_TOKEN_{instance.replace('.', '_').upper()}"
        token = os.environ.get(env_var) or os.environ.get("GITLAB_TOKEN")
        if token:
            headers["PRIVATE-TOKEN"] = token
        return headers
    
    def _is_doc_file(self, rel_path: str) -> bool:
        """Same doc file detection as GitHub scraper."""
        from scrapers.github_scraper import GitHubScraper
        # Just reuse the logic inline
        EXCLUDE_DIRS = {
            "node_modules", ".git", "__pycache__", "venv", ".venv",
            "env", ".env", ".tox", "vendor", ".bundle", "target",
            "build", "dist", ".next", ".nuxt", ".cache",
            "third_party", "third-party", "3rdparty",
        }
        DOC_PATTERNS = [
            "README*", "*.md", "*.rst", "*.txt",
            "docs/", "documentation/", "doc/", "wiki/", "man/",
            "CONTRIBUTING*", "CHANGELOG*", "LICENSE*",
        ]
        
        parts = rel_path.replace("\\", "/").split("/")
        for part in parts:
            if part in EXCLUDE_DIRS:
                return False
        
        name = parts[-1].lower()
        
        if any(name == p.lower().rstrip("*") or 
               name.endswith(p.lstrip("*").lower())
               for p in DOC_PATTERNS if "*" in p):
            return True
        if any(name == p.lower() for p in DOC_PATTERNS if "*" not in p):
            return True
        
        for p in DOC_PATTERNS:
            if p.endswith("/"):
                dir_name = p.rstrip("/").lower()
                if dir_name in parts[:-1] or parts[0] == dir_name:
                    return True
        
        doc_exts = {".md", ".rst", ".txt", ".html", ".adoc", ".asciidoc", 
                    ".mdown", ".markdown", ".rdoc", ".creole", ".wiki"}
        if any(rel_path.lower().endswith(ext) for ext in doc_exts):
            binary_like = {".png", ".jpg", ".gif", ".svg", ".ico"}
            if any(rel_path.lower().endswith(ext) for ext in binary_like):
                return False
            return True
        
        return False
    
    def _infer_content_type(self, path: str) -> str:
        ext = Path(path).suffix.lower()
        return {
            ".md": "text/markdown",
            ".rst": "text/rst",
            ".txt": "text/plain",
            ".adoc": "text/asciidoc",
            ".html": "text/html",
        }.get(ext, "text/plain")
    
    def clone_repo(self, clone_url: str, dest: Path) -> bool:
        """Shallow clone a repo."""
        if dest.exists():
            try:
                subprocess.run(
                    ["git", "-C", str(dest), "pull", "--ff-only"],
                    capture_output=True, timeout=120
                )
                return True
            except:
                shutil.rmtree(dest, ignore_errors=True)
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--single-branch",
                 clone_url, str(dest)],
                capture_output=True, timeout=180,
                env={"GIT_TERMINAL_PROMPT": "0"}
            )
            return result.returncode == 0
        except:
            return False
    
    def extract_docs_from_repo(self, instance: str, group: str, project: str, 
                               repo_path: Path) -> list:
        """Extract documentation files from a cloned repo."""
        results = []
        base_url = f"https://{instance}/{group}/{project}/-/blob/main"
        
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") 
                      and d not in ("node_modules", "venv", ".venv", "target", "build", "vendor")]
            
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == ".":
                rel_root = ""
            
            for fname in files:
                rel_path = os.path.join(rel_root, fname) if rel_root else fname
                if not self._is_doc_file(rel_path):
                    continue
                
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "rb") as f:
                        raw = f.read(8192)
                        if b"\x00" in raw:
                            continue
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read()
                    if len(content) < 50:
                        continue
                    
                    result = ScraperResult(
                        source=f"gitlab/{instance}/{group}/{project}",
                        url=f"{base_url}/{rel_path}",
                        content=content,
                        content_type=self._infer_content_type(rel_path),
                        metadata={
                            "instance": instance,
                            "group": group,
                            "project": project,
                            "path": rel_path,
                        }
                    )
                    results.append(result)
                except:
                    continue
        
        return results
    
    def get_group_projects(self, instance: str, api_url: str, group: str) -> list:
        """Get projects for a GitLab group."""
        projects = []
        page = 1
        
        headers = self._get_headers(instance)
        
        import urllib.request
        
        while True:
            url = f"{api_url}/groups/{urllib.parse.quote(group, safe='')}/projects?per_page=100&page={page}&include_subgroups=true"
            try:
                req = urllib.request.Request(url)
                for k, v in headers.items():
                    req.add_header(k, v)
                req.add_header("Accept", "application/json")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                    if not data:
                        break
                    for proj in data:
                        projects.append({
                            "name": proj["path"],
                            "full_path": proj["path_with_namespace"],
                            "clone_url": proj.get("http_url_to_repo") or proj.get("ssh_url_to_repo"),
                            "description": proj.get("description", ""),
                            "size": proj.get("statistics", {}).get("repository_size", 0) if proj.get("statistics") else 0,
                        })
                    page += 1
            except Exception as e:
                logger.warning(f"[GitLab] Failed to list projects for {group} on {instance}: {e}")
                break
        
        return projects
    
    async def scrape_instance(self, instance_name: str, config: dict):
        """Scrape all target groups on a GitLab instance."""
        logger.info(f"[GitLab] Scraping instance: {instance_name}")
        
        api_url = config["api_url"]
        groups = config["target_groups"]
        
        instance_dir = self.repo_cache / instance_name
        instance_dir.mkdir(parents=True, exist_ok=True)
        
        for group in groups:
            logger.info(f"[GitLab] [{instance_name}] Processing group: {group}")
            
            projects = self.get_group_projects(instance_name, api_url, group)
            logger.info(f"[GitLab] Found {len(projects)} projects in {group}")
            
            group_dir = instance_dir / group
            group_dir.mkdir(exist_ok=True)
            
            for project in projects:
                if project.get("size", 0) > 500_000:
                    logger.info(f"[GitLab] Skipping {project['full_path']} (too large)")
                    continue
                
                clone_url = project["clone_url"]
                if not clone_url:
                    continue
                
                # Convert SSH to HTTPS if needed
                if clone_url.startswith("git@"):
                    clone_url = clone_url.replace(":", "/").replace("git@", "https://")
                
                proj_path = group_dir / project["name"]
                
                if self.clone_repo(clone_url, proj_path):
                    docs = self.extract_docs_from_repo(
                        instance_name, group, project["name"], proj_path
                    )
                    for doc in docs:
                        self.save_document(doc)
                    
                    logger.info(f"[GitLab] {project['full_path']}: {len(docs)} docs")
                
                await asyncio.sleep(0.2)
        
        logger.info(f"[GitLab] Done with {instance_name}")
    
    async def run(self):
        """Run all GitLab scrapers."""
        logger.info(f"[GitLab] === GITLAB DOC APOCALYPSE ===")
        logger.info(f"[GitLab] {len(GITLAB_INSTANCES)} instances, "
                    f"{sum(len(i['target_groups']) for i in GITLAB_INSTANCES.values())} groups")
        
        for instance, config in GITLAB_INSTANCES.items():
            try:
                await self.scrape_instance(instance, config)
            except Exception as e:
                logger.error(f"[GitLab] Error scraping {instance}: {e}")
            
            self.save_stats()
            self.print_stats()
        
        self.save_stats()
        self._save_seen()
        self.print_stats()
        logger.info(f"[GitLab] DONE.")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/gitlab.log"),
            logging.StreamHandler()
        ]
    )
    
    scraper = GitLabScraper(max_concurrent=3)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
