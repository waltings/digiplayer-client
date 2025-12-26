#!/bin/bash
#
# DigiPlayer V1 - Raspberry Pi Setup Script
# Run this on a fresh Raspberry Pi OS Lite installation
#

set -e

echo "=================================="
echo "  DigiPlayer V1 Setup"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./setup-pi.sh"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/digiplayer"
CONFIG_DIR="/etc/digiplayer"
MEDIA_DIR="/var/lib/digiplayer/media"
LOG_DIR="/var/log/digiplayer"
PI_USER="pi"

echo ""
echo "Step 1: System update..."
apt-get update
apt-get upgrade -y

echo ""
echo "Step 2: Installing dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    cage \
    fonts-dejavu \
    network-manager \
    dnsmasq \
    hostapd \
    unclutter \
    xdotool

echo ""
echo "Step 3: Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$MEDIA_DIR"
mkdir -p "$LOG_DIR"
chown -R $PI_USER:$PI_USER "$MEDIA_DIR"
chown -R $PI_USER:$PI_USER "$LOG_DIR"

echo ""
echo "Step 4: Copying DigiPlayer files..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cp -r "$PROJECT_DIR/digiplayer" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/web" "$INSTALL_DIR/"
cp "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"

echo ""
echo "Step 5: Installing Python packages..."
pip3 install -r "$INSTALL_DIR/requirements.txt"

echo ""
echo "Step 6: Installing systemd services..."
cp "$PROJECT_DIR/systemd/digiplayer.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/digiplayer-kiosk.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable digiplayer.service
systemctl enable digiplayer-kiosk.service

echo ""
echo "Step 7: Configuring auto-login for kiosk..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $PI_USER --noclear %I \$TERM
EOF

echo ""
echo "Step 8: Disabling screen blanking..."
cat >> /etc/xdg/lxsession/LXDE-pi/autostart 2>/dev/null << EOF
@xset s off
@xset -dpms
@xset s noblank
EOF

# Also for console
cat >> /boot/cmdline.txt << EOF
 consoleblank=0
EOF

echo ""
echo "Step 9: Generating Device ID..."
cd "$INSTALL_DIR"
DEVICE_ID=$(python3 -c "import sys; sys.path.insert(0, '.'); from digiplayer.utils import generate_device_id; print(generate_device_id())")

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "  Device ID: $DEVICE_ID"
echo ""
echo "  The system will now reboot."
echo "  After reboot, you will see the registration screen."
echo ""
echo "  Register this device at:"
echo "  https://www.digireklaam.ee/players"
echo ""
read -p "Press Enter to reboot..."
reboot
