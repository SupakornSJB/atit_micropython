import dht
from machine import Pin
import utime
from inputs.base import Input


class DHT11Input(Input):
    def __init__(self, slot_id, pin, interval_ms=2000, dead_zone=0.5):
        super().__init__(slot_id, "sensor")
        self._sensor = dht.DHT11(Pin(pin))
        self._interval_ms = interval_ms  # DHT11 needs >=1s between reads
        self._dead_zone = dead_zone
        self._last_read_ms = utime.ticks_ms()  # delay first read by interval_ms
        self._last_temp = None
        self._last_hum = None

    def tick(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self._last_read_ms) < self._interval_ms:
            return None
        try:
            self._sensor.measure()
        except Exception as e:
            print("DHT11 read error (%s):" % self.slot_id, e)
            return None
        self._last_read_ms = now
        temp = self._sensor.temperature()
        hum = self._sensor.humidity()
        print("[%s] raw read: temp=%s hum=%s" % (self.slot_id, temp, hum))
        events = []
        if self._last_temp is None or abs(temp - self._last_temp) > self._dead_zone:
            self._last_temp = temp
            print("[%s] emit: temp=%.1f" % (self.slot_id, temp))
            events.append({"slotId": self.slot_id + "_temp", "inputType": self.input_type,
                           "event": "change", "value": float(temp)})
        else:
            print("[%s] skip: temp=%.1f (no change)" % (self.slot_id, temp))
        if self._last_hum is None or abs(hum - self._last_hum) > self._dead_zone:
            self._last_hum = hum
            print("[%s] emit: hum=%.1f" % (self.slot_id, hum))
            events.append({"slotId": self.slot_id + "_hum", "inputType": self.input_type,
                           "event": "change", "value": float(hum)})
        else:
            print("[%s] skip: hum=%.1f (no change)" % (self.slot_id, hum))
        return events if events else None