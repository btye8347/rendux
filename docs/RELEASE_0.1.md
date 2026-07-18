# RendUX 0.1.0b1 release notes

**Tag:** `v0.1.0b1`  
**Audience:** Internal / private host apps depending on this repo  
**Date:** 2026-07-18

## Intent

Ship a **beta library** you can `uv add` from git and use inside a real application:

1. Host owns routes + YAML config + domain `view_ctx`
2. RendUX owns widgets, chrome, contracts, RDL compile/render
3. LLMs can author RDL against the verified catalog + agent docs

## Install

```bash
uv add "rendux @ git+ssh://git@github.com/btye8347/rendux.git@v0.1.0b1"
```

Read **[CONSUMING.md](CONSUMING.md)** before wiring a host app.

## Checklist (maintainers)

- [x] Version `0.1.0b1` in `pyproject.toml` + `rendux.__version__`
- [x] Wheel builds with bundled contracts (`uv build`)
- [x] Integration API + demo uses it
- [x] README + CONSUMING + CHANGELOG + LICENSE
- [x] Consumer example under `examples/consumer/`
- [x] Tests green; packaging smoke in CI
- [x] Tests + `uv build` (contracts in wheel)
- [x] Git tag `v0.1.0b1` pushed
- [ ] Smoke-install into a scratch host app (manual)

## Upgrade path later

- `0.1.0` — after one successful host-app trial + any API fixes
- Continue Track A widget verification as apps need more widgets
