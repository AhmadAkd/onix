#!/bin/bash

echo ""
echo "================================="
echo "      Starting Onix Build"
echo "================================="
echo ""

# Make the script exit if any command fails
set -e

# Step 1: Check for virtual environment.
if [ ! -d "venv" ]; then
    echo "Warning: Virtual environment 'venv' not found."
    echo "It is recommended to install dependencies in a venv."
    echo ""
fi

# Step 2: Create the version.txt file for local development builds.
echo "Creating version.txt for build..."
echo "dev" > version.txt
echo "version.txt created successfully."
echo ""

# Step 3: Ensure sing-box binary is available (downloads if needed).
echo "Ensuring sing-box binary is available..."
python download_singbox.py
echo "sing-box binary check complete."
echo ""

# Step 4: Download GeoIP database if it doesn't exist.
if [ ! -f "geoip.db" ]; then
    echo "Downloading GeoIP database (geoip.db)..."
    curl -L -o geoip.db "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"
fi

# Step 5: Run PyInstaller to build the executable.
echo "Building the executable with PyInstaller..."
echo "This might take a few minutes."
echo ""

pyinstaller --noconfirm --onefile --windowed --name onix \
--add-data "sing-box:." \
--add-data "version.txt:." \
--add-data "geoip.db:." \
--icon="assets/icon.ico" \
main.py

echo ""
echo "======================================================="
echo " Build successful!"
echo " The executable 'onix' can be found in the 'dist' folder."
echo "======================================================="
echo ""
