"""Day 2（M1.2）runner：e1–e5 场景，验证确定性序列化、顺序语义、构造期拒绝与预算截断。

进程内启动共享 mock（复用 m1-1 的 MockHandler，含 M1.2 新增的 s8 echo 场景）。
输出：
    observations.jsonl  每个 case 一条 JSON 记录（原始观察，重跑覆盖；不入库）
    stdout              每个case的判定与汇总
退出码：全部通过 → 0；否则 → 1。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

# 共享 mock/client 基础设施暂驻 m1-1-llm-client；出现第三个消费者时再提取公共模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-1-llm-client"))

from client import call_once  # noqa: E402
from messages_lib import make_message, serialize_payload, total_chars, truncate_to_budget  # noqa: E402
from mock_server import MockHandler  # noqa: E402

ECHO_SCENARIO = "s8"
BUDGET_CHARS = 120


def sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _send_echo(host: str, port: int, payload: bytes) -> dict:
    """经 client 发送自构造 payload 到 s8，返回回显的 messages。"""
    record = call_once(host, port, ECHO_SCENARIO, request_body=payload)
    if record["outcome_class"] != "success":
        raise RuntimeError(f"echo call failed: {record['detail']}")
    return json.loads(record["response_content"])["received_messages"]


def case_e1_deterministic_serialization() -> tuple[bool, dict]:
    msgs = [
        make_message("system", "You are a concise assistant."),
        make_message("user", "Hello there"),
        make_message("assistant", "Hi! How can I help?"),
    ]
    first = serialize_payload(msgs)
    second = serialize_payload(msgs)
    ok = first == second
    record = {
        "case_id": "m1.2-e1",
        "operation": "serialize",
        "input_summary": f"{len(msgs)} messages, {total_chars(msgs)} chars",
        "budget_chars": None,
        "result": "ok" if ok else "nondeterministic",
        "payload_sha256": sha12(first),
        "echo_match": None,
        "evidence_ref": "observations.jsonl#m1.2-e1",
    }
    return ok, record


def case_e2_order_semantics(host: str, port: int) -> tuple[bool, dict]:
    msgs_a = [
        make_message("system", "You are a concise assistant."),
        make_message("user", "What is Docker?"),
        make_message("assistant", "Docker is a container runtime."),
    ]
    msgs_b = [msgs_a[0], msgs_a[2], msgs_a[1]]  # 同两条对话消息，顺序对调
    payload_a = serialize_payload(msgs_a)
    payload_b = serialize_payload(msgs_b)

    bytes_differ = payload_a != payload_b
    echo_a = _send_echo(host, port, payload_a)
    echo_b = _send_echo(host, port, payload_b)
    echo_match = echo_a == msgs_a and echo_b == msgs_b and echo_a != echo_b

    ok = bytes_differ and echo_match
    record = {
        "case_id": "m1.2-e2",
        "operation": "send",
        "input_summary": "2 orderings of the same 3 messages",
        "budget_chars": None,
        "result": "ok" if ok else f"bytes_differ={bytes_differ} echo_match={echo_match}",
        "payload_sha256": f"{sha12(payload_a)}/{sha12(payload_b)}",
        "echo_match": echo_match,
        "evidence_ref": "observations.jsonl#m1.2-e2",
    }
    return ok, record


def case_e3_reject_empty_content() -> tuple[bool, dict]:
    rejected = False
    try:
        make_message("user", "")
    except ValueError as exc:
        rejected = "empty" in str(exc)
    ok = rejected  # 构造期拒绝：根本不会走到网络层
    record = {
        "case_id": "m1.2-e3",
        "operation": "reject",
        "input_summary": 'make_message("user", "")',
        "budget_chars": None,
        "result": "rejected:empty_content" if rejected else "not_rejected",
        "payload_sha256": None,
        "echo_match": None,
        "evidence_ref": "observations.jsonl#m1.2-e3",
    }
    return ok, record


def case_e4_reject_invalid_role() -> tuple[bool, dict]:
    rejected = False
    try:
        make_message("boss", "hi")
    except ValueError as exc:
        rejected = "invalid role" in str(exc)
    ok = rejected
    record = {
        "case_id": "m1.2-e4",
        "operation": "reject",
        "input_summary": 'make_message("boss", "hi")',
        "budget_chars": None,
        "result": "rejected:invalid_role" if rejected else "not_rejected",
        "payload_sha256": None,
        "echo_match": None,
        "evidence_ref": "observations.jsonl#m1.2-e4",
    }
    return ok, record


def case_e5_truncate_to_budget(host: str, port: int) -> tuple[bool, dict]:
    msgs = [
        make_message("system", "You are a helpful ops assistant."),
        make_message("user", "Check the disk usage on server A."),
        make_message("assistant", "Disk usage is at 91 percent."),
        make_message("user", "What about memory pressure?"),
        make_message("assistant", "Memory pressure is moderate."),
        make_message("user", "Summarize the current risk."),
    ]
    truncated, report = truncate_to_budget(msgs, BUDGET_CHARS)
    payload = serialize_payload(truncated)

    fits_budget = report["total_chars"] <= BUDGET_CHARS
    system_first = bool(truncated) and truncated[0]["role"] == "system"
    oldest_dropped = msgs[1] not in truncated  # 最旧的非 system 轮次应被丢弃
    newest_kept = msgs[-1] in truncated
    echo = _send_echo(host, port, payload)
    echo_match = echo == truncated

    ok = fits_budget and system_first and oldest_dropped and newest_kept and echo_match
    record = {
        "case_id": "m1.2-e5",
        "operation": "truncate",
        "input_summary": f"{len(msgs)} messages, {total_chars(msgs)} chars",
        "budget_chars": BUDGET_CHARS,
        "result": f"kept={report['kept_messages']} dropped={report['dropped_messages']} "
        f"total_chars={report['total_chars']}",
        "payload_sha256": sha12(payload),
        "echo_match": echo_match,
        "evidence_ref": "observations.jsonl#m1.2-e5",
    }
    detail_ok = fits_budget and system_first and oldest_dropped and newest_kept
    if not detail_ok:
        record["result"] += f" | fits={fits_budget} system_first={system_first} " \
            f"oldest_dropped={oldest_dropped} newest_kept={newest_kept}"
    return ok, record


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 2 (M1.2) context scenarios runner")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8932)  # 与 Day 1 mock 端口错开
    parser.add_argument("--output", default="observations.jsonl")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[runner] mock ready on http://{args.host}:{args.port} (scenario {ECHO_SCENARIO})")

    cases = [
        ("e1 deterministic serialization", lambda: case_e1_deterministic_serialization()),
        ("e2 order semantics", lambda: case_e2_order_semantics(args.host, args.port)),
        ("e3 reject empty content", lambda: case_e3_reject_empty_content()),
        ("e4 reject invalid role", lambda: case_e4_reject_invalid_role()),
        ("e5 truncate to budget", lambda: case_e5_truncate_to_budget(args.host, args.port)),
    ]

    all_ok = True
    records: list[dict] = []
    try:
        for name, fn in cases:
            try:
                ok, record = fn()
            except Exception as exc:  # runner 需要把任何失败变成可报告记录
                ok, record = False, {
                    "case_id": name.split()[0],
                    "operation": "error",
                    "input_summary": name,
                    "budget_chars": None,
                    "result": f"exception: {type(exc).__name__}: {exc}",
                    "payload_sha256": None,
                    "echo_match": None,
                    "evidence_ref": f"observations.jsonl#{name.split()[0]}",
                }
            records.append(record)
            all_ok = all_ok and ok
            print(f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  {record['result']}")
    finally:
        server.shutdown()
        server.server_close()
        with open(args.output, "w", encoding="utf-8") as sink:
            for record in records:
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(records)} cases, details in {args.output}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
