# ======================================================
# BOUND Evaluator FINAL
# ======================================================

from backend.runtime.resolver import resolve


def compare(left, operator, right):
    ops = {
        ">":  lambda a, b: a > b,
        "<":  lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
    }

    if operator not in ops:
        raise ValueError(f"Unsupported operator: {operator}")

    return ops[operator](left, right)


def evaluate_rule(rule, state):
    cond = rule["condition"]

    metric = cond["left"]

    if metric not in state:
        raise ValueError(f"Missing metric: {metric}")

    left = resolve(state[metric])
    right = resolve(cond["right"])

    # SAFETY FINAL CHECK
    if str(type(left)) == "<class 'lark.tree.Tree'>" or str(type(right)) == "<class 'lark.tree.Tree'>":
        raise TypeError("AST not resolved properly")

    return compare(left, cond["operator"], right)


def evaluate_rules(rules, state):
    return [r for r in rules if evaluate_rule(r, state)]