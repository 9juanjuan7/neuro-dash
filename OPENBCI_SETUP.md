# OpenBCI Hardware Setup Guide

Step-by-step instructions for connecting OpenBCI devices to the EEG Car Race game.

## Prerequisites

1. **OpenBCI Hardware**: Cyton, Ganglion, or other BrainFlow-supported board
2. **Python 3.8+**: Make sure Python is installed
3. **BrainFlow Library**: Install the BrainFlow Python package

## Step 1: Install BrainFlow

Install the BrainFlow library that interfaces with OpenBCI hardware:

```bash
pip install brainflow
```

For Windows, you may also need:
```bash
pip install pyserial
```

## Step 2: Identify Your OpenBCI Device

### Cyton (USB/Serial)
- Connects via USB cable
- Uses serial port communication
- Windows: Usually `COM3`, `COM4`, etc. (check Device Manager)
- Mac/Linux: Usually `/dev/ttyUSB0`, `/dev/tty.usbserial-*`, etc.

### Ganglion
- Can connect via USB or Bluetooth Low Energy (BLE)
- USB: Similar to Cyton (serial port)
- BLE: Requires MAC address of the device

### Other Boards
- Check BrainFlow documentation for your specific board: https://brainflow.readthedocs.io/

## Step 3: Find Your Serial Port (Cyton/Ganglion USB)

### Windows
1. Connect your OpenBCI device via USB
2. Open Device Manager (Win + X → Device Manager)
3. Look under "Ports (COM & LPT)"
4. Find your OpenBCI device (e.g., "USB Serial Port (COM3)")
5. Note the COM port number (e.g., COM3, COM4)

### Mac
1. Connect your OpenBCI device via USB
2. Open Terminal
3. Run: `ls /dev/tty.*`
4. Look for something like `/dev/tty.usbserial-*` or `/dev/tty.usbmodem*`

### Linux
1. Connect your OpenBCI device via USB
2. Open Terminal
3. Run: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`
4. Look for your device (e.g., `/dev/ttyUSB0`)

## Step 4: Find MAC Address (Ganglion BLE)

If using Ganglion via Bluetooth:

1. Turn on your Ganglion board
2. Put it in pairing mode (check Ganglion documentation)
3. On your computer, scan for Bluetooth devices
4. Find your Ganglion device
5. Note the MAC address (format: `XX:XX:XX:XX:XX:XX`)

## Step 5: Connect in the Game

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```

2. **Open the sidebar** and uncheck "Demo Mode (No Hardware)"

3. **Click "Connect to OpenBCI"**

4. **If connection fails**, you may need to modify the connection code to specify your port/MAC address.

## Step 6: Modify Connection Code (If Needed)

If the automatic connection doesn't work, you may need to modify the connection code in `app.py`.

### For Cyton (USB/Serial):
```python
# In app.py, modify the connection button handler:
if st.button("Connect to OpenBCI", key="connect"):
    streamer = EEGStreamer(use_demo=False)
    # Add your serial port here
    if streamer.connect(serial_port='COM3'):  # Replace COM3 with your port
        if streamer.start_streaming():
            st.session_state.eeg_streamer = streamer
            st.success("Connected!")
```

### For Ganglion (BLE):
```python
# In app.py, modify the connection button handler:
if st.button("Connect to OpenBCI", key="connect"):
    streamer = EEGStreamer(use_demo=False)
    # Add your MAC address here
    if streamer.connect(mac_address='XX:XX:XX:XX:XX:XX'):  # Replace with your MAC
        if streamer.start_streaming():
            st.session_state.eeg_streamer = streamer
            st.success("Connected!")
```

## Step 7: Update EEG Backend (If Needed)

You may need to update `eeg_backend.py` to support your specific board type:

### For Cyton:
```python
# In eeg_backend.py, modify _init_brainflow:
from brainflow.board_shim import BoardIds

def _init_brainflow(self):
    self.params = BrainFlowInputParams()
    # Use Cyton board ID
    self.board_id = BoardIds.CYTON_BOARD.value  # or BoardIds.CYTON_DAISY_BOARD.value
```

### For Ganglion:
```python
# In eeg_backend.py, modify _init_brainflow:
def _init_brainflow(self):
    self.params = BrainFlowInputParams()
    # Use Ganglion board ID
    self.board_id = BoardIds.GANGLION_BOARD.value
```

## Troubleshooting

### Connection Fails
1. **Check USB cable**: Make sure the USB cable is properly connected
2. **Check drivers**: Install OpenBCI drivers if needed
3. **Check port permissions** (Linux/Mac): You may need to add your user to the dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   # Then logout and login again
   ```
4. **Try different USB port**: Some USB ports may not work
5. **Check board power**: Make sure the board is powered on

### "Permission Denied" Error (Linux/Mac)
```bash
# Add user to dialout group (for serial ports)
sudo usermod -a -G dialout $USER

# Or change permissions temporarily
sudo chmod 666 /dev/ttyUSB0  # Replace with your port
```

### Board Not Detected
1. Check Device Manager (Windows) or `lsusb` (Linux) to see if the device is recognized
2. Try unplugging and replugging the USB cable
3. Restart the application
4. Check if other applications are using the serial port

### BrainFlow Import Error
```bash
# Reinstall BrainFlow
pip uninstall brainflow
pip install brainflow

# On Windows, you may need Visual C++ Redistributable
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Data Not Streaming
1. Make sure the board is properly connected and powered
2. Check that electrodes are properly attached
3. Verify the board is in the correct mode (streaming mode)
4. Check the BrainFlow logs for error messages

## Testing Connection

Once connected, you should see:
- Real-time beta power values in the focus tracker
- Focus score responding to your concentration
- Car moving when you focus (in demo mode, it moves automatically)

## Board-Specific Notes

### Cyton
- **Channels**: 8 EEG channels (16 with Daisy)
- **Sampling Rate**: 250 Hz
- **Connection**: USB/Serial
- **Power**: USB or battery pack

### Ganglion
- **Channels**: 4 EEG channels
- **Sampling Rate**: 200 Hz (USB) or variable (BLE)
- **Connection**: USB or BLE
- **Power**: Battery (built-in)

### Synthetic Board (Testing)
- For testing without hardware
- Uses `BoardIds.SYNTHETIC_BOARD`
- Generates fake EEG data
- Good for development and demos

## Additional Resources

- **BrainFlow Documentation**: https://brainflow.readthedocs.io/
- **OpenBCI Documentation**: https://docs.openbci.com/
- **BrainFlow GitHub**: https://github.com/brainflow-dev/brainflow
- **OpenBCI Forum**: https://openbci.com/forum/

## Quick Reference

### Common Board IDs (BrainFlow)
```python
BoardIds.SYNTHETIC_BOARD.value      # For testing
BoardIds.CYTON_BOARD.value          # Cyton (8 channels)
BoardIds.CYTON_DAISY_BOARD.value    # Cyton + Daisy (16 channels)
BoardIds.GANGLION_BOARD.value       # Ganglion (4 channels)
```

### Common Serial Ports
- Windows: `COM3`, `COM4`, `COM5`, etc.
- Mac: `/dev/tty.usbserial-*`, `/dev/tty.usbmodem*`
- Linux: `/dev/ttyUSB0`, `/dev/ttyACM0`

### Connection Function
```python
# Serial port connection
streamer.connect(serial_port='COM3')

# BLE connection
streamer.connect(mac_address='XX:XX:XX:XX:XX:XX')
```

## Need Help?

If you're still having issues:
1. Check the BrainFlow documentation for your specific board
2. Verify your hardware is working with OpenBCI's GUI
3. Check the console/terminal for error messages
4. Try using demo mode first to verify the game works
5. Check that all dependencies are installed correctly
