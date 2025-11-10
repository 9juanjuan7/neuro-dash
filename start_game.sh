#!/bin/bash
# Launch script for Raspberry Pi (Game)
# Starts the focus race game

echo "🎮 Starting Focus Race Game"
echo "============================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: bash setup_raspberry_pi.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if focus_race.py exists
if [ ! -f "focus_race.py" ]; then
    echo "❌ focus_race.py not found!"
    exit 1
fi

# Run the game
python focus_race.py

