"""
GitHub Documentation Scraper
Clones repos from target orgs and extracts documentation files.
Rate-limited, deduped, compressed.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from base_scraper import BaseScraper, ScraperResult

logger = logging.getLogger("doc-apocalypse.github")

DOC_PATTERNS = [
    "README*",
    "README.*",
    "*.md",
    "*.rst",
    "*.txt",
    "docs/",
    "documentation/",
    "doc/",
    "wiki/",
    "man/",
    "CONTRIBUTING*",
    "CHANGELOG*",
    "LICENSE*",
]

# Exclude noise (generated dirs, node_modules, vendored deps)
EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv",
    "env", ".env", ".tox", "vendor", ".bundle", "target",
    "build", "dist", ".next", ".nuxt", ".cache", "go/pkg",
    "third_party", "third-party", "3rdparty",
}

# Top orgs by doc value
TARGET_ORGS = [
    # Cloud / Infrastructure
    "cloudflare", "kubernetes", "docker", "hashicorp", "elastic",
    "nginx", "traefik", "coredns", "etcd", "prometheus",
    "grafana", "influxdata", "datadog", "opentofu",
    
    # Languages / Runtimes
    "python", "golang", "rust-lang", "nodejs", "dotnet",
    "ruby", "jruby", "elixir-lang", "erlang", "haskell",
    "kotlin", "scala", "nim-lang", "crystal-lang", "ziglang",
    "vlang", "denoland", "bun-sh", "oven-sh",
    
    # Databases
    "redis", "postgres", "mysql", "mongo", "neo4j",
    "couchbase", "arangodb", "cockroachdb", "tidb",
    "influxdata", "timescale", "questdb", "dragonflydb",
    "sqlite", "sqlitebrowser",
    
    # Big Tech / Corporate
    "microsoft", "google", "facebook", "apple", "amazon",
    "netflix", "uber", "lyft", "twitter", "linkedin",
    "square", "stripe", "shopify",
    
    # Operating Systems / Kernels
    "torvalds", "kernel", "systemd", "NixOS", "gentoo",
    "voidlinux", "alpinelinux", "coreos", "flatpak",
    "snapcore",
    
    # Desktop / UI
    "gnome", "KDE", "swaywm", "i3", "hyprwm", "awesomeWM",
    "Alacritty", "wezterm", "kovidgoyal", "neovim",
    "vim", "zsh-users", "fish-shell", "tmux",
    
    # Dev Tools
    "git", "curl", "ffmpeg", "ImageMagick", "gpac",
    "Homebrew", "linuxbrew", "nvm-sh", "nvm", "rbenv",
    "pyenv", "asdf-vm", "conda", "jupyter",
    
    # ML / AI
    "tensorflow", "pytorch", "jax-ml", "huggingface",
    "openai", "anthropics", "llvm", "onnx", "keras-team",
    
    # Media / Creative
    "godotengine", "blender", "inkscape", "gimp",
    "obsproject", "audacity", "krita", "darktable",
    "HandBrake", "mkvtoolnix",
    
    # Security
    "openssl", "openssh", "libssh2", "letsencrypt",
    "certbot", "torproject", "signalapp",
    "WireGuard", "strongswan",
    
    # Web Servers / Proxies
    "apache", "nginx", "caddyserver", "haproxy",
    "envoyproxy", "istio", "linkerd",
    
    # Misc Heavy Hitters
    "ansible", "checkmk", "nagios", "zabbix",
    "mozilla", "libreoffice", "the-tcpdump-group",
    "htop-dev", "torvalds", "raspberrypi",
    "arduino", "espressif", "RIOT-OS",
]

# Additional repos known for great docs
EXTRA_REPOS = [
    "https://github.com/microsoft/vscode",
    "https://github.com/microsoft/terminal",
    "https://github.com/microsoft/PowerShell",
    "https://github.com/google/gvisor",
    "https://github.com/google/grumpy",
    "https://github.com/GoogleCloudPlatform/terraformer",
    "https://github.com/facebook/zstd",
    "https://github.com/facebook/folly",
    "https://github.com/amazon-science",
    "https://github.com/aws/aws-cdk",
    "https://github.com/aws/aws-sdk-js-v3",
    "https://github.com/awslabs",
    "https://github.com/netflix/metaflow",
    "https://github.com/netflix/zuul",
    "https://github.com/netflix/Hystrix",
    "https://github.com/cloudflare/workers-sdk",
    "https://github.com/cloudflare/cloudflare-docs",
    "https://github.com/kubernetes/kubernetes",
    "https://github.com/kubernetes/website",
    "https://github.com/apache/hadoop",
    "https://github.com/apache/spark",
    "https://github.com/apache/kafka",
    "https://github.com/apache/cassandra",
    "https://github.com/apache/tomcat",
    "https://github.com/apache/httpd",
    "https://github.com/apache/maven",
    "https://github.com/apache/ant",
    "https://github.com/apache/lucene",
    "https://github.com/apache/solr",
    "https://github.com/apache/zookeeper",
    "https://github.com/apache/thrift",
    "https://github.com/apache/hbase",
]


class GitHubScraper(BaseScraper):
    """Scrapes documentation from GitHub organizations and repos."""
    
    def __init__(self, data_dir: str = None, max_concurrent: int = 4):
        super().__init__("github", data_dir=data_dir, rate_limit=0.5)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.root_dir = Path("/home/natalie/projects/doc-apocalypse/data/github")
        self.root_dir.mkdir(parents=True, exist_ok=True)
        
        # Repo cache to avoid re-cloning
        self.repo_cache = self.root_dir / "_repos"
        self.repo_cache.mkdir(exist_ok=True)
    
    def _org_repo_url(self, org: str, repo: str = None) -> str:
        if repo:
            return f"https://github.com/{org}/{repo}.git"
        return f"https://github.com/{org}.git"
    
    def _is_doc_file(self, rel_path: str) -> bool:
        """Check if a file path matches doc patterns."""
        # Exclude noise dirs
        parts = rel_path.replace("\\", "/").split("/")
        for part in parts:
            if part in EXCLUDE_DIRS:
                return False
        
        name = parts[-1].lower()
        
        # Direct match
        if any(name == p.lower().rstrip("*") or 
               name.endswith(p.lstrip("*").lower())
               for p in DOC_PATTERNS if "*" in p):
            return True
        if any(name == p.lower() for p in DOC_PATTERNS if "*" not in p):
            return True
        
        # Directory-based
        for p in DOC_PATTERNS:
            if p.endswith("/"):
                dir_name = p.rstrip("/").lower()
                if dir_name in parts[:-1]:
                    return True
                if parts[0] == dir_name:
                    return True
        
        # Extension-based
        doc_exts = {".md", ".rst", ".txt", ".html", ".pdf", ".adoc", ".asciidoc", 
                    ".mdown", ".markdown", ".rdoc", ".creole", ".wiki"}
        if any(rel_path.lower().endswith(ext) for ext in doc_exts):
            # But skip generated/binary stuff
            binary_like = {".png", ".jpg", ".gif", ".svg", ".ico", ".woff", ".ttf"}
            if any(rel_path.lower().endswith(ext) for ext in binary_like):
                return False
            return True
        
        return False
    
    def clone_repo(self, repo_url: str, dest: Path) -> bool:
        """Clone a repo shallowly (single branch, depth 1) to save bandwidth."""
        if dest.exists():
            # Pull instead
            try:
                subprocess.run(
                    ["git", "-C", str(dest), "pull", "--ff-only"],
                    capture_output=True, timeout=120
                )
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                logger.warning(f"Pull failed for {repo_url}, re-cloning")
                shutil.rmtree(dest, ignore_errors=True)
        
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "--single-branch", 
                 repo_url, str(dest)],
                capture_output=True, timeout=180,
                env={"GIT_TERMINAL_PROMPT": "0"}
            )
            if result.returncode != 0:
                logger.error(f"Clone failed for {repo_url}: {result.stderr.decode()[:200]}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"Clone timeout for {repo_url}")
            return False
        except Exception as e:
            logger.error(f"Clone error for {repo_url}: {e}")
            return False
    
    def extract_docs_from_repo(self, org: str, repo_name: str, repo_path: Path) -> list:
        """Walk a cloned repo and return doc file contents."""
        results = []
        base_url = f"https://github.com/{org}/{repo_name}/blob/main"
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS 
                      and not d.startswith(".")]
            
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == ".":
                rel_root = ""
            
            for fname in files:
                rel_path = os.path.join(rel_root, fname) if rel_root else fname
                if not self._is_doc_file(rel_path):
                    continue
                
                fpath = os.path.join(root, fname)
                
                # Skip binary files
                try:
                    with open(fpath, "rb") as f:
                        raw = f.read(8192)
                        if b"\x00" in raw:
                            continue  # binary file
                    
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read()
                    
                    if len(content) < 50:  # too small to be useful
                        continue
                    
                    result = ScraperResult(
                        source=f"github/{org}/{repo_name}",
                        url=f"{base_url}/{rel_path}",
                        content=content,
                        content_type=self._infer_content_type(rel_path),
                        metadata={
                            "org": org,
                            "repo": repo_name,
                            "path": rel_path,
                            "clone_path": str(repo_path),
                        }
                    )
                    results.append(result)
                except Exception as e:
                    logger.debug(f"Error reading {fpath}: {e}")
                    continue
        
        return results
    
    def _infer_content_type(self, path: str) -> str:
        ext = Path(path).suffix.lower()
        return {
            ".md": "text/markdown",
            ".rst": "text/rst",
            ".txt": "text/plain",
            ".adoc": "text/asciidoc",
            ".html": "text/html",
            ".pdf": "application/pdf",
        }.get(ext, "text/plain")
    
    def get_org_repos(self, org: str) -> list:
        """Get list of repos for an org using GitHub API."""
        repos = []
        page = 1
        while True:
            url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}"
            try:
                import urllib.request
                req = urllib.request.Request(url)
                req.add_header("Accept", "application/vnd.github.v3+json")
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                    if not data:
                        break
                    for repo in data:
                        repos.append({
                            "name": repo["name"],
                            "clone_url": repo["clone_url"],
                            "description": repo.get("description", ""),
                            "language": repo.get("language", ""),
                            "size": repo.get("size", 0),
                        })
                    page += 1
            except Exception as e:
                logger.warning(f"Failed to list repos for {org}: {e}")
                break
        return repos
    
    async def scrape_org(self, org: str):
        """Scrape all repos for an organization."""
        logger.info(f"[GitHub] Scraping org: {org}")
        
        repos = self.get_org_repos(org)
        logger.info(f"[GitHub] Found {len(repos)} repos for {org}")
        
        org_dir = self.repo_cache / org
        org_dir.mkdir(parents=True, exist_ok=True)
        
        async with self.semaphore:
            for repo in repos:
                if repo["size"] > 500_000:  # Skip repos > 500MB (too big for shallow clone)
                    logger.info(f"[GitHub] Skipping {org}/{repo['name']} (too large: {repo['size']}KB)")
                    continue
                
                repo_path = org_dir / repo["name"]
                
                # Clone
                if not self.clone_repo(repo["clone_url"], repo_path):
                    continue
                
                # Extract docs
                docs = self.extract_docs_from_repo(org, repo["name"], repo_path)
                
                # Save
                for doc in docs:
                    self.save_document(doc)
                
                logger.info(f"[GitHub] {org}/{repo['name']}: {len(docs)} docs extracted")
                
                # Save per-repo stats
                if docs:
                    repo_stats = org_dir / f"{repo['name']}_docs.json"
                    with open(repo_stats, "w") as f:
                        json.dump({
                            "org": org,
                            "repo": repo["name"],
                            "language": repo.get("language", ""),
                            "doc_count": len(docs),
                            "docs": [(d.url, d.content_type, d.sha256[:16]) for d in docs]
                        }, f, indent=2)
                
                # Rate limit between clones
                await asyncio.sleep(0.3)
    
    async def scrape_single_repo(self, repo_url: str):
        """Scrape a single repo (non-org)."""
        # Parse org/repo from URL
        parts = repo_url.rstrip(".git").split("/")
        org, repo = parts[-2], parts[-1]
        
        logger.info(f"[GitHub] Scraping single repo: {org}/{repo}")
        
        repo_path = self.repo_cache / "_extras" / org / repo
        repo_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.clone_repo(repo_url, repo_path):
            docs = self.extract_docs_from_repo(org, repo, repo_path)
            for doc in docs:
                self.save_document(doc)
            logger.info(f"[GitHub] {org}/{repo}: {len(docs)} docs extracted")
    
    async def run(self):
        """Run the GitHub doc apocalypse."""
        logger.info(f"[GitHub] Starting scrape of {len(TARGET_ORGS)} orgs...")
        logger.info(f"[GitHub] + {len(EXTRA_REPOS)} extra repos")
        
        # Scrape orgs
        for i, org in enumerate(TARGET_ORGS):
            logger.info(f"[GitHub] [{i+1}/{len(TARGET_ORGS)}] Processing {org}")
            try:
                await self.scrape_org(org)
            except Exception as e:
                logger.error(f"[GitHub] Error scraping {org}: {e}")
            self.save_stats()
            self.print_stats()
        
        # Scrape extra repos
        logger.info(f"[GitHub] Processing {len(EXTRA_REPOS)} extra repos...")
        for repo_url in EXTRA_REPOS:
            try:
                await self.scrape_single_repo(repo_url)
            except Exception as e:
                logger.error(f"[GitHub] Error scraping {repo_url}: {e}")
        
        self.save_stats()
        self._save_seen()
        self.print_stats()
        logger.info(f"[GitHub] DONE. Total docs archived.")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/github.log"),
            logging.StreamHandler()
        ]
    )
    
    scraper = GitHubScraper(max_concurrent=4)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
