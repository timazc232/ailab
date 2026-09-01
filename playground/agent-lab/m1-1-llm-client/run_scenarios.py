"""Day 1（M1.1）runner：7 场景 × 3 次，输出观察表并对照 §10.2 预测。

进程内自动启动 mock（复用 mock_server.MockHandler），无需预先手动启动。
输出：
    observations.jsonl  每次调用一条 JSON 记录（原始观察，重跑覆盖）
    stdout              汇总表：每场景 3 次 outcome、一致性、与预测对照
退出码：全部一致且命中预测 → 0；否则 → 1。
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import ThreadingHTTPServer

from client import TIMEOUT_S, call_once
from mock_server import MockHandler

# Day 1 范围固定为 s1–s7；s8（echo）属于 M1.2，不纳入本 runner
DAY1_SCENARIOS = ("s1", "s2", "s3", "s4", "s5", "s6", "s7")

# 实验前写下的预测（plan §10.2），运行后逐一对照
PREDICTED = {
    "s1": "success",
    "s2": "http-api-protocol",
    "s3": "http-api-protocol",
    "s4": "http-api-protocol",
    "s5": "http-api-protocol",
    "s6": "transport",
    "s7": "model-result-condition",
}

RUNS_PER_SCENARIO = 3


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 1 (M1.1) scenario runner")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8931)
    parser.add_argument("--output", default="observations.jsonl")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[runner] mock ready on http://{args.host}:{args.port} (client timeout {TIMEOUT_S}s)")

    all_ok = True
    try:
        with open(args.output, "w", encoding="utf-8") as sink:
            header = (
                f"{'scenario':<9}{'run':<5}{'outcome_class':<26}"
                f"{'status':<8}{'body_parse':<18}{'finish':<9}{'ms':>6}  match"
            )
            print(header)
            for scenario in DAY1_SCENARIOS:
                outcomes = []
                for run in range(1, RUNS_PER_SCENARIO + 1):
                    record = call_once(args.host, args.port, scenario, run=run)
                    record["evidence_ref"] = f"{args.output}#{scenario}#run{run}"
                    sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                    outcome = record["outcome_class"]
                    outcomes.append(outcome)
                    match = "OK" if outcome == PREDICTED[scenario] else "FAIL"
                    print(
                        f"{scenario:<9}{run:<5}{outcome:<26}"
                        f"{str(record['http_status']):<8}{record['body_parse']:<18}"
                        f"{str(record['finish_reason']):<9}{record['elapsed_ms']:>6}  {match}"
                    )

                consistent = len(set(outcomes)) == 1
                matches = all(o == PREDICTED[scenario] for o in outcomes)
                if not (consistent and matches):
                    all_ok = False
                actual = outcomes[0] if consistent else outcomes
                print(
                    f"    -> {scenario}: consistent={consistent} "
                    f"matches_prediction={matches} "
                    f"(predicted={PREDICTED[scenario]}, actual={actual})"
                )
    finally:
        server.shutdown()
        server.server_close()

    print(f"\n{'PASS' if all_ok else 'FAIL'}: {len(DAY1_SCENARIOS) * RUNS_PER_SCENARIO} "
          f"observations written to {args.output}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
