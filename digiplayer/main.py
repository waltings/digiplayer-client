#!/usr/bin/env python3
"""DigiPlayer V1 - Raspberry Pi Digital Signage Client.

Main entry point for the DigiPlayer client application.
Runs as a service on Raspberry Pi, displaying registration screen
until the device is registered, then plays assigned content.
"""

import argparse
import logging
import signal
import sys
import threading
import time
from typing import Optional, Any

from . import __version__
from .config import load_config, save_config, Config
from .commands import CommandExecutor
from .heartbeat import HeartbeatService
from .registration import RegistrationService
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
        self.registration_service = RegistrationService(
            config,
            on_registered=self._on_registered
        )
        self.running = False
        self._web_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._registration_thread: Optional[threading.Thread] = None

    def _on_registered(self, status: dict) -> None:
        """Called when device becomes registered."""
        logger.info(f"Device registered! Player ID: {status.get('player_id')}")
        logger.info(f"Name: {status.get('name')}, Group: {status.get('group_name')}")

        # Start heartbeat service
        self.start_heartbeat()

    def start_web_server(self) -> None:
        """Start the local web UI server."""
        try:
            from web.server import init_app, run_server

            # Initialize with our services
            init_app(self.registration_service, self.config)

            # Run in background thread
            self._web_thread = threading.Thread(
                target=run_server,
                kwargs={"host": "0.0.0.0", "port": 8080, "debug": False},
                daemon=True
            )
            self._web_thread.start()
            logger.info("Web UI server started on port 8080")
        except ImportError as e:
            logger.warning(f"Web server not available: {e}")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")

    def start_registration_polling(self) -> None:
        """Start registration polling in background."""
        if self.config.player_id:
            logger.info("Already registered, skipping registration polling")
            return

        self._registration_thread = threading.Thread(
            target=self.registration_service.poll,
            daemon=True
        )
        self._registration_thread.start()
        logger.info("Registration polling started")

    def start_heartbeat(self) -> None:
        """Start the heartbeat service in a background thread."""
        if not self.config.player_id:
            logger.warning("Cannot start heartbeat - not registered")
            return

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        self._heartbeat_thread = threading.Thread(
            target=self.heartbeat_service.run,
            daemon=True
        )
        self._heartbeat_thread.start()
        logger.info("Heartbeat service started")

    def display_info(self) -> None:
        """Display device information on console."""
        print("\n" + "=" * 50)
        print("  DIGIPLAYER V1")
        print("=" * 50)
        print(f"\n  Device ID: {self.config.device_id}")
        print(f"  Server:    {self.config.server_url}")

        if self.config.player_id:
            print(f"  Player ID: {self.config.player_id} (registered)")
            print(f"  Status:    Ready")
        else:
            print(f"  Status:    Waiting for registration...")
            print(f"\n  Register at: {self.config.server_url}/players")

        print("\n  Web UI: http://localhost:8080")
        print("=" * 50 + "\n")

    def run(self, service_mode: bool = False) -> None:
        """Run the main application.

        Args:
            service_mode: If True, runs as background service (no interactive output)
        """
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        if not service_mode:
            self.display_info()

        # Start web UI server
        self.start_web_server()

        # Check if already registered
        if self.config.player_id:
            logger.info(f"Device already registered (Player ID: {self.config.player_id})")
            self.start_heartbeat()
        else:
            # Start registration polling
            self.start_registration_polling()

        # Main loop
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
        self.registration_service.stop()

    def _handle_signal(self, signum: int, frame: Any) -> None:
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
        "--service",
        action="store_true",
        help="Run in service mode (background, no interactive output)"
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
        help="Set the player ID manually"
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
    parser.add_argument(
        "--test-lookup",
        action="store_true",
        help="Test the registration lookup and exit"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset registration (clear player_id)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logger.info(f"DigiPlayer V{__version__} starting...")

    # Load configuration
    config = load_config()

    # Handle configuration commands
    if args.reset:
        config.player_id = None
        save_config(config)
        print("Registration reset. Device ID remains:", config.device_id)
        return

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
        if config.player_id:
            print(f"Player ID: {config.player_id}")
        return

    if args.test_lookup:
        reg = RegistrationService(config)
        print(f"Testing lookup for: {config.device_id}")
        print(f"URL: {reg.lookup_url}")
        result = reg.check_registration()
        print(f"Result: {result}")
        return

    if args.test_heartbeat:
        if not config.player_id:
            print(f"Error: player_id not set. Device ID is: {config.device_id}")
            print("Register this device first or use --set-player-id")
            sys.exit(1)

        heartbeat = HeartbeatService(config)
        result = heartbeat.send_heartbeat()
        print(f"Heartbeat result: {result}")
        return

    # Run the main application
    player = DigiPlayer(config)
    player.run(service_mode=args.service)


if __name__ == "__main__":
    main()
