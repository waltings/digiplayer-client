#!/bin/bash
#
# DigiPlayer V1 - First Boot Script
# Runs automatically on first boot to complete setup
#

MARKER_FILE="/etc/digiplayer/.first-boot-done"
LOG_FILE="/var/log/digiplayer/first-boot.log"

# Exit if already done
if [ -f "$MARKER_FILE" ]; then
    exit 0
fi

exec > >(tee -a "$LOG_FILE") 2>&1
echo "$(date): First boot setup starting..."

# Wait for network
echo "Waiting for network..."
for i in {1..30}; do
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo "Network available"
        break
    fi
    sleep 2
done

# Generate and save device ID
echo "Generating device ID..."
cd /opt/digiplayer
DEVICE_ID=$(python3 -c "import sys; sys.path.insert(0, '.'); from digiplayer.utils import generate_device_id; print(generate_device_id())")
echo "Device ID: $DEVICE_ID"

# Create initial config if not exists
if [ ! -f /etc/digiplayer/config.json ]; then
    python3 -c "
import sys
sys.path.insert(0, '.')
from digiplayer.config import load_config, save_config
config = load_config()
save_config(config)
print('Config created')
"
fi

# Mark as done
mkdir -p /etc/digiplayer
touch "$MARKER_FILE"

echo "$(date): First boot setup complete"
