# ======================================================
# BOUND Event Logger v2.0
# File: backend/logging/event_logger.py
# ======================================================

import json
from datetime import datetime
from pathlib import Path

LOG_DIR  = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "bound_events.log"

INFO    = "INFO"
WARNING = "WARNING"
ERROR   = "ERROR"
ACTION  = "ACTION"


class EventLogger:

    def __init__(self, log_to_file=True, log_to_console=True):
        self.log_to_file    = log_to_file
        self.log_to_console = log_to_console
        self.history        = []
        if self.log_to_file:
            LOG_DIR.mkdir(parents=True, exist_ok=True)

    def _log(self, level, message, context=None):
        entry = {
            "timestamp" : datetime.now().isoformat(),
            "level"     : level,
            "message"   : message,
            "context"   : context or {}
        }
        self.history.append(entry)
        line = f"[{entry['timestamp']}] [{level}] {message}"
        if context:
            line += f" | {json.dumps(context)}"
        if self.log_to_console:
            print(line)
        if self.log_to_file:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        return entry

    def info(self, msg, ctx=None):    return self._log(INFO, msg, ctx)
    def warning(self, msg, ctx=None): return self._log(WARNING, msg, ctx)
    def error(self, msg, ctx=None):   return self._log(ERROR, msg, ctx)
    def action(self, msg, ctx=None):  return self._log(ACTION, msg, ctx)

    def get_history(self):
        return self.history