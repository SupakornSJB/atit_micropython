class Input:
    def __init__(self, slot_id, input_type):
        self.slot_id = slot_id
        self.input_type = input_type

    def tick(self):
        # Returns list of event dicts on state change, else None.
        # Each dict: {"slotId", "inputType", "event", "value"}
        raise NotImplementedError