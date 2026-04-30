import ujson
from umqtt.simple import MQTTClient as _MQTTClient


class MqttClient:
    def __init__(self, client_id, host, port, user, password):
        self._client_id = client_id
        self._host = host
        self._port = port
        self._user = user or None
        self._password = password or None
        self._use_tls = port == 8883
        self._client = None

    def connect(self):
        ssl_params = {"server_side": False} if self._use_tls else None
        self._client = _MQTTClient(
            self._client_id,
            self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            ssl=self._use_tls,
            ssl_params=ssl_params,
        )
        self._client.connect()
        print("MQTT connected")

    def publish(self, topic, payload_dict):
        data = ujson.dumps(payload_dict)
        try:
            self._client.publish(topic, data)
        except Exception:
            print("MQTT publish failed, reconnecting...")
            try:
                self.connect()
                self._client.publish(topic, data)
            except Exception as e:
                print("MQTT reconnect failed:", e)
                raise
