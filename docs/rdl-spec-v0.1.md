# RDL Specification v0.1

**RendUX Declarative Layout** — a stack-agnostic grammar for describing dashboard UI as a tree of nodes.

- **Grammar version:** `0.1.0` (see `config/views.yaml` top-level `version:` and `contracts/rdl-grammar.json`)
- **Human authoring:** YAML (`config/views.yaml`)
- **Machine contracts:** JSON (`contracts/widgets/*.json`, `contracts/profiles/*.json`)
- **Reference renderer:** Python + Jinja2 (`rendux/core/layout.py`)
- **Linter:** `scripts/lint_rdl.py`

This document describes portable behavior. A conformant renderer must produce equivalent **resolved widget invocations** (widget name + resolved param dict) regardless of output format (HTML, React, etc.).

---

## 1. Overview

An RDL **layout** is a list of **nodes** evaluated top-to-bottom. Each node may carry an optional `when:` guard. Conformant renderers walk the tree, resolve sigil values against a **context** dict, and dispatch widget nodes to a widget implementation.

RDL does **not** define view routing, shell chrome, or themes — only the `workspace.layout` tree inside a view.

**Scope (v0.1):** internal ops/admin dashboard patterns. Baseline verified widgets: `stat_card`, `status_grid`, `timeline`, `item_list`, `alert`, `progress_bar`. See `contracts/widgets/` for the full registry.

---

## 2. Node types

### 2.1 Widget node

```yaml
widget: <name>              # required — must exist in widget registry
<param>: <value>            # widget params (see contracts/widgets/<name>.json)
when: <cond>                # optional — skip node if falsy
each: "$ctx.list"           # optional — repeat for each collection item
                            # also accepts an inline YAML list
```

Reserved keys on widget nodes: `widget`, `when`, `each`. All other keys are widget params.

### 2.2 Container node

```yaml
type: stack | row | grid | section | split
when: <cond>                # optional
children: [<node>, ...]      # stack, row, grid, section
```

**Spacing (all containers that wrap children):**

```yaml
gap: none | xs | sm | md | lg | xl    # inward — CSS gap between children
space: none | xs | sm | md | lg | xl  # outward — margin-block-end vs siblings
```

Defaults come from CSS tokens (`--rx-gap-default`, `--rx-stack-gap`, `--rx-section-gap`, `--rx-section-space`). Host themes may override the scale.

**Grid extras:**

```yaml
columns: 1 | 2 | 3 | 4 | auto   # default: auto
gap: …                            # optional (see spacing)
space: …                          # optional
```

**Stack / row extras:**

```yaml
gap: …                            # optional
space: …                          # optional
```

**Section extras:**

```yaml
heading: "Section title"
description: "Subtitle text"
gap: …                            # between heading/desc/children
space: …                          # after the section
children: [<node>, ...]
```

**Split extras** (named slots, not `children`):

```yaml
primary: [<node>, ...]
secondary: [<node>, ...]
initial: "40%"                # optional — default "50%"
min: 120                      # optional — min primary width px, default 120
id: "pane-id"                 # optional
```

### 2.3 Shorthand nodes

```yaml
- divider: true

- heading: "Section text"
  level: 2                    # optional, 1–6, default 2
```

---

## 3. Value types and sigils

| Form | Resolves to |
|---|---|
| `$ctx.key` | Dotted path into render context |
| `$ctx.a.b.c` | Nested path |
| `$item.key` | Field on current `each:` item (dotted paths supported) |
| `$item` (bare) | Entire current item when it is a plain value |
| Literal | Passed through unchanged (string, int, bool, list, dict) |

**`when:` values:** `$ctx.*` reference, boolean literal, or any truthy/falsy resolved value. Plain non-sigil strings are always truthy.

**`$item.*` outside `each:`:** resolves to empty string `""` (not an error in permissive mode).

**Lists of dicts** in params are recursively resolved.

---

## 4. Context and data flow

```
config/views.yaml  data:     →  static $ctx.* at render time
route handler      view_ctx:  →  merged into context per request
template globals              →  url_for, theme_list, etc. (renderer-specific)
```

Protected keys that widget params must **never** overwrite:

`url_for`, `request`, `view_shell`, `layout_html`, `theme_list`, `custom_theme_css`, `static_version`

---

## 5. Widget contracts

Each widget has a JSON contract at `contracts/widgets/<name>.json`:

```json
{
  "name": "stat_card",
  "status": "verified",
  "interaction": { "profile": "static" },
  "accepts_each": true,
  "props": {
    "label": { "type": "string", "required": true, "aliases": ["title"] },
    "value": { "type": "string", "required": true }
  }
}
```

### 5.1 Naming conventions

| Role | Prop name | Example widgets |
|---|---|---|
| Section heading | `title` | `status_grid`, `item_list` |
| Scalar descriptor | `label` | `stat_card`, `progress_bar` |
| Scalar value | `value` | `stat_card`, `progress_bar` |
| Collection | `items` / `events` | per-widget `item_schema` |

Data in `$ctx` may use domain field names; RDL maps explicitly (`label: "$item.label"`).

**Aliases:** deprecated prop names (e.g. `title` on `stat_card`) should warn at lint time; conformant renderers normalize to canonical names before dispatch.

### 5.2 Item schemas

Collection widgets declare `item_schema` for elements inside `items` or `events`:

```json
"item_schema": {
  "required": { "label": { "type": "string" }, "status": { "type": "enum", "enum": ["ok", "warn"] } },
  "optional": { "detail": { "type": "string" } }
}
```

### 5.3 Interaction profiles

Declared in `contracts/profiles/`. Factored now; fully enforced by linter as widgets are verified.

| Profile | Required props | Purpose |
|---|---|---|
| `static` | — | No HTMX/DOM scripting |
| `htmx-nav` | `hx_get` | HTMX GET navigation |
| `htmx-form` | `hx_post` | HTMX form POST |
| `htmx-partial` | `hx_get`, `hx_target` | Partial swap |
| `dom-dialog` | `id`, `title` | Native dialog |

### 5.4 Contract status

- **`verified`** — linter enforces props, enums, item schemas, interaction profile
- **`unverified`** — widget name must exist; prop checks skipped until audited

---

## 6. Resolution algorithm

For each node in order:

1. If `when:` present and resolves falsy → skip node
2. If widget node with `each:`:
   - Resolve `each` to a list (non-list → empty list)
   - For each item: resolve all params with that item as `$item` context → dispatch widget
3. If widget node without `each:`: resolve params → dispatch widget
4. If container: render children/slots recursively, wrap per container type
5. If shorthand: emit divider or heading

**Nesting limit:** `MAX_DEPTH = 50`. Exceeding raises `LayoutConfigError`.

---

## 7. Security model

- Widget params cannot overwrite protected context keys
- Container `type` and `columns` are allowlisted; unknown values must not inject raw user text
- `heading` and `description` text must be HTML-escaped before insertion
- Pre-rendered HTML in split containers must not be double-escaped
- Missing widget implementation: visible error placeholder (permissive) or `LayoutConfigError` (strict)

---

## 8. Linting

```bash
uv run python scripts/lint_rdl.py config/views.yaml          # strict (CI)
uv run python scripts/lint_rdl.py config/views.yaml --permissive
```

Strict mode errors on: unknown widget, missing required prop, unknown prop (verified widgets), invalid enum, unresolved static `$ctx.*` path, invalid container config, missing interaction props.

Warnings: deprecated aliases, `$item.*` outside `each:`, unknown item fields.

Notes: unverified widget (props skipped), dynamic `$ctx` (no static `data:` block).

---

## 9. Conformance testing

Portable assertions live in `tests/conformance/`. Fixtures define:

- input layout tree
- input context dict
- expected widget invocations (name + resolved params)

Conformance tests assert the **grammar layer** (dispatch + resolve), not HTML output.

- `tests/conformance/test_ops_baseline.py` — excerpt fixtures
- `tests/conformance/test_ops_full_layout.py` — full ops layout from `config/views.yaml` (12 dispatches; collect/render parity)

---

## 10. Example (ops KPI row)

```yaml
- type: grid
  columns: 4
  children:
    - widget: stat_card
      each: "$ctx.kpi"
      label: "$item.label"
      value: "$item.value"
      status: "$item.status"
      trend: "$item.trend"
      subtitle: "$item.subtitle"
```

With context `{"kpi": [{"label": "CPU", "value": "82%", "status": "ok"}]}`, a conformant renderer produces one invocation:

```json
{ "widget": "stat_card", "params": { "label": "CPU", "value": "82%", "status": "ok" } }
```

---

## Appendix: version history

| Version | Changes |
|---|---|
| 0.1.0 | Initial spec: node types, sigils, contracts, linter, ops baseline widgets |
