#!/bin/bash

echo "Starting NavBox GPS Controller installation..."

# Update system and install dependencies
echo "Updating system and installing dependencies..."
sudo apt update
if [ $? -ne 0 ]; then
    echo "Error: Failed to run 'apt update'. Check network connectivity or APT sources."
    echo "Try setting DNS (e.g., 'sudo nmcli con mod \"Wired connection 1\" ipv4.dns \"8.8.8.8,8.8.4.4\"')"
    echo "Or use alternative mirror in /etc/apt/sources.list (e.g., 'deb http://ftp.us.debian.org/debian bookworm main')."
    exit 1
fi
sudo apt install -y python3-pip python3-venv python3-serial libatlas-base-dev
if [ $? -ne 0 ]; then
    echo "Error: Failed to install APT packages. Ensure repositories are accessible."
    exit 1
fi

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv /mdt/home/navbox/venv
source /mdt/home/navbox/venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir pyserial numpy websockets
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python packages. Check pip and network connectivity."
    deactivate
    exit 1
fi
deactivate

# Install check_gps.py
echo "Installing check_gps.py..."
sudo cp check_gps.py /mdt/home/navbox/check_gps.py
sudo chmod +x /mdt/home/navbox/check_gps.py

# Run GPS check
echo "Running GPS module check..."
/mdt/home/navbox/check_gps.py
if [ $? -ne 0 ]; then
    echo "Error: GPS module check failed. Check GNSS modules and connections."
    exit 1
fi

# Install service
echo "Installing NavBox service..."
sudo cp navbox.service /etc/systemd/system/navbox.service
sudo systemctl enable navbox.service
sudo systemctl start navbox.service

# Check service status
echo "Checking NavBox service status..."
sudo systemctl status navbox.service
if [ $? -ne 0 ]; then
    echo "Error: NavBox service failed to start. Check logs with 'journalctl -u navbox.service -f'."
    exit 1
fi

echo "NavBox GPS Controller installation completed successfully!"