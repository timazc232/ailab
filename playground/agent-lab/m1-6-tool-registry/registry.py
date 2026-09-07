"""Day 6（M1.6）最小 Tool Registry / Dispatch。

统一边界：lookup → authorization → args validation → execution → normalized result。
ToolSpec 使用 frozen dataclass；参数 schema 用不可变 ArgSpec tuple，避免注册后漂移。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class DuplicateToolError(ValueError):
    pass


@dataclass(frozen=True)
class ArgSpec:
    name: str
    type_name: str  # number / string


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_schema: tuple[ArgSpec, ...]
    required_permissions: frozenset[str]
    side_effect: bool
    function: Callable[..., object]


@dataclass
class DispatchResult:
    ok: bool
    stage: str  # success / lookup / authorization / validation / execution
    reason_code: str | None
    detail: str
    result: object | None
    tool_name: str
    tool_calls_executed: int
    total_calls_executed: int


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._execution_counts: dict[str, int] = {}

    def register(self, spec: ToolSpec) -> None:
        if not spec.name:
            raise ValueError("tool name must not be empty")
        if spec.name in self._tools:
            raise DuplicateToolError(f"tool name {spec.name!r} is already registered")
        self._tools[spec.name] = spec
        self._execution_counts[spec.name] = 0

    def inventory(self, caller_permissions: frozenset[str]) -> list[dict]:
        """只暴露当前调用者有权使用的工具，按 name 确定性排序。"""
        visible = [
            spec
            for spec in self._tools.values()
            if spec.required_permissions.issubset(caller_permissions)
        ]
        visible.sort(key=lambda spec: spec.name)
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "args_schema": [
                    {"name": arg.name, "type": arg.type_name} for arg in spec.args_schema
                ],
                "side_effect": spec.side_effect,
            }
            for spec in visible
        ]

    def dispatch(
        self,
        tool_name: str,
        arguments: object,
        caller_permissions: frozenset[str],
    ) -> DispatchResult:
        # 1. lookup
        spec = self._tools.get(tool_name)
        if spec is None:
            return self._failure("lookup", "unknown_tool", "tool is not registered", tool_name)

        # 2. authorization：先鉴权，避免未授权调用者获取 schema 细节
        if not spec.required_permissions.issubset(caller_permissions):
            return self._failure(
                "authorization", "denied", "caller is not authorized for this tool", tool_name
            )

        # 3. args validation
        valid, detail = self._validate_args(spec, arguments)
        if not valid:
            return self._failure("validation", "invalid_args", detail, tool_name)

        # 4. execution：计数器紧贴函数入口；即使函数随后抛错，也算实际执行过
        self._execution_counts[tool_name] += 1
        try:
            value = spec.function(**arguments)
        except Exception as exc:
            return self._failure(
                "execution",
                "tool_error",
                f"{type(exc).__name__}: {exc}",
                tool_name,
            )

        return DispatchResult(
            True,
            "success",
            None,
            "executed",
            value,
            tool_name,
            self._execution_counts[tool_name],
            self.total_execution_count,
        )

    def execution_count(self, tool_name: str) -> int:
        return self._execution_counts.get(tool_name, 0)

    @property
    def total_execution_count(self) -> int:
        return sum(self._execution_counts.values())

    def _failure(
        self, stage: str, reason_code: str, detail: str, tool_name: str
    ) -> DispatchResult:
        return DispatchResult(
            False,
            stage,
            reason_code,
            detail,
            None,
            tool_name,
            self.execution_count(tool_name),
            self.total_execution_count,
        )

    @staticmethod
    def _validate_args(spec: ToolSpec, arguments: object) -> tuple[bool, str]:
        if not isinstance(arguments, dict):
            return False, "arguments must be an object"
        required = {arg.name for arg in spec.args_schema}
        if set(arguments) != required:
            return False, f"arguments must contain exactly {sorted(required)}"
        for arg in spec.args_schema:
            value = arguments[arg.name]
            if arg.type_name == "number":
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    return False, f"argument {arg.name!r} must be number"
            elif arg.type_name == "string":
                if not isinstance(value, str) or value == "":
                    return False, f"argument {arg.name!r} must be non-empty string"
            else:
                return False, f"unsupported schema type {arg.type_name!r}"
        return True, "ok"


def add(a: int | float, b: int | float) -> int | float:
    return a + b


def divide(a: int | float, b: int | float) -> float:
    return a / b


def restricted_report(name: str) -> dict:
    # 合成结果；不访问任何真实服务或数据
    return {"name": name, "status": "synthetic-ok"}


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            "add",
            "Add two numbers",
            (ArgSpec("a", "number"), ArgSpec("b", "number")),
            frozenset(),
            False,
            add,
        )
    )
    registry.register(
        ToolSpec(
            "divide",
            "Divide a by b",
            (ArgSpec("a", "number"), ArgSpec("b", "number")),
            frozenset(),
            False,
            divide,
        )
    )
    registry.register(
        ToolSpec(
            "restricted_report",
            "Read a synthetic restricted report",
            (ArgSpec("name", "string"),),
            frozenset({"report:read"}),
            False,
            restricted_report,
        )
    )
    return registry
