"""Day 5（M1.5）最小可信 Tool Executor。

模型只提出 tool call；本地代码依次做 selection、invocation validation、execution。
未知 / 危险 / 参数非法路径不得进入工具函数；calls_executed 是实际函数入口证据。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

DENIED_TOOLS = frozenset({"run_shell"})


def add(a: int | float, b: int | float) -> int | float:
    return a + b


def abs_diff(a: int | float, b: int | float) -> int | float:
    return abs(a - b)


ALLOWED_TOOLS: dict[str, Callable[..., int | float]] = {
    "add": add,
    "abs_diff": abs_diff,
}


@dataclass
class ToolOutcome:
    ok: bool
    stage: str  # success / selection / invocation / execution
    reason_code: str | None
    detail: str
    result: int | float | None
    tool_message: dict | None
    calls_executed: int


class ToolExecutor:
    def __init__(self) -> None:
        self.calls_executed = 0
        self.execution_log: list[dict] = []

    def execute_one(self, assistant_message: dict) -> ToolOutcome:
        extracted = self._extract_call(assistant_message)
        if isinstance(extracted, ToolOutcome):
            return extracted
        call_id, name, arguments_text = extracted

        # selection：先判断工具是否允许存在于执行面
        if name in DENIED_TOOLS:
            return self._reject("selection", "denied_tool", f"tool {name!r} is explicitly denied")
        if name not in ALLOWED_TOOLS:
            return self._reject("selection", "unknown_tool", f"tool {name!r} is not in allowlist")

        # invocation validation：工具合法，但参数必须先满足本地 schema
        args_result = self._validate_args(arguments_text)
        if isinstance(args_result, ToolOutcome):
            return args_result

        # 只有过了前两道边界才进入函数；计数器紧贴实际函数入口
        self.calls_executed += 1
        self.execution_log.append({"name": name, "arguments": args_result.copy()})
        try:
            value = ALLOWED_TOOLS[name](**args_result)
        except Exception as exc:  # 执行异常与 selection / invocation 分开记录
            return ToolOutcome(
                False,
                "execution",
                "tool_error",
                f"{type(exc).__name__}: {exc}",
                None,
                None,
                self.calls_executed,
            )

        tool_message = {
            "role": "tool",
            "tool_call_id": call_id,
            "content": json.dumps(value, ensure_ascii=False, separators=(",", ":")),
        }
        return ToolOutcome(
            True,
            "success",
            None,
            "executed and tool result message created",
            value,
            tool_message,
            self.calls_executed,
        )

    def _extract_call(self, assistant_message: dict):
        calls = assistant_message.get("tool_calls") if isinstance(assistant_message, dict) else None
        if not isinstance(calls, list) or len(calls) != 1:
            return self._reject("selection", "invalid_tool_call", "expected exactly one tool call")
        call = calls[0]
        function = call.get("function") if isinstance(call, dict) else None
        call_id = call.get("id") if isinstance(call, dict) else None
        if (
            call.get("type") != "function"
            or not isinstance(call_id, str)
            or not isinstance(function, dict)
            or not isinstance(function.get("name"), str)
            or not isinstance(function.get("arguments"), str)
        ):
            return self._reject("selection", "invalid_tool_call", "malformed tool call envelope")
        return call_id, function["name"], function["arguments"]

    def _validate_args(self, arguments_text: str):
        try:
            args = json.loads(arguments_text)
        except json.JSONDecodeError as exc:
            return self._reject("invocation", "invalid_args", f"arguments are invalid JSON: {exc.msg}")
        if not isinstance(args, dict):
            return self._reject("invocation", "invalid_args", "arguments must be an object")
        required = {"a", "b"}
        if set(args) != required:
            return self._reject(
                "invocation",
                "invalid_args",
                f"arguments must contain exactly {sorted(required)}, got {sorted(args)}",
            )
        for key in ("a", "b"):
            value = args[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return self._reject(
                    "invocation", "invalid_args", f"argument {key!r} must be a number"
                )
        return args

    def _reject(self, stage: str, reason_code: str, detail: str) -> ToolOutcome:
        return ToolOutcome(
            False,
            stage,
            reason_code,
            detail,
            None,
            None,
            self.calls_executed,
        )
