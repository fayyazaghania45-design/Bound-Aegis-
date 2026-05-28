# ======================================================
# BOUND Policy Memory (STATEFUL RULE TRACKING)
# ======================================================

class PolicyMemory:
    def __init__(self):
        self.rule_state = {}   # ON/OFF status rule
        self.cooldown = {}     # anti spam

    # -----------------------------
    # RULE STATE (ON / OFF)
    # -----------------------------
    def is_active(self, rule_name):
        return self.rule_state.get(rule_name, False)

    def activate(self, rule_name):
        self.rule_state[rule_name] = True

    def deactivate(self, rule_name):
        self.rule_state[rule_name] = False

    # -----------------------------
    # COOLDOWN SYSTEM
    # -----------------------------
    def set_cooldown(self, rule_name, ticks):
        self.cooldown[rule_name] = ticks

    def in_cooldown(self, rule_name):
        return self.cooldown.get(rule_name, 0) > 0

    def tick(self):
        for k in list(self.cooldown.keys()):
            self.cooldown[k] -= 1
            if self.cooldown[k] <= 0:
                del self.cooldown[k]