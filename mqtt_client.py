import ujson
import utime
from umqtt.simple import MQTTClient as _MQTTClient
import config


_client = None
_use_tls = config.MQTT_PORT == 8883


def connect():
    global _client
    ssl_params = {"server_side": False} if _use_tls else None
    _client = _MQTTClient(
        config.MQTT_CLIENT_ID,
        config.MQTT_HOST,
        port=config.MQTT_PORT,
        user=config.MQTT_USER or None,
        password=config.MQTT_PASSWORD or None,
        ssl=_use_tls,
        ssl_params=ssl_params,
    )
    _client.connect()
    print("MQTT connected")


def publish(topic, payload_dict):
    global _client
    data = ujson.dumps(payload_dict)
    try:
        _client.publish(topic, data)
    except Exception:
        print("MQTT publish failed, reconnecting...")
        try:
            connect()
            _client.publish(topic, data)
        except Exception as e:
            print("MQTT reconnect failed:", e)
            raise