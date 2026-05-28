# ======================================================
# BOUND Execution Engine v2.0
# File: backend/runtime/execution_engine.py
# ======================================================

from backend.enforcement.action_executor import execute_action


def execute_rules(active_rules, state):

    results = []

    if not active_rules:
        print("\n[BOUND] No active rules detected")
        return results

    for rule in active_rules:

        print(f"\n======================================")
        print(f"[RULE ACTIVATED] {rule['name']}")
        print(f"======================================")

        for action in rule["actions"]:

            result = execute_action(
                action,
                state
            )

            results.append({
                "rule": rule["name"],
                "action": action,
                "result": result
            })

    return results