# RDL Portability & Governance Plan

**Purpose:** Separate rendux's actual asset — the RDL grammar and widget contract — from its current
implementation (Python / FastAPI / Jinja2 / YAML / HTMX), so the business outcome (agent- and
human-authorable UI, no rebuilding the same widgets per tool) survives a future team choosing a
different stack. Python/FastAPI/Jinja is reference implementation #1, not the moat.

**Last audited:** 2026-07-05

---

## Implementation status (honest)

| Phase | Status | Notes |
|---|---|---|
| 0 — Decisions | **Done** | JSON canonical + YAML authoring documented; grammar `version:` commented in `views.yaml` |
| 1 — Widget contracts | **Partial (ops baseline)** | 6 verified, 32 unverified stubs; JSON source of truth (not Python `WidgetContract` dataclass) |
| 2 — RDL linter | **Done (CI-enforced)** | Strict unknown props = error (plan deviation, agreed); no pre-commit hook yet |
| 3 — Strict render mode | **Done** | `LayoutRenderer(strict=True)`, `RENDUX_STRICT=1`, verified-widget prop checks at render |
| 4 — Grammar spec | **Done** | `docs/rdl-spec-v0.1.md` |
| 5 — Conformance | **Partial** | Excerpt fixtures + full ops layout from `views.yaml`; collect/render parity test |
| 6 — Agent eval | **Done (fixture-based)** | `scripts/vibe_test.py` — 3 scenarios; LLM integration optional later |
| 7 — Config precedence | **Done** | `tests/test_config_precedence.py` |

**Test count:** 119 (run `uv run pytest tests/ -q`)

**CI:** `.github/workflows/ci.yml` — lint + pytest + strict ops smoke on push/PR

---

## Deviations from original plan (documented)

1. **Contracts in JSON**, not `contracts.py` dataclasses — agreed: JSON for system, YAML for human
2. **Unknown props → error** in strict lint (plan said warning) — agreed for CI/agent safety
3. **Phase 1 scope** — 6 ops widgets verified first; 32 stubs until audited (not full template audit)
4. **Strict render** also validates verified-widget props at runtime (closes silent-typo gap beyond original Phase 3 text)
5. **HTMX interaction profiles** declared in JSON but not enforced until widgets are verified

---

## Dependency graph

```
Phase 1 (Widget Contract Manifest)  ← partial: ops baseline
  ├─→ Phase 2 (RDL Linter)            ✓
  ├─→ Phase 4 (Grammar Spec Doc)     ✓
  │     └─→ Phase 5 (Conformance)    ← partial
  │           └─→ Phase 6 (Agent Eval)  ✗
  └─→ Phase 6

Phase 3 (Strict Mode)                 ✓
Phase 7 (Config Precedence)           ✗
```

---

## Phase 0 — Decisions

- [x] Canonical model is JSON-shaped data; YAML is human authoring surface (`docs/rdl-spec-v0.1.md`, `HANDOFF.md`)
- [x] `version:` in `config/views.yaml` = grammar version (comment added; decoupled from `pyproject.toml`)
- [x] Ops/admin scope in `HANDOFF.md`

---

## Phase 1 — Widget Contract Manifest

- [x] `contracts/widgets/*.json` — machine-readable registry
- [x] `rendux/core/contracts.py` — loader (no Jinja import)
- [x] Registry ↔ template directory sync test
- [ ] **Remaining:** audit and verify remaining 32 widgets; fix HTMX profile assignments on stubs

**Acceptance (ops baseline):** widgets used in `config/views.yaml` ops layout are verified.

---

## Phase 2 — RDL Linter

- [x] `scripts/lint_rdl.py` — `uv run python scripts/lint_rdl.py config/views.yaml`
- [x] Widget name, required props, unknown props (strict), container config, static `$ctx.*`, item schemas
- [x] `tests/test_lint_rdl.py` in pytest suite
- [x] CI enforcement
- [ ] Pre-commit hook (optional, not done)
- [ ] `pyproject.toml` console script entry (optional, not done)

**Acceptance:** `labl` typo on `stat_card` fails lint with clear error — **verified**.

---

## Phase 3 — Strict/Dev Mode

- [x] `LayoutRenderer(..., strict: bool = False)`
- [x] Missing required `$ctx.*` / `$item.*` paths raise `LayoutConfigError`
- [x] Optional props allow missing item/context keys (resolve to `None`)
- [x] Unknown widget/container raise in strict mode
- [x] Verified-widget unknown/missing props raise at render time
- [x] `RENDUX_STRICT=1` wired in `demo/main.py`
- [x] `tests/test_layout_strict.py`

**Acceptance:** `labl` typo raises at strict render — **verified**; permissive still degrades gracefully.

---

## Phase 4 — Grammar Spec Document

- [x] `docs/rdl-spec-v0.1.md`
- [x] `layout.py` docstring points to spec
- [x] Spec references widget contracts

---

## Phase 5 — Conformance Test Suite

- [x] `tests/conformance/` with structural assertions on resolved params
- [x] `collect_invocations()` API
- [x] Full ops layout test from real `config/views.yaml` (12 dispatches)
- [x] Collect/render parity test for ops layout
- [ ] Conformance fixtures linked inline from spec doc (partial — spec references test file only)
- [ ] Remaining widgets covered as they are verified

---

## Phase 6 — Agent Eval Harness

- [x] `scripts/vibe_test.py` — fixture-based eval (good + bad agent outputs)
- [x] Runs strict lint + strict render per scenario
- [x] CI step + `tests/test_vibe_test.py`
- [ ] Live LLM prompts (optional — requires API key; fixtures prove the pipeline)

**Pass rate:** 3/3 fixture scenarios (`uv run python scripts/vibe_test.py`)

---

## Phase 7 — Config Precedence Tests

- [x] `tests/test_config_precedence.py` — shell→view merge, surface defaults, render context order, layout vs template

---

## Deferred

Alternate-language renderer — only after Phase 5 is complete for all targeted widgets and Phase 6 establishes agent pass rates.

---

## How to verify this plan's claims

```bash
cd ~/dev/rendux
uv run pytest tests/ -q                                    # 119 tests
uv run python scripts/lint_rdl.py config/views.yaml        # must exit 0
uv run python scripts/vibe_test.py                         # agent eval fixtures
RENDUX_STRICT=1 uv run pytest tests/conformance/ tests/test_layout_strict.py -q
```
