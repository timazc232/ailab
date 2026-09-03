"""Day 4（M1.4）runner：g1–g5，验证 schema 分类、拒绝边界与一次受控重试。"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "m1-1-llm-client"))

from client import call_once  # noqa: E402
from mock_server import MockHandler  # noqa: E402
from schema import ValidationResult, parse_and_validate, should_retry  # noqa: E402

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8934

# 每个 case：(首次 scenario, 若 retry 则第二次 scenario)
CASES = {
    "g1": ("s12", None),       # 合法，不 retry
    "g2": ("s13", None),       # 无效 JSON，不 retry
    "g3": ("s14", "s14"),      # 缺字段，retry 仍缺 → reject
    "g4": ("s15", "s17"),      # 错类型，retry 后合法 → accept
    "g5": ("s16", None),       # 额外字段，不 retry
}

PREDICTED = {
    "g1": {"accepted": True, "error_class": None, "retried": False, "attempts": 1},
    "g2": {"accepted": False, "error_class": "invalid_json", "retried": False, "attempts": 1},
    "g3": {"accepted": False, "error_class": "missing_field", "retried": True, "attempts": 2},
    "g4": {"accepted": True, "error_class": None, "retried": True, "attempts": 2},
    "g5": {"accepted": False, "error_class": "extra_field", "retried": False, "attempts": 1},
}


def _body_from_call(record: dict) -> bytes:
    """从非流式 mock 响应取出 JSON 文本。client 在 success 路径才填 response_content。"""
    content = record.get("response_content")
    if isinstance(content, str):
        return content.encode("utf-8")
    # 非 2xx / malformed：用 detail 不够；直接再读不可用。s13 是 200+畸形 JSON，
    # client 会走 R3 body_parse=malformed，没有 response_content。
    # 对这些场景，runner 用 http 原始路径不方便；改为 mock 把畸形 JSON 放在
    # 合法 chat completion 的 content 里（content 本身是非法 JSON 字符串）。
    return b""


def _extract_model_text(record: dict) -> str:
    """结构化输出实验：模型“说的话”就是待校验的 JSON 文本。"""
    if record.get("body_parse") == "malformed":
        # s13：HTTP 200 但 chat envelope 都不是合法 JSON。当作 invalid_json。
        return "{oops"
    content = record.get("response_content")
    if not isinstance(content, str):
        return ""
    return content


def run_case(host: str, port: int, case_id: str) -> dict:
    first_scenario, retry_scenario = CASES[case_id]
    attempts = 0
    retried = False
    last: ValidationResult | None = None
    accepted_value = None
    error_class = None

    scenario = first_scenario
    while True:
        attempts += 1
        record = call_once(host, port, scenario)
        text = _extract_model_text(record)
        last = parse_and_validate(text)
        if last.ok:
            accepted_value = last.value
            error_class = None
            break
        error_class = last.error_class
        if retry_scenario is not None and should_retry(error_class, attempts - 1):
            retried = True
            scenario = retry_scenario
            continue
        accepted_value = None
        break

    return {
        "case_id": f"m1.4-{case_id}",
        "attempts": attempts,
        "retried": retried,
        "accepted": accepted_value is not None,
        "accepted_value": accepted_value,
        "error_class": error_class,
        "detail": last.detail if last else "",
        "evidence_ref": f"observations.jsonl#m1.4-{case_id}",
    }


def _matches_prediction(obs: dict, predicted: dict) -> bool:
    return (
        obs["accepted"] == predicted["accepted"]
        and obs["error_class"] == predicted["error_class"]
        and obs["retried"] == predicted["retried"]
        and obs["attempts"] == predicted["attempts"]
        and (obs["accepted_value"] is not None) == predicted["accepted"]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 4 (M1.4) structured output runner")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--output", default="observations.jsonl")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[runner] mock ready on http://{args.host}:{args.port}")

    all_ok = True
    records: list[dict] = []
    try:
        for case_id in ("g1", "g2", "g3", "g4", "g5"):
            try:
                obs = run_case(args.host, args.port, case_id)
            except Exception as exc:  # runner 把失败变成可报告记录
                obs = {
                    "case_id": f"m1.4-{case_id}",
                    "attempts": 0,
                    "retried": False,
                    "accepted": False,
                    "accepted_value": None,
                    "error_class": "runner_error",
                    "detail": f"{type(exc).__name__}: {exc}",
                    "evidence_ref": f"observations.jsonl#m1.4-{case_id}",
                }
            predicted = PREDICTED[case_id]
            ok = _matches_prediction(obs, predicted)
            # 非法输出不得进入 accepted 通道
            if not obs["accepted"] and obs["accepted_value"] is not None:
                ok = False
            records.append(obs)
            all_ok = all_ok and ok
            print(
                f"{obs['case_id']:<10} {'OK ' if ok else 'FAIL'}  "
                f"accepted={obs['accepted']!s:<5} retried={obs['retried']!s:<5} "
                f"attempts={obs['attempts']} error={obs['error_class']}"
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
