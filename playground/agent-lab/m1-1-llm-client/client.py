"""Day 1（M1.1）最小同步 LLM API client。

只用标准库 http.client；按 R1–R5 顺序分类（plan §10.3），首中即止：
    R1 transport               收到完整响应前失败（连接失败 / 读超时等 OSError、HTTPException）
    R2 http-api-protocol       收到完整响应但 status 非 2xx
    R3 http-api-protocol       2xx 但 body 非法 JSON，或违反最小字段契约
    R4 success                 JSON 合法且 finish_reason == "stop"
    R5 model-result-condition  JSON 合法但 finish_reason != "stop"

分类只依据显式契约信号；不按内容语义猜测。Day 1 只记录重试判断，不实现重试（M1.9）。
"""

from __future__ import annotations

import http.client
import json
import time
from datetime import datetime, timezone

PATH = "/v1/chat/completions"
SCENARIO_HEADER = "X-Mock-Scenario"
FAKE_API_KEY = "test-key-000"  # 占位假 key：Day 1 无真实认证，任何输出中不得出现真实凭据

# 单个 socket 超时同时覆盖 connect 与 read 两个阶段（plan §10.5 的 2s/2s）
TIMEOUT_S = 2.0


def _validate_contract(payload: object) -> tuple[bool, str]:
    """检查 §10.2 最小响应契约，返回 (是否满足, 说明)。"""
    if not isinstance(payload, dict):
        return False, "top-level JSON value is not an object"
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        return False, "choices must be a list with exactly 1 item"
    choice = choices[0]
    if not isinstance(choice, dict):
        return False, "choices[0] is not an object"
    message = choice.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        return False, "choices[0].message.content missing or not a string"
    if not isinstance(choice.get("finish_reason"), str):
        return False, "choices[0].finish_reason missing or not a string"
    return True, "ok"


def _retry_guess(outcome_class: str, status: int | None, phase: str | None) -> str:
    """记录「是否值得重试」的判断（只记录，不实现；重试策略属于 M1.9）。"""
    if outcome_class == "transport":
        if phase == "connect":
            return "yes-if-idempotent: request likely never arrived"
        return "uncertain: request may have been processed; check side effects first"
    if status == 429:
        return "yes: honor Retry-After header"
    if status is not None and 500 <= status <= 599:
        return "maybe: server-side transient"
    if status in (401, 403):
        return "no: permanent auth failure"
    if outcome_class == "http-api-protocol":
        return "no: deterministic contract violation"
    return "no"


def call_once(
    host: str,
    port: int,
    scenario: str,
    timeout_s: float = TIMEOUT_S,
    run: int | None = None,
) -> dict:
    """向本地 mock 发送一次请求，返回一条观察记录（§5.4 字段）。"""
    record: dict = {
        "scenario_id": scenario,
        "run": run,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "elapsed_ms": None,
        "request_target": f"http://{host}:{port}{PATH}",
        "request_headers_summary": {
            "Authorization": "Bearer ***redacted***",
            "Content-Type": "application/json",
            SCENARIO_HEADER: scenario,
        },
        "http_status": None,
        "response_content_type": None,
        "body_parse": "not_reached",
        "finish_reason": None,
        "outcome_class": None,
        "retry_worthiness_guess": None,
        "detail": "",
    }

    request_body = json.dumps(
        {
            "model": "mock-model-day1",
            "messages": [{"role": "user", "content": "Say hi"}],
            "max_tokens": 16,
        }
    ).encode("utf-8")

    conn = http.client.HTTPConnection(host, port, timeout=timeout_s)
    phase = "connect"
    started = time.perf_counter()
    try:
        conn.connect()
        phase = "request"
        conn.request(
            "POST",
            PATH,
            body=request_body,
            headers={
                "Authorization": f"Bearer {FAKE_API_KEY}",
                "Content-Type": "application/json",
                SCENARIO_HEADER: scenario,
            },
        )
        phase = "response-status"
        response = conn.getresponse()
        record["http_status"] = response.status
        record["response_content_type"] = response.getheader("Content-Type")
        phase = "response-body"
        raw = response.read()
    except (OSError, http.client.HTTPException) as exc:
        # R1：完整响应到达之前的一切失败都归 transport；phase 记录失败发生的位置
        record["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        record["outcome_class"] = "transport"
        record["detail"] = f"phase={phase} {type(exc).__name__}: {exc}"
        record["retry_worthiness_guess"] = _retry_guess("transport", None, phase)
        return record
    finally:
        conn.close()

    record["elapsed_ms"] = round((time.perf_counter() - started) * 1000)

    # R2：HTTP 状态层
    if not 200 <= record["http_status"] <= 299:
        record["body_parse"] = "skipped_non_2xx"
        record["outcome_class"] = "http-api-protocol"
        record["detail"] = "server rejected at HTTP layer"
        record["retry_worthiness_guess"] = _retry_guess(
            "http-error", record["http_status"], None
        )
        return record

    # R3：payload 契约层
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        record["body_parse"] = "malformed"
        record["outcome_class"] = "http-api-protocol"
        record["detail"] = f"2xx body is not valid JSON: {type(exc).__name__}"
        record["retry_worthiness_guess"] = _retry_guess("http-api-protocol", None, None)
        return record

    contract_ok, reason = _validate_contract(payload)
    if not contract_ok:
        record["body_parse"] = "schema_violation"
        record["outcome_class"] = "http-api-protocol"
        record["detail"] = reason
        record["retry_worthiness_guess"] = _retry_guess("http-api-protocol", None, None)
        return record

    record["body_parse"] = "ok"
    record["finish_reason"] = payload["choices"][0]["finish_reason"]

    # R4 / R5：模型结果层
    if record["finish_reason"] == "stop":
        record["outcome_class"] = "success"
        record["detail"] = "finished normally"
        record["retry_worthiness_guess"] = _retry_guess("success", record["http_status"], None)
    else:
        record["outcome_class"] = "model-result-condition"
        record["detail"] = f"result not normally completed: finish_reason={record['finish_reason']!r}"
        record["retry_worthiness_guess"] = _retry_guess("model-result-condition", None, None)
    return record
