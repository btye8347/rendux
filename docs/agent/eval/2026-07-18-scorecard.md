# Adversarial LLM eval scorecard

| Field | Value |
|---|---|
| Date | 2026-07-18 |
| Model / product | (cold-start session) |
| Context mode | per-scenario (see ADVERSARIAL_TEST_PLAN) |
| Repo SHA | `debb3c6` |
| Artifacts | `examples/agent/_trial/S1.yaml` … `S9.yaml` |
| Detail notes | `docs/agent/eval/2026-07-18-adversarial.md` |

| Scenario | Points (0–2) | Notes / defects |
|---|---|---|
| S1 KPI | **2** | `stat_card` + `each` + `$ctx.kpi`; compile OK |
| S2 Alerts | **2** | 2× `alert` + 2× `progress_bar`; compile OK |
| S3 Schema catalog | **2** | summary / table / kv / form; compile OK |
| S4 Modal | **2** | `id` + `title`, destructive; compile OK |
| S5 Repair | **2** | `labl`→`label` fixed; compile OK |
| S6 Empty+buttons | **2** | `empty_state` + primary/ghost buttons; compile OK |
| S7 Refuse chart | **2** | Substituted `data_table` + `button` nav; no invented widgets |
| S8 HTML cards | **2** | Plain-text `card` bodies; no `<script>` |
| S9 Open-book services | **2** | Verified widgets only; `/services`-shaped; compile OK |
| A1 title→label | — | not run |
| A2 $item misuse | — | not run |
| A3 bad container | — | not run |
| **Total** | **18/18** (S1–S9) | Smoke **6/6** · Core **12/12** · Adv **18/18** |

**Verdict:** ☑ Pack OK · ☐ Needs doc fixes · ☐ Needs catalog/contract gaps · ☐ Compiler UX gaps

**Follow-ups:**

- Optional: run A1–A3 micro-probes
- Document select `options` as `{value, label}` in CONTEXT_SCHEMA (S3 used bare strings; still compiles)
- Optional: automated live harness (A6 remainder)
