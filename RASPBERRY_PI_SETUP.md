# Raspberry Pi Setup Guide

This guide helps you set up the LSL subscriber on your Raspberry Pi to connect to the OpenBCI GUI LSL stream.

## Step 1: Initial Setup (One-time)

On your Raspberry Pi, navigate to the project directory and run:

```bash
bash setup_raspberry_pi.sh
```

This script will:
- Install `python3-full` and `python3-venv` if needed
- Create a virtual environment (`venv/`)
- Install required packages: `pylsl`, `numpy`, `scipy`, `pygame`

## Step 2: Start the LSL Subscriber

Once setup is complete, you can start the LSL subscriber in one of two ways:

### Option A: Run subscriber and game separately (recommended for debugging)

**Terminal 1 - LSL Subscriber:**
```bash
source venv/bin/activate
python lsl_subscriber.py --mode game --stream-name "OpenBCI_EEG"
```

**Terminal 2 - Game:**
```bash
source venv/bin/activate
python focus_race.py
```

### Option B: Use launch scripts (easier)

**Terminal 1 - LSL Subscriber:**
```bash
bash start_lsl_game.sh
```

**Terminal 2 - Game:**
```bash
bash start_game.sh
```

## Step 3: Verify Connection

1. **Make sure OpenBCI GUI is running** on your laptop/desktop
2. **Start the LSL stream** in OpenBCI GUI:
   - Open the "Networking" widget
   - Set `Output = LSL`
   - Set `Data Type = EEG`
   - Click "Start LSL Stream"
3. **Check the subscriber output** - you should see:
   ```
   ✅ Connected to LSL stream: OpenBCI_EEG
      Sampling rate: 250 Hz
      Channels: 8
   ```
4. **Check the game** - the focus meter should react to your concentration

## Troubleshooting

### "No LSL stream found"
- Make sure OpenBCI GUI is running and LSL stream is started
- Check that both devices are on the same network
- Try specifying the stream name: `--stream-name "YourStreamName"`

### "pylsl not available"
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Re-run setup: `bash setup_raspberry_pi.sh`

### Game not reacting
- Check that the LSL subscriber is running and connected
- Verify UDP port 5005 is not blocked by firewall
- Check subscriber output for "Attention: XX.X%" messages

## Notes

- The virtual environment must be activated each time you open a new terminal
- The launch scripts automatically activate the venv for you
- Both the subscriber and game need to be running for the game to work

