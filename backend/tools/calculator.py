import ast
import operator
import re
from typing import Optional

from tools.base import BaseTool, ToolResult

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Matches any contiguous run of digits/operators/parens/whitespace.
_TOKEN_RUN_RE = re.compile(r"[\d.\+\-\*/%^()\s]+")


class CalculatorTool(BaseTool):
    name = "CalculatorTool"
    description = "Performs basic arithmetic (+, -, *, /, %, ^, parentheses) found in the task text."

    def can_handle(self, task: str) -> bool:
        expr = self._extract_expression(task)
        if expr is None:
            return False
        try:
            ast.parse(expr.replace("^", "**"), mode="eval")
            return True
        except SyntaxError:
            return False

    def execute(self, task: str) -> ToolResult:
        expr = self._extract_expression(task)
        if expr is None:
            return ToolResult(success=False, output=None, error="No arithmetic expression found in task")
        try:
            normalized = expr.replace("^", "**")
            value = self._safe_eval(normalized)
            return ToolResult(success=True, output=value)
        except ZeroDivisionError:
            return ToolResult(success=False, output=None, error="Division by zero")
        except Exception as exc:  # noqa: BLE001 - surfaced to caller as a tool error
            return ToolResult(success=False, output=None, error=f"Could not evaluate expression '{expr}': {exc}")

    @staticmethod
    def _extract_expression(task: str) -> Optional[str]:
        """Find the longest run of numeric/operator characters that
        actually contains both a digit and an operator - this avoids
        false-positives on plain sentences with no math in them."""
        best = None
        for match in _TOKEN_RUN_RE.finditer(task):
            candidate = match.group(0).strip()
            # Strip trailing operators left by incomplete input (e.g. "5 + 10 -")
            candidate = re.sub(r"[+\-*/%^]\s*$", "", candidate).strip()
            if re.search(r"\d", candidate) and re.search(r"[+\-*/%^]", candidate):
                if best is None or len(candidate) > len(best):
                    best = candidate
        return best

    @classmethod
    def _safe_eval(cls, expr: str):
        node = ast.parse(expr, mode="eval").body
        return cls._eval_node(node)

    @classmethod
    def _eval_node(cls, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed")
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](cls._eval_node(node.left), cls._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](cls._eval_node(node.operand))
        raise ValueError("Unsupported expression syntax")
