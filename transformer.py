# ======================================================
# BOUND Transformer v2.2 FINAL FIX
# File: backend/language/transformer.py
# ======================================================

from lark import Transformer


class BoundTransformer(Transformer):

    # ==================================================
    # BASIC VALUES
    # ==================================================

    def IDENTIFIER(self, token):
        return str(token)

    def NUMBER(self, token):

        value = str(token)

        if "." in value:
            return float(value)

        return int(value)

    def STRING(self, token):
        return str(token)[1:-1]

    # ==================================================
    # COMPARATORS
    # ==================================================

    def GT(self, token):
        return ">"

    def LT(self, token):
        return "<"

    def GTE(self, token):
        return ">="

    def LTE(self, token):
        return "<="

    def EQ(self, token):
        return "=="

    def comparator(self, items):
        return items[0]

    # ==================================================
    # POLICY
    # ==================================================

    def policy_decl(self, items):

        return {
            "type": "POLICY",
            "name": items[0]
        }

    # ==================================================
    # METRIC
    # ==================================================

    def metric_type(self, items):
        return str(items[0])

    def metric_decl(self, items):

        return {
            "type": "METRIC",
            "name": items[0],
            "metric_type": items[1]
        }

    # ==================================================
    # CONDITION
    # ==================================================

    def condition(self, items):

        return {
            "left": items[0],
            "operator": items[1],
            "right": items[2]
        }

    def when_clause(self, items):
        return items[0]

    # ==================================================
    # ACTIONS
    # ==================================================

    def emit_action(self, items):

        return {
            "type": "EMIT",
            "event": items[0]
        }

    def execute_action(self, items):

        return {
            "type": "EXECUTE",
            "action": items[0]
        }

    def action(self, items):
        return items[0]

    def then_clause(self, items):
        return items[0]

    # ==================================================
    # RULE
    # ==================================================

    def rule_decl(self, items):

        name = items[0]
        condition = items[1]
        actions = items[2:]

        return {
            "type": "RULE",
            "name": name,
            "condition": condition,
            "actions": actions
        }

    # ==================================================
    # ROOT
    # ==================================================

    def start(self, items):

        policy = None
        metrics = []
        rules = []

        for item in items:

            if item["type"] == "POLICY":
                policy = item["name"]

            elif item["type"] == "METRIC":
                metrics.append(item)

            elif item["type"] == "RULE":
                rules.append(item)

        return {
            "policy": policy,
            "metrics": metrics,
            "rules": rules
        }