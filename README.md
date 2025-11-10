<img width="2240" height="1260" alt="NeuroHue-2" src="https://github.com/user-attachments/assets/0b510d1e-ec80-4c5d-80fc-f7df83fd7ced" />

# NeuroDash: EEG-Powered Focus Racing Game

**NeuroDash** is a neurofeedback game that transforms attention training into an engaging racing experience.  
Built with **OpenBCI Ganglion** and **Pygame**, the system lets players control a car using their brainwaves — while clinicians or researchers can monitor focus levels in real time through a separate dashboard.

---

## Features

### For Players
- **EEG-Controlled Gameplay**: Car speed directly tied to real-time focus level  
- **Engaging Visual Feedback**: Focus bar dynamically reflects concentration intensity  
- **Accessible Mode**: Mock EEG data available for testing without hardware  
- **Gamified Focus Training**: Improve attention while having fun  

### For Clinicians / Researchers
- **Real-Time Dashboard** (Pygame) showing:
  - Live focus intensity graph  
  - Connection status and ready state
  - Player session metrics and statistics
  - Game control buttons (Play Again, Quit)
- **Dual-UI Architecture**: Game and dashboard run simultaneously, sharing data from the same backend
- **LSL Streaming**: Support for distributed setups with game on Raspberry Pi and dashboard on laptop

---

## Gameplay Flow

- EEG / Mock Input → Data processed in backend
- Focus Calculation → Beta/Alpha ratio converted to [0–1]
- Game Update → Car speed adjusted by focus score
- Dashboard Display → Real-time focus graph + session info

---

## Tech Stack

**Frontend**
- Pygame — Interactive racing game UI for players  
- Pygame — Doctor-facing dashboard for monitoring and control  

**Backend**
- Python + Socket Communication — Real-time data streaming between EEG, dashboard, and game  
- NumPy + SciPy — Signal processing and focus computation  
- Mock EEG Generator — Enables testing without hardware  

**Hardware**
- OpenBCI Ganglion Board — 4-channel EEG acquisition system

**Focus Detection**
- Uses beta wave power analysis for real-time focus calculation
- Threshold-based approach with dynamic sensitivity adjustment
- LSL streaming support for distributed setups (game on Pi, dashboard on laptop)

---

## How to Run 🚀

### 1. Start the Focus Server (EEG or Mock Mode)
```bash
python focus_server.py
```
If OpenBCI is connected:
```bash
python focus_server.py --board-type Ganglion --serial-port COM3
```
### 2. Launch the Game (Player View)
```bash
python  focu_game.py
```
### 3. Launch the Dashboard (Clinician View)
```bash
python dashboard_pygame.py --pi-ip <pi-ip-address>
```
## Team
- Jordan Kwan
- Jinn Kasai
- Eric Kane
- Juan Rea
- Dam Dung Nguyen Mong
- Dam Hanh Nguyen Mong

## Project Links
- Devpost
- Slide Deck
- [Demo Video] (https://www.youtube.com/watch?v=61n5GsGkd9s)

## References
- Lawhern VJ, Solon AJ, Waytowich NR, Gordon SM, Hung CP, Lance BJ. EEGNet: a compact convolutional neural network for EEG-based brain-computer interfaces. J Neural Eng. 2018 Oct;15(5):056013. doi: 10.1088/1741-2552/aace8c. Epub 2018 Jun 22. PMID: 29932424. [EEGNet](https://github.com/aliasvishnu/EEGNet)
