<img width="2240" height="1260" alt="NeuroHue-2" src="https://github.com/user-attachments/assets/0b510d1e-ec80-4c5d-80fc-f7df83fd7ced" />

# NeuroDash: EEG-Powered Focus Racing Game

**NeuroDash** is a neurofeedback game that transforms attention training into an engaging racing experience.  
Built with **OpenBCI Ganglion**, **Pygame**, and **Streamlit**, the system lets players control a car using their brainwaves — while clinicians or researchers can monitor focus levels in real time through a separate dashboard.

---

## Features

### For Players
- **EEG-Controlled Gameplay**: Car speed directly tied to real-time focus level  
- **Engaging Visual Feedback**: Focus bar dynamically reflects concentration intensity  
- **Accessible Mode**: Mock EEG data available for testing without hardware  
- **Gamified Focus Training**: Improve attention while having fun  

### For Clinicians / Researchers
- **Real-Time Dashboard** (Streamlit) showing:
  - Live focus intensity graph  
  - Beta/Alpha ratio trends  
  - Player session metrics and status  
- **Dual-UI Architecture**: Game and dashboard run simultaneously, sharing data from the same backend

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
- Streamlit — Focus visualization dashboard for clinicians  

**Backend**
- Python + Socket Communication — Real-time data streaming between EEG, dashboard, and game  
- NumPy + SciPy — Signal processing and focus computation  
- Mock EEG Generator — Enables testing without hardware  

**Hardware**
- OpenBCI Ganglion Board — 4-channel EEG acquisition system

**Focus Detection Model**
- Model: EEGNet4Ch — a 4-channel EEG convolutional neural network
- Purpose: Predicts focus level from raw EEG input instead of using a static beta power threshold
- Input: 4 EEG channels × 250 timepoints (1 second of EEG at 250 Hz)
- Output: Probability of being focused (0.0–1.0)
- Training Data: Labeled EEG recordings with focus / not focus annotations
- Notebook: [EEG_training.ipynb](https://colab.research.google.com/drive/1J6ctrXqC9HnhXXJIPyBqc42KmniFzq7O?usp=sharing) contains model training, evaluation metrics, and visualizations
- Weights: [focus_eegnet_4ch.pth](https://github.com/9juanjuan7/neuro-dash/blob/main/focus_eegnet_4ch.pth) — pre-trained model for inference

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
streamlit run dashboard.py
```
## Team
- Jordan Kwan
- Jinn Kasai
- Eric Kane
- Juan Rea
- Dam Dung Nguyen Mong
- Dam Hanh Nguyen Mong

## Project Links
- [Devpost](https://devpost.com/software/neurodrive-awgdio)
- [Slide Deck](https://docs.google.com/presentation/d/1OVRy0oJ0sTellEWwlVn00hihXx4xbdlLNEIf56y-2qI/edit?usp=sharing)
- Demo Video

## References
- Lawhern VJ, Solon AJ, Waytowich NR, Gordon SM, Hung CP, Lance BJ. EEGNet: a compact convolutional neural network for EEG-based brain-computer interfaces. J Neural Eng. 2018 Oct;15(5):056013. doi: 10.1088/1741-2552/aace8c. Epub 2018 Jun 22. PMID: 29932424. [EEGNet](https://github.com/aliasvishnu/EEGNet)
