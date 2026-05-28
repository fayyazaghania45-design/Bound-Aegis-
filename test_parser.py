# ======================================================
# BOUND Unit Tests — Parser
# File: backend/tests/test_parser.py
# ======================================================

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from language.parser import parse_source


# ======================================================
# FIXTURES
# ======================================================

VALID_POLICY = """
POLICY datacenter_safety

METRIC cpu_temp NUMBER
METRIC fan_speed PERCENT

RULE thermal_warning
WHEN cpu_temp > 70
THEN EMIT thermal_alert

RULE thermal_critical
WHEN cpu_temp > 90
THEN EXECUTE emergency_cooling
THEN EXECUTE workload_isolation
"""


# ======================================================
# TESTS
# ======================================================

def test_parse_returns_ast():
    ast = parse_source(VALID_POLICY)
    assert isinstance(ast, dict)


def test_policy_name():
    ast = parse_source(VALID_POLICY)
    assert ast["policy"] == "datacenter_safety"


def test_metrics_count():
    ast = parse_source(VALID_POLICY)
    assert len(ast["metrics"]) == 2


def test_metric_names():
    ast = parse_source(VALID_POLICY)
    names = [m["name"] for m in ast["metrics"]]
    assert "cpu_temp"  in names
    assert "fan_speed" in names


def test_rules_count():
    ast = parse_source(VALID_POLICY)
    assert len(ast["rules"]) == 2


def test_rule_names():
    ast = parse_source(VALID_POLICY)
    names = [r["name"] for r in ast["rules"]]
    assert "thermal_warning"  in names
    assert "thermal_critical" in names


def test_rule_condition():
    ast  = parse_source(VALID_POLICY)
    rule = next(r for r in ast["rules"] if r["name"] == "thermal_warning")
    cond = rule["condition"]
    assert cond["left"]     == "cpu_temp"
    assert cond["operator"] == ">"
    assert cond["right"]    == 70


def test_rule_emit_action():
    ast  = parse_source(VALID_POLICY)
    rule = next(r for r in ast["rules"] if r["name"] == "thermal_warning")
    assert rule["actions"][0]["type"]  == "EMIT"
    assert rule["actions"][0]["event"] == "thermal_alert"


def test_rule_multiple_actions():
    ast  = parse_source(VALID_POLICY)
    rule = next(r for r in ast["rules"] if r["name"] == "thermal_critical")
    assert len(rule["actions"]) == 2
    assert rule["actions"][0]["action"] == "emergency_cooling"
    assert rule["actions"][1]["action"] == "workload_isolation"


def test_invalid_syntax_raises():
    with pytest.raises(Exception):
        parse_source("INVALID SYNTAX !!!")