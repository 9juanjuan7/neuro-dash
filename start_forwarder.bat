@echo off
REM Launch script for Laptop - Forwards LSL stream to Raspberry Pi over Tailscale
REM Usage: start_forwarder.bat <pi-tailscale-ip>

echo 🚀 Starting LSL Forwarder (Laptop)
echo ====================================

if "%1"=="" (
    echo ❌ Error: Raspberry Pi Tailscale IP required
    echo.
    echo Usage: start_forwarder.bat <pi-tailscale-ip>
    echo Example: start_forwarder.bat 100.69.227.30
    echo.
    echo To find Pi IP: ssh into Pi and run "tailscale ip"
    pause
    exit /b 1
)

set PI_IP=%1

echo Forwarding to Raspberry Pi: %PI_IP%
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the forwarder
python lsl_forwarder.py --pi-ip %PI_IP% --stream-name "eegstream" --mode both

pause

