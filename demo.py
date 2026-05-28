# ======================================================
# BOUND Demo Script v2.1
# File: backend/demos/demo.py
# ======================================================

import sys
import time
from pathlib import Path

# ======================================================
# ROOT SETUP
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ======================================================
# IMPORTS
# ======================================================

from backend.language.parser import parse_policy
from backend.runtime.policy_runtime import PolicyRuntime
from backend.simulation.thermal_simulation import ThermalSimulation
from backend.observability.telemetry_stream import TelemetryStream
from backend.bound_logging.event_logger import EventLogger

# ======================================================
# COLORS
# ======================================================

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    MUTED   = "\033[90m"
    WHITE   = "\033[97m"

# ======================================================
# HELPERS
# ======================================================

def header(msg, color=C.CYAN):
    line = "═" * 50
    print(f"\n{color}{C.BOLD}{line}")
    print(f"  {msg}")
    print(f"{line}{C.RESET}")

def phase(number, title, color=C.BLUE):
    print(f"\n{color}{C.BOLD}{'─'*50}")
    print(f"  PHASE {number} — {title}")
    print(f"{'─'*50}{C.RESET}\n")
    time.sleep(0.8)

def metric_line(name, value, unit, color):
    bar_len = int(float(value) / 5)
    bar     = "█" * bar_len
    print(
        f"  {C.MUTED}{name:<18}{C.RESET} "
        f"{color}{C.BOLD}{str(value):>6}{unit}{C.RESET}  "
        f"{color}{bar}{C.RESET}"
    )

def rule_activated(name, color=C.RED):
    print(f"\n  {color}{C.BOLD}▶ RULE ACTIVATED: {name}{C.RESET}")

def action_executed(action, color=C.YELLOW):
    print(f"  {color}  → {action}{C.RESET}")

def sleep(s, msg=None):
    if msg:
        print(f"\n  {C.MUTED}{msg}...{C.RESET}")
    time.sleep(s)

def print_state(state):

    temp = state.get("cpu_temp", 0)
    fan  = state.get("fan_speed", 0)
    load = state.get("traffic_load", 0)

    temp_color = (
        C.RED if temp > 90
        else C.YELLOW if temp > 70
        else C.GREEN
    )

    fan_color = (
        C.RED if fan >= 100
        else C.YELLOW if fan > 60
        else C.BLUE
    )

    load_color = (
        C.RED if load > 80
        else C.YELLOW if load > 50
        else C.GREEN
    )

    metric_line("cpu_temp", temp, "°C", temp_color)
    metric_line("fan_speed", fan, "%", fan_color)
    metric_line("traffic_load", load, "%", load_color)

# ======================================================
# PATCH SILENT RUNTIME
# ======================================================

def _runtime_cycle_silent(self):

    from backend.runtime.evaluator import evaluate_rules
    from backend.runtime.execution_engine import execute_rules_silent

    state = self.state_manager.get_state()

    active_rules = evaluate_rules(
        self.ast["rules"],
        state
    )

    results = execute_rules_silent(
        active_rules,
        state
    )

    for k, v in state.items():
        self.state_manager.update_metric(k, v)

    return results

PolicyRuntime.runtime_cycle_silent = _runtime_cycle_silent

# ======================================================
# SILENT EXECUTION ENGINE
# ======================================================

def _execute_rules_silent(active_rules, state):

    from backend.enforcement.action_executor import execute_action_silent

    results = []

    for rule in active_rules:

        for action in rule["actions"]:

            result = execute_action_silent(
                action,
                state
            )

            results.append({
                "rule": rule["name"],
                "action": action,
                "result": result
            })

    return results

import backend.runtime.execution_engine as _eng
_eng.execute_rules_silent = _execute_rules_silent

# ======================================================
# SILENT ACTION EXECUTOR
# ======================================================

def _execute_action_silent(action, state):

    from backend.enforcement.action_executor import _action_registry

    atype = action["type"]

    if atype == "EMIT":

        return {
            "status": "success",
            "type": "EMIT",
            "event": action["event"]
        }

    elif atype == "EXECUTE":

        name = action["action"]

        handler = _action_registry.get(name)

        if handler:
            handler(state)

        return {
            "status": "success",
            "type": "EXECUTE",
            "action": name
        }

    else:
        raise ValueError(f"Unknown action type: {atype}")

import backend.enforcement.action_executor as _exec
_exec.execute_action_silent = _execute_action_silent

# ======================================================
# MAIN DEMO
# ======================================================

def main():

    POLICY_PATH = ROOT_DIR / "policies" / "datacenter.bound"

    logger = EventLogger(
        log_to_file=True,
        log_to_console=False
    )

    telemetry = TelemetryStream(
        write_to_file=True
    )

    ast = parse_policy(POLICY_PATH)

    runtime = PolicyRuntime(ast)

    sim = ThermalSimulation()

    header("BOUND — Policy Runtime Demo", C.BLUE)

    print(f"\n  {C.MUTED}Policy   :{C.RESET} {C.WHITE}{ast['policy']}{C.RESET}")
    print(f"  {C.MUTED}Metrics  :{C.RESET} {C.WHITE}{[m['name'] for m in ast['metrics']]}{C.RESET}")
    print(f"  {C.MUTED}Rules    :{C.RESET} {C.WHITE}{[r['name'] for r in ast['rules']]}{C.RESET}")

    sleep(1.5, "Initializing runtime")

    # ==================================================
    # PHASE 1
    # ==================================================

    phase(1, "NORMAL OPERATION", C.GREEN)

    sim.set_load(25.0)

    for _ in range(4):

        sim_state = sim.step()

        runtime.update_metric("cpu_temp", sim_state["cpu_temp"])
        runtime.update_metric("fan_speed", sim_state["fan_speed"])
        runtime.update_metric("traffic_load", sim_state["traffic_load"])

        results = runtime.runtime_cycle_silent()

        state = runtime.get_state()

        print(f"  {C.MUTED}Cycle #{sim_state['cycle']}{C.RESET}")

        print_state(state)

        print()

        telemetry.record(
            state=state,
            active_rules=[],
            results=[]
        )

        sleep(1.2)

    # ==================================================
    # PHASE 2
    # ==================================================

    phase(2, "LOAD SPIKE — WARNING THRESHOLD", C.YELLOW)

    sim.set_load(75.0)

    for _ in range(4):

        sim_state = sim.step()

        runtime.update_metric("cpu_temp", sim_state["cpu_temp"])
        runtime.update_metric("fan_speed", sim_state["fan_speed"])
        runtime.update_metric("traffic_load", sim_state["traffic_load"])

        results = runtime.runtime_cycle_silent()

        state = runtime.get_state()

        active_rule_names = [r["rule"] for r in results]

        print(f"  {C.MUTED}Cycle #{sim_state['cycle']}{C.RESET}")

        print_state(state)

        if "thermal_warning" in active_rule_names:

            rule_activated("thermal_warning", C.YELLOW)

            action_executed(
                "EMIT thermal_alert",
                C.YELLOW
            )

            logger.action(
                "thermal_warning activated",
                {"cpu_temp": state["cpu_temp"]}
            )

        print()

        active_rules_obj = [
            r for r in ast["rules"]
            if r["name"] in active_rule_names
        ]

        telemetry.record(
            state=state,
            active_rules=active_rules_obj,
            results=results
        )

        sleep(1.2)

    # ==================================================
    # PHASE 3
    # ==================================================

    phase(3, "CRITICAL — ENFORCEMENT EXECUTING", C.RED)

    sim.set_load(95.0)

    runtime.update_metric("cpu_temp", 91)

    for _ in range(4):

        sim_state = sim.step()

        forced_temp = min(
            105,
            sim_state["cpu_temp"] + 5
        )

        runtime.update_metric("cpu_temp", forced_temp)
        runtime.update_metric("fan_speed", sim_state["fan_speed"])
        runtime.update_metric("traffic_load", sim_state["traffic_load"])

        results = runtime.runtime_cycle_silent()

        state = runtime.get_state()

        active_rule_names = [r["rule"] for r in results]

        print(f"  {C.MUTED}Cycle #{sim_state['cycle']}{C.RESET}")

        print_state(state)

        if "thermal_critical" in active_rule_names:

            rule_activated("thermal_critical", C.RED)

            action_executed(
                "EXECUTE emergency_cooling → fan_speed = 100%",
                C.RED
            )

            action_executed(
                "EXECUTE workload_isolation → traffic_load = 20%",
                C.RED
            )

            logger.action(
                "thermal_critical activated",
                {"cpu_temp": state["cpu_temp"]}
            )

            sim.apply_emergency_cooling()
            sim.apply_workload_isolation()

        if "thermal_warning" in active_rule_names:

            rule_activated(
                "thermal_warning",
                C.YELLOW
            )

            action_executed(
                "EMIT thermal_alert",
                C.YELLOW
            )

        print()

        active_rules_obj = [
            r for r in ast["rules"]
            if r["name"] in active_rule_names
        ]

        telemetry.record(
            state=state,
            active_rules=active_rules_obj,
            results=results
        )

        sleep(1.5)

    # ==================================================
    # PHASE 4
    # ==================================================

    phase(4, "RECOVERY — SYSTEM STABILIZING", C.GREEN)

    sim.set_load(20.0)

    for _ in range(5):

        sim_state = sim.step()

        runtime.update_metric("cpu_temp", sim_state["cpu_temp"])
        runtime.update_metric("fan_speed", sim_state["fan_speed"])
        runtime.update_metric("traffic_load", sim_state["traffic_load"])

        results = runtime.runtime_cycle_silent()

        state = runtime.get_state()

        print(f"  {C.MUTED}Cycle #{sim_state['cycle']}{C.RESET}")

        print_state(state)

        if not results:
            print(f"  {C.GREEN}✓ System stabilizing{C.RESET}")

        print()

        telemetry.record(
            state=state,
            active_rules=[],
            results=[]
        )

        sleep(1.2)

    # ==================================================
    # SUMMARY
    # ==================================================

    header("DEMO COMPLETE", C.GREEN)

    snapshots = telemetry.get_all()

    total_cycles = len(snapshots)

    crit_cycles = sum(
        1 for s in snapshots
        if "thermal_critical" in s["active_rules"]
    )

    warn_cycles = sum(
        1 for s in snapshots
        if "thermal_warning" in s["active_rules"]
    )

    print(f"\n  Total cycles    : {total_cycles}")
    print(f"  Warning cycles  : {warn_cycles}")
    print(f"  Critical cycles : {crit_cycles}")

    telemetry.print_metric_trend("cpu_temp")

    print(
        f"\n  {C.GREEN}{C.BOLD}"
        f"BOUND Demonstration Complete."
        f"{C.RESET}\n"
    )

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print(
            f"\n\n  {C.MUTED}"
            f"Demo interrupted."
            f"{C.RESET}\n"
        )