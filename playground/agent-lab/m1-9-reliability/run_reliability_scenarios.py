"""Day 9（M1.9）runner：n1–n8 故障注入矩阵。"""

from __future__ import annotations

import json

from reliability import (
    CallResult,
    RetryPolicy,
    TraceRecorder,
    VirtualClock,
    call_with_fallback,
    call_with_retry,
)


def flaky_caller(error_outcomes: list[str], success_value, permanent_errors=("401", "403", "404")):
    """前 N 次返回注入错误，之后成功。permanent 错误始终 permanent。"""
    calls = {"count": 0}

    def invoke():
        calls["count"] += 1
        index = calls["count"] - 1
        if index < len(error_outcomes):
            outcome = error_outcomes[index]
            return outcome, None, f"injected {outcome} (call #{calls['count']})"
        return "ok", success_value, ""

    return invoke, calls


def obs(case_id, ok, **data):
    return ok, {"case_id": f"m1.9-{case_id}", **data, "evidence_ref": f"observations.jsonl#m1.9-{case_id}"}


def base_setup(deadline_ms: int = 10_000):
    return RetryPolicy(), VirtualClock(), deadline_ms


def n1_retry_then_success():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n1")
    invoke, calls = flaky_caller(["429"], "answer")
    result = call_with_retry(name="model", kind="model_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline)
    model_events = [e for e in trace.events if e["kind"] == "model_call"]
    ok = result.ok and result.attempts == 2 and len(model_events) == 2 and calls["count"] == 2
    return obs("n1", ok, scenario="429 once then success", outcome=result.outcome,
               attempts=result.attempts, trace_events=len(trace.events), value=result.value)


def n2_retries_exhausted():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n2")
    invoke, calls = flaky_caller(["429", "429", "429", "429", "429"], "never")
    result = call_with_retry(name="model", kind="model_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline)
    ok = (not result.ok and result.outcome == "retries_exhausted"
          and result.attempts == 3 and calls["count"] == 3)  # 1 原始 + 2 重试
    return obs("n2", ok, scenario="persistent 429", outcome=result.outcome,
               attempts=result.attempts, max_retries=policy.max_retries)


def n3_permanent_no_retry():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n3")
    invoke, calls = flaky_caller(["401"], "never")
    result = call_with_retry(name="model", kind="model_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline)
    ok = (not result.ok and result.outcome == "permanent_error"
          and result.attempts == 1 and calls["count"] == 1)
    return obs("n3", ok, scenario="401 permanent", outcome=result.outcome,
               attempts=result.attempts)


def n4_tool_timeout_retry():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n4")
    invoke, calls = flaky_caller(["timeout"], 5)
    result = call_with_retry(name="add", kind="tool_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline, idempotent=True)
    ok = result.ok and result.attempts == 2 and result.value == 5 and calls["count"] == 2
    return obs("n4", ok, scenario="tool timeout then success", outcome=result.outcome,
               attempts=result.attempts, value=result.value)


def n5_deadline_exceeded():
    policy, clock, _ = base_setup()
    trace = TraceRecorder("n5")
    invoke, calls = flaky_caller(["429", "429", "429", "429"], "never")
    # deadline=150：attempt1(0ms 失败) → backoff 100ms → now=100 < 150 → attempt2 失败
    # → backoff 200ms → now=300 ≥ 150 → 停止，无 attempt3
    result = call_with_retry(name="model", kind="model_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=150)
    ok = (not result.ok and result.outcome == "deadline_exceeded"
          and result.attempts == 2 and calls["count"] == 2
          and all(e["outcome"] != "deadline_exceeded" or e["seq"] == len(trace.events)
                  for e in trace.events))
    return obs("n5", ok, scenario="deadline stops retries", outcome=result.outcome,
               attempts=result.attempts, final_clock_ms=clock.now_ms, deadline_ms=150)


def n6_non_idempotent_no_retry():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n6")
    invoke, calls = flaky_caller(["timeout"], None)  # 超时：不知道发没发出去
    result = call_with_retry(name="send_report", kind="tool_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline, idempotent=False)
    manual_events = [e for e in trace.events if e["outcome"] == "manual_review"]
    ok = (not result.ok and result.outcome == "manual_review"
          and result.attempts == 1 and calls["count"] == 1 and len(manual_events) == 1)
    return obs("n6", ok, scenario="non-idempotent side effect fails", outcome=result.outcome,
               attempts=result.attempts, auto_retried=False)


def n7_fallback():
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n7")
    primary, primary_calls = flaky_caller(["404"], "never")  # permanent
    fallback, fallback_calls = flaky_caller([], "cached-result")
    result = call_with_fallback(primary_name="fetch_report", primary_invoke=primary,
                                fallback_name="cached_report", fallback_invoke=fallback,
                                policy=policy, clock=clock, trace=trace, deadline_ms=deadline)
    ok = (result.ok and result.used_fallback and result.value == "cached-result"
          and primary_calls["count"] == 1 and fallback_calls["count"] == 1)
    return obs("n7", ok, scenario="primary permanent failure -> declared fallback",
               outcome=result.outcome, fallback_used=result.used_fallback,
               primary_attempts=1, value=result.value)


def n8_trace_reconstruction():
    # 重新跑 n1 场景并只用 trace 重建结论
    policy, clock, deadline = base_setup()
    trace = TraceRecorder("n8")
    invoke, calls = flaky_caller(["429"], "answer")
    result = call_with_retry(name="model", kind="model_call", invoke=invoke, policy=policy,
                             clock=clock, trace=trace, deadline_ms=deadline)

    text = trace.to_jsonl()
    restored = TraceRecorder.from_jsonl(text, "n8")
    events = restored.events
    model_calls = [e for e in events if e["kind"] == "model_call"]
    backoffs = [e for e in events if e["kind"] == "backoff"]
    seqs = [e["seq"] for e in events]
    run_ids = {e["run_id"] for e in events}
    # 重建结论：最后一个 model_call 是 ok → 运行成功；尝试次数 = model_call 数
    reconstructed_ok = model_calls[-1]["outcome"] == "ok"
    reconstructed_attempts = len(model_calls)
    ok = (reconstructed_ok is result.ok and reconstructed_attempts == result.attempts
          and len(backoffs) == 1 and seqs == sorted(seqs) and len(set(seqs)) == len(seqs)
          and run_ids == {"n8"} and len(text.splitlines()) == len(events))
    return obs("n8", ok, scenario="rebuild run from trace only",
               reconstructed_ok=reconstructed_ok, reconstructed_attempts=reconstructed_attempts,
               trace_events=len(events), seq_strictly_increasing=seqs == sorted(seqs))


def main() -> int:
    cases = [n1_retry_then_success, n2_retries_exhausted, n3_permanent_no_retry,
             n4_tool_timeout_retry, n5_deadline_exceeded, n6_non_idempotent_no_retry,
             n7_fallback, n8_trace_reconstruction]
    all_ok = True
    records = []
    for fn in cases:
        try:
            ok, record = fn()
        except Exception as exc:
            ok = False
            record = {"case_id": fn.__name__, "outcome": "runner_error",
                      "detail": f"{type(exc).__name__}: {exc}",
                      "evidence_ref": f"observations.jsonl#{fn.__name__}"}
        records.append(record)
        all_ok = all_ok and ok
        print(f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  outcome={str(record.get('outcome')):<18} "
              f"attempts={record.get('attempts', '-')}")

    with open("observations.jsonl", "w", encoding="utf-8") as sink:
        for record in records:
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in observations.jsonl")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
