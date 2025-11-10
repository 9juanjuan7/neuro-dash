#!/bin/bash
# Setup script for Raspberry Pi
# Creates virtual environment and installs dependencies

echo "🍓 Setting up Raspberry Pi environment..."
echo "=========================================="

# Check if python3-full is installed
if ! dpkg -l | grep -q python3-full; then
    echo "Installing python3-full..."
    sudo apt update
    sudo apt install -y python3-full python3-venv
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install pylsl numpy scipy pygame

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Or use the launch scripts:"
echo "  ./start_lsl_game.sh"
echo "  ./start_game.sh"

