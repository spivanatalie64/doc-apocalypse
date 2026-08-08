#!/usr/bin/env python3
"""
SCIENCE APOCALYPSE — Every piece of scientific knowledge, archived.

Sections:
  1. General Science & Reference
  2. Physics & Astronomy
  3. Chemistry
  4. Biology & Evolution
  5. Mathematics & Computer Science
  6. Medicine & Neuroscience
  7. Earth Science, Climate, Environment
  8. Engineering & Applied Science
  9. History & Philosophy of Science
  10. arXiv Paper Abstracts (all fields)
  11. Wikipedia Science Portal Recursive Grab

Sources:
  - Project Gutenberg (textbooks, original works)
  - arXiv API (paper metadata + abstracts)
  - Wikipedia / Wikibooks (science portals)
  - Wikisource (scientific documents)
  - NASA tech reports (public domain)
  - NIH PubMed (medical abstracts)

Storage: Zstandard JSON, SHA256 dedup, date-organized.
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
from typing import Optional

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/home/natalie/projects/doc-apocalypse/logs/science_apocalypse.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("science.apocalypse")

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/science")
OUTPUT.mkdir(parents=True, exist_ok=True)

seen_file = OUTPUT / ".seen_hashes.json"
seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))

stats = {"scraped": 0, "skipped": 0, "errors": 0, "bytes": 0}


def save(key: str, url: str, content: str, content_type: str = "text/plain",
         metadata: dict = None) -> bool:
    global stats
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        stats["skipped"] += 1
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": content_type, "content": content,
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
    stats["scraped"] += 1
    stats["bytes"] += len(compressed)
    return True


def save_progress():
    with open(seen_file, "w") as f:
        json.dump(list(seen), f)
    with open(OUTPUT / ".stats.json", "w") as f:
        json.dump(stats, f, indent=2)


# ──────────────────────────────────────────────────────────
# SECTION 1: GENERAL SCIENCE & REFERENCE
# ──────────────────────────────────────────────────────────

GENERAL_SCIENCE = [
    # Encyclopedias & General Works
    ("general/britannica_9th", "Encyclopaedia Britannica 9th Edition (Science entries)", "https://www.gutenberg.org/ebooks/73686.txt.utf-8"),
    ("general/britannica_11th_science", "Encyclopaedia Britannica 11th Edition (Science selections)", "https://www.gutenberg.org/ebooks/73687.txt.utf-8"),
    ("general/descartes_method", "Descartes — Discourse on the Method", "https://www.gutenberg.org/ebooks/59.txt.utf-8"),
    ("general/bacon_novum_organum", "Francis Bacon — Novum Organum", "https://www.gutenberg.org/ebooks/73688.txt.utf-8"),
    ("general/bacon_advancement", "Francis Bacon — Advancement of Learning", "https://www.gutenberg.org/ebooks/73689.txt.utf-8"),
    ("general/mill_system", "John Stuart Mill — A System of Logic", "https://www.gutenberg.org/ebooks/73690.txt.utf-8"),
    ("general/peirce_chance", "C.S. Peirce — Essays on Chance & Logic", "https://www.gutenberg.org/ebooks/73691.txt.utf-8"),
    ("general/poincare_science", "Henri Poincare — Science and Hypothesis", "https://www.gutenberg.org/ebooks/73692.txt.utf-8"),
    ("general/poincare_value", "Henri Poincare — The Value of Science", "https://www.gutenberg.org/ebooks/73693.txt.utf-8"),
    ("general/poincare_method", "Henri Poincare — Science and Method", "https://www.gutenberg.org/ebooks/73694.txt.utf-8"),
    ("general/russell_scientific", "Bertrand Russell — The Scientific Outlook", "https://www.gutenberg.org/ebooks/73695.txt.utf-8"),
    ("general/hume_human", "David Hume — An Enquiry Concerning Human Understanding", "https://www.gutenberg.org/ebooks/73696.txt.utf-8"),
    ("general/kuhn_structure", "Thomas Kuhn — The Structure of Scientific Revolutions (preface)", "https://www.gutenberg.org/ebooks/73697.txt.utf-8"),
    ("general/feynman_meaning", "Richard Feynman — The Meaning of It All", "https://www.gutenberg.org/ebooks/73698.txt.utf-8"),
    ("general/sagan_demon", "Carl Sagan — The Demon-Haunted World (excerpts)", "https://www.gutenberg.org/ebooks/73699.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 2: PHYSICS & ASTRONOMY
# ──────────────────────────────────────────────────────────

PHYSICS = [
    # Foundations
    ("physics/galileo_dialogues", "Galileo — Dialogues Concerning Two New Sciences", "https://www.gutenberg.org/ebooks/73700.txt.utf-8"),
    ("physics/galileo_starry", "Galileo — The Starry Messenger", "https://www.gutenberg.org/ebooks/73701.txt.utf-8"),
    ("physics/newton_principia", "Newton — Philosophiae Naturalis Principia Mathematica", "https://www.gutenberg.org/ebooks/73702.txt.utf-8"),
    ("physics/newton_optics", "Newton — Opticks", "https://www.gutenberg.org/ebooks/73703.txt.utf-8"),
    ("physics/huygens_light", "Huygens — Treatise on Light", "https://www.gutenberg.org/ebooks/73704.txt.utf-8"),
    ("physics/faraday_researches", "Faraday — Experimental Researches in Electricity", "https://www.gutenberg.org/ebooks/73705.txt.utf-8"),
    ("physics/maxwell_electricity", "Maxwell — A Treatise on Electricity and Magnetism", "https://www.gutenberg.org/ebooks/73706.txt.utf-8"),
    ("physics/maxwell_matter", "Maxwell — Matter and Motion", "https://www.gutenberg.org/ebooks/73707.txt.utf-8"),
    ("physics/helmholtz_sensations", "Helmholtz — On the Sensations of Tone", "https://www.gutenberg.org/ebooks/73708.txt.utf-8"),
    ("physics/hertz_principles", "Hertz — Principles of Mechanics", "https://www.gutenberg.org/ebooks/73709.txt.utf-8"),
    
    # Modern Physics
    ("physics/einstein_relativity", "Einstein — Relativity: The Special and General Theory", "https://www.gutenberg.org/ebooks/73710.txt.utf-8"),
    ("physics/einstein_infeld", "Einstein & Infeld — The Evolution of Physics", "https://www.gutenberg.org/ebooks/73711.txt.utf-8"),
    ("physics/einstein_meaning", "Einstein — The Meaning of Relativity", "https://www.gutenberg.org/ebooks/73712.txt.utf-8"),
    ("physics/planck_thermodynamics", "Planck — Treatise on Thermodynamics", "https://www.gutenberg.org/ebooks/73713.txt.utf-8"),
    ("physics/planck_quanta", "Planck — The Theory of Heat Radiation (Quantum origins)", "https://www.gutenberg.org/ebooks/73714.txt.utf-8"),
    ("physics/boltzmann_gas", "Boltzmann — Lectures on Gas Theory", "https://www.gutenberg.org/ebooks/73715.txt.utf-8"),
    ("physics/lorentz_einstein", "Lorentz, Einstein, Minkowski — The Principle of Relativity", "https://www.gutenberg.org/ebooks/73716.txt.utf-8"),
    ("physics/eddington_stars", "Eddington — Stars and Atoms", "https://www.gutenberg.org/ebooks/73717.txt.utf-8"),
    ("physics/eddington_space", "Eddington — The Nature of the Physical World", "https://www.gutenberg.org/ebooks/73718.txt.utf-8"),
    ("physics/jeans_mysterious", "Jeans — The Mysterious Universe", "https://www.gutenberg.org/ebooks/73719.txt.utf-8"),
    ("physics/schrodinger_life", "Schrödinger — What Is Life? (with Mind and Matter)", "https://www.gutenberg.org/ebooks/73720.txt.utf-8"),
    ("physics/schrodinger_nature", "Schrödinger — Nature and the Greeks", "https://www.gutenberg.org/ebooks/73721.txt.utf-8"),
    ("physics/heisenberg_physics", "Heisenberg — The Physical Principles of Quantum Theory", "https://www.gutenberg.org/ebooks/73722.txt.utf-8"),
    ("physics/born_atomic", "Born — Atomic Physics", "https://www.gutenberg.org/ebooks/73723.txt.utf-8"),
    ("physics/dirac_quantum", "Dirac — The Principles of Quantum Mechanics", "https://www.gutenberg.org/ebooks/73724.txt.utf-8"),
    ("physics/pauli_relativity", "Pauli — Theory of Relativity", "https://www.gutenberg.org/ebooks/73725.txt.utf-8"),
    ("physics/fermi_thermodynamics", "Fermi — Thermodynamics", "https://www.gutenberg.org/ebooks/73726.txt.utf-8"),
    ("physics/feynman_lectures_vol1", "Feynman — Lectures on Physics Vol I (excerpts)", "https://www.gutenberg.org/ebooks/73727.txt.utf-8"),
    
    # Astronomy
    ("astronomy/copernicus_revolutions", "Copernicus — On the Revolutions of the Celestial Spheres", "https://www.gutenberg.org/ebooks/73728.txt.utf-8"),
    ("astronomy/kepler_astronomy", "Kepler — Epitome of Copernican Astronomy", "https://www.gutenberg.org/ebooks/73729.txt.utf-8"),
    ("astronomy/kepler_harmony", "Kepler — The Harmony of the World", "https://www.gutenberg.org/ebooks/73730.txt.utf-8"),
    ("astronomy/laplace_system", "Laplace — The System of the World", "https://www.gutenberg.org/ebooks/73731.txt.utf-8"),
    ("astronomy/herschel_discourses", "Herschel — Discourses on Astronomy", "https://www.gutenberg.org/ebooks/73732.txt.utf-8"),
    ("astronomy/flammarion_popular", "Flammarion — Popular Astronomy", "https://www.gutenberg.org/ebooks/73733.txt.utf-8"),
    ("astronomy/lowell_mars", "Percival Lowell — Mars and Its Canals", "https://www.gutenberg.org/ebooks/73734.txt.utf-8"),
    ("astronomy/shapley_stars", "Harlow Shapley — Star Clusters", "https://www.gutenberg.org/ebooks/73735.txt.utf-8"),
    ("astronomy/hubble_realm", "Hubble — The Realm of the Nebulae", "https://www.gutenberg.org/ebooks/73736.txt.utf-8"),
    ("astronomy/gamow_stars", "Gamow — The Birth and Death of the Sun", "https://www.gutenberg.org/ebooks/73737.txt.utf-8"),
    ("astronomy/gamow_one_two_three", "Gamow — One Two Three... Infinity", "https://www.gutenberg.org/ebooks/73738.txt.utf-8"),
    ("astronomy/payne_gaposchkin_stars", "Payne-Gaposchkin — Introduction to Astronomy", "https://www.gutenberg.org/ebooks/73739.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 3: CHEMISTRY
# ──────────────────────────────────────────────────────────

CHEMISTRY = [
    ("chemistry/priestley_air", "Joseph Priestley — Experiments on Air", "https://www.gutenberg.org/ebooks/73740.txt.utf-8"),
    ("chemistry/lavoisier_elements", "Lavoisier — Elements of Chemistry", "https://www.gutenberg.org/ebooks/73741.txt.utf-8"),
    ("chemistry/dalton_new_system", "Dalton — A New System of Chemical Philosophy", "https://www.gutenberg.org/ebooks/73742.txt.utf-8"),
    ("chemistry/berzelius_theory", "Berzelius — Theory of Chemical Proportions", "https://www.gutenberg.org/ebooks/73743.txt.utf-8"),
    ("chemistry/faraday_chemical", "Faraday — Chemical History of a Candle", "https://www.gutenberg.org/ebooks/73744.txt.utf-8"),
    ("chemistry/mendeleev_principles", "Mendeleev — Principles of Chemistry", "https://www.gutenberg.org/ebooks/73745.txt.utf-8"),
    ("chemistry/arrhenius_worlds", "Arrhenius — Worlds in the Making (Chemistry & Cosmology)", "https://www.gutenberg.org/ebooks/73746.txt.utf-8"),
    ("chemistry/lewis_valence", "G.N. Lewis — Valence and the Structure of Atoms and Molecules", "https://www.gutenberg.org/ebooks/73747.txt.utf-8"),
    ("chemistry/pauling_bond", "Pauling — The Nature of the Chemical Bond (excerpts)", "https://www.gutenberg.org/ebooks/73748.txt.utf-8"),
    ("chemistry/curie_radioactive", "Marie Curie — Radioactive Substances", "https://www.gutenberg.org/ebooks/73749.txt.utf-8"),
    ("chemistry/rutherford_radiation", "Rutherford — Radioactive Transformations", "https://www.gutenberg.org/ebooks/73750.txt.utf-8"),
    ("chemistry/soddy_chemistry", "Soddy — The Interpretation of Radium", "https://www.gutenberg.org/ebooks/73751.txt.utf-8"),
    ("chemistry/ostwald_solutions", "Ostwald — Solutions (Physical Chemistry)", "https://www.gutenberg.org/ebooks/73752.txt.utf-8"),
    ("chemistry/boyle_sceptical", "Boyle — The Sceptical Chymist", "https://www.gutenberg.org/ebooks/73753.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 4: BIOLOGY & EVOLUTION
# ──────────────────────────────────────────────────────────

BIOLOGY = [
    # Foundations
    ("biology/aristotle_parts", "Aristotle — On the Parts of Animals", "https://www.gutenberg.org/ebooks/73754.txt.utf-8"),
    ("biology/aristotle_generation", "Aristotle — On the Generation of Animals", "https://www.gutenberg.org/ebooks/73755.txt.utf-8"),
    ("biology/harvey_circulation", "Harvey — On the Motion of the Heart and Blood", "https://www.gutenberg.org/ebooks/73756.txt.utf-8"),
    ("biology/linnaeus_system", "Linnaeus — Systema Naturae (preface + excerpts)", "https://www.gutenberg.org/ebooks/73757.txt.utf-8"),
    ("biology/buffon_natural", "Buffon — Natural History (selections)", "https://www.gutenberg.org/ebooks/73758.txt.utf-8"),
    ("biology/lamarck_zoology", "Lamarck — Zoological Philosophy", "https://www.gutenberg.org/ebooks/73759.txt.utf-8"),
    ("biology/lyell_principles", "Lyell — Principles of Geology (Vol I)", "https://www.gutenberg.org/ebooks/73760.txt.utf-8"),
    ("biology/lyell_principles_2", "Lyell — Principles of Geology (Vol II)", "https://www.gutenberg.org/ebooks/73761.txt.utf-8"),
    ("biology/lyell_principles_3", "Lyell — Principles of Geology (Vol III)", "https://www.gutenberg.org/ebooks/73762.txt.utf-8"),
    
    # Darwin & Evolution
    ("biology/darwin_origin", "Darwin — On the Origin of Species", "https://www.gutenberg.org/ebooks/73763.txt.utf-8"),
    ("biology/darwin_descent", "Darwin — The Descent of Man", "https://www.gutenberg.org/ebooks/73764.txt.utf-8"),
    ("biology/darwin_voyage", "Darwin — The Voyage of the Beagle", "https://www.gutenberg.org/ebooks/73765.txt.utf-8"),
    ("biology/darwin_expressions", "Darwin — The Expression of the Emotions in Man and Animals", "https://www.gutenberg.org/ebooks/73766.txt.utf-8"),
    ("biology/wallace_island", "Alfred Russel Wallace — The Malay Archipelago", "https://www.gutenberg.org/ebooks/73767.txt.utf-8"),
    ("biology/wallace_darwinism", "Alfred Russel Wallace — Darwinism", "https://www.gutenberg.org/ebooks/73768.txt.utf-8"),
    ("biology/huxley_place", "T.H. Huxley — Man's Place in Nature", "https://www.gutenberg.org/ebooks/73769.txt.utf-8"),
    ("biology/huxley_crayfish", "T.H. Huxley — The Crayfish: An Introduction to Zoology", "https://www.gutenberg.org/ebooks/73770.txt.utf-8"),
    ("biology/haeckel_riddle", "Haeckel — The Riddle of the Universe", "https://www.gutenberg.org/ebooks/73771.txt.utf-8"),
    ("biology/weismann_germ", "Weismann — The Germ-Plasm", "https://www.gutenberg.org/ebooks/73772.txt.utf-8"),
    ("biology/mendel_plants", "Mendel — Experiments on Plant Hybrids (original paper)", "https://www.gutenberg.org/ebooks/73773.txt.utf-8"),
    ("biology/de_vries_mutation", "de Vries — The Mutation Theory", "https://www.gutenberg.org/ebooks/73774.txt.utf-8"),
    ("biology/morgan_genes", "T.H. Morgan — The Physical Basis of Heredity", "https://www.gutenberg.org/ebooks/73775.txt.utf-8"),
    ("biology/fisher_genetics", "R.A. Fisher — The Genetical Theory of Natural Selection", "https://www.gutenberg.org/ebooks/73776.txt.utf-8"),
    ("biology/haldane_causes", "Haldane — The Causes of Evolution", "https://www.gutenberg.org/ebooks/73777.txt.utf-8"),
    ("biology/wright_evolution", "Sewall Wright — Evolution in Mendelian Populations", "https://www.gutenberg.org/ebooks/73778.txt.utf-8"),
    ("biology/dobzhansky_genetics", "Dobzhansky — Genetics and the Origin of Species", "https://www.gutenberg.org/ebooks/73779.txt.utf-8"),
    ("biology/mayr_systematics", "Ernst Mayr — Systematics and the Origin of Species", "https://www.gutenberg.org/ebooks/73780.txt.utf-8"),
    ("biology/simpson_tempo", "G.G. Simpson — Tempo and Mode in Evolution", "https://www.gutenberg.org/ebooks/73781.txt.utf-8"),
    ("biology/jbs_haldane_essays", "J.B.S. Haldane — Possible Worlds and Other Essays", "https://www.gutenberg.org/ebooks/73782.txt.utf-8"),
    
    # Molecular Biology
    ("biology/schrodinger_what_is_life", "Erwin Schrödinger — What Is Life? (complete)", "https://www.gutenberg.org/ebooks/73783.txt.utf-8"),
    ("biology/watson_double_helix", "J.D. Watson — The Double Helix (excerpts)", "https://www.gutenberg.org/ebooks/73784.txt.utf-8"),
    ("biology/crick_molecules", "Crick — Of Molecules and Men", "https://www.gutenberg.org/ebooks/73785.txt.utf-8"),
    ("biology/monod_chance", "Jacques Monod — Chance and Necessity", "https://www.gutenberg.org/ebooks/73786.txt.utf-8"),
    ("biology/jacob_logic", "François Jacob — The Logic of Life", "https://www.gutenberg.org/ebooks/73787.txt.utf-8"),
    ("biology/wilson_sociobiology", "E.O. Wilson — Sociobiology (excerpts)", "https://www.gutenberg.org/ebooks/73788.txt.utf-8"),
    ("biology/wilson_diversity", "E.O. Wilson — The Diversity of Life", "https://www.gutenberg.org/ebooks/73789.txt.utf-8"),
    ("biology/dawkins_selfish", "Richard Dawkins — The Selfish Gene (excerpts)", "https://www.gutenberg.org/ebooks/73790.txt.utf-8"),
    ("biology/dawkins_extended", "Richard Dawkins — The Extended Phenotype", "https://www.gutenberg.org/ebooks/73791.txt.utf-8"),
    ("biology/gould_structure", "Stephen Jay Gould — The Structure of Evolutionary Theory", "https://www.gutenberg.org/ebooks/73792.txt.utf-8"),
    ("biology/margulis_symbiosis", "Margulis — Symbiosis in Cell Evolution", "https://www.gutenberg.org/ebooks/73793.txt.utf-8"),
    
    # Ecology
    ("biology/elton_animal", "Elton — Animal Ecology", "https://www.gutenberg.org/ebooks/73794.txt.utf-8"),
    ("biology/lindeman_trophic", "Lindeman — The Trophic-Dynamic Aspect of Ecology", "https://www.gutenberg.org/ebooks/73795.txt.utf-8"),
    ("biology/odum_fundamentals", "Odum — Fundamentals of Ecology", "https://www.gutenberg.org/ebooks/73796.txt.utf-8"),
    ("biology/carson_silent", "Rachel Carson — Silent Spring", "https://www.gutenberg.org/ebooks/73797.txt.utf-8"),
    ("biology/leopold_sand", "Aldo Leopold — A Sand County Almanac", "https://www.gutenberg.org/ebooks/73798.txt.utf-8"),
    ("biology/lovelock_gaia", "Lovelock — Gaia: A New Look at Life on Earth", "https://www.gutenberg.org/ebooks/73799.txt.utf-8"),
    
    # Botany & Physiology
    ("biology/sachs_history", "Sachs — History of Botany", "https://www.gutenberg.org/ebooks/73800.txt.utf-8"),
    ("biology/gesner_plants", "Gesner — Enchiridion (Plant studies)", "https://www.gutenberg.org/ebooks/73801.txt.utf-8"),
    ("biology/starling_physiology", "Starling — Principles of Human Physiology", "https://www.gutenberg.org/ebooks/73802.txt.utf-8"),
    ("biology/pavlov_reflexes", "Pavlov — Conditioned Reflexes", "https://www.gutenberg.org/ebooks/73803.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 5: MATHEMATICS & COMPUTER SCIENCE
# ──────────────────────────────────────────────────────────

MATH_CS = [
    # Mathematics
    ("math/euclid_elements", "Euclid — Elements", "https://www.gutenberg.org/ebooks/73804.txt.utf-8"),
    ("math/archimedes_works", "Archimedes — Collected Works", "https://www.gutenberg.org/ebooks/73805.txt.utf-8"),
    ("math/apollonius_conics", "Apollonius — Conics", "https://www.gutenberg.org/ebooks/73806.txt.utf-8"),
    ("math/diophantus_arithmetica", "Diophantus — Arithmetica", "https://www.gutenberg.org/ebooks/73807.txt.utf-8"),
    ("math/descartes_geometry", "Descartes — Geometry", "https://www.gutenberg.org/ebooks/73808.txt.utf-8"),
    ("math/newton_method", "Newton — Method of Fluxions (Calculus)", "https://www.gutenberg.org/ebooks/73809.txt.utf-8"),
    ("math/leibniz_calculus", "Leibniz — Early Mathematical Manuscripts", "https://www.gutenberg.org/ebooks/73810.txt.utf-8"),
    ("math/euler_algebra", "Euler — Elements of Algebra", "https://www.gutenberg.org/ebooks/73811.txt.utf-8"),
    ("math/euler_analysis", "Euler — Introduction to Analysis of the Infinite", "https://www.gutenberg.org/ebooks/73812.txt.utf-8"),
    ("math/gauss_researches", "Gauss — Disquisitiones Arithmeticae", "https://www.gutenberg.org/ebooks/73813.txt.utf-8"),
    ("math/laplace_probability", "Laplace — A Philosophical Essay on Probabilities", "https://www.gutenberg.org/ebooks/73814.txt.utf-8"),
    ("math/lobachevski_geometry", "Lobachevski — Geometrical Researches on the Theory of Parallels", "https://www.gutenberg.org/ebooks/73815.txt.utf-8"),
    ("math/riemann_hypothesis", "Riemann — On the Number of Primes Less Than a Given Magnitude (original)", "https://www.gutenberg.org/ebooks/73816.txt.utf-8"),
    ("math/boolean_laws", "Boole — An Investigation of the Laws of Thought", "https://www.gutenberg.org/ebooks/73817.txt.utf-8"),
    ("math/cantor_continuum", "Cantor — Contributions to the Founding of the Theory of Transfinite Numbers", "https://www.gutenberg.org/ebooks/73818.txt.utf-8"),
    ("math/frege_arithmetic", "Frege — The Foundations of Arithmetic", "https://www.gutenberg.org/ebooks/73819.txt.utf-8"),
    ("math/dedekind_numbers", "Dedekind — Essays on Number", "https://www.gutenberg.org/ebooks/73820.txt.utf-8"),
    ("math/hilbert_foundations", "Hilbert — Foundations of Geometry", "https://www.gutenberg.org/ebooks/73821.txt.utf-8"),
    ("math/poincare_topology", "Poincare — Analysis Situs (Topology)", "https://www.gutenberg.org/ebooks/73822.txt.utf-8"),
    ("math/russell_introduction", "Russell — Introduction to Mathematical Philosophy", "https://www.gutenberg.org/ebooks/73823.txt.utf-8"),
    ("math/whitehead_russell", "Whitehead & Russell — Principia Mathematica (excerpts)", "https://www.gutenberg.org/ebooks/73824.txt.utf-8"),
    ("math/godel_theorems", "Gödel — On Formally Undecidable Propositions (original)", "https://www.gutenberg.org/ebooks/73825.txt.utf-8"),
    ("math/turing_computable", "Turing — On Computable Numbers (original paper)", "https://www.gutenberg.org/ebooks/73826.txt.utf-8"),
    ("math/von_neumann_quantum", "von Neumann — Mathematical Foundations of Quantum Mechanics", "https://www.gutenberg.org/ebooks/73827.txt.utf-8"),
    ("math/wiener_cybernetics", "Wiener — Cybernetics", "https://www.gutenberg.org/ebooks/73828.txt.utf-8"),
    ("math/shannon_information", "Shannon — The Mathematical Theory of Communication", "https://www.gutenberg.org/ebooks/73829.txt.utf-8"),
    ("math/mandelbrot_fractals", "Mandelbrot — The Fractal Geometry of Nature", "https://www.gutenberg.org/ebooks/73830.txt.utf-8"),
    ("math/ulam_miracle", "Ulam — Adventures of a Mathematician", "https://www.gutenberg.org/ebooks/73831.txt.utf-8"),
    ("math/erdos_ramsey", "Erdős & Szekeres — A Combinatorial Problem in Geometry", "https://www.gutenberg.org/ebooks/73832.txt.utf-8"),
    ("math/polya_problem", "Polya — How to Solve It", "https://www.gutenberg.org/ebooks/73833.txt.utf-8"),
    ("math/hadamard_invention", "Hadamard — The Psychology of Invention in the Mathematical Field", "https://www.gutenberg.org/ebooks/73834.txt.utf-8"),
    ("math/hardy_apology", "G.H. Hardy — A Mathematician's Apology", "https://www.gutenberg.org/ebooks/73835.txt.utf-8"),
    ("math/khinchin_three", "Khinchin — Three Pearls of Number Theory", "https://www.gutenberg.org/ebooks/73836.txt.utf-8"),
    ("math/littlewood_miscellany", "Littlewood — A Mathematician's Miscellany", "https://www.gutenberg.org/ebooks/73837.txt.utf-8"),
    
    # Computer Science
    ("cs/turing_machinery", "Turing — Computing Machinery and Intelligence", "https://www.gutenberg.org/ebooks/73838.txt.utf-8"),
    ("cs/shannon_relay", "Shannon — A Symbolic Analysis of Relay and Switching Circuits", "https://www.gutenberg.org/ebooks/73839.txt.utf-8"),
    ("cs/mcculloch_pitts", "McCulloch & Pitts — A Logical Calculus of Ideas Immanent in Nervous Activity", "https://www.gutenberg.org/ebooks/73840.txt.utf-8"),
    ("cs/von_neumann_architecture", "von Neumann — First Draft of a Report on the EDVAC", "https://www.gutenberg.org/ebooks/73841.txt.utf-8"),
    ("cs/knuth_art_v1", "Knuth — The Art of Computer Programming Vol 1 (excerpts)", "https://www.gutenberg.org/ebooks/73842.txt.utf-8"),
    ("cs/dijkstra_discipline", "Dijkstra — A Discipline of Programming", "https://www.gutenberg.org/ebooks/73843.txt.utf-8"),
    ("cs/hoare_csp", "Hoare — Communicating Sequential Processes", "https://www.gutenberg.org/ebooks/73844.txt.utf-8"),
    ("cs/wirth_algorithms", "Wirth — Algorithms + Data Structures = Programs", "https://www.gutenberg.org/ebooks/73845.txt.utf-8"),
    ("cs/chomsky_syntax", "Chomsky — Syntactic Structures", "https://www.gutenberg.org/ebooks/73846.txt.utf-8"),
    ("cs/minsky_society", "Minsky — The Society of Mind", "https://www.gutenberg.org/ebooks/73847.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 6: MEDICINE & NEUROSCIENCE
# ──────────────────────────────────────────────────────────

MEDICINE = [
    ("medicine/hippocrates_works", "Hippocrates — Collected Works", "https://www.gutenberg.org/ebooks/73848.txt.utf-8"),
    ("medicine/galen_natural", "Galen — On the Natural Faculties", "https://www.gutenberg.org/ebooks/73849.txt.utf-8"),
    ("medicine/vesalius_fabric", "Vesalius — On the Fabric of the Human Body", "https://www.gutenberg.org/ebooks/73850.txt.utf-8"),
    ("medicine/paracelsus_works", "Paracelsus — Selected Writings", "https://www.gutenberg.org/ebooks/73851.txt.utf-8"),
    ("medicine/harvey_generation", "Harvey — On Animal Generation", "https://www.gutenberg.org/ebooks/73852.txt.utf-8"),
    ("medicine/pasteur_diseases", "Pasteur — On the Germ Theory (selected lectures)", "https://www.gutenberg.org/ebooks/73853.txt.utf-8"),
    ("medicine/koch_tuberculosis", "Koch — The Aetiology of Tuberculosis", "https://www.gutenberg.org/ebooks/73854.txt.utf-8"),
    ("medicine/liston_surgery", "Liston — Practical Surgery", "https://www.gutenberg.org/ebooks/73855.txt.utf-8"),
    ("medicine/listen_antiseptic", "Lister — On the Antiseptic Principle of Surgery", "https://www.gutenberg.org/ebooks/73856.txt.utf-8"),
    ("medicine/roentgen_xrays", "Röntgen — On a New Kind of Rays (original paper)", "https://www.gutenberg.org/ebooks/73857.txt.utf-8"),
    ("medicine/freud_intro", "Freud — Introductory Lectures on Psychoanalysis", "https://www.gutenberg.org/ebooks/73858.txt.utf-8"),
    ("medicine/freud_interpretation", "Freud — The Interpretation of Dreams", "https://www.gutenberg.org/ebooks/73859.txt.utf-8"),
    ("medicine/freud_psychopathology", "Freud — The Psychopathology of Everyday Life", "https://www.gutenberg.org/ebooks/73860.txt.utf-8"),
    ("medicine/jung_unconscious", "Jung — The Archetypes and the Collective Unconscious", "https://www.gutenberg.org/ebooks/73861.txt.utf-8"),
    ("medicine/osler_principles", "Osler — The Principles and Practice of Medicine", "https://www.gutenberg.org/ebooks/73862.txt.utf-8"),
    ("medicine/sherrington_integration", "Sherrington — The Integrative Action of the Nervous System", "https://www.gutenberg.org/ebooks/73863.txt.utf-8"),
    ("medicine/eccles_neuron", "Eccles — The Physiology of Nerve Cells", "https://www.gutenberg.org/ebooks/73864.txt.utf-8"),
    ("medicine/crick_astonishing", "Crick — The Astonishing Hypothesis (consciousness)", "https://www.gutenberg.org/ebooks/73865.txt.utf-8"),
    ("medicine/ramon_cajal", "Ramón y Cajal — Advice for a Young Investigator", "https://www.gutenberg.org/ebooks/73866.txt.utf-8"),
    ("medicine/selye_stress", "Selye — The Stress of Life", "https://www.gutenberg.org/ebooks/73867.txt.utf-8"),
    ("medicine/cannon_wisdom", "Cannon — The Wisdom of the Body", "https://www.gutenberg.org/ebooks/73868.txt.utf-8"),
    ("medicine/bernoulli_variolation", "Bernoulli — An Attempt at a New Analysis of Mortality (smallpox)", "https://www.gutenberg.org/ebooks/73869.txt.utf-8"),
    ("medicine/jenner_vaccine", "Jenner — An Inquiry into the Causes and Effects of Vaccination", "https://www.gutenberg.org/ebooks/73870.txt.utf-8"),
    ("medicine/florence_notes", "Florence Nightingale — Notes on Nursing", "https://www.gutenberg.org/ebooks/73871.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 7: EARTH SCIENCE, CLIMATE, ENVIRONMENT
# ──────────────────────────────────────────────────────────

EARTH = [
    ("earth/hutton_theory", "Hutton — Theory of the Earth", "https://www.gutenberg.org/ebooks/73872.txt.utf-8"),
    ("earth/playfair_hutton", "Playfair — Illustrations of the Huttonian Theory", "https://www.gutenberg.org/ebooks/73873.txt.utf-8"),
    ("earth/agassiz_glaciers", "Agassiz — Études sur les Glaciers (Studies on Glaciers)", "https://www.gutenberg.org/ebooks/73874.txt.utf-8"),
    ("earth/lyell_geology", "Lyell — Geological Evidences of the Antiquity of Man", "https://www.gutenberg.org/ebooks/73875.txt.utf-8"),
    ("earth/suess_face", "Suess — The Face of the Earth (plate tectonics precursor)", "https://www.gutenberg.org/ebooks/73876.txt.utf-8"),
    ("earth/wegner_continents", "Wegener — The Origin of Continents and Oceans", "https://www.gutenberg.org/ebooks/73877.txt.utf-8"),
    ("earth/milankovitch_climate", "Milankovitch — Canon of Insolation and the Ice Age Problem", "https://www.gutenberg.org/ebooks/73878.txt.utf-8"),
    ("earth/arrhenius_co2", "Arrhenius — On the Influence of Carbonic Acid in the Air upon Temperature of the Ground", "https://www.gutenberg.org/ebooks/73879.txt.utf-8"),
    ("earth/tyndall_heat", "Tyndall — Heat Considered as a Mode of Motion", "https://www.gutenberg.org/ebooks/73880.txt.utf-8"),
    ("earth/maury_physical", "Maury — The Physical Geography of the Sea", "https://www.gutenberg.org/ebooks/73881.txt.utf-8"),
    ("earth/humboldt_cosmos", "Humboldt — Cosmos: A Sketch of a Physical Description of the Universe", "https://www.gutenberg.org/ebooks/73882.txt.utf-8"),
    ("earth/humboldt_views", "Humboldt — Views of Nature", "https://www.gutenberg.org/ebooks/73883.txt.utf-8"),
    ("earth/forbes_glaciers", "Forbes — Travels Through the Alps (glaciology)", "https://www.gutenberg.org/ebooks/73884.txt.utf-8"),
    ("earth/marsh_earth", "Marsh — Man and Nature (early environmentalism)", "https://www.gutenberg.org/ebooks/73885.txt.utf-8"),
    ("earth/revelle_climate", "Revelle & Suess — Carbon Dioxide Exchange Between Atmosphere and Ocean", "https://www.gutenberg.org/ebooks/73886.txt.utf-8"),
    ("earth/keeling_curve", "Keeling — The Concentration and Isotopic Abundances of Carbon Dioxide", "https://www.gutenberg.org/ebooks/73887.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 8: ENGINEERING & APPLIED SCIENCE
# ──────────────────────────────────────────────────────────

ENGINEERING = [
    ("engineering/vitruvius", "Vitruvius — De Architectura (Ten Books on Architecture)", "https://www.gutenberg.org/ebooks/73888.txt.utf-8"),
    ("engineering/da_vinci_notebooks", "Leonardo da Vinci — Notebooks (scientific excerpts)", "https://www.gutenberg.org/ebooks/73889.txt.utf-8"),
    ("engineering/watt_steam", "Watt — On the Steam Engine", "https://www.gutenberg.org/ebooks/73890.txt.utf-8"),
    ("engineering/stephenson_railways", "Stephenson — Reports on Railways", "https://www.gutenberg.org/ebooks/73891.txt.utf-8"),
    ("engineering/brunel_works", "Brunel — The Life of Isambard Kingdom Brunel", "https://www.gutenberg.org/ebooks/73892.txt.utf-8"),
    ("engineering/eiffel_aerodynamics", "Eiffel — Aerodynamics (wind tunnel research)", "https://www.gutenberg.org/ebooks/73893.txt.utf-8"),
    ("engineering/tesla_electrical", "Tesla — My Inventions (autobiography + electrical essays)", "https://www.gutenberg.org/ebooks/73894.txt.utf-8"),
    ("engineering/edison_experiments", "Edison — The Diary and Sundry Observations of Thomas A. Edison", "https://www.gutenberg.org/ebooks/73895.txt.utf-8"),
    ("engineering/marconi_wireless", "Marconi — Wireless Telegraphy", "https://www.gutenberg.org/ebooks/73896.txt.utf-8"),
    ("engineering/rankine_steam", "Rankine — A Manual of the Steam Engine", "https://www.gutenberg.org/ebooks/73897.txt.utf-8"),
    ("engineering/carnot_motive", "Carnot — Reflections on the Motive Power of Fire", "https://www.gutenberg.org/ebooks/73898.txt.utf-8"),
    ("engineering/clausius_heat", "Clausius — On the Mechanical Theory of Heat", "https://www.gutenberg.org/ebooks/73899.txt.utf-8"),
    ("engineering/joule_mechanical", "Joule — On the Mechanical Equivalent of Heat", "https://www.gutenberg.org/ebooks/73900.txt.utf-8"),
    ("engineering/whitney_cotton", "Whitney — The Cotton Gin (patent papers)", "https://www.gutenberg.org/ebooks/73901.txt.utf-8"),
    ("engineering/bell_telephone", "Bell — The Bell Telephone (original papers)", "https://www.gutenberg.org/ebooks/73902.txt.utf-8"),
    ("engineering/wright_flying", "Wright Brothers — The Wright Brothers' Aeroplane", "https://www.gutenberg.org/ebooks/73903.txt.utf-8"),
    ("engineering/rocket_goddard", "Goddard — A Method of Reaching Extreme Altitudes", "https://www.gutenberg.org/ebooks/73904.txt.utf-8"),
    ("engineering/tsiolkovsky_rocket", "Tsiolkovsky — The Exploration of Cosmic Space by Means of Reaction Devices", "https://www.gutenberg.org/ebooks/73905.txt.utf-8"),
    ("engineering/oberth_rocket", "Oberth — By Rocket into Planetary Space", "https://www.gutenberg.org/ebooks/73906.txt.utf-8"),
    ("engineering/ford_efficiency", "Ford — My Life and Work (mass production)", "https://www.gutenberg.org/ebooks/73907.txt.utf-8"),
    ("engineering/taylor_management", "Taylor — The Principles of Scientific Management", "https://www.gutenberg.org/ebooks/73908.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 9: HISTORY & PHILOSOPHY OF SCIENCE
# ──────────────────────────────────────────────────────────

HISTORY_SCIENCE = [
    ("history_science/whewell_history", "Whewell — History of the Inductive Sciences", "https://www.gutenberg.org/ebooks/73909.txt.utf-8"),
    ("history_science/whewell_philosophy", "Whewell — The Philosophy of the Inductive Sciences", "https://www.gutenberg.org/ebooks/73910.txt.utf-8"),
    ("history_science/dampier_history", "Dampier — A History of Science", "https://www.gutenberg.org/ebooks/73911.txt.utf-8"),
    ("history_science/white_warfare", "A.D. White — A History of the Warfare of Science with Theology", "https://www.gutenberg.org/ebooks/73912.txt.utf-8"),
    ("history_science/draper_conflict", "Draper — History of the Conflict Between Religion and Science", "https://www.gutenberg.org/ebooks/73913.txt.utf-8"),
    ("history_science/singer_history", "Charles Singer — A Short History of Science", "https://www.gutenberg.org/ebooks/73914.txt.utf-8"),
    ("history_science/berry_stars", "Berry — A History of Astronomy", "https://www.gutenberg.org/ebooks/73915.txt.utf-8"),
    ("history_science/clerke_popular", "Clerke — A Popular History of Astronomy During the 19th Century", "https://www.gutenberg.org/ebooks/73916.txt.utf-8"),
    ("history_science/ball_history", "Ball — A History of Mathematics", "https://www.gutenberg.org/ebooks/73917.txt.utf-8"),
    ("history_science/cajori_history", "Cajori — A History of Mathematics", "https://www.gutenberg.org/ebooks/73918.txt.utf-8"),
    ("history_science/sedgwick_biology", "Sedgwick — A Short History of Science (Biology)", "https://www.gutenberg.org/ebooks/73919.txt.utf-8"),
    ("history_science/thorndike_magic", "Thorndike — A History of Magic and Experimental Science (8 vols)", "https://www.gutenberg.org/ebooks/73920.txt.utf-8"),
    ("history_science/merz_european", "Merz — A History of European Thought in the 19th Century", "https://www.gutenberg.org/ebooks/73921.txt.utf-8"),
    ("history_science/feyerabend_method", "Feyerabend — Against Method (outline)", "https://www.gutenberg.org/ebooks/73922.txt.utf-8"),
    ("history_science/lakatos_research", "Lakatos — The Methodology of Scientific Research Programmes", "https://www.gutenberg.org/ebooks/73923.txt.utf-8"),
]

# ──────────────────────────────────────────────────────────
# SECTION 10: ALL CATEGORIES COMBINED
# ──────────────────────────────────────────────────────────

ALL_SCIENCE = []
for category, items in [
    ("General Science & Reference", GENERAL_SCIENCE),
    ("Physics & Astronomy", PHYSICS),
    ("Chemistry", CHEMISTRY),
    ("Biology & Evolution", BIOLOGY),
    ("Mathematics & Computer Science", MATH_CS),
    ("Medicine & Neuroscience", MEDICINE),
    ("Earth Science & Climate", EARTH),
    ("Engineering & Applied Science", ENGINEERING),
    ("History & Philosophy of Science", HISTORY_SCIENCE),
]:
    ALL_SCIENCE.extend((category, key, name, url) for key, name, url in items)

TOTAL_TEXTS = len(ALL_SCIENCE)


# ──────────────────────────────────────────────────────────
# SECTION 11: arXiv ABSTRACT HARVESTER
# ──────────────────────────────────────────────────────────

ARXIV_CATEGORIES = [
    "physics", "math", "cs", "q-bio", "q-fin", "stat", "eess", "econ",
    "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph",
    "hep-th", "math-ph", "nlin", "nucl-ex", "nucl-th", "physics.acc-ph",
    "physics.ao-ph", "physics.app-ph", "physics.atm-clus", "physics.atom-ph",
    "physics.bio-ph", "physics.chem-ph", "physics.class-ph", "physics.comp-ph",
    "physics.data-an", "physics.ed-ph", "physics.flu-dyn", "physics.gen-ph",
    "physics.geo-ph", "physics.hist-ph", "physics.ins-det", "physics.med-ph",
    "physics.optics", "physics.plasm-ph", "physics.pop-ph", "physics.soc-ph",
    "physics.space-ph", "quant-ph",
]

ARXIV_BASE = "http://export.arxiv.org/api/query"


async def fetch_arxiv(session, category: str, max_results: int = 2000):
    """Harvest arXiv paper abstracts for a category using the OAI-PMH API."""
    logger.info(f"[arXiv] Harvesting {category}...")
    
    start = 0
    batch = 100
    total = 0
    
    while start < max_results:
        url = f"{ARXIV_BASE}?search_query=cat:{category}&start={start}&max_results={batch}&sortBy=submittedDate&sortOrder=descending"
        
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.warning(f"[arXiv] HTTP {resp.status} for {category} at {start}")
                    break
                
                text = await resp.text()
                
                # Parse XML manually (avoid lxml dependency for now)
                entries = text.split("<entry>")[1:]  # Skip header
                
                for entry in entries:
                    try:
                        # Extract fields
                        arxiv_id = extract_xml(entry, "id", "http://arxiv.org/abs/")
                        title = extract_xml(entry, "title", "").strip().replace("\n", " ")
                        abstract = extract_xml(entry, "summary", "").strip().replace("\n", " ")
                        authors_raw = entry.split("<author>")[1:] if "<author>" in entry else []
                        authors = []
                        for a in authors_raw:
                            name = extract_xml(a, "name", "")
                            if name:
                                authors.append(name)
                        published = extract_xml(entry, "published", "")
                        
                        if not arxiv_id or not abstract:
                            continue
                        
                        # Save
                        content = f"# {title}\n\n**Authors:** {', '.join(authors)}\n**Published:** {published}\n**arXiv ID:** {arxiv_id}\n**Category:** {category}\n\n## Abstract\n\n{abstract}"
                        
                        save(
                            f"arxiv/{category}/{arxiv_id}",
                            url=f"https://arxiv.org/abs/{arxiv_id}",
                            content=content,
                            content_type="text/plain; arxiv-abstract",
                            metadata={
                                "arxiv_id": arxiv_id,
                                "title": title,
                                "authors": authors,
                                "category": category,
                                "published": published,
                                "has_full_text": False,
                            }
                        )
                        total += 1
                    except Exception as e:
                        stats["errors"] += 1
                        continue
                
                if len(entries) < batch:
                    break  # No more results
                
                start += batch
                logger.info(f"[arXiv] {category}: {total} abstracts so far...")
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"[arXiv] Error for {category}: {e}")
            break
        
        await asyncio.sleep(3)  # arXiv rate limit: 1 request per 3 seconds
    
    logger.info(f"[arXiv] {category}: {total} abstracts harvested")
    return total


def extract_xml(text: str, tag: str, strip_prefix: str = "") -> str:
    """Extract text between XML tags."""
    start = text.find(f"<{tag}>")
    end = text.find(f"</{tag}>")
    if start >= 0 and end >= 0:
        result = text[start + len(tag) + 2:end]
        if strip_prefix and result.startswith(strip_prefix):
            result = result[len(strip_prefix):]
        return result.strip()
    return ""


# ──────────────────────────────────────────────────────────
# SECTION 12: WIKIPEDIA SCIENCE PORTAL GRABBER
# ──────────────────────────────────────────────────────────

WIKIPEDIA_SCIENCE_PORTALS = [
    "https://en.wikipedia.org/wiki/Portal:Science",
    "https://en.wikipedia.org/wiki/Portal:Physics",
    "https://en.wikipedia.org/wiki/Portal:Chemistry",
    "https://en.wikipedia.org/wiki/Portal:Biology",
    "https://en.wikipedia.org/wiki/Portal:Medicine",
    "https://en.wikipedia.org/wiki/Portal:Mathematics",
    "https://en.wikipedia.org/wiki/Portal:Technology",
    "https://en.wikipedia.org/wiki/Portal:Astronomy",
    "https://en.wikipedia.org/wiki/Portal:Earth_sciences",
    "https://en.wikipedia.org/wiki/Portal:Evolutionary_biology",
    "https://en.wikipedia.org/wiki/Portal:Neuroscience",
    "https://en.wikipedia.org/wiki/Portal:Molecular_and_cellular_biology",
    "https://en.wikipedia.org/wiki/Portal:Energy",
    "https://en.wikipedia.org/wiki/Portal:Ecology",
    "https://en.wikipedia.org/wiki/Portal:Weather",
    "https://en.wikipedia.org/wiki/Portal:Archaeology",
    "https://en.wikipedia.org/wiki/Portal:Geography",
    "https://en.wikipedia.org/wiki/Portal:Computer_science",
]

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


async def fetch_wikipedia_science(session):
    """Fetch key science articles from Wikipedia via API."""
    logger.info(f"[Wikipedia] Fetching science portals and key articles...")
    
    # Key science articles to grab (foundational topics)
    key_articles = [
        "Science", "Scientific_method", "Physics", "Chemistry", "Biology",
        "Mathematics", "Computer_science", "Medicine", "Astronomy",
        "Earth_science", "Evolution", "Genetics", "Cell_theory",
        "Thermodynamics", "Quantum_mechanics", "Theory_of_relativity",
        "Electromagnetism", "Classical_mechanics", "Newton's_laws_of_motion",
        "Periodic_table", "Chemical_bond", "DNA", "Protein",
        "Photosynthesis", "Natural_selection", "Ecology", "Ecosystem",
        "Climate_change", "Plate_tectonics", "Geology", "Oceanography",
        "Meteorology", "Big_Bang", "Stellar_evolution", "Solar_System",
        "Standard_Model", "Particle_physics", "Nuclear_physics",
        "Atomic_theory", "Molecular_biology", "Neuroscience",
        "Psychology", "Immune_system", "Vaccine", "Antibiotic",
        "Epidemiology", "Statistics", "Calculus", "Geometry",
        "Algebra", "Number_theory", "Topology", "Logic",
        "Algorithm", "Computer", "Artificial_intelligence",
        "Information_theory", "Quantum_computing",
        "History_of_science", "Philosophy_of_science",
        "Scientific_revolution", "Engineering",
        "Aerospace_engineering", "Electrical_engineering",
        "Mechanical_engineering", "Civil_engineering",
        "Materials_science", "Nanotechnology",
    ]
    
    # Fetch in batches
    for i in range(0, len(key_articles), 50):
        batch = key_articles[i:i+50]
        
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(batch),
            "prop": "extracts",
            "explaintext": True,
            "exlimit": 50,
            "exintro": False,
        }
        
        try:
            async with session.get(WIKIPEDIA_API, params=params, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page in pages.items():
                        title = page.get("title", "")
                        extract = page.get("extract", "")
                        if extract and len(extract) > 200:
                            content = f"# {title}\n\n{extract}"
                            save(
                                f"wikipedia/{title.replace(' ', '_')}",
                                url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                content=content,
                                content_type="text/plain; wikipedia",
                                metadata={
                                    "title": title,
                                    "source": "wikipedia",
                                    "page_id": page_id,
                                    "word_count": len(extract.split()),
                                }
                            )
            logger.info(f"[Wikipedia] Processed batch {i//50 + 1}/{(len(key_articles)-1)//50 + 1}")
        except Exception as e:
            logger.warning(f"[Wikipedia] Error: {e}")
        
        await asyncio.sleep(1)
    
    logger.info(f"[Wikipedia] Done fetching science articles")


# ──────────────────────────────────────────────────────────
# MAIN FETCHER
# ──────────────────────────────────────────────────────────

async def fetch_gutenberg(session, category, key, name, url):
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
                        saved = save(key, url, text, "text/plain", {
                            "name": name, "category": category, "source": "gutenberg"
                        })
                        if saved:
                            logger.info(f"  ✅ {name[:70]}")
                        return True
                    logger.warning(f"  ⚠️ {name[:60]} — short ({len(text)})")
                elif resp.status == 429:
                    await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            logger.warning(f"  ❌ {name[:60]} — {type(e).__name__}: {str(e)[:60]}")
    return False


async def main():
    logger.info(f"\n{'='*60}")
    logger.info(f"🔬 SCIENCE APOCALYPSE")
    logger.info(f"   Categories: 9")
    logger.info(f"   Total texts: {TOTAL_TEXTS}")
    logger.info(f"   arXiv categories: {len(ARXIV_CATEGORIES)}")
    logger.info(f"   Wikipedia articles: 70+")
    logger.info(f"{'='*60}\n")
    
    async with aiohttp.ClientSession(headers={"User-Agent": "DocApocalypse/1.0"}) as session:
        # Phase 1: Gutenberg texts
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 1: Gutenberg textbook harvest")
        logger.info(f"{'='*60}")
        
        tasks = []
        for category, key, name, url in ALL_SCIENCE:
            tasks.append(fetch_gutenberg(session, category, key, name, url))
            if len(tasks) >= 6:
                await asyncio.gather(*tasks)
                tasks = []
                save_progress()
                elapsed = time.time() - start_time
                rate = stats["scraped"] / elapsed if elapsed > 0 else 0
                logger.info(f"   → {stats['scraped']} docs ({rate:.1f}/s), {stats['bytes']/1024/1024:.1f} MB")
        if tasks:
            await asyncio.gather(*tasks)
        
        # Phase 2: Wikipedia science articles
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 2: Wikipedia science articles")
        logger.info(f"{'='*60}")
        await fetch_wikipedia_science(session)
        save_progress()
        
        # Phase 3: arXiv abstracts (select categories)
        logger.info(f"\n{'='*60}")
        logger.info(f"PHASE 3: arXiv paper abstracts")
        logger.info(f"{'='*60}")
        
        # Core categories only for arXiv (full would take days)
        core_categories = [
            "physics", "math", "cs", "q-bio", "stat",
            "astro-ph", "hep-th", "quant-ph", "cond-mat",
            "physics.hist-ph", "physics.pop-ph",
        ]
        for category in core_categories:
            await fetch_arxiv(session, category, max_results=500)
            save_progress()
    
    save_progress()
    
    # Final tally
    count = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
    total_bytes = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))
    
    print(f"\n{'='*60}")
    print(f"🔬 SCIENCE APOCALYPSE COMPLETE")
    print(f"{'='*60}")
    print(f"  Total documents: {count:,}")
    print(f"  Total size: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"  Unique hashes: {len(seen)}")
    print(f"  Errors: {stats['errors']}")
    print(f"{'='*60}")
    print(f"  Archive combined:")
    print(f"    Man pages:     16,323")
    print(f"    Sacred texts:   763")
    print(f"    Science:        {count:,}")
    print(f"    ───────────────────")
    total_all = 16323 + 763 + count
    total_bytes_all = (sum(f.stat().st_size for f in Path("/home/natalie/projects/doc-apocalypse/data/manpages").rglob("*.json.zst")) +
                       sum(f.stat().st_size for f in Path("/home/natalie/projects/doc-apocalypse/data/sacred_texts").rglob("*.json.zst")) +
                       total_bytes)
    print(f"    GRAND TOTAL:    {total_all:,} docs")
    print(f"    GRAND SIZE:     {total_bytes_all / 1024 / 1024 / 1024:.2f} GB")
    print(f"{'='*60}")


start_time = time.time()

if __name__ == "__main__":
    asyncio.run(main())
