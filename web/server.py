"""Local web server for DigiPlayer UI.

Provides:
- Registration screen with Device ID
- Status display
- WiFi configuration (when in hotspot mode)
"""

import logging
import os
from pathlib import Path

from flask import Flask, render_template, jsonify, request

logger = logging.getLogger(__name__)

# Get the web directory path
WEB_DIR = Path(__file__).parent
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR)
)

# Will be set by main.py
registration_service = None
config = None


def init_app(reg_service, app_config):
    """Initialize the web app with services."""
    global registration_service, config
    registration_service = reg_service
    config = app_config


@app.route("/")
def index():
    """Main page - shows registration or status screen."""
    status = {}
    if registration_service:
        status = registration_service.get_status_for_ui()

    if status.get("registered"):
        return render_template("status.html", status=status)
    else:
        return render_template("registration.html", status=status)


@app.route("/api/status")
def api_status():
    """API endpoint for getting current status (for AJAX polling)."""
    if registration_service:
        # Update status before returning
        registration_service.update_status()
        return jsonify(registration_service.get_status_for_ui())
    return jsonify({"error": "Service not initialized"})


@app.route("/wifi")
def wifi_setup():
    """WiFi configuration page."""
    return render_template("wifi_setup.html")


@app.route("/api/wifi/scan")
def wifi_scan():
    """Scan for available WiFi networks."""
    try:
        import subprocess
        result = subprocess.run(
            ["sudo", "iwlist", "wlan0", "scan"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Parse output for SSIDs
        networks = []
        for line in result.stdout.split("\n"):
            if "ESSID:" in line:
                ssid = line.split("ESSID:")[1].strip().strip('"')
                if ssid and ssid not in networks:
                    networks.append(ssid)

        return jsonify({"networks": networks})
    except Exception as e:
        logger.error(f"WiFi scan failed: {e}")
        return jsonify({"error": str(e), "networks": []})


@app.route("/api/wifi/connect", methods=["POST"])
def wifi_connect():
    """Connect to a WiFi network."""
    data = request.json
    ssid = data.get("ssid")
    password = data.get("password")

    if not ssid:
        return jsonify({"error": "SSID required"}), 400

    try:
        # Write wpa_supplicant config
        wpa_config = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
'''
        config_path = "/etc/wpa_supplicant/wpa_supplicant.conf"

        # Append to existing config
        with open(config_path, "a") as f:
            f.write(wpa_config)

        # Restart networking
        import subprocess
        subprocess.run(["sudo", "wpa_cli", "-i", "wlan0", "reconfigure"], check=True)

        return jsonify({"success": True, "message": "WiFi configured. Reconnecting..."})
    except Exception as e:
        logger.error(f"WiFi connect failed: {e}")
        return jsonify({"error": str(e)}), 500


def run_server(host="0.0.0.0", port=8080, debug=False):
    """Run the Flask server."""
    logger.info(f"Starting web server on {host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_server(debug=True)
