#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║              Doc-Apocalypse Runner Script                    ║
# ║  Usage:                                                      ║
# ║    ./run.sh                     # Run everything             ║
# ║    ./run.sh --github            # GitHub only               ║
# ║    ./run.sh --manpages          # Man pages only             ║
# ║    ./run.sh --corporate         # Corporate docs only        ║
# ║    ./run.sh --gitlab            # GitLab only                ║
# ║    ./run.sh --index             # Build search index         ║
# ║    ./run.sh --stats             # Show stats                 ║
# ║    ./run.sh --dry-run           # Preview what will happen   ║
# ║    ./run.sh --install-pkgfile   # Install pkgfile for man    ║
# ╚══════════════════════════════════════════════════════════════╝

set -e
cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║            DOC-APOCALYPSE — RUNNER                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

python3 apocalypse.py "$@"
