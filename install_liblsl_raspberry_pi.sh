#!/bin/bash
# Install liblsl on Raspberry Pi

echo "📦 Installing liblsl for Raspberry Pi..."
echo "=========================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This script is designed for Raspberry Pi"
    echo "   Proceeding anyway..."
fi

# Update package list
echo "Updating package list..."
sudo apt update

# Try to install liblsl from apt (if available)
echo ""
echo "Attempting to install liblsl via apt..."
if sudo apt install -y liblsl1 liblsl-dev 2>/dev/null; then
    echo "✅ liblsl installed via apt"
    exit 0
fi

# If apt doesn't work, try building from source
echo ""
echo "⚠️  liblsl not available in apt repositories"
echo "Building from source..."
echo ""

# Install build dependencies
echo "Installing build dependencies..."
sudo apt install -y build-essential cmake git

# Clone and build liblsl
cd /tmp
if [ -d "liblsl" ]; then
    rm -rf liblsl
fi

echo "Cloning liblsl repository..."
git clone https://github.com/sccn/liblsl.git
cd liblsl

echo "Building liblsl..."
mkdir build
cd build
cmake ..
make -j4

echo "Installing liblsl..."
sudo make install
sudo ldconfig

echo ""
echo "✅ liblsl installed!"
echo ""
echo "Now reinstall pylsl:"
echo "  source venv/bin/activate"
echo "  pip install --force-reinstall pylsl"

