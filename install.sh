#!/bin/bash
#
# DigiPlayer V1 Installation Script
# For Raspberry Pi OS Lite
#

set -e

INSTALL_DIR="/opt/digiplayer"
CONFIG_DIR="/etc/digiplayer"
MEDIA_DIR="/var/lib/digiplayer/media"
LOG_DIR="/var/log/digiplayer"

echo "=================================="
echo "  DigiPlayer V1 Installer"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./install.sh)"
    exit 1
fi

# Check if Raspberry Pi
if ! grep -q "Raspberry Pi\|BCM" /proc/cpuinfo 2>/dev/null; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "1. Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv

echo ""
echo "2. Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$MEDIA_DIR"
mkdir -p "$LOG_DIR"

echo ""
echo "3. Copying files..."
cp -r digiplayer "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

echo ""
echo "4. Installing Python dependencies..."
cd "$INSTALL_DIR"
pip3 install -r requirements.txt

echo ""
echo "5. Installing systemd service..."
cp systemd/digiplayer.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable digiplayer.service

echo ""
echo "6. Generating device ID..."
DEVICE_ID=$(python3 -c "from digiplayer.utils import generate_device_id; print(generate_device_id())")
echo ""
echo "=================================="
echo "  Installation Complete!"
echo "=================================="
echo ""
echo "  Device ID: $DEVICE_ID"
echo ""
echo "  Next steps:"
echo "  1. Register this device ID in the DigiPlayer web UI"
echo "  2. Get the player_id from the web UI"
echo "  3. Run: digiplayer --set-player-id <ID>"
echo "  4. Start the service: systemctl start digiplayer"
echo ""
echo "  Useful commands:"
echo "    digiplayer --show-id        Show device ID"
echo "    digiplayer --test-heartbeat Test server connection"
echo "    systemctl status digiplayer View service status"
echo "    journalctl -u digiplayer -f View logs"
echo ""
