from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class Effect(StrEnum):
    READ = "read"
    WRITE = "write"


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    APPROVER = "approver"


@dataclass(frozen=True)
class ToolPolicy:
    server: str
    name: str
    effect: Effect
    allowed_roles: tuple[Role, ...]
    approval_required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["effect"] = self.effect.value
        data["allowed_roles"] = [x.value for x in self.allowed_roles]
        return data


@dataclass(frozen=True)
class PlannedToolCall:
    server: str
    tool: str
    arguments: dict[str, Any]
    reason: str


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    actor: str
    role: str
    phase: str
    server: str
    tool: str
    decision: str
    request_hash: str
    previous_hash: str
    event_hash: str
