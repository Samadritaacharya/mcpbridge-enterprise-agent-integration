from __future__ import annotations

from .models import PlannedToolCall


def plan_request(text: str) -> PlannedToolCall:
    q = text.lower().strip()
    if "change request" in q or "change" in q and "create" in q:
        return PlannedToolCall("itsm", "create_change_request", {"service": "payments-api", "summary": text, "risk": "medium", "implementation_window": "next approved maintenance window"}, "Write intent detected: change-management action.")
    if "create incident" in q or "open incident" in q:
        return PlannedToolCall("itsm", "create_incident", {"title": "Agent-proposed incident", "service": "payments-api", "severity": "SEV-2", "summary": text}, "Write intent detected: incident creation.")
    if "github issue" in q or "create issue" in q:
        return PlannedToolCall("github", "create_github_issue", {"repo": "payments-api", "title": "Agent-proposed follow-up", "body": text, "severity": "medium"}, "Write intent detected: repository issue creation.")
    if "incident" in q:
        incident_id = "INC-428" if "428" in q else "INC-431"
        return PlannedToolCall("itsm", "get_incident", {"incident_id": incident_id}, "Read-only ITSM investigation.")
    if "repository" in q or "repo" in q or "ci" in q or "deploy" in q:
        repo = "payments-api" if "payment" in q else "platformpulse"
        return PlannedToolCall("github", "get_repository_status", {"repo": repo}, "Read-only repository health request.")
    if "purchase order" in q or "po" in q:
        supplier = "SUP-BETA" if "beta" in q else "SUP-ALPHA"
        return PlannedToolCall("business", "query_purchase_orders", {"supplier_id": supplier}, "Read-only business-system query.")
    if "supplier" in q or "alpha" in q or "beta" in q:
        return PlannedToolCall("business", "compare_suppliers", {"left": "SUP-ALPHA", "right": "SUP-BETA"}, "Read-only supplier comparison.")
    return PlannedToolCall("business", "generate_decision_pack", {"question": text}, "Default advisory decision-pack route.")
