from machine import Pin
import utime
import config


class Button:
    def __init__(self, pin_number, on_press=None, on_release=None):
        self._pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self._on_press = on_press
        self._on_release = on_release
        # Pull-up: unpressed = 1, pressed = 0
        self._last_state = self._pin.value()
        self._last_change_ms = utime.ticks_ms()

    def tick(self):
        current_state = self._pin.value()
        now = utime.ticks_ms()

        if current_state != self._last_state:
            if utime.ticks_diff(now, self._last_change_ms) >= config.DEBOUNCE_MS:
                self._last_state = current_state
                self._last_change_ms = now
                if current_state == 0 and self._on_press:
                    self._on_press()
                elif current_state == 1 and self._on_release:
                    self._on_release()