#!/usr/bin/env python3
"""Build contracts/catalog.verified.json from verified widget contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIDGETS_DIR = ROOT / "contracts" / "widgets"
OUTPUT = ROOT / "contracts" / "catalog.verified.json"

# Tiny usage snippets for few-shot grounding (optional per widget)
SNIPPETS: dict[str, dict] = {
    "stat_card": {
        "widget": "stat_card",
        "each": "$ctx.kpi",
        "label": "$item.label",
        "value": "$item.value",
        "status": "$item.status",
    },
    "alert": {
        "widget": "alert",
        "variant": "warn",
        "title": "Attention",
        "message": "Something needs review.",
    },
    "data_table": {
        "widget": "data_table",
        "title": "$ctx.table.title",
        "columns": "$ctx.table.columns",
        "rows": "$ctx.table.rows",
        "searchable": True,
    },
    "form": {
        "widget": "form",
        "fields": "$ctx.edit_form.fields",
        "submit_label": "Save",
        "cancel_href": "/",
    },
    "modal": {
        "widget": "modal",
        "id": "confirm",
        "title": "Confirm?",
        "body": "This action cannot be undone.",
        "trigger_label": "Confirm",
    },
    "kv_table": {
        "widget": "kv_table",
        "title": "$ctx.detail.title",
        "rows": "$ctx.detail.rows",
    },
}


def build_catalog() -> dict:
    widgets: list[dict] = []
    for path in sorted(WIDGETS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "verified":
            continue
        if not data.get("description"):
            raise SystemExit(f"verified widget {data.get('name')!r} missing description")
        entry = {
            "name": data["name"],
            "description": data["description"],
            "accepts_each": data.get("accepts_each", False),
            "interaction": data.get("interaction", {"profile": "static"}),
            "props": data.get("props", {}),
        }
        if "item_schema" in data:
            entry["item_schema"] = data["item_schema"]
        if data["name"] in SNIPPETS:
            entry["example"] = SNIPPETS[data["name"]]
        widgets.append(entry)

    return {
        "version": "0.1.0",
        "description": (
            "Closed vocabulary for LLM RDL authoring. "
            "Only these verified widgets may be emitted."
        ),
        "widget_count": len(widgets),
        "widgets": widgets,
    }


def main() -> int:
    catalog = build_catalog()
    OUTPUT.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)} ({catalog['widget_count']} widgets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
