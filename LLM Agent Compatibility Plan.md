# LLM Agent Compatibility Plan

**Purpose:** Make RendUX / RDL reliably authorable by LLMs. Treat the existing stack as a
**compiler** (grammar + contracts + linter + strict render). Add an **agent interface layer**
so a model can emit valid view YAML from a closed vocabulary without reading Jinja or Python.

**Created:** 2026-07-18  
**Depends on:** RDL Portability & Governance Plan (Phases 0–7 ops/admin baseline)  
**Companion demo:** `/services` (`config/services_admin.yaml`)

---

## Principle

| Layer | Owner | LLM sees? |
|---|---|---|
| Intent (product ask) | human | yes (task prompt) |
| Context schema (`data:` shape) | app / human | yes (schema + example) |
| Layout (RDL YAML) | **LLM** | authors this |
| Contracts + grammar | RendUX | yes (verified catalog only) |
| Templates / Python | RendUX | **no** |

Do **not** invent a second DSL. RDL YAML + JSON contracts **are** the agent language. Wrap them.

---

## Implementation status

| Phase | Status | Deliverable |
|---|---|---|
| A0 — Plan memorialized | **Done** | this document + HANDOFF pointer |
| A1 — Agent prompt pack | **Done** | `docs/agent/{SYSTEM,CHEATSHEET,ANTI_PATTERNS,RECIPES}.md` |
| A2 — Verified catalog | **Done** | `description` on contracts → `contracts/catalog.verified.json` |
| A3 — Compile loop | **Done** | `rendux/core/agent_compile.py` + `scripts/agent_compile.py` + tests |
| A4 — Few-shot examples | **Done** | `examples/agent/{kpi_dashboard,ops_alerts,service_admin}.yaml` |
| A5 — Context schema convention | **Done** | `docs/agent/CONTEXT_SCHEMA.md` |
| A6 — Live LLM eval | **Executed (manual)** | Scorecard `docs/agent/eval/2026-07-18-adversarial.md` — S1–S9 **18/18**; automated live harness still pending |
| A7 — Agent tools / MCP | Deferred | `lint_rdl`, `list_widgets`, `compile_view` tools |

**Definition of done (LLM-compatible):**

1. Agent given only `SYSTEM.md` + `catalog.verified.json` + 2–3 recipes can author a view fragment.
2. Fragment is a view include: `data:` + `workspace.layout:`.
3. `agent_compile.py` accepts it (strict lint + strict render).
4. Failures return structured, path-addressable errors for one-shot repair.
5. Fixture (then live) eval measures pass rate on admin/ops tasks.

---

## Phase A1 — Agent prompt pack

**Path:** `docs/agent/`

| File | Role | Token budget |
|---|---|---|
| `SYSTEM.md` | System prompt: role, output format, hard rules | ~1–2k tokens |
| `CHEATSHEET.md` | Nodes, sigils, containers, verified widget list | ~1–2 pages |
| `RECIPES.md` | 6–10 copyable patterns | reference, not always in prompt |
| `ANTI_PATTERNS.md` | Common LLM failures + fixes | reference / repair hints |

**Hard rules (must appear in SYSTEM.md):**

- Only widgets with `status: verified` (from catalog)
- Prefer `$ctx.*` + `each:` over large inline lists in layout
- No invented props / widgets / container types
- Containers: `stack | row | grid | section | split` only
- Output YAML only — no Python, HTML, or markdown fences unless asked
- Success = passes `agent_compile`

**Acceptance:** files exist; SYSTEM.md is self-contained enough to paste as a system prompt.

---

## Phase A2 — Verified catalog

**Source of truth:** `contracts/widgets/*.json` (verified only).

1. Add `description` (one sentence) to every verified widget contract.
2. `scripts/build_agent_catalog.py` generates `contracts/catalog.verified.json`:
   - name, description, accepts_each, interaction, props, item_schema
   - optional tiny usage snippet
3. CI or test: catalog is up to date / rebuildable.

**Acceptance:** catalog lists exactly the verified set; agent docs point to it as the closed vocabulary.

**Do not** expose unverified stubs to agents until audited (Track A remainder).

---

## Phase A3 — Compile loop

**Script:** `scripts/agent_compile.py`

```
YAML fragment (file or stdin)
  → parse as view include (data + layout)
  → RdlLinter(strict=True)
  → LayoutRenderer(strict=True).render(...)
  → JSON report: { ok, errors[], warnings[], notes[] }
```

Exit code 0 on success, 1 on failure (agent-friendly).

**Acceptance:** good `/services`-like fragment exits 0; typo prop exits 1 with path in error.

---

## Phase A4 — Few-shot examples

**Path:** `examples/agent/`

| File | Teaches |
|---|---|
| `kpi_dashboard.yaml` | grid + `stat_card` + `each` |
| `service_admin.yaml` | table + kv + form + modal (trimmed `/services`) |
| `ops_alerts.yaml` | alerts + progress + timeline |

Keep each file small enough to fit in a few-shot prompt.

---

## Phase A5 — Context schema convention

**Path:** `docs/agent/CONTEXT_SCHEMA.md`

Document the pattern: human/app defines `data:` keys; LLM maps them in layout.

Example for services admin:

```yaml
summary: [{label, value, status}]
services_table: {title, columns, rows, ...}
selected_service: {title, rows}
edit_form: {action, fields, submit_label, cancel_href}
```

**Acceptance:** recipe docs reference schema; `/services` remains the living example.

---

## Phase A6 — Live LLM eval (Track C)

Extend `scripts/vibe_test.py` (or sibling):

- Fixture path remains default (no API key)
- Optional `--live` with model API: prompt = SYSTEM + catalog + task → compile → score
- Tasks: “KPI ops row”, “services catalog page”, “form + confirm modal”

**Acceptance:** documented pass-rate command; CI stays fixture-only.

---

## Phase A7 — Agent tools (deferred)

Optional MCP / CLI tools for Cursor and other agents:

- `list_widgets` → catalog
- `compile_view` → agent_compile
- `lint_rdl` → existing linter

Defer until A1–A3 are stable.

---

## Explicit non-goals

- Teaching agents from `components_showcase.yaml` (too large; unverified widgets; HTML-in-props)
- Putting HANDOFF / governance full text in the system prompt
- A parallel “agent DSL” beside RDL
- Waiting for all 38 widgets to be verified before shipping the agent pack

---

## Tracking checklist

- [x] Plan file created (`LLM Agent Compatibility Plan.md`)
- [x] A1 prompt pack
- [x] A2 catalog + descriptions
- [x] A3 `agent_compile.py`
- [x] A4 examples
- [x] A5 context schema doc
- [x] A6 adversarial manual test plan (`docs/agent/ADVERSARIAL_TEST_PLAN.md`)
- [x] A6 executed + scorecard filed under `docs/agent/eval/` (`2026-07-18-adversarial.md`)
- [ ] A6 automated live harness (optional)
- [ ] A7 tools (deferred)

---

## How to verify

```bash
cd ~/dev/rendux
uv run python scripts/build_agent_catalog.py
uv run python scripts/agent_compile.py examples/agent/service_admin.yaml
uv run pytest tests/test_agent_compile.py tests/test_agent_catalog.py -q
```

**Cold-start / adversarial validation (separate session):** follow  
[`docs/agent/ADVERSARIAL_TEST_PLAN.md`](docs/agent/ADVERSARIAL_TEST_PLAN.md) — do not skip; fixture tests do not prove the prompt pack.
