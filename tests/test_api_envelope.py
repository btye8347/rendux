from datetime import UTC, datetime

from rendux.core.responses import api_envelope


def test_api_envelope_provides_stable_core_contract():
    payload = api_envelope(
        capability="services",
        operation="list",
        data={"services": []},
        source="rendux.services",
        count=0,
        read_only=True,
        generated_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )

    assert payload == {
        "api": {
            "version": "1.0",
            "capability": "services",
            "operation": "list",
            "capability_version": "0.1",
        },
        "data": {"services": []},
        "meta": {
            "generated_at": "2026-01-01T12:00:00Z",
            "source": "rendux.services",
            "count": 0,
            "read_only": True,
            "mcp": {
                "compatible": True,
                "tool_name": "rendux.services.list",
                "content_type": "application/json",
                "read_only": True,
            },
        },
        "errors": [],
    }


def test_api_envelope_default_tool_prefix_is_rendux():
    payload = api_envelope(
        capability="views",
        operation="get",
        data={},
        source="rendux.views",
        generated_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )

    assert payload["meta"]["mcp"]["tool_name"] == "rendux.views.get"


def test_api_envelope_custom_tool_prefix():
    payload = api_envelope(
        capability="notes",
        operation="create",
        data={"note": {"id": "n1"}},
        source="app.notes",
        tool_prefix="myapp",
        read_only=False,
        errors=[{"code": "partial_warning", "message": "Example.", "source": "app.notes"}],
        generated_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )

    assert payload["meta"]["mcp"]["tool_name"] == "myapp.notes.create"
    assert payload["meta"]["mcp"]["read_only"] is False
    assert payload["errors"][0]["code"] == "partial_warning"
