# LSL Setup Guide - Multi-Device Setup

This guide explains how to run the game on Raspberry Pi and dashboard on your laptop, both connected to the same LSL stream from OpenBCI GUI.

## Prerequisites

1. **OpenBCI GUI** running on your laptop with LSL stream started
2. **Raspberry Pi** with game installed
3. **Laptop** with dashboard installed
4. Both devices on the same network (or localhost for testing)

## Step 1: Start LSL Stream in OpenBCI GUI

1. Launch OpenBCI GUI
2. Connect to your board and start data stream
3. Open the **Networking** widget
4. Set:
   - **Output** = LSL
   - **Data Type** = EEG (or TimeSeries for raw data)
5. Click **"Start LSL Stream"**
6. Verify the stream name (usually "OpenBCI_EEG")

## Step 2: Install Dependencies

On both Raspberry Pi and Laptop:

```bash
pip install pylsl numpy scipy
```

## Step 3: Run on Raspberry Pi (Game)

On the Raspberry Pi, run:

```bash
# Linux/Raspberry Pi
bash start_lsl_game.sh

# Or directly:
python lsl_subscriber.py --mode game --stream-name "OpenBCI_EEG"
```

This will:
- Connect to the LSL stream
- Compute attention scores
- Send to the game on port 5005

Then start the game:

```bash
python focus_race.py
```

## Step 4: Run on Laptop (Dashboard)

On your laptop, run:

```bash
# Windows
start_lsl_dashboard.bat

# Linux/Mac
bash start_lsl_dashboard.sh

# Or directly:
python lsl_subscriber.py --mode dashboard --stream-name "OpenBCI_EEG"
```

This will:
- Connect to the same LSL stream
- Compute attention scores and ready flags
- Send to the dashboard on port 5006

Then start the dashboard:

```bash
python dashboard_pygame.py --pi-ip <pi-ip-address>
```

## Step 5: Verify Connection

Both subscribers should show:
- ✅ Connected to LSL stream
- Real-time attention scores
- Ready flag status

## Troubleshooting

### Stream Not Found
- Verify OpenBCI GUI is running and LSL stream is started
- Check stream name matches (default: "OpenBCI_EEG")
- Use `--stream-name` to specify custom name

### Network Issues
- For localhost: Both scripts use 127.0.0.1
- For network: Update IP addresses in scripts
- Ensure firewall allows UDP ports 5005 and 5006

### No Data
- Check OpenBCI GUI shows live data
- Verify LSL stream is actually streaming (check Networking widget)
- Try increasing timeout: `--timeout 20.0`

## Advanced Options

### Custom Stream Name
```bash
python lsl_subscriber.py --stream-name "MyCustomStream"
```

### Both Modes (for testing)
```bash
python lsl_subscriber.py --mode both
```

### Adjust Update Rate
```bash
python lsl_subscriber.py --update-rate 0.033  # ~30 Hz
```

### Custom Threshold
```bash
python lsl_subscriber.py --threshold 80.0
```

## Architecture

```
OpenBCI GUI (Laptop)
    ↓ LSL Stream
    ├─→ LSL Subscriber (Raspberry Pi) → Game (UDP 5005)
    └─→ LSL Subscriber (Laptop) → Dashboard (UDP 5006)
```

Both subscribers connect to the same LSL stream and compute attention scores independently, ensuring synchronized data.

