#!/bin/bash
# Doc-Apocalypse Reader Launcher
# Usage: ./launch_reader.sh [--search "query"]

cd "$(dirname "$0")"

if [ "$1" = "--search" ]; then
    python3 reader.py --search "$2"
elif [ "$1" = "--stats" ]; then
    python3 reader.py --search "" | head -5
    python3 -c "
import json
from pathlib import Path
index = Path('/home/natalie/projects/doc-apocalypse/indexes/doc_apocalypse_index.json')
if index.exists():
    with open(index) as f:
        data = json.load(f)
    docs = data.get('docs', [])
    sections = {}
    for d in docs:
        s = d.get('section', 'unknown')
        sections[s] = sections.get(s, 0) + 1
    print(f'📊 Archive: {len(docs):,} documents')
    for s, c in sorted(sections.items()):
        print(f'   {s}: {c:,}')
"
else
    python3 reader.py
fi
