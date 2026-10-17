#!/usr/bin/env python3
"""
Usage: python scripts/provision_device.py <device-id> [--port /dev/ttyUSB0]
Flashes ca.crt, device.crt, device.key onto the ESP32 filesystem.
"""
import argparse
import subprocess
import sys
from pathlib import Path


def flash_file(port: str, local_path: Path, remote_path: str):
    result = subprocess.run(
        ["mpremote", "connect", port, "cp", str(local_path), f":{remote_path}"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR flashing {local_path}: {result.stderr}")
        sys.exit(1)
    print(f"  Flashed {local_path} → :{remote_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device_id", help="e.g. esp32-device-1")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    args = parser.parse_args()

    cert_dir = Path("certs") / args.device_id
    if not cert_dir.exists():
        print(f"ERROR: {cert_dir} not found. Run gen_device_cert.sh first.")
        sys.exit(1)

    print(f"Provisioning {args.device_id} on {args.port}...")
    flash_file(args.port, Path("certs/ca.crt"),        "ca.crt")
    flash_file(args.port, cert_dir / "device.crt",     "device.crt")
    flash_file(args.port, cert_dir / "device.key",     "device.key")
    print("Done. Verify with: mpremote connect <port> ls")


if __name__ == "__main__":
    main()