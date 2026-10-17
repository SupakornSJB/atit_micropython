import ujson
from umqtt.simple import MQTTClient as _MQTTClient


class MqttClient:
    def __init__(self, client_id, host, port, user=None, password=None,
                 ca_cert_path=None, cert_path=None, key_path=None):
        self._client_id = client_id
        self._host = host
        self._port = port
        self._user = user or None
        self._password = password or None
        self._use_tls = ca_cert_path is not None or cert_path is not None
        self._ca_cert = self._load_file(ca_cert_path)
        self._cert = self._load_file(cert_path)
        self._key = self._load_file(key_path)
        self._client = None

    def _load_file(self, path):
        if path is None:
            return None
        try:
            with open(path, 'rb') as f:
                data = f.read()
            print("[MQTT] Loaded %s (%d bytes)" % (path, len(data)))
            return data
        except OSError as e:
            print("[MQTT] Could not load %s: %s" % (path, e))
            return None

    def connect(self):
        print("[MQTT] Connecting to %s:%d client_id=%s" % (self._host, self._port, self._client_id))
        print("[MQTT] TLS=%s ca=%s cert=%s key=%s user=%s" % (
            self._use_tls,
            "yes" if self._ca_cert else "NO",
            "yes" if self._cert else "NO",
            "yes" if self._key else "NO",
            self._user if self._user else "none",
        ))
        if self._use_tls:
            ssl_params = {"server_side": False, "server_hostname": self._host}
            if self._ca_cert:
                try:
                    import ussl as _ssl
                except ImportError:
                    import ssl as _ssl
                ssl_params["cadata"] = self._ca_cert
                ssl_params["cert_reqs"] = _ssl.CERT_REQUIRED
                print("[MQTT] Broker cert verification: REQUIRED")
            else:
                print("[MQTT] WARNING: no CA cert — broker cert NOT verified")
            if self._cert and self._key:
                ssl_params["cert"] = self._cert
                ssl_params["key"] = self._key
                print("[MQTT] Client cert: present")
            else:
                print("[MQTT] Client cert: NONE (password auth only)")
        else:
            ssl_params = None

        try:
            self._client = _MQTTClient(
                self._client_id,
                self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                ssl=self._use_tls,
                ssl_params=ssl_params,
                keepalive=60,
            )
            self._client.connect()
            print("[MQTT] Connected to %s:%d" % (self._host, self._port))
        except Exception as e:
            print("[MQTT] Connect FAILED: %s %s" % (type(e).__name__, e))
            raise

    def ping(self):
        try:
            self._client.ping()
        except Exception as e:
            print("[MQTT] Ping failed:", e)
            raise

    def publish(self, topic, payload_dict):
        data = ujson.dumps(payload_dict)
        try:
            self._client.publish(topic, data)
        except Exception:
            print("[MQTT] Publish failed, reconnecting...")
            try:
                self.connect()
                self._client.publish(topic, data)
            except Exception as e:
                print("[MQTT] Reconnect failed:", e)
                raise