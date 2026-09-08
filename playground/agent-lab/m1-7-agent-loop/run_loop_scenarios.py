"""Day 7（M1.7）runner：l1–l7 Agent Loop / State / Lifecycle。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-6-tool-registry"))

from registry import build_default_registry
from runtime import AgentRuntime, ResourceProbe, ScriptedModel, final_decision, tool_decision
from state import AgentState


def execute(state, decisions, *, cancel=None, interrupt=None):
    registry = build_default_registry()
    resource = ResourceProbe()
    runtime = AgentRuntime(registry, resource)
    result = runtime.run(state, ScriptedModel(decisions), should_cancel=cancel, should_interrupt=interrupt)
    return result, registry, resource


def observation(case_id, ok, state, resource, **extra):
    return ok, {
        "case_id": f"m1.7-{case_id}",
        "status": state.status,
        "termination_reason": state.termination_reason,
        "step_count": state.step_count,
        "model_cursor": state.model_cursor,
        "roles": [message["role"] for message in state.messages],
        "tool_trace_count": len(state.tool_trace),
        "resource_opened": resource.opened,
        "resource_closed": resource.closed,
        "resource_active": resource.active,
        **extra,
        "evidence_ref": f"observations.jsonl#m1.7-{case_id}",
    }


def l1_direct_answer():
    state = AgentState.create("l1", "Answer directly", 3)
    state, registry, resource = execute(state, [final_decision("direct answer")])
    ok = state.status == "completed" and state.termination_reason == "final_answer" and state.step_count == 1 and registry.total_execution_count == 0 and resource.closed == 1
    return observation("l1", ok, state, resource, total_tool_executions=registry.total_execution_count, final_answer=state.final_answer)


def l2_single_tool():
    state = AgentState.create("l2", "Calculate 2 + 3", 3)
    decisions = [tool_decision("l2-add", "add", {"a": 2, "b": 3}), final_decision("2 + 3 = 5")]
    state, registry, resource = execute(state, decisions)
    roles = [m["role"] for m in state.messages]
    ok = state.status == "completed" and state.step_count == 2 and registry.execution_count("add") == 1 and roles == ["system", "user", "assistant", "tool", "assistant"] and state.messages[3]["content"] == "5"
    return observation("l2", ok, state, resource, add_executions=registry.execution_count("add"), final_answer=state.final_answer)


def l3_multiple_tools():
    state = AgentState.create("l3", "Use two calculations", 4)
    decisions = [
        tool_decision("l3-add", "add", {"a": 2, "b": 3}),
        tool_decision("l3-divide", "divide", {"a": 10, "b": 2}),
        final_decision("add=5, divide=5"),
    ]
    state, registry, resource = execute(state, decisions)
    roles = [m["role"] for m in state.messages]
    ok = state.status == "completed" and state.step_count == 3 and registry.execution_count("add") == 1 and registry.execution_count("divide") == 1 and roles == ["system", "user", "assistant", "tool", "assistant", "tool", "assistant"]
    return observation("l3", ok, state, resource, add_executions=registry.execution_count("add"), divide_executions=registry.execution_count("divide"), final_answer=state.final_answer)


def l4_max_steps():
    state = AgentState.create("l4", "Keep calling add", 3)
    decisions = [tool_decision(f"l4-add-{i}", "add", {"a": i, "b": 1}) for i in range(5)]
    state, registry, resource = execute(state, decisions)
    ok = state.status == "failed" and state.termination_reason == "max_steps" and state.step_count == 3 and registry.execution_count("add") == 3 and resource.closed == 1
    return observation("l4", ok, state, resource, add_executions=registry.execution_count("add"), max_steps=state.max_steps)


def l5_cancelled():
    state = AgentState.create("l5", "Cancel after first tool", 4)
    decisions = [tool_decision("l5-add", "add", {"a": 2, "b": 3}), final_decision("should not run")]
    state, registry, resource = execute(state, decisions, cancel=lambda current: current.step_count >= 1)
    ok = state.status == "cancelled" and state.termination_reason == "cancelled" and state.step_count == 1 and registry.execution_count("add") == 1 and state.final_answer is None and resource.closed == 1 and not resource.active
    return observation("l5", ok, state, resource, add_executions=registry.execution_count("add"), final_answer=state.final_answer)


def make_interrupted_state():
    state = AgentState.create("l6-l7", "Pause and resume", 4)
    decisions = [tool_decision("l6-add", "add", {"a": 2, "b": 3}), final_decision("resumed answer: 5")]
    state, registry, resource = execute(state, decisions, interrupt=lambda current: current.step_count >= 1)
    return state, decisions, registry, resource


def l6_interrupted_checkpoint():
    state, decisions, registry, resource = make_interrupted_state()
    checkpoint = state.to_json()
    restored = AgentState.from_json(checkpoint)
    ok = state.status == "paused" and state.termination_reason == "interrupted" and state.step_count == 1 and state.model_cursor == 1 and restored == state and registry.execution_count("add") == 1 and resource.closed == 1
    return observation("l6", ok, state, resource, add_executions=registry.execution_count("add"), checkpoint_roundtrip_equal=restored == state, checkpoint_bytes=len(checkpoint))


def l7_resume_without_replay():
    paused, decisions, first_registry, first_resource = make_interrupted_state()
    restored = AgentState.from_json(paused.to_json())
    resumed, second_registry, second_resource = execute(restored, decisions)
    total_add_executions = first_registry.execution_count("add") + second_registry.execution_count("add")
    ok = resumed.status == "completed" and resumed.termination_reason == "final_answer" and resumed.step_count == 2 and resumed.model_cursor == 2 and first_registry.execution_count("add") == 1 and second_registry.execution_count("add") == 0 and total_add_executions == 1 and len(resumed.tool_trace) == 1 and first_resource.closed == 1 and second_resource.closed == 1
    return observation("l7", ok, resumed, second_resource, first_session_add_executions=first_registry.execution_count("add"), resume_session_add_executions=second_registry.execution_count("add"), total_add_executions=total_add_executions, first_resource_closed=first_resource.closed, final_answer=resumed.final_answer)


def main() -> int:
    cases = [l1_direct_answer, l2_single_tool, l3_multiple_tools, l4_max_steps, l5_cancelled, l6_interrupted_checkpoint, l7_resume_without_replay]
    all_ok = True
    records = []
    for fn in cases:
        try:
            ok, record = fn()
        except Exception as exc:
            ok = False
            record = {"case_id": fn.__name__, "status": "runner_error", "termination_reason": f"{type(exc).__name__}: {exc}", "evidence_ref": f"observations.jsonl#{fn.__name__}"}
        all_ok = all_ok and ok
        records.append(record)
        print(f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  status={record.get('status'):<9} reason={record.get('termination_reason'):<12} steps={record.get('step_count', '-')} tools={record.get('tool_trace_count', '-')}")

    with open("observations.jsonl", "w", encoding="utf-8") as sink:
        for record in records:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in observations.jsonl")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
