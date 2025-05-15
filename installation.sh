#!/bin/bash

# NavBox GPS Controller Installation Script
# Run with sudo: sudo bash installation.sh

# Exit on any error
set -e

# Define variables
INSTALL_DIR="/mdt/home/navbox"
LOG_DIR="${INSTALL_DIR}/logs"
USER="navbox"
SERVICE_FILE="/etc/systemd/system/navbox.service"
PYTHON_VERSION="3.11"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root. Use: sudo bash installation.sh"
    exit 1
fi

echo "Starting NavBox GPS Controller installation..."

# 1. Update system and install dependencies
echo "Updating system and installing dependencies..."
apt update
apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-pip

# Install Python packages
pip3 install pyserial requests websockets

# 2. Create navbox user
echo "Creating navbox user..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
    echo "User $USER created."
else
    echo "User $USER already exists."
fi

# 3. Setup directories
echo "Setting up directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
chown -R "$USER:$USER" "$INSTALL_DIR"

# 4. Copy application files
echo "Copying application files..."
for file in config.json gps_logger.py heading_calc.py main.py retry_queue.json check_gps.py; do
    if [ -f "${SCRIPT_DIR}/${file}" ]; then
        cp "${SCRIPT_DIR}/${file}" "$INSTALL_DIR/"
        chown "$USER:$USER" "${INSTALL_DIR}/${file}"
        chmod 644 "${INSTALL_DIR}/${file}"
        echo "Copied $file to $INSTALL_DIR"
    else
        echo "Warning: $file not found in ${SCRIPT_DIR}"
    fi
done

# Copy index.html (optional, for dashboard)
if [ -f "${SCRIPT_DIR}/index.html" ]; then
    cp "${SCRIPT_DIR}/index.html" "$INSTALL_DIR/"
    chown "$USER:$USER" "${INSTALL_DIR}/index.html"
    chmod 644 "${INSTALL_DIR}/index.html"
    echo "Copied index.html to $INSTALL_DIR"
else
    echo "Warning: index.html not found in ${SCRIPT_DIR}"
fi

# 5. Copy and configure service file
echo "Configuring systemd service..."
if [ -f "${SCRIPT_DIR}/navbox.service" ]; then
    cp "${SCRIPT_DIR}/navbox.service" "$SERVICE_FILE"
    chmod 644 "$SERVICE_FILE"
    echo "Copied navbox.service to $SERVICE_FILE"
else
    echo "Error: navbox.service not found in ${SCRIPT_DIR}"
    exit 1
fi

# 6. Check GPS module connections
echo "Checking GPS module connections..."
if [ -f "${INSTALL_DIR}/check_gps.py" ]; then
    # Run as navbox user to ensure correct permissions
    if ! su -s /bin/bash "$USER" -c "python${PYTHON_VERSION} ${INSTALL_DIR}/check_gps.py"; then
        echo "Error: GPS module check failed."
        echo "Ensure GPS modules are connected to /dev/ttyACM0 and /dev/ttyACM1 and powered on."
        echo "Check serial permissions: sudo usermod -a -G dialout $USER"
        echo "Verify baud rate in config.json matches GPS modules (default: 9600)."
        exit 1
    else
        echo "GPS module check passed."
    fi
else
    echo "Error: check_gps.py not found in $INSTALL_DIR"
    exit 1
fi

# 7. Enable and start service
echo "Enabling and starting navbox service..."
systemctl daemon-reload
systemctl enable navbox.service
systemctl start navbox.service

# 8. Verify service status
echo "Checking service status..."
if systemctl is-active --quiet navbox.service; then
    echo "NavBox service is running successfully."
else
    echo "Error: NavBox service failed to start. Check logs with: journalctl -u navbox.service"
    exit 1
fi

echo "Installation completed successfully!"
echo "To access the dashboard, copy ${INSTALL_DIR}/index.html to a web server or open it in a browser."
echo "Ensure GPS modules are connected to /dev/ttyACM0 and /dev/ttyACM1."
echo "Check service logs with: journalctl -u navbox.service"
echo "Access live data via WebSocket at: ws://localhost:8080/api/position"