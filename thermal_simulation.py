# ======================================================
# BOUND Thermal Simulation v2.0
# File: backend/simulation/thermal_simulation.py
# ======================================================

import random

BASE_TEMP      = 40.0
MAX_TEMP       = 105.0
AMBIENT_TEMP   = 25.0
LOAD_FACTOR    = 0.6
COOLING_FACTOR = 0.15
NOISE_RANGE    = 2.0
FAN_IDLE       = 20
FAN_MAX        = 100
FAN_TEMP_START = 50.0
FAN_TEMP_MAX   = 90.0


class ThermalSimulation:

    def __init__(self):
        self.cpu_temp     = BASE_TEMP
        self.fan_speed    = FAN_IDLE
        self.traffic_load = 0.0
        self.cycle        = 0

    def set_load(self, load_percent):
        self.traffic_load = max(0.0, min(100.0, load_percent))

    def step(self):
        self.cycle += 1

        heat    = (self.traffic_load / 100.0) * LOAD_FACTOR * (MAX_TEMP - AMBIENT_TEMP)
        cooling = (self.fan_speed / 100.0) * COOLING_FACTOR * (self.cpu_temp - AMBIENT_TEMP)
        noise   = random.uniform(-NOISE_RANGE, NOISE_RANGE)

        self.cpu_temp += heat - cooling + noise
        self.cpu_temp  = round(max(AMBIENT_TEMP, min(MAX_TEMP, self.cpu_temp)), 1)
        self.fan_speed = self._auto_fan(self.cpu_temp)

        return self._state()

    def _auto_fan(self, temp):
        if temp <= FAN_TEMP_START: return FAN_IDLE
        if temp >= FAN_TEMP_MAX:   return FAN_MAX
        ratio = (temp - FAN_TEMP_START) / (FAN_TEMP_MAX - FAN_TEMP_START)
        return round(FAN_IDLE + ratio * (FAN_MAX - FAN_IDLE), 1)

    def apply_emergency_cooling(self):
        self.fan_speed = FAN_MAX
        print("[THERMAL SIM] Emergency cooling — fan_speed = 100%")

    def apply_workload_isolation(self):
        self.traffic_load = 20.0
        print("[THERMAL SIM] Workload isolated — traffic_load = 20%")

    def _state(self):
        return {
            "cycle"        : self.cycle,
            "cpu_temp"     : self.cpu_temp,
            "fan_speed"    : self.fan_speed,
            "traffic_load" : self.traffic_load
        }

    def print_status(self):
        s = self._state()
        print(f"\n[THERMAL SIM] Cycle #{s['cycle']}")
        print(f"  cpu_temp     : {s['cpu_temp']:>6.1f}°C  {'█' * int(s['cpu_temp'] / 5)}")
        print(f"  fan_speed    : {s['fan_speed']:>6.1f}%   {'█' * int(s['fan_speed'] / 5)}")
        print(f"  traffic_load : {s['traffic_load']:>6.1f}%   {'█' * int(s['traffic_load'] / 5)}")


if __name__ == "__main__":
    sim = ThermalSimulation()
    sim.set_load(90.0)
    print("\n======================================")
    print("BOUND THERMAL SIMULATION")
    print("======================================")
    for _ in range(15):
        sim.step()
        sim.print_status()