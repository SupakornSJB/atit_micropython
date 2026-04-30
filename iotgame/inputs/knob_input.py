from machine import ADC, Pin
import utime
from iotgame.inputs.base import Input
from iotgame.debug import DEBUG


class KnobInput(Input):
    def __init__(self, slot_id, pin, min_raw=0, max_raw=4095, dead_zone=0.02, center=None, samples=8):
        super().__init__(slot_id, "knob")
        self._adc = ADC(Pin(pin))
        self._adc.atten(ADC.ATTN_11DB)
        self._min_raw = min_raw
        self._max_raw = max_raw
        self._center = center
        self._dead_zone = dead_zone
        self._samples = samples
        self._last_value = None

    def tick(self):
        raw = sum(self._adc.read() for _ in range(self._samples)) // self._samples

        if self._center is None:
            span = self._max_raw - self._min_raw
            value = (raw - self._min_raw) / span if span else 0.0
        else:
            center = self._center
            if raw >= center:
                upper_span = self._max_raw - center
                value = 0.5 + 0.5 * (raw - center) / upper_span if upper_span else 1.0
            else:
                lower_span = center - self._min_raw
                value = 0.5 * (raw - self._min_raw) / lower_span if lower_span else 0.0

        value = max(0.0, min(1.0, value))

        if self._last_value is None or abs(value - self._last_value) > self._dead_zone:
            self._last_value = value
            if DEBUG: print("[%s] emit: change value=%.3f" % (self.slot_id, value))
            return [{"slotId": self.slot_id, "inputType": self.input_type,
                     "event": "change", "value": value}]

        return None
