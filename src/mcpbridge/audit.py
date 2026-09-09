from __future__ import annotations

import hashlib
import json
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from .models import AuditEvent

_lock = Lock()
_events: deque[AuditEvent] = deque(maxlen=250)
_last_hash = "GENESIS"


def _hash_payload(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def append_audit(
    *,
    actor: str,
    role: str,
    phase: str,
    server: str,
    tool: str,
    decision: str,
    arguments: dict,
) -> AuditEvent:
    """Append a tamper-evident in-memory audit event.

    The lock covers reading the previous hash and writing the new event so concurrent
    requests cannot fork the in-process chain. Durable cross-instance audit retention is
    intentionally documented as a production-hardening requirement.
    """

    global _last_hash
    request_hash = _hash_payload(arguments)
    with _lock:
        base = {
            "event_id": str(uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "role": role,
            "phase": phase,
            "server": server,
            "tool": tool,
            "decision": decision,
            "request_hash": request_hash,
            "previous_hash": _last_hash,
        }
        event_hash = _hash_payload(base)
        event = AuditEvent(**base, event_hash=event_hash)
        _events.appendleft(event)
        _last_hash = event_hash
        return event


def list_audit(limit: int = 50) -> list[dict]:
    with _lock:
        return [event.__dict__.copy() for event in list(_events)[: max(1, min(limit, 100))]]


def verify_audit_chain() -> bool:
    """Verify the currently retained in-memory chain from oldest to newest."""

    with _lock:
        ordered = list(reversed(_events))
    previous = "GENESIS"
    for event in ordered:
        if event.previous_hash != previous:
            return False
        base = {
            "event_id": event.event_id,
            "timestamp": event.timestamp,
            "actor": event.actor,
            "role": event.role,
            "phase": event.phase,
            "server": event.server,
            "tool": event.tool,
            "decision": event.decision,
            "request_hash": event.request_hash,
            "previous_hash": event.previous_hash,
        }
        if _hash_payload(base) != event.event_hash:
            return False
        previous = event.event_hash
    return True


def reset_audit_for_tests() -> None:
    global _last_hash
    with _lock:
        _events.clear()
        _last_hash = "GENESIS"
