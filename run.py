# ======================================================
# BOUND Main Entry Point v2.1
# File: run.py
# ======================================================

from pathlib import Path

# ======================================================
# IMPORTS
# ======================================================

from backend.language.parser import parse_policy
from backend.runtime.policy_runtime import PolicyRuntime
from backend.simulation.thermal_simulation import ThermalSimulation
from backend.observability.telemetry_stream import TelemetryStream
from backend.bound_logging.event_logger import EventLogger

# ======================================================
# POLICY PATH
# ======================================================

BASE_DIR = Path(__file__).resolve().parent

POLICY_PATH = BASE_DIR / "policies" / "datacenter.bound"

# ======================================================
# MAIN
# ======================================================

def main():

    logger = EventLogger(
        log_to_file=True,
        log_to_console=False
    )

    telemetry = TelemetryStream(
        write_to_file=True
    )

    logger.info("BOUND runtime starting")

    ast = parse_policy(POLICY_PATH)

    runtime = PolicyRuntime(ast)

    sim = ThermalSimulation()

    sim.set_load(90.0)

    print("\n======================================")
    print(f"BOUND — Policy: {ast['policy']}")
    print("======================================\n")

    for cycle in range(1, 6):

        print(f"─── CYCLE #{cycle} ───────────────────────────")

        sim_state = sim.step()

        sim.print_status()

        runtime.update_metric(
            "cpu_temp",
            sim_state["cpu_temp"]
        )

        runtime.update_metric(
            "fan_speed",
            sim_state["fan_speed"]
        )

        runtime.update_metric(
            "traffic_load",
            sim_state["traffic_load"]
        )

        results = runtime.runtime_cycle()

        active_rule_names = list({
            r["rule"] for r in results
        })

        active_rules = [
            r for r in ast["rules"]
            if r["name"] in active_rule_names
        ]

        telemetry.record(
            state=runtime.get_state(),
            active_rules=active_rules,
            results=results
        )

        for result in results:

            logger.action(
                f"Action executed: "
                f"{result['action']['type']} → "
                f"{result['action'].get('event') or result['action'].get('action')}",
                {"rule": result["rule"]}
            )

        for result in results:

            action = result["action"]

            if action["type"] == "EXECUTE":

                if action["action"] == "emergency_cooling":
                    sim.apply_emergency_cooling()

                elif action["action"] == "workload_isolation":
                    sim.apply_workload_isolation()

    telemetry.print_metric_trend("cpu_temp")

    telemetry.print_metric_trend("fan_speed")

    print("======================================")
    print("BOUND RUNTIME COMPLETE")
    print("======================================\n")


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    main()