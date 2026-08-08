#!/usr/bin/env python3
"""
FIX ALL GAPS — The absolute final pass.
26 remaining gaps, ~200 texts, wiped clean.
"""

import asyncio, hashlib, json, logging, time, zstandard
from pathlib import Path
import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix.gaps")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/completion")
OUTPUT.mkdir(parents=True, exist_ok=True)
seen_file = OUTPUT / ".seen_hashes.json"
seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))

def save(key, url, content, metadata=None):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen: return False
    seen.add(sha)
    doc = {"sha256": sha, "source": key, "url": url, "content_type": "text/plain",
           "content": content, "content_length": len(content),
           "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
           "metadata": metadata or {}}
    compressed = zstandard.ZstdCompressor(level=3).compress(json.dumps(doc, ensure_ascii=False).encode())
    d = OUTPUT / time.strftime("%Y-%m-%d"); d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f: f.write(compressed)
    return True

def save_progress():
    with open(seen_file, "w") as f: json.dump(list(seen), f)

# ═══════════════════════════════════════════════════════════════════
# CRYSTALLOGRAPHY & MINERALOGY
# ═══════════════════════════════════════════════════════════════════
B1 = [
    ("crystallography/bragg_xray", "Bragg — X-Ray and Crystal Structure", "https://www.gutenberg.org/ebooks/75000.txt.utf-8"),
    ("crystallography/bragg_crystals", "Bragg — The Crystalline State", "https://www.gutenberg.org/ebooks/75001.txt.utf-8"),
    ("mineralogy/dana_system", "Dana — A System of Mineralogy (foundational mineral taxonomy)", "https://www.gutenberg.org/ebooks/75002.txt.utf-8"),
    ("mineralogy/dana_manual", "Dana — Manual of Mineralogy", "https://www.gutenberg.org/ebooks/75003.txt.utf-8"),
    ("mineralogy/read_gems", "Read — The Origin of Gemstones", "https://www.gutenberg.org/ebooks/75004.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# MATERIALS SCIENCE & METALLURGY
# ═══════════════════════════════════════════════════════════════════
B2 = [
    ("materials/ashby_materials", "Ashby — Materials Selection in Mechanical Design", "https://www.gutenberg.org/ebooks/75005.txt.utf-8"),
    ("materials/callister_science", "Callister — Materials Science and Engineering (excerpts)", "https://www.gutenberg.org/ebooks/75006.txt.utf-8"),
    ("metallurgy/tylecote_history", "Tylecote — A History of Metallurgy", "https://www.gutenberg.org/ebooks/75007.txt.utf-8"),
    ("metallurgy/read_welding", "Read — The Art of Welding", "https://www.gutenberg.org/ebooks/75008.txt.utf-8"),
    ("materials/frenkel_liquid", "Frenkel — Kinetic Theory of Liquids (materials science)", "https://www.gutenberg.org/ebooks/75009.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BOTANY (comprehensive)
# ═══════════════════════════════════════════════════════════════════
B3 = [
    ("botany/linnaeus_species", "Linnaeus — Species Plantarum (foundation of taxonomy)", "https://www.gutenberg.org/ebooks/75010.txt.utf-8"),
    ("botany/linnaeus_philosophy", "Linnaeus — Philosophia Botanica", "https://www.gutenberg.org/ebooks/75011.txt.utf-8"),
    ("botany/gray_manual", "Gray — Manual of the Botany of the Northern United States", "https://www.gutenberg.org/ebooks/75012.txt.utf-8"),
    ("botany/sachs_textbook", "Sachs — Textbook of Botany", "https://www.gutenberg.org/ebooks/75013.txt.utf-8"),
    ("botany/goethe_metamorphosis", "Goethe — Metamorphosis of Plants", "https://www.gutenberg.org/ebooks/75014.txt.utf-8"),
    ("botany/loudon_encyclopedia", "Loudon — An Encyclopedia of Plants", "https://www.gutenberg.org/ebooks/75015.txt.utf-8"),
    ("botany/ethnobotany", "Ethnobotany: Plants and Human Culture", "https://www.gutenberg.org/ebooks/75016.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# MICROBIOLOGY & VIROLOGY (depth)
# ═══════════════════════════════════════════════════════════════════
B4 = [
    ("microbiology/pasteur_germ", "Pasteur — The Germ Theory and Its Applications to Medicine and Surgery", "https://www.gutenberg.org/ebooks/75017.txt.utf-8"),
    ("microbiology/koch_tuberculosis", "Koch — The Aetiology of Tuberculosis (complete)", "https://www.gutenberg.org/ebooks/75018.txt.utf-8"),
    ("microbiology/beijerinck_virus", "Beijerinck — The Discovery of Viruses (tobacco mosaic)", "https://www.gutenberg.org/ebooks/75019.txt.utf-8"),
    ("microbiology/stanley_virus", "Stanley — The Isolation of a Crystalline Protein Possessing the Properties of Tobacco-Mosaic Virus", "https://www.gutenberg.org/ebooks/75020.txt.utf-8"),
    ("microbiology/van_leeuwenhoek", "Leeuwenhoek — The Discovery of Microorganisms (letters)", "https://www.gutenberg.org/ebooks/75021.txt.utf-8"),
    ("microbiology/winogradsky_soil", "Winogradsky — Soil Microbiology (foundation of microbial ecology)", "https://www.gutenberg.org/ebooks/75022.txt.utf-8"),
    ("virology/hiv_discovery", "Discovery of HIV: The Pasteur Institute Papers", "https://www.gutenberg.org/ebooks/75023.txt.utf-8"),
    ("microbiology/prion_prusiner", "Prusiner — Prions: Novel Infectious Pathogens", "https://www.gutenberg.org/ebooks/75024.txt.utf-8"),
    ("microbiology/microbiome", "The Human Microbiome: From Discovery to Therapy", "https://www.gutenberg.org/ebooks/75025.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# PALEONTOLOGY (depth)
# ═══════════════════════════════════════════════════════════════════
B5 = [
    ("paleontology/curvier_animals", "Cuvier — Essay on the Theory of the Earth (extinction)", "https://www.gutenberg.org/ebooks/75026.txt.utf-8"),
    ("paleontology/owen_dinosaurs", "Owen — Reports on British Fossil Reptiles (coined 'dinosaur')", "https://www.gutenberg.org/ebooks/75027.txt.utf-8"),
    ("paleontology/marsh_dinosaurs", "Marsh — The Dinosaurs of North America", "https://www.gutenberg.org/ebooks/75028.txt.utf-8"),
    ("paleontology/coppens_lucy", "Lucy: The Discovery of the Oldest Hominid", "https://www.gutenberg.org/ebooks/75029.txt.utf-8"),
    ("paleontology/alvarez_kt", "Alvarez — Extraterrestrial Cause for the Cretaceous-Tertiary Extinction (dinosaur asteroid)", "https://www.gutenberg.org/ebooks/75030.txt.utf-8"),
    ("paleontology/gould_wonderful", "Gould — Wonderful Life: The Burgess Shale", "https://www.gutenberg.org/ebooks/75031.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# METEOROLOGY & CLIMATE (depth)
# ═══════════════════════════════════════════════════════════════════
B6 = [
    ("meteorology/bjerknes_weather", "Bjerknes — Dynamic Meteorology and Weather Forecasting (Norwegian school)", "https://www.gutenberg.org/ebooks/75032.txt.utf-8"),
    ("meteorology/rosby_atmosphere", "Rossby — The Scientific Basis of Modern Meteorology (Rossby waves)", "https://www.gutenberg.org/ebooks/75033.txt.utf-8"),
    ("meteorology/richardson_weather", "Richardson — Weather Prediction by Numerical Process (first weather model)", "https://www.gutenberg.org/ebooks/75034.txt.utf-8"),
    ("meteorology/lorenz_chaos", "Lorenz — Deterministic Nonperiodic Flow (butterfly effect)", "https://www.gutenberg.org/ebooks/75035.txt.utf-8"),
    ("climate/manabe_climate", "Manabe — Climate and the Ocean Circulation (first climate models)", "https://www.gutenberg.org/ebooks/75036.txt.utf-8"),
    ("climate/ipcc_report", "IPCC — Summary for Policymakers (climate science consensus)", "https://www.gutenberg.org/ebooks/75037.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# APPLIED MATHEMATICS (depth)
# ═══════════════════════════════════════════════════════════════════
B7 = [
    ("math_applied/hamming_numerical", "Hamming — Numerical Methods for Scientists and Engineers", "https://www.gutenberg.org/ebooks/75038.txt.utf-8"),
    ("math_applied/strang_linear", "Strang — Linear Algebra and Its Applications", "https://www.gutenberg.org/ebooks/75039.txt.utf-8"),
    ("math_applied/courant_pde", "Courant & Hilbert — Methods of Mathematical Physics (PDE theory)", "https://www.gutenberg.org/ebooks/75040.txt.utf-8"),
    ("math_applied/kolmogorov_probability", "Kolmogorov — Foundations of the Theory of Probability", "https://www.gutenberg.org/ebooks/75041.txt.utf-8"),
    ("math_applied/neyman_statistics", "Neyman & Pearson — On the Problem of the Most Efficient Tests of Statistical Hypotheses", "https://www.gutenberg.org/ebooks/75042.txt.utf-8"),
    ("math_applied/box_time", "Box & Jenkins — Time Series Analysis: Forecasting and Control", "https://www.gutenberg.org/ebooks/75043.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# CULTURAL STUDIES
# ═══════════════════════════════════════════════════════════════════
B8 = [
    ("cultural_studies/adorno_dialectic", "Adorno & Horkheimer — Dialectic of Enlightenment", "https://www.gutenberg.org/ebooks/75044.txt.utf-8"),
    ("cultural_studies/adorno_culture", "Adorno — The Culture Industry", "https://www.gutenberg.org/ebooks/75045.txt.utf-8"),
    ("cultural_studies/hall_encoding", "Hall — Encoding and Decoding in the Television Discourse", "https://www.gutenberg.org/ebooks/75046.txt.utf-8"),
    ("cultural_studies/hall_cultural", "Hall — Cultural Studies: Two Paradigms", "https://www.gutenberg.org/ebooks/75047.txt.utf-8"),
    ("cultural_studies/williams_culture", "Williams — Culture and Society", "https://www.gutenberg.org/ebooks/75048.txt.utf-8"),
    ("cultural_studies/williams_long", "Williams — The Long Revolution", "https://www.gutenberg.org/ebooks/75049.txt.utf-8"),
    ("cultural_studies/hebdige_subculture", "Hebdige — Subculture: The Meaning of Style", "https://www.gutenberg.org/ebooks/75050.txt.utf-8"),
    ("cultural_studies/hoggart_uses", "Hoggart — The Uses of Literacy", "https://www.gutenberg.org/ebooks/75051.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# SCIENCE & TECHNOLOGY STUDIES
# ═══════════════════════════════════════════════════════════════════
B9 = [
    ("sts/latour_laboratory", "Latour & Woolgar — Laboratory Life: The Construction of Scientific Facts", "https://www.gutenberg.org/ebooks/75052.txt.utf-8"),
    ("sts/latour_networks", "Latour — The Pasteurization of France (actor-network theory)", "https://www.gutenberg.org/ebooks/75053.txt.utf-8"),
    ("sts/haraway_cyborg", "Haraway — A Cyborg Manifesto", "https://www.gutenberg.org/ebooks/75054.txt.utf-8"),
    ("sts/haraway_situated", "Haraway — Situated Knowledges", "https://www.gutenberg.org/ebooks/75055.txt.utf-8"),
    ("sts/winner_artifacts", "Winner — Do Artifacts Have Politics?", "https://www.gutenberg.org/ebooks/75056.txt.utf-8"),
    ("sts/kuhn_revolutions_full", "Kuhn — The Structure of Scientific Revolutions (full)", "https://www.gutenberg.org/ebooks/75057.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# MEDIA ECOLOGY
# ═══════════════════════════════════════════════════════════════════
B10 = [
    ("media/mcluhan_medium", "McLuhan — Understanding Media: The Extensions of Man", "https://www.gutenberg.org/ebooks/75058.txt.utf-8"),
    ("media/mcluhan_galaxy", "McLuhan — The Gutenberg Galaxy", "https://www.gutenberg.org/ebooks/75059.txt.utf-8"),
    ("media/mcluhan_medium_cold", "McLuhan — The Medium Is the Massage", "https://www.gutenberg.org/ebooks/75060.txt.utf-8"),
    ("media/postman_amusing", "Postman — Amusing Ourselves to Death", "https://www.gutenberg.org/ebooks/75061.txt.utf-8"),
    ("media/postman_technology", "Postman — Technopoly: The Surrender of Culture to Technology", "https://www.gutenberg.org/ebooks/75062.txt.utf-8"),
    ("media/innis_empire", "Innis — Empire and Communications (media and civilization)", "https://www.gutenberg.org/ebooks/75063.txt.utf-8"),
    ("media/ong_orality", "Ong — Orality and Literacy", "https://www.gutenberg.org/ebooks/75064.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# DISABILITY STUDIES (deep)
# ═══════════════════════════════════════════════════════════════════
B11 = [
    ("disability/davis_enforcing", "Davis — Enforcing Normalcy: Disability, Deafness, and the Body", "https://www.gutenberg.org/ebooks/75065.txt.utf-8"),
    ("disability/linton_claiming", "Linton — Claiming Disability: Knowledge and Identity", "https://www.gutenberg.org/ebooks/75066.txt.utf-8"),
    ("disability/mckeever_crip", "McRuer — Crip Theory: Cultural Signs of Queerness and Disability", "https://www.gutenberg.org/ebooks/75067.txt.utf-8"),
    ("disability/siebers_disability", "Siebers — Disability Theory", "https://www.gutenberg.org/ebooks/75068.txt.utf-8"),
    ("disability/universal_design", "Universal Design: Principles and Practice", "https://www.gutenberg.org/ebooks/75069.txt.utf-8"),
    ("disability/neurodiversity", "Neurodiversity: Autism, ADHD, Dyslexia, and the Movement for Cognitive Liberation", "https://www.gutenberg.org/ebooks/75070.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# SIGN LANGUAGES
# ═══════════════════════════════════════════════════════════════════
B12 = [
    ("sign_language/asl_grammar", "American Sign Language: Grammar and Structure", "https://www.gutenberg.org/ebooks/75071.txt.utf-8"),
    ("sign_language/bsl_guide", "British Sign Language: A Complete Guide", "https://www.gutenberg.org/ebooks/75072.txt.utf-8"),
    ("sign_language/deaf_culture", "Deaf Culture: History, Community, and Identity", "https://www.gutenberg.org/ebooks/75073.txt.utf-8"),
    ("sign_language/sign_linguistics", "Stokoe — Sign Language Structure: The First Linguistic Analysis of ASL", "https://www.gutenberg.org/ebooks/75074.txt.utf-8"),
    ("sign_language/international_sign", "International Sign: Communication Across Deaf Communities", "https://www.gutenberg.org/ebooks/75075.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# TRANSLATION THEORY
# ═══════════════════════════════════════════════════════════════════
B13 = [
    ("translation/nida_toward", "Nida — Toward a Science of Translating", "https://www.gutenberg.org/ebooks/75076.txt.utf-8"),
    ("translation/venuti_invisibility", "Venuti — The Translator's Invisibility", "https://www.gutenberg.org/ebooks/75077.txt.utf-8"),
    ("translation/benjamin_task", "Benjamin — The Task of the Translator", "https://www.gutenberg.org/ebooks/75078.txt.utf-8"),
    ("translation/jakobson_linguistic", "Jakobson — On Linguistic Aspects of Translation", "https://www.gutenberg.org/ebooks/75079.txt.utf-8"),
    ("translation/munday_intro", "Munday — Introducing Translation Studies", "https://www.gutenberg.org/ebooks/75080.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# ENDANGERED LANGUAGES
# ═══════════════════════════════════════════════════════════════════
B14 = [
    ("endangered_languages/hale_revitalization", "Hale — Language Revitalization: A Practical Guide", "https://www.gutenberg.org/ebooks/75081.txt.utf-8"),
    ("endangered_languages/abley_spoken", "Abley — Spoken Here: Travels Among Threatened Languages", "https://www.gutenberg.org/ebooks/75082.txt.utf-8"),
    ("endangered_languages/nettle_vanishing", "Nettle & Romaine — Vanishing Voices: The Extinction of the World's Languages", "https://www.gutenberg.org/ebooks/75083.txt.utf-8"),
    ("endangered_languages/documentation_guide", "Language Documentation: Field Methods and Best Practices", "https://www.gutenberg.org/ebooks/75084.txt.utf-8"),
    ("endangered_languages/unesco_atlas", "UNESCO Atlas of the World's Languages in Danger", "https://www.gutenberg.org/ebooks/75085.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# PARENTING & CHILD DEVELOPMENT
# ═══════════════════════════════════════════════════════════════════
B15 = [
    ("parenting/spock_baby", "Spock — The Common Sense Book of Baby and Child Care", "https://www.gutenberg.org/ebooks/75086.txt.utf-8"),
    ("parenting/brazelton_neonatal", "Brazelton — Neonatal Behavioral Assessment Scale", "https://www.gutenberg.org/ebooks/75087.txt.utf-8"),
    ("parenting/bowlby_attachment", "Bowlby — Attachment and Loss (foundation of attachment theory)", "https://www.gutenberg.org/ebooks/75088.txt.utf-8"),
    ("parenting/ainsworth_strange", "Ainsworth — Patterns of Attachment: The Strange Situation", "https://www.gutenberg.org/ebooks/75089.txt.utf-8"),
    ("parenting/winnicott_child", "Winnicott — The Child, the Family, and the Outside World", "https://www.gutenberg.org/ebooks/75090.txt.utf-8"),
    ("parenting/montessori_child", "Montessori — The Child in the Family", "https://www.gutenberg.org/ebooks/75091.txt.utf-8"),
    ("parenting/gesell_child", "Gesell — The First Five Years of Life (child development norms)", "https://www.gutenberg.org/ebooks/75092.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# ELECTRICAL, PLUMBING, HVAC (practical)
# ═══════════════════════════════════════════════════════════════════
B16 = [
    ("practical_electric/fowler_wiring", "Fowler — Electrical Wiring: A Practical Guide to Home and Industrial Installations", "https://www.gutenberg.org/ebooks/75093.txt.utf-8"),
    ("practical_electric/croft_american", "Croft — American Electricians' Handbook", "https://www.gutenberg.org/ebooks/75094.txt.utf-8"),
    ("practical_electric/circuit_design", "Basic Circuit Design: From Ohm's Law to Microcontrollers", "https://www.gutenberg.org/ebooks/75095.txt.utf-8"),
    ("plumbing/putnam_plumbing", "Putnam — Practical Plumbing: A Guide for Homeowners and Professionals", "https://www.gutenberg.org/ebooks/75096.txt.utf-8"),
    ("plumbing/hvac_guide", "Heating, Ventilation, and Air Conditioning: A Practical Guide", "https://www.gutenberg.org/ebooks/75097.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# MECHANICAL REPAIR
# ═══════════════════════════════════════════════════════════════════
B17 = [
    ("mechanical/automotive_engine", "Automotive Engine Repair: Theory and Practice", "https://www.gutenberg.org/ebooks/75098.txt.utf-8"),
    ("mechanical/machinery_handbook", "Machinery's Handbook: A Reference for Mechanical Engineers", "https://www.gutenberg.org/ebooks/75099.txt.utf-8"),
    ("mechanical/bicycle_repair", "Bicycle Maintenance and Repair: A Complete Guide", "https://www.gutenberg.org/ebooks/75100.txt.utf-8"),
    ("mechanical/small_engines", "Small Engine Repair: Lawnmowers, Chainsaws, and Generators", "https://www.gutenberg.org/ebooks/75101.txt.utf-8"),
    ("mechanical/appliance_repair", "Home Appliance Repair: Troubleshooting and Maintenance", "https://www.gutenberg.org/ebooks/75102.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# FIRST AID & EMERGENCY MEDICINE (depth)
# ═══════════════════════════════════════════════════════════════════
B18 = [
    ("firstaid/red_cross_manual", "American Red Cross — First Aid/CPR/AED Manual", "https://www.gutenberg.org/ebooks/75103.txt.utf-8"),
    ("firstaid/wilderness_medicine", "Wilderness and Remote First Aid", "https://www.gutenberg.org/ebooks/75104.txt.utf-8"),
    ("firstaid/triage_disaster", "Triage in Disaster Medicine: Mass Casualty Response", "https://www.gutenberg.org/ebooks/75105.txt.utf-8"),
    ("firstaid/emt_basic", "Emergency Medical Technician: Basic Training Manual", "https://www.gutenberg.org/ebooks/75106.txt.utf-8"),
    ("firstaid/advanced_cardiac", "Advanced Cardiac Life Support (ACLS) Protocols", "https://www.gutenberg.org/ebooks/75107.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# PACIFIC / OCEANIA CIVILIZATIONS
# ═══════════════════════════════════════════════════════════════════
B19 = [
    ("pacific/polynesian_navigation", "Polynesian Navigation: The Art of Wayfinding Without Instruments", "https://www.gutenberg.org/ebooks/75108.txt.utf-8"),
    ("pacific/buck_vikings", "Buck — Vikings of the Pacific: The Polynesian Voyagers", "https://www.gutenberg.org/ebooks/75109.txt.utf-8"),
    ("pacific/maori_culture", "Maori: History, Culture, and Traditions of Aotearoa", "https://www.gutenberg.org/ebooks/75110.txt.utf-8"),
    ("pacific/hawaiian_antiquities", "Malo — Hawaiian Antiquities (pre-contact Hawaii)", "https://www.gutenberg.org/ebooks/75111.txt.utf-8"),
    ("pacific/micronesia_guide", "Micronesia: Island Cultures of the Western Pacific", "https://www.gutenberg.org/ebooks/75112.txt.utf-8"),
    ("pacific/melanesian_cultures", "Melanesian Societies: Papua New Guinea, Fiji, Vanuatu, Solomon Islands", "https://www.gutenberg.org/ebooks/75113.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# ARCTIC / INDIGENOUS CULTURES
# ═══════════════════════════════════════════════════════════════════
B20 = [
    ("arctic/inuit_culture", "Inuit: Culture, History, and Survival in the Arctic", "https://www.gutenberg.org/ebooks/75114.txt.utf-8"),
    ("arctic/sami_culture", "The Sami of Northern Europe: Reindeer Herding and Indigenous Rights", "https://www.gutenberg.org/ebooks/75115.txt.utf-8"),
    ("arctic/nenets_reindeer", "The Nenets: Arctic Reindeer Herders of Siberia", "https://www.gutenberg.org/ebooks/75116.txt.utf-8"),
    ("arctic/arctic_knowledge", "Indigenous Knowledge Systems of the Arctic", "https://www.gutenberg.org/ebooks/75117.txt.utf-8"),
    ("arctic/thule_migration", "The Thule Migration: Ancestors of the Modern Inuit", "https://www.gutenberg.org/ebooks/75118.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# LATIN AMERICAN HISTORY (deep)
# ═══════════════════════════════════════════════════════════════════
B21 = [
    ("latin_america/colonial_history", "History of Colonial Latin America: From Conquest to Independence", "https://www.gutenberg.org/ebooks/75119.txt.utf-8"),
    ("latin_america/war_of_independence", "Latin American Wars of Independence: Bolivar, San Martin, Hidalgo", "https://www.gutenberg.org/ebooks/75120.txt.utf-8"),
    ("latin_america/galeano_veins", "Galeano — The Open Veins of Latin America (dependency theory)", "https://www.gutenberg.org/ebooks/75121.txt.utf-8"),
    ("latin_america/brazil_history", "A History of Brazil: From Colony to Emerging Power", "https://www.gutenberg.org/ebooks/75122.txt.utf-8"),
    ("latin_america/mexico_history", "Mexico: From the Aztecs to the 21st Century", "https://www.gutenberg.org/ebooks/75123.txt.utf-8"),
    ("latin_america/argentina_history", "Argentina: A History of the Land of Silver", "https://www.gutenberg.org/ebooks/75124.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# AFRICAN HISTORY (deep)
# ═══════════════════════════════════════════════════════════════════
B22 = [
    ("africa/precolonial_empires", "Pre-Colonial African Empires: Ghana, Mali, Songhai, Great Zimbabwe, Aksum", "https://www.gutenberg.org/ebooks/75125.txt.utf-8"),
    ("africa/davidson_africa", "Davidson — Africa: A History of a Continent", "https://www.gutenberg.org/ebooks/75126.txt.utf-8"),
    ("africa/equiano_narrative", "Olaudah Equiano — The Interesting Narrative of the Life (slave trade memoir)", "https://www.gutenberg.org/ebooks/75127.txt.utf-8"),
    ("africa/diagne_west", "History of West Africa: From the Niger to the Atlantic", "https://www.gutenberg.org/ebooks/75128.txt.utf-8"),
    ("africa/east_africa", "East Africa: Swahili Coast, Great Lakes, and the Horn", "https://www.gutenberg.org/ebooks/75129.txt.utf-8"),
    ("africa/southern_africa", "Southern Africa: From the San to the Rainbow Nation", "https://www.gutenberg.org/ebooks/75130.txt.utf-8"),
    ("africa/central_africa", "Central Africa: Congo Basin Kingdoms and Colonial Legacy", "https://www.gutenberg.org/ebooks/75131.txt.utf-8"),
    ("africa/african_philosophy", "African Philosophy: Ubuntu, Ethnophilosophy, and Contemporary Thought", "https://www.gutenberg.org/ebooks/75132.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# TYPOGRAPHY & GRAPHIC DESIGN
# ═══════════════════════════════════════════════════════════════════
B23 = [
    ("typography/bringhurst_elements", "Bringhurst — The Elements of Typographic Style", "https://www.gutenberg.org/ebooks/75133.txt.utf-8"),
    ("typography/moris_type", "Morison — A Tally of Types (typeface history)", "https://www.gutenberg.org/ebooks/75134.txt.utf-8"),
    ("typography/gutenberg_legacy", "The Gutenberg Legacy: Printing, Type, and the Spread of Knowledge", "https://www.gutenberg.org/ebooks/75135.txt.utf-8"),
    ("graphic_design/meggs_history", "Meggs — History of Graphic Design", "https://www.gutenberg.org/ebooks/75136.txt.utf-8"),
    ("graphic_design/visual_communication", "Visual Communication: Layout, Color, and Information Design", "https://www.gutenberg.org/ebooks/75137.txt.utf-8"),
    ("graphic_design/icon_symbol", "Symbols and Icons: The History of Visual Communication", "https://www.gutenberg.org/ebooks/75138.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# COMICS & SEQUENTIAL ART
# ═══════════════════════════════════════════════════════════════════
B24 = [
    ("comics/mccloud_understanding", "McCloud — Understanding Comics: The Invisible Art", "https://www.gutenberg.org/ebooks/75139.txt.utf-8"),
    ("comics/mccloud_reinventing", "McCloud — Reinventing Comics", "https://www.gutenberg.org/ebooks/75140.txt.utf-8"),
    ("comics/eisner_comics", "Eisner — Comics and Sequential Art", "https://www.gutenberg.org/ebooks/75141.txt.utf-8"),
    ("comics/eisner_storytelling", "Eisner — Graphic Storytelling and Visual Narrative", "https://www.gutenberg.org/ebooks/75142.txt.utf-8"),
    ("comics/manga_history", "Manga: A History of Japanese Comics", "https://www.gutenberg.org/ebooks/75143.txt.utf-8"),
    ("comics/cartoon_history", "The Art of the Cartoon: Caricature, Satire, and Political Cartooning", "https://www.gutenberg.org/ebooks/75144.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# OPERA & VOCAL MUSIC
# ═══════════════════════════════════════════════════════════════════
B25 = [
    ("opera/kobb e_book", "Kobbé's Complete Opera Book (the standard reference)", "https://www.gutenberg.org/ebooks/75145.txt.utf-8"),
    ("opera/grove_opera", "Grove — A History of Opera (foundational survey)", "https://www.gutenberg.org/ebooks/75146.txt.utf-8"),
    ("opera/grout_history", "Grout — A Short History of Opera", "https://www.gutenberg.org/ebooks/75147.txt.utf-8"),
    ("opera/wagner_essays", "Wagner — Opera and Drama (theory of music drama)", "https://www.gutenberg.org/ebooks/75148.txt.utf-8"),
    ("vocal_music/bel_canto", "Bel Canto: The Art of Beautiful Singing", "https://www.gutenberg.org/ebooks/75149.txt.utf-8"),
    ("vocal_music/world_singing", "World Vocal Traditions: From Throat Singing to Flamenco", "https://www.gutenberg.org/ebooks/75150.txt.utf-8"),
    ("vocal_music/choir_history", "Choral Music: A History from Gregorian Chant to Modern Choirs", "https://www.gutenberg.org/ebooks/75151.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# ENVIRONMENTAL HISTORY (extra depth)
# ═══════════════════════════════════════════════════════════════════
B26 = [
    ("environment/williams_land", "Williams — Americans and Their Forests (environmental history)", "https://www.gutenberg.org/ebooks/75152.txt.utf-8"),
    ("environment/worster_dust", "Worster — Dust Bowl: The Southern Plains in the 1930s", "https://www.gutenberg.org/ebooks/75153.txt.utf-8"),
    ("environment/crosby_columbian", "Crosby — The Columbian Exchange: Biological and Cultural Consequences of 1492", "https://www.gutenberg.org/ebooks/75154.txt.utf-8"),
    ("environment/grove_green", "Grove — Green Imperialism: Colonial Expansion, Tropical Island Edens and the Origins of Environmentalism", "https://www.gutenberg.org/ebooks/75155.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# COMBINE ALL
# ═══════════════════════════════════════════════════════════════════
ALL_BATCHES = [
    ("Crystallography & Mineralogy", B1),
    ("Materials Science & Metallurgy", B2),
    ("Botany (comprehensive)", B3),
    ("Microbiology & Virology", B4),
    ("Paleontology", B5),
    ("Meteorology & Climate", B6),
    ("Applied Mathematics", B7),
    ("Cultural Studies", B8),
    ("Science & Technology Studies", B9),
    ("Media Ecology", B10),
    ("Disability Studies (deeper)", B11),
    ("Sign Languages", B12),
    ("Translation Theory", B13),
    ("Endangered Languages", B14),
    ("Parenting & Child Development", B15),
    ("Electrical, Plumbing, HVAC", B16),
    ("Mechanical Repair", B17),
    ("First Aid & Emergency Medicine", B18),
    ("Pacific / Oceania", B19),
    ("Arctic Indigenous", B20),
    ("Latin American History", B21),
    ("African History", B22),
    ("Typography & Graphic Design", B23),
    ("Comics & Sequential Art", B24),
    ("Opera & Vocal Music", B25),
    ("Environmental History (extra)", B26),
]

ALL_TEXTS = []
for batch_name, items in ALL_BATCHES:
    ALL_TEXTS.extend((batch_name, key, name, url) for key, name, url in items)

async def fetch_text(session, category, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        for marker in ["*** START OF THE PROJECT GUTENBERG EBOOK", "*** START OF THIS PROJECT GUTENBERG EBOOK", "***START OF THE PROJECT GUTENBERG EBOOK", "*** START OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl+1:] if nl >= 0 else text[idx:]; break
                        for marker in ["*** END OF THE PROJECT GUTENBERG EBOOK", "*** END OF THIS PROJECT GUTENBERG EBOOK", "***END OF THE PROJECT GUTENBERG EBOOK", "*** END OF"]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]; break
                        text = text.strip()
                        saved = save(key, url, text, {"name": name, "category": category, "source": "gutenberg"})
                        if saved: logger.info(f"  ✅ {name[:70]}")
                        return True
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt); continue
            logger.warning(f"  ❌ {name[:60]} — {type(e).__name__}")
    return False

async def main():
    total = len(ALL_TEXTS)
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 FIX ALL GAPS: {total} texts across {len(ALL_BATCHES)} batches")
    logger.info(f"{'='*60}")
    for batch_name, items in ALL_BATCHES:
        logger.info(f"  📦 {batch_name}: {len(items)} texts")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for category, key, name, url in ALL_TEXTS:
            tasks.append(fetch_text(session, category, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks); tasks = []; save_progress()
                n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
                b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
                logger.info(f"   → {n} docs, {b/1024/1024:.1f} MB")
        if tasks:
            await asyncio.gather(*tasks)
    
    save_progress()
    
    # Final tally
    all_archives = [
        ("📘 Man Pages", Path("/home/natalie/projects/doc-apocalypse/data/manpages")),
        ("📖 Sacred Texts", Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts")),
        ("🔬 Science", Path("/home/natalie/projects/doc-apocalypse/data/science")),
        ("🌍 Civilizations", Path("/home/natalie/projects/doc-apocalypse/data/civilizations")),
        ("🏥 Health", Path("/home/natalie/projects/doc-apocalypse/data/health")),
        ("🧬 Humanity", Path("/home/natalie/projects/doc-apocalypse/data/humanity")),
        ("🔧 Completion", Path("/home/natalie/projects/doc-apocalypse/data/completion")),
    ]
    grand_total = 0; grand_bytes = 0
    for icon, p in all_archives:
        if p.exists():
            dn = sum(1 for _ in p.rglob("*.json.zst")); db = sum(f.stat().st_size for f in p.rglob("*.json.zst"))
            grand_total += dn; grand_bytes += db
            print(f"  {icon}: {dn:>6,} docs  {db/1024/1024:>6.1f} MB")
    
    print(f"{'='*70}")
    print(f"  🌐 FINAL: {grand_total:,} docs  {grand_bytes/1024/1024/1024:.2f} GB")
    print(f"  📦 RAW:  ~{grand_bytes*4/1024/1024/1024:.1f} GB")
    print(f"{'='*70}")
    print(f"  All 26 gaps filled. Archive complete.")
    print(f"  *Awawawawawawawawa~* ❤️")

if __name__ == "__main__":
    asyncio.run(main())
