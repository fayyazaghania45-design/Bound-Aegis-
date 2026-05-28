# ======================================================
# BOUND State Manager v2.0
# File: backend/runtime/state_manager.py
# ======================================================


class StateManager:

    def __init__(self):
        self.state = {}

    def register_metrics(self, metrics):
        for m in metrics:
            self.state[m["name"]] = 0

    def update_metric(self, name, value):
        if name not in self.state:
            raise ValueError(f"Unknown metric: {name}")
        self.state[name] = value

    def get_metric(self, name):
        if name not in self.state:
            raise ValueError(f"Unknown metric: {name}")
        return self.state[name]

    def get_state(self):
        return dict(self.state)

    def print_state(self):
        print("\n======================================")
        print("BOUND RUNTIME STATE")
        print("======================================")
        for k, v in self.state.items():
            print(f"  {k}: {v}")
        print("======================================\n")