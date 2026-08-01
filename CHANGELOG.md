# Changelog

## Unreleased

### Added

- **Layout spacing scale** — CSS tokens `--rx-space-*` with RDL `gap` / `space` on
  containers (`none|xs|sm|md|lg|xl`). Inward gap + outward block rhythm; section
  defaults via `--rx-section-gap` / `--rx-section-space`.
- **`chat` / `chat_message` widgets** — verified chat panel (thread + composer) with
  HTMX append hooks; demo at `/chat` with mock `/partials/chat/send`.

## 0.1.0b1 — 2026-07-18

First **beta** release for private consumption as a git dependency.

### Packaging

- Installable via hatchling wheel; `contracts/` bundled into `rendux/contracts`
- Path helpers: `templates_dir()`, `static_dir()`, `contracts_dir()`, `catalog_verified_path()`
- Public version: `rendux.__version__`
- Host integration: `rendux.integration.configure_app` / `render_view`

### RDL / product (included baseline)

- Grammar + linter + strict render
- 19 verified widget contracts (ops + admin set)
- Demo views: `/ops` (live poll), `/services` (admin use case), `/components`
- LLM agent pack: `docs/agent/*`, `agent_compile`, adversarial eval scorecard 18/18

### Docs

- `README.md` — install + quick start
- `docs/CONSUMING.md` — host-app integration guide
- `LICENSE` — proprietary

### Known limitations

- 19 of 38 widgets verified; rest are stubs (lint skips prop checks)
- Private git only (not on PyPI)
- API may shift before 0.1.0 final
