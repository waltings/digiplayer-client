"""Utility functions for DigiPlayer client."""

import hashlib
import logging
import os
import re
import socket
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def get_cpu_serial() -> str:
    """Get Raspberry Pi CPU serial number from /proc/cpuinfo."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("Serial"):
                    return line.split(":")[1].strip()
    except FileNotFoundError:
        pass

    # Fallback for non-Pi systems (development)
    return "0000000000000000"


def get_mac_address() -> str:
    """Get primary network interface MAC address."""
    # Try common interface names
    for iface in ["eth0", "wlan0", "en0", "enp0s3"]:
        try:
            path = f"/sys/class/net/{iface}/address"
            if os.path.exists(path):
                with open(path, "r") as f:
                    return f.read().strip().replace(":", "")
        except Exception:
            pass

    # Fallback: use uuid-based MAC
    import uuid
    mac = uuid.getnode()
    return format(mac, "012x")


def get_ip_address() -> str:
    """Get the device's IP address."""
    try:
        # Connect to external server to determine IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "0.0.0.0"


def get_screen_resolution() -> str:
    """Get current screen resolution."""
    try:
        # Try fbset first (framebuffer)
        result = subprocess.run(
            ["fbset", "-s"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            match = re.search(r'geometry (\d+) (\d+)', result.stdout)
            if match:
                return f"{match.group(1)}x{match.group(2)}"

        # Try xrandr
        result = subprocess.run(
            ["xrandr", "--current"],
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "DISPLAY": ":0"}
        )
        if result.returncode == 0:
            match = re.search(r'current (\d+) x (\d+)', result.stdout)
            if match:
                return f"{match.group(1)}x{match.group(2)}"
    except Exception as e:
        logger.debug(f"Could not get resolution: {e}")

    return "unknown"


def get_storage_info() -> tuple[int, int]:
    """Get storage usage in bytes. Returns (used, total)."""
    try:
        statvfs = os.statvfs("/")
        total = statvfs.f_frsize * statvfs.f_blocks
        free = statvfs.f_frsize * statvfs.f_bavail
        used = total - free
        return used, total
    except Exception:
        return 0, 0


def generate_device_id() -> str:
    """Generate unique device ID based on hardware."""
    cpu_serial = get_cpu_serial()
    mac = get_mac_address()

    unique = f"{cpu_serial}-{mac}"
    hash_value = hashlib.md5(unique.encode()).hexdigest()[:12].upper()
    return f"DIG{hash_value}"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def is_raspberry_pi() -> bool:
    """Check if running on a Raspberry Pi."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            return "Raspberry Pi" in f.read() or "BCM" in f.read()
    except FileNotFoundError:
        return False
