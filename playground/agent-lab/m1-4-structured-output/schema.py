"""Day 4（M1.4）最小 schema 校验 + 一次受控重试。

契约（plan §8）：
- 只实现 object / required / type / enum / additionalProperties=false 子集。
- 非法输出不得进入 accepted 通道。
- 可 retry：missing_field、wrong_type；最多 1 次。
- 不可 retry：invalid_json、extra_field。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

ALLOWED_STATUS = ("ok", "degraded", "down")
RETRYABLE = frozenset({"missing_field", "wrong_type"})
MAX_RETRIES = 1


@dataclass
class ValidationResult:
    ok: bool
    error_class: str | None = None  # invalid_json / missing_field / wrong_type / extra_field
    detail: str = ""
    value: dict | None = None  # 仅 ok 时非空；非法对象绝不放这里


def parse_and_validate(raw: str | bytes) -> ValidationResult:
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            return ValidationResult(False, "invalid_json", f"not utf-8: {exc}")
    else:
        text = raw
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return ValidationResult(False, "invalid_json", f"malformed JSON: {exc.msg}")

    if not isinstance(payload, dict):
        return ValidationResult(False, "wrong_type", "top-level value is not an object")

    extra = [k for k in payload if k not in {"status", "severity", "summary"}]
    if extra:
        return ValidationResult(False, "extra_field", f"unexpected fields: {extra}")

    missing = [k for k in ("status", "severity", "summary") if k not in payload]
    if missing:
        return ValidationResult(False, "missing_field", f"missing fields: {missing}")

    status = payload["status"]
    if not isinstance(status, str) or status not in ALLOWED_STATUS:
        return ValidationResult(
            False, "wrong_type", f"status must be one of {ALLOWED_STATUS}, got {status!r}"
        )

    severity = payload["severity"]
    # JSON 数字：bool 是 int 子类，必须排除
    if isinstance(severity, bool) or not isinstance(severity, int) or not 0 <= severity <= 5:
        return ValidationResult(
            False, "wrong_type", f"severity must be int 0-5, got {severity!r}"
        )

    summary = payload["summary"]
    if not isinstance(summary, str) or summary == "":
        return ValidationResult(False, "wrong_type", "summary must be a non-empty string")

    return ValidationResult(True, None, "ok", {"status": status, "severity": severity, "summary": summary})


def should_retry(error_class: str | None, attempt: int) -> bool:
    """attempt 从 0 计：首次失败后 attempt=0 仍可 retry。"""
    return error_class in RETRYABLE and attempt < MAX_RETRIES
