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

# Check network connectivity
echo "Checking network connectivity..."
if ! ping -c 4 8.8.8.8 > /dev/null 2>&1; then
    echo "Error: No internet connectivity. Cannot ping 8.8.8.8."
    echo "Check Wi-Fi connection with: nmcli device status"
    exit 1
fi
if ! ping -c 4 google.com > /dev/null 2>&1; then
    echo "Error: DNS resolution failed. Cannot ping google.com."
    echo "Setting Google DNS for wlan0..."
    WIFI_CON="preconfigured"
    if ! nmcli con show --active | grep -q "$WIFI_CON"; then
        echo "Error: Wi-Fi connection '$WIFI_CON' not active."
        echo "Connect to Wi-Fi with: nmcli device wifi connect 'Your-SSID' password 'Your-Password'"
        exit 1
    fi
    nmcli con mod "$WIFI_CON" ipv4.dns "8.8.8.8,8.8.4.4"
    nmcli con mod "$WIFI_CON" ipv4.ignore-auto-dns yes
    nmcli con up "$WIFI_CON"
    if ! ping -c 4 google.com > /dev/null 2>&1; then
        echo "Error: DNS still not working. Setting manual DNS..."
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
        chattr +i /etc/resolv.conf
        if ! ping -c 4 google.com > /dev/null 2>&1; then
            echo "Error: DNS resolution still failing. Check router or ISP."
            exit 1
        fi
    fi
fi

# 1. Update system and install dependencies
echo "Updating system and installing dependencies..."
apt update
if [ $? -ne 0 ]; then
    echo "Error: 'apt update' failed. Try editing /etc/apt/sources.list to use 'http://ftp.us.debian.org/debian'."
    exit 1
fi
apt install -y python${PYTHON_VERSION} python3-pip python3-venv python3-serial libatlas-base-dev
if [ $? -ne 0 ]; then
    echo "Error: Failed to install APT packages. Check repository access."
    exit 1
fi

# 2. Create virtual environment
echo "Setting up Python virtual environment..."
mkdir -p "$INSTALL_DIR"
python3 -m venv "${INSTALL_DIR}/venv"
source "${INSTALL_DIR}/venv/bin/activate"
pip install --no-cache-dir pyserial numpy websockets
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python packages."
    deactivate
    exit 1
fi
deactivate

# 3. Create navbox user
echo "Creating navbox user..."
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER"
    echo "User $USER created."
else
    echo "User $USER already exists."
fi

# 4. Setup directories
echo "Setting up directories..."
mkdir -p "$LOG_DIR"
chown -R "$USER:$USER" "$INSTALL_DIR"

# 5. Copy application files
echo "Copying application files..."
for file in config.json gps_logger.py heading_calc.py main.py retry_queue.json checkgps1.py  index.html; do
    if [ -f "${SCRIPT_DIR}/${file}" ]; then
        cp "${SCRIPT_DIR}/${file}" "$INSTALL_DIR/"
        chown "$USER:$USER" "${INSTALL_DIR}/${file}"
        chmod 644 "${INSTALL_DIR}/${file}"
        echo "Copied $file to $INSTALL_DIR"
    else
        echo "Warning: $file not found in ${SCRIPT_DIR}"
    fi
done
# # Ensure main.py and checkgps1.py  are executable
# if [ -f "${INSTALL_DIR}/main.py" ]; then
#     chmod +x "${INSTALL_DIR}/main.py"
# fi
# if [ -f "${INSTALL_DIR}/checkgps1.py " ]; then
#     chmod +x "${INSTALL_DIR}/checkgps1.py "
# fi

# 6. Ensure navbox user has serial port access
echo "Granting serial port access to navbox user..."
usermod -a -G dialout "$USER"

# # 7. Check GPS module connections
# echo "Checking GPS module connections..."
# if [ -f "${INSTALL_DIR}/checkgps1.py " ]; then
#     if ! su -s /bin/bash "$USER" -c "${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/checkgps1.py "; then
#         echo "Error: GPS module check failed."
#         echo "Ensure NEO-M8N modules are connected to /dev/ttyACM0 and /dev/ttyACM1 and powered on."
#         echo "Check serial permissions: groups $USER"
#         echo "Verify baud rate in config.json (default: 9600)."
#         exit 1
#     else
#         echo "GPS module check passed."
#     fi
# else
#     echo "Error: checkgps1.py  not found in $INSTALL_DIR"
#     exit 1
# fi

# 8. Copy and configure service file
echo "Configuring systemd service..."
if [ -f "${SCRIPT_DIR}/navbox.service" ]; then
    cp "${SCRIPT_DIR}/navbox.service" "$SERVICE_FILE"
    chmod 644 "$SERVICE_FILE"
    echo "Copied navbox.service to $SERVICE_FILE"
else
    echo "Error: navbox.service not found in ${SCRIPT_DIR}"
    exit 1
fi

# 9. Enable and start service
echo "Enabling and starting navbox service..."
systemctl daemon-reload
systemctl enable navbox.service
systemctl start navbox.service

# 10. Verify service status
echo "Checking service status..."
if systemctl is-active --quiet navbox.service; then
    echo "NavBox service is running successfully."
else
    echo "Error: NavBox service failed to start. Check logs with: journalctl -u navbox.service"
    exit 1
fi

echo "Installation completed successfully!"
echo "To access the dashboard, copy ${INSTALL_DIR}/index.html to a web server or open it in a browser."
echo "Ensure NEO-M8N modules are connected to /dev/ttyACM0 and /dev/ttyACM1."
echo "Check service logs with: journalctl -u navbox.service"
echo "Access live data via WebSocket at: ws://localhost:8080/api/position"