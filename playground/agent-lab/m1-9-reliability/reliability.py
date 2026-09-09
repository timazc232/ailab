"""Day 9（M1.9）可靠性层：分类重试、deadline、backoff、幂等性判断与最小 trace。

时间用虚拟时钟推进（测试不真实 sleep）；trace 为 append-only JSONL 事件流。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class VirtualClock:
    def __init__(self, start_ms: int = 0) -> None:
        self.now_ms = start_ms

    def sleep(self, ms: int) -> None:
        self.now_ms += ms


class TraceRecorder:
    """append-only 事件流：run_id 串联，seq 单调递增。"""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.events: list[dict] = []

    def record(self, kind: str, name: str, attempt: int, outcome: str,
               detail: str = "", elapsed_ms: int = 0) -> None:
        self.events.append({
            "run_id": self.run_id,
            "seq": len(self.events) + 1,
            "clock_ms": None,  # 由调用方补：见 record_with_clock
            "kind": kind,
            "name": name,
            "attempt": attempt,
            "outcome": outcome,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
        })
        self.events[-1].pop("clock_ms")

    def record_event(self, clock: VirtualClock, kind: str, name: str, attempt: int,
                     outcome: str, detail: str = "", elapsed_ms: int = 0) -> None:
        self.events.append({
            "run_id": self.run_id,
            "seq": len(self.events) + 1,
            "ts_ms": clock.now_ms,
            "kind": kind,
            "name": name,
            "attempt": attempt,
            "outcome": outcome,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
        })

    def to_jsonl(self) -> str:
        return "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in self.events)

    @classmethod
    def from_jsonl(cls, text: str, run_id: str) -> "TraceRecorder":
        recorder = cls(run_id)
        for line in text.splitlines():
            if line.strip():
                event = json.loads(line)
                if event.get("run_id") != run_id:
                    raise ValueError("trace contains foreign run_id")
                recorder.events.append(event)
        return recorder


class RetryPolicy:
    """分类决策表：只有 transient 且幂等的调用才允许自动重试。"""

    TRANSIENT = frozenset({"429", "500", "timeout"})
    PERMANENT = frozenset({"401", "403", "404", "invalid_args", "schema_violation"})

    def __init__(self, max_retries: int = 2, base_backoff_ms: int = 100) -> None:
        self.max_retries = max_retries
        self.base_backoff_ms = base_backoff_ms

    def classify(self, outcome: str) -> str:
        if outcome in self.TRANSIENT:
            return "transient"
        if outcome in self.PERMANENT:
            return "permanent"
        raise ValueError(f"unclassified outcome {outcome!r}")

    def backoff_ms(self, retry_number: int) -> int:
        # 指数退避：100, 200, 400, ...
        return self.base_backoff_ms * (2 ** (retry_number - 1))


@dataclass
class CallResult:
    ok: bool
    outcome: str  # ok / retries_exhausted / permanent_error / deadline_exceeded / manual_review / fallback
    value: object = None
    attempts: int = 0
    detail: str = ""
    used_fallback: bool = False


def call_with_retry(
    *,
    name: str,
    kind: str,
    invoke,  # () -> (outcome: str, value, detail: str)
    policy: RetryPolicy,
    clock: VirtualClock,
    trace: TraceRecorder,
    deadline_ms: int,
    idempotent: bool = True,
) -> CallResult:
    attempt = 0
    while True:
        # 每次发起新尝试前检查 deadline
        if clock.now_ms >= deadline_ms:
            trace.record_event(clock, kind, name, attempt, "deadline_exceeded",
                               "deadline reached before next attempt")
            return CallResult(False, "deadline_exceeded", attempts=attempt)

        attempt += 1
        outcome, value, detail = invoke()
        trace.record_event(clock, kind, name, attempt, outcome, detail)

        if outcome == "ok":
            return CallResult(True, "ok", value, attempt)

        classification = policy.classify(outcome)
        if classification == "permanent":
            return CallResult(False, "permanent_error", None, attempt,
                              f"{outcome}: {detail}")

        # transient：幂等性决定能否自动重试
        if not idempotent:
            trace.record_event(clock, kind, name, attempt, "manual_review",
                              "non-idempotent side-effect failure; no auto retry")
            return CallResult(False, "manual_review", None, attempt,
                              f"{outcome}: {detail}")

        retries_used = attempt - 1
        if retries_used >= policy.max_retries:
            return CallResult(False, "retries_exhausted", None, attempt,
                              f"gave up after {attempt} attempts; last error {outcome}")

        backoff = policy.backoff_ms(retries_used + 1)
        clock.sleep(backoff)
        trace.record_event(clock, "backoff", name, attempt, "wait", f"{backoff}ms")


def call_with_fallback(
    *,
    primary_name: str,
    primary_invoke,
    fallback_name: str,
    fallback_invoke,
    policy: RetryPolicy,
    clock: VirtualClock,
    trace: TraceRecorder,
    deadline_ms: int,
) -> CallResult:
    """显式声明的降级：主工具 permanent 失败后使用备用工具。"""
    primary = call_with_retry(name=primary_name, kind="tool_call", invoke=primary_invoke,
                              policy=policy, clock=clock, trace=trace, deadline_ms=deadline_ms)
    if primary.ok:
        return primary
    trace.record_event(clock, "decision", primary_name, primary.attempts,
                       "fallback", f"primary failed ({primary.outcome}); switching to {fallback_name}")
    fallback = call_with_retry(name=fallback_name, kind="tool_call", invoke=fallback_invoke,
                               policy=policy, clock=clock, trace=trace, deadline_ms=deadline_ms)
    if fallback.ok:
        fallback.used_fallback = True
    return fallback
