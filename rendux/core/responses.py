from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

API_ENVELOPE_VERSION = "1.0"
DEFAULT_CAPABILITY_VERSION = "0.1"


def api_envelope(
    *,
    capability: str,
    operation: str,
    data: dict[str, Any],
    source: str,
    count: int | None = None,
    read_only: bool = True,
    errors: list[dict[str, Any]] | None = None,
    capability_version: str = DEFAULT_CAPABILITY_VERSION,
    generated_at: datetime | None = None,
    tool_prefix: str = "rendux",
) -> dict[str, Any]:
    generated = generated_at or datetime.now(UTC)
    meta: dict[str, Any] = {
        "generated_at": _format_timestamp(generated),
        "source": source,
        "read_only": read_only,
        "mcp": {
            "compatible": True,
            "tool_name": f"{tool_prefix}.{capability}.{operation}",
            "content_type": "application/json",
            "read_only": read_only,
        },
    }
    if count is not None:
        meta["count"] = count

    return {
        "api": {
            "version": API_ENVELOPE_VERSION,
            "capability": capability,
            "operation": operation,
            "capability_version": capability_version,
        },
        "data": data,
        "meta": meta,
        "errors": errors or [],
    }


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
