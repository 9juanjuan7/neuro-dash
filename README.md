<img width="2240" height="1260" alt="NeuroHue-2" src="https://github.com/user-attachments/assets/0b510d1e-ec80-4c5d-80fc-f7df83fd7ced" />

# NeuroDash: EEG-Powered Focus Racing Game

NeuroDash helps hospitals capture pediatric measurements faster and calmer by turning focus into a measurable, hands‑free game with a clear “ready” signal for staff. Built with OpenBCI Ganglion EEG hardware and Python/Pygame, processing real-time beta wave signals to translate brain activity into interactive gameplay.

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
- Python + LSL + UDP — LSL streams EEG data from OpenBCI GUI, UDP sockets transmit processed focus scores to game and dashboard
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

This setup uses LSL (Lab Streaming Layer) streaming for distributed operation, with the game running on a Raspberry Pi and the dashboard on a laptop. Both connect to the same LSL stream from OpenBCI GUI.

### Prerequisites

- OpenBCI Ganglion board connected to your laptop
- OpenBCI GUI installed and running
- Raspberry Pi set up with the repository (see [RASPBERRY_PI_SETUP.md](RASPBERRY_PI_SETUP.md))
- SSH access to the Raspberry Pi
- Both devices on the same network (or using Tailscale/VPN)

### Step-by-Step Setup

#### 1. Start LSL Stream from OpenBCI GUI

1. Open **OpenBCI GUI** on your laptop
2. Connect to your **Ganglion** board
3. Go to the **Networking** widget
4. Set **Output = LSL**
5. Set **Data Type = EEG** (or "Timeseries Raw")
6. Set **Stream Name = "eegstream"** (or your preferred name)
7. Click **Start LSL Stream**

#### 2. Start LSL Forwarder (Laptop)

On your laptop, run the forwarder to bridge the LSL stream to the Raspberry Pi:

```bash
python lsl_forwarder.py --pi-ip <pi-tailscale-ip> --stream-name "eegstream" --threshold 70 --mode both
```

Replace `<pi-tailscale-ip>` with your Raspberry Pi's IP address (e.g., `100.72.174.84`).

The forwarder will:

- Connect to the local LSL stream from OpenBCI GUI
- Process EEG data and compute focus scores
- Forward data to both the game (port 5005) and dashboard (port 5006) on the Pi

#### 3. Start Dashboard (Laptop)

In a new terminal on your laptop, run:

```bash
python dashboard_pygame.py --pi-ip <pi-tailscale-ip>
```

Replace `<pi-tailscale-ip>` with your Raspberry Pi's IP address.

The dashboard will:

- Receive focus data from the forwarder
- Display real-time focus metrics and history
- Allow you to control the game (Play Again, Quit)

#### 4. Start Game on Raspberry Pi

SSH into your Raspberry Pi:

```bash
ssh <pi-username>@<pi-ip-address>
```

Once connected, navigate to the project directory:

```bash
cd ~/neuro-dash
```

Then run the game:

```bash
bash start_game.sh
```

This will:

- Launch the focus racing game
- The game will receive focus data via UDP from the forwarder running on your laptop
- Display the game on the Pi's screen

**Note:** The game receives data directly from the LSL forwarder via UDP (port 5005), so no additional LSL subscriber is needed on the Pi for this setup.

### Alternative: Using Launch Scripts

**On Laptop:**

- Use `start_forwarder.bat` (Windows) or `start_forwarder.sh` (Linux/Mac) with the Pi IP as argument

**On Raspberry Pi:**

- Use `start_lsl_game.sh` to start the LSL subscriber and game
- Use `start_game.sh` if you want to run the game separately

### Troubleshooting

- **LSL stream not found**: Make sure OpenBCI GUI is running and the LSL stream is started
- **Connection issues**: Verify both devices are on the same network or using Tailscale
- **Game not receiving data**: Check that the forwarder is running and the Pi IP is correct
- **Dashboard not showing data**: Ensure the forwarder is running with `--mode both` or `--mode dashboard`
  
## Team
- Jordan Kwan
- Jinn Kasai
- Eric Kane
- Juan Rea
- Dam Dung Nguyen Mong
- Dam Hanh Nguyen Mong

## Project Links
- [Devpost](https://devpost.com/software/neurodrive-awgdio)
- [Slide Deck](https://docs.google.com/presentation/d/1OVRy0oJ0sTellEWwlVn00hihXx4xbdlLNEIf56y-2qI/edit?slide=id.g3a1a60e7b61_0_79#slide=id.g3a1a60e7b61_0_79)
- [Demo Video](https://www.youtube.com/watch?v=61n5GsGkd9s)

## References
- Lawhern VJ, Solon AJ, Waytowich NR, Gordon SM, Hung CP, Lance BJ. EEGNet: a compact convolutional neural network for EEG-based brain-computer interfaces. J Neural Eng. 2018 Oct;15(5):056013. doi: 10.1088/1741-2552/aace8c. Epub 2018 Jun 22. PMID: 29932424. [EEGNet](https://github.com/aliasvishnu/EEGNet)
