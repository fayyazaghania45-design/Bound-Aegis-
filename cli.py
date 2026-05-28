# ======================================================
# BOUND CLI v2.1
# File: backend/cli/cli.py
# ======================================================

import cmd
import sys
from pathlib import Path

# ======================================================
# ROOT SETUP
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ======================================================
# PATHS
# ======================================================

POLICIES_DIR = ROOT_DIR / "policies"

# ======================================================
# IMPORTS
# ======================================================

from backend.language.parser import parse_policy
from backend.runtime.policy_runtime import PolicyRuntime
from backend.simulation.thermal_simulation import ThermalSimulation
from backend.observability.telemetry_stream import TelemetryStream
from backend.bound_logging.event_logger import EventLogger

# ======================================================
# BANNER
# ======================================================

BANNER = """
╔══════════════════════════════════════╗
║          BOUND CLI v2.1             ║
║    Policy-as-Code Runtime CLI       ║
╚══════════════════════════════════════╝

Type 'help' to see available commands.
"""

# ======================================================
# CLI CLASS
# ======================================================

class BoundCLI(cmd.Cmd):

    prompt = "\nbound> "
    intro  = BANNER

    # --------------------------------------------------

    def __init__(self):

        super().__init__()

        self.runtime   = None
        self.ast       = None

        self.sim = ThermalSimulation()

        self.telemetry = TelemetryStream(
            write_to_file=False
        )

        self.logger = EventLogger(
            log_to_file=False,
            log_to_console=False
        )

    # ==================================================
    # HELPERS
    # ==================================================

    def _require_runtime(self):

        if self.runtime is None:

            print(
                "[ERROR] No policy loaded.\n"
                "Run: load <policy_file>"
            )

            return False

        return True

    # ==================================================
    # LOAD POLICY
    # ==================================================

    def do_load(self, arg):

        """
        Load a .bound policy file.

        Usage:
            load datacenter.bound
        """

        if not arg:

            print(
                "[ERROR] Usage: load <policy_file>"
            )

            return

        path = (
            Path(arg)
            if Path(arg).is_absolute()
            else POLICIES_DIR / arg
        )

        if not path.exists():

            print(
                f"[ERROR] File not found: {path}"
            )

            return

        try:

            self.ast = parse_policy(path)

            self.runtime = PolicyRuntime(
                self.ast
            )

            print(
                f"\n[OK] Policy loaded: "
                f"{self.ast['policy']}"
            )

            print(
                f"  Metrics : "
                f"{[m['name'] for m in self.ast['metrics']]}"
            )

            print(
                f"  Rules   : "
                f"{[r['name'] for r in self.ast['rules']]}"
            )

        except Exception as e:

            print(f"[ERROR] {e}")

    # ==================================================
    # SET METRIC
    # ==================================================

    def do_set(self, arg):

        """
        Inject metric value.

        Usage:
            set cpu_temp 95
        """

        if not self._require_runtime():
            return

        parts = arg.strip().split()

        if len(parts) != 2:

            print(
                "[ERROR] Usage: set <metric> <value>"
            )

            return

        try:

            metric = parts[0]

            value = float(parts[1])

            if value == int(value):
                value = int(value)

            self.runtime.update_metric(
                metric,
                value
            )

            print(
                f"[OK] {metric} = {value}"
            )

        except ValueError as e:

            print(f"[ERROR] {e}")

    # ==================================================
    # RUN CYCLE
    # ==================================================

    def do_run(self, arg):

        """
        Run one runtime cycle.

        Usage:
            run
        """

        if not self._require_runtime():
            return

        results = self.runtime.runtime_cycle()

        state = self.runtime.get_state()

        active_rule_names = list({
            r["rule"] for r in results
        })

        active_rules = [
            r for r in self.ast["rules"]
            if r["name"] in active_rule_names
        ]

        self.telemetry.record(
            state=state,
            active_rules=active_rules,
            results=results
        )

        if not results:

            print(
                "[INFO] No rules triggered."
            )

    # ==================================================
    # SHOW STATE
    # ==================================================

    def do_state(self, arg):

        """
        Show runtime state.

        Usage:
            state
        """

        if not self._require_runtime():
            return

        state = self.runtime.get_state()

        print("\n======================================")
        print("BOUND CURRENT STATE")
        print("======================================")

        for k, v in state.items():

            try:
                bar = "█" * int(float(v) / 5)
            except:
                bar = ""

            print(
                f"  {k:<20} "
                f"{str(v):>8}   "
                f"{bar}"
            )

        print("======================================\n")

    # ==================================================
    # SIMULATION
    # ==================================================

    def do_simulate(self, arg):

        """
        Run thermal simulation.

        Usage:
            simulate <cycles> <load>

        Example:
            simulate 10 90
        """

        if not self._require_runtime():
            return

        parts = arg.strip().split()

        cycles = (
            int(parts[0])
            if len(parts) > 0 and parts[0].isdigit()
            else 5
        )

        load = (
            float(parts[1])
            if len(parts) > 1
            else 80.0
        )

        self.sim.set_load(load)

        print(
            f"\n[SIMULATION] "
            f"{cycles} cycles at {load}% load\n"
        )

        for _ in range(cycles):

            sim_state = self.sim.step()

            self.sim.print_status()

            self.runtime.update_metric(
                "cpu_temp",
                sim_state["cpu_temp"]
            )

            self.runtime.update_metric(
                "fan_speed",
                sim_state["fan_speed"]
            )

            self.runtime.update_metric(
                "traffic_load",
                sim_state["traffic_load"]
            )

            results = self.runtime.runtime_cycle()

            state = self.runtime.get_state()

            active_rule_names = list({
                r["rule"] for r in results
            })

            active_rules = [
                r for r in self.ast["rules"]
                if r["name"] in active_rule_names
            ]

            self.telemetry.record(
                state=state,
                active_rules=active_rules,
                results=results
            )

            for result in results:

                action = result["action"]

                if action["type"] == "EXECUTE":

                    if action["action"] == "emergency_cooling":
                        self.sim.apply_emergency_cooling()

                    elif action["action"] == "workload_isolation":
                        self.sim.apply_workload_isolation()

        print("\n[OK] Simulation complete.\n")

    # ==================================================
    # SHOW TREND
    # ==================================================

    def do_trend(self, arg):

        """
        Show metric trend.

        Usage:
            trend cpu_temp
        """

        if not arg:

            print(
                "[ERROR] Usage: trend <metric>"
            )

            return

        if not self.telemetry.get_all():

            print(
                "[INFO] No telemetry yet.\n"
                "Run 'simulate' or 'run' first."
            )

            return

        self.telemetry.print_metric_trend(
            arg.strip()
        )

    # ==================================================
    # SHOW RULES
    # ==================================================

    def do_rules(self, arg):

        """
        Show all rules.

        Usage:
            rules
        """

        if not self._require_runtime():
            return

        print("\n======================================")
        print("BOUND POLICY RULES")
        print("======================================")

        for rule in self.ast["rules"]:

            cond = rule["condition"]

            print(f"\n  RULE : {rule['name']}")

            print(
                f"  WHEN : "
                f"{cond['left']} "
                f"{cond['operator']} "
                f"{cond['right']}"
            )

            for action in rule["actions"]:

                print(
                    f"  THEN : "
                    f"{action['type']} "
                    f"{action.get('event') or action.get('action')}"
                )

        print("\n======================================\n")

    # ==================================================
    # CLEAR
    # ==================================================

    def do_clear(self, arg):

        """
        Clear terminal screen.
        """

        import os

        os.system(
            "clear"
            if os.name == "posix"
            else "cls"
        )

    # ==================================================
    # EXIT
    # ==================================================

    def do_exit(self, arg):

        """
        Exit CLI.
        """

        print("\n[BOUND] Goodbye.\n")

        return True

    def do_quit(self, arg):

        """
        Exit CLI.
        """

        return self.do_exit(arg)

    # ==================================================
    # DEFAULTS
    # ==================================================

    def emptyline(self):
        pass

    def default(self, line):

        print(
            f"[ERROR] Unknown command: '{line}'\n"
            f"Type 'help' to see commands."
        )

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":

    cli = BoundCLI()

    default_policy = (
        POLICIES_DIR / "datacenter.bound"
    )

    if default_policy.exists():

        print(
            f"\n[BOUND] Auto-loading:\n"
            f"{default_policy}"
        )

        cli.do_load(
            str(default_policy)
        )

    try:

        cli.cmdloop()

    except KeyboardInterrupt:

        print(
            "\n\n[BOUND] Interrupted.\n"
        )