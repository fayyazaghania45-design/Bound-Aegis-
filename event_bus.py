# ======================================================
# BOUND Event Bus (INDUSTRIAL CORE)
# ======================================================

class EventBus:

    def __init__(self):
        self.last_events = set()

    def emit_once(self, event_name):
        """
        hanya emit sekali sampai state berubah
        """
        if event_name in self.last_events:
            return False

        self.last_events.add(event_name)
        return True

    def reset(self):
        """
        reset ketika state berubah besar
        """
        self.last_events.clear()