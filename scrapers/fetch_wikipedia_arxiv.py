#!/usr/bin/env python3
"""
Fetch Wikipedia science articles and arXiv abstracts.
Run after science_apocalypse.py to add the remaining content.
"""

import hashlib, json, time, urllib.request, zstandard, re
from pathlib import Path

OUTPUT = Path("/home/natalie/projects/doc-apocalypse/data/science")
OUTPUT.mkdir(parents=True, exist_ok=True)
seen_file = OUTPUT / ".seen_hashes.json"

seen = set()
if seen_file.exists():
    with open(seen_file) as f:
        seen = set(json.load(f))

print(f"Loaded {len(seen)} seen hashes")


def save(key, url, content, meta):
    sha = hashlib.sha256(content.encode()).hexdigest()
    if sha in seen:
        return False
    seen.add(sha)
    doc = {
        "sha256": sha, "source": key, "url": url,
        "content_type": "text/plain", "content": content,
        "content_length": len(content),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "metadata": meta,
    }
    compressed = zstandard.ZstdCompressor(level=3).compress(
        json.dumps(doc, ensure_ascii=False).encode()
    )
    d = OUTPUT / time.strftime("%Y-%m-%d")
    d.mkdir(exist_ok=True)
    with open(d / f"{sha[:16]}.json.zst", "wb") as f:
        f.write(compressed)
    return True


# ── PHASE 1: WIKIPEDIA SCIENCE ARTICLES ──

articles = [
    "Science", "Scientific_method", "Physics", "Chemistry", "Biology",
    "Mathematics", "Computer_science", "Medicine", "Astronomy",
    "Earth_science", "Evolution", "Genetics", "Cell_theory",
    "Thermodynamics", "Quantum_mechanics", "Theory_of_relativity",
    "Electromagnetism", "Classical_mechanics", "Newton%27s_laws_of_motion",
    "Periodic_table", "DNA", "Protein", "Natural_selection",
    "Ecology", "Climate_change", "Plate_tectonics", "Geology",
    "Oceanography", "Meteorology", "Big_Bang", "Stellar_evolution",
    "Solar_System", "Standard_Model", "Particle_physics",
    "Nuclear_physics", "Atomic_theory", "Molecular_biology",
    "Neuroscience", "Immune_system", "Vaccine", "Antibiotic",
    "Statistics", "Calculus", "Geometry", "Algebra", "Number_theory",
    "Topology", "Logic", "Algorithm", "Artificial_intelligence",
    "Information_theory", "Quantum_computing", "History_of_science",
    "Philosophy_of_science", "Scientific_revolution", "Engineering",
    "Electrical_engineering", "Mechanical_engineering",
    "Civil_engineering", "Materials_science", "Nanotechnology",
    "Evolutionary_biology", "Biochemistry", "Cell_biology",
    "Astrobiology", "Cosmology", "Astrophysics",
    "Condensed_matter_physics", "Optics", "Acoustics",
    "Organic_chemistry", "Inorganic_chemistry",
    "Genomics", "Proteomics", "Bioinformatics",
    "Epidemiology", "Pharmacology", "Toxicology",
    "Botany", "Zoology", "Microbiology", "Virology",
    "Psychology", "Psychiatry", "Neurology",
    "Radiology", "Cardiology", "Oncology",
    "Conservation_biology", "Marine_biology",
    "Paleontology", "Anthropology", "Archaeology",
    "Soil_science", "Hydrology", "Climatology",
    "Mineralogy", "Volcanology",
    "Aerospace_engineering", "Chemical_engineering",
    "Nuclear_engineering", "Biomedical_engineering",
    "Environmental_engineering", "Computer_engineering",
    "Robotics", "Telecommunications", "Semiconductors",
    "Relativity", "Spacetime", "Black_hole", "Supernova",
    "Galaxy", "Nebula", "Exoplanet", "Dark_matter", "Dark_energy",
    "Cognitiuscience", "Sleep", "Memory", "Learning",
    "Enzyme", "Metabolism", "Homeostasis", "Hormone",
    "Stem_cell", "Gene_therapy", "CRISPR", "Epigenetics",
    "Vaccination", "Herd_immunity", "Pandemic", "Zoonosis",
]

api = "https://en.wikipedia.org/w/api.php"
count = 0

print(f"\n{'='*60}")
print(f"PHASE 1: Wikipedia Science Articles")
print(f"{'='*60}")

for i in range(0, len(articles), 50):
    batch = articles[i:i+50]
    titles = "|".join(batch)
    url = f"{api}?action=query&format=json&titles={titles}&prop=extracts&explaintext=1&exlimit=50"
    
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "DocApocalypse/1.0")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        
        pages = data.get("query", {}).get("pages", {})
        batch_count = 0
        for pid, page in pages.items():
            title = page.get("title", "")
            extract = page.get("extract", "")
            if extract and len(extract) > 200:
                content = f"# {title}\n\n{extract}"
                meta = {"title": title, "source": "wikipedia", "word_count": len(extract.split())}
                if save(f"wikipedia/{title.replace(' ', '_')}", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}", content, meta):
                    count += 1
                    batch_count += 1
        
        print(f"  Batch {i//50 + 1}/{(len(articles)-1)//50 + 1}: +{batch_count} articles (total: {count})")
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(0.5)

print(f"\n✅ Wikipedia: {count} articles saved")

# Save progress
with open(seen_file, "w") as f:
    json.dump(list(seen), f)

# ── PHASE 2: ARXIV ABSTRACT HARVEST ──

print(f"\n{'='*60}")
print(f"PHASE 2: arXiv Abstracts (via OAI-PMH)")
print(f"{'='*60}")

arxiv_categories = [
    ("physics", "physics:general"),
    ("math", "math"),
    ("cs", "cs"),
    ("q-bio", "q-bio"),
    ("stat", "stat"),
    ("astro-ph", "astro-ph"),
    ("hep-th", "hep-th"),
    ("quant-ph", "quant-ph"),
    ("cond-mat", "cond-mat"),
    ("physics.hist-ph", "physics.hist-ph"),
    ("physics.pop-ph", "physics.pop-ph"),
]

arxiv_total = 0

for cat_code, cat_name in arxiv_categories:
    try:
        # Use OAI-PMH to get recent papers
        oai_url = f"http://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=arXiv&set={cat_code}"
        
        req = urllib.request.Request(oai_url)
        req.add_header("User-Agent", "DocApocalypse/1.0")
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8", errors="replace")
            
            # Extract paper IDs and titles
            ids = re.findall(r'<id>http://arxiv.org/abs/(.+?)</id>', data)
            titles = re.findall(r'<title>(.+?)</title>', data)
            abstracts = re.findall(r'<abstract>(.+?)</abstract>', data, re.DOTALL)
            
            cat_count = 0
            for j, (arxiv_id, title_text) in enumerate(zip(ids, titles)):
                if j >= 100:  # Limit per category
                    break
                abstract = abstracts[j] if j < len(abstracts) else ""
                abstract = abstract.strip().replace("\n", " ").replace("  ", " ")
                title_text = title_text.strip().replace("\n", " ").replace("  ", " ")
                
                if abstract:
                    content = f"# {title_text}\n\n## Abstract\n\n{abstract}"
                    meta = {
                        "arxiv_id": arxiv_id, "title": title_text,
                        "category": cat_code, "source": "arxiv",
                    }
                    if save(f"arxiv/{cat_code}/{arxiv_id}", f"https://arxiv.org/abs/{arxiv_id}", content, meta):
                        cat_count += 1
            
            arxiv_total += cat_count
            print(f"  {cat_code}: +{cat_count} abstracts (total: {arxiv_total})")
            
        except Exception as e:
            print(f"  {cat_code}: Error - {e}")
    
    except Exception as e:
        print(f"  {cat_code}: Connection error - {e}")
    
    time.sleep(5)  # arXiv rate limit

print(f"\n✅ arXiv: {arxiv_total} abstracts saved")

# ── FINAL ──
with open(seen_file, "w") as f:
    json.dump(list(seen), f)

total = sum(1 for _ in OUTPUT.rglob("*.json.zst"))
total_bytes = sum(f.stat().st_size for f in OUTPUT.rglob("*.json.zst"))

print(f"\n{'='*60}")
print(f"SCIENCE HARVEST COMPLETE")
print(f"{'='*60}")
print(f"Total in science/: {total} docs")
print(f"Total size: {total_bytes/1024/1024:.1f} MB")
print(f"Unique hashes: {len(seen)}")
print(f"{'='*60}")
