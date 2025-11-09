# Quick Guide: Connect to OpenBCI

## Very Simple Steps

### 1. Install BrainFlow

```bash
pip install brainflow
```

### 2. Connect Your Device

- **Cyton/Ganglion (USB)**: Plug in USB cable to your computer
- **Ganglion (Bluetooth)**: Turn on and pair via Bluetooth

### 3. Find Your Port/Address

**Windows (USB):**

- Press `Win + X` → Device Manager
- Look under "Ports (COM & LPT)"
- Find your device (e.g., "COM3" or "COM4")
- Write down the COM number (e.g., `COM3`)

**Mac/Linux (USB):**

- Open Terminal
- Run: `ls /dev/tty.*` (Mac) or `ls /dev/ttyUSB*` (Linux)
- Find your device (e.g., `/dev/tty.usbserial-ABC123`)
- Write down the full path

**Bluetooth (Ganglion):**

- Turn on your Ganglion
- On your computer, scan for Bluetooth devices
- Find "Ganglion" and note the MAC address (e.g., `00:11:22:33:44:55`)

### 4. Run the App

```bash
streamlit run app.py
```

### 5. Connect in the App

1. Open the **sidebar** (click the arrow on the top left)
2. **Uncheck** "Demo Mode (No Hardware)"
3. Select connection type:
   - **"Serial Port"** for USB connection
   - **"Bluetooth (MAC)"** for Bluetooth connection
4. Enter your port or MAC address:
   - USB: Enter the COM port (e.g., `COM3`) or device path
   - Bluetooth: Enter the MAC address (e.g., `00:11:22:33:44:55`)
5. Click **"Connect to OpenBCI"**
6. You should see "Connected! ✅"

### 6. Start Racing!

- Click "Start Race"
- Complete calibration (focus for 10 seconds)
- Race!

## Troubleshooting

**Connection fails?**

- Make sure device is powered on
- Check USB cable is connected properly
- Verify the port/MAC address is correct
- Make sure no other app is using the device
- **On Windows: Install FTDI drivers** (see `WINDOWS_DRIVERS.md` for details)
  - Download from: https://ftdichip.com/drivers/vcp-drivers/
  - Install and restart your computer
  - Check Device Manager to verify the device appears as a COM port

**Still not working?**

- Try a different USB port
- Restart the app
- Check `OPENBCI_SETUP.md` for detailed troubleshooting

## That's It!

You're ready to race with your brain! 🧠🏎️
