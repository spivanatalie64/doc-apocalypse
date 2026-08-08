#!/usr/bin/env python3
"""
Sacred Text Harvester — Eilatan's Heresy Edition 🖤

Pulls every major religious text from across the internet:
  - Bible (15+ translations, original languages)
  - Quran (multiple translations + Arabic)
  - Torah + Talmud + Zohar + Kabbalah
  - Vedas, Upanishads, Bhagavad Gita, Puranas
  - Pali Canon, Tibetan Kangyur, Mahayana Sutras
  - Tao Te Ching, Zhuangzi, Analects
  - Gnostic Gospels, Nag Hammadi, Dead Sea Scrolls
  - Eddas, Greek mythology primary sources, Pyramid Texts
  - Baha'i, Mormon, Sikh, Jain, Zoroastrian scriptures
  - Creeds, catechisms, ecumenical councils

Sources:
  - Project Gutenberg (public domain texts)
  - Internet Sacred Text Archive (sacred-texts.com)
  - Wikisource / Wikipedia
  - GitHub repos (bible-translations, quran-data, etc.)
  - Direct API sources (bible-api.com, quran.com API)
  - SuttaCentral (Buddhist canon)
  - GRETIL (Indic texts)
  - Perseus Project (Greek/Latin classics)

Storage: Same Zstandard JSON format as the doc apocalypse.
"""

import asyncio
import gzip
import hashlib
import json
import logging
import os
import re
import subprocess
import time
import zstandard as zstd
from pathlib import Path
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup as BS4  # renamed to avoid confusion with god lol

logger = logging.getLogger("doc-apocalypse.sacred")


# ── DATA SOURCES ─────────────────────────────────────────────

SOURCES = {
    # ── BIBLE ────────────────────────────────────────────────
    "bible_kjv": {
        "name": "Bible (King James Version)",
        "url": "https://raw.githubusercontent.com/aruljohn/Bible-kjv/master/json/Genesis.json",
        "source_type": "github_json",
        "language": "en",
        "tradition": "Christianity",
        "repo_url": "https://api.github.com/repos/aruljohn/Bible-kjv/contents/json",
    },
    "bible_niv": {
        "name": "Bible (New International Version)",
        "url": "https://raw.githubusercontent.com/aruljohn/Bible-niv/master/json/Genesis.json",
        "source_type": "github_json",
        "language": "en",
        "tradition": "Christianity",
        "repo_url": "https://api.github.com/repos/aruljohn/Bible-niv/contents/json",
    },
    "bible_vulgate": {
        "name": "Bible (Latin Vulgate)",
        "url": "https://www.gutenberg.org/ebooks/1581.txt.utf-8",
        "source_type": "gutenberg",
        "language": "la",
        "tradition": "Christianity",
    },
    "bible_lxx": {
        "name": "Septuagint (Greek OT)",
        "url": "https://www.gutenberg.org/ebooks/71567.txt.utf-8",
        "source_type": "gutenberg",
        "language": "grc",
        "tradition": "Christianity",
    },
    "bible_tischendorf": {
        "name": "Greek NT (Tischendorf)",
        "url": "https://www.gutenberg.org/ebooks/71455.txt.utf-8",
        "source_type": "gutenberg",
        "language": "grc",
        "tradition": "Christianity",
    },
    "bible_web": {
        "name": "Bible (World English Bible)",
        "url": "https://www.gutenberg.org/ebooks/8294.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Christianity",
    },
    "bible_wlc": {
        "name": "Hebrew OT (Westminster Leningrad)",
        "url": "https://raw.githubusercontent.com/talolard/hebrewBibleJSON/master/books_json/Genesis.json",
        "source_type": "github_json",
        "language": "he",
        "tradition": "Judaism",
        "repo_url": "https://api.github.com/repos/talolard/hebrewBibleJSON/contents/books_json",
    },
    
    # ── QURAN ────────────────────────────────────────────────
    "quran_arabic": {
        "name": "Quran (Arabic)",
        "url": "https://raw.githubusercontent.com/fawazahmed0/quran-api/main/ar.json",
        "source_type": "github_json",
        "language": "ar",
        "tradition": "Islam",
    },
    "quran_yusuf_ali": {
        "name": "Quran (Yusuf Ali English)",
        "url": "https://raw.githubusercontent.com/fawazahmed0/quran-api/main/en.yusufali.json",
        "source_type": "github_json",
        "language": "en",
        "tradition": "Islam",
    },
    "quran_pickthall": {
        "name": "Quran (Pickthall English)",
        "url": "https://raw.githubusercontent.com/fawazahmed0/quran-api/main/en.pickthall.json",
        "source_type": "github_json",
        "language": "en",
        "tradition": "Islam",
    },
    "quran_sahih": {
        "name": "Quran (Sahih International)",
        "url": "https://raw.githubusercontent.com/fawazahmed0/quran-api/main/en.sahih.json",
        "source_type": "github_json",
        "language": "en",
        "tradition": "Islam",
    },
    
    # ── HINDU ────────────────────────────────────────────────
    "bhagavad_gita": {
        "name": "Bhagavad Gita",
        "url": "https://www.gutenberg.org/ebooks/2388.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Hinduism",
    },
    "rig_veda": {
        "name": "Rig Veda (English translation)",
        "url": "https://sacred-texts.com/hin/rigveda/rvi01.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Hinduism",
        "base_url": "https://sacred-texts.com/hin/rigveda/",
    },
    "upanishads": {
        "name": "Principal Upanishads",
        "url": "https://www.gutenberg.org/ebooks/71812.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Hinduism",
    },
    "yoga_sutras": {
        "name": "Yoga Sutras of Patanjali",
        "url": "https://sacred-texts.com/hin/yogasutr.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Hinduism",
    },
    
    # ── BUDDHIST ─────────────────────────────────────────────
    "dhammapada": {
        "name": "Dhammapada (Pali + English)",
        "url": "https://www.gutenberg.org/ebooks/2017.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Buddhism",
    },
    "heart_sutra": {
        "name": "Heart Sutra",
        "url": "https://raw.githubusercontent.com/btashton/sutras/master/sutras/heart_sutra.json",
        "source_type": "github_json",
        "language": "en+zh",
        "tradition": "Buddhism",
    },
    "tibetan_book_dead": {
        "name": "Tibetan Book of the Dead (Bardo Thodol)",
        "url": "https://www.gutenberg.org/ebooks/64966.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Buddhism",
    },
    
    # ── TAOIST ───────────────────────────────────────────────
    "tao_te_ching": {
        "name": "Tao Te Ching",
        "url": "https://www.gutenberg.org/ebooks/216.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Taoism",
    },
    "zhuangzi": {
        "name": "Zhuangzi (Chuang Tzu)",
        "url": "https://www.gutenberg.org/ebooks/71388.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Taoism",
    },
    "i_ching": {
        "name": "I Ching (Yi Jing)",
        "url": "https://www.gutenberg.org/ebooks/18189.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Taoism/Confucianism",
    },
    
    # ── CONFUCIAN ─────────────────────────────────────────────
    "analects": {
        "name": "Analects of Confucius",
        "url": "https://sacred-texts.com/cfu/conf1.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Confucianism",
    },
    "mencius": {
        "name": "Mencius",
        "url": "https://sacred-texts.com/cfu/menc/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Confucianism",
    },
    
    # ── GNOSTIC / APOCRYPHAL ──────────────────────────────────
    "nag_hammadi": {
        "name": "Nag Hammadi Library",
        "url": "https://www.gutenberg.org/ebooks/67610.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Gnosticism",
    },
    "dead_sea_scrolls": {
        "name": "Dead Sea Scrolls",
        "url": "https://www.gutenberg.org/ebooks/56336.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Judaism",
    },
    "didache": {
        "name": "Didache",
        "url": "https://www.gutenberg.org/ebooks/44985.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Christianity",
    },
    "shepherd_of_hermas": {
        "name": "Shepherd of Hermas",
        "url": "https://www.gutenberg.org/ebooks/68526.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Christianity",
    },
    
    # ── NORSE ─────────────────────────────────────────────────
    "poetic_edda": {
        "name": "Poetic Edda (Codex Regius)",
        "url": "https://sacred-texts.com/neu/poe/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Norse Paganism",
    },
    "prose_edda": {
        "name": "Prose Edda (Snorri Sturluson)",
        "url": "https://sacred-texts.com/neu/pre/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Norse Paganism",
    },
    
    # ── GREEK / ROMAN ─────────────────────────────────────────
    "theogony": {
        "name": "Hesiod - Theogony",
        "url": "https://sacred-texts.com/cla/hesiod/theogony.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Greek Mythology",
    },
    "iliad": {
        "name": "Homer - Iliad",
        "url": "https://www.gutenberg.org/ebooks/6130.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Greek Mythology",
    },
    "odyssey": {
        "name": "Homer - Odyssey",
        "url": "https://www.gutenberg.org/ebooks/1727.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Greek Mythology",
    },
    
    # ── EGYPTIAN ──────────────────────────────────────────────
    "egyptian_book_of_the_dead": {
        "name": "Egyptian Book of the Dead",
        "url": "https://sacred-texts.com/egy/ebod/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Egyptian Mythology",
    },
    "pyramid_texts": {
        "name": "Pyramid Texts",
        "url": "https://sacred-texts.com/egy/pyt/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Egyptian Mythology",
    },
    
    # ── JEWISH ────────────────────────────────────────────────
    "torah": {
        "name": "Torah (Jewish Publication Society)",
        "url": "https://www.gutenberg.org/ebooks/7171.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Judaism",
    },
    "talmud_bavli": {
        "name": "Talmud",
        "url": "https://www.gutenberg.org/ebooks/21039.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Judaism",
    },
    "zohar": {
        "name": "Zohar (Kabbalah)",
        "url": "https://www.gutenberg.org/ebooks/4109.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Kabbalah",
    },
    "mishnah": {
        "name": "Mishnah",
        "url": "https://www.gutenberg.org/ebooks/10882.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Judaism",
    },
    
    # ── SIKH ──────────────────────────────────────────────────
    "guru_granth": {
        "name": "Guru Granth Sahib",
        "url": "https://www.gutenberg.org/ebooks/17980.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Sikhism",
    },
    
    # ── MORMON ────────────────────────────────────────────────
    "book_of_mormon": {
        "name": "Book of Mormon",
        "url": "https://www.gutenberg.org/ebooks/17.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Mormonism",
    },
    "dc_mormon": {
        "name": "Doctrine and Covenants",
        "url": "https://www.gutenberg.org/ebooks/18.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Mormonism",
    },
    "pearl_great_price": {
        "name": "Pearl of Great Price",
        "url": "https://www.gutenberg.org/ebooks/19.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Mormonism",
    },
    
    # ── ZOROASTRIAN ───────────────────────────────────────────
    "avesta": {
        "name": "Avesta (Zoroastrian scriptures)",
        "url": "https://sacred-texts.com/zor/sbe23/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Zoroastrianism",
    },
    "gathas": {
        "name": "Gathas (Hymns of Zarathustra)",
        "url": "https://sacred-texts.com/zor/sbe31/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Zoroastrianism",
    },
    
    # ── BAHA'I ────────────────────────────────────────────────
    "kitab_i_aqdas": {
        "name": "Kitab-i-Aqdas (Most Holy Book)",
        "url": "https://www.gutenberg.org/ebooks/18800.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Baha'i",
    },
    "kitab_i_iqan": {
        "name": "Kitab-i-Iqan (Book of Certitude)",
        "url": "https://www.gutenberg.org/ebooks/24215.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Baha'i",
    },
    "hidden_words": {
        "name": "Hidden Words of Baha'u'llah",
        "url": "https://www.gutenberg.org/ebooks/6157.txt.utf-8",
        "source_type": "gutenberg",
        "language": "en",
        "tradition": "Baha'i",
    },
    
    # ── JAIN ──────────────────────────────────────────────────
    "akaram_sutras": {
        "name": "Akaram Sutras (Jain Agamas)",
        "url": "https://sacred-texts.com/jai/sbe22/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Jainism",
    },
    "tattvartha_sutra": {
        "name": "Tattvartha Sutra",
        "url": "https://sacred-texts.com/jai/tattvartha.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Jainism",
    },
    
    # ── SHINTO ────────────────────────────────────────────────
    "kojiki": {
        "name": "Kojiki (Records of Ancient Matters)",
        "url": "https://sacred-texts.com/shi/kj/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Shinto",
    },
    "nihongi": {
        "name": "Nihongi (Chronicles of Japan)",
        "url": "https://sacred-texts.com/shi/nihon1.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Shinto",
    },
    
    # ── HERMETIC / OCCULT ─────────────────────────────────────
    "corpus_hermeticum": {
        "name": "Corpus Hermeticum",
        "url": "https://sacred-texts.com/eso/herm/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Hermeticism",
    },
    "emerald_tablet": {
        "name": "Emerald Tablet of Hermes",
        "url": "https://sacred-texts.com/alc/emerald.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Hermeticism",
    },
    "picatrix": {
        "name": "Picatrix (Ghayat al-Hakim)",
        "url": "https://sacred-texts.com/grim/picatrix/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Occult",
    },
    "key_of_solomon": {
        "name": "Key of Solomon",
        "url": "https://sacred-texts.com/grim/kos/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Occult",
    },
    "lesser_key_of_solomon": {
        "name": "Lesser Key of Solomon (Ars Goetia)",
        "url": "https://sacred-texts.com/grim/lks/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Occult",
    },
    
    # ── CREEDS / COUNCILS ─────────────────────────────────────
    "ecumenical_councils": {
        "name": "Ecumenical Councils (Nicene, Chalcedon, etc.)",
        "url": "https://sacred-texts.com/chr/councils/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Christianity",
    },
    "athanasian_creed": {
        "name": "Athanasian Creed",
        "url": "https://sacred-texts.com/chr/athacred.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Christianity",
    },
    
    # ── CELTIC ────────────────────────────────────────────────
    "mabinogion": {
        "name": "Mabinogion (Welsh mythology)",
        "url": "https://sacred-texts.com/neu/celt/mab/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Celtic Mythology",
    },
    "cuchulainn": {
        "name": "Cuchulainn (Ulster Cycle)",
        "url": "https://sacred-texts.com/neu/celt/cuch/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Celtic Mythology",
    },
    
    # ── CAODAISM ──────────────────────────────────────────────
    "caodai": {
        "name": "Caodai Scriptures",
        "url": "https://sacred-texts.com/tao/caodaism.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Caodaism",
    },
    
    # ── NATIVE AMERICAN ───────────────────────────────────────
    "popol_vuh": {
        "name": "Popol Vuh (Mayan creation myth)",
        "url": "https://sacred-texts.com/nam/maya/popol/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Mayan",
    },
    "navajo_ceremonials": {
        "name": "Navajo Ceremonials",
        "url": "https://sacred-texts.com/nam/navajo.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Native American",
    },
    
    # ── WICCA / NEOPAGAN ──────────────────────────────────────
    "wiccan_rede": {
        "name": "Wiccan Rede + Charge of the Goddess",
        "url": "https://sacred-texts.com/pag/wicca.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Wicca",
    },
    "arda_viraf": {
        "name": "Arda Viraf Namak",
        "url": "https://sacred-texts.com/zor/av/index.htm",
        "source_type": "scrape_sacred_texts",
        "language": "en",
        "tradition": "Zoroastrianism",
    },
}


# ── MORE SOURCES (additional free-text sources) ──────────────

ADDITIONAL_GITHUB = [
    # Apocrypha
    "https://raw.githubusercontent.com/openscriptures/apocrypha/master/apocrypha.json",
    # Mormon/Talmud additional
    "https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/json/Midrash/Tanhuma.json",
    "https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/json/Midrash/Rabbah.json",
    "https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/json/Tosefta.json",
    # Bible commentaries
    "https://raw.githubusercontent.com/openscriptures/commentary/master/commentary.json",
    # Buddhist
    "https://raw.githubusercontent.com/suttacentral/sc-data/main/sc_bilara_data/root/pli/sutta/sn/root-pli-sn.json",
    "https://raw.githubusercontent.com/suttacentral/sc-data/main/sc_bilara_data/root/pli/sutta/mn/root-pli-mn.json",
    "https://raw.githubusercontent.com/suttacentral/sc-data/main/sc_bilara_data/root/pli/sutta/dn/root-pli-dn.json",
    "https://raw.githubusercontent.com/suttacentral/sc-data/main/sc_bilara_data/root/pli/sutta/an/root-pli-an.json",
    "https://raw.githubusercontent.com/suttacentral/sc-data/main/sc_bilara_data/root/pli/vinaya/root-pli-vi.json",
    # Hindu
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/rigveda.json",
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/yajurveda.json",
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/samaveda.json",
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/atharvaveda.json",
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/upanishads.json",
    "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/puranas.json",
    # Jain
    "https://raw.githubusercontent.com/jain-library/jain-agama/master/agama.json",
]

ADDITIONAL_GUTENBERG = [
    "https://www.gutenberg.org/ebooks/19337.txt.utf-8",  # Golden Bough (Frazer)
    "https://www.gutenberg.org/ebooks/17405.txt.utf-8",  # Varieties of Religious Experience (James)
    "https://www.gutenberg.org/ebooks/1063.txt.utf-8",   # City of God (Augustine)
    "https://www.gutenberg.org/ebooks/3296.txt.utf-8",   # Confessions (Augustine)
    "https://www.gutenberg.org/ebooks/1581.txt.utf-8",   # Summa Theologica (Aquinas)
    "https://www.gutenberg.org/ebooks/21039.txt.utf-8",  # Imitation of Christ (Kempis)
    "https://www.gutenberg.org/ebooks/2698.txt.utf-8",   # Dark Night of the Soul (John of the Cross)
    "https://www.gutenberg.org/ebooks/21655.txt.utf-8",  # Interior Castle (Teresa of Avila)
    "https://www.gutenberg.org/ebooks/37117.txt.utf-8",  # Upanishads (trans. Max Müller)
    "https://www.gutenberg.org/ebooks/64317.txt.utf-8",  # Dhammapada (trans. Max Müller)
    "https://www.gutenberg.org/ebooks/5000.txt.utf-8",   # Tao Te Ching (trans. Legge)
    "https://www.gutenberg.org/ebooks/18800.txt.utf-8",  # Analects (trans. Legge)
    "https://www.gutenberg.org/ebooks/24215.txt.utf-8",  # Bhagavad Gita (trans. Telang)
    "https://www.gutenberg.org/ebooks/6157.txt.utf-8",   # Meditations (Marcus Aurelius)
    "https://www.gutenberg.org/ebooks/44985.txt.utf-8",  # Enchiridion (Epictetus)
    "https://www.gutenberg.org/ebooks/68526.txt.utf-8",  # Poetic Edda (trans. Bellows)
    "https://www.gutenberg.org/ebooks/17980.txt.utf-8",  # Egyptian Book of the Dead (Budge)
]


class SacredTextHarvester:
    """Harvests all major religious and sacred texts from the internet."""
    
    def __init__(self, data_dir: str = "/home/natalie/projects/doc-apocalypse/data/sacred_texts",
                 max_concurrent: int = 6):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_file = self.data_dir / ".seen_hashes.json"
        self.stats_file = self.data_dir / ".stats.json"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        self.seen = set()
        self.stats = {"scraped": 0, "skipped": 0, "errors": 0, "bytes": 0}
        
        self._load_seen()
    
    def _load_seen(self):
        if self.seen_file.exists():
            try:
                with open(self.seen_file) as f:
                    self.seen = set(json.load(f))
                logger.info(f"[Sacred] Loaded {len(self.seen)} seen hashes")
            except:
                pass
    
    def _save_seen(self):
        with open(self.seen_file, "w") as f:
            json.dump(list(self.seen), f)
    
    def _save_stats(self):
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)
    
    def save_document(self, source_key: str, url: str, content: str, 
                      content_type: str = "text/plain",
                      metadata: Optional[dict] = None) -> bool:
        """Save a sacred text document with dedup and compression."""
        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        
        if sha256 in self.seen:
            self.stats["skipped"] += 1
            return False
        
        self.seen.add(sha256)
        
        doc_data = {
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
        compressed = cctx.compress(json.dumps(doc_data, ensure_ascii=False).encode("utf-8"))
        
        date_dir = self.data_dir / time.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        fpath = date_dir / f"{sha256[:16]}.json.zst"
        with open(fpath, "wb") as f:
            f.write(compressed)
        
        self.stats["scraped"] += 1
        self.stats["bytes"] += len(compressed)
        
        return True
    
    async def fetch(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch a URL with rate limiting."""
        for attempt in range(3):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", "10"))
                        logger.warning(f"[Sacred] Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.warning(f"[Sacred] HTTP {resp.status}: {url}")
                        return None
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                logger.warning(f"[Sacred] Failed to fetch {url}: {e}")
                return None
        return None
    
    async def fetch_json(self, session: aiohttp.ClientSession, url: str) -> Optional[dict]:
        """Fetch and parse JSON from a URL."""
        text = await self.fetch(session, url)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.error(f"[Sacred] JSON parse error for {url}: {e}")
        return None
    
    def extract_text_sacred_texts(self, html: str, url: str) -> Optional[str]:
        """Extract clean text from sacred-texts.com HTML."""
        try:
            soup = BS4(html, "lxml")
            
            # Remove navigation cruft
            for tag in soup(["script", "style", "nav", "footer", "form", 
                           "table", "img", "iframe"]):
                tag.decompose()
            
            # Find main content - sacred-texts uses <blockquote> for the actual content
            content = soup.find("blockquote")
            if not content:
                # Fallback to body
                content = soup.body
            
            if not content:
                return None
            
            # Get title
            title = soup.title.string if soup.title else url
            title = title.strip()
            
            text = content.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            
            return f"# {title}\n\n{text}"
        except Exception as e:
            logger.debug(f"Error extracting {url}: {e}")
            return None
    
    async def process_github_json(self, session: aiohttp.ClientSession, 
                                   key: str, config: dict):
        """Process a GitHub JSON source (structured scripture data)."""
        logger.info(f"[Sacred] Processing {config['name']}...")
        
        # Handle multi-file repos (Bible books as separate files)
        repo_url = config.get("repo_url")
        if repo_url:
            logger.info(f"[Sacred] Fetching multi-file index from {repo_url}")
            files = await self.fetch_json(session, repo_url)
            if files and isinstance(files, list):
                all_data = {}
                for item in files:
                    if item.get("name", "").endswith(".json"):
                        fname = item["name"]
                        file_url = item["download_url"]
                        logger.info(f"[Sacred] Fetching {fname}...")
                        file_data = await self.fetch_json(session, file_url)
                        if file_data:
                            all_data[fname.replace(".json", "")] = file_data
                        await asyncio.sleep(0.2)
                
                if all_data:
                    text = json.dumps(all_data, indent=2, ensure_ascii=False)
                    self.save_document(
                        source_key=key,
                        url=config["url"],
                        content=text,
                        content_type="application/json",
                        metadata={
                            "name": config["name"],
                            "tradition": config.get("tradition", ""),
                            "language": config.get("language", ""),
                            "source_type": "github_json_multi",
                            "size_bytes": len(text),
                            "books": list(all_data.keys()),
                        }
                    )
                    
                    readable = self._json_to_readable(key, config, all_data)
                    if readable:
                        self.save_document(
                            source_key=f"{key}_readable",
                            url=config["url"],
                            content=readable,
                            content_type="text/plain; readable",
                            metadata={
                                "name": f"{config['name']} (Readable)",
                                "tradition": config.get("tradition", ""),
                                "language": config.get("language", ""),
                            }
                        )
                    return
        
        # Single file
        data = await self.fetch_json(session, config["url"])
        if not data:
            logger.warning(f"[Sacred] Failed to fetch {config['name']}")
            return
        
        # Flatten JSON into readable text
        text = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.save_document(
            source_key=key,
            url=config["url"],
            content=text,
            content_type="application/json",
            metadata={
                "name": config["name"],
                "tradition": config.get("tradition", ""),
                "language": config.get("language", ""),
                "source_type": "github_json",
                "size_bytes": len(text),
            }
        )
        
        # Also save a readable plaintext version by extracting just the text
        readable = self._json_to_readable(key, config, data)
        if readable:
            self.save_document(
                source_key=f"{key}_readable",
                url=config["url"],
                content=readable,
                content_type="text/plain; readable",
                metadata={
                    "name": f"{config['name']} (Readable)",
                    "tradition": config.get("tradition", ""),
                    "language": config.get("language", ""),
                    "source_type": "github_json_readable",
                }
            )
    
    def _json_to_readable(self, key: str, config: dict, data) -> Optional[str]:
        """Convert a structured JSON scripture into readable text."""
        lines = []
        lines.append(f"# {config['name']}")
        lines.append(f"Tradition: {config.get('tradition', 'Unknown')}")
        lines.append(f"Language: {config.get('language', 'Unknown')}")
        lines.append("")
        
        # Try to detect structure and flatten
        if isinstance(data, dict):
            # Bible structure: books -> chapters -> verses
            if any(k in str(data).lower() for k in ["chapter", "verse", "book"]):
                if "books" in data:
                    for book in data["books"]:
                        name = book.get("name", "")
                        chapters = book.get("chapters", book.get("verses", []))
                        lines.append(f"\n## {name}\n")
                        for i, chapter in enumerate(chapters):
                            if isinstance(chapter, list):
                                lines.append(f"\n### Chapter {i+1}\n")
                                for j, verse in enumerate(chapter):
                                    lines.append(f"{j+1}. {verse}")
                            elif isinstance(chapter, dict):
                                for vnum, vtext in chapter.items():
                                    lines.append(f"{vnum}. {vtext}")
                elif "chapters" in data:
                    for i, ch in enumerate(data["chapters"]):
                        lines.append(f"\n### Chapter {i+1}\n")
                        if isinstance(ch, dict):
                            for vnum, vtext in ch.items():
                                lines.append(f"{vnum}. {vtext}")
                        elif isinstance(ch, list):
                            for j, v in enumerate(ch):
                                lines.append(f"{j+1}. {v}")
                else:
                    # Flatten all nested strings
                    self._flatten_dict(data, lines, 0)
            
            # Quran structure: surahs -> ayahs
            elif "surahs" in data or "chapters" in data.get("data", {}):
                surahs = data.get("surahs", data.get("data", {}).get("surahs", []))
                if not surahs and "surah" in str(data)[:200]:
                    # Try flat structure
                    for surah_num, surah_data in data.items():
                        if isinstance(surah_data, dict):
                            name = surah_data.get("name", f"Surah {surah_num}")
                            lines.append(f"\n## {name}\n")
                            verses = surah_data.get("verses", surah_data.get("ayahs", []))
                            for v in verses:
                                if isinstance(v, dict):
                                    lines.append(f"{v.get('number', v.get('id', ''))}. {v.get('text', '')}")
                                else:
                                    lines.append(str(v))
                for s in surahs:
                    name = s.get("name", s.get("englishName", ""))
                    lines.append(f"\n## {name}\n")
                    verses = s.get("verses", s.get("ayahs", []))
                    for v in verses:
                        if isinstance(v, dict):
                            lines.append(f"{v.get('id', v.get('number', ''))}. {v.get('text', '')}")
                        else:
                            lines.append(str(v))
            
            # Talmud/Zohar: tractates -> pages
            elif "tractates" in data or "massechet" in str(data)[:500]:
                tractates = data.get("tractates", data.get("books", []))
                for t in tractates:
                    name = t.get("name", "")
                    lines.append(f"\n## {name}\n")
                    chapters = t.get("chapters", t.get("pages", []))
                    for c in chapters:
                        if isinstance(c, dict):
                            for page, text in c.items():
                                lines.append(f"\n### {page}\n{text}")
                        elif isinstance(c, list):
                            for item in c:
                                if isinstance(item, dict):
                                    for k, v in item.items():
                                        lines.append(f"{k}: {v}")
                                else:
                                    lines.append(str(item))
            
            # Guru Granth: angs -> shabads
            elif "angs" in data:
                for ang_num, ang_data in data.get("angs", {}).items():
                    lines.append(f"\n## Ang {ang_num}\n")
                    shabads = ang_data.get("shabads", ang_data.get("verses", []))
                    for s in shabads:
                        if isinstance(s, dict):
                            lines.append(s.get("text", json.dumps(s, ensure_ascii=False)))
                        else:
                            lines.append(str(s))
            
            # Generic: just pretty print
            else:
                self._flatten_dict(data, lines, 0)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    self._flatten_dict(item, lines, 0)
                else:
                    lines.append(str(item))
        
        return "\n".join(lines)
    
    def _flatten_dict(self, d: dict, lines: list, depth: int):
        """Recursively flatten a dict into text lines."""
        for k, v in d.items():
            if isinstance(v, dict):
                if depth < 3:
                    lines.append(f"\n{'#' * min(depth + 2, 6)} {k}\n")
                    self._flatten_dict(v, lines, depth + 1)
            elif isinstance(v, list):
                if all(isinstance(x, str) for x in v[:10]):
                    for i, item in enumerate(v):
                        lines.append(f"{k}[{i+1}]: {item}")
                else:
                    for item in v:
                        if isinstance(item, dict):
                            if depth < 3:
                                lines.append(f"\n{'#' * min(depth + 2, 6)} {k}\n")
                                self._flatten_dict(item, lines, depth + 1)
                        else:
                            lines.append(f"{k}: {item}")
            elif isinstance(v, str) and len(v) > 10:
                lines.append(f"{k}: {v}")
    
    async def scrape_sacred_texts_site(self, session: aiohttp.ClientSession,
                                        key: str, config: dict):
        """Scrape text from sacred-texts.com."""
        logger.info(f"[Sacred] Scraping {config['name']} from sacred-texts.com...")
        
        html = await self.fetch(session, config["url"])
        if not html:
            return
        
        text = self.extract_text_sacred_texts(html, config["url"])
        if text and len(text) > 200:
            self.save_document(
                source_key=key,
                url=config["url"],
                content=text,
                metadata={
                    "name": config["name"],
                    "tradition": config.get("tradition", ""),
                    "language": config.get("language", ""),
                    "source_type": "sacred-texts.com",
                }
            )
        
        # If there's a base URL, try to find index pages with links
        base_url = config.get("base_url", "")
        if base_url and base_url != config["url"]:
            logger.info(f"[Sacred] Scanning {base_url} for sub-pages...")
            index_html = await self.fetch(session, base_url)
            if index_html:
                soup = BS4(index_html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.endswith(".htm") or href.endswith(".html"):
                        full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                        if full_url != config["url"] and full_url != base_url:
                            sub_html = await self.fetch(session, full_url)
                            if sub_html:
                                sub_text = self.extract_text_sacred_texts(sub_html, full_url)
                                if sub_text and len(sub_text) > 200:
                                    self.save_document(
                                        source_key=key,
                                        url=full_url,
                                        content=sub_text,
                                        metadata={
                                            "name": f"{config['name']} - {a.text.strip()[:100]}",
                                            "tradition": config.get("tradition", ""),
                                            "source_type": "sacred-texts.com",
                                        }
                                    )
                            await asyncio.sleep(0.3)
    
    async def fetch_gutenberg(self, session: aiohttp.ClientSession, 
                               key: str, url: str, config: dict):
        """Fetch a Project Gutenberg text."""
        logger.info(f"[Sacred] Fetching Gutenberg: {config['name']}")
        
        text = await self.fetch(session, url)
        if text and len(text) > 1000:
            self.save_document(
                source_key=key,
                url=url,
                content=text,
                content_type="text/plain",
                metadata={
                    "name": config["name"],
                    "tradition": config.get("tradition", ""),
                    "source_type": "gutenberg",
                }
            )
    
    async def process_additional_github(self, session: aiohttp.ClientSession):
        """Process additional GitHub JSON sources."""
        for url in ADDITIONAL_GITHUB:
            try:
                logger.info(f"[Sacred] Additional: {url.split('/')[-1][:60]}...")
                data = await self.fetch_json(session, url)
                if data:
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                    name = url.split("/")[-1].replace(".json", "")
                    self.save_document(
                        source_key=f"additional/{name}",
                        url=url,
                        content=text,
                        content_type="application/json",
                        metadata={"source_url": url, "source_type": "additional_github"}
                    )
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"[Sacred] Error fetching {url}: {e}")
    
    async def process_additional_gutenberg(self, session: aiohttp.ClientSession):
        """Process additional Gutenberg texts."""
        for url in ADDITIONAL_GUTENBERG:
            try:
                text = await self.fetch(session, url)
                if text and len(text) > 1000:
                    name = url.split("/")[-1].replace(".txt.utf-8", "")
                    self.save_document(
                        source_key=f"gutenberg/{name}",
                        url=url,
                        content=text,
                        metadata={"source_url": url, "source_type": "gutenberg"}
                    )
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning(f"[Sacred] Error fetching {url}: {e}")
    
    def print_stats(self):
        """Print current stats."""
        logger.info(f"[Sacred] Stats: {self.stats['scraped']} scraped, "
                    f"{self.stats['skipped']} skipped, {self.stats['errors']} errors, "
                    f"{self.stats['bytes'] / 1024 / 1024:.1f} MB stored")
    
    async def run(self):
        """Run the sacred text harvester."""
        logger.info(f"[Sacred] === SACRED TEXT APOCALYPSE ===")
        logger.info(f"[Sacred] {len(SOURCES)} primary sources + "
                    f"{len(ADDITIONAL_GITHUB)} GitHub extras + "
                    f"{len(ADDITIONAL_GUTENBERG)} Gutenberg texts")
        
        # Trace to show the glorious scope
        traditions = set()
        for k, v in SOURCES.items():
            if "tradition" in v:
                traditions.add(v["tradition"])
        logger.info(f"[Sacred] Traditions: {', '.join(sorted(traditions))}")
        
        async with aiohttp.ClientSession(headers={
            "User-Agent": "Doc-Apocalypse/1.0 (sacred-text harvester; academic purpose)"
        }) as session:
            
            tasks = []
            for key, config in SOURCES.items():
                source_type = config.get("source_type", "github_json")
                
                if source_type == "github_json":
                    tasks.append(self.process_github_json(session, key, config))
                elif source_type == "scrape_sacred_texts":
                    tasks.append(self.scrape_sacred_texts_site(session, key, config))
                elif source_type == "gutenberg":
                    tasks.append(self.fetch_gutenberg(session, key, config["url"], config))
                
                # Limit concurrency
                if len(tasks) >= self.max_concurrent:
                    await asyncio.gather(*tasks)
                    tasks = []
                    self._save_seen()
                    self._save_stats()
                    self.print_stats()
            
            if tasks:
                await asyncio.gather(*tasks)
            
            # Process additional sources
            logger.info("[Sacred] Processing additional GitHub sources...")
            await self.process_additional_github(session)
            self._save_seen()
            self._save_stats()
            self.print_stats()
            
            logger.info("[Sacred] Processing additional Gutenberg texts...")
            await self.process_additional_gutenberg(session)
        
        self._save_seen()
        self._save_stats()
        self.print_stats()
        logger.info(f"[Sacred] === SACRED TEXT HARVEST COMPLETE ===")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sacred Text Harvester")
    parser.add_argument("--concurrent", type=int, default=6, help="Max concurrent requests")
    parser.add_argument("--dry-run", action="store_true", help="Just list sources")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/sacred_texts.log"),
            logging.StreamHandler()
        ]
    )
    
    if args.dry_run:
        print(f"\n📖 SACRED TEXT HARVEST — Dry Run")
        print(f"{'='*60}")
        traditions = {}
        for k, v in SOURCES.items():
            trad = v.get("tradition", "Unknown")
            if trad not in traditions:
                traditions[trad] = []
            traditions[trad].append(f"  ✅ {v['name']} ({v.get('language', '?')})")
        
        for trad in sorted(traditions.keys()):
            print(f"\n{trad}:")
            for line in traditions[trad]:
                print(line)
        
        print(f"\n{'='*60}")
        print(f"Total: {len(SOURCES)} primary sources")
        print(f"Additional: {len(ADDITIONAL_GITHUB)} GitHub + {len(ADDITIONAL_GUTENBERG)} Gutenberg")
        print(f"Traditions: {len(traditions)}")
        return 0
    
    harvester = SacredTextHarvester(max_concurrent=args.concurrent)
    await harvester.run()


if __name__ == "__main__":
    asyncio.run(main())
