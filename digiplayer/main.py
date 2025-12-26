#!/usr/bin/env python3
"""DigiPlayer V1 - Raspberry Pi Digital Signage Client.

Main entry point for the DigiPlayer client application.
"""

import argparse
import logging
import os
import signal
import sys
import threading
import time
from typing import Optional

from . import __version__
from .config import load_config, save_config, Config
from .commands import CommandExecutor
from .heartbeat import HeartbeatService
from .utils import setup_logging, is_raspberry_pi

logger = logging.getLogger(__name__)


class DigiPlayer:
    """Main DigiPlayer application."""

    def __init__(self, config: Config):
        self.config = config
        self.command_executor = CommandExecutor(config)
        self.heartbeat_service = HeartbeatService(
            config,
            command_handler=self.command_executor.execute
        )
        self.running = False
        self._heartbeat_thread: Optional[threading.Thread] = None

    def display_device_id(self) -> None:
        """Display device ID on screen and console."""
        device_id = self.config.device_id

        # Print to console
        print("\n" + "=" * 50)
        print("  DIGIPLAYER V1")
        print("=" * 50)
        print(f"\n  Device ID: {device_id}\n")
        print("  Register this ID in the DigiPlayer web UI")
        print("  at: " + self.config.server_url)
        print("\n" + "=" * 50 + "\n")

        if self.config.player_id:
            print(f"  Player ID: {self.config.player_id} (registered)")
        else:
            print("  Status: Not registered yet")
            print("  After registration, set player_id in config")

        print("\n")

        # TODO: Display on screen using framebuffer or X11
        self._display_on_screen(device_id)

    def _display_on_screen(self, device_id: str) -> None:
        """Display device ID on the screen (for registration)."""
        if not is_raspberry_pi():
            logger.debug("Not on Raspberry Pi, skipping screen display")
            return

        try:
            # Simple console display using fbi or Plymouth
            # For MVP, we just log to console which appears on screen in kiosk mode
            pass
        except Exception as e:
            logger.debug(f"Could not display on screen: {e}")

    def start_heartbeat(self) -> None:
        """Start the heartbeat service in a background thread."""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        self._heartbeat_thread = threading.Thread(
            target=self.heartbeat_service.run,
            daemon=True
        )
        self._heartbeat_thread.start()
        logger.info("Heartbeat thread started")

    def run(self) -> None:
        """Run the main application loop."""
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        # Display device ID
        self.display_device_id()

        # Start heartbeat service
        self.start_heartbeat()

        # Main loop - keep running
        logger.info("DigiPlayer running. Press Ctrl+C to stop.")
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.stop()

    def stop(self) -> None:
        """Stop the application."""
        logger.info("Stopping DigiPlayer...")
        self.running = False
        self.heartbeat_service.stop()

    def _handle_signal(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.stop()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DigiPlayer V1 - Raspberry Pi Digital Signage Client"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"DigiPlayer V{__version__}"
    )
    parser.add_argument(
        "--show-id",
        action="store_true",
        help="Show device ID and exit"
    )
    parser.add_argument(
        "--set-player-id",
        type=int,
        metavar="ID",
        help="Set the player ID after registration"
    )
    parser.add_argument(
        "--set-server",
        type=str,
        metavar="URL",
        help="Set the server URL"
    )
    parser.add_argument(
        "--test-heartbeat",
        action="store_true",
        help="Send a single test heartbeat and exit"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logger.info(f"DigiPlayer V{__version__} starting...")

    # Load configuration
    config = load_config()

    # Handle configuration commands
    if args.set_player_id:
        config.player_id = args.set_player_id
        save_config(config)
        print(f"Player ID set to: {args.set_player_id}")
        return

    if args.set_server:
        config.server_url = args.set_server
        save_config(config)
        print(f"Server URL set to: {args.set_server}")
        return

    if args.show_id:
        print(f"Device ID: {config.device_id}")
        return

    if args.test_heartbeat:
        if not config.player_id:
            print(f"Error: player_id not set. Device ID is: {config.device_id}")
            print("Register this device and then run:")
            print(f"  digiplayer --set-player-id <ID>")
            sys.exit(1)

        heartbeat = HeartbeatService(config)
        result = heartbeat.send_heartbeat()
        print(f"Heartbeat result: {result}")
        return

    # Run the main application
    player = DigiPlayer(config)
    player.run()


if __name__ == "__main__":
    main()
