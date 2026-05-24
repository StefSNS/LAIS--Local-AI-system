#!/usr/bin/env bash
# LAIS One-Line Installer for Linux/macOS
# Run: bash <(curl -s https://raw.githubusercontent.com/StefSNS/LAIS--Local-AI-system/main/install.sh)
set -euo pipefail

REPO_URL="https://github.com/StefSNS/LAIS--Local-AI-system.git"
INSTALL_DIR="${LAIS_DIR:-$HOME/LAIS}"
QUICK=false
[[ "${1:-}" == "--quick" ]] && QUICK=true

echo ""
echo "  ============================================================"
echo "         LAIS - Local AI System  v2.0.0"
echo "         Voice AI + GUI Orchestrator + CLI Coder"
echo "  ============================================================"
echo ""

# Phase 1: Prerequisites
echo "  >>> Phase 1/5: Checking Prerequisites"
PY_VER=$(python3 --version 2>/dev/null || python --version 2>/dev/null || true)
if echo "$PY_VER" | grep -qE "3\.(1[1-9]|[2-9][0-9])"; then
    echo "  [OK] $PY_VER"
else
    echo "  [FAIL] Python 3.11+ required. Install from https://python.org"
    exit 1
fi

if command -v git &>/dev/null; then
    echo "  [OK] Git found"
else
    echo "  [FAIL] Git not found. Install with: apt install git (Linux) or brew install git (macOS)"
    exit 1
fi

# Phase 2: Download
echo "  >>> Phase 2/5: Downloading LAIS"
if [ -d "$INSTALL_DIR" ]; then
    echo "  [!] LAIS already installed at $INSTALL_DIR"
    if [ "$QUICK" = false ]; then
        read -rp "  Update existing installation? (Y/n) " resp
        if [ "$resp" = "n" ] || [ "$resp" = "N" ]; then echo "Exiting."; exit 0; fi
    fi
    cd "$INSTALL_DIR"
    git pull
    echo "  [OK] Updated to latest version"
else
    echo "  Cloning to $INSTALL_DIR ..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    echo "  [OK] Downloaded to $INSTALL_DIR"
fi

# Phase 3: Python installer
echo "  >>> Phase 3/5: Running Python Installer"
cd "$INSTALL_DIR"
if [ "$QUICK" = true ]; then
    python3 install.py --quick 2>/dev/null || python install.py --quick
else
    python3 install.py 2>/dev/null || python install.py
fi

# Phase 4: Post-install
echo "  >>> Phase 4/5: Linux Setup"
PLATFORM=$(uname -s)
if [ "$PLATFORM" = "Linux" ]; then
    echo "  [*] Linux detected — GUI features require X11/Wayland display"
    echo "  [*] Install audio: sudo apt install portaudio19-dev python3-pyaudio (Ubuntu/Debian)"
fi

# Phase 5: Summary
echo "  >>> Phase 5/5: Installation Summary"
SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1 || echo "N/A")
echo ""
echo "  Location: $INSTALL_DIR"
echo "  Size:     $SIZE"
echo ""
echo "  Next steps:"
echo "    1. cd $INSTALL_DIR"
echo "    2. Set your Gemini API key in models/Mark-XXXIX/config/api_keys.json"
echo "    3. Run agents:"
echo "       python models/Mark-XXXIX/main.py            (JARVIS voice AI)"
echo "       python models/ai_engine/main.py              (AI Engine GUI)"
echo ""
echo "  Docs:  https://github.com/StefSNS/LAIS--Local-AI-system#readme"
echo "  Repo:  $REPO_URL"
echo ""
