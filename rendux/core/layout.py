"""
RendUX Declarative Layout (RDL) renderer.

Spec summary
------------
A layout is a list of *nodes*. Each node is one of:

  Widget node
    widget: <name>          # required — resolves to widgets/<name>.html
    <param>: <value>        # flat widget params
    when:  <cond>           # optional — suppress if falsy
    each:  "$ctx.list"      # optional — repeat for each item in collection

  Container node
    type: stack | row | grid | section | split
    children: [<node>, ...]
    # grid only:
    columns: 2 | 3 | 4 | auto
    # stack / row only:
    gap: sm | lg            # default gap omitted (uses CSS class default)
    # section extras:
    heading: "Section title"
    description: "Subtitle"
    # split extras:
    primary:   [<node>, ...]
    secondary: [<node>, ...]
    initial: "40%"
    min: 120

  Shorthand nodes
    divider: true
    heading: "Text"
    level: 2 | 3            # for heading shorthand

Value resolution
----------------
  "$ctx.key"       → context["key"]
  "$ctx.a.b.c"     → nested lookup through dicts / attrs
  "$item.key"      → current item in an `each` loop (dict or attr)
  anything else    → literal value, passed through unchanged

Lists and dicts inside params are recursively resolved.
"""

from __future__ import annotations

import re
from typing import Any

from jinja2 import Environment


_CTX_RE  = re.compile(r"^\$ctx\.(.+)$")
_ITEM_RE = re.compile(r"^\$item\.(.+)$")

_RESERVED = frozenset({"widget", "when", "each"})

_GAP_MODIFIERS = frozenset({"sm", "lg"})


class LayoutRenderer:
    """Walks a RDL node tree and renders it to an HTML string."""

    def __init__(self, env: Environment) -> None:
        self._env = env

    # ── public ──────────────────────────────────────────────────────────────

    def render(self, nodes: list[Any], ctx: dict[str, Any]) -> str:
        """Render a list of RDL nodes into an HTML string."""
        parts: list[str] = []
        for node in nodes or []:
            html = self._dispatch(node, ctx, item=None)
            if html:
                parts.append(html)
        return "\n".join(parts)

    # ── dispatch ─────────────────────────────────────────────────────────────

    def _dispatch(self, node: Any, ctx: dict[str, Any], item: Any) -> str:
        if not isinstance(node, dict):
            return ""
        if not self._check_when(node, ctx, item):
            return ""
        if "widget" in node:
            return self._widget(node, ctx, item)
        if "type" in node:
            return self._container(node, ctx)
        if node.get("divider"):
            return self._render_template("divider", ctx, {})
        if "heading" in node:
            level = min(max(int(node.get("level", 2)), 1), 6)
            text  = str(node["heading"])
            return f'<h{level} class="workspace-heading">{text}</h{level}>'
        return ""

    # ── widget ───────────────────────────────────────────────────────────────

    def _widget(self, node: dict, ctx: dict[str, Any], item: Any) -> str:
        name  = node["widget"]
        params = {k: v for k, v in node.items() if k not in _RESERVED}

        each_ref = node.get("each")
        if each_ref is not None:
            collection = self._resolve(each_ref, ctx, item)
            parts: list[str] = []
            for entry in (collection or []):
                resolved = self._resolve_all(params, ctx, item=entry)
                parts.append(self._render_template(name, ctx, resolved))
            return "\n".join(parts)

        resolved = self._resolve_all(params, ctx, item)
        return self._render_template(name, ctx, resolved)

    def _render_template(
        self, widget: str, ctx: dict[str, Any], extra: dict[str, Any]
    ) -> str:
        tmpl = self._env.get_template(f"widgets/{widget}.html")
        return tmpl.render({**ctx, **extra})

    # ── containers ───────────────────────────────────────────────────────────

    def _container(self, node: dict, ctx: dict[str, Any]) -> str:
        t = node["type"]

        if t == "section":
            return self._section(node, ctx)
        if t == "split":
            return self._split(node, ctx)

        inner = self.render(node.get("children", []), ctx)

        if t == "grid":
            cols = node.get("columns", "auto")
            css  = f"layout-grid-{cols}"
        elif t in ("stack", "row"):
            gap    = node.get("gap", "")
            suffix = f"-{gap}" if gap in _GAP_MODIFIERS else ""
            css    = f"layout-{t}{suffix}"
        else:
            css = f"layout-{t}"

        return f'<div class="{css}">{inner}</div>'

    def _section(self, node: dict, ctx: dict[str, Any]) -> str:
        heading = node.get("heading", "")
        desc    = node.get("description", "")
        inner   = self.render(node.get("children", []), ctx)
        parts   = ['<div class="component-section">']
        if heading:
            parts.append(f'<h2 class="section-label">{heading}</h2>')
        if desc:
            parts.append(f'<p class="section-desc">{desc}</p>')
        parts.append(inner)
        parts.append("</div>")
        return "\n".join(parts)

    def _split(self, node: dict, ctx: dict[str, Any]) -> str:
        primary_html   = self.render(node.get("primary",   []), ctx)
        secondary_html = self.render(node.get("secondary", []), ctx)
        pane_node = {
            "widget":          "split_pane",
            "primary":         primary_html,
            "secondary":       secondary_html,
            "initial_primary": node.get("initial", "50%"),
            "min_primary":     node.get("min", 120),
            "pane_id":         str(node.get("id", "rdl-0")),
        }
        return self._widget(pane_node, ctx, None)

    # ── conditionals & resolution ────────────────────────────────────────────

    def _check_when(self, node: dict, ctx: dict[str, Any], item: Any) -> bool:
        cond = node.get("when")
        if cond is None:
            return True
        return bool(self._resolve(cond, ctx, item))

    def _resolve(self, value: Any, ctx: dict[str, Any], item: Any) -> Any:
        if not isinstance(value, str):
            return value
        m = _CTX_RE.match(value)
        if m:
            return _deep_get(ctx, m.group(1).split("."))
        if item is not None:
            m = _ITEM_RE.match(value)
            if m:
                keys = m.group(1).split(".")
                src  = item if isinstance(item, dict) else vars(item) if hasattr(item, "__dict__") else {}
                return _deep_get(src, keys)
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


# ── helpers ──────────────────────────────────────────────────────────────────

def _deep_get(obj: Any, keys: list[str]) -> Any:
    for k in keys:
        if obj is None:
            return None
        obj = obj.get(k) if isinstance(obj, dict) else getattr(obj, k, None)
    return obj
