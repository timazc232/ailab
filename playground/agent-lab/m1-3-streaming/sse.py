"""Day 3（M1.3）增量 SSE parser。

契约（plan §8）：
- 事件形态：`data: {json}\\n\\n`，终止 `data: [DONE]`。
- UTF-8 用 codecs 增量解码器，跨 chunk 字符不得损坏。
- 完整性：事件内 finish_reason 且收到 [DONE] 才算 complete；
  任一协议错误则不得判 complete。
"""

from __future__ import annotations

import codecs
import json
from dataclasses import dataclass, field

# 非流式参考答案：f1/f2 重组结果必须与此字节级一致
REFERENCE_TEXT = "你好，世界。Streaming does not change the answer."

# parser 每次从 socket 读的字节数（与 mock 的写入粒度独立）
READ_SIZE = 8


@dataclass
class StreamParseResult:
    events_received: int = 0
    deltas_assembled: str = ""
    finish_reason: str | None = None
    done_received: bool = False
    completeness: str = "incomplete"  # complete / incomplete / cancelled / protocol_error
    errors: list[str] = field(default_factory=list)
    text_matches_nonstream: bool | None = None

    def finalize(self, *, cancelled: bool = False) -> None:
        if cancelled:
            self.completeness = "cancelled"
        elif self.errors:
            self.completeness = "protocol_error"
        elif self.finish_reason and self.done_received:
            self.completeness = "complete"
        else:
            self.completeness = "incomplete"
        self.text_matches_nonstream = self.deltas_assembled == REFERENCE_TEXT


def _split_events(buf: str) -> tuple[str, list[str]]:
    """按空行切出完整 SSE 事件，返回 (剩余缓冲, 完整事件列表)。"""
    events: list[str] = []
    # 同时接受 LF 与 CRLF 分隔
    while True:
        if "\r\n\r\n" in buf:
            sep = "\r\n\r\n"
        elif "\n\n" in buf:
            sep = "\n\n"
        else:
            break
        raw, buf = buf.split(sep, 1)
        if raw.strip():
            events.append(raw)
    return buf, events


def _data_payload(event_text: str) -> str | None:
    lines = []
    for line in event_text.splitlines():
        if line.startswith("data:"):
            lines.append(line[5:].lstrip())
    if not lines:
        return None
    return "\n".join(lines)


def _apply_event(result: StreamParseResult, event_text: str) -> None:
    payload = _data_payload(event_text)
    if payload is None:
        return
    result.events_received += 1
    if payload.strip() == "[DONE]":
        result.done_received = True
        return
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError as exc:
        result.errors.append(f"malformed_json: {exc.msg}")
        return
    choices = obj.get("choices") if isinstance(obj, dict) else None
    if not isinstance(choices, list) or not choices:
        result.errors.append("missing_choices")
        return
    choice = choices[0] if isinstance(choices[0], dict) else {}
    delta = choice.get("delta") if isinstance(choice.get("delta"), dict) else {}
    content = delta.get("content")
    if isinstance(content, str):
        result.deltas_assembled += content
    finish = choice.get("finish_reason")
    if isinstance(finish, str) and finish:
        result.finish_reason = finish


def parse_sse_response(
    response,
    conn,
    *,
    cancel_after_events: int | None = None,
) -> StreamParseResult:
    """从 http.client 响应增量解析 SSE。cancel_after_events 模拟用户点停止。"""
    decoder = codecs.getincrementaldecoder("utf-8")()
    buf = ""
    result = StreamParseResult()
    cancelled = False

    def _flush_events() -> bool:
        """处理缓冲中的完整事件。返回 True 表示应停止读取（已取消）。"""
        nonlocal buf, cancelled
        buf, events = _split_events(buf)
        for event in events:
            _apply_event(result, event)
            if cancel_after_events is not None and result.events_received >= cancel_after_events:
                cancelled = True
                try:
                    conn.close()
                except OSError:
                    pass
                return True
        return False

    try:
        while True:
            chunk = response.read(READ_SIZE)
            if not chunk:
                break
            buf += decoder.decode(chunk)
            if _flush_events():
                break
        if not cancelled:
            buf += decoder.decode(b"", final=True)
            _flush_events()
            leftover = buf.strip()
            if leftover:
                result.errors.append("trailing_incomplete_event")
    except (OSError, Exception) as exc:  # 取消关闭连接时可能抛 IncompleteRead / OSError
        if not cancelled:
            result.errors.append(f"read_error: {type(exc).__name__}: {exc}")

    result.finalize(cancelled=cancelled)
    return result
