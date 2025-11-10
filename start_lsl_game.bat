@echo off
REM Launch script for Raspberry Pi (Game mode) - Windows version
REM Connects to LSL stream and sends attention scores to the game

echo 🎮 Starting LSL Subscriber for Game
echo ====================================

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the subscriber in game mode
python lsl_subscriber.py --mode game --stream-name "OpenBCI_EEG" --game-port 5005

pause

