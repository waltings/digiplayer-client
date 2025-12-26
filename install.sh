#!/bin/bash
#
# DigiPlayer V1 - Quick Install Script
# For Raspberry Pi OS (with desktop or lite)
#

set -e

echo "=================================="
echo "  DigiPlayer V1 Installer"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

# Run the full setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/scripts/setup-pi.sh"
