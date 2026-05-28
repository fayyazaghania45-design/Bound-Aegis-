# ======================================================
# BOUND REST API vFINAL - FULL FIXED VERSION
# ======================================================

import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# ======================================================
# ROOT SETUP
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ======================================================
# IMPORT CORE MODULES
# ======================================================

from backend.language.parser import parse_policy
from backend.runtime.policy_runtime import PolicyRuntime
from backend.simulation.thermal_simulation import ThermalSimulation
from backend.observability.telemetry_stream import TelemetryStream
from backend.bound_logging.event_logger import EventLogger

# ======================================================
# FLASK INIT
# ======================================================

app = Flask(__name__)
CORS(app)

LOCK = threading.Lock()

# ======================================================
# LOAD POLICY
# ======================================================

POLICY_PATH = ROOT_DIR / "policies" / "datacenter.bound"

ast = parse_policy(POLICY_PATH)

# ======================================================
# CORE SYSTEMS
# ======================================================

runtime = PolicyRuntime(ast)

sim = ThermalSimulation()

telemetry = TelemetryStream(
    write_to_file=False
)

logger = EventLogger(
    log_to_file=False,
    log_to_console=True
)

# ======================================================
# ACTION REGISTRY
# ======================================================

ACTION_REGISTRY = {
    "emergency_cooling":
        sim.apply_emergency_cooling,

    "workload_isolation":
        sim.apply_workload_isolation
}

# ======================================================
# DASHBOARD ROUTES
# ======================================================

@app.route("/")
def dashboard():

    return send_from_directory(
        str(ROOT_DIR / "dashboard"),
        "index.html"
    )


@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(
        str(ROOT_DIR / "dashboard"),
        path
    )

# ======================================================
# API : STATE
# ======================================================

@app.route("/api/runtime/state", methods=["GET"])
def get_state():

    return jsonify({
        "status": "ok",
        "state": runtime.get_state()
    })

# ======================================================
# API : RULES
# ======================================================

@app.route("/api/runtime/rules", methods=["GET"])
def get_rules():

    formatted_rules = []

    for rule in ast.get("rules", []):

        cond = rule.get("condition", {})

        right = cond.get("right")

        # ==========================================
        # FIX TREE(Token...) DISPLAY BUG
        # ==========================================

        try:

            if hasattr(right, "children"):
                right = right.children[0]

            right = str(right)

        except:
            right = str(right)

        condition_text = (
            f"{cond.get('left')} "
            f"{cond.get('operator')} "
            f"{right}"
        )

        formatted_rules.append({

            "name":
                rule.get("name", "unknown"),

            "condition":
                condition_text,

            "actions": [

                a.get("event") or
                a.get("action")

                for a in rule.get("actions", [])
            ]
        })

    return jsonify({

        "status": "ok",

        "policy":
            ast.get("policy", "unknown"),

        "rules":
            formatted_rules
    })

# ======================================================
# API : TELEMETRY
# ======================================================

@app.route("/api/runtime/telemetry", methods=["GET"])
def get_telemetry():

    return jsonify({

        "status": "ok",

        "snapshots":
            telemetry.get_all()
    })

# ======================================================
# API : UPDATE METRIC
# ======================================================

@app.route("/api/runtime/metric", methods=["POST"])
def update_metric():

    data = request.get_json()

    if not data:

        return jsonify({
            "status": "error",
            "message": "Missing JSON body"
        }), 400

    if "name" not in data or "value" not in data:

        return jsonify({
            "status": "error",
            "message": "Required fields: name, value"
        }), 400

    try:

        runtime.update_metric(
            data["name"],
            data["value"]
        )

        logger.info(
            f"Metric updated: "
            f"{data['name']} = {data['value']}"
        )

        return jsonify({

            "status": "ok",

            "metric":
                data["name"],

            "value":
                data["value"]
        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 400

# ======================================================
# API : RUNTIME CYCLE
# ======================================================

@app.route("/api/runtime/cycle", methods=["POST"])
def runtime_cycle():

    with LOCK:

        results = runtime.runtime_cycle()

        current_state = runtime.get_state()

        active_rule_names = sorted({

            r.get("rule",
            r.get("name", "unknown"))

            for r in results
        })

        active_rules = [

            r for r in ast.get("rules", [])

            if r.get("name")
            in active_rule_names
        ]

        snapshot = telemetry.record(

            state=current_state,

            active_rules=active_rules,

            results=results
        )

        return jsonify({

            "status": "ok",

            "cycle":
                snapshot.get("cycle"),

            "state":
                current_state,

            "active_rules":
                active_rule_names,

            "results":
                results
        })

# ======================================================
# API : SIMULATION ENGINE
# ======================================================

@app.route("/api/runtime/simulate", methods=["POST"])
def simulate():

    data = request.get_json() or {}

    cycles = min(
        int(data.get("cycles", 5)),
        10
    )

    load = float(
        data.get("load", 80.0)
    )

    sim.set_load(load)

    snapshots = []

    for _ in range(cycles):

        sim_state = sim.step()

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

        with LOCK:

            results = runtime.runtime_cycle()

        # ==========================================
        # EXECUTE ACTIONS
        # ==========================================

        for result in results:

            action = result.get("action", {})

            if action.get("type") == "EXECUTE":

                action_name = action.get("action")

                executor = ACTION_REGISTRY.get(
                    action_name
                )

                if executor:
                    executor()

        current_state = runtime.get_state()

        active_rule_names = sorted({

            r.get("rule",
            r.get("name", "unknown"))

            for r in results
        })

        active_rules = [

            r for r in ast.get("rules", [])

            if r.get("name")
            in active_rule_names
        ]

        snapshot = telemetry.record(

            state=current_state,

            active_rules=active_rules,

            results=results
        )

        snapshots.append(snapshot)

    return jsonify({

        "status": "ok",

        "cycles":
            cycles,

        "load":
            load,

        "snapshots":
            snapshots
    })

# ======================================================
# API : HEALTH CHECK
# ======================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({

        "status": "ok",

        "service":
            "BOUND Runtime API"
    })

# ======================================================
# MAIN ENTRY
# ======================================================

if __name__ == "__main__":

    print("\n======================================")
    print("BOUND Runtime API Running")
    print("======================================")
    print("Dashboard URL : http://127.0.0.1:5000/")
    print("API URL       : http://127.0.0.1:5000/api/runtime")
    print("======================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )