from machine import mem32
mem32[0x3FF480D4] = mem32[0x3FF480D4] & ~(1 << 31)  # disable brownout detector

from iotgame import IoTDevice
import config

print("[config] MQTT_HOST=%s MQTT_PORT=%s" % (config.MQTT_HOST, config.MQTT_PORT))
print("[config] CA_CERT_PATH=%s CERT_PATH=%s KEY_PATH=%s" % (
    getattr(config, "CA_CERT_PATH", "NOT SET"),
    getattr(config, "CERT_PATH", "NOT SET"),
    getattr(config, "KEY_PATH", "NOT SET"),
))

device = IoTDevice(
    device_id     = config.DEVICE_ID,
    mqtt_host     = config.MQTT_HOST,
    mqtt_port     = config.MQTT_PORT,
    wifi_ssid     = config.WIFI_SSID,
    wifi_password = config.WIFI_PASSWORD,
    mqtt_user     = getattr(config, "MQTT_USER", None),
    mqtt_password = getattr(config, "MQTT_PASSWORD", None),
    ca_cert_path  = getattr(config, "CA_CERT_PATH", None),
    cert_path     = getattr(config, "CERT_PATH", None),
    key_path      = getattr(config, "KEY_PATH", None),
)

for cfg in config.INPUTS:
    device.add_input_from_config(cfg)

device.run()
