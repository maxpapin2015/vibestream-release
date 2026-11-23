#!/usr/bin/env bash
set -e
echo "========================================================"
echo "  VibeStream - Spotify-Style Desktop Music Player"
echo "========================================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed. Please install Python 3.10+."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "[2/3] Installing dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

echo "[3/3] Starting VibeStream..."
python3 main.py
