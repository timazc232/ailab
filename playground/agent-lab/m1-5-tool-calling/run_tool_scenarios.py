"""Day 5（M1.5）runner：t1–t5，验证 tool selection / invocation / execution 边界与结果回填。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-2-messages"))

from messages_lib import serialize_payload  # noqa: E402
from executor import ToolExecutor  # noqa: E402
from fixtures import FIXTURES  # noqa: E402

PREDICTED = {
    "t1": {"ok": True, "stage": "success", "reason": None, "calls": 1, "result": 5},
    "t2": {"ok": False, "stage": "selection", "reason": "unknown_tool", "calls": 0},
    "t3": {"ok": False, "stage": "invocation", "reason": "invalid_args", "calls": 0},
    "t4": {"ok": False, "stage": "selection", "reason": "denied_tool", "calls": 0},
}


def run_t1_to_t4(case_id: str) -> tuple[bool, dict]:
    executor = ToolExecutor()
    outcome = executor.execute_one(FIXTURES[case_id])
    predicted = PREDICTED[case_id]
    ok = (
        outcome.ok == predicted["ok"]
        and outcome.stage == predicted["stage"]
        and outcome.reason_code == predicted["reason"]
        and outcome.calls_executed == predicted["calls"]
        and ("result" not in predicted or outcome.result == predicted["result"])
    )
    return ok, {
        "case_id": f"m1.5-{case_id}",
        "ok": outcome.ok,
        "stage": outcome.stage,
        "reason_code": outcome.reason_code,
        "detail": outcome.detail,
        "calls_executed": outcome.calls_executed,
        "result": outcome.result,
        "tool_message": outcome.tool_message,
        "execution_log": executor.execution_log,
        "evidence_ref": f"observations.jsonl#m1.5-{case_id}",
    }


def run_t5_result_fillback() -> tuple[bool, dict]:
    executor = ToolExecutor()
    outcome = executor.execute_one(FIXTURES["t1"])
    if not outcome.ok or outcome.tool_message is None:
        return False, {"case_id": "m1.5-t5", "error": "t1 execution prerequisite failed"}

    messages = [
        {"role": "system", "content": "You are a calculator."},
        {"role": "user", "content": "What is 2 + 3?"},
        FIXTURES["t1"],
        outcome.tool_message,
    ]
    first = serialize_payload(messages)
    second = serialize_payload(messages)
    decoded = json.loads(first)
    tool_message = decoded["messages"][-1]
    ok = (
        first == second
        and tool_message["role"] == "tool"
        and tool_message["tool_call_id"] == "call_t1"
        and tool_message["content"] == "5"
        and outcome.calls_executed == 1
    )
    return ok, {
        "case_id": "m1.5-t5",
        "ok": ok,
        "stage": "fillback",
        "reason_code": None,
        "detail": "tool message appended and deterministically serialized",
        "calls_executed": outcome.calls_executed,
        "result": outcome.result,
        "tool_message": tool_message,
        "payload_bytes_equal": first == second,
        "evidence_ref": "observations.jsonl#m1.5-t5",
    }


def main() -> int:
    cases = [
        ("t1", lambda: run_t1_to_t4("t1")),
        ("t2", lambda: run_t1_to_t4("t2")),
        ("t3", lambda: run_t1_to_t4("t3")),
        ("t4", lambda: run_t1_to_t4("t4")),
        ("t5", run_t5_result_fillback),
    ]
    all_ok = True
    records: list[dict] = []
    for name, fn in cases:
        try:
            ok, record = fn()
        except Exception as exc:  # runner 将意外失败变成证据
            ok = False
            record = {
                "case_id": f"m1.5-{name}",
                "ok": False,
                "stage": "runner",
                "reason_code": "runner_error",
                "detail": f"{type(exc).__name__}: {exc}",
                "calls_executed": None,
                "evidence_ref": f"observations.jsonl#m1.5-{name}",
            }
        records.append(record)
        all_ok = all_ok and ok
        print(
            f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  "
            f"stage={record.get('stage'):<10} reason={record.get('reason_code')} "
            f"executed={record.get('calls_executed')} result={record.get('result')}"
        )

    with open("observations.jsonl", "w", encoding="utf-8") as sink:
        for record in records:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in observations.jsonl")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
