# RendUX — Session Handoff

**Date:** 2026-07-05  
**Host:** dev-01 (Linux, Python 3.12)  
**Path:** `~/dev/rendux` (NFS — `10.10.10.10:/mnt/huron/axym/dev`)  
**Branch:** `master` — `a1ea2c0` (1 commit ahead of `origin/master`)  
**Test count:** 95 passing (includes RDL linter + contract registry tests)

---

## dev-01 setup

```bash
cd ~/dev/rendux
export PATH="$HOME/.local/bin:$PATH"

# first-time (removes macOS .venv, creates Linux venv)
uv sync --group dev

# dev server
uv run uvicorn demo.main:app --reload --host 0.0.0.0 --port 8001

# tests
uv run pytest tests/ -q
```

Or run `~/rendux/setup-dev-01.sh` once TrueNAS permissions are fixed.

### Mac → dev-01 migration

The tree was copied from macOS with a Homebrew Python 3.14 `.venv` that does not work on Linux. Delete `.venv` and run `uv sync --group dev` to recreate on Python 3.12.

---

## What exists

RendUX is a config-driven UI shell runtime: FastAPI + Jinja2 + HTMX + PyYAML. No database. No CCC references.

**Scope (v1):** internal ops/admin dashboard shell — not a general app framework. Widget additions should serve monitoring, status, configuration, and operator workflows. The ops view (`/ops`) is the baseline RDL reference.

**Contracts:** JSON widget contracts in `contracts/widgets/` (machine); YAML in `config/views.yaml` (human authoring). Lint with `uv run python scripts/lint_rdl.py config/views.yaml`.

### Stack

```
demo/main.py              FastAPI app — wires views, themes, layout renderer
rendux/core/layout.py     RDL engine — YAML node tree → HTML
rendux/core/themes.py     ThemeService — YAML → CSS custom properties
rendux/views/service.py   ViewConfigService — loads views.yaml, resolves workspaces
rendux/templates/         38 widget templates + shell chrome + workspace wrappers
rendux/static/css/        themes.css (CSS vars), app.css (all widget styles)
rendux/static/js/         theme.js (window.RendUX.setTheme API)
config/views.yaml         View + layout declarations
config/themes.yaml        Theme declarations
tests/                    88 tests across 5 files
```

---

## RDL — RendUX Declarative Layout

YAML-native declarative UI. `workspace.layout:` in views.yaml is a list of nodes.

### Node types

```yaml
# Widget
- widget: stat_card
  label: "CPU"
  value: "$ctx.cpu"

# Container
- type: grid          # stack | row | grid | section | split
  columns: 4          # 1|2|3|4|auto
  gap: sm             # sm|lg
  children: [...]

# Shorthands
- divider: true
- heading: "Section"
  level: 2            # 1–6, defaults to 2

# Iteration
- widget: stat_card
  each: "$ctx.kpi"    # resolves list from context
  label: "$item.label"
  value: "$item.value"

# Conditional
- widget: alert
  when: "$ctx.has_alerts"
```

### Value sigils

| Sigil | Resolves to |
|---|---|
| `$ctx.key` | Dotted path into render context |
| `$ctx.a.b.c` | Nested dotted path |
| `$item.key` | Current item inside `each:` |
| `$item` | Bare item (plain value, not dict) |
| Anything else | Passed through as literal |

### Data flow

```
config/views.yaml  data:  →  view_data()  →  $ctx.*  (static, no Python)
route handler  view_ctx={}              →  $ctx.*  (dynamic, request-time)
templates.env.globals                  →  url_for, theme_list, etc (always)
```

### Security model

- `_PROTECTED_CTX` frozenset — widget params cannot overwrite `url_for`, `request`, `view_shell`, `theme_list`, `custom_theme_css`, `static_version`, `layout_html`
- Heading / section / description text is `escape()`d before insertion
- Split container wraps pre-rendered HTML in `Markup()` to prevent double-escaping
- Unknown container `type` → HTML comment (not raw text injection)
- Invalid `columns` → `"auto"` (not crash)
- Missing widget template → visible error placeholder `<div class="alert alert-error">`
- `MAX_DEPTH = 50` → `LayoutConfigError` if exceeded

---

## Widget library

**Tier 1 (12):** alert, avatar, badge, breadcrumb, button, card, divider, empty_state, panel, progress_bar, status_badge, tag  
**Tier 2 (11):** collapsible, form, item_list, kv_table, modal, pagination, skeleton, stat_card, status_grid, tabs, toast  
**Tier 3 (15):** code_block, command_palette, context_menu, data_table, drawer, file_drop, multi_select, nav_rail, popover, split_pane, stepper, tab_bar, theme_switcher, timeline, tooltip

---

## Theme system

`config/themes.yaml` → `ThemeService` → generates `html[data-theme="id"] { --rx-* }` CSS block per theme.

Anti-FOUC: inline script in `base.html` reads `localStorage["rx-theme"]` before first paint and sets `document.documentElement.dataset.theme`.

Public API: `window.RendUX.setTheme("light"|"dark"|"system")` — updates DOM, fires media query listener, persists to localStorage.

---

## Views

| View ID | Route | Workspace kind |
|---|---|---|
| `home` | `/` | template: `workspaces/home.html` |
| `components` | `/components` | template: `workspaces/components.html` |
| `ops` | `/ops` | **layout** (RDL — full declarative) |
| `about` | `/about` | template: `workspaces/about.html` |

The `ops` view is the primary RDL demo. It has a `data:` block in views.yaml with `kpi`, `service_health`, `recent_events`, `recent_changes`. The layout uses `$ctx.*` and `each: "$ctx.kpi"` / `$item.*` throughout.

---

## Key files for next session

| File | Why |
|---|---|
| `rendux/core/layout.py` | RDL engine — fully hardened, read this before touching |
| `rendux/views/service.py` | `WorkspaceDescriptor`, `resolve_workspace()`, `view_data()` |
| `demo/main.py` | `_render_view()` — how layout/template dispatch works |
| `config/views.yaml` | Ops view is the living RDL example |
| `tests/test_layout.py` | 59 tests — run these when touching the engine |

---

## Commit history (this arc)

```
a1ea2c0  Fix: RDL engine hardening — security, validation, structural revisions, $ctx data injection
0afd5fe  Add: RendUX Declarative Layout (RDL) engine and Ops demo view
3339d8c  Add: Tier 3 widgets batch 2 (6 widgets)
87f9b29  Add: Tier 3 widget library (8 widgets)
f363b65  Add: light/dark/system theme with custom theme support
2926705  Add: Tier 2 widget library — 7 HTMX-assisted widgets
c0dc2f4  Add: Tier 1 widget library — 10 new widgets + layout helpers
a292ccd  Add: four core widgets with demo data across all views
290d85f  Init: RendUX — config-driven UI shell runtime with multi-view demo
```

---

## Possible next directions (no commitment)

1. **Dynamic view_ctx** — poll a live data source (health check endpoints, metrics) and inject via `view_ctx={}` in the route handler. The plumbing is already there.
2. **Components view via RDL** — replace the hardcoded `components.html` template with a layout that renders the widget showcase declaratively.
3. **RDL linter** — add `scripts/lint_views.py` to validate layout node trees (unknown widget names, unknown container types, required params).
4. **Split / drawer layouts** — the `split_pane` and `drawer` widgets exist but no top-level layout uses them yet.
5. **HTMX partials via RDL** — `each:` list refreshed by a polling HTMX partial (server push pattern).
