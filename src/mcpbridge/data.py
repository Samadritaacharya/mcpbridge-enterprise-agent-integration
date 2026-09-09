from __future__ import annotations

REPOSITORIES = {
    "platformpulse": {
        "name": "platformpulse",
        "default_branch": "main",
        "open_prs": 2,
        "open_issues": 5,
        "ci": "green",
        "last_deploy": "2026-09-08T16:20:00Z",
        "risk": "low",
    },
    "payments-api": {
        "name": "payments-api",
        "default_branch": "main",
        "open_prs": 6,
        "open_issues": 12,
        "ci": "degraded",
        "last_deploy": "2026-09-09T08:40:00Z",
        "risk": "medium",
    },
}

INCIDENTS = {
    "INC-428": {
        "id": "INC-428",
        "service": "payments-api",
        "severity": "SEV-2",
        "status": "investigating",
        "summary": "Elevated checkout latency after morning deployment.",
        "owner": "Payments SRE",
    },
    "INC-431": {
        "id": "INC-431",
        "service": "supplier-portal",
        "severity": "SEV-3",
        "status": "monitoring",
        "summary": "Intermittent document-upload timeouts.",
        "owner": "Platform Operations",
    },
}

SUPPLIERS = {
    "SUP-ALPHA": {
        "id": "SUP-ALPHA",
        "name": "Alpha Components",
        "unit_price_eur": 438,
        "lead_time_days": 28,
        "warranty_months": 48,
        "security_updates_years": 5,
        "risk": "medium",
    },
    "SUP-BETA": {
        "id": "SUP-BETA",
        "name": "Beta Systems",
        "unit_price_eur": 492,
        "lead_time_days": 41,
        "warranty_months": 60,
        "security_updates_years": 7,
        "risk": "low",
    },
}

PURCHASE_ORDERS = [
    {"po": "PO-9021", "supplier_id": "SUP-ALPHA", "value_eur": 131400, "status": "approved"},
    {"po": "PO-9033", "supplier_id": "SUP-BETA", "value_eur": 98400, "status": "pending"},
]
