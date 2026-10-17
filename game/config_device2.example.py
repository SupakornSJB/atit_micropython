import iotgame.debug
iotgame.debug.DEBUG = True

WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"

# Device identity — must match ASP.NET device registry
DEVICE_ID = "esp32-device-2"

# MQTT Broker
MQTT_HOST      = "your-broker-host"
MQTT_PORT      = 1883
MQTT_USER      = None
MQTT_PASSWORD  = None

# ESP32 #2 — Player 2 (knob for absolute X position + digital up/down/fire)
# slotId is a physical hardware identifier only; semantic mapping lives in ASP.NET registry
INPUTS = [
    # Knob maps to absolute horizontal position (0.0 = left, 1.0 = right)
    {"slotId": "knob",     "type": "knob",   "pin": 34,
     "min_raw": 0, "max_raw": 4095, "dead_zone": 0.02},
    {"slotId": "btn-up",   "type": "button", "pin": 14, "debounce_ms": 50},
    {"slotId": "btn-down", "type": "button", "pin": 27, "debounce_ms": 50},
    {"slotId": "btn-fire", "type": "button", "pin": 32, "debounce_ms": 50},
]