#!/bin/bash
# Launch script for Raspberry Pi (Game mode)
# Connects to LSL stream and sends attention scores to the game

echo "🎮 Starting LSL Subscriber for Game (Raspberry Pi)"
echo "================================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the subscriber in game mode
python lsl_subscriber.py --mode game --stream-name "OpenBCI_EEG" --game-port 5005

