# ======================================================
# BOUND Runtime Intelligence Layer (LOMBA READY)
# ======================================================

class RuntimeIntelligence:

    def __init__(self):
        self.event_log = []
        self.anomaly_score = 0

    # ==================================================
    # EVENT LOGGER (TIMELINE)
    # ==================================================
    def log_event(self, event_type, name, state):
        self.event_log.append({
            "type": event_type,
            "name": name,
            "state": dict(state)
        })

    def get_timeline(self):
        return self.event_log[-20:]

    # ==================================================
    # ANOMALY SCORE (RULE-BASED AI FEEL)
    # ==================================================
    def compute_anomaly(self, cpu_temp, fan_speed, traffic_load):

        score = 0

        if cpu_temp > 100:
            score += 50
        elif cpu_temp > 90:
            score += 30
        elif cpu_temp > 80:
            score += 10

        if fan_speed < 50:
            score += 30

        if traffic_load > 85:
            score += 20

        self.anomaly_score = min(score, 100)
        return self.anomaly_score