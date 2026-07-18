# Minimal host-app skeleton

Example of a **third-party app** that depends on the RendUX package (not this repo’s `demo/`).

## Setup

In a new project:

```toml
# pyproject.toml
dependencies = [
  "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1",
  "uvicorn[standard]>=0.35.0",
]
```

Copy this folder’s `config/` and `main.py`, then:

```bash
uv sync
uv run uvicorn main:app --reload --port 8010
```

Open http://127.0.0.1:8010/

## Layout

```
config/
  views.yaml           # shell + view registry
  home_layout.yaml     # RDL fragment (data + layout)
main.py                # configure_app + render_view
```

Full integration notes: [docs/CONSUMING.md](../../docs/CONSUMING.md).
