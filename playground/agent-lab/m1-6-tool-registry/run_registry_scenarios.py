"""Day 6（M1.6）runner：r1–r7，验证注册、inventory、权限与统一 dispatch 边界。"""

from __future__ import annotations

import json

from registry import (
    ArgSpec,
    DuplicateToolError,
    ToolSpec,
    build_default_registry,
)

NO_PERMISSIONS = frozenset()
REPORT_READER = frozenset({"report:read"})


def record(case_id: str, ok: bool, **data) -> tuple[bool, dict]:
    return ok, {"case_id": f"m1.6-{case_id}", **data, "evidence_ref": f"observations.jsonl#m1.6-{case_id}"}


def r1_valid_dispatch():
    registry = build_default_registry()
    result = registry.dispatch("add", {"a": 2, "b": 3}, NO_PERMISSIONS)
    ok = result.ok and result.result == 5 and result.tool_calls_executed == 1
    return record("r1", ok, stage=result.stage, reason=result.reason_code, result=result.result,
                  tool_calls_executed=result.tool_calls_executed, total_calls_executed=result.total_calls_executed)


def r2_duplicate_rejected():
    registry = build_default_registry()

    def wrong_add(a, b):
        return -999

    rejected = False
    try:
        registry.register(ToolSpec("add", "wrong replacement", (ArgSpec("a", "number"), ArgSpec("b", "number")), frozenset(), False, wrong_add))
    except DuplicateToolError:
        rejected = True
    duplicate_attempt_calls_executed = registry.total_execution_count
    after = registry.dispatch("add", {"a": 2, "b": 3}, NO_PERMISSIONS)
    ok = rejected and duplicate_attempt_calls_executed == 0 and after.ok and after.result == 5
    return record("r2", ok, stage="registration", reason="duplicate_name" if rejected else None,
                  duplicate_attempt_calls_executed=duplicate_attempt_calls_executed,
                  original_result=after.result, tool_calls_executed=after.tool_calls_executed)


def r3_unknown_tool():
    registry = build_default_registry()
    result = registry.dispatch("unknown_tool", {}, NO_PERMISSIONS)
    ok = not result.ok and result.stage == "lookup" and result.reason_code == "unknown_tool" and result.total_calls_executed == 0
    return record("r3", ok, stage=result.stage, reason=result.reason_code,
                  tool_calls_executed=result.tool_calls_executed, total_calls_executed=result.total_calls_executed)


def r4_invalid_args():
    registry = build_default_registry()
    result = registry.dispatch("add", {"a": "two"}, NO_PERMISSIONS)
    ok = not result.ok and result.stage == "validation" and result.reason_code == "invalid_args" and result.tool_calls_executed == 0
    return record("r4", ok, stage=result.stage, reason=result.reason_code, detail=result.detail,
                  tool_calls_executed=result.tool_calls_executed, total_calls_executed=result.total_calls_executed)


def r5_authorization_first():
    registry = build_default_registry()
    # 参数故意错误；若顺序正确，结果仍应停在 authorization，不泄漏 schema 细节
    result = registry.dispatch("restricted_report", {"wrong": 123}, NO_PERMISSIONS)
    ok = not result.ok and result.stage == "authorization" and result.reason_code == "denied" and result.tool_calls_executed == 0 and "name" not in result.detail
    return record("r5", ok, stage=result.stage, reason=result.reason_code, detail=result.detail,
                  tool_calls_executed=result.tool_calls_executed, total_calls_executed=result.total_calls_executed)


def r6_execution_exception():
    registry = build_default_registry()
    result = registry.dispatch("divide", {"a": 10, "b": 0}, NO_PERMISSIONS)
    ok = not result.ok and result.stage == "execution" and result.reason_code == "tool_error" and result.tool_calls_executed == 1
    return record("r6", ok, stage=result.stage, reason=result.reason_code, detail=result.detail,
                  tool_calls_executed=result.tool_calls_executed, total_calls_executed=result.total_calls_executed)


def r7_filtered_inventory():
    registry = build_default_registry()
    ordinary = registry.inventory(NO_PERMISSIONS)
    privileged = registry.inventory(REPORT_READER)
    ordinary_names = [item["name"] for item in ordinary]
    privileged_names = [item["name"] for item in privileged]
    ok = ordinary_names == ["add", "divide"] and privileged_names == ["add", "divide", "restricted_report"]
    return record("r7", ok, stage="inventory", reason=None,
                  ordinary=ordinary_names, privileged=privileged_names,
                  ordinary_sorted=ordinary_names == sorted(ordinary_names),
                  privileged_sorted=privileged_names == sorted(privileged_names))


def main() -> int:
    cases = [r1_valid_dispatch, r2_duplicate_rejected, r3_unknown_tool, r4_invalid_args,
             r5_authorization_first, r6_execution_exception, r7_filtered_inventory]
    all_ok = True
    records = []
    for fn in cases:
        try:
            ok, obs = fn()
        except Exception as exc:
            ok = False
            obs = {"case_id": fn.__name__, "stage": "runner", "reason": "runner_error",
                   "detail": f"{type(exc).__name__}: {exc}", "evidence_ref": f"observations.jsonl#{fn.__name__}"}
        records.append(obs)
        all_ok = all_ok and ok
        print(f"{obs['case_id']:<10} {'OK ' if ok else 'FAIL'}  stage={obs.get('stage'):<13} reason={obs.get('reason')} executed={obs.get('tool_calls_executed', '-')} result={obs.get('result', obs.get('original_result'))}")

    with open("observations.jsonl", "w", encoding="utf-8") as sink:
        for obs in records:
            sink.write(json.dumps(obs, ensure_ascii=False) + "\n")
    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in observations.jsonl")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
