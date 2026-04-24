WIFI_SSID     = "your-ssid"
WIFI_PASSWORD = "your-password"

# Device identity — must be unique per physical device
DEVICE_ID = "esp32-01"

# MQTT Broker
MQTT_HOST      = "your-broker-host"
MQTT_PORT      = 1883
MQTT_USER      = ""
MQTT_PASSWORD  = ""
MQTT_CLIENT_ID = DEVICE_ID

# Topic template — must match server wildcard: game/devices/+/slot/+
MQTT_TOPIC_TEMPLATE = "game/devices/{device_id}/slot/{slot_id}"

# Inputs — slotId is a physical identifier only (e.g. btn1, knob1)
# Semantic name and player assignment live in the ASP.NET device registry
INPUTS = [
    {"slotId": "btn1",  "type": "button", "pin": 14, "debounce_ms": 50},
    # {"slotId": "btn2",  "type": "button", "pin": 27, "debounce_ms": 50},
    # {"slotId": "knob1", "type": "knob",   "pin": 34, "min_raw": 0, "max_raw": 4095, "dead_zone": 0.02},
    # {"slotId": "dht1",  "type": "dht11",  "pin": 4},
]