# EEG Car Race Game

A simple browser-based car race controlled entirely by EEG focus (beta waves) using OpenBCI and BrainFlow.

## Features

- **Simple Linear Race**: Car moves forward based on EEG focus
- **Timed Competition**: Race against the clock and compete for fastest time
- **Real-time Feedback**: Live focus bar, threshold display, and attention tracker graph
- **Calibration**: Quick calibration screen to set your personal focus threshold
- **Leaderboard**: Track fastest race times and focus streaks
- **Demo Mode**: Works with synthetic EEG data if hardware is unavailable

## Installation

```bash
pip install -r requirements.txt
```

For OpenBCI hardware support:
```bash
pip install brainflow
```

## Usage

Run the game:
```bash
streamlit run app.py
```

### Demo Mode
If no hardware is connected, the app automatically uses demo mode with synthetic EEG data.

### Hardware Mode
1. Connect your OpenBCI device (Cyton, Ganglion, etc.)
2. Click "Connect to OpenBCI" in the sidebar
3. Calibrate your focus threshold
4. Start racing!

## How It Works

- **Beta Waves (13-30 Hz)**: Indicate focus/concentration
- **Movement**: Car moves forward when focus exceeds threshold
- **Speed**: Higher focus = faster movement
- **Goal**: Complete the race in the fastest time possible
- **Competition**: Leaderboard tracks your best times

## Gameplay

1. **Calibrate**: Focus for 10 seconds to set your threshold
2. **Race**: Maintain high focus to move faster
3. **Finish**: Complete the race as fast as possible
4. **Compete**: Check the leaderboard for your rank