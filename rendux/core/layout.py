"""
RendUX Declarative Layout (RDL) renderer.

Implements RDL grammar v0.1 — see docs/rdl-spec-v0.1.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, TemplateNotFound
from markupsafe import Markup, escape

from rendux.core.contracts import canonical_prop_names, load_widget_registry, normalize_widget_props

# ── constants ────────────────────────────────────────────────────────────────

MAX_DEPTH = 50

_CTX_RE  = re.compile(r"^\$ctx\.(.+)$")
_ITEM_RE = re.compile(r"^\$item\.(.+)$")
_ITEM_BARE = "$item"

_RESERVED = frozenset({"widget", "when", "each"})

_KNOWN_TYPES    = frozenset({"stack", "row", "grid", "section", "split"})
_VALID_COLUMNS  = frozenset({1, 2, 3, 4, "auto"})
_GAP_MODIFIERS  = frozenset({"sm", "lg"})
_GAP_CSS        = {"sm": "0.5rem", "lg": "1.5rem"}

# Keys that widget params must never overwrite
_PROTECTED_CTX = frozenset({
    "url_for", "request", "view_shell", "layout_html",
    "theme_list", "custom_theme_css", "static_version",
})


# ── exceptions ───────────────────────────────────────────────────────────────

class LayoutConfigError(ValueError):
    """Raised for structural errors in a layout definition."""


@dataclass(frozen=True)
class WidgetInvocation:
    """Resolved widget dispatch — portable conformance assertion unit."""

    widget: str
    params: dict[str, Any]


# ── renderer ─────────────────────────────────────────────────────────────────

class LayoutRenderer:
    """Walks an RDL node tree and renders it to an HTML string."""

    def __init__(self, env: Environment, *, strict: bool = False) -> None:
        self._env = env
        self._strict = strict

    # ── public ──────────────────────────────────────────────────────────────

    def render(
        self,
        nodes: list[Any] | None,
        ctx: dict[str, Any],
        _depth: int = 0,
    ) -> str:
        """Render a list of RDL nodes into an HTML string."""
        if _depth > MAX_DEPTH:
            raise LayoutConfigError(
                f"Layout nesting exceeds the maximum depth ({MAX_DEPTH}). "
                "Check for runaway recursion in your layout definition."
            )
        parts: list[str] = []
        for node in nodes or []:
            html = self._dispatch(node, ctx, item=None, depth=_depth)
            if html:
                parts.append(html)
        return "\n".join(parts)

    def collect_invocations(
        self,
        nodes: list[Any] | None,
        ctx: dict[str, Any],
        _depth: int = 0,
    ) -> list[WidgetInvocation]:
        """Return resolved widget dispatches without rendering HTML."""
        if _depth > MAX_DEPTH:
            raise LayoutConfigError(
                f"Layout nesting exceeds the maximum depth ({MAX_DEPTH}). "
                "Check for runaway recursion in your layout definition."
            )
        out: list[WidgetInvocation] = []
        for node in nodes or []:
            self._collect_node(node, ctx, item=None, depth=_depth, out=out)
        return out

    # ── dispatch ─────────────────────────────────────────────────────────────

    def _dispatch(
        self,
        node: Any,
        ctx: dict[str, Any],
        item: Any,
        depth: int,
    ) -> str:
        if not isinstance(node, dict):
            return ""
        if not self._check_when(node, ctx, item):
            return ""

        if "widget" in node:
            return self._widget(node, ctx, item)
        if "type" in node:
            return self._container(node, ctx, depth)
        if node.get("divider"):
            return self._render_template("divider", ctx, {})
        if "heading" in node:
            try:
                level = min(max(int(node.get("level", 2)), 1), 6)
            except (ValueError, TypeError):
                level = 2
            text = escape(str(node["heading"]))
            return f'<h{level} class="workspace-heading">{text}</h{level}>'
        return ""

    def _collect_node(
        self,
        node: Any,
        ctx: dict[str, Any],
        item: Any,
        depth: int,
        out: list[WidgetInvocation],
    ) -> None:
        if not isinstance(node, dict):
            return
        if not self._check_when(node, ctx, item):
            return

        if "widget" in node:
            self._collect_widget(node, ctx, item, out)
            return
        if "type" in node:
            self._collect_container(node, ctx, depth, out)
            return
        if node.get("divider"):
            out.append(WidgetInvocation("divider", {}))
            return
        if "heading" in node:
            out.append(WidgetInvocation("_heading", {
                "heading": node.get("heading"),
                "level": node.get("level", 2),
            }))
            return

    def _collect_widget(
        self,
        node: dict,
        ctx: dict[str, Any],
        item: Any,
        out: list[WidgetInvocation],
    ) -> None:
        name = node.get("widget")
        if not name or not isinstance(name, str):
            return

        params = {k: v for k, v in node.items() if k not in _RESERVED}
        each_ref = node.get("each")

        if each_ref is not None:
            collection = self._resolve(each_ref, ctx, item)
            if not isinstance(collection, (list, tuple)):
                collection = []
            for entry in collection:
                resolved = self._resolve_all(params, ctx, item=entry, widget=name)
                safe = normalize_widget_props(name, {
                    k: v for k, v in resolved.items() if k not in _PROTECTED_CTX
                })
                out.append(WidgetInvocation(name, safe))
            return

        resolved = self._resolve_all(params, ctx, item, widget=name)
        safe = normalize_widget_props(name, {
            k: v for k, v in resolved.items() if k not in _PROTECTED_CTX
        })
        out.append(WidgetInvocation(name, safe))

    def _collect_container(
        self,
        node: dict,
        ctx: dict[str, Any],
        depth: int,
        out: list[WidgetInvocation],
    ) -> None:
        t = node.get("type", "")
        if t == "split":
            primary = node.get("primary", [])
            secondary = node.get("secondary", [])
            for child in primary if isinstance(primary, list) else []:
                self._collect_node(child, ctx, None, depth + 1, out)
            for child in secondary if isinstance(secondary, list) else []:
                self._collect_node(child, ctx, None, depth + 1, out)
            # split dispatches split_pane widget at render time
            out.append(WidgetInvocation("split_pane", {
                "initial_primary": node.get("initial", "50%"),
                "min_primary": node.get("min", 120),
                "pane_id": str(node.get("id", "rdl-0")),
            }))
            return

        children = node.get("children", [])
        if isinstance(children, list):
            for child in children:
                self._collect_node(child, ctx, None, depth + 1, out)

    # ── widget ───────────────────────────────────────────────────────────────

    def _widget(self, node: dict, ctx: dict[str, Any], item: Any) -> str:
        name = node.get("widget")
        if not name or not isinstance(name, str):
            return ""

        params   = {k: v for k, v in node.items() if k not in _RESERVED}
        each_ref = node.get("each")

        if each_ref is not None:
            collection = self._resolve(each_ref, ctx, item)
            if not isinstance(collection, (list, tuple)):
                collection = []
            parts: list[str] = []
            for entry in collection:
                resolved = self._resolve_all(params, ctx, item=entry, widget=name)
                parts.append(self._render_template(name, ctx, resolved))
            return "\n".join(parts)

        resolved = self._resolve_all(params, ctx, item, widget=name)
        return self._render_template(name, ctx, resolved)

    def _render_template(
        self,
        widget: str,
        ctx: dict[str, Any],
        extra: dict[str, Any],
    ) -> str:
        # Strip protected keys so widget params cannot overwrite globals
        safe_extra = normalize_widget_props(widget, {
            k: v for k, v in extra.items() if k not in _PROTECTED_CTX
        })
        if self._strict:
            self._strict_check_widget_props(widget, safe_extra)
        try:
            tmpl = self._env.get_template(f"widgets/{widget}.html")
            return tmpl.render({**ctx, **safe_extra})
        except TemplateNotFound:
            if self._strict:
                raise LayoutConfigError(f"Unknown widget: {widget!r}") from None
            return (
                f'<div class="alert alert-error">'
                f'Unknown widget: {escape(str(widget))}'
                f'</div>'
            )

    def _strict_check_widget_props(self, widget: str, params: dict[str, Any]) -> None:
        contract = load_widget_registry().get(widget)
        if not contract or contract.get("status") != "verified":
            return
        alias_map = canonical_prop_names(contract)
        known = set(contract.get("props", {})) | set(alias_map.keys())
        for key in params:
            if key not in known:
                raise LayoutConfigError(f"Unknown prop {key!r} on widget {widget!r}")
        for prop, spec in contract.get("props", {}).items():
            if not spec.get("required"):
                continue
            if prop in params:
                continue
            if any(alias in params for alias in spec.get("aliases", [])):
                continue
            raise LayoutConfigError(f"Widget {widget!r} missing required prop {prop!r}")

    # ── containers ───────────────────────────────────────────────────────────

    def _container(self, node: dict, ctx: dict[str, Any], depth: int) -> str:
        t = node.get("type", "")

        if t not in _KNOWN_TYPES:
            if self._strict:
                raise LayoutConfigError(f"Unknown container type: {t!r}")
            return f'<!-- rdl: unknown container type "{escape(str(t))}" -->'

        if t == "section":
            return self._section(node, ctx, depth)
        if t == "split":
            return self._split(node, ctx, depth)

        inner = self.render(node.get("children", []), ctx, _depth=depth + 1)

        if t == "grid":
            raw_cols = node.get("columns", "auto")
            if self._strict and raw_cols not in _VALID_COLUMNS:
                raise LayoutConfigError(f"Invalid grid columns: {raw_cols!r}")
            cols     = raw_cols if raw_cols in _VALID_COLUMNS else "auto"
            css      = f"layout-grid-{cols}"
            gap      = node.get("gap")
            if gap is not None and gap not in _GAP_MODIFIERS:
                if self._strict:
                    raise LayoutConfigError(f"Invalid grid gap: {gap!r}")
            if gap in _GAP_MODIFIERS:
                return f'<div class="{css}" style="gap:{_GAP_CSS[gap]}">{inner}</div>'
            return f'<div class="{css}">{inner}</div>'

        # stack / row
        gap    = node.get("gap", "")
        if gap and gap not in _GAP_MODIFIERS:
            if self._strict:
                raise LayoutConfigError(f"Invalid {t} gap: {gap!r}")
        suffix = f"-{gap}" if gap in _GAP_MODIFIERS else ""
        css    = f"layout-{t}{suffix}"
        return f'<div class="{css}">{inner}</div>'

    def _section(self, node: dict, ctx: dict[str, Any], depth: int) -> str:
        heading = escape(str(node.get("heading", "")))
        desc    = escape(str(node.get("description", "")))
        inner   = self.render(node.get("children", []), ctx, _depth=depth + 1)
        parts   = ['<div class="component-section">']
        if heading:
            parts.append(f'<h2 class="section-label">{heading}</h2>')
        if desc:
            parts.append(f'<p class="section-desc">{desc}</p>')
        parts.append(inner)
        parts.append("</div>")
        return "\n".join(parts)

    def _split(self, node: dict, ctx: dict[str, Any], depth: int) -> str:
        primary_html   = self.render(node.get("primary",   []), ctx, _depth=depth + 1)
        secondary_html = self.render(node.get("secondary", []), ctx, _depth=depth + 1)
        # Wrap in Markup so Jinja2 autoescape does not double-encode the HTML
        pane_node = {
            "widget":          "split_pane",
            "primary":         Markup(primary_html),
            "secondary":       Markup(secondary_html),
            "initial_primary": node.get("initial", "50%"),
            "min_primary":     node.get("min", 120),
            "pane_id":         str(node.get("id", "rdl-0")),
        }
        return self._widget(pane_node, ctx, None)

    # ── resolution ───────────────────────────────────────────────────────────

    def _check_when(self, node: dict, ctx: dict[str, Any], item: Any) -> bool:
        cond = node.get("when")
        if cond is None:
            return True
        if isinstance(cond, bool):
            return cond
        return bool(self._resolve(cond, ctx, item))

    def _resolve(
        self,
        value: Any,
        ctx: dict[str, Any],
        item: Any,
        *,
        param_key: str | None = None,
        widget: str | None = None,
    ) -> Any:
        if not isinstance(value, str):
            return value

        m = _CTX_RE.match(value)
        if m:
            keys = m.group(1).split(".")
            if self._strict and not self._is_optional_prop(widget, param_key):
                return _deep_get_required(ctx, keys, ref=value)
            if self._strict:
                found, result = _deep_get_optional(ctx, keys)
                if not found:
                    return None
                return result
            return _deep_get(ctx, keys)

        # $item.key — only meaningful inside each:
        if item is not None:
            if value == _ITEM_BARE:
                return item
            m = _ITEM_RE.match(value)
            if m:
                keys = m.group(1).split(".")
                src  = item if isinstance(item, dict) else (
                    vars(item) if hasattr(item, "__dict__") else {}
                )
                if self._strict and not self._is_optional_prop(widget, param_key):
                    return _deep_get_required(src, keys, ref=value)
                if self._strict:
                    found, result = _deep_get_optional(src, keys)
                    if not found:
                        return None
                    return result
                return _deep_get(src, keys)

        # $item.* outside each: → empty string (permissive) or error (strict)
        if value.startswith("$item"):
            if self._strict:
                raise LayoutConfigError(f"{value!r} used outside each: block")
            return ""

        return value

    def _is_optional_prop(self, widget: str | None, param_key: str | None) -> bool:
        if not widget or not param_key:
            return False
        contract = load_widget_registry().get(widget)
        if not contract:
            return False
        spec = contract.get("props", {}).get(param_key)
        return bool(spec and not spec.get("required"))

    def _resolve_all(
        self,
        params: dict[str, Any],
        ctx: dict[str, Any],
        item: Any = None,
        *,
        widget: str | None = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str):
                out[k] = self._resolve(v, ctx, item, param_key=k, widget=widget)
            elif isinstance(v, list):
                out[k] = [
                    self._resolve_all(i, ctx, item, widget=widget) if isinstance(i, dict)
                    else self._resolve(i, ctx, item, widget=widget)
                    for i in v
                ]
            elif isinstance(v, dict):
                out[k] = self._resolve_all(v, ctx, item, widget=widget)
            else:
                out[k] = v
        return out


# ── helpers ───────────────────────────────────────────────────────────────────

def _deep_get(obj: Any, keys: list[str]) -> Any:
    for k in keys:
        if obj is None:
            return None
        obj = obj.get(k) if isinstance(obj, dict) else getattr(obj, k, None)
    return obj


def _deep_get_required(obj: Any, keys: list[str], *, ref: str) -> Any:
    """Like _deep_get but raises when any path segment is missing."""
    current = obj
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            raise LayoutConfigError(f"Unresolved reference {ref!r}")
        current = current[k]
    return current


def _deep_get_optional(obj: Any, keys: list[str]) -> tuple[bool, Any]:
    """Return (found, value). found is False when any segment is missing."""
    current = obj
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return False, None
        current = current[k]
    return True, current
