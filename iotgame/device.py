import utime
from machine import Pin
from iotgame.mqtt import MqttClient
from iotgame.inputs.button_input import ButtonInput
from iotgame.inputs.knob_input import KnobInput
from iotgame.inputs.dht11_input import Dht11Input
from iotgame.inputs.ultrasonic_input import UltrasonicInput


class IoTDevice:
    def __init__(self, device_id, mqtt_host, mqtt_port, wifi_ssid, wifi_password,
                 mqtt_user=None, mqtt_password=None,
                 ca_cert_path=None, cert_path=None, key_path=None):
        self._device_id = device_id
        self._wifi_ssid = wifi_ssid
        self._wifi_password = wifi_password
        self._mqtt = MqttClient(
            device_id, mqtt_host, mqtt_port,
            user=mqtt_user, password=mqtt_password,
            ca_cert_path=ca_cert_path, cert_path=cert_path, key_path=key_path,
        )
        self._inputs = []
        self._seq = 0
        self._led = Pin(2, Pin.OUT)

    def add_input(self, inp):
        self._inputs.append(inp)
        print("[device] registered slot: %s (%s)" % (inp.slot_id, inp.input_type))

    def add_input_from_config(self, cfg):
        self.add_input(self._build_input(cfg))

    def _build_input(self, cfg):
        t = cfg["type"]
        if t == "button":
            return ButtonInput(cfg["slotId"], cfg["pin"], cfg.get("debounce_ms", 50), cfg.get("pull_up", True))
        if t == "knob":
            return KnobInput(cfg["slotId"], cfg["pin"],
                             cfg.get("min_raw", 0), cfg.get("max_raw", 4095),
                             cfg.get("dead_zone", 0.02), cfg.get("center", None),
                             cfg.get("samples", 8))
        if t == "dht11":
            return Dht11Input(cfg["slotId"], cfg["pin"],
                              cfg.get("read_interval_ms", 2000))
        if t == "ultrasonic":
            return UltrasonicInput(cfg["slotId"], cfg["trig_pin"], cfg["echo_pin"],
                                   cfg.get("min_cm", 2.0), cfg.get("max_cm", 200.0),
                                   cfg.get("dead_zone_cm", 2.0),
                                   cfg.get("read_interval_ms", 100))
        raise ValueError("Unknown input type: " + t)

    def _blink_error(self):
        for _ in range(10):
            self._led.value(1)
            utime.sleep_ms(100)
            self._led.value(0)
            utime.sleep_ms(100)

    def _ensure_connected(self):
        from iotgame import wifi
        wifi.connect(self._wifi_ssid, self._wifi_password)
        self._mqtt.connect()

    def _publish_event(self, event_dict):
        topic = "game/devices/%s/slot/%s" % (self._device_id, event_dict["slotId"])
        payload = {
            "deviceId": self._device_id,
            "slotId": event_dict["slotId"],
            "inputType": event_dict["inputType"],
            "event": event_dict["event"],
            "value": event_dict["value"],
            "timestamp": utime.time(),
            "sequenceNumber": self._seq,
        }
        if "auxiliary" in event_dict:
            payload["auxiliary"] = event_dict["auxiliary"]
        self._mqtt.publish(topic, payload)
        self._seq += 1

    def run(self):
        print("[device] starting with %d slot(s):" % len(self._inputs))
        for inp in self._inputs:
            print("  - %s (%s)" % (inp.slot_id, inp.input_type))
        backoff = 1
        while True:
            try:
                self._ensure_connected()
                backoff = 1
                last_ping_ms = utime.ticks_ms()
                while True:
                    for inp in self._inputs:
                        try:
                            events = inp.tick()
                        except Exception as e:
                            print("Slot error (%s):" % inp.slot_id, e)
                            events = None
                        if events:
                            for ev in events:
                                self._publish_event(ev)
                            last_ping_ms = utime.ticks_ms()
                    now = utime.ticks_ms()
                    if utime.ticks_diff(now, last_ping_ms) > 30000:
                        self._mqtt.ping()
                        last_ping_ms = now
                    utime.sleep_ms(10)
            except Exception as e:
                print("Device error:", e)
                self._blink_error()
                utime.sleep(backoff)
                backoff = min(backoff * 2, 30)
