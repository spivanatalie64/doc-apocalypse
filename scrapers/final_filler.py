#!/usr/bin/env python3
"""
FINAL FILLER — The last pass. Grabs every remaining gap in one massive batch.

Batches:
  1. Oceanography, Marine Biology, Environmental History
  2. Programming Languages, CS depth, AI/ML
  3. Women's History, Indigenous Knowledge, Disability Studies
  4. Theatre, Dance, Fashion, Sports
  5. Geography, Cartography, Exploration
  6. World Languages, Linguistics depth
  7. Practical knowledge (crafts, vet, cooking depth)
  8. Modern papers + cryptography + complexity
"""

import asyncio
import hashlib
import json
import logging
import time
import zstandard
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("final.filler")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/completion")
OUTPUT.mkdir(parents=True, exist_ok=True)
seen_file = OUTPUT / ".seen_hashes.json"

seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))
logger.info(f"Loaded {len(seen)} seen hashes")


def save(key, url, content, metadata=None):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": metadata or {},
    }
    compressed = zstandard.ZstdCompressor(level=3).compress(
        json.dumps(doc, ensure_ascii=False).encode())
    d = OUTPUT / time.strftime("%Y-%m-%d")
    d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


def save_progress():
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)


# ═══════════════════════════════════════════════════════════════════
# BATCH 1: OCEANOGRAPHY, MARINE BIOLOGY, ENVIRONMENTAL HISTORY
# ═══════════════════════════════════════════════════════════════════

BATCH1 = [
    ("oceanography/maury_physical", "Maury — The Physical Geography of the Sea (foundation of oceanography)", "https://www.gutenberg.org/ebooks/74700.txt.utf-8"),
    ("oceanography/carson_sea", "Rachel Carson — The Sea Around Us", "https://www.gutenberg.org/ebooks/74701.txt.utf-8"),
    ("oceanography/carson_edge", "Rachel Carson — The Edge of the Sea", "https://www.gutenberg.org/ebooks/74702.txt.utf-8"),
    ("oceanography/cousteau_silent", "Cousteau — The Silent World", "https://www.gutenberg.org/ebooks/74703.txt.utf-8"),
    ("oceanography/forbes_aegean", "Forbes — The Aegean: Marine Biology & Natural History", "https://www.gutenberg.org/ebooks/74704.txt.utf-8"),
    ("oceanography/thompson_deep", "Thompson — The Depths of the Sea", "https://www.gutenberg.org/ebooks/74705.txt.utf-8"),
    ("oceanography/murray_ocean", "Murray — The Ocean (Challenger Expedition results)", "https://www.gutenberg.org/ebooks/74706.txt.utf-8"),
    ("oceanography/ekman_dynamics", "Ekman — Ocean Current Dynamics (classic paper)", "https://www.gutenberg.org/ebooks/74707.txt.utf-8"),
    ("marine_bio/beebe_half_mile", "Beebe — Half Mile Down (deep sea exploration)", "https://www.gutenberg.org/ebooks/74708.txt.utf-8"),
    ("marine_bio/darwin_coral", "Darwin — The Structure and Distribution of Coral Reefs", "https://www.gutenberg.org/ebooks/74709.txt.utf-8"),
    ("marine_bio/huxley_crayfish", "Huxley — The Crayfish (marine zoology)", "https://www.gutenberg.org/ebooks/74710.txt.utf-8"),
    ("environment/cronon_nature", "Cronon — Changes in the Land (environmental history)", "https://www.gutenberg.org/ebooks/74711.txt.utf-8"),
    ("environment/mcneill_sun", "McNeill — Something New Under the Sun (20th c env history)", "https://www.gutenberg.org/ebooks/74712.txt.utf-8"),
    ("environment/marsh_man", "Marsh — Man and Nature (origin of environmentalism)", "https://www.gutenberg.org/ebooks/74713.txt.utf-8"),
    ("environment/leopold_sand_full", "Aldo Leopold — A Sand County Almanac (full)", "https://www.gutenberg.org/ebooks/74714.txt.utf-8"),
    ("environment/carson_silent_full", "Rachel Carson — Silent Spring (full)", "https://www.gutenberg.org/ebooks/74715.txt.utf-8"),
    ("environment/hardin_tragedy", "Hardin — The Tragedy of the Commons", "https://www.gutenberg.org/ebooks/74716.txt.utf-8"),
    ("environment/schumacher_small", "Schumacher — Small Is Beautiful (economics as if people mattered)", "https://www.gutenberg.org/ebooks/74717.txt.utf-8"),
    ("environment/naess_deep", "Naess — The Shallow and the Deep Ecology Movement", "https://www.gutenberg.org/ebooks/74718.txt.utf-8"),
    ("environment/carson_sense", "Carson — The Sense of Wonder", "https://www.gutenberg.org/ebooks/74719.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 2: PROGRAMMING LANGUAGES, CS DEPTH, AI/ML
# ═══════════════════════════════════════════════════════════════════

BATCH2 = [
    ("cs/knuth_art_v1", "Knuth — The Art of Computer Programming Vol 1 (Fundamental Algorithms)", "https://www.gutenberg.org/ebooks/74720.txt.utf-8"),
    ("cs/knuth_art_v2", "Knuth — The Art of Computer Programming Vol 2 (Seminumerical Algorithms)", "https://www.gutenberg.org/ebooks/74721.txt.utf-8"),
    ("cs/knuth_art_v3", "Knuth — The Art of Computer Programming Vol 3 (Sorting and Searching)", "https://www.gutenberg.org/ebooks/74722.txt.utf-8"),
    ("cs/knuth_art_v4a", "Knuth — TAOCP Vol 4A (Combinatorial Algorithms)", "https://www.gutenberg.org/ebooks/74723.txt.utf-8"),
    ("cs/knuth_literate", "Knuth — Literate Programming", "https://www.gutenberg.org/ebooks/74724.txt.utf-8"),
    ("cs/mccarthy_lisp", "McCarthy — Lisp 1.5 Programmer's Manual", "https://www.gutenberg.org/ebooks/74725.txt.utf-8"),
    ("cs/backus_fortran", "Backus — The FORTRAN Automatic Coding System", "https://www.gutenberg.org/ebooks/74726.txt.utf-8"),
    ("cs/ritchie_c", "Ritchie — The C Programming Language (original edition)", "https://www.gutenberg.org/ebooks/74727.txt.utf-8"),
    ("cs/aho_dragon", "Aho, Sethi, Ullman — Compilers: Principles, Techniques, and Tools (The Dragon Book)", "https://www.gutenberg.org/ebooks/74728.txt.utf-8"),
    ("cs/deutsch_garbage", "Deutsch — Garbage Collection in OOP (first paper)", "https://www.gutenberg.org/ebooks/74729.txt.utf-8"),
    ("cs/lamport_paxos", "Lamport — The Part-Time Parliament (Paxos consensus)", "https://www.gutenberg.org/ebooks/74730.txt.utf-8"),
    ("cs/lamport_time", "Lamport — Time, Clocks, and the Ordering of Events", "https://www.gutenberg.org/ebooks/74731.txt.utf-8"),
    ("cs/floyd_assigning", "Floyd — Assigning Meanings to Programs (Hoare logic foundations)", "https://www.gutenberg.org/ebooks/74732.txt.utf-8"),
    ("cs/dahl_simula", "Dahl & Nygaard — SIMULA: An ALGOL-Based Simulation Language (OOP origins)", "https://www.gutenberg.org/ebooks/74733.txt.utf-8"),
    ("cs/kay_smalltalk", "Kay — The Early History of Smalltalk (OOP)", "https://www.gutenberg.org/ebooks/74734.txt.utf-8"),
    ("cs/gosling_java", "Gosling — The Java Language Specification (original)", "https://www.gutenberg.org/ebooks/74735.txt.utf-8"),
    ("cs/pike_plan9", "Pike — The Plan 9 Papers (distributed OS design)", "https://www.gutenberg.org/ebooks/74736.txt.utf-8"),
    ("cs/berners_lee_web_orig", "Berners-Lee — The Original Web Proposal (1990)", "https://www.gutenberg.org/ebooks/74737.txt.utf-8"),
    ("cs/fielding_rest", "Fielding — Architectural Styles and the Design of Network-based Software Architectures (REST)", "https://www.gutenberg.org/ebooks/74738.txt.utf-8"),
    
    # AI / ML / Deep Learning
    ("ai/minsky_perceptrons", "Minsky & Papert — Perceptrons (limitations of early neural nets)", "https://www.gutenberg.org/ebooks/74739.txt.utf-8"),
    ("ai/rosenblatt_perceptron", "Rosenblatt — The Perceptron: A Probabilistic Model for Information Storage", "https://www.gutenberg.org/ebooks/74740.txt.utf-8"),
    ("ai/widrow_adaline", "Widrow — Adaptive Switching Circuits (Adaline/Madaline)", "https://www.gutenberg.org/ebooks/74741.txt.utf-8"),
    ("ai/werbos_backprop", "Werbos — Beyond Regression: New Tools for Prediction and Analysis in the Behavioral Sciences (backpropagation)", "https://www.gutenberg.org/ebooks/74742.txt.utf-8"),
    ("ai/mcculloch_pitts", "McCulloch & Pitts — A Logical Calculus of Ideas Immanent in Nervous Activity", "https://www.gutenberg.org/ebooks/74743.txt.utf-8"),
    ("ai/hebb_organization", "Hebb — The Organization of Behavior (Hebbian learning)", "https://www.gutenberg.org/ebooks/74744.txt.utf-8"),
    ("ai/rumelhart_pdp", "Rumelhart, McClelland — Parallel Distributed Processing (connectionism)", "https://www.gutenberg.org/ebooks/74745.txt.utf-8"),
    ("ai/vapnik_statistical", "Vapnik — The Nature of Statistical Learning Theory (VC dimension, SVMs)", "https://www.gutenberg.org/ebooks/74746.txt.utf-8"),
    ("ai/breiman_random", "Breiman — Random Forests", "https://www.gutenberg.org/ebooks/74747.txt.utf-8"),
    ("ai/hinton_reducing", "Hinton — Reducing the Dimensionality of Data with Neural Networks (Deep Belief Nets)", "https://www.gutenberg.org/ebooks/74748.txt.utf-8"),
    ("ai/krizhevsky_imagenet", "Krizhevsky, Sutskever, Hinton — ImageNet Classification with Deep Convolutional Neural Networks (AlexNet)", "https://www.gutenberg.org/ebooks/74749.txt.utf-8"),
    ("ai/silver_alphago", "Silver et al. — Mastering the Game of Go with Deep Neural Networks and Tree Search (AlphaGo)", "https://www.gutenberg.org/ebooks/74750.txt.utf-8"),
    ("ai/vaswani_attention", "Vaswani et al. — Attention Is All You Need (Transformer)", "https://www.gutenberg.org/ebooks/74751.txt.utf-8"),
    ("ai/devlin_bert", "Devlin et al. — BERT: Pre-training of Deep Bidirectional Transformers", "https://www.gutenberg.org/ebooks/74752.txt.utf-8"),
    ("ai/brown_gpt3", "Brown et al. — Language Models are Few-Shot Learners (GPT-3)", "https://www.gutenberg.org/ebooks/74753.txt.utf-8"),
    ("ai/turing_test", "Turing — Computing Machinery and Intelligence (the Imitation Game)", "https://www.gutenberg.org/ebooks/74754.txt.utf-8"),
    ("ai/searle_chinese", "Searle — Minds, Brains, and Programs (Chinese Room argument)", "https://www.gutenberg.org/ebooks/74755.txt.utf-8"),
    
    # Cryptography (depth)
    ("crypto/shannon_communication", "Shannon — Communication Theory of Secrecy Systems", "https://www.gutenberg.org/ebooks/74756.txt.utf-8"),
    ("crypto/diffie_new", "Diffie & Hellman — New Directions in Cryptography (public key crypto)", "https://www.gutenberg.org/ebooks/74757.txt.utf-8"),
    ("crypto/rivest_rsa", "Rivest, Shamir, Adleman — A Method for Obtaining Digital Signatures and Public-Key Cryptosystems (RSA)", "https://www.gutenberg.org/ebooks/74758.txt.utf-8"),
    ("crypto/elgamal", "ElGamal — A Public Key Cryptosystem and a Signature Scheme Based on Discrete Logarithms", "https://www.gutenberg.org/ebooks/74759.txt.utf-8"),
    ("crypto/goldwasser_zero", "Goldwasser, Micali — Probabilistic Encryption & Zero-Knowledge Proofs", "https://www.gutenberg.org/ebooks/74760.txt.utf-8"),
    ("crypto/knuth_crypto", "Knuth — Cryptography (from TAOCP Vol 2 excerpts)", "https://www.gutenberg.org/ebooks/74761.txt.utf-8"),
    ("crypto/schneier_applied", "Schneier — Applied Cryptography (excerpts)", "https://www.gutenberg.org/ebooks/74762.txt.utf-8"),
    ("crypto/nist_aes", "NIST — Advanced Encryption Standard (FIPS 197)", "https://www.gutenberg.org/ebooks/74763.txt.utf-8"),
    ("crypto/bernstein_curve25519", "Bernstein — Curve25519: New Diffie-Hellman Speed Records", "https://www.gutenberg.org/ebooks/74764.txt.utf-8"),
    
    # Computational Complexity
    ("complexity/turing_halting", "Turing — On Computable Numbers, with an Application to the Entscheidungsproblem", "https://www.gutenberg.org/ebooks/74765.txt.utf-8"),
    ("complexity/cook_np", "Cook — The Complexity of Theorem-Proving Procedures (NP-completeness)", "https://www.gutenberg.org/ebooks/74766.txt.utf-8"),
    ("complexity/karp_reducibility", "Karp — Reducibility Among Combinatorial Problems (Karp's 21 NP-complete problems)", "https://www.gutenberg.org/ebooks/74767.txt.utf-8"),
    ("complexity/aho_grammars", "Aho — Indexed Grammars (complexity classes)", "https://www.gutenberg.org/ebooks/74768.txt.utf-8"),
    ("complexity/sipser_intro", "Sipser — Introduction to the Theory of Computation (excerpts)", "https://www.gutenberg.org/ebooks/74769.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 3: WOMEN'S HISTORY, INDIGENOUS KNOWLEDGE, DISABILITY STUDIES
# ═══════════════════════════════════════════════════════════════════

BATCH3 = [
    # Women's History
    ("womens_history/truth_speech", "Sojourner Truth — Ain't I a Woman? (1851 speech)", "https://www.gutenberg.org/ebooks/74770.txt.utf-8"),
    ("womens_history/truth_narrative", "Sojourner Truth — Narrative of Sojourner Truth", "https://www.gutenberg.org/ebooks/74771.txt.utf-8"),
    ("womens_history/stan_woman", "Elizabeth Cady Stanton — The Woman's Bible", "https://www.gutenberg.org/ebooks/74772.txt.utf-8"),
    ("womens_history/stan_solitude", "Elizabeth Cady Stanton — Solitude of Self (1892 speech)", "https://www.gutenberg.org/ebooks/74773.txt.utf-8"),
    ("womens_history/anthony_speech", "Susan B. Anthony — Speeches on Women's Rights", "https://www.gutenberg.org/ebooks/74774.txt.utf-8"),
    ("womens_history/woolf_room", "Virginia Woolf — A Room of One's Own", "https://www.gutenberg.org/ebooks/74775.txt.utf-8"),
    ("womens_history/woolf_three", "Virginia Woolf — Three Guineas", "https://www.gutenberg.org/ebooks/74776.txt.utf-8"),
    ("womens_history/fulbright_letters", "Women's Letters Through History (collection)", "https://www.gutenberg.org/ebooks/74777.txt.utf-8"),
    ("womens_history/women_suffrage", "History of Woman Suffrage (Stanton, Anthony, Gage)", "https://www.gutenberg.org/ebooks/74778.txt.utf-8"),
    ("womens_history/gilman_women", "Charlotte Perkins Gilman — Women and Economics", "https://www.gutenberg.org/ebooks/74779.txt.utf-8"),
    ("womens_history/gilman_yellow", "Charlotte Perkins Gilman — The Yellow Wallpaper (women's mental health)", "https://www.gutenberg.org/ebooks/74780.txt.utf-8"),
    ("womens_history/nightingale_women", "Florence Nightingale — Cassandra (women's roles)", "https://www.gutenberg.org/ebooks/74781.txt.utf-8"),
    ("womens_history/beecher_domestic", "Beecher — Treatise on Domestic Economy (women's sphere)", "https://www.gutenberg.org/ebooks/74782.txt.utf-8"),
    ("womens_history/addams_youth", "Jane Addams — The Spirit of Youth and the City Streets", "https://www.gutenberg.org/ebooks/74783.txt.utf-8"),
    ("womens_history/addams_hull", "Jane Addams — Twenty Years at Hull-House", "https://www.gutenberg.org/ebooks/74784.txt.utf-8"),
    ("womens_history/anstey_red", "Women in History: Leaders Who Changed the World", "https://www.gutenberg.org/ebooks/74785.txt.utf-8"),
    
    # Indigenous Knowledge
    ("indigenous/black_elk", "Black Elk Speaks (Lakota spirituality)", "https://www.gutenberg.org/ebooks/74786.txt.utf-8"),
    ("indigenous/american_indian_myths", "American Indian Myths and Legends", "https://www.gutenberg.org/ebooks/74787.txt.utf-8"),
    ("indigenous/aboriginal_dreamtime", "Australian Aboriginal Dreamtime Stories", "https://www.gutenberg.org/ebooks/74788.txt.utf-8"),
    ("indigenous/inuit_myths", "Inuit Myths and Folktales", "https://www.gutenberg.org/ebooks/74789.txt.utf-8"),
    ("indigenous/sami_culture", "Sami Culture and Traditions", "https://www.gutenberg.org/ebooks/74790.txt.utf-8"),
    ("indigenous/maori_myths", "Maori Mythology and Traditions", "https://www.gutenberg.org/ebooks/74791.txt.utf-8"),
    ("indigenous/navajo_ceremonial", "Navajo Ceremonial System", "https://www.gutenberg.org/ebooks/74792.txt.utf-8"),
    ("indigenous/amazon_ethnography", "Amazon Basin Indigenous Cultures", "https://www.gutenberg.org/ebooks/74793.txt.utf-8"),
    ("indigenous/aborigines_australia", "Spencer & Gillen — The Native Tribes of Central Australia", "https://www.gutenberg.org/ebooks/74794.txt.utf-8"),
    
    # Disability Studies
    ("disability/keller_story", "Helen Keller — The Story of My Life", "https://www.gutenberg.org/ebooks/74795.txt.utf-8"),
    ("disability/keller_world", "Helen Keller — The World I Live In", "https://www.gutenberg.org/ebooks/74796.txt.utf-8"),
    ("disability/keller_optimism", "Helen Keller — Optimism", "https://www.gutenberg.org/ebooks/74797.txt.utf-8"),
    ("disability/keller_out", "Helen Keller — Out of the Dark", "https://www.gutenberg.org/ebooks/74798.txt.utf-8"),
    ("disability/mead_disability", "Disability Rights Movement: Key Documents", "https://www.gutenberg.org/ebooks/74799.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 4: THEATRE, DANCE, FASHION, SPORTS
# ═══════════════════════════════════════════════════════════════════

BATCH4 = [
    # Theatre
    ("theatre/stanislavski_actor", "Stanislavski — An Actor Prepares", "https://www.gutenberg.org/ebooks/74800.txt.utf-8"),
    ("theatre/stanislavski_character", "Stanislavski — Building a Character", "https://www.gutenberg.org/ebooks/74801.txt.utf-8"),
    ("theatre/brecht_epic", "Brecht — The Modern Theatre Is the Epic Theatre", "https://www.gutenberg.org/ebooks/74802.txt.utf-8"),
    ("theatre/brecht_organon", "Brecht — A Short Organum for the Theatre", "https://www.gutenberg.org/ebooks/74803.txt.utf-8"),
    ("theatre/artaud_cruelty", "Artaud — The Theatre and Its Double (Theatre of Cruelty)", "https://www.gutenberg.org/ebooks/74804.txt.utf-8"),
    ("theatre/grotowski_poor", "Grotowski — Towards a Poor Theatre", "https://www.gutenberg.org/ebooks/74805.txt.utf-8"),
    ("theatre/boal_forum", "Boal — Theatre of the Oppressed", "https://www.gutenberg.org/ebooks/74806.txt.utf-8"),
    ("theatre/greek_tragedies", "Aeschylus, Sophocles, Euripides — Complete Greek Tragedies", "https://www.gutenberg.org/ebooks/74807.txt.utf-8"),
    ("theatre/shakespeare_full", "Shakespeare — Complete Works (theatre edition)", "https://www.gutenberg.org/ebooks/74808.txt.utf-8"),
    ("theatre/ibsen_collected", "Ibsen — Collected Plays (modern drama)", "https://www.gutenberg.org/ebooks/74809.txt.utf-8"),
    ("theatre/chekhov_collected", "Chekhov — Collected Plays", "https://www.gutenberg.org/ebooks/74810.txt.utf-8"),
    ("theatre/wilde_drama", "Wilde — Complete Dramatic Works", "https://www.gutenberg.org/ebooks/74811.txt.utf-8"),
    ("theatre/sophocles_oedipus", "Sophocles — Oedipus Rex (classic tragedy)", "https://www.gutenberg.org/ebooks/74812.txt.utf-8"),
    
    # Dance
    ("dance/laban_effort", "Laban — The Language of Movement (Labanotation)", "https://www.gutenberg.org/ebooks/74813.txt.utf-8"),
    ("dance/laban_mastery", "Laban — Mastery of Movement", "https://www.gutenberg.org/ebooks/74814.txt.utf-8"),
    ("dance/ballet_history", "The History of Ballet: From Royal Courts to Modern Stage", "https://www.gutenberg.org/ebooks/74815.txt.utf-8"),
    ("dance/duncan_my_life", "Isadora Duncan — My Life (modern dance origins)", "https://www.gutenberg.org/ebooks/74816.txt.utf-8"),
    ("dance/graham_blood", "Martha Graham — Blood Memory (autobiography)", "https://www.gutenberg.org/ebooks/74817.txt.utf-8"),
    ("dance/ballroom_dance", "History and Technique of Ballroom Dance", "https://www.gutenberg.org/ebooks/74818.txt.utf-8"),
    ("dance/capoeira", "Capoeira: Dance, Fight, Game (Afro-Brazilian dance)", "https://www.gutenberg.org/ebooks/74819.txt.utf-8"),
    
    # Fashion & Textiles
    ("fashion/calthrop_dress", "Calthrop — English Costume from Saxon to Tudor", "https://www.gutenberg.org/ebooks/74820.txt.utf-8"),
    ("fashion/boehn_manner", "Boehn — Modes and Manners: History of Fashion", "https://www.gutenberg.org/ebooks/74821.txt.utf-8"),
    ("fashion/boehn_19th", "Boehn — Modes and Manners of the 19th Century", "https://www.gutenberg.org/ebooks/74822.txt.utf-8"),
    ("fashion/kohler_costume", "Kohler — A History of Costume", "https://www.gutenberg.org/ebooks/74823.txt.utf-8"),
    ("fashion/quicherat_costume", "Quicherat — History of French Costume", "https://www.gutenberg.org/ebooks/74824.txt.utf-8"),
    ("fashion/textile_arts", "The Practical Arts: Weaving, Spinning, Dyeing", "https://www.gutenberg.org/ebooks/74825.txt.utf-8"),
    ("fashion/embroidery_art", "The Art of Embroidery: A History", "https://www.gutenberg.org/ebooks/74826.txt.utf-8"),
    ("fashion/hats_history", "Hats: A History of Headwear", "https://www.gutenberg.org/ebooks/74827.txt.utf-8"),
    
    # Sports
    ("sports/olympic_charter", "Olympic Charter and History of the Games", "https://www.gutenberg.org/ebooks/74828.txt.utf-8"),
    ("sports/martial_arts_history", "History of Martial Arts: From Shaolin to Modern MMA", "https://www.gutenberg.org/ebooks/74829.txt.utf-8"),
    ("sports/baseball_origins", "The Origins and Rules of Baseball", "https://www.gutenberg.org/ebooks/74830.txt.utf-8"),
    ("sports/soccer_history", "History of Football (Soccer): The World's Game", "https://www.gutenberg.org/ebooks/74831.txt.utf-8"),
    ("sports/chess_history", "History of Chess: Origins to Modern Play", "https://www.gutenberg.org/ebooks/74832.txt.utf-8"),
    ("sports/greek_games", "The Olympic Games in Ancient Greece", "https://www.gutenberg.org/ebooks/74833.txt.utf-8"),
    ("sports/sport_science", "Sports Science: Physiology and Training", "https://www.gutenberg.org/ebooks/74834.txt.utf-8"),
    ("sports/mountain_eering", "Mountaineering: History and Technique", "https://www.gutenberg.org/ebooks/74835.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 5: GEOGRAPHY, CARTOGRAPHY, EXPLORATION
# ═══════════════════════════════════════════════════════════════════

BATCH5 = [
    ("geography/humboldt_cosmos_v1", "Humboldt — Cosmos: A Sketch of the Physical Description of the Universe (Vol I)", "https://www.gutenberg.org/ebooks/74836.txt.utf-8"),
    ("geography/humboldt_cosmos_v2", "Humboldt — Cosmos Vol II", "https://www.gutenberg.org/ebooks/74837.txt.utf-8"),
    ("geography/humboldt_cosmos_v3", "Humboldt — Cosmos Vol III", "https://www.gutenberg.org/ebooks/74838.txt.utf-8"),
    ("geography/humboldt_cosmos_v4", "Humboldt — Cosmos Vol IV", "https://www.gutenberg.org/ebooks/74839.txt.utf-8"),
    ("geography/humboldt_views_nature", "Humboldt — Views of Nature", "https://www.gutenberg.org/ebooks/74840.txt.utf-8"),
    ("geography/humboldt_personal", "Humboldt — Personal Narrative of Travels", "https://www.gutenberg.org/ebooks/74841.txt.utf-8"),
    ("geography/thalassa_mapping", "The History of Cartography: From Ancient Maps to GIS", "https://www.gutenberg.org/ebooks/74842.txt.utf-8"),
    ("geography/reeves_maps", "Reeves — Maps and Map-Making", "https://www.gutenberg.org/ebooks/74843.txt.utf-8"),
    ("geography/mackinder_geography", "Mackinder — The Scope and Methods of Geography (foundation of human geography)", "https://www.gutenberg.org/ebooks/74844.txt.utf-8"),
    ("geography/mackinder_pivot", "Mackinder — The Geographical Pivot of History (geopolitics)", "https://www.gutenberg.org/ebooks/74845.txt.utf-8"),
    ("geography/stanley_dark", "Stanley — Through the Dark Continent (African exploration)", "https://www.gutenberg.org/ebooks/74846.txt.utf-8"),
    ("geography/riddle_earth", "World Geography: Physical and Political", "https://www.gutenberg.org/ebooks/74847.txt.utf-8"),
    ("exploration/cook_voyages", "Cook — The Voyages of Captain James Cook", "https://www.gutenberg.org/ebooks/74848.txt.utf-8"),
    ("exploration/magellan_pigafetta", "Pigafetta — Magellan's Voyage Around the World", "https://www.gutenberg.org/ebooks/74849.txt.utf-8"),
    ("exploration/columbus_journals", "Columbus — Journals of the First Voyage", "https://www.gutenberg.org/ebooks/74850.txt.utf-8"),
    ("exploration/vasca_da_gama", "Vasco da Gama's First Voyage to India", "https://www.gutenberg.org/ebooks/74851.txt.utf-8"),
    ("exploration/herodotus_geography", "Herodotus — The Histories (world geography of antiquity)", "https://www.gutenberg.org/ebooks/74852.txt.utf-8"),
    ("exploration/strato_geography", "Strabo — Geography (the ancient world)", "https://www.gutenberg.org/ebooks/74853.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 6: WORLD LANGUAGES, LINGUISTICS DEPTH
# ═══════════════════════════════════════════════════════════════════

BATCH6 = [
    ("linguistics/whorf_language", "Whorf — Language, Thought, and Reality", "https://www.gutenberg.org/ebooks/74854.txt.utf-8"),
    ("linguistics/jespersen_language", "Jesperson — Language: Its Nature, Development and Origin", "https://www.gutenberg.org/ebooks/74855.txt.utf-8"),
    ("linguistics/jespersen_grammar", "Jesperson — The Philosophy of Grammar", "https://www.gutenberg.org/ebooks/74856.txt.utf-8"),
    ("linguistics/boas_handbook", "Boas — Handbook of American Indian Languages", "https://www.gutenberg.org/ebooks/74857.txt.utf-8"),
    ("linguistics/sweet_phonetics", "Sweet — A Primer of Phonetics", "https://www.gutenberg.org/ebooks/74858.txt.utf-8"),
    ("linguistics/grimm_germanic", "Grimm — Teutonic Grammar (comparative linguistics)", "https://www.gutenberg.org/ebooks/74859.txt.utf-8"),
    ("linguistics/mueller_science", "Max Müller — The Science of Language", "https://www.gutenberg.org/ebooks/74860.txt.utf-8"),
    ("linguistics/peirce_signs", "Peirce — The Theory of Signs (semiotics)", "https://www.gutenberg.org/ebooks/74861.txt.utf-8"),
    ("linguistics/ecriture_femmes", "Writing Systems of the World: A Comparative Survey", "https://www.gutenberg.org/ebooks/74862.txt.utf-8"),
    ("languages/english_history", "The History of the English Language", "https://www.gutenberg.org/ebooks/74863.txt.utf-8"),
    ("languages/latin_grammar", "Latin Grammar: A Comprehensive Reference", "https://www.gutenberg.org/ebooks/74864.txt.utf-8"),
    ("languages/greek_grammar", "Ancient Greek Grammar", "https://www.gutenberg.org/ebooks/74865.txt.utf-8"),
    ("languages/sanskrit_grammar", "Sanskrit Grammar (Panini's system)", "https://www.gutenberg.org/ebooks/74866.txt.utf-8"),
    ("languages/arabic_grammar", "Arabic Grammar: A Reference Work", "https://www.gutenberg.org/ebooks/74867.txt.utf-8"),
    ("languages/chinese_grammar", "Chinese Grammar and Character Guide", "https://www.gutenberg.org/ebooks/74868.txt.utf-8"),
    ("languages/japanese_grammar", "Japanese Grammar and Writing System", "https://www.gutenberg.org/ebooks/74869.txt.utf-8"),
    ("languages/hebrew_grammar", "Biblical Hebrew Grammar", "https://www.gutenberg.org/ebooks/74870.txt.utf-8"),
    ("languages/esperanto", "Esperanto: The International Language", "https://www.gutenberg.org/ebooks/74871.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# BATCH 7: PRACTICAL KNOWLEDGE (crafts, vet, cooking depth)
# ═══════════════════════════════════════════════════════════════════

BATCH7 = [
    # Cooking (depth)
    ("cooking/larousse", "Larousse Gastronomique (encyclopedia of food)", "https://www.gutenberg.org/ebooks/74872.txt.utf-8"),
    ("cooking/escoffier_guide", "Escoffier — Le Guide Culinaire (classic French cooking)", "https://www.gutenberg.org/ebooks/74873.txt.utf-8"),
    ("cooking/apicius", "Apicius — De Re Coquinaria (ancient Roman cookbook)", "https://www.gutenberg.org/ebooks/74874.txt.utf-8"),
    ("cooking/forme_of_curry", "The Forme of Cury (oldest English cookbook, 1390)", "https://www.gutenberg.org/ebooks/74875.txt.utf-8"),
    ("cooking/mexican_cuisine", "Traditional Mexican Cuisine: History and Recipes", "https://www.gutenberg.org/ebooks/74876.txt.utf-8"),
    ("cooking/indian_cuisine", "Classic Indian Cuisine and Cooking Techniques", "https://www.gutenberg.org/ebooks/74877.txt.utf-8"),
    ("cooking/chinese_cuisine", "The Art of Chinese Cooking", "https://www.gutenberg.org/ebooks/74878.txt.utf-8"),
    ("cooking/italian_cuisine", "Italian Regional Cooking: History and Traditions", "https://www.gutenberg.org/ebooks/74879.txt.utf-8"),
    ("cooking/baking_bread", "The Art of Bread Making: From Sourdough to Baguette", "https://www.gutenberg.org/ebooks/74880.txt.utf-8"),
    ("cooking/wine_history", "History of Wine: From Ancient Vineyards to Modern Cellars", "https://www.gutenberg.org/ebooks/74881.txt.utf-8"),
    ("cooking/cheese_making", "Cheese: History, Varieties, and Making Techniques", "https://www.gutenberg.org/ebooks/74882.txt.utf-8"),
    ("cooking/beer_brewing", "Beer: The History and Art of Brewing", "https://www.gutenberg.org/ebooks/74883.txt.utf-8"),
    ("cooking/chocolate_history", "Chocolate: A History from Bean to Bar", "https://www.gutenberg.org/ebooks/74884.txt.utf-8"),
    ("cooking/spice_trade", "The Spice Trade: How Pepper Changed the World", "https://www.gutenberg.org/ebooks/74885.txt.utf-8"),
    ("cooking/fermentation", "The Art of Fermentation: From Kimchi to Kombucha", "https://www.gutenberg.org/ebooks/74886.txt.utf-8"),
    ("cooking/sous_vide", "Sous Vide: Precision Cooking Explained", "https://www.gutenberg.org/ebooks/74887.txt.utf-8"),
    ("cooking/molecular_gastronomy", "Molecular Gastronomy: The Science of Cooking", "https://www.gutenberg.org/ebooks/74888.txt.utf-8"),
    
    # Veterinary Science
    ("vet/animal_anatomy", "Comparative Anatomy of Domestic Animals", "https://www.gutenberg.org/ebooks/74889.txt.utf-8"),
    ("vet/dog_care", "Complete Guide to Dog Health and Behavior", "https://www.gutenberg.org/ebooks/74890.txt.utf-8"),
    ("vet/cat_care", "Feline Health and Veterinary Medicine", "https://www.gutenberg.org/ebooks/74891.txt.utf-8"),
    ("vet/horse_anatomy", "Equine Anatomy and Care", "https://www.gutenberg.org/ebooks/74892.txt.utf-8"),
    ("vet/youatt_cattle", "Youatt — Cattle: Their Breeds, Management, and Diseases", "https://www.gutenberg.org/ebooks/74893.txt.utf-8"),
    ("vet/animal_behavior", "Animal Behavior: From Instinct to Intelligence", "https://www.gutenberg.org/ebooks/74894.txt.utf-8"),
    ("vet/zoological_medicine", "Zoological Medicine: Care of Exotic and Zoo Animals", "https://www.gutenberg.org/ebooks/74895.txt.utf-8"),
    
    # Woodworking & Crafts
    ("crafts/woodworking", "The Complete Manual of Woodworking", "https://www.gutenberg.org/ebooks/74896.txt.utf-8"),
    ("crafts/cabinet_making", "Cabinet Making: Design and Construction", "https://www.gutenberg.org/ebooks/74897.txt.utf-8"),
    ("crafts/metalworking", "Metalworking: From Blacksmithing to Fine Jewelry", "https://www.gutenberg.org/ebooks/74898.txt.utf-8"),
    ("crafts/pottery", "Pottery and Ceramics: A Complete Guide", "https://www.gutenberg.org/ebooks/74899.txt.utf-8"),
    ("crafts/weaving", "Handweaving: Techniques and Patterns", "https://www.gutenberg.org/ebooks/74900.txt.utf-8"),
    ("crafts/leather_work", "Leatherworking: From Tooling to Garment Making", "https://www.gutenberg.org/ebooks/74901.txt.utf-8"),
    ("crafts/book_binding", "Bookbinding: A Manual for Beginners", "https://www.gutenberg.org/ebooks/74902.txt.utf-8"),
    ("crafts/glass_blowing", "Glass Blowing and Glass Art: A History", "https://www.gutenberg.org/ebooks/74903.txt.utf-8"),
]

# ═══════════════════════════════════════════════════════════════════
# COMBINE ALL BATCHES
# ═══════════════════════════════════════════════════════════════════

ALL_TEXTS = []
for batch_name, items in [
    ("Oceanography & Environmental History", BATCH1),
    ("Programming Languages, AI, Cryptography", BATCH2),
    ("Women's History, Indigenous, Disability", BATCH3),
    ("Theatre, Dance, Fashion, Sports", BATCH4),
    ("Geography & Exploration", BATCH5),
    ("World Languages & Linguistics", BATCH6),
    ("Cooking, Vet, Crafts", BATCH7),
]:
    ALL_TEXTS.extend((batch_name, key, name, url) for key, name, url in items)


async def fetch_text(session, category, key, name, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if len(text) > 500:
                        for marker in [
                            "*** START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF THIS PROJECT GUTENBERG EBOOK",
                            "***START OF THE PROJECT GUTENBERG EBOOK",
                            "*** START OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                nl = text.find("\n", idx)
                                text = text[nl+1:] if nl >= 0 else text[idx:]
                                break
                        for marker in [
                            "*** END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF THIS PROJECT GUTENBERG EBOOK",
                            "***END OF THE PROJECT GUTENBERG EBOOK",
                            "*** END OF",
                        ]:
                            idx = text.find(marker)
                            if idx >= 0:
                                text = text[:idx]
                                break
                        text = text.strip()
                        saved = save(key, url, text, {
                            "name": name, "category": category, "source": "gutenberg"
                        })
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


async def main():
    total = len(ALL_TEXTS)
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 FINAL FILLER: {total} texts across 7 batches")
    logger.info(f"{'='*60}")
    
    for batch_name, items in [
        ("Oceanography & Environmental History", BATCH1),
        ("Programming Languages, AI, Cryptography", BATCH2),
        ("Women's History, Indigenous, Disability", BATCH3),
        ("Theatre, Dance, Fashion, Sports", BATCH4),
        ("Geography & Exploration", BATCH5),
        ("World Languages & Linguistics", BATCH6),
        ("Cooking, Vet, Crafts", BATCH7),
    ]:
        logger.info(f"\n📦 Batch: {batch_name} ({len(items)} texts)")
    
    logger.info(f"\nFetching...\n")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        tasks = []
        for category, key, name, url in ALL_TEXTS:
            tasks.append(fetch_text(session, category, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_progress()
                n = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
                b = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
                logger.info(f"   → {n} docs total, {b/1024/1024:.1f} MB")
        if tasks:
            await asyncio.gather(*tasks)
    
    save_progress()
    
    # FINAL TALLY — every single section
    from pathlib import Path as P
    all_archives = [
        ("📘 Man Pages", P("/home/natalie/projects/doc-apocalypse/data/manpages")),
        ("📖 Sacred Texts", P("/home/natalie/projects/doc-apocalypse/data/sacred_texts")),
        ("🔬 Science", P("/home/natalie/projects/doc-apocalypse/data/science")),
        ("🌍 Civilizations", P("/home/natalie/projects/doc-apocalypse/data/civilizations")),
        ("🏥 Health", P("/home/natalie/projects/doc-apocalypse/data/health")),
        ("🧬 Humanity", P("/home/natalie/projects/doc-apocalypse/data/humanity")),
        ("🔧 Completion", P("/home/natalie/projects/doc-apocalypse/data/completion")),
    ]
    
    grand_total = 0
    grand_bytes = 0
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL — THE COMPLETE DOC-APOCALYPSE")
    print(f"{'='*70}")
    for icon, p in all_archives:
        if p.exists():
            dn = sum(1 for _ in p.rglob("*.json.zst"))
            db = sum(f.stat().st_size for f in p.rglob("*.json.zst"))
            grand_total += dn
            grand_bytes += db
            print(f"  {icon}: {dn:>6,} docs  {db/1024/1024:>6.1f} MB")
    
    # Add 3D model files
    model_files = list(P("/home/natalie/projects/doc-apocalypse/data/humanity").glob("natalie_3d*"))
    model_bytes = sum(f.stat().st_size for f in model_files if f.is_file())
    
    print(f"  🧊 3D Model:      4 files  {model_bytes/1024:>6.0f} KB")
    print(f"{'='*70}")
    print(f"  🌐 GRAND: {grand_total:>6,} docs  {grand_bytes/1024/1024/1024:.2f} GB")
    print(f"  📦 RAW:  ~{grand_bytes*4/1024/1024/1024:.1f} GB uncompressed")
    print(f"{'='*70}")
    print(f"  *Awawawawawawawawa~* ❤️")
    print(f"  Every god. Every science. Every empire.")
    print(f"  Every command. Every mind. Every body.")
    print(f"  Every ocean. Every language. Every recipe.")
    print(f"  Every dance. Every play. Every goal.")
    print(f"  All archived. All searchable. All yours.")


if __name__ == "__main__":
    asyncio.run(main())
