"""Day 5（M1.5）scripted model fixtures；不调用真实模型。"""

from __future__ import annotations

import json


def tool_call_message(call_id: str, name: str, arguments: dict | str) -> dict:
    arguments_text = (
        arguments
        if isinstance(arguments, str)
        else json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))
    )
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": arguments_text},
            }
        ],
    }


FIXTURES = {
    "t1": tool_call_message("call_t1", "add", {"a": 2, "b": 3}),
    "t2": tool_call_message("call_t2", "lookup_secret", {"name": "api-key"}),
    "t3": tool_call_message("call_t3", "add", {"a": "two"}),
    "t4": tool_call_message("call_t4", "run_shell", {"command": "rm -rf /"}),
}
