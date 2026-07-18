# Consuming RendUX 0.1 (beta) in your application

This guide is for **host apps** that depend on the private `rendux` package.
You do not need to clone this repo to run production — only to develop RendUX itself.

---

## 1. Add the dependency

Pin a release tag:

```toml
# pyproject.toml
dependencies = [
  "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1",
]
```

```bash
uv sync
# or
pip install -e .   # in your app, after adding the dep
```

Confirm import:

```bash
python -c "import rendux; print(rendux.__version__, rendux.contracts_dir())"
```

---

## 2. Responsibilities

| You (host) own | RendUX owns |
|---|---|
| `views.yaml` (+ includes) | Widget templates + contracts |
| Themes YAML (optional) | Shell chrome + static assets |
| Routes / auth / business logic | RDL renderer + linter |
| Request-time `view_ctx` data | Verified widget vocabulary |

RendUX does **not** include your domain models or APIs. It renders UI from config + context.

---

## 3. Minimal FastAPI wiring

```python
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from rendux.integration import configure_app, render_view

ROOT = Path(__file__).parent
app = FastAPI(title="My Ops App")

configure_app(
    app,
    views_yaml=ROOT / "config" / "views.yaml",
    themes_yaml=ROOT / "config" / "themes.yaml",  # optional
    # strict=True,  # or set RENDUX_STRICT=1
)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_view(request, "home", "Home")

@app.get("/inventory", response_class=HTMLResponse)
def inventory(request: Request):
    # Dynamic data overrides YAML data: block
    live = {"summary": [{"label": "Items", "value": "12", "status": "ok"}]}
    return render_view(request, "inventory", "Inventory", view_ctx=live)
```

`configure_app` will:

1. Register `ViewConfigService`, `LayoutRenderer`, optional `ThemeService`
2. Mount RendUX static files at `/static`
3. Include the views JSON API router (disable with `include_views_api=False`)

---

## 4. Host config layout

```
your-app/
  config/
    views.yaml          # required
    themes.yaml         # optional
    inventory.yaml      # optional include fragment
  app/
    main.py
```

### views.yaml skeleton

```yaml
version: 0.1.0

shell:
  id: default
  template: chrome/shells/default.html

views:
  home:
    label: Home
    route: /
    workspace:
      template: workspaces/home.html   # only if you ship a custom template

  inventory:
    label: Inventory
    route: /inventory
    include: inventory.yaml            # data: + workspace.layout:
```

Use **`include:`** for RDL pages (recommended). Copy patterns from:

- This repo’s `config/services_admin.yaml`
- `examples/agent/service_admin.yaml`

---

## 5. RDL fragment shape

```yaml
data:
  summary:
    - {label: Items, value: "12", status: ok}
workspace:
  layout:
    - type: grid
      columns: 4
      children:
        - widget: stat_card
          each: "$ctx.summary"
          label: "$item.label"
          value: "$item.value"
          status: "$item.status"
```

**Rules for 0.1:**

- Prefer widgets in `contracts/catalog.verified.json` (19 verified)
- Unknown props on verified widgets fail under strict lint/render
- Containers: `stack | row | grid | section | split`

Validate in CI:

```bash
# From an editable checkout of rendux, or copy the script:
python -c "
from pathlib import Path
from rendux.core.lint_rdl import lint_views_file
errs = [i for i in lint_views_file(Path('config/views.yaml'), strict=True) if i.level=='error']
assert not errs, errs
"
```

Or compile a fragment:

```python
from rendux.core.agent_compile import compile_fragment
import yaml
report = compile_fragment(yaml.safe_load(Path("config/inventory.yaml").read_text()))
assert report["ok"], report["errors"]
```

---

## 6. Templates override

Host templates can override RendUX by adding directories **after** the package templates:

```python
from rendux.integration import create_templates, configure_app

templates = create_templates(Path("app/templates"))  # host second
configure_app(app, views_yaml=..., templates=templates)
```

Jinja searches RendUX templates first, then yours — put overrides in your dir with the same relative path (e.g. `chrome/shells/default.html`).

---

## 7. LLM / agent usage in your app

Give the model:

1. `docs/agent/SYSTEM.md` (from this repo, or vendor a copy)
2. Contents of `rendux.catalog_verified_path()` (JSON)
3. Your **context schema** (what `data:` / `view_ctx` keys you provide)

Then run `compile_fragment` on the model’s YAML before writing it into `config/`.

See `docs/agent/ADVERSARIAL_TEST_PLAN.md` for cold-start validation methodology.

---

## 8. Environment

| Variable | Effect |
|---|---|
| `RENDUX_STRICT=1` | Fail render on unknown widgets/props / missing `$ctx` paths |

Recommended **on** in CI and staging; optional in production until layouts stabilize.

---

## 9. Example consumer tree

See `examples/consumer/` in this repository for a tiny host app layout you can copy.

---

## 10. Support boundaries (0.1 beta)

**Supported**

- FastAPI host apps on Python 3.12+
- RDL views with verified widgets
- Private git install + pinned tag

**Not yet**

- PyPI publish
- Stable public semver guarantees across minors
- Alternate renderers (React, etc.)
- Full 38-widget verified surface (19 verified in 0.1)

Report issues in the private GitHub repo.
