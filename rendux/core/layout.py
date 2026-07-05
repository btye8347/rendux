"""
RendUX Declarative Layout (RDL) renderer — v0.2

Language spec
=============

A layout is a list of *nodes*. Nodes are evaluated top-to-bottom and rendered
into an HTML string. Every node may carry an optional ``when:`` guard.

Node types
----------

Widget node::

    widget: <name>              # required — resolves to widgets/<name>.html
    <param>: <value>            # flat widget params (see Value types below)
    when:  <cond>               # optional — suppress node if falsy
    each:  "$ctx.list"          # optional — repeat for each item in collection
                                #            also accepts an inline YAML list

Container node::

    type: stack | row | grid | section | split
    children: [<node>, ...]     # required for stack / row / grid
    when: <cond>

    # grid extras:
    columns: 1 | 2 | 3 | 4 | auto   # default: auto; other values are errors
    gap: sm | lg                      # emits inline style="gap:..." on the div

    # stack / row extras:
    gap: sm | lg                      # appended to CSS class: layout-stack-sm

    # section extras:
    heading: "Section title"
    description: "Subtitle text"
    children: [<node>, ...]

    # split extras — uses named slots, not children:
    primary:   [<node>, ...]    # left / top panel
    secondary: [<node>, ...]    # right / bottom panel
    initial: "40%"              # initial primary width
    min: 120                    # minimum primary width in px

Shorthand nodes::

    { divider: true }
    { heading: "Text", level: 2 }    # level defaults to 2; clamped 1–6

Value types
-----------

``"$ctx.key"``
    Resolved from the render context dict. Supports dotted paths:
    ``"$ctx.stats.cpu"`` → ``ctx["stats"]["cpu"]``.

``"$item.key"``
    Current iteration item inside an ``each:`` loop. Dotted paths supported.
    Outside an ``each:`` block, ``$item.*`` resolves to an empty string.

``"$item"`` (bare)
    The entire current item when it is a plain value (not a dict).

Literal values
    Strings, ints, booleans, lists, and dicts are passed through unchanged.
    A list of dicts is recursively resolved.

``when:`` values
    Accepts a ``$ctx.*`` reference, a YAML boolean (``true`` / ``false``),
    or any Python-truthy/falsy value. Plain non-sigil strings are always
    truthy — use ``$ctx.*`` or a boolean literal instead.

Nesting limit
-------------
Layout trees may not exceed ``MAX_DEPTH`` (50) levels. Deeper trees raise
``LayoutConfigError``. This prevents runaway recursion from malformed YAML.

Security model
--------------
* Widget params are prevented from overwriting protected context keys
  (``url_for``, ``request``, ``view_shell``, and theme/static globals).
* Container ``type`` and ``columns`` values are allowlisted; unknown values
  emit an HTML comment rather than injecting raw text.
* ``heading`` and ``description`` text is HTML-escaped before insertion.
* Pre-rendered HTML strings passed to the ``split`` container are wrapped in
  ``markupsafe.Markup`` so Jinja2 does not double-escape them.
* Missing widget templates render a visible error placeholder rather than
  raising a 500.
"""

from __future__ import annotations

import re
from typing import Any

from jinja2 import Environment, TemplateNotFound
from markupsafe import Markup, escape

from rendux.core.contracts import normalize_widget_props

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


# ── renderer ─────────────────────────────────────────────────────────────────

class LayoutRenderer:
    """Walks an RDL node tree and renders it to an HTML string."""

    def __init__(self, env: Environment) -> None:
        self._env = env

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
                resolved = self._resolve_all(params, ctx, item=entry)
                parts.append(self._render_template(name, ctx, resolved))
            return "\n".join(parts)

        resolved = self._resolve_all(params, ctx, item)
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
        try:
            tmpl = self._env.get_template(f"widgets/{widget}.html")
            return tmpl.render({**ctx, **safe_extra})
        except TemplateNotFound:
            return (
                f'<div class="alert alert-error">'
                f'Unknown widget: {escape(str(widget))}'
                f'</div>'
            )

    # ── containers ───────────────────────────────────────────────────────────

    def _container(self, node: dict, ctx: dict[str, Any], depth: int) -> str:
        t = node.get("type", "")

        if t not in _KNOWN_TYPES:
            return f'<!-- rdl: unknown container type "{escape(str(t))}" -->'

        if t == "section":
            return self._section(node, ctx, depth)
        if t == "split":
            return self._split(node, ctx, depth)

        inner = self.render(node.get("children", []), ctx, _depth=depth + 1)

        if t == "grid":
            raw_cols = node.get("columns", "auto")
            cols     = raw_cols if raw_cols in _VALID_COLUMNS else "auto"
            css      = f"layout-grid-{cols}"
            gap      = node.get("gap")
            if gap in _GAP_MODIFIERS:
                return f'<div class="{css}" style="gap:{_GAP_CSS[gap]}">{inner}</div>'
            return f'<div class="{css}">{inner}</div>'

        # stack / row
        gap    = node.get("gap", "")
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

    def _resolve(self, value: Any, ctx: dict[str, Any], item: Any) -> Any:
        if not isinstance(value, str):
            return value

        m = _CTX_RE.match(value)
        if m:
            return _deep_get(ctx, m.group(1).split("."))

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
                return _deep_get(src, keys)

        # $item.* outside each: → empty string (not the raw sigil)
        if value.startswith("$item"):
            return ""

        return value

    def _resolve_all(
        self,
        params: dict[str, Any],
        ctx: dict[str, Any],
        item: Any = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in params.items():
            if isinstance(v, str):
                out[k] = self._resolve(v, ctx, item)
            elif isinstance(v, list):
                out[k] = [
                    self._resolve_all(i, ctx, item) if isinstance(i, dict)
                    else self._resolve(i, ctx, item)
                    for i in v
                ]
            elif isinstance(v, dict):
                out[k] = self._resolve_all(v, ctx, item)
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
