# ======================================================
# BOUND Unit Tests — Runtime Integration
# File: backend/tests/test_runtime.py
# ======================================================

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from language.parser     import parse_source
from runtime.policy_runtime import PolicyRuntime

POLICY = """
POLICY datacenter_safety

METRIC cpu_temp NUMBER
METRIC fan_speed PERCENT
METRIC traffic_load PERCENT

RULE thermal_warning
WHEN cpu_temp > 70
THEN EMIT thermal_alert

RULE thermal_critical
WHEN cpu_temp > 90
THEN EXECUTE emergency_cooling
THEN EXECUTE workload_isolation
"""


@pytest.fixture
def runtime():
    ast = parse_source(POLICY)
    return PolicyRuntime(ast)


# ======================================================
# STATE MANAGER TESTS
# ======================================================

def test_initial_state_zero(runtime):
    state = runtime.get_state()
    assert state["cpu_temp"]     == 0
    assert state["fan_speed"]    == 0
    assert state["traffic_load"] == 0


def test_update_metric(runtime):
    runtime.update_metric("cpu_temp", 95)
    assert runtime.get_state()["cpu_temp"] == 95


def test_update_unknown_metric_raises(runtime):
    with pytest.raises(ValueError):
        runtime.update_metric("unknown_metric", 99)


# ======================================================
# RUNTIME CYCLE TESTS
# ======================================================

def test_no_rules_triggered_below_threshold(runtime):
    runtime.update_metric("cpu_temp", 50)
    results = runtime.runtime_cycle()
    assert results == []


def test_warning_rule_triggered(runtime):
    runtime.update_metric("cpu_temp", 80)
    results = runtime.runtime_cycle()
    rules   = [r["rule"] for r in results]
    assert "thermal_warning" in rules


def test_critical_rule_triggered(runtime):
    runtime.update_metric("cpu_temp", 95)
    results = runtime.runtime_cycle()
    rules   = [r["rule"] for r in results]
    assert "thermal_critical" in rules


def test_emergency_cooling_sets_fan_speed(runtime):
    runtime.update_metric("cpu_temp", 95)
    runtime.runtime_cycle()
    assert runtime.get_state()["fan_speed"] == 100


def test_workload_isolation_sets_traffic_load(runtime):
    runtime.update_metric("cpu_temp", 95)
    runtime.runtime_cycle()
    assert runtime.get_state()["traffic_load"] == 20


def test_determinism_same_state_same_result(runtime):
    """Same state must always produce same results — core BOUND guarantee."""
    runtime.update_metric("cpu_temp", 95)
    runtime.update_metric("fan_speed", 40)
    runtime.update_metric("traffic_load", 85)

    ast     = parse_source(POLICY)
    runtime2 = PolicyRuntime(ast)
    runtime2.update_metric("cpu_temp", 95)
    runtime2.update_metric("fan_speed", 40)
    runtime2.update_metric("traffic_load", 85)

    results1 = [r["rule"] for r in runtime.runtime_cycle()]
    results2 = [r["rule"] for r in runtime2.runtime_cycle()]

    assert results1 == results2