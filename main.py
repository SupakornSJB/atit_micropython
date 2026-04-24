import config
from device import IoTDevice
from inputs.button_input import ButtonInput
from inputs.knob_input import KnobInput
from inputs.dht11_input import DHT11Input

device = IoTDevice(
    device_id=config.DEVICE_ID,
    mqtt_host=config.MQTT_HOST,
    mqtt_port=config.MQTT_PORT,
    mqtt_user=config.MQTT_USER,
    mqtt_password=config.MQTT_PASSWORD,
    wifi_ssid=config.WIFI_SSID,
    wifi_password=config.WIFI_PASSWORD,
)

_input_classes = {
    "button": lambda cfg: ButtonInput(
        cfg["slotId"], cfg["pin"], cfg.get("debounce_ms", 50)
    ),
    "knob": lambda cfg: KnobInput(
        cfg["slotId"], cfg["pin"],
        cfg.get("min_raw", 0), cfg.get("max_raw", 4095), cfg.get("dead_zone", 0.02)
    ),
    "dht11": lambda cfg: DHT11Input(
        cfg["slotId"], cfg["pin"], cfg.get("interval_ms", 2000)
    ),
}

for input_cfg in config.INPUTS:
    factory = _input_classes.get(input_cfg["type"])
    if factory:
        device.add_input(factory(input_cfg))
    else:
        print("Unknown input type:", input_cfg["type"])

device.run()