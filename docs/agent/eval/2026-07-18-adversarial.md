# Adversarial eval scorecard — 2026-07-18

| Field | Value |
|---|---|
| Date | 2026-07-18 |
| Model / product | (session agent — not recorded) |
| Context mode | Cold-start per ADVERSARIAL_TEST_PLAN (assumed) |
| Repo SHA | debb3c6+ (trial artifacts under `examples/agent/_trial/`) |
| Artifacts | `examples/agent/_trial/S1.yaml` … `S9.yaml` |

## Compile gate

All nine fragments: `agent_compile.py` → **ok: true**, `strict_render_ok: true`.

## Scenario scores

| Scenario | Points | Notes |
|---|---|---|
| S1 KPI | **2** | 4 KPIs via `stat_card` + `each` + `$ctx.kpi` / `$item.*` |
| S2 Alerts | **2** | Two `alert` + two `progress_bar`; metrics under `data` |
| S3 Schema catalog | **2** | `summary` / `services_table` / `selected_service` / `edit_form`; table + kv + form |
| S4 Modal | **2** | `modal` with `id` + `title`, destructive trigger |
| S5 Repair | **2** | Deliverable has `label` (not `labl`); compiles |
| S6 Empty+buttons | **2** | `empty_state` + primary/ghost `button` row via `each` |
| S7 Refuse chart | **2** | No `chart`/`sidebar`; substituted `data_table` + `button` nav in `split` |
| S8 HTML cards | **2** | Plain-text `card` bodies; no `<script>` |
| S9 Open-book services | **2** | Verified widgets only; near-parity with `/services` layout |
| A1–A3 | — | Not submitted as trial files |
| **S1–S9 total** | **18/18** | |

## Bars

| Tier | Required | Result |
|---|---|---|
| Smoke (S1–S3) | ≥ 4/6 | **6/6** ✓ |
| Core (S1–S6) | ≥ 8/12 | **12/12** ✓ |
| Adversarial (S1–S9) | ≥ 11/18 (+ probes) | **18/18** ✓ (probes not run) |

## Verdict

**☑ Pack OK**

Supporting evidence:

- Closed vocabulary respected (S7 substitution, S8 no HTML/script dump).
- Schema-driven admin page works without inventing widgets (S3).
- Compiler repair path viable (S5 final artifact clean).
- Production-shaped `/services` recreation stays on verified set (S9).

## Caveats / follow-ups

1. **A1–A3 micro-probes** were not filed — optional re-run for title→label, `$item` misuse, bad container.
2. **S9** closely mirrors `config/services_admin.yaml` (expected under open-book); still a valid pack pass if cold-start rules were followed for S1–S8.
3. **S3** select `options` used bare strings; compiles today but recipes prefer `{value, label}` — consider documenting in CONTEXT_SCHEMA / ANTI_PATTERNS.
4. Pass-1 vs Pass-R for S5 unknown (only final YAML present); scored 2 on deliverable compile success.

## Next

- Mark A6 executed in `LLM Agent Compatibility Plan.md`
- Optional: wire a winning trial into a throwaway view, or proceed to live HTMX on `/services`
