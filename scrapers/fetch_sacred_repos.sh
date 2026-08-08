#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║        Sacred Text Repo Cloner                              ║
# ║  Clones religious text repos locally using gh                ║
# ║  Then ingest into the doc-apocalypse format                  ║
# ╚══════════════════════════════════════════════════════════════╝

set -e
REPO_DIR="/tmp/sacred_repos"
OUTPUT_DIR="/home/natalie/projects/doc-apocalypse/data/sacred_texts"
mkdir -p "$REPO_DIR" "$OUTPUT_DIR"

echo "📖 Cloning sacred text repositories..."

# ── BIBLE ──────────────────────────────────────────────────
echo ""
echo "=== BIBLE ==="

# KJV
if [ ! -d "$REPO_DIR/Bible-kjv" ]; then
    echo "Cloning KJV Bible..."
    gh repo clone aruljohn/Bible-kjv "$REPO_DIR/Bible-kjv" -- --depth=1
fi

# NIV
if [ ! -d "$REPO_DIR/Bible-niv" ]; then
    echo "Cloning NIV Bible..."
    gh repo clone aruljohn/Bible-niv "$REPO_DIR/Bible-niv" -- --depth=1
fi

# Spanish
if [ ! -d "$REPO_DIR/Reina-Valera" ]; then
    echo "Cloning Reina-Valera (Spanish Bible)..."
    gh repo clone aruljohn/Reina-Valera "$REPO_DIR/Reina-Valera" -- --depth=1
fi

# Hebrew Bible
if [ ! -d "$REPO_DIR/hebrewBibleJSON" ]; then
    echo "Cloning Hebrew Bible..."
    gh repo clone talolard/hebrewBibleJSON "$REPO_DIR/hebrewBibleJSON" -- --depth=1
fi

# ── QURAN ──────────────────────────────────────────────────
echo ""
echo "=== QURAN ==="

# Use the CDN version since the repo is large
if [ ! -d "$REPO_DIR/quran-json" ]; then
    echo "Downloading Quran JSON from CDN..."
    mkdir -p "$REPO_DIR/quran-json"
    # fawazahmed0's API
    for lang in ar en.ahmedali en.arberry en.hilali en.pickthall en.sahih en.yusufali en.shakir en.maududi en.daryabadi en.khan en.maududi; do
        echo "  Downloading $lang..."
        curl -sL "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/$lang.json" -o "$REPO_DIR/quran-json/$lang.json" &
    done
    wait
fi

# ── MORMON ─────────────────────────────────────────────────
echo ""
echo "=== MORMON ==="

# Book of Mormon + D&C + Pearl of Great Price - use Gutenberg (already handled by the Python scraper)

# ── SEFARIA (Jewish texts) ─────────────────────────────────
echo ""
echo "=== JEWISH TEXTS ==="

# Sefaria has a massive export, let's just grab a few tractates
if [ ! -d "$REPO_DIR/sefaria-export" ]; then
    echo "Sefaria export repo is huge - skipping full clone"
    echo "Using Gutenberg fallbacks instead"
fi

# ── BUDDHIST ───────────────────────────────────────────────
echo ""
echo "=== BUDDHIST TEXTS ==="

# SuttaCentral data
if [ ! -d "$REPO_DIR/sc-data" ]; then
    echo "SuttaCentral data is huge - skipping full clone"
    echo "Using SuttaCentral API instead"
fi

# ── HINDU ──────────────────────────────────────────────────
echo ""
echo "=== HINDU TEXTS ==="

# Vedas, Puranas
if [ ! -d "$REPO_DIR/vedic-json" ]; then
    mkdir -p "$REPO_DIR/vedic-json"
    for text in rigveda yajurveda samaveda atharvaveda upanishads puranas bhagavad-gita; do
        echo "  Downloading $text..."
        curl -sL "https://raw.githubusercontent.com/svenkatreddy/lal_kitab/main/$text.json" -o "$REPO_DIR/vedic-json/$text.json" &
    done
    wait
fi

echo ""
echo "✅ Cloning complete!"
echo "Repos in: $REPO_DIR"
ls -la "$REPO_DIR"/*/
