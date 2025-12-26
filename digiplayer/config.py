"""Configuration management for DigiPlayer client."""

import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from .utils import generate_device_id

logger = logging.getLogger(__name__)

# Default paths
CONFIG_DIR = Path("/etc/digiplayer")
CONFIG_FILE = CONFIG_DIR / "config.json"
MEDIA_DIR = Path("/var/lib/digiplayer/media")
LOG_DIR = Path("/var/log/digiplayer")

# Development paths (when not running as root)
DEV_CONFIG_DIR = Path.home() / ".digiplayer"
DEV_CONFIG_FILE = DEV_CONFIG_DIR / "config.json"
DEV_MEDIA_DIR = DEV_CONFIG_DIR / "media"
DEV_LOG_DIR = DEV_CONFIG_DIR / "logs"


@dataclass
class Config:
    """DigiPlayer configuration."""

    # Server settings
    server_url: str = "https://www.digireklaam.ee"
    api_prefix: str = "/api/v1"

    # Device identification
    device_id: str = ""
    player_id: Optional[int] = None  # Set after registration

    # Timing
    heartbeat_interval: int = 30  # seconds

    # Display settings
    display_timeout: int = 5  # seconds per image

    # Paths (will be set based on environment)
    media_dir: str = ""
    log_dir: str = ""

    def __post_init__(self):
        """Generate device ID if not set."""
        if not self.device_id:
            self.device_id = generate_device_id()

    @property
    def api_url(self) -> str:
        """Full API URL."""
        return f"{self.server_url}{self.api_prefix}"

    @property
    def heartbeat_url(self) -> str:
        """Heartbeat endpoint URL."""
        if self.player_id:
            return f"{self.api_url}/players/{self.player_id}/heartbeat"
        return ""

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def get_config_paths() -> tuple[Path, Path, Path]:
    """Get appropriate config paths based on environment."""
    # Use system paths if running as root, otherwise dev paths
    if os.geteuid() == 0:
        return CONFIG_DIR, MEDIA_DIR, LOG_DIR
    else:
        return DEV_CONFIG_DIR, DEV_MEDIA_DIR, DEV_LOG_DIR


def load_config() -> Config:
    """Load configuration from file or create default."""
    config_dir, media_dir, log_dir = get_config_paths()
    config_file = config_dir / "config.json"

    # Ensure directories exist
    config_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    config = Config(
        media_dir=str(media_dir),
        log_dir=str(log_dir)
    )

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
                config = Config.from_dict(data)
                config.media_dir = str(media_dir)
                config.log_dir = str(log_dir)
                logger.info(f"Loaded config from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    else:
        # Save default config
        save_config(config)
        logger.info(f"Created default config at {config_file}")

    return config


def save_config(config: Config) -> None:
    """Save configuration to file."""
    config_dir, _, _ = get_config_paths()
    config_file = config_dir / "config.json"

    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_file, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info(f"Saved config to {config_file}")
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
