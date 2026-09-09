#!/usr/bin/env bash

# Exit immediately if any step fails
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 1. Automatic Python Virtual Environment Setup
if [ ! -d "venv" ]; then
    echo " ⚙ Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate the venv safely
source venv/bin/activate

# 2. Automated Dependency Integrity Check
if ! python3 -c "import pygame, pydub" 2>/dev/null; then
    echo " Checking dependencies if missing then Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# 3. Suppress all C-extension warnings and splash prompts globally
export PYGAME_DETECT_AVX2=1
export PYGAME_HIDE_SUPPORT_PROMPT=1

# 4. Auto-detect local user Music folder if no path parameter was supplied
MUSIC_TARGET="${1:-$HOME/Music}"

# 5. Launch the clean interface binary
exec python3 MusicPlayerCli.py "$MUSIC_TARGET"
