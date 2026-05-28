# ======================================================
# BOUND Policy Runtime vFINAL (COMPETITION READY)
# ======================================================

from backend.runtime.evaluator import evaluate_rules
from backend.runtime.execution_engine import execute_rules
from backend.runtime.state_manager import StateManager
from backend.runtime.resolver import resolve
from backend.runtime.system_state import SystemState
from backend.runtime.policy_memory import PolicyMemory
from backend.runtime.event_bus import EventBus
from backend.runtime.runtime_intelligence import RuntimeIntelligence


class PolicyRuntime:

    def __init__(self, ast):
        self.ast = ast

        self.state_manager = StateManager()
        self.state_manager.register_metrics(ast["metrics"])

        # CORE SYSTEMS
        self.system_state = SystemState()
        self.memory = PolicyMemory()
        self.event_bus = EventBus()
        self.intel = RuntimeIntelligence()

    # ==================================================
    # COMPATIBILITY (run.py SAFE)
    # ==================================================
    def update_metric(self, name, value):
        self.state_manager.update_metric(name, value)

    def get_state(self):
        return self.state_manager.get_state()

    # ==================================================
    # MAIN RUNTIME CYCLE
    # ==================================================
    def runtime_cycle(self):

        print("\n======================================")
        print("BOUND RUNTIME CYCLE")
        print("======================================")

        # -----------------------------
        # LOAD STATE
        # -----------------------------
        raw_state = self.state_manager.get_state()
        state = {k: resolve(v) for k, v in raw_state.items()}

        cpu_temp = state.get("cpu_temp", 0)
        fan_speed = state.get("fan_speed", 0)
        traffic_load = state.get("traffic_load", 0)

        # -----------------------------
        # STATE MACHINE
        # -----------------------------
        mode = self.system_state.transition(cpu_temp)

        print(f"\n[STATE MACHINE] MODE = {mode}")
        print(f"[PRIORITY LEVEL] {self.system_state.priority()}")

        # reset event bus if state changed
        if self.system_state.changed():
            self.event_bus.reset()

        # tick cooldown system
        self.memory.tick()

        # -----------------------------
        # ANOMALY SCORE (INTELLIGENCE LAYER)
        # -----------------------------
        anomaly = self.intel.compute_anomaly(cpu_temp, fan_speed, traffic_load)
        print(f"[ANOMALY SCORE] {anomaly}/100")

        # -----------------------------
        # RULE ENGINE
        # -----------------------------
        rules = evaluate_rules(self.ast["rules"], state)

        # PRIORITY SORT (FIXED LOGIC)
        # critical mode = highest priority first execution
        rules.sort(key=lambda r: self.system_state.priority(), reverse=True)

        filtered_rules = []

        for rule in rules:
            name = rule["name"]

            # -------------------------
            # COOLDOWN (ANTI SPAM)
            # -------------------------
            if self.memory.in_cooldown(name):
                continue

            # -------------------------
            # EVENT DEDUP (IMPORTANT)
            # -------------------------
            if not self.event_bus.emit_once(name):
                continue

            # -------------------------
            # STATE FILTERING LOGIC
            # -------------------------
            if mode == "normal" and "warning" not in name:
                continue

            filtered_rules.append(rule)
            self.memory.activate(name)

            # log intelligence event
            self.intel.log_event("RULE_TRIGGERED", name, state)

        # -----------------------------
        # EXECUTION ENGINE
        # -----------------------------
        results = execute_rules(filtered_rules, state)

        # -----------------------------
        # COOLDOWN CONFIGURATION
        # -----------------------------
        for rule in filtered_rules:
            name = rule["name"]

            if name == "thermal_critical":
                self.memory.set_cooldown(name, 3)

            elif name == "thermal_warning":
                self.memory.set_cooldown(name, 1)

        # -----------------------------
        # SYNC STATE BACK
        # -----------------------------
        for k, v in state.items():
            self.state_manager.update_metric(k, v)

        self.state_manager.print_state()

        # -----------------------------
        # INTELLIGENCE OUTPUT (LOMBA VALUE)
        # -----------------------------
        print("\n[EVENT TIMELINE]")
        for e in self.intel.get_timeline():
            print(f"- {e['type']} :: {e['name']}")

        print("\n======================================")

        return results