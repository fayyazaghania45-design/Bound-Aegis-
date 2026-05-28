# ======================================================
# BOUND Unit Tests — Evaluator
# File: backend/tests/test_evaluator.py
# ======================================================

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from runtime.evaluator import compare, evaluate_rule, evaluate_rules


# ======================================================
# compare()
# ======================================================

def test_compare_gt_true():
    assert compare(95, ">", 90) is True

def test_compare_gt_false():
    assert compare(80, ">", 90) is False

def test_compare_lt_true():
    assert compare(40, "<", 70) is True

def test_compare_gte_equal():
    assert compare(90, ">=", 90) is True

def test_compare_lte_equal():
    assert compare(90, "<=", 90) is True

def test_compare_eq_true():
    assert compare(100, "==", 100) is True

def test_compare_eq_false():
    assert compare(99, "==", 100) is False

def test_compare_invalid_operator():
    with pytest.raises(ValueError):
        compare(1, "!=", 2)


# ======================================================
# evaluate_rule()
# ======================================================

RULE_GT = {
    "name"      : "thermal_warning",
    "condition" : {"left": "cpu_temp", "operator": ">", "right": 70},
    "actions"   : []
}

def test_evaluate_rule_true():
    assert evaluate_rule(RULE_GT, {"cpu_temp": 95}) is True

def test_evaluate_rule_false():
    assert evaluate_rule(RULE_GT, {"cpu_temp": 60}) is False

def test_evaluate_rule_missing_metric():
    with pytest.raises(ValueError):
        evaluate_rule(RULE_GT, {"fan_speed": 50})


# ======================================================
# evaluate_rules() — determinism tests
# ======================================================

RULES = [
    {
        "name"      : "thermal_warning",
        "condition" : {"left": "cpu_temp", "operator": ">", "right": 70},
        "actions"   : []
    },
    {
        "name"      : "thermal_critical",
        "condition" : {"left": "cpu_temp", "operator": ">", "right": 90},
        "actions"   : []
    }
]

def test_both_rules_active():
    active = evaluate_rules(RULES, {"cpu_temp": 95})
    names  = [r["name"] for r in active]
    assert "thermal_warning"  in names
    assert "thermal_critical" in names

def test_only_warning_active():
    active = evaluate_rules(RULES, {"cpu_temp": 80})
    names  = [r["name"] for r in active]
    assert "thermal_warning"  in names
    assert "thermal_critical" not in names

def test_no_rules_active():
    active = evaluate_rules(RULES, {"cpu_temp": 50})
    assert active == []

def test_same_input_same_output():
    """Determinism: same state always produces same active rules."""
    state = {"cpu_temp": 95}
    assert evaluate_rules(RULES, state) == evaluate_rules(RULES, state)s