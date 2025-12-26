# DigiPlayer V1 - Raspberry Pi Client

Digital signage player client for Raspberry Pi that connects to the DigiPlayer server.

## Features

- Automatic device ID generation
- Heartbeat communication with server
- Remote command execution (reboot, refresh, screen on/off)
- Media file synchronization (coming soon)
- Image/video playback (coming soon)

## Requirements

- Raspberry Pi 3 B/B+ or Pi 4
- Raspberry Pi OS Lite (recommended)
- Python 3.9+
- Network connection

## Quick Start

### 1. Install on Raspberry Pi

```bash
# Clone or copy files to Raspberry Pi
scp -r digiplayer-client/ pi@raspberrypi:/home/pi/

# SSH into Pi
ssh pi@raspberrypi

# Install
cd /home/pi/digiplayer-client
sudo ./install.sh
```

### 2. Register Device

After installation, you'll see a Device ID like `DIG343EB7AE0A2`.

1. Go to the DigiPlayer web UI (https://www.digireklaam.ee)
2. Navigate to Players → Add Player
3. Enter the Device ID
4. Note the assigned Player ID

### 3. Configure Player ID

```bash
sudo digiplayer --set-player-id <YOUR_PLAYER_ID>
```

### 4. Start Service

```bash
sudo systemctl start digiplayer
```

## Manual Usage

```bash
# Show device ID
digiplayer --show-id

# Test heartbeat connection
digiplayer --test-heartbeat

# Run in foreground (for debugging)
digiplayer -v

# Set server URL (if different)
digiplayer --set-server https://your-server.com
```

## Configuration

Configuration is stored in `/etc/digiplayer/config.json`:

```json
{
  "server_url": "https://www.digireklaam.ee",
  "api_prefix": "/api/v1",
  "device_id": "DIG343EB7AE0A2",
  "player_id": 1,
  "heartbeat_interval": 30
}
```

## Service Management

```bash
# Start
sudo systemctl start digiplayer

# Stop
sudo systemctl stop digiplayer

# Status
sudo systemctl status digiplayer

# View logs
sudo journalctl -u digiplayer -f

# Restart
sudo systemctl restart digiplayer
```

## Directory Structure

```
/opt/digiplayer/          # Application code
/etc/digiplayer/          # Configuration
/var/lib/digiplayer/media # Media files
/var/log/digiplayer/      # Logs
```

## Development

For development on non-Pi systems:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
python -m digiplayer.main --show-id
```

## Troubleshooting

### Device not connecting
1. Check network connection
2. Verify server URL: `digiplayer --test-heartbeat`
3. Ensure player_id is set correctly

### Service won't start
```bash
sudo journalctl -u digiplayer --no-pager -n 50
```

### Reset configuration
```bash
sudo rm /etc/digiplayer/config.json
sudo digiplayer --show-id
```

## License

MIT License
