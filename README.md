# DigiPlayer V1 - Raspberry Pi Client

Plug-and-play digital signage player for Raspberry Pi. Flash the SD card, boot, and register - no command line needed.

**Server**: https://www.digireklaam.ee

---

## Quick Start (5 minutes)

### Step 1: Flash the SD Card

1. Download the latest `digiplayer-v1.x.x.img.xz` from [Releases](https://github.com/waltings/digiplayer-client/releases)
2. Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [Balena Etcher](https://etcher.balena.io/)
3. Select the downloaded image file
4. Select your SD card
5. Click "Write" and wait for completion

### Step 2: Boot the Player

1. Insert the SD card into your Raspberry Pi
2. Connect HDMI cable to your monitor/TV
3. Connect Ethernet cable (or use WiFi setup below)
4. Connect power

### Step 3: Register the Player

After boot (30-60 seconds), you'll see the registration screen:

```
┌─────────────────────────────────────────────────┐
│                                                 │
│              DIGIPLAYER                         │
│         UNREGISTERED PLAYER                     │
│                                                 │
│     ┌─────────────────────────────┐             │
│     │      DIG343EB7AE0A2         │             │
│     └─────────────────────────────┘             │
│                                                 │
│     Register this ID at:                        │
│     www.digireklaam.ee/players                  │
│                                                 │
│     Internet: ● Connected                       │
│     Server:   ● Online                          │
│     Status:   ○ Waiting for registration...     │
│                                                 │
└─────────────────────────────────────────────────┘
```

1. Note the **Device ID** shown on screen (e.g., `DIG343EB7AE0A2`)
2. Go to https://www.digireklaam.ee
3. Navigate to **Players** → **Add Player**
4. Enter the Device ID and save

The player will automatically detect registration within 5 seconds and start playing content!

---

## Adding Content

### Upload Media Files

1. Go to https://www.digireklaam.ee
2. Navigate to **Media** page
3. Click **Upload** button
4. Select images (JPG, PNG) or videos (MP4, WebM)
5. Wait for upload to complete

Supported formats:
- **Images**: JPG, PNG, GIF, WebP
- **Videos**: MP4, WebM, MOV (H.264 recommended)

### Create a Playlist

1. Navigate to **Playlists** page
2. Click **New Playlist**
3. Enter a name (e.g., "Main Display")
4. Add media items from your library
5. Set duration for each item (default: 10 seconds for images)
6. Drag to reorder items
7. Save the playlist

### Assign Playlist to Players

Players are organized in **Groups**. Each group has one playlist.

1. Navigate to **Groups** page
2. Create a group or edit existing one (e.g., "Store Displays")
3. In the **Settings** tab, select a playlist
4. In the **Players** tab, add your players
5. Save changes

All players in the group will automatically sync and play the assigned playlist.

---

## Adding More Players

Adding additional players is simple:

1. Flash a new SD card with the DigiPlayer image
2. Boot the new Raspberry Pi
3. Note the Device ID shown on screen
4. Register at https://www.digireklaam.ee → **Players** → **Add Player**
5. Add the new player to an existing group (or create a new group)

Each player gets a unique Device ID based on its hardware, so you can flash as many SD cards as needed from the same image.

---

## WiFi Setup (No Ethernet)

If you don't have Ethernet available:

### Option 1: WiFi Hotspot Mode

If no network is detected, the player creates a WiFi hotspot:

1. Connect your phone/laptop to WiFi network: `DigiPlayer-XXXX`
2. A setup page opens automatically (or go to http://192.168.4.1)
3. Select your WiFi network and enter password
4. The player saves settings and reconnects

### Option 2: Pre-configure WiFi

Before first boot, add WiFi credentials to the SD card:

1. After flashing, re-insert the SD card
2. Open the `boot` partition
3. Create file `wpa_supplicant.conf`:

```
country=EE
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Your_WiFi_Name"
    psk="Your_WiFi_Password"
    key_mgmt=WPA-PSK
}
```

4. Eject SD card and boot

---

## Remote Commands

Control players remotely from the web interface:

| Command | Description |
|---------|-------------|
| **Refresh** | Reload content immediately |
| **Reboot** | Restart the player |
| **Screen On** | Turn display on |
| **Screen Off** | Turn display off (save energy) |
| **Screenshot** | Capture current screen |

To send commands:
1. Go to **Players** page
2. Click on a player
3. Select command from the menu

---

## Player Status

Each player sends a heartbeat every 30 seconds with:

- **Online/Offline** status
- **IP address**
- **Current content** being played
- **System info** (OS version, uptime)

View all player statuses on the **Players** page. Green = online, Red = offline (no heartbeat for 2+ minutes).

---

## Troubleshooting

### Player shows "No Internet"

- Check Ethernet cable connection
- For WiFi: Verify credentials are correct
- Try connecting to the `DigiPlayer-XXXX` hotspot to reconfigure WiFi

### Player shows "Server Offline"

- Check if https://www.digireklaam.ee is accessible
- Verify firewall isn't blocking outbound HTTPS (port 443)

### Player stuck on "Waiting for registration"

- Verify you entered the correct Device ID (case-sensitive)
- Check the player exists in the Players list
- Make sure the player is in a group with an assigned playlist

### Content not updating

- Check the playlist is assigned to the player's group
- Try sending a "Refresh" command
- Check player logs: `sudo journalctl -u digiplayer -f`

### Black screen after registration

- Ensure playlist has media items
- Check media files uploaded successfully
- Video format might not be supported (use H.264 MP4)

### Need to reset the player

SSH into the player (if needed):
```bash
ssh pi@<player-ip>
# Password: digiplayer

# Reset registration
sudo digiplayer --reset

# Reboot
sudo reboot
```

---

## Technical Details

### Supported Hardware

- Raspberry Pi 3 Model B/B+
- Raspberry Pi 4 (all RAM variants)
- Raspberry Pi 5

### Default Credentials

- **Username**: `pi`
- **Password**: `digiplayer`
- **SSH**: Enabled by default

### Directory Structure

```
/opt/digiplayer/          # Application code
/etc/digiplayer/          # Configuration
/var/lib/digiplayer/media # Downloaded media files
/var/log/digiplayer/      # Application logs
```

### Configuration File

Located at `/etc/digiplayer/config.json`:

```json
{
  "server_url": "https://www.digireklaam.ee",
  "device_id": "DIG343EB7AE0A2",
  "player_id": 42,
  "heartbeat_interval": 30
}
```

### Service Management

```bash
# View status
sudo systemctl status digiplayer

# View logs
sudo journalctl -u digiplayer -f

# Restart service
sudo systemctl restart digiplayer

# Stop service
sudo systemctl stop digiplayer
```

### Network Ports

- **Outbound HTTPS (443)**: Server communication
- **Inbound (8080)**: Local web UI (registration screen)

---

## Building Your Own Image

The image is built automatically via GitHub Actions. To build manually:

1. Fork this repository
2. Push to `main` branch or create a tag `v1.x.x`
3. GitHub Actions builds the image (~2 hours)
4. Download from Actions artifacts or Releases

### Manual Build (Linux only)

```bash
# Clone pi-gen
git clone https://github.com/RPi-Distro/pi-gen.git
cd pi-gen

# Copy our configuration
# ... (see .github/workflows/build-image.yml for details)

# Build
sudo ./build.sh
```

---

## Development

For testing on a non-Pi system:

```bash
# Clone repository
git clone https://github.com/waltings/digiplayer-client.git
cd digiplayer-client

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with verbose output
python -m digiplayer.main -v

# Show device ID
python -m digiplayer.main --show-id

# Test server connection
python -m digiplayer.main --test-lookup
```

---

## License

MIT License

---

## Support

- **Issues**: https://github.com/waltings/digiplayer-client/issues
- **Server**: https://www.digireklaam.ee
