# ======================================================
# BOUND Action Executor v2.0
# File: backend/enforcement/action_executor.py
# ======================================================


def execute_action(action, state):

    atype = action["type"]

    if atype == "EMIT":
        event = action["event"]
        print(f"[EMIT EVENT] {event}")
        return {"status": "success", "type": "EMIT", "event": event}

    elif atype == "EXECUTE":
        name = action["action"]
        print(f"[EXECUTE ACTION] {name}")

        if name == "emergency_cooling":
            state["fan_speed"] = 100
            print("[STATE UPDATE] fan_speed = 100")

        elif name == "workload_isolation":
            state["traffic_load"] = 20
            print("[STATE UPDATE] traffic_load = 20")

        else:
            print(f"[WARNING] Unknown action: {name}")

        return {"status": "success", "type": "EXECUTE", "action": name}

    else:
        raise ValueError(f"Unknown action type: {atype}")