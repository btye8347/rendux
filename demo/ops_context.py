"""Request-time context for the /ops RDL view.

Merged over static ``data:`` from config/views.yaml (route-level wins).
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def build_ops_view_ctx(static: dict[str, Any]) -> dict[str, Any]:
    """Build dynamic ops context from YAML baseline plus live-ish overrides."""
    now = datetime.now(timezone.utc).astimezone()
    clock = now.strftime("%H:%M:%S")
    open_alerts = 2 + (now.minute % 4)

    kpi = deepcopy(static.get("kpi", []))
    for row in kpi:
        if row.get("label") == "Open Alerts":
            row["value"] = str(open_alerts)
            row["trend"] = f"live @ {clock}"
        elif row.get("label") == "Deployments Today":
            row["trend"] = f"refreshed {clock}"

    live_event = {
        "title": "Live refresh",
        "time": clock,
        "status": "info",
        "body": "Ops dashboard data injected via view_ctx at request time.",
    }
    recent_events = [live_event, *deepcopy(static.get("recent_events", []))]

    return {
        "kpi": kpi,
        "recent_events": recent_events[:6],
        "service_health": deepcopy(static.get("service_health", [])),
        "recent_changes": deepcopy(static.get("recent_changes", [])),
    }
