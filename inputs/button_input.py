from machine import Pin
import utime
from inputs.base import Input
from config import DEBUG


class ButtonInput(Input):
    def __init__(self, slot_id, pin, debounce_ms=50, pull_up=True):
        super().__init__(slot_id, "button")
        pull = Pin.PULL_UP if pull_up else Pin.PULL_DOWN
        self._pin = Pin(pin, Pin.IN, pull)
        self._debounce_ms = debounce_ms
        self._pull_up = pull_up
        self._last_state = self._pin.value()
        self._last_change_ms = utime.ticks_ms()

    def tick(self):
        current = self._pin.value()
        now = utime.ticks_ms()
        if current != self._last_state:
            if utime.ticks_diff(now, self._last_change_ms) >= self._debounce_ms:
                self._last_state = current
                self._last_change_ms = now
                if (current == 0) == self._pull_up:
                    if DEBUG: print("[%s] emit: pressed" % self.slot_id)
                    return [{"slotId": self.slot_id, "inputType": self.input_type,
                              "event": "pressed", "value": 1.0}]
                else:
                    if DEBUG: print("[%s] emit: released" % self.slot_id)
                    return [{"slotId": self.slot_id, "inputType": self.input_type,
                              "event": "released", "value": 0.0}]
        return None