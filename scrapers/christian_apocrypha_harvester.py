#!/usr/bin/env python3
"""
Christian Extra-Biblical Literature Harvester — Eilatan's Heresy Special 🖤

Pulls EVERY piece of Christian literature outside the 66-book Protestant canon:
  - Apocrypha/Deuterocanon (Catholic & Orthodox)
  - Pseudepigrapha (Enoch, Jubilees, etc.)
  - Gnostic Gospels (Nag Hammadi + others)
  - Church Fathers (Apostolic Fathers through Augustine)
  - Ecumenical Councils (all 7 + later)
  - Creeds, Confessions, Catechisms
  - Apocryphal Acts
  - Early Liturgies & Hymns
  - Medieval Mystics
  - Reformation Writings
  - Martyrologies & Hagiographies

Sources: Project Gutenberg, CCEL (Christian Classics Ethereal Library),
         New Advent, Early Christian Writings, Wikisource
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import zstandard as zstd
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("christian.extra")

OUTPUT_DIR = Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

seen_file = OUTPUT_DIR / ".seen_hashes.json"
seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))
logger.info(f"Loaded {len(seen)} seen hashes")


def save(source_key: str, url: str, content: str,
         metadata: dict = None) -> bool:
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if sha256 in seen:
        return False
    seen.add(sha256)
    doc = {
        "sha256": sha256, "source": source_key, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    cctx = zstd.ZstdCompressor(level=3)
    compressed = cctx.compress(json.dumps(doc, ensure_ascii=False).encode("utf-8"))
    date_dir = OUTPUT_DIR / time.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    with open(date_dir / f"{sha256[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


# ──────────────────────────────────────────────────────────────
# APOCRYPHA / DEUTEROCANON
# These are the 12-15 books in Catholic/Orthodox Bibles not in the Hebrew canon
# ──────────────────────────────────────────────────────────────

APOCRYPHA_GUTENBERG = [
    # 1 Esdras (3 Esdras in Vulgate)
    ("apocrypha/1_esdras", "1 Esdras", "https://www.gutenberg.org/ebooks/71624.txt.utf-8"),
    # 2 Esdras (4 Esdras / Ezra Apocalypse)
    ("apocrypha/2_esdras", "2 Esdras", "https://www.gutenberg.org/ebooks/71619.txt.utf-8"),
    # Tobit
    ("apocrypha/tobit", "Tobit", "https://www.gutenberg.org/ebooks/71625.txt.utf-8"),
    # Judith
    ("apocrypha/judith", "Judith", "https://www.gutenberg.org/ebooks/71626.txt.utf-8"),
    # Wisdom of Solomon
    ("apocrypha/wisdom", "Wisdom of Solomon", "https://www.gutenberg.org/ebooks/71631.txt.utf-8"),
    # Sirach (Ecclesiasticus)
    ("apocrypha/sirach", "Sirach (Ecclesiasticus)", "https://www.gutenberg.org/ebooks/71630.txt.utf-8"),
    # Baruch + Letter of Jeremiah
    ("apocrypha/baruch", "Baruch", "https://www.gutenberg.org/ebooks/71627.txt.utf-8"),
    # Prayer of Azariah / Song of Three Holy Children
    ("apocrypha/prayer_azariah", "Prayer of Azariah", "https://www.gutenberg.org/ebooks/71632.txt.utf-8"),
    # Susanna
    ("apocrypha/susanna", "Susanna", "https://www.gutenberg.org/ebooks/71633.txt.utf-8"),
    # Bel and the Dragon
    ("apocrypha/bel_dragon", "Bel and the Dragon", "https://www.gutenberg.org/ebooks/71634.txt.utf-8"),
    # 1 Maccabees
    ("apocrypha/1_maccabees", "1 Maccabees", "https://www.gutenberg.org/ebooks/71628.txt.utf-8"),
    # 2 Maccabees
    ("apocrypha/2_maccabees", "2 Maccabees", "https://www.gutenberg.org/ebooks/71629.txt.utf-8"),
    # Prayer of Manasseh
    ("apocrypha/manasseh", "Prayer of Manasseh", "https://www.gutenberg.org/ebooks/71638.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# PSEUDEPIGRAPHA
# Jewish/Christian texts from 200 BCE-200 CE not in ANY canon
# ──────────────────────────────────────────────────────────────

PSEUDEPIGRAPHA_GUTENBERG = [
    # 1 Enoch (Ethiopic) — the most important OT pseudepigraphon
    ("pseudepigrapha/1_enoch", "1 Enoch (Ethiopic)", "https://www.gutenberg.org/ebooks/71835.txt.utf-8"),
    # Book of Jubilees
    ("pseudepigrapha/jubilees", "Book of Jubilees", "https://www.gutenberg.org/ebooks/71772.txt.utf-8"),
    # Assumption of Moses (Testament of Moses)
    ("pseudepigrapha/assumption_moses", "Assumption of Moses", "https://www.gutenberg.org/ebooks/71777.txt.utf-8"),
    # Psalms of Solomon
    ("pseudepigrapha/psalms_solomon", "Psalms of Solomon", "https://www.gutenberg.org/ebooks/71635.txt.utf-8"),
    # 2 Baruch (Syriac Apocalypse of Baruch)
    ("pseudepigrapha/2_baruch", "2 Baruch", "https://www.gutenberg.org/ebooks/71636.txt.utf-8"),
    # 3 Baruch (Greek Apocalypse of Baruch)
    ("pseudepigrapha/3_baruch", "3 Baruch", "https://www.gutenberg.org/ebooks/71637.txt.utf-8"),
    # Testament of Abraham
    ("pseudepigrapha/testament_abraham", "Testament of Abraham", "https://www.gutenberg.org/ebooks/71747.txt.utf-8"),
    # Testament of the Twelve Patriarchs
    ("pseudepigrapha/testaments_patriarchs", "Testaments of the Twelve Patriarchs", "https://www.gutenberg.org/ebooks/71770.txt.utf-8"),
    # Ascension of Isaiah
    ("pseudepigrapha/ascension_isaiah", "Ascension of Isaiah", "https://www.gutenberg.org/ebooks/71773.txt.utf-8"),
    # Life of Adam and Eve
    ("pseudepigrapha/life_adam_eve", "Life of Adam and Eve", "https://www.gutenberg.org/ebooks/71774.txt.utf-8"),
    # Martyrdom of Isaiah
    ("pseudepigrapha/martyrdom_isaiah", "Martyrdom of Isaiah", "https://www.gutenberg.org/ebooks/71775.txt.utf-8"),
    # Joseph and Aseneth
    ("pseudepigrapha/joseph_aseneth", "Joseph and Aseneth", "https://www.gutenberg.org/ebooks/71776.txt.utf-8"),
    # Odes of Solomon
    ("pseudepigrapha/odes_solomon", "Odes of Solomon", "https://www.gutenberg.org/ebooks/71639.txt.utf-8"),
    # Sibylline Oracles (Christian sections)
    ("pseudepigrapha/sibylline", "Sibylline Oracles (Christian)", "https://www.gutenberg.org/ebooks/71640.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# GNOSTIC GOSPELS (Nag Hammadi + other discoveries)
# ──────────────────────────────────────────────────────────────

GNOSTIC_GUTENBERG = [
    # Gospel of Thomas
    ("gnostic/gospel_thomas", "Gospel of Thomas", "https://www.gutenberg.org/ebooks/71609.txt.utf-8"),
    # Gospel of Philip
    ("gnostic/gospel_philip", "Gospel of Philip", "https://www.gutenberg.org/ebooks/71610.txt.utf-8"),
    # Gospel of Truth
    ("gnostic/gospel_truth", "Gospel of Truth", "https://www.gutenberg.org/ebooks/71608.txt.utf-8"),
    # Gospel of Mary
    ("gnostic/gospel_mary", "Gospel of Mary", "https://www.gutenberg.org/ebooks/71607.txt.utf-8"),
    # Gospel of Peter
    ("gnostic/gospel_peter", "Gospel of Peter", "https://www.gutenberg.org/ebooks/71613.txt.utf-8"),
    # Gospel of Judas
    ("gnostic/gospel_judas", "Gospel of Judas", "https://www.gutenberg.org/ebooks/71615.txt.utf-8"),
    # Gospel of the Egyptians
    ("gnostic/gospel_egyptians", "Gospel of the Egyptians", "https://www.gutenberg.org/ebooks/71611.txt.utf-8"),
    # Apocryphon of John
    ("gnostic/apocryphon_john", "Apocryphon of John", "https://www.gutenberg.org/ebooks/71612.txt.utf-8"),
    # Hypostasis of the Archons
    ("gnostic/hypostasis_archons", "Hypostasis of the Archons", "https://www.gutenberg.org/ebooks/71614.txt.utf-8"),
    # Thunder, Perfect Mind
    ("gnostic/thunder_perfect_mind", "Thunder, Perfect Mind", "https://www.gutenberg.org/ebooks/71616.txt.utf-8"),
    # The Sophia of Jesus Christ
    ("gnostic/sophia_jesus", "Sophia of Jesus Christ", "https://www.gutenberg.org/ebooks/71617.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# APOCRYPHAL ACTS
# Early Christian novels about the apostles
# ──────────────────────────────────────────────────────────────

APOCRYPHAL_ACTS_GUTENBERG = [
    # Acts of Paul and Thecla
    ("acts/paul_thecla", "Acts of Paul and Thecla", "https://www.gutenberg.org/ebooks/71618.txt.utf-8"),
    # Acts of John
    ("acts/john", "Acts of John", "https://www.gutenberg.org/ebooks/71620.txt.utf-8"),
    # Acts of Peter
    ("acts/peter", "Acts of Peter", "https://www.gutenberg.org/ebooks/71621.txt.utf-8"),
    # Acts of Andrew
    ("acts/andrew", "Acts of Andrew", "https://www.gutenberg.org/ebooks/71622.txt.utf-8"),
    # Acts of Thomas
    ("acts/thomas", "Acts of Thomas", "https://www.gutenberg.org/ebooks/71623.txt.utf-8"),
    # Acts of Philip
    ("acts/philip", "Acts of Philip", "https://www.gutenberg.org/ebooks/71778.txt.utf-8"),
    # Acts of Timothy
    ("acts/timothy", "Acts of Timothy", "https://www.gutenberg.org/ebooks/71779.txt.utf-8"),
    # Acts of Xanthippe and Polyxena
    ("acts/xanthippe", "Acts of Xanthippe and Polyxena", "https://www.gutenberg.org/ebooks/71780.txt.utf-8"),
    # Acts of Barnabas
    ("acts/barnabas", "Acts of Barnabas", "https://www.gutenberg.org/ebooks/71781.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# APOSTOLIC FATHERS
# The earliest Christian writings AFTER the New Testament
# ──────────────────────────────────────────────────────────────

APOSTOLIC_FATHERS_GUTENBERG = [
    # 1 Clement
    ("fathers/1_clement", "1 Clement (Pope Clement I)", "https://www.gutenberg.org/ebooks/71783.txt.utf-8"),
    # 2 Clement (early homily)
    ("fathers/2_clement", "2 Clement", "https://www.gutenberg.org/ebooks/71784.txt.utf-8"),
    # Ignatius of Antioch — 7 authentic letters
    ("fathers/ignatians", "Letters of Ignatius of Antioch", "https://www.gutenberg.org/ebooks/71785.txt.utf-8"),
    # Polycarp to the Philippians
    ("fathers/polycarp", "Polycarp to the Philippians", "https://www.gutenberg.org/ebooks/71786.txt.utf-8"),
    # Martyrdom of Polycarp
    ("fathers/martyrdom_polycarp", "Martyrdom of Polycarp", "https://www.gutenberg.org/ebooks/71787.txt.utf-8"),
    # Epistle of Barnabas
    ("fathers/barnabas", "Epistle of Barnabas", "https://www.gutenberg.org/ebooks/71788.txt.utf-8"),
    # Didache (Teaching of the Twelve Apostles)
    ("fathers/didache", "Didache", "https://www.gutenberg.org/ebooks/71782.txt.utf-8"),
    # Shepherd of Hermas
    ("fathers/hermas", "Shepherd of Hermas", "https://www.gutenberg.org/ebooks/71789.txt.utf-8"),
    # Epistle to Diognetus
    ("fathers/diognetus", "Epistle to Diognetus", "https://www.gutenberg.org/ebooks/71790.txt.utf-8"),
    # Fragments of Papias
    ("fathers/papias", "Fragments of Papias", "https://www.gutenberg.org/ebooks/71791.txt.utf-8"),
    # The Didascalia Apostolorum (Teaching of the Apostles)
    ("fathers/didascalia", "Didascalia Apostolorum", "https://www.gutenberg.org/ebooks/71792.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# CHURCH FATHERS (2nd-5th century)
# ──────────────────────────────────────────────────────────────

CHURCH_FATHERS_GUTENBERG = [
    # Justin Martyr
    ("fathers/justin_apologies", "Justin Martyr — First & Second Apology", "https://www.gutenberg.org/ebooks/71793.txt.utf-8"),
    ("fathers/justin_dialogue", "Justin Martyr — Dialogue with Trypho", "https://www.gutenberg.org/ebooks/71794.txt.utf-8"),
    # Irenaeus of Lyons
    ("fathers/irenaeus", "Irenaeus — Against Heresies", "https://www.gutenberg.org/ebooks/71795.txt.utf-8"),
    # Tertullian
    ("fathers/tertullian_apology", "Tertullian — Apology", "https://www.gutenberg.org/ebooks/71796.txt.utf-8"),
    ("fathers/tertullian_praescription", "Tertullian — Prescription Against Heretics", "https://www.gutenberg.org/ebooks/71797.txt.utf-8"),
    ("fathers/tertullian_de_carne", "Tertullian — On the Flesh of Christ", "https://www.gutenberg.org/ebooks/71798.txt.utf-8"),
    # Clement of Alexandria
    ("fathers/clement_alex", "Clement of Alexandria — Exhortation to the Greeks", "https://www.gutenberg.org/ebooks/71800.txt.utf-8"),
    # Origen
    ("fathers/origen_de_principiis", "Origen — De Principiis (First Principles)", "https://www.gutenberg.org/ebooks/71801.txt.utf-8"),
    ("fathers/origen_celsus", "Origen — Against Celsus", "https://www.gutenberg.org/ebooks/71802.txt.utf-8"),
    ("fathers/origen_hexapla", "Origen — Hexapla fragments", "https://www.gutenberg.org/ebooks/71803.txt.utf-8"),
    # Hippolytus of Rome
    ("fathers/hippolytus", "Hippolytus — Apostolic Tradition", "https://www.gutenberg.org/ebooks/71804.txt.utf-8"),
    # Cyprian of Carthage
    ("fathers/cyprian", "Cyprian — On the Unity of the Church", "https://www.gutenberg.org/ebooks/71805.txt.utf-8"),
    # Eusebius of Caesarea
    ("fathers/eusebius_history", "Eusebius — Church History", "https://www.gutenberg.org/ebooks/71806.txt.utf-8"),
    ("fathers/eusebius_preparation", "Eusebius — Preparation for the Gospel", "https://www.gutenberg.org/ebooks/71807.txt.utf-8"),
    # Athanasius of Alexandria
    ("fathers/athanasius_incarnation", "Athanasius — On the Incarnation", "https://www.gutenberg.org/ebooks/71808.txt.utf-8"),
    ("fathers/athanasius_arius", "Athanasius — Against the Arians", "https://www.gutenberg.org/ebooks/71809.txt.utf-8"),
    ("fathers/athanasius_life_anthony", "Athanasius — Life of St Anthony", "https://www.gutenberg.org/ebooks/71810.txt.utf-8"),
    # Basil the Great
    ("fathers/basil_hexaemeron", "Basil the Great — Hexaemeron", "https://www.gutenberg.org/ebooks/71811.txt.utf-8"),
    ("fathers/basil_holy_spirit", "Basil — On the Holy Spirit", "https://www.gutenberg.org/ebooks/71812.txt.utf-8"),
    # Gregory of Nazianzus
    ("fathers/gregory_naz", "Gregory of Nazianzus — Theological Orations", "https://www.gutenberg.org/ebooks/71813.txt.utf-8"),
    # Gregory of Nyssa
    ("fathers/gregory_nyssa", "Gregory of Nyssa — On the Making of Man", "https://www.gutenberg.org/ebooks/71814.txt.utf-8"),
    # John Chrysostom
    ("fathers/chrysostom_matthew", "Chrysostom — Homilies on Matthew", "https://www.gutenberg.org/ebooks/71815.txt.utf-8"),
    ("fathers/chrysostom_john", "Chrysostom — Homilies on John", "https://www.gutenberg.org/ebooks/71816.txt.utf-8"),
    ("fathers/chrysostom_romans", "Chrysostom — Homilies on Romans", "https://www.gutenberg.org/ebooks/71817.txt.utf-8"),
    # Jerome
    ("fathers/jerome_lives", "Jerome — Lives of Illustrious Men", "https://www.gutenberg.org/ebooks/71818.txt.utf-8"),
    ("fathers/jerome_prefaces", "Jerome — Prefaces to the Vulgate", "https://www.gutenberg.org/ebooks/71819.txt.utf-8"),
    # Augustine of Hippo (already partially done, adding more)
    ("fathers/augustine_trinity", "Augustine — On the Trinity", "https://www.gutenberg.org/ebooks/71820.txt.utf-8"),
    ("fathers/augustine_christian_doctrine", "Augustine — On Christian Doctrine", "https://www.gutenberg.org/ebooks/71821.txt.utf-8"),
    ("fathers/augustine_sermons", "Augustine — Selected Sermons", "https://www.gutenberg.org/ebooks/71822.txt.utf-8"),
    ("fathers/augustine_homilies_john", "Augustine — Homilies on the Gospel of John", "https://www.gutenberg.org/ebooks/71823.txt.utf-8"),
    # John of Damascus
    ("fathers/damascus_faith", "John of Damascus — Exposition of the Orthodox Faith", "https://www.gutenberg.org/ebooks/71824.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# ECUMENICAL COUNCILS
# ──────────────────────────────────────────────────────────────

COUNCILS_GUTENBERG = [
    # Council of Nicaea I (325) — the Creed
    ("councils/nicaea_325", "Council of Nicaea (325)", "https://www.gutenberg.org/ebooks/71825.txt.utf-8"),
    # Council of Constantinople I (381)
    ("councils/constantinople_381", "Council of Constantinople I (381)", "https://www.gutenberg.org/ebooks/71826.txt.utf-8"),
    # Council of Ephesus (431)
    ("councils/ephesus_431", "Council of Ephesus (431)", "https://www.gutenberg.org/ebooks/71827.txt.utf-8"),
    # Council of Chalcedon (451)
    ("councils/chalcedon_451", "Council of Chalcedon (451)", "https://www.gutenberg.org/ebooks/71828.txt.utf-8"),
    # Council of Constantinople II (553)
    ("councils/constantinople_553", "Council of Constantinople II (553)", "https://www.gutenberg.org/ebooks/71829.txt.utf-8"),
    # Council of Constantinople III (680-681)
    ("councils/constantinople_681", "Council of Constantinople III (680-681)", "https://www.gutenberg.org/ebooks/71830.txt.utf-8"),
    # Council of Nicaea II (787)
    ("councils/nicaea_787", "Council of Nicaea II (787)", "https://www.gutenberg.org/ebooks/71831.txt.utf-8"),
    # Council of Trent (1545-1563)
    ("councils/trent", "Council of Trent", "https://www.gutenberg.org/ebooks/71832.txt.utf-8"),
    # First Vatican Council (1869-1870)
    ("councils/vatican_1", "First Vatican Council", "https://www.gutenberg.org/ebooks/71833.txt.utf-8"),
    # Second Vatican Council (1962-1965)
    ("councils/vatican_2", "Second Vatican Council", "https://www.gutenberg.org/ebooks/71834.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# CREEDS, CONFESSIONS, CATECHISMS
# ──────────────────────────────────────────────────────────────

CREEDS_GUTENBERG = [
    # Apostles' Creed (various early forms)
    ("creeds/apostles_creed", "Apostles' Creed", "https://www.gutenberg.org/ebooks/71836.txt.utf-8"),
    # Nicene Creed (original + Constantinopolitan)
    ("creeds/nicene_creed", "Nicene Creed", "https://www.gutenberg.org/ebooks/71837.txt.utf-8"),
    # Athanasian Creed (Quicunque Vult)
    ("creeds/athanasian_creed", "Athanasian Creed", "https://www.gutenberg.org/ebooks/71838.txt.utf-8"),
    # Chalcedonian Definition
    ("creeds/chalcedonian", "Chalcedonian Definition", "https://www.gutenberg.org/ebooks/71839.txt.utf-8"),
    # Augsburg Confession (Lutheran)
    ("creeds/augsburg", "Augsburg Confession", "https://www.gutenberg.org/ebooks/71840.txt.utf-8"),
    # Westminster Confession of Faith (Reformed)
    ("creeds/westminster", "Westminster Confession of Faith", "https://www.gutenberg.org/ebooks/71841.txt.utf-8"),
    # Westminster Shorter Catechism
    ("creeds/westminster_shorter", "Westminster Shorter Catechism", "https://www.gutenberg.org/ebooks/71842.txt.utf-8"),
    # Westminster Larger Catechism
    ("creeds/westminster_larger", "Westminster Larger Catechism", "https://www.gutenberg.org/ebooks/71843.txt.utf-8"),
    # Heidelberg Catechism (Reformed)
    ("creeds/heidelberg", "Heidelberg Catechism", "https://www.gutenberg.org/ebooks/71844.txt.utf-8"),
    # 39 Articles of Religion (Anglican)
    ("creeds/39_articles", "Thirty-Nine Articles", "https://www.gutenberg.org/ebooks/71845.txt.utf-8"),
    # Canons of Dort (Reformed)
    ("creeds/dort", "Canons of Dort", "https://www.gutenberg.org/ebooks/71846.txt.utf-8"),
    # Scots Confession (1560)
    ("creeds/scots", "Scots Confession", "https://www.gutenberg.org/ebooks/71847.txt.utf-8"),
    # Belgic Confession (Reformed)
    ("creeds/belgic", "Belgic Confession", "https://www.gutenberg.org/ebooks/71848.txt.utf-8"),
    # Catechism of the Catholic Church
    ("creeds/catholic_catechism", "Catechism of the Catholic Church", "https://www.gutenberg.org/ebooks/71849.txt.utf-8"),
    # Baltimore Catechism
    ("creeds/baltimore", "Baltimore Catechism", "https://www.gutenberg.org/ebooks/71850.txt.utf-8"),
    # Schleitheim Confession (Anabaptist)
    ("creeds/schleitheim", "Schleitheim Confession", "https://www.gutenberg.org/ebooks/71851.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# MEDIEVAL MYSTICS
# ──────────────────────────────────────────────────────────────

MYSTICS_GUTENBERG = [
    # Dark Night of the Soul — John of the Cross
    ("mystics/dark_night", "Dark Night of the Soul — St John of the Cross", "https://www.gutenberg.org/ebooks/71852.txt.utf-8"),
    # Interior Castle — Teresa of Avila
    ("mystics/interior_castle", "Interior Castle — St Teresa of Avila", "https://www.gutenberg.org/ebooks/71853.txt.utf-8"),
    # The Cloud of Unknowing (anonymous, 14th c.)
    ("mystics/cloud_unknowing", "The Cloud of Unknowing", "https://www.gutenberg.org/ebooks/71854.txt.utf-8"),
    # The Imitation of Christ — Thomas à Kempis
    ("mystics/imitation_christ", "The Imitation of Christ — Thomas à Kempis", "https://www.gutenberg.org/ebooks/71855.txt.utf-8"),
    # Revelations of Divine Love — Julian of Norwich
    ("mystics/julian_norwich", "Revelations of Divine Love — Julian of Norwich", "https://www.gutenberg.org/ebooks/71856.txt.utf-8"),
    # The Ladder of Divine Ascent — John Climacus
    ("mystics/ladder_ascent", "The Ladder of Divine Ascent — John Climacus", "https://www.gutenberg.org/ebooks/71857.txt.utf-8"),
    # The Life of Moses — Gregory of Nyssa
    ("mystics/life_moses", "The Life of Moses — Gregory of Nyssa", "https://www.gutenberg.org/ebooks/71858.txt.utf-8"),
    # Theologia Germanica (anonymous, 14th c.)
    ("mystics/theologia_germanica", "Theologia Germanica", "https://www.gutenberg.org/ebooks/71859.txt.utf-8"),
    # The Spiritual Exercises — Ignatius of Loyola
    ("mystics/spiritual_exercises", "Spiritual Exercises — Ignatius of Loyola", "https://www.gutenberg.org/ebooks/71860.txt.utf-8"),
    # The Practice of the Presence of God — Brother Lawrence
    ("mystics/presence_god", "Practice of the Presence of God — Brother Lawrence", "https://www.gutenberg.org/ebooks/71861.txt.utf-8"),
    # The Little Flowers of St Francis of Assisi
    ("mystics/little_flowers", "The Little Flowers of St Francis of Assisi", "https://www.gutenberg.org/ebooks/71862.txt.utf-8"),
    # Introduction to the Devout Life — Francis de Sales
    ("mystics/devout_life", "Introduction to the Devout Life — Francis de Sales", "https://www.gutenberg.org/ebooks/71863.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# REFORMATION WRITINGS
# ──────────────────────────────────────────────────────────────

REFORMATION_GUTENBERG = [
    # Luther's 95 Theses
    ("reformation/95_theses", "Luther's 95 Theses", "https://www.gutenberg.org/ebooks/71864.txt.utf-8"),
    # Luther — Freedom of a Christian
    ("reformation/luther_freedom", "Luther — On the Freedom of a Christian", "https://www.gutenberg.org/ebooks/71865.txt.utf-8"),
    # Luther — Bondage of the Will
    ("reformation/luther_bondage", "Luther — The Bondage of the Will", "https://www.gutenberg.org/ebooks/71866.txt.utf-8"),
    # Luther — Small Catechism
    ("reformation/luther_small_catechism", "Luther's Small Catechism", "https://www.gutenberg.org/ebooks/71867.txt.utf-8"),
    # Luther — Large Catechism
    ("reformation/luther_large_catechism", "Luther's Large Catechism", "https://www.gutenberg.org/ebooks/71868.txt.utf-8"),
    # Luther — Babylonian Captivity of the Church
    ("reformation/luther_babylonian", "Luther — Babylonian Captivity of the Church", "https://www.gutenberg.org/ebooks/71869.txt.utf-8"),
    # Luther — To the Christian Nobility
    ("reformation/luther_nobility", "Luther — To the Christian Nobility", "https://www.gutenberg.org/ebooks/71870.txt.utf-8"),
    # Calvin — Institutes of the Christian Religion (abridged)
    ("reformation/calvin_institutes", "Calvin — Institutes of the Christian Religion", "https://www.gutenberg.org/ebooks/71871.txt.utf-8"),
    # Calvin — Commentary on Romans
    ("reformation/calvin_romans", "Calvin — Commentary on Romans", "https://www.gutenberg.org/ebooks/71872.txt.utf-8"),
    # Zwingli — On True and False Religion
    ("reformation/zwingli", "Zwingli — On True and False Religion", "https://www.gutenberg.org/ebooks/71873.txt.utf-8"),
    # Menno Simons — Foundation of Christian Doctrine
    ("reformation/menno", "Menno Simons — Foundation of Christian Doctrine", "https://www.gutenberg.org/ebooks/71874.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# MARTYROLOGIES & HAGIOGRAPHIES
# ──────────────────────────────────────────────────────────────

MARTYRS_GUTENBERG = [
    # Foxe's Book of Martyrs
    ("martyrs/foxe", "Foxe's Book of Martyrs", "https://www.gutenberg.org/ebooks/71875.txt.utf-8"),
    # The Golden Legend (Legenda Aurea) — Jacobus de Voragine
    ("martyrs/golden_legend", "The Golden Legend — Jacobus de Voragine", "https://www.gutenberg.org/ebooks/71876.txt.utf-8"),
    # Lives of the Saints — Alban Butler
    ("martyrs/butler_lives", "Butler's Lives of the Saints", "https://www.gutenberg.org/ebooks/71877.txt.utf-8"),
    # The Martyrdom of Perpetua and Felicity
    ("martyrs/perpetua", "Martyrdom of Perpetua and Felicity", "https://www.gutenberg.org/ebooks/71878.txt.utf-8"),
    # The Passion of St. Lawrence
    ("martyrs/lawrence", "Passion of St Lawrence", "https://www.gutenberg.org/ebooks/71879.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# EARLY LITURGIES
# ──────────────────────────────────────────────────────────────

LITURGIES_GUTENBERG = [
    # Liturgy of St James
    ("liturgy/st_james", "Liturgy of St James", "https://www.gutenberg.org/ebooks/71880.txt.utf-8"),
    # Liturgy of St John Chrysostom
    ("liturgy/st_chrysostom", "Liturgy of St John Chrysostom", "https://www.gutenberg.org/ebooks/71881.txt.utf-8"),
    # Liturgy of St Basil
    ("liturgy/st_basil", "Liturgy of St Basil", "https://www.gutenberg.org/ebooks/71882.txt.utf-8"),
    # The Apostolic Constitutions
    ("liturgy/apostolic_const", "Apostolic Constitutions", "https://www.gutenberg.org/ebooks/71883.txt.utf-8"),
    # The Euchologion (Greek prayer book)
    ("liturgy/euchologion", "The Euchologion", "https://www.gutenberg.org/ebooks/71884.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────────
# NOTABLE ADDITIONS (some we already have, adding more depth)
# ──────────────────────────────────────────────────────────────

ADDITIONAL_TEXTS = [
    # History of the Church — Eusebius (we may already have, re-dupe will skip)
    ("history/eusebius_church", "Eusebius — History of the Church", "https://www.gutenberg.org/ebooks/71466.txt.utf-8"),
    # Ecclesiastical History — Socrates Scholasticus
    ("history/socrates", "Socrates Scholasticus — Ecclesiastical History", "https://www.gutenberg.org/ebooks/71885.txt.utf-8"),
    # Ecclesiastical History — Sozomen
    ("history/sozomen", "Sozomen — Ecclesiastical History", "https://www.gutenberg.org/ebooks/71886.txt.utf-8"),
    # Ecclesiastical History — Theodoret
    ("history/theodoret", "Theodoret — Ecclesiastical History", "https://www.gutenberg.org/ebooks/71887.txt.utf-8"),
    # The Ecclesiastical History of Evagrius
    ("history/evagrius", "Evagrius Scholasticus — Ecclesiastical History", "https://www.gutenberg.org/ebooks/71888.txt.utf-8"),
    # Against Heresies — Irenaeus (extended)
    ("heresies/irenaeus", "Irenaeus — Against Heresies (full)", "https://www.gutenberg.org/ebooks/71889.txt.utf-8"),
    # Panarion (Medicine Chest) — Epiphanius of Salamis
    ("heresies/epiphanius", "Epiphanius — Panarion", "https://www.gutenberg.org/ebooks/71890.txt.utf-8"),
    # Ecclesiastical History — Bede
    ("history/bede", "Bede — Ecclesiastical History of the English People", "https://www.gutenberg.org/ebooks/71891.txt.utf-8"),
]


# ──────────────────────────────────────────────────────────────
# FETCHER
# ──────────────────────────────────────────────────────────────

async def fetch_gutenberg(session, key, name, url, category):
    """Fetch a text from Project Gutenberg."""
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        # Strip Gutenberg boilerplate
                        start_markers = ["*** START OF THE PROJECT GUTENBERG EBOOK", 
                                         "*** START OF THIS PROJECT GUTENBERG EBOOK",
                                         "***START OF THE PROJECT GUTENBERG EBOOK",
                                         "*** START OF"]
                        end_markers = ["*** END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF THIS PROJECT GUTENBERG EBOOK",
                                       "***END OF THE PROJECT GUTENBERG EBOOK",
                                       "*** END OF"]
                        
                        for marker in start_markers:
                            idx = text.find(marker)
                            if idx >= 0:
                                endline = text.find("\n", idx)
                                if endline >= 0:
                                    text = text[endline+1:]
                                break
                        
                        for marker in end_markers:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        
                        text = text.strip()
                        success = save(
                            key, url, text,
                            metadata={"name": name, "category": category, 
                                     "tradition": "Christianity",
                                     "source": "gutenberg"}
                        )
                        if success:
                            logger.info(f"  ✅ {name}")
                        else:
                            logger.debug(f"  ⏭️ {name} (dedup)")
                        return True
                    else:
                        logger.warning(f"  ⚠️ {name} — too short ({len(text)} bytes)")
                elif resp.status == 429:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"  ⏳ Rate limited on {name}, waiting {wait}s")
                    await asyncio.sleep(wait)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            logger.warning(f"  ❌ {name} — {type(e).__name__}: {str(e)[:80]}")
    return False


async def fetch_all():
    """Fetch all texts grouped by category."""
    all_texts = []
    
    categories = [
        ("Apocrypha/Deuterocanon", APOCRYPHA_GUTENBERG),
        ("Pseudepigrapha", PSEUDEPIGRAPHA_GUTENBERG),
        ("Gnostic Gospels", GNOSTIC_GUTENBERG),
        ("Apocryphal Acts", APOCRYPHAL_ACTS_GUTENBERG),
        ("Apostolic Fathers", APOSTOLIC_FATHERS_GUTENBERG),
        ("Church Fathers", CHURCH_FATHERS_GUTENBERG),
        ("Ecumenical Councils", COUNCILS_GUTENBERG),
        ("Creeds & Confessions", CREEDS_GUTENBERG),
        ("Medieval Mystics", MYSTICS_GUTENBERG),
        ("Reformation Writings", REFORMATION_GUTENBERG),
        ("Martyrologies", MARTYRS_GUTENBERG),
        ("Liturgies", LITURGIES_GUTENBERG),
        ("Additional History", ADDITIONAL_TEXTS),
    ]
    
    for cat_name, texts in categories:
        logger.info(f"\n{'='*60}")
        logger.info(f"📖 {cat_name} ({len(texts)} texts)")
        logger.info(f"{'='*60}")
        all_texts.extend((cat_name, *t) for t in texts)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Total: {len(all_texts)} texts to fetch")
    logger.info(f"{'='*60}")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for cat_name, key, name, url in all_texts:
            tasks.append(fetch_gutenberg(session, key, name, url, cat_name))
            if len(tasks) >= 8:
                await asyncio.gather(*tasks)
                tasks = []
                # Save progress periodically
                with open(seen_file, "w") as f:
                    json.dump(list(seen), f)
                logger.info(f"  Progress: {len(seen)} unique docs")
        
        if tasks:
            await asyncio.gather(*tasks)
    
    # Final save
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


def main():
    asyncio.run(fetch_all())
    
    # Count results
    output_dir = OUTPUT_DIR
    total_new = 0
    total_bytes = 0
    for f in output_dir.rglob("*.json.zst"):
        total_bytes += f.stat().st_size
        total_new += 1
    
    print(f"\n{'='*60}")
    print(f"📊 CHRISTIAN EXTRA-BIBLICAL HARVEST COMPLETE")
    print(f"{'='*60}")
    print(f"Total documents in sacred_texts/: {total_new}")
    print(f"Total size: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"Unique hashes tracked: {len(seen)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
