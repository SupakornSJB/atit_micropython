import utime
import ujson
from machine import Pin
import wifi_client
import mqtt_client
import config


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