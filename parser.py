# ======================================================
# BOUND Parser v2.1
# File: backend/language/parser.py
# ======================================================

from pathlib import Path

from lark import Lark

from backend.language.transformer import BoundTransformer

# ======================================================
# GRAMMAR PATH
# ======================================================

GRAMMAR_PATH = (
    Path(__file__).resolve().parent
    / "grammar.lark"
)

# ======================================================
# LOAD GRAMMAR
# ======================================================

with open(
    GRAMMAR_PATH,
    "r",
    encoding="utf-8"
) as f:

    GRAMMAR = f.read()

# ======================================================
# CREATE PARSER
# ======================================================

parser = Lark(
    GRAMMAR,
    parser="lalr",
    transformer=BoundTransformer()
)

# ======================================================
# PARSE POLICY
# ======================================================

def parse_policy(policy_path):

    """
    Parse .bound policy file into AST.

    Example:
        ast = parse_policy(
            "policies/datacenter.bound"
        )
    """

    policy_path = Path(policy_path)

    if not policy_path.exists():

        raise FileNotFoundError(
            f"Policy file not found: {policy_path}"
        )

    with open(
        policy_path,
        "r",
        encoding="utf-8"
    ) as f:

        source = f.read()

    ast = parser.parse(source)

    return ast