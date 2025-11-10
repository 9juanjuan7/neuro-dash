#!/bin/bash
# Launch script for Laptop (Linux/Mac) - Forwards LSL stream to Raspberry Pi over Tailscale
# Usage: ./start_forwarder.sh <pi-tailscale-ip>

echo "🚀 Starting LSL Forwarder (Laptop)"
echo "===================================="

if [ -z "$1" ]; then
    echo "❌ Error: Raspberry Pi Tailscale IP required"
    echo ""
    echo "Usage: ./start_forwarder.sh <pi-tailscale-ip>"
    echo "Example: ./start_forwarder.sh 100.69.227.30"
    echo ""
    echo "To find Pi IP: ssh into Pi and run 'tailscale ip'"
    exit 1
fi

PI_IP=$1

echo "Forwarding to Raspberry Pi: $PI_IP"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the forwarder
python lsl_forwarder.py --pi-ip "$PI_IP" --stream-name "eegstream" --mode both

