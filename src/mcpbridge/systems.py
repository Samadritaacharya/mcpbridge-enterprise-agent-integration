from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from .data import INCIDENTS, PURCHASE_ORDERS, REPOSITORIES, SUPPLIERS


def search_repository(query: str) -> list[dict]:
    q = query.lower().strip()
    return [deepcopy(v) for k, v in REPOSITORIES.items() if q in k.lower() or q in str(v).lower()]


def get_repository_status(repo: str) -> dict:
    if repo not in REPOSITORIES:
        raise ValueError(f"unknown repository: {repo}")
    return deepcopy(REPOSITORIES[repo])


def create_github_issue(repo: str, title: str, body: str, severity: str = "medium") -> dict:
    if repo not in REPOSITORIES:
        raise ValueError(f"unknown repository: {repo}")
    return {"issue_id": f"ISS-{uuid4().hex[:7].upper()}", "repo": repo, "title": title, "body": body, "severity": severity, "status": "created", "synthetic": True}


def get_incident(incident_id: str) -> dict:
    if incident_id not in INCIDENTS:
        raise ValueError(f"unknown incident: {incident_id}")
    return deepcopy(INCIDENTS[incident_id])


def create_incident(title: str, service: str, severity: str, summary: str) -> dict:
    return {"id": f"INC-{1000 + len(INCIDENTS) + 1}", "title": title, "service": service, "severity": severity, "summary": summary, "status": "created", "synthetic": True}


def create_change_request(service: str, summary: str, risk: str, implementation_window: str) -> dict:
    return {"id": f"CHG-{uuid4().hex[:6].upper()}", "service": service, "summary": summary, "risk": risk, "implementation_window": implementation_window, "status": "created", "synthetic": True}


def get_supplier(supplier_id: str) -> dict:
    if supplier_id not in SUPPLIERS:
        raise ValueError(f"unknown supplier: {supplier_id}")
    return deepcopy(SUPPLIERS[supplier_id])


def compare_suppliers(left: str, right: str) -> dict:
    a, b = get_supplier(left), get_supplier(right)
    return {
        "left": a,
        "right": b,
        "summary": f"{a['name']} is lower cost/faster; {b['name']} has longer warranty and security-update coverage.",
        "recommendation": "Choose by business priority; human approval remains required for downstream writes.",
    }


def query_purchase_orders(supplier_id: str) -> list[dict]:
    return [deepcopy(po) for po in PURCHASE_ORDERS if po["supplier_id"] == supplier_id]


def generate_decision_pack(question: str) -> dict:
    return {
        "question": question,
        "evidence": ["SUP-ALPHA", "SUP-BETA", "PO-9021", "PO-9033"],
        "recommendation": "Prefer Alpha for cost/lead-time sensitivity; retain Beta for resilience-led requirements.",
        "authority": "advisory-only",
        "requires_human_decision": True,
    }
