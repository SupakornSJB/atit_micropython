# ESP32 #1 — Player 1 ship (thumbstick) + round-control buttons + environment sensors.
# Copy to game/config.py, fill in the placeholders, and upload it to the board as :config.py.
# See ATITFinalProject/docs/setup.md for the full setup.

import iotgame.debug
iotgame.debug.DEBUG = False  # True prints every reading and publish to the serial console

WIFI_SSID     = "your-ssid"          # 2.4 GHz only — the ESP32 cannot join 5 GHz networks
WIFI_PASSWORD = "your-password"

# Must match the certificate CN (scripts/gen_device_cert.sh <DEVICE_ID>) and a device id in
# the relay's DeviceRegistry (ATITInfraNode/GameServer/appsettings.json)
DEVICE_ID = "esp32-01"

# MQTT broker — TLS is enabled automatically when the cert paths below are set
MQTT_HOST      = "your-broker-host"   # must match the broker certificate's CN
MQTT_PORT      = 8883
MQTT_USER      = None                 # identity comes from the client certificate
MQTT_PASSWORD  = None

# Files flashed onto the board by scripts/provision_device.py
CA_CERT_PATH  = "ca.crt"
CERT_PATH     = "device.crt"
KEY_PATH      = "device.key"

# slotId is the physical slot name only — what each slot does (move, fire, admin, environment)
# is decided by the relay's DeviceRegistry. Pin numbers are examples; match your wiring.
INPUTS = [
    {"slotId": "joystick-x",  "type": "knob",   "pin": 34,
     "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04},
    {"slotId": "joystick-y",  "type": "knob",   "pin": 35,
     "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04},
    {"slotId": "stick-click", "type": "button", "pin": 32, "debounce_ms": 50},

    # Operator buttons — start / end the round (higher debounce against accidental presses)
    {"slotId": "btn-1",       "type": "button", "pin": 14, "debounce_ms": 100},
    {"slotId": "btn-2",       "type": "button", "pin": 27, "debounce_ms": 100},

    # DHT11 publishes temperature as the value and humidity as auxiliary data
    {"slotId": "dht11",       "type": "dht11",  "pin": 4, "read_interval_ms": 2000},
    {"slotId": "distance",    "type": "ultrasonic", "trig_pin": 5, "echo_pin": 18,
     "min_cm": 2.0, "max_cm": 200.0, "dead_zone_cm": 2.0, "read_interval_ms": 100},
]
