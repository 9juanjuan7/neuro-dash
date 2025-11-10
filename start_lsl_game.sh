#!/bin/bash
# Launch script for Raspberry Pi (Game mode)
# Connects to LSL stream and sends attention scores to the game

echo "🎮 Starting LSL Subscriber for Game (Raspberry Pi)"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: bash setup_raspberry_pi.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if lsl_subscriber.py exists
if [ ! -f "lsl_subscriber.py" ]; then
    echo "❌ lsl_subscriber.py not found!"
    exit 1
fi

# Run the subscriber in game mode
python lsl_subscriber.py --mode game --stream-name "eegstream" --game-port 5005
