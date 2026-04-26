import machine
import utime
from inputs.base import Input


class UltrasonicInput(Input):
    def __init__(self, slot_id, trig_pin, echo_pin,
                 min_cm=2.0, max_cm=200.0, dead_zone_cm=2.0, read_interval_ms=100):
        super().__init__(slot_id, "sensor")
        self._trig = machine.Pin(trig_pin, machine.Pin.OUT)
        self._echo = machine.Pin(echo_pin, machine.Pin.IN)
        self._min_cm = min_cm
        self._max_cm = max_cm
        self._dead_zone_cm = dead_zone_cm
        self._read_interval_ms = read_interval_ms
        self._last_read_ms = 0
        self._last_distance = None

    def _measure_cm(self):
        self._trig.value(0)
        utime.sleep_us(2)
        self._trig.value(1)
        utime.sleep_us(10)
        self._trig.value(0)
        start = utime.ticks_us()
        timeout = utime.ticks_add(start, 30000)
        while self._echo.value() == 0:
            if utime.ticks_diff(utime.ticks_us(), timeout) > 0:
                return None
        pulse_start = utime.ticks_us()
        while self._echo.value() == 1:
            if utime.ticks_diff(utime.ticks_us(), timeout) > 0:
                return None
        pulse_end = utime.ticks_us()
        duration_us = utime.ticks_diff(pulse_end, pulse_start)
        return (duration_us * 0.0343) / 2.0

    def tick(self):
        now = utime.ticks_ms()
        if utime.ticks_diff(now, self._last_read_ms) < self._read_interval_ms:
            return None
        self._last_read_ms = now
        cm = self._measure_cm()
        if cm is None:
            return None
        cm = max(self._min_cm, min(self._max_cm, cm))
        if (self._last_distance is not None and
                abs(cm - self._last_distance) < self._dead_zone_cm):
            return None
        self._last_distance = cm
        print("[%s] emit: distance=%.1f cm" % (self.slot_id, cm))
        return [{"slotId": self.slot_id, "inputType": self.input_type,
                 "event": "change", "value": cm}]