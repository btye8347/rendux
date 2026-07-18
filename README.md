# RendUX

**Version:** 0.1.0b1 (beta)  
**Status:** Private package — usable as a dependency in your own apps; not published to PyPI.

RendUX is a **config-driven UI shell** for internal ops/admin applications:

- **RDL** — YAML declarative layouts (`workspace.layout`)
- **Widget contracts** — JSON schemas + linter + strict render
- **Reference stack** — FastAPI + Jinja2 + HTMX

The moat is the **grammar and contracts**, not the Python runtime. Agents and humans author RDL; the library compiles and renders it.

---

## Install (private git dependency)

Requires GitHub access to `btye8347/rendux` (SSH key or token).

### uv

```bash
uv add "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

### pip

```bash
pip install "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

### pyproject.toml

```toml
dependencies = [
  "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1",
]
```

Pin a tag (`v0.1.0b1`) or commit SHA for reproducible builds. Track `master` only if you accept breakage.

---

## Quick start (host app)

```python
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from rendux.integration import configure_app, render_view

app = FastAPI()
configure_app(
    app,
    views_yaml=Path("config/views.yaml"),
    themes_yaml=Path("config/themes.yaml"),  # optional
)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return render_view(request, "dashboard", "Dashboard")
```

Your `config/views.yaml` declares views and RDL layouts (or `include:` fragments).  
Full guide: **[docs/CONSUMING.md](docs/CONSUMING.md)**.

---

## What ships in the package

| Asset | Location |
|---|---|
| Python API | `rendux.*` |
| Jinja widgets / chrome | `rendux.templates_dir()` |
| Static CSS/JS | `rendux.static_dir()` |
| Widget contracts | `rendux.contracts_dir()` |
| LLM catalog | `rendux.catalog_verified_path()` |

Host apps supply **their own** `views.yaml`, `themes.yaml`, and domain data (`view_ctx`).

---

## Demo (this repo)

```bash
cd ~/dev/rendux
uv sync --group dev
uv run uvicorn demo.main:app --reload --host 0.0.0.0 --port 8001
```

| Route | Purpose |
|---|---|
| `/ops` | Live ops dashboard (RDL + polling) |
| `/services` | Admin app use-case demo |
| `/components` | Widget showcase |

---

## Agent / LLM authoring

Cold-start prompt pack and compile loop:

- `docs/agent/SYSTEM.md`
- `contracts/catalog.verified.json` (19 verified widgets)
- `uv run python scripts/agent_compile.py path/to/fragment.yaml`

Plans: `LLM Agent Compatibility Plan.md`, `docs/agent/ADVERSARIAL_TEST_PLAN.md`.

---

## Develop

```bash
uv sync --group dev
uv run pytest tests/ -q
uv run python scripts/lint_rdl.py config/views.yaml
uv build   # produces dist/*.whl with bundled contracts
```

---

## Versioning

- **0.1.0b1** — first beta for private consumption
- Semver-ish: breaking RDL/contract changes bump minor while in beta when practical
- See [CHANGELOG.md](CHANGELOG.md)

---

## License

Proprietary — see [LICENSE](LICENSE). Private repository; do not republish.
