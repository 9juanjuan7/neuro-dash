# Windows Drivers for OpenBCI

## What Drivers Do You Need?

OpenBCI boards (Cyton, Ganglion via USB) use **FTDI USB-to-Serial chips** that require drivers on Windows to communicate with your computer.

## Driver Installation Guide

### For Cyton Boards (USB Connection)

Cyton boards use **FTDI FT231X** chips and require FTDI Virtual COM Port (VCP) drivers.

#### Step 1: Download FTDI Drivers

1. Go to the FTDI website: https://ftdichip.com/drivers/vcp-drivers/
2. Download the **Windows installer** for your system:
   - **Windows 10/11 (64-bit)**: Download "CDM v2.XX.XX WHQL Certified" for Windows
   - Select the `.exe` installer (not the `.zip`)

#### Step 2: Install Drivers

1. **Disconnect your OpenBCI device** (if connected)
2. Run the downloaded installer (e.g., `CDM v2.XX.XX WHQL Certified.exe`)
3. Follow the installation wizard:
   - Accept the license agreement
   - Choose "Install" (not "Extract")
   - Wait for installation to complete
4. **Restart your computer** (recommended)

#### Step 3: Verify Installation

1. Connect your OpenBCI Cyton board via USB
2. Power on the board
3. Open **Device Manager**:
   - Press `Win + X` → Select "Device Manager"
   - Or: Press `Win + R` → Type `devmgmt.msc` → Press Enter
4. Look under **"Ports (COM & LPT)"**
5. You should see:
   - **"USB Serial Port (COM3)"** or similar
   - **No yellow warning triangles**
   - **No "Unknown Device"** entries

### For Ganglion Boards (USB Connection)

Ganglion boards also use FTDI chips and require the same FTDI VCP drivers as Cyton.

**Follow the same steps as Cyton above.**

### For Ganglion Boards (Bluetooth)

**No drivers needed!** Bluetooth connections use Windows' built-in Bluetooth drivers.

Just make sure:
- Bluetooth is enabled on your computer
- Your Ganglion is in pairing mode
- You have the MAC address of your Ganglion

## Troubleshooting Driver Issues

### Device Shows as "Unknown Device" or Has Yellow Triangle

**Problem**: Drivers not installed or incorrect drivers installed.

**Solution**:
1. Right-click on the device in Device Manager
2. Select **"Update Driver"**
3. Choose **"Browse my computer for drivers"**
4. Select **"Let me pick from a list of available drivers"**
5. Select **"FTDI"** from the manufacturer list
6. Select **"USB Serial Port"** from the model list
7. Click **"Next"** and follow the prompts

### Device Not Appearing in Device Manager

**Problem**: Device not recognized at all.

**Solutions**:
1. **Try a different USB cable** (some cables are power-only)
2. **Try a different USB port** (prefer USB 2.0 ports, not USB 3.0)
3. **Check device power** - Make sure the board is powered on
4. **Uninstall old drivers**:
   - In Device Manager, right-click the device
   - Select "Uninstall device"
   - Check "Delete the driver software for this device"
   - Reinstall drivers from step 1 above

### "Access Denied" or "Port Already in Use" Errors

**Problem**: Another application is using the COM port.

**Solutions**:
1. Close any other applications that might be using the device:
   - OpenBCI GUI
   - Other Python scripts
   - Serial terminal programs
2. Restart your computer if the port is stuck
3. Check what's using the port:
   - Open Command Prompt as Administrator
   - Run: `netstat -ano | findstr :COM3` (replace COM3 with your port)
   - End the process if needed

### Driver Installation Fails

**Problem**: Installer won't run or fails during installation.

**Solutions**:
1. **Run as Administrator**:
   - Right-click the installer
   - Select "Run as administrator"
2. **Disable antivirus temporarily** (sometimes blocks driver installation)
3. **Check Windows updates** - Make sure Windows is up to date
4. **Try compatibility mode**:
   - Right-click installer → Properties → Compatibility
   - Check "Run this program in compatibility mode for Windows 10"
5. **Manual installation**:
   - Extract the driver files from the installer
   - Use Device Manager to manually point to the driver folder

## Alternative: Using Zadig (For Advanced Users)

If FTDI drivers don't work, you can use **Zadig** to install WinUSB drivers:

1. Download Zadig: https://zadig.akeo.ie/
2. Connect your OpenBCI device
3. Open Zadig
4. Select your device from the dropdown
5. Select "WinUSB" as the driver
6. Click "Install Driver" or "Replace Driver"

**Note**: This will replace the FTDI driver. You may need to use BrainFlow's different connection method if you use Zadig.

## Quick Checklist

Before connecting:
- [ ] FTDI drivers installed
- [ ] Computer restarted after driver installation
- [ ] Device appears in Device Manager under "Ports (COM & LPT)"
- [ ] No yellow warning triangles
- [ ] COM port number noted (e.g., COM3)
- [ ] Device is powered on
- [ ] No other applications using the device

## Still Having Issues?

1. **Check OpenBCI Documentation**: 
   - https://docs.openbci.com/Troubleshooting/FTDI_Fix_Windows/
   
2. **Check BrainFlow Documentation**:
   - https://brainflow.readthedocs.io/

3. **Check Device Manager Details**:
   - Right-click device → Properties → Details
   - Look at "Hardware Ids" to identify the chip type
   - Search for that chip's specific drivers

4. **Try on Another Computer**:
   - Helps determine if it's a driver issue or hardware issue

5. **Contact OpenBCI Support**:
   - OpenBCI Forum: https://openbci.com/forum/
   - They can help with driver-specific issues

## Summary

**For USB connections (Cyton, Ganglion USB):**
- Install **FTDI VCP Drivers** from https://ftdichip.com/drivers/vcp-drivers/
- Restart computer
- Verify in Device Manager

**For Bluetooth (Ganglion only):**
- No drivers needed!
- Use Windows built-in Bluetooth

That's it! Once drivers are installed, your device should appear as a COM port and you can connect via the app.

