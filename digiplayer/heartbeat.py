"""Heartbeat service for DigiPlayer client."""

import logging
import time
from typing import Callable, Optional

import requests

from .config import Config, save_config
from .utils import get_ip_address, get_mac_address, get_screen_resolution, get_storage_info

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Service for sending heartbeats to the server."""

    def __init__(self, config: Config, command_handler: Optional[Callable] = None):
        self.config = config
        self.command_handler = command_handler
        self.running = False
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0
        self.registered = False

    def send_heartbeat(self) -> dict:
        """Send a single heartbeat to the server."""
        if not self.config.player_id:
            logger.warning("Player ID not set - cannot send heartbeat")
            return {"status": "error", "message": "Not registered"}

        storage_used, storage_total = get_storage_info()

        payload = {
            "unique_id": self.config.device_id,
            "status": "online",
            "storage_used": storage_used,
            "storage_total": storage_total,
            "ip_address": get_ip_address(),
            "mac_address": get_mac_address(),
            "screen_resolution": get_screen_resolution(),
        }

        try:
            response = requests.post(
                self.config.heartbeat_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                self.consecutive_failures = 0
                self.last_error = None

                # Process any pending commands
                commands = data.get("commands", [])
                if commands and self.command_handler:
                    for cmd in commands:
                        self.command_handler(cmd)

                logger.debug(f"Heartbeat OK - {len(commands)} commands")
                return data

            elif response.status_code == 404:
                logger.error("Player not found on server - check registration")
                self.last_error = "Player not found"
                return {"status": "error", "message": "Player not found"}

            else:
                self.last_error = f"HTTP {response.status_code}"
                logger.error(f"Heartbeat failed: {response.status_code} - {response.text}")
                return {"status": "error", "message": self.last_error}

        except requests.exceptions.Timeout:
            self.consecutive_failures += 1
            self.last_error = "Timeout"
            logger.warning("Heartbeat timeout")
            return {"status": "error", "message": "Timeout"}

        except requests.exceptions.ConnectionError as e:
            self.consecutive_failures += 1
            self.last_error = "Connection error"
            logger.warning(f"Connection error: {e}")
            return {"status": "error", "message": "Connection error"}

        except Exception as e:
            self.consecutive_failures += 1
            self.last_error = str(e)
            logger.error(f"Heartbeat error: {e}")
            return {"status": "error", "message": str(e)}

    def check_registration(self) -> bool:
        """Check if player is registered on the server."""
        if not self.config.player_id:
            return False

        try:
            # Try to send heartbeat - if it works, we're registered
            response = self.send_heartbeat()
            return response.get("status") == "ok"
        except Exception:
            return False

    def find_player_id(self) -> Optional[int]:
        """Try to find player ID by unique_id on server.

        Note: This requires an API endpoint to lookup by unique_id.
        For now, player_id must be set manually after registration.
        """
        # TODO: Implement lookup endpoint on backend
        logger.info(f"Device ID: {self.config.device_id}")
        logger.info("Register this device in the web UI and set player_id in config")
        return None

    def run(self, interval: Optional[int] = None) -> None:
        """Run the heartbeat loop."""
        if interval is None:
            interval = self.config.heartbeat_interval

        self.running = True
        logger.info(f"Starting heartbeat service (interval: {interval}s)")
        logger.info(f"Device ID: {self.config.device_id}")
        logger.info(f"Server: {self.config.server_url}")

        if self.config.player_id:
            logger.info(f"Player ID: {self.config.player_id}")
        else:
            logger.warning("Player ID not set - heartbeat disabled until registered")

        while self.running:
            if self.config.player_id:
                self.send_heartbeat()

            time.sleep(interval)

    def stop(self) -> None:
        """Stop the heartbeat loop."""
        self.running = False
        logger.info("Heartbeat service stopped")
