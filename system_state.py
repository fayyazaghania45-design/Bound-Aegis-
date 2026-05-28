# ======================================================
# BOUND System State Machine vFINAL + PRIORITY
# ======================================================

class SystemState:

    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"

    def __init__(self):
        self.current_state = self.NORMAL
        self.last_state = self.NORMAL

    # ==================================================
    # STATE TRANSITION
    # ==================================================
    def transition(self, cpu_temp):

        self.last_state = self.current_state

        if cpu_temp >= 100:
            self.current_state = self.CRITICAL

        elif cpu_temp >= 80:
            self.current_state = self.WARNING

        else:
            self.current_state = self.NORMAL

        return self.current_state

    # ==================================================
    # STATE CHANGE DETECTOR
    # ==================================================
    def changed(self):
        return self.current_state != self.last_state

    # ==================================================
    # PRIORITY ENGINE (LOMBA / INDUSTRIAL VALUE)
    # ==================================================
    def priority(self):

        if self.current_state == self.CRITICAL:
            return 3   # highest priority

        elif self.current_state == self.WARNING:
            return 2   # medium priority

        else:
            return 1   # normal priority

    # ==================================================
    # HUMAN READABLE DEBUG
    # ==================================================
    def info(self):
        return {
            "state": self.current_state,
            "priority": self.priority()
        }