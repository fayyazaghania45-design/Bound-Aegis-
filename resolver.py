# ======================================================
# BOUND AST Resolver FINAL (FIXED)
# ======================================================

from lark import Tree, Token


def resolve(value):
    """
    Mengubah semua bentuk AST (Tree/Token) → primitive (float/int/bool/str)
    """

    # 1. sudah value final
    if isinstance(value, (int, float, bool, str)):
        return value

    # 2. Token dari Lark
    if isinstance(value, Token):
        try:
            return float(value)
        except:
            return str(value)

    # 3. Tree Lark (INI FIX UTAMA)
    if isinstance(value, Tree):

        # kalau cuma 1 child → lanjut turun
        if len(value.children) == 1:
            return resolve(value.children[0])

        # node number
        if value.data in ("number", "float", "int"):
            return float(value.children[0])

        # node string
        if value.data == "string":
            return str(value.children[0])

        # fallback recursive
        return resolve(value.children[0])

    return value