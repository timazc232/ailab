"""Day 7（M1.7）可 JSON 序列化的显式 Agent State。"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass, field

VALID_STATUSES = frozenset({"created", "running", "completed", "failed", "cancelled", "paused"})
ALLOWED_TRANSITIONS = {
    "created": frozenset({"running"}),
    "paused": frozenset({"running", "cancelled"}),
    "running": frozenset({"completed", "failed", "cancelled", "paused"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}


@dataclass
class AgentState:
    version: int
    run_id: str
    status: str
    termination_reason: str | None
    step_count: int
    max_steps: int
    model_cursor: int
    messages: list[dict] = field(default_factory=list)
    tool_trace: list[dict] = field(default_factory=list)
    final_answer: str | None = None

    @classmethod
    def create(cls, run_id: str, user_message: str, max_steps: int) -> "AgentState":
        if not run_id or not user_message:
            raise ValueError("run_id and user_message must not be empty")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        return cls(
            version=1,
            run_id=run_id,
            status="created",
            termination_reason=None,
            step_count=0,
            max_steps=max_steps,
            model_cursor=0,
            messages=[
                {"role": "system", "content": "You are a deterministic scripted agent."},
                {"role": "user", "content": user_message},
            ],
        )

    def transition(self, new_status: str, reason: str | None = None) -> None:
        if new_status not in VALID_STATUSES:
            raise ValueError(f"unknown status {new_status!r}")
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"illegal state transition {self.status!r} -> {new_status!r}")
        self.status = new_status
        self.termination_reason = reason

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> "AgentState":
        data = json.loads(text)
        required = {
            "version", "run_id", "status", "termination_reason", "step_count",
            "max_steps", "model_cursor", "messages", "tool_trace", "final_answer",
        }
        if not isinstance(data, dict) or set(data) != required:
            raise ValueError("checkpoint fields do not match AgentState contract")
        if data["version"] != 1 or data["status"] not in VALID_STATUSES:
            raise ValueError("unsupported checkpoint version or status")
        if not all(isinstance(data[key], int) for key in ("step_count", "max_steps", "model_cursor")):
            raise ValueError("checkpoint counters must be integers")
        if not isinstance(data["messages"], list) or not isinstance(data["tool_trace"], list):
            raise ValueError("checkpoint messages and tool_trace must be lists")
        return cls(**deepcopy(data))
