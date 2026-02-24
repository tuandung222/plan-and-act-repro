from __future__ import annotations

import ast
import math
from typing import Any

_ALLOWED_FUNCS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "exp": math.exp,
}

_ALLOWED_CONSTS = {
    "pi": math.pi,
    "e": math.e,
}


class _SafeEval:
    def eval(self, expression: str) -> float:
        node = ast.parse(expression, mode="eval")
        return float(self._visit(node.body))

    def _visit(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = self._visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value

        if isinstance(node, ast.BinOp):
            left = self._visit(node.left)
            right = self._visit(node.right)

            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            if isinstance(node.op, ast.Pow):
                return left**right
            raise ValueError("Unsupported binary operator")

        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_CONSTS:
                return float(_ALLOWED_CONSTS[node.id])
            raise ValueError(f"Unsupported symbol: {node.id}")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = _ALLOWED_FUNCS.get(node.func.id)
            if fn is None:
                raise ValueError(f"Unsupported function: {node.func.id}")
            args = [self._visit(arg) for arg in node.args]
            return float(fn(*args))

        raise ValueError("Unsupported expression")


class CalculatorTool:
    name = "calculator"

    def __init__(self) -> None:
        self._safe_eval = _SafeEval()

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        expression = str(arguments.get("expression", "")).strip()
        if not expression:
            expression = str(arguments.get("query", "")).strip()

        if not expression:
            return {"ok": False, "error": "Missing expression"}

        try:
            value = self._safe_eval.eval(expression)
        except Exception as exc:
            return {
                "ok": False,
                "expression": expression,
                "error": str(exc),
            }

        return {
            "ok": True,
            "expression": expression,
            "result": value,
        }
