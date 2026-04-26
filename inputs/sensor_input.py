from inputs.base import Input
from config import DEBUG


class SensorInput(Input):
    def __init__(self, slot_id, dead_zone=0.02):
        super().__init__(slot_id, "sensor")
        self._dead_zone = dead_zone
        self._last_value = None

    def read_raw(self):
        # Subclasses override this to return a float reading.
        raise NotImplementedError

    def tick(self):
        try:
            value = float(self.read_raw())
        except Exception as e:
            print("SensorInput read error (%s):" % self.slot_id, e)
            return None
        if self._last_value is None or abs(value - self._last_value) > self._dead_zone:
            self._last_value = value
            if DEBUG: print("[%s] emit: change value=%.3f" % (self.slot_id, value))
            return [{"slotId": self.slot_id, "inputType": self.input_type,
                     "event": "change", "value": value}]
        return None