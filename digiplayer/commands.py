"""Command execution for DigiPlayer client."""

import logging
import os
import subprocess
from typing import Optional

import requests

from .config import Config

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes commands received from the server."""

    def __init__(self, config: Config):
        self.config = config

    def execute(self, command: dict) -> bool:
        """Execute a command and acknowledge it."""
        cmd_id = command.get("id")
        cmd_type = command.get("command_type")
        cmd_data = command.get("command_data", {})

        logger.info(f"Executing command: {cmd_type} (id={cmd_id})")

        success = False
        error_message = None

        try:
            if cmd_type == "reboot":
                success = self._reboot()
            elif cmd_type == "refresh":
                success = self._refresh()
            elif cmd_type == "screen_on":
                success = self._screen_on()
            elif cmd_type == "screen_off":
                success = self._screen_off()
            elif cmd_type == "screenshot":
                success = self._screenshot()
            elif cmd_type == "update_playlist":
                success = self._update_playlist(cmd_data)
            else:
                error_message = f"Unknown command type: {cmd_type}"
                logger.warning(error_message)

        except Exception as e:
            error_message = str(e)
            logger.error(f"Command execution failed: {e}")

        # Acknowledge the command
        if cmd_id:
            self._acknowledge(cmd_id, success, error_message)

        return success

    def _acknowledge(self, command_id: int, success: bool, error_message: Optional[str] = None) -> None:
        """Acknowledge command execution to the server."""
        if not self.config.player_id:
            return

        url = f"{self.config.api_url}/players/{self.config.player_id}/commands/{command_id}/acknowledge"
        params = {"success": str(success).lower()}
        if error_message:
            params["error_message"] = error_message

        try:
            response = requests.post(url, params=params, timeout=10)
            if response.status_code == 200:
                logger.debug(f"Command {command_id} acknowledged")
            else:
                logger.warning(f"Failed to acknowledge command: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to acknowledge command: {e}")

    def _reboot(self) -> bool:
        """Reboot the device."""
        logger.info("Rebooting device...")
        try:
            subprocess.run(["sudo", "reboot"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Reboot failed: {e}")
            return False

    def _refresh(self) -> bool:
        """Refresh content (re-sync media)."""
        logger.info("Refreshing content...")
        # TODO: Implement media sync
        return True

    def _screen_on(self) -> bool:
        """Turn screen on."""
        logger.info("Turning screen on...")
        try:
            # Try vcgencmd (Raspberry Pi)
            subprocess.run(
                ["vcgencmd", "display_power", "1"],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try tvservice
                subprocess.run(
                    ["tvservice", "-p"],
                    check=True,
                    capture_output=True
                )
                return True
            except Exception as e:
                logger.error(f"Screen on failed: {e}")
                return False

    def _screen_off(self) -> bool:
        """Turn screen off."""
        logger.info("Turning screen off...")
        try:
            # Try vcgencmd (Raspberry Pi)
            subprocess.run(
                ["vcgencmd", "display_power", "0"],
                check=True,
                capture_output=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try tvservice
                subprocess.run(
                    ["tvservice", "-o"],
                    check=True,
                    capture_output=True
                )
                return True
            except Exception as e:
                logger.error(f"Screen off failed: {e}")
                return False

    def _screenshot(self) -> bool:
        """Capture and upload a screenshot."""
        logger.info("Capturing screenshot...")
        screenshot_path = "/tmp/screenshot.png"

        try:
            # Capture screenshot using raspi2png or scrot
            try:
                subprocess.run(
                    ["raspi2png", "-p", screenshot_path],
                    check=True,
                    capture_output=True
                )
            except FileNotFoundError:
                subprocess.run(
                    ["scrot", screenshot_path],
                    check=True,
                    capture_output=True,
                    env={**os.environ, "DISPLAY": ":0"}
                )

            # Upload screenshot
            # TODO: Implement screenshot upload endpoint
            logger.info(f"Screenshot saved to {screenshot_path}")
            return True

        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    def _update_playlist(self, data: dict) -> bool:
        """Update the current playlist."""
        logger.info(f"Updating playlist: {data}")
        # TODO: Implement playlist update
        return True
