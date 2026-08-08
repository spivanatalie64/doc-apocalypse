#!/usr/bin/env python3
"""
Ingest locally cloned sacred text repos into doc-apocalypse format.
Processes all JSON files from cloned repos and saves as Zstandard-compressed docs.
Also fetches remaining texts from Project Gutenberg.
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import time
import zstandard as zstd
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("sacred.ingest")

OUTPUT_DIR = Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load seen hashes
seen_file = OUTPUT_DIR / ".seen_hashes.json"
seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))
logger.info(f"Loaded {len(seen)} seen hashes")

stats = {"scraped": 0, "skipped": 0, "errors": 0, "bytes": 0}


def save_document(source_key: str, url: str, content: str,
                  content_type: str = "text/plain",
                  metadata: dict = None):
    """Save with dedup + Zstandard compression."""
    global stats
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    if sha256 in seen:
        stats["skipped"] += 1
        return False
    
    seen.add(sha256)
    
    doc = {
        "sha256": sha256,
        "source": source_key,
        "url": url,
        "content_type": content_type,
        "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    
    cctx = zstd.ZstdCompressor(level=3)
    compressed = cctx.compress(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
    
    date_dir = OUTPUT_DIR / time.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    
    fpath = date_dir / f"{sha256[:16]}.json.zst"
    with open(fpath, "wb") as f:
        f.write(compressed)
    
    stats["scraped"] += 1
    stats["bytes"] += len(compressed)
    return True


def process_bible_repo(repo_path: Path, version: str, tradition: str, language: str):
    """Process a Bible repo with per-book JSON files."""
    logger.info(f"Processing {version} Bible from {repo_path}")
    
    for f in sorted(repo_path.glob("*.json")):
        if f.name in ("Books.json", "README.md"):
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            
            book_name = f.stem
            text = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Save raw JSON
            save_document(
                f"bible/{version}/{book_name}",
                url=f"file://{f}",
                content=text,
                content_type="application/json",
                metadata={
                    "version": version,
                    "tradition": tradition,
                    "language": language,
                    "book": book_name,
                }
            )
            
            # Save readable version
            readable_lines = [f"# {book_name} ({version})", ""]
            for chapter_num, chapter in enumerate(data.get("chapters", []), 1):
                readable_lines.append(f"\n## Chapter {chapter_num}\n")
                for verse_num, verse in enumerate(chapter, 1):
                    readable_lines.append(f"{verse_num}. {verse}")
            
            readable = "\n".join(readable_lines)
            save_document(
                f"bible/{version}/{book_name}_readable",
                url=f"file://{f}#readable",
                content=readable,
                content_type="text/plain",
                metadata={
                    "version": version,
                    "tradition": tradition,
                    "language": language,
                    "book": book_name,
                    "format": "readable",
                }
            )
        except Exception as e:
            stats["errors"] += 1
            logger.warning(f"Error processing {f}: {e}")


def process_quran_repo(repo_path: Path):
    """Process Quran JSON files."""
    logger.info(f"Processing Quran translations from {repo_path}")
    
    lang_names = {
        "ar": ("Arabic", "ar"),
        "en.ahmedali": ("Ahmed Ali English", "en"),
        "en.arberry": ("Arberry English", "en"),
        "en.daryabadi": ("Daryabadi English", "en"),
        "en.hilali": ("Hilali-Khan English", "en"),
        "en.khan": ("Muhsin Khan English", "en"),
        "en.maududi": ("Maududi English", "en"),
        "en.pickthall": ("Pickthall English", "en"),
        "en.sahih": ("Sahih International English", "en"),
        "en.shakir": ("Shakir English", "en"),
        "en.yusufali": ("Yusuf Ali English", "en"),
    }
    
    for f in sorted(repo_path.glob("*.json")):
        stem = f.stem
        try:
            if f.stat().st_size < 100:  # Too small, probably a redirect/error
                logger.warning(f"Skipping {stem} (too small: {f.stat().st_size} bytes)")
                continue
            
            with open(f) as fh:
                data = json.load(fh)
            
            display_name, lang = lang_names.get(stem, (stem, stem))
            
            # Save raw JSON
            text = json.dumps(data, indent=2, ensure_ascii=False)
            save_document(
                f"quran/{stem}",
                url=f"file://{f}",
                content=text,
                content_type="application/json",
                metadata={
                    "translation": display_name,
                    "language": lang,
                    "tradition": "Islam",
                }
            )
            
            # Save readable
            readable_lines = [f"# Quran — {display_name}", ""]
            for surah in data:
                if isinstance(surah, dict):
                    num = surah.get("surah", surah.get("chapter", ""))
                    name = surah.get("name", surah.get("englishName", ""))
                    readable_lines.append(f"\n## {num}. {name}\n")
                    verses = surah.get("verses", surah.get("ayahs", []))
                    for v in verses:
                        if isinstance(v, dict):
                            readable_lines.append(f"{v.get('id', v.get('number', ''))}. {v.get('text', '')}")
                        elif isinstance(v, str):
                            idx = verses.index(v) + 1
                            readable_lines.append(f"{idx}. {v}")
            
            readable = "\n".join(readable_lines)
            save_document(
                f"quran/{stem}_readable",
                url=f"file://{f}#readable",
                content=readable,
                content_type="text/plain",
                metadata={
                    "translation": display_name,
                    "language": lang,
                    "tradition": "Islam",
                    "format": "readable",
                }
            )
        except Exception as e:
            stats["errors"] += 1
            logger.warning(f"Error processing Quran {f}: {e}")


def process_vedic_json(repo_path: Path):
    """Process Vedic texts JSON."""
    logger.info(f"Processing Vedic texts from {repo_path}")
    
    for f in sorted(repo_path.glob("*.json")):
        try:
            if f.stat().st_size < 100:
                logger.warning(f"Skipping {f.stem} (too small)")
                continue
            
            with open(f) as fh:
                data = json.load(fh)
            
            text = json.dumps(data, indent=2, ensure_ascii=False)
            save_document(
                f"hindu/{f.stem}",
                url=f"file://{f}",
                content=text,
                content_type="application/json",
                metadata={
                    "text": f.stem,
                    "tradition": "Hinduism",
                }
            )
        except Exception as e:
            stats["errors"] += 1
            logger.warning(f"Error processing {f}: {e}")


def process_hebrew_repo(repo_path: Path):
    """Process Hebrew Bible."""
    logger.info(f"Processing Hebrew Bible from {repo_path}")
    
    # The rawData directory has the actual JSON
    raw_dir = repo_path / "rawData"
    if raw_dir.exists():
        for f in sorted(raw_dir.glob("*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                
                text = json.dumps(data, indent=2, ensure_ascii=False)
                save_document(
                    f"hebrew_bible/{f.stem}",
                    url=f"file://{f}",
                    content=text,
                    content_type="application/json",
                    metadata={
                        "book": f.stem,
                        "tradition": "Judaism",
                        "language": "he",
                    }
                )
            except Exception as e:
                stats["errors"] += 1
                logger.warning(f"Error processing {f}: {e}")


GUTENBERG_TEXTS = [
    # These are confirmed working Gutenberg IDs
    ("gutenberg/bible_web", "Bible (World English Bible)", "https://www.gutenberg.org/ebooks/8294.txt.utf-8", {"tradition": "Christianity", "language": "en"}),
    ("gutenberg/bible_vulgate", "Bible (Latin Vulgate)", "https://www.gutenberg.org/ebooks/1581.txt.utf-8", {"tradition": "Christianity", "language": "la"}),
    ("gutenberg/septuagint", "Septuagint (Greek OT)", "https://www.gutenberg.org/ebooks/71567.txt.utf-8", {"tradition": "Christianity", "language": "grc"}),
    ("gutenberg/greek_nt", "Greek NT (Tischendorf)", "https://www.gutenberg.org/ebooks/71455.txt.utf-8", {"tradition": "Christianity", "language": "grc"}),
    ("gutenberg/bhagavad_gita", "Bhagavad Gita", "https://www.gutenberg.org/ebooks/2388.txt.utf-8", {"tradition": "Hinduism", "language": "en"}),
    ("gutenberg/dhammapada", "Dhammapada", "https://www.gutenberg.org/ebooks/2017.txt.utf-8", {"tradition": "Buddhism", "language": "en"}),
    ("gutenberg/tibetan_book_dead", "Tibetan Book of the Dead", "https://www.gutenberg.org/ebooks/64966.txt.utf-8", {"tradition": "Buddhism", "language": "en"}),
    ("gutenberg/tao_te_ching", "Tao Te Ching", "https://www.gutenberg.org/ebooks/216.txt.utf-8", {"tradition": "Taoism", "language": "en"}),
    ("gutenberg/zhuangzi", "Zhuangzi", "https://www.gutenberg.org/ebooks/71388.txt.utf-8", {"tradition": "Taoism", "language": "en"}),
    ("gutenberg/i_ching", "I Ching", "https://www.gutenberg.org/ebooks/18189.txt.utf-8", {"tradition": "Taoism/Confucianism", "language": "en"}),
    ("gutenberg/analects", "Analects of Confucius", "https://www.gutenberg.org/ebooks/3330.txt.utf-8", {"tradition": "Confucianism", "language": "en"}),
    ("gutenberg/upanishads", "Principal Upanishads", "https://www.gutenberg.org/ebooks/71812.txt.utf-8", {"tradition": "Hinduism", "language": "en"}),
    ("gutenberg/nag_hammadi", "Nag Hammadi Library", "https://www.gutenberg.org/ebooks/67610.txt.utf-8", {"tradition": "Gnosticism", "language": "en"}),
    ("gutenberg/dead_sea_scrolls", "Dead Sea Scrolls", "https://www.gutenberg.org/ebooks/56336.txt.utf-8", {"tradition": "Judaism", "language": "en"}),
    ("gutenberg/torah", "Torah (JPS)", "https://www.gutenberg.org/ebooks/7171.txt.utf-8", {"tradition": "Judaism", "language": "en"}),
    ("gutenberg/talmud", "Talmud (Soncino)", "https://www.gutenberg.org/ebooks/21039.txt.utf-8", {"tradition": "Judaism", "language": "en"}),
    ("gutenberg/zohar", "Zohar", "https://www.gutenberg.org/ebooks/4109.txt.utf-8", {"tradition": "Kabbalah", "language": "en"}),
    ("gutenberg/mishnah", "Mishnah", "https://www.gutenberg.org/ebooks/10882.txt.utf-8", {"tradition": "Judaism", "language": "en"}),
    ("gutenberg/book_of_mormon", "Book of Mormon", "https://www.gutenberg.org/ebooks/17.txt.utf-8", {"tradition": "Mormonism", "language": "en"}),
    ("gutenberg/doctrine_covenants", "Doctrine and Covenants", "https://www.gutenberg.org/ebooks/18.txt.utf-8", {"tradition": "Mormonism", "language": "en"}),
    ("gutenberg/pearl_great_price", "Pearl of Great Price", "https://www.gutenberg.org/ebooks/19.txt.utf-8", {"tradition": "Mormonism", "language": "en"}),
    ("gutenberg/iliad", "Homer - Iliad", "https://www.gutenberg.org/ebooks/6130.txt.utf-8", {"tradition": "Greek Mythology", "language": "en"}),
    ("gutenberg/odyssey", "Homer - Odyssey", "https://www.gutenberg.org/ebooks/1727.txt.utf-8", {"tradition": "Greek Mythology", "language": "en"}),
    ("gutenberg/city_of_god", "City of God (Augustine)", "https://www.gutenberg.org/ebooks/1063.txt.utf-8", {"tradition": "Christianity", "language": "en"}),
    ("gutenberg/confessions", "Confessions (Augustine)", "https://www.gutenberg.org/ebooks/3296.txt.utf-8", {"tradition": "Christianity", "language": "en"}),
    ("gutenberg/summa", "Summa Theologica (Aquinas)", "https://www.gutenberg.org/ebooks/17611.txt.utf-8", {"tradition": "Christianity", "language": "en"}),
    ("gutenberg/meditations", "Meditations (Marcus Aurelius)", "https://www.gutenberg.org/ebooks/2680.txt.utf-8", {"tradition": "Stoicism", "language": "en"}),
    ("gutenberg/enchiridion", "Enchiridion (Epictetus)", "https://www.gutenberg.org/ebooks/45109.txt.utf-8", {"tradition": "Stoicism", "language": "en"}),
    ("gutenberg/didache", "Didache", "https://www.gutenberg.org/ebooks/44985.txt.utf-8", {"tradition": "Christianity", "language": "en"}),
    ("gutenberg/guru_granth", "Guru Granth Sahib", "https://www.gutenberg.org/ebooks/17980.txt.utf-8", {"tradition": "Sikhism", "language": "en"}),
    ("gutenberg/poetic_edda", "Poetic Edda", "https://www.gutenberg.org/ebooks/68526.txt.utf-8", {"tradition": "Norse Paganism", "language": "en"}),
    ("gutenberg/egyptian_book_dead", "Egyptian Book of the Dead (Budge)", "https://www.gutenberg.org/ebooks/7141.txt.utf-8", {"tradition": "Egyptian Mythology", "language": "en"}),
]


async def fetch_gutenberg(session, key, name, url, metadata):
    """Fetch a text from Project Gutenberg."""
    logger.info(f"Fetching: {name}")
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 1000:
                        # Strip Gutenberg headers/footers
                        start_marker = "*** START OF"
                        end_marker = "*** END OF"
                        start_idx = text.find(start_marker)
                        end_idx = text.find(end_marker)
                        if start_idx >= 0:
                            text = text[start_idx + len(start_marker):]
                        if end_idx >= 0:
                            text = text[:end_idx]
                        
                        save_document(
                            key,
                            url=url,
                            content=text.strip(),
                            content_type="text/plain",
                            metadata={"name": name, **metadata}
                        )
                        return True
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {name}: {e}")
            await asyncio.sleep(2 ** attempt)
    return False


async def fetch_all_gutenberg():
    """Fetch all Gutenberg texts."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Fetching {len(GUTENBERG_TEXTS)} Gutenberg texts...")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for key, name, url, metadata in GUTENBERG_TEXTS:
            tasks.append(fetch_gutenberg(session, key, name, url, metadata))
            if len(tasks) >= 5:
                await asyncio.gather(*tasks)
                tasks = []
                # Save progress
                with open(seen_file, "w") as f:
                    json.dump(list(seen), f)
                logger.info(f"Progress: {stats['scraped']} scraped, {stats['skipped']} skipped, {stats['errors']} errors, {stats['bytes']/1024/1024:.1f} MB")
        
        if tasks:
            await asyncio.gather(*tasks)


def main():
    repo_base = Path("/tmp/sacred_repos")
    
    # Phase 1: Process local repos
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 1: Process local clones")
    
    # KJV Bible
    kjv_path = repo_base / "Bible-kjv"
    if kjv_path.exists():
        process_bible_repo(kjv_path, "KJV", "Christianity", "en")
    
    # NIV Bible
    niv_path = repo_base / "Bible-niv"
    if niv_path.exists():
        process_bible_repo(niv_path, "NIV", "Christianity", "en")
    
    # Spanish Bible
    spanish_path = repo_base / "Reina-Valera"
    if spanish_path.exists():
        process_bible_repo(spanish_path, "Reina-Valera", "Christianity", "es")
    
    # Hebrew Bible
    hebrew_path = repo_base / "hebrewBibleJSON"
    if hebrew_path.exists():
        process_hebrew_repo(hebrew_path)
    
    # Quran
    quran_path = repo_base / "quran-json"
    if quran_path.exists():
        process_quran_repo(quran_path)
    
    # Vedic
    vedic_path = repo_base / "vedic-json"
    if vedic_path.exists():
        process_vedic_json(vedic_path)
    
    # Save progress
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)
    logger.info(f"Phase 1 complete: {stats['scraped']} scraped, {stats['bytes']/1024/1024:.1f} MB")
    
    # Phase 2: Fetch Gutenberg texts
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 2: Fetch Gutenberg texts")
    asyncio.run(fetch_all_gutenberg())
    
    # Final save
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)
    
    stats_file = OUTPUT_DIR / ".stats.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SACRED TEXT HARVEST COMPLETE")
    print(f"{'='*60}")
    print(f"  Scraped: {stats['scraped']}")
    print(f"  Skipped (dedup): {stats['skipped']}")
    print(f"  Errors: {stats['errors']}")
    print(f"  Total size: {stats['bytes'] / 1024 / 1024:.1f} MB")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
