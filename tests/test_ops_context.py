"""Tests for request-time /ops view_ctx injection."""

from __future__ import annotations

from demo.ops_context import build_ops_view_ctx


def test_build_ops_view_ctx_prepends_live_event():
    static = {
        "recent_events": [
            {"title": "Deployment complete", "time": "09:22", "status": "ok", "body": "done"},
        ],
    }
    ctx = build_ops_view_ctx(static)
    assert ctx["recent_events"][0]["title"] == "Live refresh"
    assert "view_ctx" in ctx["recent_events"][0]["body"]
    assert ctx["recent_events"][1]["title"] == "Deployment complete"


def test_build_ops_view_ctx_updates_open_alerts_kpi():
    static = {
        "kpi": [
            {"label": "Active Services", "value": "24"},
            {"label": "Open Alerts", "value": "3", "trend": "static"},
        ],
    }
    ctx = build_ops_view_ctx(static)
    alerts = next(row for row in ctx["kpi"] if row["label"] == "Open Alerts")
    assert alerts["value"] in {"2", "3", "4", "5"}
    assert alerts["trend"].startswith("live @ ")
    assert static["kpi"][1]["value"] == "3"  # baseline unchanged


def test_ops_http_includes_live_refresh_marker():
    from starlette.testclient import TestClient

    from demo.main import create_app

    client = TestClient(create_app())
    response = client.get("/ops")
    assert response.status_code == 200
    assert "Live refresh" in response.text
    assert "view_ctx" in response.text
