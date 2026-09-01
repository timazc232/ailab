"""Day 2（M1.2）messages 构造、校验、确定性序列化与预算截断。

契约（plan §5.3 / §8）：
- role 限定 system / user / assistant；空 content 与非法 role 在构造期 raise（fail fast）。
- 序列化固定参数（sort_keys=False + 紧凑分隔符 + ensure_ascii=False），字节确定。
- 截断 Policy：保 system + 从最新轮次向回保留（drop-oldest-except-system），无空洞。
- 字符数是预算 proxy，不是 token；用于验证机制，不用于容量/费用宣称。
"""

from __future__ import annotations

import json

MODEL = "mock-model-day1"
VALID_ROLES = ("system", "user", "assistant")


def make_message(role: str, content: str) -> dict:
    """构造一条消息；非法输入在构造期拒绝，让非法状态不可表示。"""
    if not isinstance(role, str) or role not in VALID_ROLES:
        raise ValueError(f"invalid role {role!r}; expected one of {VALID_ROLES}")
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")
    if content == "":
        raise ValueError("content must not be empty")
    return {"role": role, "content": content}


def serialize_payload(messages: list[dict], model: str = MODEL) -> bytes:
    """把请求 payload 序列化为字节；固定参数保证同输入 → 同字节。"""
    payload = {"model": model, "messages": messages}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def total_chars(messages: list[dict]) -> int:
    """字符预算 proxy：所有 content 的字符数之和（不含 role 与结构开销）。"""
    return sum(len(m["content"]) for m in messages)


def truncate_to_budget(messages: list[dict], budget_chars: int) -> tuple[list[dict], dict]:
    """按 Policy 截断：保全部 system；非 system 从最新向回保留，放不下即停（更早的全部丢弃）。

    返回 (截断后的消息列表, policy 报告)。列表顺序保持时间线顺序，system 在前。
    """
    if budget_chars <= 0:
        raise ValueError(f"budget_chars must be positive, got {budget_chars}")

    system_msgs = [m for m in messages if m["role"] == "system"]
    others = [m for m in messages if m["role"] != "system"]
    system_chars = total_chars(system_msgs)
    if system_chars > budget_chars:
        raise ValueError(
            f"system messages alone ({system_chars} chars) exceed budget {budget_chars}"
        )

    kept_reversed: list[dict] = []
    used = system_chars
    for msg in reversed(others):
        cost = len(msg["content"])
        if used + cost > budget_chars:
            break  # 放不下即停：更早的轮次全部丢弃，保持对话连续、无空洞
        kept_reversed.append(msg)
        used += cost

    kept = list(reversed(kept_reversed))
    result = system_msgs + kept
    report = {
        "budget_chars": budget_chars,
        "input_messages": len(messages),
        "kept_messages": len(result),
        "dropped_messages": len(messages) - len(result),
        "total_chars": total_chars(result),
    }
    return result, report
