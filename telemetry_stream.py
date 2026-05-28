# ======================================================
# BOUND Telemetry Stream v2.0
# File: backend/observability/telemetry_stream.py
# ======================================================

import json
from datetime import datetime
from pathlib import Path

TELEMETRY_DIR  = Path(__file__).resolve().parent.parent.parent / "logs"
TELEMETRY_FILE = TELEMETRY_DIR / "telemetry.jsonl"


class TelemetryStream:

    def __init__(self, write_to_file=True):
        self.write_to_file = write_to_file
        self.snapshots     = []
        self.cycle_count   = 0
        if self.write_to_file:
            TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)

    def record(self, state, active_rules=None, results=None):
        self.cycle_count += 1
        snapshot = {
            "cycle"        : self.cycle_count,
            "timestamp"    : datetime.now().isoformat(),
            "state"        : dict(state),
            "active_rules" : [r["name"] for r in (active_rules or [])],
            "results"      : results or []
        }
        self.snapshots.append(snapshot)
        if self.write_to_file:
            with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(snapshot) + "\n")
        return snapshot

    def get_latest(self):
        return self.snapshots[-1] if self.snapshots else None

    def get_all(self):
        return self.snapshots

    def get_metric_history(self, metric_name):
        return [
            {"cycle": s["cycle"], "timestamp": s["timestamp"], "value": s["state"].get(metric_name)}
            for s in self.snapshots
        ]

    def print_metric_trend(self, metric_name):
        history = self.get_metric_history(metric_name)
        print(f"\n[TELEMETRY TREND] {metric_name}")
        print("--------------------------------------")
        for e in history:
            bar = "█" * int((e["value"] or 0) // 5)
            print(f"  Cycle {e['cycle']:>3} | {bar} {e['value']}")
        print("--------------------------------------\n")