"""Day 3（M1.3）runner：f1–f5，验证增量 SSE 重组、任意分块、畸形事件、断流与取消。"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-1-llm-client"))

import http.client  # noqa: E402

from mock_server import PATH, SCENARIO_HEADER, MockHandler  # noqa: E402
from sse import REFERENCE_TEXT, StreamParseResult, parse_sse_response  # noqa: E402

ECHO_HOST_DEFAULT = "127.0.0.1"
ECHO_PORT_DEFAULT = 8933


def _open_stream(
    host: str,
    port: int,
    scenario: str,
    *,
    write_size: int | None = None,
) -> tuple[http.client.HTTPConnection, http.client.HTTPResponse]:
    conn = http.client.HTTPConnection(host, port, timeout=5)
    headers = {
        "Content-Type": "application/json",
        SCENARIO_HEADER: scenario,
    }
    if write_size is not None:
        headers["X-Mock-Write-Size"] = str(write_size)
    body = b'{"model":"mock-model-day1","messages":[{"role":"user","content":"hi"}],"stream":true}'
    conn.request("POST", PATH, body=body, headers=headers)
    response = conn.getresponse()
    return conn, response


def _record(case_id: str, result: StreamParseResult, chunk_strategy: str) -> dict:
    return {
        "case_id": case_id,
        "chunk_strategy": chunk_strategy,
        "events_received": result.events_received,
        "deltas_assembled": result.deltas_assembled,
        "finish_reason": result.finish_reason,
        "done_received": result.done_received,
        "completeness": result.completeness,
        "errors": result.errors,
        "text_matches_nonstream": result.text_matches_nonstream,
        "evidence_ref": f"observations.jsonl#{case_id}",
    }


def _run_parse(
    host: str,
    port: int,
    scenario: str,
    *,
    write_size: int | None = None,
    cancel_after_events: int | None = None,
) -> StreamParseResult:
    conn, response = _open_stream(host, port, scenario, write_size=write_size)
    try:
        return parse_sse_response(response, conn, cancel_after_events=cancel_after_events)
    finally:
        try:
            conn.close()
        except OSError:
            pass


def case_f1(host: str, port: int) -> tuple[bool, dict]:
    result = _run_parse(host, port, "s9")
    ok = (
        result.completeness == "complete"
        and result.text_matches_nonstream is True
        and result.finish_reason == "stop"
        and result.done_received
        and not result.errors
    )
    return ok, _record("m1.3-f1", result, "whole")


def case_f2(host: str, port: int) -> tuple[bool, dict]:
    result = _run_parse(host, port, "s9", write_size=3)
    ok = (
        result.completeness == "complete"
        and result.deltas_assembled == REFERENCE_TEXT
        and result.text_matches_nonstream is True
        and not result.errors
    )
    return ok, _record("m1.3-f2", result, "3-byte")


def case_f3(host: str, port: int) -> tuple[bool, dict]:
    result = _run_parse(host, port, "s10")
    ok = bool(result.errors) and result.completeness == "protocol_error"
    return ok, _record("m1.3-f3", result, "whole")


def case_f4(host: str, port: int) -> tuple[bool, dict]:
    result = _run_parse(host, port, "s11")
    ok = (
        result.completeness == "incomplete"
        and not result.done_received
        and result.finish_reason is None
        and result.deltas_assembled != ""
        and result.deltas_assembled != REFERENCE_TEXT
    )
    return ok, _record("m1.3-f4", result, "whole")


def case_f5(host: str, port: int) -> tuple[bool, dict]:
    result = _run_parse(host, port, "s9", cancel_after_events=2)
    ok = (
        result.completeness == "cancelled"
        and result.events_received >= 2
        and not result.done_received
        and result.deltas_assembled != REFERENCE_TEXT
    )
    return ok, _record("m1.3-f5", result, "whole")


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 3 (M1.3) streaming scenarios runner")
    parser.add_argument("--host", default=ECHO_HOST_DEFAULT)
    parser.add_argument("--port", type=int, default=ECHO_PORT_DEFAULT)
    parser.add_argument("--output", default="observations.jsonl")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[runner] mock ready on http://{args.host}:{args.port}")

    cases = [
        ("f1 happy path", lambda: case_f1(args.host, args.port)),
        ("f2 3-byte chunks + unicode split", lambda: case_f2(args.host, args.port)),
        ("f3 malformed event", lambda: case_f3(args.host, args.port)),
        ("f4 disconnect mid-stream", lambda: case_f4(args.host, args.port)),
        ("f5 client cancel", lambda: case_f5(args.host, args.port)),
    ]

    all_ok = True
    records: list[dict] = []
    try:
        for name, fn in cases:
            try:
                ok, record = fn()
            except Exception as exc:  # runner 把失败变成可报告记录
                ok = False
                record = {
                    "case_id": name.split()[0],
                    "chunk_strategy": "?",
                    "events_received": 0,
                    "deltas_assembled": "",
                    "finish_reason": None,
                    "done_received": False,
                    "completeness": "error",
                    "errors": [f"{type(exc).__name__}: {exc}"],
                    "text_matches_nonstream": False,
                    "evidence_ref": f"observations.jsonl#{name.split()[0]}",
                }
            records.append(record)
            all_ok = all_ok and ok
            assembled = record["deltas_assembled"]
            preview = assembled if len(assembled) <= 40 else assembled[:40] + "..."
            print(
                f"{record['case_id']:<10} {'OK ' if ok else 'FAIL'}  "
                f"completeness={record['completeness']:<16} "
                f"events={record['events_received']} "
                f"match={record['text_matches_nonstream']} "
                f"text={preview!r}"
            )
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
