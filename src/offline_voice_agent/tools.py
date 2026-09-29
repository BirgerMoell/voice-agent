from __future__ import annotations

import ast
import json
import math
import operator
import os
import signal
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: JsonObject
    handler: Callable[..., Any]

    def ollama_schema(self) -> JsonObject:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> ToolRegistry:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool
        return self

    def schemas(self) -> list[JsonObject]:
        return [tool.ollama_schema() for tool in self._tools.values()]

    def call(self, name: str, arguments: JsonObject | str | None) -> JsonObject:
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        try:
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            value = self._tools[name].handler(**(arguments or {}))
            return value if isinstance(value, dict) else {"result": value}
        # A tool is an extension boundary: third-party handlers must become observations instead
        # of terminating the live audio loop, regardless of their exception type.
        except Exception as error:  # noqa: BLE001
            return {"error": str(error), "tool": name}

    def __contains__(self, name: str) -> bool:
        return name in self._tools


OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def safe_calculate(expression: str) -> JsonObject:
    if len(expression) > 100:
        raise ValueError("Expression is too long")

    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("Exponent is too large")
            return OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](evaluate(node.operand))
        raise ValueError("Only numbers and arithmetic operators are allowed")

    value = evaluate(ast.parse(expression, mode="eval"))
    if not math.isfinite(float(value)):
        raise ValueError("Result is not finite")
    return {"expression": expression, "result": value}


def calculator_tool() -> Tool:
    return Tool(
        name="calculate",
        description="Evaluate arithmetic safely and exactly.",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        handler=safe_calculate,
    )


def run_bash(command: str, timeout_seconds: int = 30, cwd: str | None = None) -> JsonObject:
    """Intentionally unrestricted. Only register this tool in explicitly opted-in apps."""
    timeout_seconds = max(1, min(int(timeout_seconds), 300))
    working_directory = str(Path(cwd or os.getcwd()).resolve())
    process = subprocess.Popen(
        ["/bin/bash", "-lc", command], cwd=working_directory, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True,
    )
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
    output = output or ""
    if len(output) > 12_000:
        output = output[:6_000] + "\n...[truncated]...\n" + output[-6_000:]
    return {
        "command": command, "cwd": working_directory, "exit_code": process.returncode,
        "timed_out": timed_out, "output": output,
    }


def bash_tool(cwd: str | None = None) -> Tool:
    return Tool(
        name="run_bash",
        description="Run any Bash command as the current OS user. This tool is unrestricted.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 300},
            },
            "required": ["command"],
        },
        handler=lambda command, timeout_seconds=30: run_bash(command, timeout_seconds, cwd),
    )
