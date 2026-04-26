import dht
import machine
import utime
from inputs.base import Input


class Dht11Input(Input):
    def __init__(self, slot_id, pin, read_interval_ms=2000):
        super().__init__(slot_id, "sensor")
        self._sensor = dht.DHT11(machine.Pin(pin))
        self._read_interval_ms = max(read_interval_ms, 1000)  # DHT11 minimum 1s
        self._last_read_ms = utime.ticks_ms()  # delay first read by interval
        self._last_temp = None

    def tick(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self._last_read_ms) < self._read_interval_ms:
            return None
        self._last_read_ms = now
        try:
            self._sensor.measure()
            temp = self._sensor.temperature()
            print("[%s] raw read: temp=%s" % (self.slot_id, temp))
        except Exception as e:
            print("[%s] read error:" % self.slot_id, e)
            return None
        if temp == self._last_temp:
            return None
        self._last_temp = temp
        print("[%s] emit: temp=%.1f" % (self.slot_id, temp))
        return [{"slotId": self.slot_id, "inputType": self.input_type,
                 "event": "change", "value": float(temp)}]