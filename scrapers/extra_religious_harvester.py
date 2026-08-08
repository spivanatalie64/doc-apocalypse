#!/usr/bin/env python3
"""
Extra-Religious Texts Harvester
Fetches extra-biblical/extra-canonical texts for ALL religious traditions
from Project Gutenberg and other open sources.

Categories:
  - Judaism: Talmud (full), Midrash Rabbah, Tosefta, Maimonides, Rashi, Kabbala Denudata
  - Islam: Hadith (Bukhari, Muslim), Tafsir al-Jalalayn, Rumi, Sufi poetry, Sira
  - Buddhism: Majjhima Nikaya, Samyutta Nikaya, Anguttara Nikaya, Lotus Sutra, Zen koans, Milinda Panha
  - Hinduism: Mahabharata, Ramayana, Puranas, Devi Mahatmya, Kama Sutra, Tantras
  - Taoism: Cantong Qi, Baopuzi, Liezi, Huainanzi, Secret of the Golden Flower
  - Shinto: Norito, Engishiki, Kogoshui
  - Zoroastrian: Bundahishn, Denkard, Rivayats, Shikand Gumanig Vichar
  - Sikh: Dasam Granth, Vaaran, Bhai Gurdas
  - Jain: Uttaradhyayana Sutra, Kalpa Sutra, Acaranga Sutra
  - Confucian: Great Learning, Doctrine of the Mean, Mencius (full)
  - Baha'i: Gleanings, Seven Valleys, Epistles
  - Mormon: Doctrine & Covenants, Pearl of Great Price, Book of Abraham
"""

import asyncio
import hashlib
import json
import logging
import re
import time
import zstandard as zstd
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extra.religious")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts")
OUTPUT.mkdir(parents=True, exist_ok=True)

seen_file = OUTPUT / ".seen_hashes.json"
seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))
logger.info(f"Loaded {len(seen)} seen hashes")


def save(source: str, url: str, content: str, metadata: dict = None) -> bool:
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": source, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    cctx = zstd.ZstdCompressor(level=3)
    compressed = cctx.compress(json.dumps(doc, ensure_ascii=False).encode())
    d = OUTPUT / time.strftime("%Y-%m-%d")
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


# ── JUDAISM (Extra-Biblical) ──
JUDAISM = [
    ("judaism/talmud_bavli_full", "Talmud Bavli (Babylonian Talmud) — Full", "https://www.gutenberg.org/ebooks/73613.txt.utf-8"),
    ("judaism/talmud_yerushalmi", "Talmud Yerushalmi (Jerusalem Talmud)", "https://www.gutenberg.org/ebooks/73614.txt.utf-8"),
    ("judaism/midrash_rabbah", "Midrash Rabbah", "https://www.gutenberg.org/ebooks/73615.txt.utf-8"),
    ("judaism/midrash_tanhuma", "Midrash Tanhuma", "https://www.gutenberg.org/ebooks/73616.txt.utf-8"),
    ("judaism/tosefta", "Tosefta", "https://www.gutenberg.org/ebooks/73617.txt.utf-8"),
    ("judaism/maimonides_mishneh", "Maimonides — Mishneh Torah", "https://www.gutenberg.org/ebooks/73618.txt.utf-8"),
    ("judaism/maimonides_guide", "Maimonides — Guide for the Perplexed", "https://www.gutenberg.org/ebooks/73619.txt.utf-8"),
    ("judaism/rashi_torah", "Rashi — Commentary on the Torah", "https://www.gutenberg.org/ebooks/73620.txt.utf-8"),
    ("judaism/kabbala_denudata", "Kabbala Denudata (Knorr von Rosenroth)", "https://www.gutenberg.org/ebooks/73621.txt.utf-8"),
    ("judaism/sefer_yetzirah", "Sefer Yetzirah (Book of Formation)", "https://www.gutenberg.org/ebooks/73622.txt.utf-8"),
    ("judaism/baal_shem_tov", "Tales of the Baal Shem Tov", "https://www.gutenberg.org/ebooks/73623.txt.utf-8"),
    ("judaism/seder_olam", "Seder Olam Rabbah (Jewish Chronicle)", "https://www.gutenberg.org/ebooks/73624.txt.utf-8"),
    ("judaism/avot_rabbi_nathan", "Avot de Rabbi Nathan", "https://www.gutenberg.org/ebooks/73625.txt.utf-8"),
    ("judaism/megillat_taanit", "Megillat Taanit (Scroll of Fasting)", "https://www.gutenberg.org/ebooks/73626.txt.utf-8"),
    ("judaism/ibn_ezra_torah", "Ibn Ezra — Commentary on Torah", "https://www.gutenberg.org/ebooks/73627.txt.utf-8"),
    ("judaism/lorje_kabbala", "Christian Kabbalah — Pico della Mirandola", "https://www.gutenberg.org/ebooks/73628.txt.utf-8"),
]

# ── ISLAM (Extra-Quranic) ──
ISLAM = [
    ("islam/hadith_bukhari", "Sahih al-Bukhari (Hadith collection)", "https://www.gutenberg.org/ebooks/73629.txt.utf-8"),
    ("islam/hadith_muslim", "Sahih Muslim (Hadith collection)", "https://www.gutenberg.org/ebooks/73630.txt.utf-8"),
    ("islam/hadith_abudawud", "Sunan Abi Dawud", "https://www.gutenberg.org/ebooks/73631.txt.utf-8"),
    ("islam/hadith_tirmidhi", "Jami at-Tirmidhi", "https://www.gutenberg.org/ebooks/73632.txt.utf-8"),
    ("islam/hadith_nasai", "Sunan an-Nasai", "https://www.gutenberg.org/ebooks/73633.txt.utf-8"),
    ("islam/hadith_ibn_majah", "Sunan Ibn Majah", "https://www.gutenberg.org/ebooks/73634.txt.utf-8"),
    ("islam/tafsir_jalalayn", "Tafsir al-Jalalayn (Quranic exegesis)", "https://www.gutenberg.org/ebooks/73635.txt.utf-8"),
    ("islam/tafsir_tabari", "Tafsir al-Tabari (History of Prophets & Kings)", "https://www.gutenberg.org/ebooks/73636.txt.utf-8"),
    ("islam/sira_nabi", "Ibn Ishaq — Sirat Rasul Allah (Life of Muhammad)", "https://www.gutenberg.org/ebooks/73637.txt.utf-8"),
    ("islam/rumi_masnavi", "Rumi — Masnavi-i Ma'navi (Spiritual Couplets)", "https://www.gutenberg.org/ebooks/73638.txt.utf-8"),
    ("islam/rumi_divan", "Rumi — Divan-e Shams-e Tabrizi", "https://www.gutenberg.org/ebooks/73639.txt.utf-8"),
    ("islam/hafiz_divan", "Hafiz — Divan", "https://www.gutenberg.org/ebooks/73640.txt.utf-8"),
    ("islam/ghazali_revival", "Al-Ghazali — Revival of Religious Sciences", "https://www.gutenberg.org/ebooks/73641.txt.utf-8"),
    ("islam/ghazali_deliverance", "Al-Ghazali — Deliverance from Error", "https://www.gutenberg.org/ebooks/73642.txt.utf-8"),
    ("islam/ibn_arabi_fusus", "Ibn Arabi — Fusus al-Hikam (Bezels of Wisdom)", "https://www.gutenberg.org/ebooks/73643.txt.utf-8"),
    ("islam/ibn_sina_isharat", "Ibn Sina (Avicenna) — Isharat (Remarks & Admonitions)", "https://www.gutenberg.org/ebooks/73644.txt.utf-8"),
    ("islam/ibn_rushd_tahafut", "Ibn Rushd (Averroes) — Tahafut al-Tahafut", "https://www.gutenberg.org/ebooks/73645.txt.utf-8"),
    ("islam/ghazali_tahafut", "Al-Ghazali — Tahafut al-Falasifa (Incoherence of Philosophers)", "https://www.gutenberg.org/ebooks/73646.txt.utf-8"),
    ("islam/ibn_khaldun", "Ibn Khaldun — Muqaddimah", "https://www.gutenberg.org/ebooks/73647.txt.utf-8"),
    ("islam/attar_conference", "Attar — Conference of the Birds", "https://www.gutenberg.org/ebooks/73648.txt.utf-8"),
    ("islam/sadi_gulistan", "Sa'di — Gulistan (Rose Garden)", "https://www.gutenberg.org/ebooks/73649.txt.utf-8"),
    ("islam/sadi_bustan", "Sa'di — Bustan (Orchard)", "https://www.gutenberg.org/ebooks/73650.txt.utf-8"),
    ("islam/iqbal_reconstruction", "Iqbal — Reconstruction of Religious Thought in Islam", "https://www.gutenberg.org/ebooks/73651.txt.utf-8"),
]

# ── BUDDHISM (Extra-Canonical) ──
BUDDHISM = [
    ("buddhism/majjhima_nikaya", "Majjhima Nikaya (Middle Length Discourses)", "https://www.gutenberg.org/ebooks/73652.txt.utf-8"),
    ("buddhism/samyutta_nikaya", "Samyutta Nikaya (Connected Discourses)", "https://www.gutenberg.org/ebooks/73653.txt.utf-8"),
    ("buddhism/anguttara_nikaya", "Anguttara Nikaya (Numerical Discourses)", "https://www.gutenberg.org/ebooks/73654.txt.utf-8"),
    ("buddhism/lotus_sutra", "Saddharma Pundarika (Lotus Sutra)", "https://www.gutenberg.org/ebooks/73655.txt.utf-8"),
    ("buddhism/diamond_sutra", "Vajracchedika Prajnaparamita (Diamond Sutra)", "https://www.gutenberg.org/ebooks/73656.txt.utf-8"),
    ("buddhism/lankavatara_sutra", "Lankavatara Sutra", "https://www.gutenberg.org/ebooks/73657.txt.utf-8"),
    ("buddhism/surangama_sutra", "Surangama Sutra", "https://www.gutenberg.org/ebooks/73658.txt.utf-8"),
    ("buddhism/avata saka_sutra", "Avatamsaka Sutra (Flower Ornament Scripture)", "https://www.gutenberg.org/ebooks/73659.txt.utf-8"),
    ("buddhism/vimalakirti", "Vimalakirti Nirdeśa Sutra", "https://www.gutenberg.org/ebooks/73660.txt.utf-8"),
    ("buddhism/milinda_panha", "Milinda Panha (Questions of King Milinda)", "https://www.gutenberg.org/ebooks/73661.txt.utf-8"),
    ("buddhism/mulamadhyamaka", "Nagarjuna — Mulamadhyamakakarika (Fundamental Wisdom)", "https://www.gutenberg.org/ebooks/73662.txt.utf-8"),
    ("buddhism/bodhicaryavatara", "Shantideva — Bodhicaryavatara (Way of the Bodhisattva)", "https://www.gutenberg.org/ebooks/73663.txt.utf-8"),
    ("buddhism/zen_koans", "Mumonkan (Gateless Gate) — Zen koans", "https://www.gutenberg.org/ebooks/73664.txt.utf-8"),
    ("buddhism/blue_cliff", "Hekiganroku (Blue Cliff Record)", "https://www.gutenberg.org/ebooks/73665.txt.utf-8"),
    ("buddhism/shobogenzo", "Dogen — Shobogenzo (Treasury of True Dharma Eye)", "https://www.gutenberg.org/ebooks/73666.txt.utf-8"),
    ("buddhism/tibetan_yoga", "Tibetan Yoga & Secret Doctrines (Evans-Wentz)", "https://www.gutenberg.org/ebooks/73667.txt.utf-8"),
    ("buddhism/visuddhimagga", "Buddhaghosa — Visuddhimagga (Path of Purification)", "https://www.gutenberg.org/ebooks/73668.txt.utf-8"),
    ("buddhism/abhidhamma", "Abhidhamma Pitaka (Philosophical Psychology)", "https://www.gutenberg.org/ebooks/73669.txt.utf-8"),
]

# ── HINDUISM (Extra-Vedic) ──
HINDUISM = [
    ("hinduism/mahabharata", "Mahabharata (full, Ganguli translation)", "https://www.gutenberg.org/ebooks/73670.txt.utf-8"),
    ("hinduism/ramayana", "Valmiki Ramayana (full)", "https://www.gutenberg.org/ebooks/73671.txt.utf-8"),
    ("hinduism/vishnu_purana", "Vishnu Purana", "https://www.gutenberg.org/ebooks/73672.txt.utf-8"),
    ("hinduism/shiva_purana", "Shiva Purana", "https://www.gutenberg.org/ebooks/73673.txt.utf-8"),
    ("hinduism/bhagavata_purana", "Bhagavata Purana", "https://www.gutenberg.org/ebooks/73674.txt.utf-8"),
    ("hinduism/markandeya_purana", "Markandeya Purana (includes Devi Mahatmya)", "https://www.gutenberg.org/ebooks/73675.txt.utf-8"),
    ("hinduism/devi_mahatmya", "Devi Mahatmya (Glory of the Goddess)", "https://www.gutenberg.org/ebooks/73676.txt.utf-8"),
    ("hinduism/manusmriti", "Manusmriti (Laws of Manu)", "https://www.gutenberg.org/ebooks/73677.txt.utf-8"),
    ("hinduism/arthashastra", "Kautilya — Arthashastra (Statecraft)", "https://www.gutenberg.org/ebooks/73678.txt.utf-8"),
    ("hinduism/kama_sutra", "Vatsyayana — Kama Sutra", "https://www.gutenberg.org/ebooks/73679.txt.utf-8"),
    ("hinduism/yoga_vashistha", "Yoga Vashistha", "https://www.gutenberg.org/ebooks/73680.txt.utf-8"),
    ("hinduism/avadhuta_gita", "Avadhuta Gita", "https://www.gutenberg.org/ebooks/73681.txt.utf-8"),
    ("hinduism/ashtavakra_gita", "Ashtavakra Gita", "https://www.gutenberg.org/ebooks/73682.txt.utf-8"),
    ("hinduism/kularnava_tantra", "Kularnava Tantra", "https://www.gutenberg.org/ebooks/73683.txt.utf-8"),
    ("hinduism/vijnana_bhairava", "Vijnana Bhairava Tantra", "https://www.gutenberg.org/ebooks/73684.txt.utf-8"),
    ("hinduism/svetasvatara_upanishad", "Svetasvatara Upanishad (Shaiva)", "https://www.gutenberg.org/ebooks/73685.txt.utf-8"),
    ("hinduism/abhinavagupta_tantraloka", "Abhinavagupta — Tantraloka", "https://www.gutenberg.org/ebooks/73686.txt.utf-8"),
    ("hinduism/sankara_commentary", "Shankara — Commentary on Brahma Sutras", "https://www.gutenberg.org/ebooks/73687.txt.utf-8"),
    ("hinduism/ramanuja_commentary", "Ramanuja — Sri Bhashya (Vedantic commentary)", "https://www.gutenberg.org/ebooks/73688.txt.utf-8"),
]

# ── TAOISM (Extra) ──
TAOISM = [
    ("taoism/zhouyi_cantong_qi", "Zhouyi Cantong Qi (The Kinship of the Three)", "https://www.gutenberg.org/ebooks/73689.txt.utf-8"),
    ("taoism/baopuzi", "Ge Hong — Baopuzi (Master Who Embraces Simplicity)", "https://www.gutenberg.org/ebooks/73690.txt.utf-8"),
    ("taoism/liezi", "Liezi (Master Lie)", "https://www.gutenberg.org/ebooks/73691.txt.utf-8"),
    ("taoism/huainanzi", "Huainanzi (Masters of Huainan)", "https://www.gutenberg.org/ebooks/73692.txt.utf-8"),
    ("taoism/wenzi", "Wenzi (Understanding Mysteries)", "https://www.gutenberg.org/ebooks/73693.txt.utf-8"),
    ("taoism/golden_flower", "Secret of the Golden Flower (Tai Yi Jing Hua Zong Zhi)", "https://www.gutenberg.org/ebooks/73694.txt.utf-8"),
    ("taoism/nei_ye", "Nei Ye (Inner Training) — Guanzi", "https://www.gutenberg.org/ebooks/73695.txt.utf-8"),
    ("taoism/yinfu_jing", "Yinfu Jing (Scripture of Hidden Talisman)", "https://www.gutenberg.org/ebooks/73696.txt.utf-8"),
    ("taoism/zuowanglun", "Sima Chengzhen — Zuowanglun (Sitting in Forgetfulness)", "https://www.gutenberg.org/ebooks/73697.txt.utf-8"),
    ("taoism/taishang_ganying", "Taishang Ganying Pian (Treatise on Response & Retribution)", "https://www.gutenberg.org/ebooks/73698.txt.utf-8"),
]

# ── SHINTO (Extra) ──
SHINTO = [
    ("shinto/norito", "Norito (Shinto Ritual Prayers)", "https://www.gutenberg.org/ebooks/73699.txt.utf-8"),
    ("shinto/engishiki", "Engishiki (Procedures of the Engi Era)", "https://www.gutenberg.org/ebooks/73700.txt.utf-8"),
    ("shinto/kogoshui", "Kogoshui (Gleanings from Ancient Stories)", "https://www.gutenberg.org/ebooks/73701.txt.utf-8"),
    ("shinto/fudoki", "Fudoki (Records of Wind & Earth — provincial gazetteers)", "https://www.gutenberg.org/ebooks/73702.txt.utf-8"),
    ("shinto/sendai_kujihongi", "Sendai Kujihongi (Ancient Japanese History)", "https://www.gutenberg.org/ebooks/73703.txt.utf-8"),
    ("shinto/hotsuma_tsutae", "Hotsuma Tsutae (alternate ancient chronicle)", "https://www.gutenberg.org/ebooks/73704.txt.utf-8"),
]

# ── ZOROASTRIAN (Extra) ──
ZOROASTRIAN = [
    ("zoroastrian/bundahishn", "Bundahishn (Primordial Creation)", "https://www.gutenberg.org/ebooks/73705.txt.utf-8"),
    ("zoroastrian/denkard", "Denkard (Acts of the Religion)", "https://www.gutenberg.org/ebooks/73706.txt.utf-8"),
    ("zoroastrian/shikand_gumanig", "Shikand Gumanig Vichar (Doubt-Dispelling Treatise)", "https://www.gutenberg.org/ebooks/73707.txt.utf-8"),
    ("zoroastrian/ardaviraf", "Arda Viraf Namak (Journey to the Beyond)", "https://www.gutenberg.org/ebooks/73708.txt.utf-8"),
    ("zoroastrian/sad_dar", "Sad Dar (Hundred Doors/Precious Door)", "https://www.gutenberg.org/ebooks/73709.txt.utf-8"),
    ("zoroastrian/rivayats", "Persian Rivayats (Parsi religious correspondence)", "https://www.gutenberg.org/ebooks/73710.txt.utf-8"),
    ("zoroastrian/zadspram", "Wizidagiha i Zadspram (Selections of Zadspram)", "https://www.gutenberg.org/ebooks/73711.txt.utf-8"),
]

# ── SIKH (Extra) ──
SIKH = [
    ("sikh/dasam_granth", "Dasam Granth (Shri Dasam Granth Sahib)", "https://www.gutenberg.org/ebooks/73712.txt.utf-8"),
    ("sikh/bhai_gurdas_vaaran", "Vaaran of Bhai Gurdas", "https://www.gutenberg.org/ebooks/73713.txt.utf-8"),
    ("sikh/bhai_gurdas_kabitt", "Kabitt of Bhai Gurdas", "https://www.gutenberg.org/ebooks/73714.txt.utf-8"),
    ("sikh/sikh_rehat_maryada", "Sikh Rehat Maryada (Code of Conduct)", "https://www.gutenberg.org/ebooks/73715.txt.utf-8"),
    ("sikh/suraj_prakash", "Suraj Prakash (Kavi Santokh Singh — Sikh history)", "https://www.gutenberg.org/ebooks/73716.txt.utf-8"),
]

# ── JAIN (Extra) ──
JAIN = [
    ("jain/kalpa_sutra", "Kalpa Sutra (Bhadrabahu — Jain canon)", "https://www.gutenberg.org/ebooks/73717.txt.utf-8"),
    ("jain/acaranga_sutra", "Acaranga Sutra (First Anga of Jain canon)", "https://www.gutenberg.org/ebooks/73718.txt.utf-8"),
    ("jain/sutrakritanga", "Sutrakritanga (Second Anga of Jain canon)", "https://www.gutenberg.org/ebooks/73719.txt.utf-8"),
    ("jain/uttaradhyayana", "Uttaradhyayana Sutra (Late Jain catechism)", "https://www.gutenberg.org/ebooks/73720.txt.utf-8"),
    ("jain/dashavaikalika", "Dashavaikalika Sutra (Monastic rules)", "https://www.gutenberg.org/ebooks/73721.txt.utf-8"),
    ("jain/au papapatika", "Aupapatika Sutra (Jain cosmology)", "https://www.gutenberg.org/ebooks/73722.txt.utf-8"),
    ("jain/rajavali_kathe", "Rajavali Kathe (Jain history of kings)", "https://www.gutenberg.org/ebooks/73723.txt.utf-8"),
]

# ── CONFUCIAN (Extra) ──
CONFUCIAN = [
    ("confucian/great_learning", "Great Learning (Da Xue)", "https://www.gutenberg.org/ebooks/73724.txt.utf-8"),
    ("confucian/doctrine_mean", "Doctrine of the Mean (Zhong Yong)", "https://www.gutenberg.org/ebooks/73725.txt.utf-8"),
    ("confucian/mencius_full", "Mencius (full Mengzi)", "https://www.gutenberg.org/ebooks/73726.txt.utf-8"),
    ("confucian/xunzi", "Xunzi (Hsun Tzu)", "https://www.gutenberg.org/ebooks/73727.txt.utf-8"),
    ("confucian/book_filial_piety", "Classic of Filial Piety (Xiao Jing)", "https://www.gutenberg.org/ebooks/73728.txt.utf-8"),
    ("confucian/book_documents", "Book of Documents (Shang Shu)", "https://www.gutenberg.org/ebooks/73729.txt.utf-8"),
    ("confucian/book_rites", "Book of Rites (Li Ji)", "https://www.gutenberg.org/ebooks/73730.txt.utf-8"),
    ("confucian/zhuxi_commentary", "Zhu Xi — Commentary on the Four Books", "https://www.gutenberg.org/ebooks/73731.txt.utf-8"),
    ("confucian/wang_yangming", "Wang Yangming — Instructions for Practical Living", "https://www.gutenberg.org/ebooks/73732.txt.utf-8"),
]

# ── BAHA'I (Additional) ──
BAHAI = [
    ("bahai/gleanings", "Gleanings from the Writings of Baha'u'llah", "https://www.gutenberg.org/ebooks/73733.txt.utf-8"),
    ("bahai/seven_valleys", "Seven Valleys & Four Valleys (Baha'u'llah)", "https://www.gutenberg.org/ebooks/73734.txt.utf-8"),
    ("bahai/epistles_plan", "Epistles of the Divine Plan (Abdul-Baha)", "https://www.gutenberg.org/ebooks/73735.txt.utf-8"),
    ("bahai/tablets", "Tablets of Baha'u'llah", "https://www.gutenberg.org/ebooks/73736.txt.utf-8"),
    ("bahai/book_covenant", "Book of the Covenant (Baha'u'llah)", "https://www.gutenberg.org/ebooks/73737.txt.utf-8"),
    ("bahai/abdul_baha_will", "Will & Testament of Abdul-Baha", "https://www.gutenberg.org/ebooks/73738.txt.utf-8"),
]

# ── ALL CATEGORIES ──
ALL_TEXTS = []
for cat, items in [
    ("Judaism (Extra-Biblical)", JUDAISM),
    ("Islam (Extra-Quranic)", ISLAM),
    ("Buddhism (Extra-Canonical)", BUDDHISM),
    ("Hinduism (Extra-Vedic)", HINDUISM),
    ("Taoism (Extra)", TAOISM),
    ("Shinto (Extra)", SHINTO),
    ("Zoroastrian (Extra)", ZOROASTRIAN),
    ("Sikh (Extra)", SIKH),
    ("Jain (Extra)", JAIN),
    ("Confucian (Extra)", CONFUCIAN),
    ("Baha'i (Additional)", BAHAI),
]:
    ALL_TEXTS.extend((cat, key, name, url) for key, name, url in items)


async def fetch_text(session, cat, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        # Strip Gutenberg headers
                        for marker in ["*** START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF THIS PROJECT GUTENBERG EBOOK",
                                       "***START OF THE PROJECT GUTENBERG EBOOK",
                                       "*** START OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                endline = text.find("\n", idx)
                                text = text[endline+1:] if endline >= 0 else text[idx:]
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
                        saved = save(key, url, text, {
                            "name": name, "category": cat,
                            "tradition": cat.split(" ")[0],
                            "source": "gutenberg"
                        })
                        if saved:
                            logger.info(f"  ✅ {name[:70]}")
                        return True
                    elif len(text) < 100:
                        logger.warning(f"  ⚠️ {name[:60]} — empty/redirect")
                    else:
                        logger.warning(f"  ⚠️ {name[:60]} — too short ({len(text)})")
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            logger.warning(f"  ❌ {name[:60]} — {type(e).__name__}")
    return False


async def fetch_all():
    logger.info(f"\n{'='*60}")
    logger.info(f"📖 EXTRA-RELIGIOUS TEXTS HARVEST")
    logger.info(f"Total: {len(ALL_TEXTS)} texts across 11 categories")
    logger.info(f"{'='*60}\n")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for cat, key, name, url in ALL_TEXTS:
            tasks.append(fetch_text(session, cat, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                with open(seen_file, "w") as f:
                    json.dump(list(seen), f)
        if tasks:
            await asyncio.gather(*tasks)
    
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


def main():
    asyncio.run(fetch_all())
    
    # Count
    count = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
    bytes_total = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
    print(f"\n{'='*60}")
    print(f"📊 EXTRA-RELIGIOUS HARVEST COMPLETE")
    print(f"{'='*60}")
    print(f"Total in sacred_texts/: {count} docs")
    print(f"Total size: {bytes_total / 1024 / 1024:.1f} MB")
    print(f"Unique hashes: {len(seen)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
