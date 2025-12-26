"""Registration service for DigiPlayer client.

Polls the server to check if the device has been registered.
Once registered, saves the player_id and starts normal operation.
"""

import logging
import time
from typing import Optional, Callable

import requests

from .config import Config, save_config
from .utils import get_ip_address

logger = logging.getLogger(__name__)


class RegistrationService:
    """Service for checking and handling device registration."""

    def __init__(self, config: Config, on_registered: Optional[Callable] = None):
        self.config = config
        self.on_registered = on_registered
        self.running = False
        self.poll_interval = 5  # seconds
        self.last_status = {
            "internet": False,
            "server": False,
            "registered": False,
            "ip_address": None,
            "error": None
        }

    @property
    def lookup_url(self) -> str:
        """URL for the lookup endpoint."""
        return f"{self.config.api_url}/players/lookup"

    def check_internet(self) -> bool:
        """Check if internet is available."""
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except Exception:
            try:
                requests.get("https://1.1.1.1", timeout=5)
                return True
            except Exception:
                return False

    def check_server(self) -> bool:
        """Check if DigiPlayer server is reachable."""
        try:
            response = requests.get(
                f"{self.config.server_url}/api/v1/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            # Try the lookup endpoint as fallback
            try:
                response = requests.get(
                    self.lookup_url,
                    params={"unique_id": "test"},
                    timeout=5
                )
                return response.status_code in [200, 404]
            except Exception:
                return False

    def check_registration(self) -> dict:
        """Check if this device is registered on the server.

        Returns:
            dict with registration info or error
        """
        try:
            response = requests.get(
                self.lookup_url,
                params={"unique_id": self.config.device_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return {
                    "registered": False,
                    "error": f"HTTP {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {"registered": False, "error": "Timeout"}
        except requests.exceptions.ConnectionError:
            return {"registered": False, "error": "Connection error"}
        except Exception as e:
            return {"registered": False, "error": str(e)}

    def update_status(self) -> dict:
        """Update and return current status."""
        self.last_status["ip_address"] = get_ip_address()
        self.last_status["internet"] = self.check_internet()

        if self.last_status["internet"]:
            self.last_status["server"] = self.check_server()
        else:
            self.last_status["server"] = False

        if self.last_status["server"]:
            result = self.check_registration()
            self.last_status["registered"] = result.get("registered", False)
            self.last_status["error"] = result.get("error")

            if self.last_status["registered"]:
                # Save player_id to config
                player_id = result.get("player_id")
                if player_id and player_id != self.config.player_id:
                    logger.info(f"Device registered! Player ID: {player_id}")
                    self.config.player_id = player_id
                    save_config(self.config)

                    # Include all registration info
                    self.last_status["player_id"] = player_id
                    self.last_status["name"] = result.get("name")
                    self.last_status["group_name"] = result.get("group_name")
                    self.last_status["playlist_name"] = result.get("playlist_name")
        else:
            self.last_status["registered"] = False

        return self.last_status

    def poll(self) -> None:
        """Run registration polling loop."""
        self.running = True
        logger.info(f"Starting registration polling (interval: {self.poll_interval}s)")
        logger.info(f"Device ID: {self.config.device_id}")
        logger.info(f"Lookup URL: {self.lookup_url}")

        while self.running:
            status = self.update_status()

            if status["registered"]:
                logger.info("Device is registered!")
                if self.on_registered:
                    self.on_registered(status)
                break

            # Log status periodically
            if status["error"]:
                logger.warning(f"Registration check failed: {status['error']}")
            else:
                logger.debug(f"Waiting for registration... Internet: {status['internet']}, Server: {status['server']}")

            time.sleep(self.poll_interval)

    def stop(self) -> None:
        """Stop the polling loop."""
        self.running = False
        logger.info("Registration polling stopped")

    def get_status_for_ui(self) -> dict:
        """Get status formatted for UI display."""
        return {
            "device_id": self.config.device_id,
            "server_url": self.config.server_url,
            "internet_connected": self.last_status["internet"],
            "server_online": self.last_status["server"],
            "registered": self.last_status["registered"],
            "ip_address": self.last_status["ip_address"],
            "error": self.last_status["error"],
            "player_name": self.last_status.get("name"),
            "group_name": self.last_status.get("group_name"),
            "playlist_name": self.last_status.get("playlist_name"),
        }
