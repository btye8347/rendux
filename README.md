# RendUX

**Config-driven UI shell for ops/admin apps** — declare layouts in YAML (RDL), render with FastAPI + Jinja2 + HTMX.

| | |
|---|---|
| **Version** | `0.1.0b1` (beta) |
| **Python** | ≥ 3.12 |
| **Install** | Private git dependency (not on PyPI) |
| **License** | Proprietary — see [LICENSE](LICENSE) |

```bash
uv add "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

---

## Why RendUX

Internal tools keep re-implementing the same dashboards, tables, and forms. RendUX separates:

1. **RDL** — a portable layout grammar humans and LLMs can author
2. **Widget contracts** — machine-checkable props (lint + strict render)
3. **Reference runtime** — Python/FastAPI/Jinja today; not the long-term moat

You keep domain logic and routes. RendUX renders the shell and widgets from config.

---

## Features (0.1 beta)

- **RDL layouts** — `grid` / `stack` / `section` / `split`, `$ctx` / `$item`, `each:`
- **19 verified widgets** — ops + admin set (`stat_card`, `data_table`, `form`, `modal`, …)
- **Strict compile loop** — linter + strict renderer; agent-friendly JSON errors
- **Host integration API** — `configure_app` / `render_view`
- **Themes** — light/dark/system + YAML custom themes
- **LLM pack** — system prompt, verified catalog, recipes, adversarial eval (passed)

---

## Install in your application

Requires SSH (or HTTPS token) access to this private repo. **Pin the tag.**

### uv

```bash
uv add "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

### pip / pyproject.toml

```toml
dependencies = [
  "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1",
]
```

```bash
pip install "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

Verify:

```bash
python -c "import rendux; print(rendux.__version__, rendux.contracts_dir())"
```

**Full host-app guide → [docs/CONSUMING.md](docs/CONSUMING.md)**  
**Copy-paste skeleton → [examples/consumer/](examples/consumer/)**

---

## Quick start (host app)

```python
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from rendux.integration import configure_app, render_view

app = FastAPI(title="My Ops App")
configure_app(
    app,
    views_yaml=Path("config/views.yaml"),
    themes_yaml=Path("config/themes.yaml"),  # optional
)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_view(request, "home", "Home")
```

Example `config/views.yaml`:

```yaml
version: 0.1.0
shell:
  id: default
  template: chrome/shells/default.html
views:
  home:
    label: Home
    route: /
    include: home_layout.yaml   # data: + workspace.layout:
```

---

## What the package provides

| API / path | Purpose |
|---|---|
| `rendux.integration.configure_app` | Wire services, static, views API |
| `rendux.integration.render_view` | Render a view (layout or template) |
| `rendux.templates_dir()` | Packaged Jinja templates |
| `rendux.static_dir()` | CSS / JS / HTMX vendor |
| `rendux.contracts_dir()` | Widget JSON contracts + grammar |
| `rendux.catalog_verified_path()` | Closed vocabulary for LLMs |
| `rendux.core.agent_compile.compile_fragment` | Lint + strict-render a YAML fragment |

**You supply:** `views.yaml`, optional themes, routes, auth, and `view_ctx` data.

---

## Demo (this repository)

```bash
git clone git@github.com:btye8347/rendux.git
cd rendux
uv sync --group dev
uv run uvicorn demo.main:app --reload --host 0.0.0.0 --port 8001
```

| Route | What it shows |
|---|---|
| `/` | Home |
| `/ops` | Ops dashboard — RDL + live HTMX poll |
| `/services` | Admin catalog use case |
| `/components` | Widget showcase |
| `/about` | About |

---

## Documentation

| Doc | Audience |
|---|---|
| [docs/CONSUMING.md](docs/CONSUMING.md) | **Using RendUX as a dependency** |
| [docs/rdl-spec-v0.1.md](docs/rdl-spec-v0.1.md) | RDL grammar |
| [docs/agent/SYSTEM.md](docs/agent/SYSTEM.md) | LLM system prompt |
| [docs/agent/CHEATSHEET.md](docs/agent/CHEATSHEET.md) | Agent quick reference |
| [docs/agent/RECIPES.md](docs/agent/RECIPES.md) | Copyable layout patterns |
| [docs/agent/ADVERSARIAL_TEST_PLAN.md](docs/agent/ADVERSARIAL_TEST_PLAN.md) | Cold-start validation |
| [docs/RELEASE_0.1.md](docs/RELEASE_0.1.md) | 0.1 beta release notes |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [LLM Agent Compatibility Plan.md](LLM%20Agent%20Compatibility%20Plan.md) | Agent pack roadmap |
| [RDL Portability & Governance Plan.md](RDL%20Portability%20%26%20Governance%20Plan.md) | Grammar / contracts roadmap |
| [HANDOFF.md](HANDOFF.md) | Dev environment notes |

---

## LLM / agent authoring

RendUX is designed so an LLM can emit RDL without reading Jinja:

1. Give the model `docs/agent/SYSTEM.md` + `contracts/catalog.verified.json`
2. Optionally add a recipe from `examples/agent/`
3. Validate output:

```bash
uv run python scripts/agent_compile.py path/to/fragment.yaml --pretty
```

Cold-start adversarial suite scored **18/18** — see `docs/agent/eval/`.

---

## Develop (contributors)

```bash
uv sync --group dev
uv run pytest tests/ -q
uv run python scripts/lint_rdl.py config/views.yaml
uv run python scripts/vibe_test.py
uv build   # wheel includes bundled contracts
```

CI runs lint, pytest, vibe fixtures, strict ops smoke, and wheel build.

### Repository layout

```
rendux/                 # Installable package
  integration.py        # configure_app / render_view
  paths.py              # templates / static / contracts locations
  core/                 # RDL engine, contracts, lint, agent_compile
  templates/            # Widgets + chrome
  static/               # CSS / JS
contracts/              # Widget JSON (bundled into wheel)
config/                 # Demo views + themes
demo/                   # Reference FastAPI app
docs/                   # Spec, consuming guide, agent pack
examples/
  agent/                # Few-shot RDL fragments
  consumer/             # Minimal host-app skeleton
scripts/                # lint_rdl, agent_compile, catalog builder
tests/
```

---

## Versioning & status

- **`0.1.0b1`** — first private beta; API may still shift before `0.1.0`
- Pin **`v0.1.0b1`** (or a commit SHA) in host apps — do not float on `master` unless you accept breakage
- **19 / 38** widgets verified; unverified stubs are skipped by prop lint until audited
- Not published to PyPI (`Private :: Do Not Upload`)

---

## License

Proprietary and confidential. See [LICENSE](LICENSE). Do not redistribute outside authorized use.
