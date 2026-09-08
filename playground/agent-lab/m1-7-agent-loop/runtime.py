"""Day 7（M1.7）最小 scripted Agent Runtime。"""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-6-tool-registry"))

from registry import ToolRegistry  # noqa: E402
from state import AgentState  # noqa: E402


class ResourceProbe:
    """代表一次 runtime session 的临时资源，用计数证明所有退出路径都清理。"""

    def __init__(self) -> None:
        self.opened = 0
        self.closed = 0
        self.active = False

    def open(self) -> None:
        if self.active:
            raise RuntimeError("resource is already open")
        self.active = True
        self.opened += 1

    def close(self) -> None:
        if self.active:
            self.active = False
            self.closed += 1


class ScriptedModel:
    """无内部 cursor；AgentState.model_cursor 是恢复位置的唯一事实来源。"""

    def __init__(self, decisions: list[dict]) -> None:
        self.decisions = deepcopy(decisions)

    def next_decision(self, state: AgentState) -> dict:
        if state.model_cursor >= len(self.decisions):
            raise RuntimeError("script exhausted before final answer")
        decision = deepcopy(self.decisions[state.model_cursor])
        state.model_cursor += 1
        return decision


def final_decision(content: str) -> dict:
    return {"type": "final", "content": content}


def tool_decision(call_id: str, name: str, arguments: dict) -> dict:
    return {"type": "tool_call", "id": call_id, "name": name, "arguments": deepcopy(arguments)}


class AgentRuntime:
    def __init__(self, registry: ToolRegistry, resource: ResourceProbe) -> None:
        self.registry = registry
        self.resource = resource

    def run(
        self,
        state: AgentState,
        model: ScriptedModel,
        *,
        caller_permissions: frozenset[str] = frozenset(),
        should_cancel: Callable[[AgentState], bool] | None = None,
        should_interrupt: Callable[[AgentState], bool] | None = None,
    ) -> AgentState:
        if state.status not in {"created", "paused"}:
            raise ValueError(f"state {state.status!r} cannot start or resume")

        self.resource.open()
        state.transition("running")
        try:
            while state.status == "running":
                # cancel / interrupt 只在完整 step 边界检查
                if should_cancel is not None and should_cancel(state):
                    state.transition("cancelled", "cancelled")
                    break
                if should_interrupt is not None and should_interrupt(state):
                    state.transition("paused", "interrupted")
                    break
                if state.step_count >= state.max_steps:
                    state.transition("failed", "max_steps")
                    break

                try:
                    decision = model.next_decision(state)
                    state.step_count += 1
                    self._apply_decision(state, decision, caller_permissions)
                except Exception as exc:
                    state.tool_trace.append({
                        "kind": "runtime_error",
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    state.transition("failed", "model_error")
        finally:
            self.resource.close()
        return state

    def _apply_decision(
        self, state: AgentState, decision: dict, caller_permissions: frozenset[str]
    ) -> None:
        if not isinstance(decision, dict):
            raise ValueError("model decision must be an object")
        decision_type = decision.get("type")
        if decision_type == "final":
            content = decision.get("content")
            if not isinstance(content, str) or content == "":
                raise ValueError("final answer must be a non-empty string")
            state.messages.append({"role": "assistant", "content": content})
            state.final_answer = content
            state.transition("completed", "final_answer")
            return
        if decision_type != "tool_call":
            raise ValueError(f"unknown decision type {decision_type!r}")

        call_id = decision.get("id")
        name = decision.get("name")
        arguments = decision.get("arguments")
        if not isinstance(call_id, str) or not isinstance(name, str) or not isinstance(arguments, dict):
            raise ValueError("malformed tool decision")

        state.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": call_id,
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                },
            }],
        })
        outcome = self.registry.dispatch(name, arguments, caller_permissions)
        tool_content = (
            json.dumps(outcome.result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if outcome.ok
            else json.dumps({"ok": False, "stage": outcome.stage, "reason": outcome.reason_code},
                            ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
        state.messages.append({"role": "tool", "tool_call_id": call_id, "content": tool_content})
        state.tool_trace.append({
            "call_id": call_id,
            "name": name,
            "arguments": deepcopy(arguments),
            "ok": outcome.ok,
            "stage": outcome.stage,
            "reason": outcome.reason_code,
            "result": deepcopy(outcome.result),
        })
        if not outcome.ok:
            state.transition("failed", "tool_error")
