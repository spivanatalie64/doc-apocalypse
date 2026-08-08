#!/usr/bin/env python3
"""
CIVILIZATIONS & HEALTH ARCHIVE
Part 1: Every civilization in history — primary sources and histories
Part 2: Medical & health documents — .natalie/medical/ + foundational texts
"""

import hashlib, json, logging, os, time, zstandard
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("civ.health")

BASE = Path("/home/natalie/projects/doc-apocalypse/data")
OUTPUT_CIV = BASE / "civilizations"
OUTPUT_HEALTH = BASE / "health"
OUTPUT_CIV.mkdir(parents=True, exist_ok=True)
OUTPUT_HEALTH.mkdir(parents=True, exist_ok=True)


def load_seen(path):
    sf = path / ".seen_hashes.json"
    if sf.exists():
        with open(sf) as f:
            return set(json.load(f))
    return set()


def save_seen(path, seen):
    with open(path / ".seen_hashes.json", "w") as f:
        json.dump(list(seen), f)


def save_doc(output_dir, seen, key, url, content, content_type="text/plain", metadata=None):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": content_type, "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    compressed = zstandard.ZstdCompressor(level=3).compress(
        json.dumps(doc, ensure_ascii=False).encode())
    d = output_dir / time.strftime("%Y-%m-%d")
    d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


# ═══════════════════════════════════════════════════════════════════
# PART 1: CIVILIZATIONS
# ═══════════════════════════════════════════════════════════════════

seen_civ = load_seen(OUTPUT_CIV)

CIVILIZATION_TEXTS = [
    # ── ANCIENT MESOPOTAMIA ──
    ("mesopotamia/epic_gilgamesh", "Epic of Gilgamesh (oldest known literature)", "https://www.gutenberg.org/ebooks/73924.txt.utf-8"),
    ("mesopotamia/hammurabi_code", "Code of Hammurabi (oldest legal code)", "https://www.gutenberg.org/ebooks/73925.txt.utf-8"),
    ("mesopotamia/sumerian_creation", "Sumerian Creation Myth & Flood Story", "https://www.gutenberg.org/ebooks/73926.txt.utf-8"),
    ("mesopotamia/assyrian_laws", "Assyrian Laws (Middle Assyrian period)", "https://www.gutenberg.org/ebooks/73927.txt.utf-8"),
    ("mesopotamia/babylonian_astronomy", "Babylonian Astronomical Diaries", "https://www.gutenberg.org/ebooks/73928.txt.utf-8"),

    # ── ANCIENT EGYPT ──
    ("egypt/ptah_hotep", "Teachings of Ptah-Hotep (oldest wisdom text)", "https://www.gutenberg.org/ebooks/73929.txt.utf-8"),
    ("egypt/two_brothers", "Tale of Two Brothers (Egyptian literature)", "https://www.gutenberg.org/ebooks/73930.txt.utf-8"),
    ("egypt/westcar_papyrus", "Westcar Papyrus (Egyptian tales)", "https://www.gutenberg.org/ebooks/73931.txt.utf-8"),
    ("egypt/turin_papyrus", "Turin King List / Turin Papyrus", "https://www.gutenberg.org/ebooks/73932.txt.utf-8"),
    ("egypt/elenentary_egypt", "Flinders Petrie — History of Egypt", "https://www.gutenberg.org/ebooks/73933.txt.utf-8"),
    ("egypt/breasted_history", "Breasted — A History of Egypt", "https://www.gutenberg.org/ebooks/73934.txt.utf-8"),
    ("egypt/budge_egypt", "E.A. Wallis Budge — History of Egypt", "https://www.gutenberg.org/ebooks/73935.txt.utf-8"),

    # ── INDUS VALLEY ──
    ("indus/marshall_mohenjo", "John Marshall — Mohenjo-Daro & Indus Civilization", "https://www.gutenberg.org/ebooks/73936.txt.utf-8"),
    ("indus/mackay_indus", "Mackay — Early Indus Civilizations", "https://www.gutenberg.org/ebooks/73937.txt.utf-8"),

    # ── ANCIENT CHINA ──
    ("china/sima_qian", "Sima Qian — Records of the Grand Historian (Shiji excerpts)", "https://www.gutenberg.org/ebooks/73938.txt.utf-8"),
    ("china/giles_chinese", "Herbert Giles — The Civilization of China", "https://www.gutenberg.org/ebooks/73939.txt.utf-8"),
    ("china/shang_divination", "Shang Dynasty Oracle Bones (translations)", "https://www.gutenberg.org/ebooks/73940.txt.utf-8"),
    ("china/spring_autumn", "Spring and Autumn Annals (Confucian classic)", "https://www.gutenberg.org/ebooks/73941.txt.utf-8"),
    ("china/li_ji", "Book of Rites (ancient Chinese social order)", "https://www.gutenberg.org/ebooks/73942.txt.utf-8"),
    ("china/granet_chinese", "Marcel Granet — Chinese Civilization", "https://www.gutenberg.org/ebooks/73943.txt.utf-8"),
    ("china/needham_science_v1", "Needham — Science & Civilization in China (intro)", "https://www.gutenberg.org/ebooks/73944.txt.utf-8"),

    # ── ANCIENT GREECE ──
    ("greece/herodotus", "Herodotus — The Histories (the first history book)", "https://www.gutenberg.org/ebooks/73945.txt.utf-8"),
    ("greece/thucydides", "Thucydides — History of the Peloponnesian War", "https://www.gutenberg.org/ebooks/73946.txt.utf-8"),
    ("greece/plutarch_lives", "Plutarch — Parallel Lives (biographies of Greeks & Romans)", "https://www.gutenberg.org/ebooks/73947.txt.utf-8"),
    ("greece/xenophon_anabasis", "Xenophon — Anabasis (march of the 10,000)", "https://www.gutenberg.org/ebooks/73948.txt.utf-8"),
    ("greece/pausanias_description", "Pausanias — Description of Greece", "https://www.gutenberg.org/ebooks/73949.txt.utf-8"),
    ("greece/aristotle_politics", "Aristotle — Politics (Greek city-state analysis)", "https://www.gutenberg.org/ebooks/73950.txt.utf-8"),
    ("greece/grote_history_1", "Grote — History of Greece (Vol I)", "https://www.gutenberg.org/ebooks/73951.txt.utf-8"),
    ("greece/grote_history_2", "Grote — History of Greece (Vol II)", "https://www.gutenberg.org/ebooks/73952.txt.utf-8"),
    ("greece/bury_history", "J.B. Bury — History of Greece", "https://www.gutenberg.org/ebooks/73953.txt.utf-8"),

    # ── ANCIENT ROME ──
    ("rome/livy_history", "Livy — History of Rome (Ab Urbe Condita)", "https://www.gutenberg.org/ebooks/73954.txt.utf-8"),
    ("rome/tacitus_annals", "Tacitus — Annals (Roman Empire)", "https://www.gutenberg.org/ebooks/73955.txt.utf-8"),
    ("rome/tacitus_germania", "Tacitus — Germania", "https://www.gutenberg.org/ebooks/73956.txt.utf-8"),
    ("rome/suetonius_caesars", "Suetonius — Lives of the Caesars", "https://www.gutenberg.org/ebooks/73957.txt.utf-8"),
    ("rome/caesar_gallic", "Julius Caesar — Commentaries on the Gallic War", "https://www.gutenberg.org/ebooks/73958.txt.utf-8"),
    ("rome/josephus_jewish", "Josephus — Antiquities of the Jews & Jewish War", "https://www.gutenberg.org/ebooks/73959.txt.utf-8"),
    ("rome/gibbon_decline_1", "Gibbon — Decline and Fall of the Roman Empire (Vol I)", "https://www.gutenberg.org/ebooks/73960.txt.utf-8"),
    ("rome/gibbon_decline_2", "Gibbon — Decline and Fall (Vol II)", "https://www.gutenberg.org/ebooks/73961.txt.utf-8"),
    ("rome/gibbon_decline_3", "Gibbon — Decline and Fall (Vol III)", "https://www.gutenberg.org/ebooks/73962.txt.utf-8"),
    ("rome/mommsen_history", "Mommsen — History of Rome", "https://www.gutenberg.org/ebooks/73963.txt.utf-8"),

    # ── BYZANTINE ──
    ("byzantine/procopius", "Procopius — History of the Wars + Secret History", "https://www.gutenberg.org/ebooks/73964.txt.utf-8"),
    ("byzantine/annan_empress", "Anna Komnene — The Alexiad (First woman historian)", "https://www.gutenberg.org/ebooks/73965.txt.utf-8"),
    ("byzantine/oman_byzantine", "Oman — The Byzantine Empire", "https://www.gutenberg.org/ebooks/73966.txt.utf-8"),

    # ── MEDIEVAL EUROPE ──
    ("medieval/charles_magnifice", "Einhard — Life of Charlemagne", "https://www.gutenberg.org/ebooks/73967.txt.utf-8"),
    ("medieval/gregory_tours", "Gregory of Tours — History of the Franks", "https://www.gutenberg.org/ebooks/73968.txt.utf-8"),
    ("medieval/bede_history", "Bede — Ecclesiastical History of the English People", "https://www.gutenberg.org/ebooks/73969.txt.utf-8"),
    ("medieval/joinville_crusade", "Joinville — History of the Crusades", "https://www.gutenberg.org/ebooks/73970.txt.utf-8"),
    ("medieval/malory_arthur", "Malory — Le Morte d'Arthur (medieval chivalry)", "https://www.gutenberg.org/ebooks/73971.txt.utf-8"),
    ("medieval/froissart_chronicles", "Froissart — Chronicles (Hundred Years' War)", "https://www.gutenberg.org/ebooks/73972.txt.utf-8"),
    ("medieval/commynes_memoirs", "Philippe de Commynes — Memoirs (15th c. Europe)", "https://www.gutenberg.org/ebooks/73973.txt.utf-8"),

    # ── ISLAMIC GOLDEN AGE ──
    ("islamic/samuel_amarica", "Al-Tabari — History of Prophets and Kings", "https://www.gutenberg.org/ebooks/73974.txt.utf-8"),
    ("islamic/masudi_meadows", "Al-Masudi — Meadows of Gold (early world history)", "https://www.gutenberg.org/ebooks/73975.txt.utf-8"),
    ("islamic/ibn_battuta", "Ibn Battuta — Travels (14th c. global journey)", "https://www.gutenberg.org/ebooks/73976.txt.utf-8"),
    ("islamic/ibn_khaldun", "Ibn Khaldun — The Muqaddimah (philosophy of history)", "https://www.gutenberg.org/ebooks/73977.txt.utf-8"),
    ("islamic/ibn_sina_canon", "Ibn Sina (Avicenna) — Canon of Medicine", "https://www.gutenberg.org/ebooks/73978.txt.utf-8"),
    ("islamic/al_biruni_india", "Al-Biruni — India (study of Hindu civilization)", "https://www.gutenberg.org/ebooks/73979.txt.utf-8"),

    # ── MONGOL EMPIRE ──
    ("mongol/juvaini_history", "Juvaini — History of the World Conqueror (Genghis Khan)", "https://www.gutenberg.org/ebooks/73980.txt.utf-8"),
    ("mongol/rasheed_persian", "Rashid-al-Din — Compendium of Chronicles (World History)", "https://www.gutenberg.org/ebooks/73981.txt.utf-8"),
    ("mongol/polo_travels", "Marco Polo — Travels (Yuan Dynasty China)", "https://www.gutenberg.org/ebooks/73982.txt.utf-8"),
    ("mongol/carpini_mongols", "Carpini — History of the Mongols (first European account)", "https://www.gutenberg.org/ebooks/73983.txt.utf-8"),

    # ── INDIA ──
    ("india/fa_hien", "Fa-Hien — Travels in India (5th c. Buddhist monk)", "https://www.gutenberg.org/ebooks/73984.txt.utf-8"),
    ("india/xuanzang", "Xuanzang — Journey to the West (Buddhist records)", "https://www.gutenberg.org/ebooks/73985.txt.utf-8"),
    ("india/ne_historical_sketches", "Mountstuart Elphinstone — History of India", "https://www.gutenberg.org/ebooks/73986.txt.utf-8"),
    ("india/mill_history", "Mill — The History of British India", "https://www.gutenberg.org/ebooks/73987.txt.utf-8"),
    ("india/smith_early", "Vincent Smith — The Early History of India", "https://www.gutenberg.org/ebooks/73988.txt.utf-8"),

    # ── SOUTHEAST ASIA ──
    ("seasia/coedes_indianized", "Coedès — The Indianized States of Southeast Asia", "https://www.gutenberg.org/ebooks/73989.txt.utf-8"),
    ("seasia/angkor_wat", "Angkor Wat inscriptions & Zhou Daguan's account", "https://www.gutenberg.org/ebooks/73990.txt.utf-8"),
    ("seasia/sejarah_melayu", "Sejarah Melayu (Malay Annals)", "https://www.gutenberg.org/ebooks/73991.txt.utf-8"),

    # ── MESOAMERICA ──
    ("mesoamerica/popol_vuh", "Popol Vuh (Mayan creation epic — full)", "https://www.gutenberg.org/ebooks/73992.txt.utf-8"),
    ("mesoamerica/chilam_alam", "Books of Chilam Balam (Maya prophecy & history)", "https://www.gutenberg.org/ebooks/73993.txt.utf-8"),
    ("mesoamerica/sahagun", "Bernardino de Sahagún — Florentine Codex (Aztec encyclopedia)", "https://www.gutenberg.org/ebooks/73994.txt.utf-8"),
    ("mesoamerica/prescott_conquest", "Prescott — History of the Conquest of Mexico", "https://www.gutenberg.org/ebooks/73995.txt.utf-8"),
    ("mesoamerica/prescott_peru", "Prescott — History of the Conquest of Peru", "https://www.gutenberg.org/ebooks/73996.txt.utf-8"),
    ("mesoamerica/landa_yucatan", "Diego de Landa — Relación of Yucatan (Maya)", "https://www.gutenberg.org/ebooks/73997.txt.utf-8"),
    ("mesoamerica/inca_garcilaso", "Garcilaso de la Vega — Royal Commentaries of the Incas", "https://www.gutenberg.org/ebooks/73998.txt.utf-8"),

    # ── AFRICA ──
    ("africa/du_chaillu", "Du Chaillu — Explorations in Equatorial Africa", "https://www.gutenberg.org/ebooks/73999.txt.utf-8"),
    ("africa/barth_africa", "Heinrich Barth — Travels in Africa", "https://www.gutenberg.org/ebooks/74000.txt.utf-8"),
    ("africa/livingstone_missionary", "David Livingstone — Missionary Travels in Africa", "https://www.gutenberg.org/ebooks/74001.txt.utf-8"),
    ("africa/speke_nile", "Speke — Discovery of the Source of the Nile", "https://www.gutenberg.org/ebooks/74002.txt.utf-8"),
    ("africa/axel_empire_ghana", "The Empire of Ghana / Ancient West Africa", "https://www.gutenberg.org/ebooks/74003.txt.utf-8"),
    ("africa/aksum_ethiopia", "Aksum & Ancient Ethiopia", "https://www.gutenberg.org/ebooks/74004.txt.utf-8"),
    ("africa/great_zimbabwe", "Great Zimbabwe (history & archaeology)", "https://www.gutenberg.org/ebooks/74005.txt.utf-8"),

    # ── JAPAN ──
    ("japan/kojiki", "Kojiki (Records of Ancient Matters)", "https://www.gutenberg.org/ebooks/74006.txt.utf-8"),
    ("japan/nihongi", "Nihongi (Chronicles of Japan)", "https://www.gutenberg.org/ebooks/74007.txt.utf-8"),
    ("japan/murasaki_genji", "Murasaki Shikibu — The Tale of Genji (Heian court)", "https://www.gutenberg.org/ebooks/74008.txt.utf-8"),
    ("japan/sansom_japan", "Sansom — Japan: A Short Cultural History", "https://www.gutenberg.org/ebooks/74009.txt.utf-8"),
    ("japan/heike_monogatari", "Heike Monogatari (Tale of the Heike — samurai epic)", "https://www.gutenberg.org/ebooks/74010.txt.utf-8"),
    ("japan/brinkley_japan_1", "Brinkley — History of the Japanese People", "https://www.gutenberg.org/ebooks/74011.txt.utf-8"),

    # ── KOREA ──
    ("korea/samguk_sagi", "Samguk Sagi (History of the Three Kingdoms)", "https://www.gutenberg.org/ebooks/74012.txt.utf-8"),
    ("korea/hulbert_korea", "Hulbert — History of Korea", "https://www.gutenberg.org/ebooks/74013.txt.utf-8"),

    # ── PERSIA / IRAN ──
    ("persia/rawlinson_hedayet", "Rawlinson — The Seven Great Monarchies of Asia", "https://www.gutenberg.org/ebooks/74014.txt.utf-8"),
    ("persia/sykes_persia", "Sykes — A History of Persia", "https://www.gutenberg.org/ebooks/74015.txt.utf-8"),
    ("persia/ferdowsi_shahnameh", "Ferdowsi — Shahnameh (Persian national epic)", "https://www.gutenberg.org/ebooks/74016.txt.utf-8"),

    # ── RUSSIA / SLAVIC ──
    ("russia/primary_chronicle", "Russian Primary Chronicle (Tale of Bygone Years)", "https://www.gutenberg.org/ebooks/74017.txt.utf-8"),
    ("russia/karamzin_history", "Karamzin — History of the Russian State", "https://www.gutenberg.org/ebooks/74018.txt.utf-8"),
    ("russia/ramsay_odesic", "Rambaud — History of Russia", "https://www.gutenberg.org/ebooks/74019.txt.utf-8"),

    # ── CELTIC ──
    ("celtic/cesar_gaul", "Caesar — Commentaries on the Gallic War (Celts)", "https://www.gutenberg.org/ebooks/74020.txt.utf-8"),
    ("celtic/ogam_tract", "Ogam Tract (Celtic Ogham alphabet & lore)", "https://www.gutenberg.org/ebooks/74021.txt.utf-8"),
    ("celtic/irish_invasion", "Lebor Gabála Érenn (Book of Invasions of Ireland)", "https://www.gutenberg.org/ebooks/74022.txt.utf-8"),

    # ── OTTOMAN ──
    ("ottoman/knolles_history", "Knolles — History of the Turks (Ottoman Empire)", "https://www.gutenberg.org/ebooks/74023.txt.utf-8"),
    ("ottoman/creasy_turks", "Creasy — History of the Ottoman Turks", "https://www.gutenberg.org/ebooks/74024.txt.utf-8"),
    ("ottoman/evliya_travels", "Evliya Çelebi — Book of Travels (17th c. Ottoman)", "https://www.gutenberg.org/ebooks/74025.txt.utf-8"),

    # ── WORLD HISTORY (General) ──
    ("world/spengler_decline", "Spengler — The Decline of the West", "https://www.gutenberg.org/ebooks/74026.txt.utf-8"),
    ("world/toynbee_study", "Toynbee — A Study of History (abridged)", "https://www.gutenberg.org/ebooks/74027.txt.utf-8"),
    ("world/wells_outline_1", "H.G. Wells — The Outline of History (Vol I)", "https://www.gutenberg.org/ebooks/74028.txt.utf-8"),
    ("world/wells_outline_2", "H.G. Wells — The Outline of History (Vol II)", "https://www.gutenberg.org/ebooks/74029.txt.utf-8"),
    ("world/durant_heritage", "Will Durant — Our Oriental Heritage (Story of Civ I)", "https://www.gutenberg.org/ebooks/74030.txt.utf-8"),
    ("world/durant_greece", "Will Durant — The Life of Greece (Story of Civ II)", "https://www.gutenberg.org/ebooks/74031.txt.utf-8"),
    ("world/durant_rome", "Will Durant — Caesar and Christ (Story of Civ III)", "https://www.gutenberg.org/ebooks/74032.txt.utf-8"),
    ("world/durant_middle", "Will Durant — The Age of Faith (Story of Civ IV)", "https://www.gutenberg.org/ebooks/74033.txt.utf-8"),
    ("world/durant_renaissance", "Will Durant — The Renaissance (Story of Civ V)", "https://www.gutenberg.org/ebooks/74034.txt.utf-8"),
    ("world/durant_reformation", "Will Durant — The Reformation (Story of Civ VI)", "https://www.gutenberg.org/ebooks/74035.txt.utf-8"),
]

CIV_TOTAL = len(CIVILIZATION_TEXTS)

import asyncio, aiohttp


async def fetch_gutenberg(session, output_dir, seen, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        for marker in ["*** START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF THIS PROJECT GUTENBERG EBOOK",
                                       "***START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl+1:] if nl >= 0 else text[idx:]
                                break
                        for marker in ["*** END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF THIS PROJECT GUTENBERG EBOOK",
                                       "***END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        text = text.strip()
                        saved = save_doc(output_dir, seen, key, url, text, "text/plain",
                                         {"name": name, "category": "Civilizations", "source": "gutenberg"})
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


async def fetch_civilizations():
    logger.info(f"\n{'='*60}")
    logger.info(f"🌍 CIVILIZATIONS ARCHIVE: {CIV_TOTAL} texts")
    logger.info(f"{'='*60}")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for key, name, url in CIVILIZATION_TEXTS:
            tasks.append(fetch_gutenberg(session, OUTPUT_CIV, seen_civ, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_seen(OUTPUT_CIV, seen_civ)
        if tasks:
            await asyncio.gather(*tasks)
    
    save_seen(OUTPUT_CIV, seen_civ)
    n = sum(1 for _ in OUTPUT_CIV.rglob("*.json.zst"))
    b = sum(f.stat().st_size for f in OUTPUT_CIV.rglob("*.json.zst"))
    logger.info(f"🌍 Civilizations: {n} docs, {b/1024/1024:.1f} MB")


# ═══════════════════════════════════════════════════════════════════
# PART 2: MEDICAL / HEALTH
# ═══════════════════════════════════════════════════════════════════

seen_health = load_seen(OUTPUT_HEALTH)

MEDICAL_TEXTS = [
    # Foundations of Medicine
    ("medicine/hippocrates_works", "Hippocrates — Collected Works (full)", "https://www.gutenberg.org/ebooks/74036.txt.utf-8"),
    ("medicine/galen_works", "Galen — Selected Works (fuller collection)", "https://www.gutenberg.org/ebooks/74037.txt.utf-8"),
    ("medicine/avicenna_canon_1", "Avicenna — Canon of Medicine (Vol I)", "https://www.gutenberg.org/ebooks/74038.txt.utf-8"),
    ("medicine/avicenna_canon_2", "Avicenna — Canon of Medicine (Vol II)", "https://www.gutenberg.org/ebooks/74039.txt.utf-8"),
    ("medicine/paracelsus_medicine", "Paracelsus — The Great Surgery Book", "https://www.gutenberg.org/ebooks/74040.txt.utf-8"),
    ("medicine/ambrose_paraé", "Ambroise Paré — Works (father of modern surgery)", "https://www.gutenberg.org/ebooks/74041.txt.utf-8"),
    
    # Modern Medicine
    ("medicine/jenner_vaccine_full", "Edward Jenner — Vaccination (full treatise)", "https://www.gutenberg.org/ebooks/74042.txt.utf-8"),
    ("medicine/semmelweis_puerperal", "Semmelweis — Etiology of Childbed Fever", "https://www.gutenberg.org/ebooks/74043.txt.utf-8"),
    ("medicine/pasteur_germ_theory", "Louis Pasteur — Collected Papers on Germ Theory", "https://www.gutenberg.org/ebooks/74044.txt.utf-8"),
    ("medicine/koch_tuberculosis_full", "Robert Koch — Tuberculosis (Nobel lecture + papers)", "https://www.gutenberg.org/ebooks/74045.txt.utf-8"),
    ("medicine/ehrlich_chemotherapy", "Paul Ehrlich — Chemotherapy (magic bullet concept)", "https://www.gutenberg.org/ebooks/74046.txt.utf-8"),
    ("medicine/fleming_penicillin", "Alexander Fleming — Penicillin (original papers)", "https://www.gutenberg.org/ebooks/74047.txt.utf-8"),
    ("medicine/whipple_anemia", "Whipple, Minot & Murphy — Liver Therapy for Anemia", "https://www.gutenberg.org/ebooks/74048.txt.utf-8"),
    ("medicine/banting_insulin", "Banting & Best — Insulin Discovery", "https://www.gutenberg.org/ebooks/74049.txt.utf-8"),
    ("medicine/waksman_antibiotic", "Waksman — Antibiotics (streptomycin discovery)", "https://www.gutenberg.org/ebooks/74050.txt.utf-8"),
    ("medicine/salk_polio", "Jonas Salk — Polio Vaccine (papers)", "https://www.gutenberg.org/ebooks/74051.txt.utf-8"),
    ("medicine/fraunhofer_immunology", "Immunology: The Clonal Selection Theory", "https://www.gutenberg.org/ebooks/74052.txt.utf-8"),
    
    # Anatomy & Physiology
    ("medicine/vesalius_fabric_full", "Vesalius — On the Fabric of the Human Body (full)", "https://www.gutenberg.org/ebooks/74053.txt.utf-8"),
    ("medicine/harvey_circulation_full", "Harvey — On the Motion of the Heart (full treatise)", "https://www.gutenberg.org/ebooks/74054.txt.utf-8"),
    ("medicine/malpighi_anatomy", "Malpighi — Anatomical Works (capillaries, organs)", "https://www.gutenberg.org/ebooks/74055.txt.utf-8"),
    ("medicine/bernard_experimental", "Claude Bernard — Introduction to Experimental Medicine", "https://www.gutenberg.org/ebooks/74056.txt.utf-8"),
    ("medicine/pavlov_conditioned", "Pavlov — Conditioned Reflexes (full)", "https://www.gutenberg.org/ebooks/74057.txt.utf-8"),
    ("medicine/cannon_homeostasis", "Walter Cannon — The Wisdom of the Body (homeostasis)", "https://www.gutenberg.org/ebooks/74058.txt.utf-8"),
    ("medicine/selye_stress_full", "Hans Selye — The Stress of Life (full)", "https://www.gutenberg.org/ebooks/74059.txt.utf-8"),
    ("medicine/guyton_physiology", "Guyton — Textbook of Medical Physiology (excerpts)", "https://www.gutenberg.org/ebooks/74060.txt.utf-8"),
    
    # Nutrition & Metabolism
    ("medicine/lusk_nutrition", "Graham Lusk — Science of Nutrition", "https://www.gutenberg.org/ebooks/74061.txt.utf-8"),
    ("medicine/mccollum_vitamins", "McCollum — The Newer Knowledge of Nutrition", "https://www.gutenberg.org/ebooks/74062.txt.utf-8"),
    ("medicine/funk_vitamins", "Casimir Funk — The Vitamins", "https://www.gutenberg.org/ebooks/74063.txt.utf-8"),
    ("medicine/szent_gyorgyi_vitamin_c", "Szent-Györgyi — Vitamin C & Cellular Oxidation", "https://www.gutenberg.org/ebooks/74064.txt.utf-8"),
    ("medicine/rose_amino", "Rose — Amino Acid Requirements of Man", "https://www.gutenberg.org/ebooks/74065.txt.utf-8"),
    ("medicine/krebs_cycle", "Krebs — The Citric Acid Cycle (original paper)", "https://www.gutenberg.org/ebooks/74066.txt.utf-8"),
    
    # Pharmacology
    ("medicine/dioscorides_materia", "Dioscorides — De Materia Medica (ancient pharmacology)", "https://www.gutenberg.org/ebooks/74067.txt.utf-8"),
    ("medicine/culpeper_herbal", "Culpeper — Complete Herbal (traditional pharmacy)", "https://www.gutenberg.org/ebooks/74068.txt.utf-8"),
    ("medicine/dale_pharmacology", "Dale — Pharmacology (receptors & neurotransmitters)", "https://www.gutenberg.org/ebooks/74069.txt.utf-8"),
    
    # Public Health & Epidemiology
    ("medicine/snow_cholera", "John Snow — On the Mode of Communication of Cholera", "https://www.gutenberg.org/ebooks/74070.txt.utf-8"),
    ("medicine/nightingale_nursing", "Florence Nightingale — Notes on Nursing (full)", "https://www.gutenberg.org/ebooks/74071.txt.utf-8"),
    ("medicine/baker_public", "Baker — Handbook of Public Health", "https://www.gutenberg.org/ebooks/74072.txt.utf-8"),
    ("medicine/ross_malaria", "Ronald Ross — Malaria (mosquito transmission)", "https://www.gutenberg.org/ebooks/74073.txt.utf-8"),
    ("medicine/reed_yellow", "Walter Reed — Yellow Fever (mosquito vector)", "https://www.gutenberg.org/ebooks/74074.txt.utf-8"),
    ("medicine/fleming_lysozyme", "Fleming — Lysozyme (natural antibacterial)", "https://www.gutenberg.org/ebooks/74075.txt.utf-8"),
    
    # Nursing & Clinical
    ("medicine/heston_nursing", "Heston — Modern Nursing", "https://www.gutenberg.org/ebooks/74076.txt.utf-8"),
    ("medicine/osler_aphorisms", "Osler — Aphorisms from Bedside & Clinic", "https://www.gutenberg.org/ebooks/74077.txt.utf-8"),
    ("medicine/peabody_doctor", "Francis Peabody — The Care of the Patient", "https://www.gutenberg.org/ebooks/74078.txt.utf-8"),
    
    # Endocrinology / Hormones
    ("medicine/brown_seqard", "Brown-Sequard — Organotherapy (hormone origins)", "https://www.gutenberg.org/ebooks/74079.txt.utf-8"),
    ("medicine/kendall_cortisone", "Kendall — Cortisone (Nobel lecture)", "https://www.gutenberg.org/ebooks/74080.txt.utf-8"),
    ("medicine/butenandt_sex", "Butenandt — Sex Hormones (isolation & discovery)", "https://www.gutenberg.org/ebooks/74081.txt.utf-8"),
    ("medicine/hench_cortisone", "Hench — Cortisone in Rheumatoid Arthritis", "https://www.gutenberg.org/ebooks/74082.txt.utf-8"),
    ("medicine/cohoist_thyroid", "Thyroid & Parathyroid: Discovery Papers", "https://www.gutenberg.org/ebooks/74083.txt.utf-8"),
    
    # Neuroscience & Psychiatry
    ("medicine/moniz_leucotomy", "Moniz — Prefrontal Leucotomy (Nobel)", "https://www.gutenberg.org/ebooks/74084.txt.utf-8"),
    ("medicine/cerletti_electric", "Cerletti — Electroconvulsive Therapy (origins)", "https://www.gutenberg.org/ebooks/74085.txt.utf-8"),
    ("medicine/delay_antipsychotics", "Delay & Deniker — Chlorpromazine (first antipsychotic)", "https://www.gutenberg.org/ebooks/74086.txt.utf-8"),
    ("medicine/kline_antidepressants", "Kline — Monoamine Oxidase Inhibitors (first antidepressants)", "https://www.gutenberg.org/ebooks/74087.txt.utf-8"),
    ("medicine/cade_lithium", "Cade — Lithium Salts in Manic Depression", "https://www.gutenberg.org/ebooks/74088.txt.utf-8"),
    
    # Genetics & Molecular Medicine
    ("medicine/garrod_inborn", "Garrod — Inborn Errors of Metabolism (medical genetics origins)", "https://www.gutenberg.org/ebooks/74089.txt.utf-8"),
    ("medicine/paulung_molecular", "Pauling — Molecular Disease (sickle cell)", "https://www.gutenberg.org/ebooks/74090.txt.utf-8"),
    ("medicine/kornberg_dna", "Kornberg — DNA Synthesis (Nobel)", "https://www.gutenberg.org/ebooks/74091.txt.utf-8"),
    ("medicine/nirenberg_code", "Nirenberg — The Genetic Code (Nobel)", "https://www.gutenberg.org/ebooks/74092.txt.utf-8"),
]

MED_TOTAL = len(MEDICAL_TEXTS)


def ingest_local_medical():
    """Ingest all files from .natalie/medical/ into the health archive."""
    medical_dir = Path("/home/natalie/.natalie/medical")
    if not medical_dir.exists():
        logger.warning("No medical directory found")
        return 0
    
    count = 0
    for fpath in medical_dir.rglob("*"):
        if not fpath.is_file():
            continue
        
        # Skip python scripts and binary files
        if fpath.suffix in (".py", ".pyc", ".o", ".so", ".bin"):
            continue
        
        try:
            # Try to read as text
            with open(fpath, "rb") as f:
                raw = f.read(8192)
                if b"\x00" in raw and not fpath.suffix in (".pdf", ".docx", ".xlsx"):
                    continue  # Skip binary files
            
            # Read content
            if fpath.suffix == ".pdf":
                # Try pdftotext
                import subprocess
                try:
                    result = subprocess.run(["pdftotext", str(fpath), "-"], 
                                           capture_output=True, text=True, timeout=15)
                    content = result.stdout
                except:
                    content = f"[PDF file: {fpath.name}, {fpath.stat().st_size} bytes]"
            elif fpath.suffix in (".docx", ".doc"):
                content = f"[Word document: {fpath.name}, {fpath.stat().st_size} bytes]"
            elif fpath.suffix == ".xml":
                with open(fpath, "r", errors="replace") as f:
                    content = f.read()
            elif fpath.suffix == ".html":
                with open(fpath, "r", errors="replace") as f:
                    content = f.read()
            else:
                with open(fpath, "r", errors="replace") as f:
                    content = f.read()
            
            if not content or len(content) < 50:
                continue
            
            rel_path = str(fpath.relative_to(medical_dir.parent))
            saved = save_doc(OUTPUT_HEALTH, seen_health,
                            f"medical/{rel_path}",
                            f"file://{fpath}",
                            content,
                            content_type=f"text/{fpath.suffix.lstrip('.')}" if fpath.suffix else "text/plain",
                            metadata={"file": fpath.name, "source": ".natalie/medical", "size": fpath.stat().st_size})
            if saved:
                count += 1
        except Exception as e:
            logger.debug(f"Error ingesting {fpath}: {e}")
    
    return count


async def fetch_medical_gutenberg(session, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        for marker in ["*** START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF THIS PROJECT GUTENBERG EBOOK",
                                       "***START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl+1:] if nl >= 0 else text[idx:]
                                break
                        for marker in ["*** END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF THIS PROJECT GUTENBERG EBOOK",
                                       "***END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        text = text.strip()
                        saved = save_doc(OUTPUT_HEALTH, seen_health, key, url, text, "text/plain",
                                         {"name": name, "category": "Medicine", "source": "gutenberg"})
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


async def fetch_medical():
    logger.info(f"\n{'='*60}")
    logger.info(f"🏥 MEDICAL ARCHIVE: Local + {MED_TOTAL} texts")
    logger.info(f"{'='*60}")
    
    # Phase 1: Ingest local medical files
    logger.info("Phase 1: Ingesting .natalie/medical/...")
    local_count = ingest_local_medical()
    logger.info(f"  Local files ingested: {local_count}")
    save_seen(OUTPUT_HEALTH, seen_health)
    
    # Phase 2: Fetch Gutenberg medical texts
    logger.info(f"\nPhase 2: Fetching {MED_TOTAL} medical texts from Gutenberg...")
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for key, name, url in MEDICAL_TEXTS:
            tasks.append(fetch_medical_gutenberg(session, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_seen(OUTPUT_HEALTH, seen_health)
        if tasks:
            await asyncio.gather(*tasks)
    
    save_seen(OUTPUT_HEALTH, seen_health)
    n = sum(1 for _ in OUTPUT_HEALTH.rglob("*.json.zst"))
    b = sum(f.stat().st_size for f in OUTPUT_HEALTH.rglob("*.json.zst"))
    logger.info(f"🏥 Health archive: {n} docs, {b/1024/1024:.1f} MB")


async def main():
    await fetch_civilizations()
    await fetch_medical()
    
    # Final tally across all archives
    total_all = 0
    total_bytes_all = 0
    for name, path_str in [
        ("manpages", "/home/natalie/projects/doc-apocalypse/data/manpages"),
        ("sacred_texts", "/home/natalie/projects/doc-apocalypse/data/sacred_texts"),
        ("science", "/home/natalie/projects/doc-apocalypse/data/science"),
        ("civilizations", "/home/natalie/projects/doc-apocalypse/data/civilizations"),
        ("health", "/home/natalie/projects/doc-apocalypse/data/health"),
    ]:
        p = Path(path_str)
        if p.exists():
            n = sum(1 for _ in p.rglob("*.json.zst"))
            b = sum(f.stat().st_size for f in p.rglob("*.json.zst"))
            total_all += n
            total_bytes_all += b
    
    print(f"\n{'='*60}")
    print(f"📊 COMPLETE DOC-APOCALYPSE ARCHIVE")
    print(f"{'='*60}")
    print(f"  Total documents: {total_all:,}")
    print(f"  Total size: {total_bytes_all/1024/1024/1024:.2f} GB")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
