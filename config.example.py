DEBUG = False  # set True to enable verbose serial output from all input classes

WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"

# Device identity — must be unique per physical device
DEVICE_ID = "esp32-01"

# MQTT Broker
MQTT_HOST      = "your-broker-host"
MQTT_PORT      = 1883
MQTT_USER      = None
MQTT_PASSWORD  = None
MQTT_CLIENT_ID = DEVICE_ID

CA_CERT_PATH  = "ca.crt"
CERT_PATH     = "device.crt"
KEY_PATH      = "device.key"

# Topic template — must match server wildcard: game/devices/+/slot/+
MQTT_TOPIC_TEMPLATE = "game/devices/{device_id}/slot/{slot_id}"

# --- Phase 3 device examples ---

# Player ship device (thumbstick + fire button)
# DEVICE_ID = "esp32-p1-ship"
# INPUTS = [
#     {"slotId": "joystick-x",  "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04},
#     {"slotId": "joystick-y",  "type": "knob",   "pin": 35, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.04},
#     {"slotId": "stick-click", "type": "button", "pin": 32, "debounce_ms": 50},
#     {"slotId": "fire",        "type": "button", "pin": 14, "debounce_ms": 50},
# ]

# Stage controller device (DHT11 + ultrasonic + button)
# DEVICE_ID = "esp32-stage"
# INPUTS = [
#     {"slotId": "temp",      "type": "dht11",      "pin": 4,
#      "read_interval_ms": 2000},  # slotId matches sensor type — publishes both temp (value) and humidity (auxiliary)
#     {"slotId": "distance",  "type": "ultrasonic",  "trig_pin": 5, "echo_pin": 18,
#      "min_cm": 2.0, "max_cm": 200.0, "dead_zone_cm": 2.0, "read_interval_ms": 100},
#     {"slotId": "pipe-flip", "type": "button",      "pin": 14, "debounce_ms": 50},
# ]

# Boss bird device (single flap button)
# DEVICE_ID = "esp32-p3-bird"
# INPUTS = [
#     {"slotId": "flap", "type": "button", "pin": 14, "debounce_ms": 50},
# ]

# Default minimal config
INPUTS = [
    {"slotId": "btn1", "type": "button", "pin": 14, "debounce_ms": 50},
]