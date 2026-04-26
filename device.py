import utime
import ujson
from machine import Pin
import wifi_client
import mqtt_client
import config
from inputs.button_input import ButtonInput
from inputs.knob_input import KnobInput
from inputs.dht11_input import Dht11Input
from inputs.ultrasonic_input import UltrasonicInput


class IoTDevice:
    def __init__(self, device_id, mqtt_host, mqtt_port, mqtt_user,
                 mqtt_password, wifi_ssid, wifi_password):
        self._device_id = device_id
        self._inputs = []
        self._seq = 0
        self._led = Pin(2, Pin.OUT)

    def add_input(self, inp):
        self._inputs.append(inp)
        print("[device] registered slot: %s (%s)" % (inp.slot_id, inp.input_type))

    def _build_input(self, cfg):
        t = cfg["type"]
        if t == "button":
            return ButtonInput(cfg["slotId"], cfg["pin"], cfg.get("debounce_ms", 50))
        if t == "knob":
            return KnobInput(cfg["slotId"], cfg["pin"],
                             cfg.get("min_raw", 0), cfg.get("max_raw", 4095),
                             cfg.get("dead_zone", 0.02))
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
        wifi_client.connect()
        mqtt_client.connect()

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
        mqtt_client.publish(topic, payload)
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
                    utime.sleep_ms(10)
            except Exception as e:
                print("Device error:", e)
                self._blink_error()
                utime.sleep(backoff)
                backoff = min(backoff * 2, 30)