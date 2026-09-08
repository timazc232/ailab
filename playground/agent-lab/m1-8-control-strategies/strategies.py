"""Day 8（M1.8）控制策略层：plan / reflection / approval，构建在 M1.7 Runtime 之上。

不 fork Runtime；策略通过 decision script + 本地确定性 checker + 钩子组合表达。
"""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-7-agent-loop"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-6-tool-registry"))

import json

from registry import ArgSpec, ToolRegistry, ToolSpec  # noqa: E402
from runtime import AgentRuntime, ResourceProbe, ScriptedModel, final_decision, tool_decision  # noqa: E402
from state import AgentState  # noqa: E402


def send_report(content: str) -> dict:
    """副作用工具 stub：只记录调用，不产生真实副作用。"""
    return {"sent": True, "content": content}


APPROVAL_PERMISSION = frozenset({"report:send"})


def build_approval_registry() -> ToolRegistry:
    from registry import add, divide

    registry = ToolRegistry()
    registry.register(ToolSpec("add", "Add two numbers",
                               (ArgSpec("a", "number"), ArgSpec("b", "number")),
                               frozenset(), False, add))
    registry.register(ToolSpec("divide", "Divide a by b",
                               (ArgSpec("a", "number"), ArgSpec("b", "number")),
                               frozenset(), False, divide))
    registry.register(ToolSpec("send_report", "Send a report (side effect, needs approval)",
                               (ArgSpec("content", "string"),),
                               APPROVAL_PERMISSION, True, send_report))
    return registry


class QualityChecker:
    """确定性 checker：模拟 ground truth 判断（非真实模型质量评估）。"""

    def __init__(self, acceptable_answers: set[str]) -> None:
        self.acceptable = acceptable_answers
        self.checks = 0

    def is_acceptable(self, answer: str) -> bool:
        self.checks += 1
        return answer in self.acceptable


class PlanFirstModel(ScriptedModel):
    """p2：第一条 decision 是 plan 消息（type=plan）。"""

    pass


def plan_decision(content: str) -> dict:
    return {"type": "plan", "content": content}


# ---- 策略 p1 / p2：直接复用 M1.7 Runtime，plan 作为 assistant message ----

def run_reactive(user_message: str, decisions: list[dict]):
    state = AgentState.create("p1", user_message, 5)
    model_decisions = len(decisions)
    registry, resource, runtime = _make_runtime()
    result = runtime.run(state, ScriptedModel(decisions))
    return result, registry, resource, model_decisions


def run_plan_first(user_message: str, decisions: list[dict]):
    state = AgentState.create("p2", user_message, 5)
    model_decisions = len(decisions)
    registry, resource, runtime = _make_runtime()
    # plan 消息由 runtime 以 assistant 普通消息形式写入
    plan = decisions[0]
    state.messages.append({"role": "assistant", "content": plan["content"]})
    state.model_cursor += 1
    state.step_count += 1
    result = runtime.run(state, ScriptedModel(decisions))
    return result, registry, resource, model_decisions


# ---- 策略 p3 / p4：失败后一次 Reflection，上限 1 ----

def run_reflection(user_message: str, first_answer: str, revised_answer: str,
                   checker: QualityChecker):
    state = AgentState.create("p3", user_message, 8)
    registry, resource, runtime = _make_runtime()
    state.transition("running")
    max_reflections = 1
    reflections = 0
    final_answer = None

    # 第一轮：模型给出答案
    state.messages.append({"role": "assistant", "content": first_answer})
    state.model_cursor += 1
    state.step_count += 1

    while True:
        candidate = first_answer if reflections == 0 else revised_answer
        if checker.is_acceptable(candidate):
            final_answer = candidate
            state.transition("completed", "final_answer")
            break
        if reflections >= max_reflections:
            # p4：上限耗尽，带着最后一个答案停止
            final_answer = revised_answer if reflections > 0 else first_answer
            state.transition("failed", "reflection_budget_exhausted")
            break
        # 一次 Reflection：把失败反馈写入 context，再生成修正答案
        reflections += 1
        state.messages.append({
            "role": "user",
            "content": f"Reflection {reflections}: your answer was rejected; revise it.",
        })
        state.messages.append({"role": "assistant", "content": revised_answer})
        state.model_cursor += 1
        state.step_count += 1

    state.final_answer = final_answer
    # reflection 策略不经过 runtime.run 的 session 循环，资源保持未打开（0/0），如实记录
    return state, registry, resource, reflections, checker.checks


# ---- 策略 p5：副作用工具前人工审批 ----

def run_approval(user_message: str, *, approved: bool):
    state = AgentState.create("p5", user_message, 5)
    decisions = [
        tool_decision("p5-add", "add", {"a": 2, "b": 3}),
        {"type": "tool_call", "id": "p5-send", "name": "send_report", "arguments": {"content": "report: 5"}},
        final_decision("report sent"),
    ]
    registry = build_approval_registry()
    resource = ResourceProbe()

    # 第一段：执行到 send_report 之前
    # 通过 should_interrupt 在 send_report 决策前暂停：拦截在 step 边界
    class Gate:
        def __init__(self):
            self.paused = False

        def check(self, current: AgentState) -> bool:
            # add 已执行（trace 中有 add），且尚未暂停过 → 在 send_report 前停下
            if not self.paused and any(t.get("name") == "add" for t in current.tool_trace):
                self.paused = True
                return True
            return False

    gate = Gate()
    runtime = AgentRuntime(registry, resource)
    state = runtime.run(state, ScriptedModel(decisions), caller_permissions=APPROVAL_PERMISSION,
                       should_interrupt=gate.check)
    paused_state = deepcopy(state)

    if paused_state.status != "paused":
        return paused_state, registry, resource, {"approved": approved, "executed_while_paused": None}

    if not approved:
        paused_state.transition("cancelled", "approval_denied")
        return paused_state, registry, resource, {"approved": False}

    # 批准 → resume：新 session；paused 状态直接交给 runtime，由其执行 paused→running
    resumed = AgentState.from_json(paused_state.to_json())
    runtime2 = AgentRuntime(registry, ResourceProbe())
    result = runtime2.run(resumed, ScriptedModel(decisions), caller_permissions=APPROVAL_PERMISSION)
    return result, registry, resource, {"approved": True, "resume_resource": runtime2.resource}


def _make_runtime():
    from registry import build_default_registry
    registry = build_default_registry()
    resource = ResourceProbe()
    runtime = AgentRuntime(registry, resource)
    return registry, resource, runtime
