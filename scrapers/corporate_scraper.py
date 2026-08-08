"""
Corporate Documentation Scraper
Targets: Microsoft Learn, Google Cloud, AWS, Cloudflare, Oracle, IBM, Red Hat, Canonical
Uses sitemaps, recursive wget-style scraping, and API endpoints where available.
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

from base_scraper import BaseScraper, ScraperResult

logger = logging.getLogger("doc-apocalypse.corporate")

CORPORATE_TARGETS = {
    "microsoft_learn": {
        "name": "Microsoft Learn",
        "base_url": "https://learn.microsoft.com/en-us/",
        "sitemap": "https://learn.microsoft.com/en-us/sitemap.xml",
        "docsets": ["dotnet", "azure", "windows", "powershell", "vscode", "typescript", "aspnet"],
        "rate_limit": 0.5,
        "max_pages": 10000,
    },
    "google_cloud": {
        "name": "Google Cloud Docs",
        "base_url": "https://cloud.google.com/docs/",
        "sitemap": "https://cloud.google.com/sitemap.xml",
        "docsets": ["compute", "storage", "kubernetes", "bigquery", "iam", "run", "functions"],
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "aws_docs": {
        "name": "AWS Docs",
        "base_url": "https://docs.aws.amazon.com/",
        "sitemap": "https://docs.aws.amazon.com/sitemap.xml",
        "docsets": ["ec2", "s3", "lambda", "eks", "rds", "iam", "dynamodb", "cloudfront"],
        "rate_limit": 0.3,
        "max_pages": 10000,
    },
    "cloudflare_docs": {
        "name": "Cloudflare Docs",
        "base_url": "https://developers.cloudflare.com/",
        "sitemap": "https://developers.cloudflare.com/sitemap.xml",
        "docsets": ["workers", "pages", "d1", "r2", "kv", "ai", "turnstile", "zero-trust"],
        "rate_limit": 0.2,  # Be nice to the Gray Goddess
        "max_pages": 5000,
    },
    "arch_wiki": {
        "name": "Arch Wiki",
        "base_url": "https://wiki.archlinux.org/",
        "sitemap": "https://wiki.archlinux.org/sitemap.xml",
        "docsets": [],
        "rate_limit": 0.3,
        "max_pages": 10000,
    },
    "mdn_docs": {
        "name": "MDN Web Docs",
        "base_url": "https://developer.mozilla.org/en-US/",
        "sitemap": "https://developer.mozilla.org/sitemaps/en-US/sitemap.xml.gz",
        "docsets": ["docs/Web", "docs/Learn", "docs/Glossary"],
        "rate_limit": 0.5,
        "max_pages": 20000,
    },
    "readthedocs": {
        "name": "ReadTheDocs",
        "base_url": "https://readthedocs.org/",
        "api_url": "https://readthedocs.org/api/v3/",
        "rate_limit": 0.5,
        "max_pages": 5000,
    },
    "devdocs": {
        "name": "DevDocs",
        "base_url": "https://devdocs.io/",
        "docs_json": "https://devdocs.io/docs.json",
        "rate_limit": 0.5,
        "max_pages": 5000,
    },
    "docker_docs": {
        "name": "Docker Docs",
        "base_url": "https://docs.docker.com/",
        "sitemap": "https://docs.docker.com/sitemap.xml",
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "kubernetes_docs": {
        "name": "Kubernetes Docs",
        "base_url": "https://kubernetes.io/docs/",
        "sitemap": "https://kubernetes.io/docs/sitemap.xml",
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "terraform_docs": {
        "name": "Terraform Docs",
        "base_url": "https://developer.hashicorp.com/terraform/docs",
        "sitemap": "https://developer.hashicorp.com/sitemap.xml",
        "rate_limit": 0.3,
        "max_pages": 3000,
    },
    "nginx_docs": {
        "name": "nginx Docs",
        "base_url": "https://nginx.org/en/docs/",
        "rate_limit": 0.3,
        "max_pages": 1000,
    },
    "postgres_docs": {
        "name": "PostgreSQL Docs",
        "base_url": "https://www.postgresql.org/docs/current/",
        "sitemap": "https://www.postgresql.org/sitemap.xml",
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "python_docs": {
        "name": "Python Docs",
        "base_url": "https://docs.python.org/3/",
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "rust_docs": {
        "name": "Rust Docs",
        "base_url": "https://doc.rust-lang.org/",
        "rate_limit": 0.3,
        "max_pages": 5000,
    },
    "golang_docs": {
        "name": "Go Docs",
        "base_url": "https://go.dev/doc/",
        "rate_limit": 0.3,
        "max_pages": 2000,
    },
    "nodejs_docs": {
        "name": "Node.js Docs",
        "base_url": "https://nodejs.org/en/docs/",
        "rate_limit": 0.3,
        "max_pages": 3000,
    },
}


class CorporateScraper(BaseScraper):
    """Scrapes corporate and major project documentation websites."""
    
    def __init__(self, data_dir: str = None, max_concurrent: int = 6):
        super().__init__("corporate", data_dir=data_dir, rate_limit=0.3)
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.visited_urls = set()
        self.seen_urls_file = Path(self.data_dir) / ".visited_urls.json"
        self._load_visited()
    
    def _load_visited(self):
        if self.seen_urls_file.exists():
            try:
                with open(self.seen_urls_file) as f:
                    self.visited_urls = set(json.load(f))
                logger.info(f"[Corporate] Loaded {len(self.visited_urls)} visited URLs")
            except Exception as e:
                logger.warning(f"[Corporate] Failed to load visited URLs: {e}")
    
    def _save_visited(self):
        with open(self.seen_urls_file, "w") as f:
            json.dump(list(self.visited_urls), f)
    
    def _extract_text_from_html(self, html: str, source_url: str) -> Optional[str]:
        """Extract readable text content from HTML."""
        try:
            soup = BeautifulSoup(html, "lxml")
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "footer", "header", 
                           "aside", "noscript", "iframe", "svg", "form"]):
                tag.decompose()
            
            # Try to find main content area
            main_content = None
            for selector in ["main", "[role='main']", "article", ".content", 
                           "#content", ".documentation", ".doc-content",
                           ".markdown", ".post-content", "[class*='content']",
                           "#readme", ".readme"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.body
            
            if not main_content:
                return None
            
            # Get text
            text = main_content.get_text(separator="\n", strip=True)
            
            # Clean up
            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]{2,}", " ", text)
            
            # Get title
            title = soup.title.string if soup.title else source_url
            
            return f"# {title}\n\n{text}"
        except Exception as e:
            logger.debug(f"Error extracting text from {source_url}: {e}")
            return None
    
    async def fetch_sitemap(self, sitemap_url: str) -> list:
        """Fetch and parse an XML sitemap."""
        urls = []
        async with aiohttp.ClientSession() as session:
            content = await self.fetch(session, sitemap_url)
            if content:
                soup = BeautifulSoup(content, "lxml-xml")
                for loc in soup.find_all("loc"):
                    url = loc.text.strip()
                    urls.append(url)
                logger.info(f"[Corporate] Sitemap {sitemap_url}: {len(urls)} URLs")
        return urls
    
    async def scrape_url(self, session: aiohttp.ClientSession, url: str, 
                         source_name: str) -> bool:
        """Scrape a single URL and save it."""
        if url in self.visited_urls:
            return False
        
        html = await self.fetch(session, url)
        if not html:
            return False
        
        text = self._extract_text_from_html(html, url)
        if not text or len(text) < 100:
            return False
        
        result = ScraperResult(
            source=source_name,
            url=url,
            content=text,
            content_type="text/markdown",
            metadata={
                "source_name": CORPORATE_TARGETS.get(source_name, {}).get("name", source_name),
                "html_length": len(html),
            }
        )
        
        path = self.save_document(result)
        self.visited_urls.add(url)
        
        return True
    
    async def scrape_source(self, source_key: str, config: dict):
        """Scrape a single corporate documentation source."""
        logger.info(f"[Corporate] Starting: {config['name']}")
        
        base_url = config["base_url"]
        urls_to_scrape = set()
        
        # Get URL list
        if "sitemap" in config:
            sitemap_urls = await self.fetch_sitemap(config["sitemap"])
            for url in sitemap_urls:
                if base_url in url:
                    urls_to_scrape.add(url)
        
        # Add docset URLs
        for docset in config.get("docsets", []):
            docset_url = urljoin(base_url, docset)
            urls_to_scrape.add(docset_url)
        
        # Ensure base URL is included
        urls_to_scrape.add(base_url)
        
        # Limit
        max_pages = config.get("max_pages", 5000)
        urls_to_scrape = list(urls_to_scrape)[:max_pages]
        
        logger.info(f"[Corporate] {config['name']}: {len(urls_to_scrape)} URLs to scrape")
        
        # Scrape
        async with aiohttp.ClientSession() as session:
            concurrency = asyncio.Semaphore(self.max_concurrent)
            
            async def scrape_with_limit(url):
                async with concurrency:
                    return await self.scrape_url(session, url, source_key)
            
            tasks = [scrape_with_limit(url) for url in urls_to_scrape]
            results = await asyncio.gather(*tasks)
            
            success = sum(1 for r in results if r)
            logger.info(f"[Corporate] {config['name']}: {success}/{len(urls_to_scrape)} pages scraped")
    
    async def scrape_devdocs(self):
        """Scrape DevDocs documentation list."""
        config = CORPORATE_TARGETS["devdocs"]
        async with aiohttp.ClientSession() as session:
            content = await self.fetch(session, config["docs_json"])
            if content:
                docs = json.loads(content)
                logger.info(f"[Corporate] DevDocs: {len(docs)} documentation sets available")
                
                for doc in docs[:50]:  # Limit to first 50
                    slug = doc.get("slug", "")
                    url = f"https://devdocs.io/{slug}/"
                    
                    html = await self.fetch(session, url)
                    if html:
                        text = self._extract_text_from_html(html, url)
                        if text:
                            result = ScraperResult(
                                source="devdocs",
                                url=url,
                                content=text,
                                content_type="text/markdown",
                                metadata={"slug": slug, "name": doc.get("name", slug)}
                            )
                            self.save_document(result)
                    
                    await asyncio.sleep(0.2)
    
    async def scrape_readthedocs(self):
        """Scrape ReadTheDocs top projects."""
        config = CORPORATE_TARGETS["readthedocs"]
        top_projects = [
            "python", "django", "flask", "requests", "numpy", "pandas",
            "matplotlib", "scipy", "scikit-learn", "pytorch", "tensorflow",
            "kubernetes", "docker-compose", "ansible", "celery",
            "sphinx", "mkdocs", "pip", "jupyter",
        ]
        
        async with aiohttp.ClientSession() as session:
            for project in top_projects:
                url = f"https://{project}.readthedocs.io/en/latest/"
                html = await self.fetch(session, url)
                if html:
                    text = self._extract_text_from_html(html, url)
                    if text:
                        result = ScraperResult(
                            source="readthedocs",
                            url=url,
                            content=text,
                            content_type="text/markdown",
                            metadata={"project": project}
                        )
                        self.save_document(result)
                
                # Also get docs.json for sitemap
                sitemap_url = f"https://{project}.readthedocs.io/sitemap.xml"
                sitemap_urls = await self.fetch_sitemap(sitemap_url)
                for su in sitemap_urls[:200]:  # Limit per project
                    await self.scrape_url(session, su, "readthedocs")
                
                await asyncio.sleep(0.5)
    
    async def run(self):
        """Run all corporate scrapers."""
        logger.info(f"[Corporate] === CORPORATE DOC APOCALYPSE ===")
        logger.info(f"[Corporate] {len(CORPORATE_TARGETS)} targets configured")
        
        for source_key, config in CORPORATE_TARGETS.items():
            try:
                if source_key == "devdocs":
                    await self.scrape_devdocs()
                elif source_key == "readthedocs":
                    await self.scrape_readthedocs()
                else:
                    await self.scrape_source(source_key, config)
                
                self.save_stats()
                self._save_visited()
                self.print_stats()
            except Exception as e:
                logger.error(f"[Corporate] Error scraping {source_key}: {e}")
                continue
        
        self.save_stats()
        self._save_visited()
        self._save_seen()
        self.print_stats()
        logger.info(f"[Corporate] DONE.")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/corporate.log"),
            logging.StreamHandler()
        ]
    )
    
    scraper = CorporateScraper(max_concurrent=6)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
