<img width="2240" height="1260" alt="NeuroHue-2" src="https://github.com/user-attachments/assets/a310344a-5915-4306-8943-936a1f1ed88a" />

# EEG Car Race Game

A simple browser-based car race controlled entirely by EEG focus (beta waves) using OpenBCI and BrainFlow.

## Features

- **Simple Linear Race**: Car moves forward based on EEG focus
- **Timed Competition**: Race against the clock and compete for fastest time
- **Real-time Feedback**: Live focus bar, threshold display, and attention tracker graph
- **Calibration**: Quick calibration screen to set your personal focus threshold
- **Leaderboard**: Track fastest race times and focus streaks
- **Demo Mode**: Works with synthetic EEG data if hardware is unavailable

## How to run

```bash
Launch the server
python focus_server.py --board-type Ganglion --serial-port COM3
```
Run the game:
```bash
python focus.py
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

## Future
- ML-based focus detection: Train a classifier to recognize focus vs. distraction patterns
- Multiplayer races: Compete head-to-head via networked EEG streams
- Expanded frequency bands: Track alpha/theta for relaxation or meditation
- Advanced analytics: Historical focus tracking and personalized feedback
- Enhanced visuals: Unity or WebGL for immersive gameplay
- Integration: Combine with VR or color accessibility applications

## Contributors
- Jordan Kwan
- Jinn Kasai
- Eric Kane
- Juan Rea
- Dam Dung Nguyen Mong
- Dam Hanh Nguyen Mong


## Project Links
- Devpost
- Slide Deck
- Demo Video

## Extra Materials 
(Video Link)
