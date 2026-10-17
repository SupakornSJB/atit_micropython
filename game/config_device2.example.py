# ESP32 #2 — Player 2 ship (knob for horizontal position + up / down / fire buttons).
# Copy to game/config.py, fill in the placeholders, and upload it to the board as :config.py.
# See ATITFinalProject/docs/setup.md for the full setup.

import iotgame.debug
iotgame.debug.DEBUG = False  # True prints every reading and publish to the serial console

WIFI_SSID     = "your-ssid"          # 2.4 GHz only — the ESP32 cannot join 5 GHz networks
WIFI_PASSWORD = "your-password"

# Must match the certificate CN (scripts/gen_device_cert.sh <DEVICE_ID>) and a device id in
# the relay's DeviceRegistry (ATITInfraNode/GameServer/appsettings.json)
DEVICE_ID = "esp32-02"

# MQTT broker — TLS is enabled automatically when the cert paths below are set
MQTT_HOST      = "your-broker-host"   # must match the broker certificate's CN
MQTT_PORT      = 8883
MQTT_USER      = None                 # identity comes from the client certificate
MQTT_PASSWORD  = None

# Files flashed onto the board by scripts/provision_device.py
CA_CERT_PATH  = "ca.crt"
CERT_PATH     = "device.crt"
KEY_PATH      = "device.key"

# slotId is the physical slot name only — the relay's DeviceRegistry maps
# btn-1 → move up, btn-2 → move down, btn-3 → fire, knob → horizontal position.
INPUTS = [
    {"slotId": "btn-1", "type": "button", "pin": 16, "debounce_ms": 50, "pull_up": False},
    {"slotId": "btn-2", "type": "button", "pin": 17, "debounce_ms": 50, "pull_up": False},
    {"slotId": "btn-3", "type": "button", "pin": 18, "debounce_ms": 50, "pull_up": False},
    {"slotId": "knob",  "type": "knob",   "pin": 32,
     "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04},
]
