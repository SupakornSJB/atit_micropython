import config
from device import IoTDevice

device = IoTDevice(
    device_id=config.DEVICE_ID,
    mqtt_host=config.MQTT_HOST,
    mqtt_port=config.MQTT_PORT,
    mqtt_user=config.MQTT_USER,
    mqtt_password=config.MQTT_PASSWORD,
    wifi_ssid=config.WIFI_SSID,
    wifi_password=config.WIFI_PASSWORD,
)

for input_cfg in config.INPUTS:
    device.add_input(device._build_input(input_cfg))

device.run()