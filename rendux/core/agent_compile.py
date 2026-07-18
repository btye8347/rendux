"""Compile RDL view fragments for LLM authoring loops."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from rendux.core.layout import LayoutConfigError, LayoutRenderer
from rendux.core.lint_rdl import RdlLinter

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
_TEMPLATES = _PACKAGE_ROOT / "rendux" / "templates"


def compile_fragment(fragment: dict[str, Any]) -> dict[str, Any]:
    """Lint and strict-render a view fragment. Returns a JSON-serializable report."""
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    notes: list[dict[str, str]] = []

    data_block = fragment.get("data", {})
    if data_block is None:
        data_block = {}
    if not isinstance(data_block, dict):
        errors.append({"path": "data", "message": "data must be a mapping"})
        data_block = {}

    workspace = fragment.get("workspace", {})
    if not isinstance(workspace, dict):
        errors.append({"path": "workspace", "message": "workspace must be a mapping"})
        layout: list[Any] = []
    else:
        layout = workspace.get("layout", [])
        if layout is None:
            layout = []
        if not isinstance(layout, list):
            errors.append({"path": "workspace.layout", "message": "layout must be a list"})
            layout = []

    if not errors:
        config = {
            "views": {
                "_agent": {
                    "data": data_block,
                    "workspace": {"layout": layout},
                }
            }
        }
        issues = RdlLinter(strict=True).lint_views_config(config)
        for issue in issues:
            entry = {"path": issue.path, "message": issue.message}
            if issue.level == "error":
                errors.append(entry)
            elif issue.level == "warning":
                warnings.append(entry)
            else:
                notes.append(entry)

    render_ok = False
    if not errors:
        try:
            env = Environment(loader=FileSystemLoader(str(_TEMPLATES)), autoescape=True)
            LayoutRenderer(env, strict=True).render(layout, data_block)
            render_ok = True
        except LayoutConfigError as exc:
            errors.append({"path": "workspace.layout", "message": str(exc)})

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "notes": notes,
        "strict_render_ok": render_ok,
    }
