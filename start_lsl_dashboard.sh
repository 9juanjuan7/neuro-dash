#!/bin/bash
# Launch script for Laptop (Dashboard mode)
# Connects to LSL stream and sends attention scores + ready flags to dashboard

echo "👩‍⚕️ Starting LSL Subscriber for Dashboard (Laptop)"
echo "=================================================="

# Check if virtual environment exists (optional, for consistency)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the subscriber in dashboard mode
python lsl_subscriber.py --mode dashboard --stream-name "OpenBCI_EEG" --dashboard-port 5006
