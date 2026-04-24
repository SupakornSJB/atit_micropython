from machine import ADC, Pin
import utime
from inputs.base import Input


class KnobInput(Input):
    def __init__(self, slot_id, pin, min_raw=0, max_raw=4095, dead_zone=0.02):
        super().__init__(slot_id, "knob")
        self._adc = ADC(Pin(pin))
        self._adc.atten(ADC.ATTN_11DB)  # full 0–3.3V range
        self._min_raw = min_raw
        self._max_raw = max_raw
        self._dead_zone = dead_zone
        self._last_value = None

    def tick(self):
        raw = self._adc.read()
        span = self._max_raw - self._min_raw
        value = (raw - self._min_raw) / span if span else 0.0
        value = max(0.0, min(1.0, value))
        if self._last_value is None or abs(value - self._last_value) > self._dead_zone:
            self._last_value = value
            print("[%s] emit: change value=%.3f" % (self.slot_id, value))
            return [{"slotId": self.slot_id, "inputType": self.input_type,
                     "event": "change", "value": value}]
        return None