"""Day 8（M1.8）runner：p1–p5 控制策略对比。"""

from __future__ import annotations

import json

from strategies import (
    APPROVAL_PERMISSION,
    QualityChecker,
    run_approval,
    run_plan_first,
    run_reactive,
    run_reflection,
)
from runtime import final_decision, tool_decision


def obs(case_id, ok, **data):
    return ok, {"case_id": f"m1.8-{case_id}", **data, "evidence_ref": f"observations.jsonl#m1.8-{case_id}"}


def p1_reactive():
    decisions = [tool_decision("p1-add", "add", {"a": 2, "b": 3}), final_decision("2 + 3 = 5")]
    state, registry, resource, model_decisions = run_reactive("Calculate 2 + 3", decisions)
    ok = (state.status == "completed" and state.step_count == 2 and model_decisions == 2
          and registry.execution_count("add") == 1 and resource.closed == 1
          and state.final_answer == "2 + 3 = 5")
    return obs("p1", ok, strategy="reactive", status=state.status, reason=state.termination_reason,
               steps=state.step_count, model_decisions=model_decisions,
               tool_executions=registry.total_execution_count,
               resource=f"{resource.opened}/{resource.closed}", final=state.final_answer)


def p2_plan_first():
    decisions = [
        {"type": "plan", "content": "Plan: 1) add 2+3 2) report the result"},
        tool_decision("p2-add", "add", {"a": 2, "b": 3}),
        final_decision("2 + 3 = 5"),
    ]
    state, registry, resource, model_decisions = run_plan_first("Calculate 2 + 3", decisions)
    plan_in_context = any(m["role"] == "assistant" and "Plan:" in str(m.get("content")) for m in state.messages)
    ok = (state.status == "completed" and state.step_count == 3 and model_decisions == 3
          and plan_in_context and registry.execution_count("add") == 1 and resource.closed == 1)
    return obs("p2", ok, strategy="plan_first", status=state.status, reason=state.termination_reason,
               steps=state.step_count, model_decisions=model_decisions,
               plan_in_context=plan_in_context,
               tool_executions=registry.total_execution_count,
               resource=f"{resource.opened}/{resource.closed}", final=state.final_answer)


def p3_reflection_fix():
    checker = QualityChecker({"2 + 3 = 5"})
    state, registry, resource, reflections, checks = run_reflection(
        "Calculate 2 + 3", first_answer="2 + 3 = 6", revised_answer="2 + 3 = 5", checker=checker)
    ok = (state.status == "completed" and reflections == 1 and checks == 2
          and state.final_answer == "2 + 3 = 5"
          and state.termination_reason == "final_answer")
    return obs("p3", ok, strategy="reflection", status=state.status, reason=state.termination_reason,
               reflections=reflections, checker_checks=checks, steps=state.step_count,
               final=state.final_answer)


def p4_reflection_cap():
    checker = QualityChecker({"nothing ever matches"})
    state, registry, resource, reflections, checks = run_reflection(
        "Calculate 2 + 3", first_answer="2 + 3 = 6", revised_answer="2 + 3 = 7",
        checker=checker)
    ok = (state.status == "failed" and state.termination_reason == "reflection_budget_exhausted"
          and reflections == 1 and checks == 2)
    return obs("p4", ok, strategy="reflection_cap", status=state.status,
               reason=state.termination_reason, max_reflections=1,
               reflections=reflections, checker_checks=checks, final=state.final_answer)


def p5_approval_granted():
    state, registry, resource, meta = run_approval("Calculate and send the report", approved=True)
    send_count = registry.execution_count("send_report")
    resume_resource = meta.get("resume_resource")
    ok = (state.status == "completed" and send_count == 1
          and resource.closed == 1
          and resume_resource is not None and resume_resource.closed == 1)
    return obs("p5", ok, strategy="approval_granted", status=state.status,
               reason=state.termination_reason, send_report_executions=send_count,
               first_session_resource=f"{resource.opened}/{resource.closed}",
               resume_session_resource=f"{resume_resource.opened}/{resume_resource.closed}" if resume_resource else None,
               final=state.final_answer)


def p5b_approval_denied():
    state, registry, resource, meta = run_approval("Calculate and send the report", approved=False)
    send_count = registry.execution_count("send_report")
    ok = (state.status == "cancelled" and state.termination_reason == "approval_denied"
          and send_count == 0 and resource.closed == 1)
    return obs("p5b", ok, strategy="approval_denied", status=state.status,
               reason=state.termination_reason, send_report_executions=send_count,
               resource=f"{resource.opened}/{resource.closed}")


def main() -> int:
    cases = [p1_reactive, p2_plan_first, p3_reflection_fix, p4_reflection_cap,
             p5_approval_granted, p5b_approval_denied]
    all_ok = True
    records = []
    for fn in cases:
        try:
            ok, record = fn()
        except Exception as exc:
            ok = False
            record = {"case_id": fn.__name__, "status": "runner_error",
                      "detail": f"{type(exc).__name__}: {exc}",
                      "evidence_ref": f"observations.jsonl#{fn.__name__}"}
        records.append(record)
        all_ok = all_ok and ok
        print(f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  status={record.get('status'):<9} "
              f"reason={record.get('reason')} steps={record.get('steps','-')} "
              f"reflections={record.get('reflections','-')} send={record.get('send_report_executions','-')}")

    with open("observations.jsonl", "w", encoding="utf-8") as sink:
        for record in records:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in observations.jsonl")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
