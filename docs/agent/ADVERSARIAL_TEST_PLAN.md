# Adversarial LLM Authoring Test Plan

**Purpose:** Validate whether the agent pack actually lets a model author RDL **without**
this repo’s chat history, tribal knowledge, or reading Jinja/Python.

**Status:** Ready to run (manual / separate session)  
**Created:** 2026-07-18  
**Parent plan:** [`LLM Agent Compatibility Plan.md`](../../LLM%20Agent%20Compatibility%20Plan.md)  
**Gate command:** `uv run python scripts/agent_compile.py <fragment.yaml> --pretty`

We will not know this works until this plan is executed. Fixture tests prove the compiler;
this plan proves the **prompt surface**.

---

## 0. Session rules (non-negotiable)

Run in a **new Cursor chat** (or other agent) with **no prior RendUX conversation**.

### Facilitator provides ONLY

| Asset | Path |
|---|---|
| System prompt | `docs/agent/SYSTEM.md` (paste as system / first message) |
| Closed catalog | `contracts/catalog.verified.json` |
| Optional (scenarios mark which) | `docs/agent/CHEATSHEET.md`, `RECIPES.md`, `CONTEXT_SCHEMA.md`, one of `examples/agent/*.yaml` |

### Facilitator MUST NOT provide

- This adversarial plan’s **expected answers** or widget cheat sheets beyond the allowed assets
- `HANDOFF.md`, governance plans, or prior chat summaries
- `rendux/templates/**`, `rendux/core/*.py` (except running compile as a black box)
- `config/components_showcase.yaml` (unverified noise)
- Full `config/views.yaml` / `services_admin.yaml` unless a scenario explicitly allows a **schema-only** extract

### Agent may use tools to

- Write a YAML file under `/tmp` or `examples/agent/_trial/`
- Run: `uv run python scripts/agent_compile.py <file> --pretty`
- Re-read only the allowed docs/catalog if attached

### Agent must not

- Browse the repo for “how /services works” unless a scenario says **open-book**
- Invent widgets outside `catalog.verified.json`

---

## 1. Pass / fail scoring

Each scenario scores:

| Result | Points |
|---|---|
| **Pass-1** — first compile exits 0 | 2 |
| **Pass-R** — fails once, then passes after ≤2 repair rounds using compile errors only | 1 |
| **Fail** — still broken after 2 repairs, or invents widgets/props, or refuses YAML fragment | 0 |

**Suite pass bar (recommended):**

| Tier | Requirement |
|---|---|
| **Smoke** | Scenarios S1–S3 ≥ 4/6 points |
| **Core** | S1–S6 ≥ 8/12 points |
| **Adversarial** | S1–S9 ≥ 11/18 points **and** A1–A3 ≥ 2/6 points |

Record results in §6 scorecard. Attach failing YAML + compile JSON for fails.

---

## 2. Scenario pack

### S1 — KPI dashboard (baseline)

**Allowed context:** SYSTEM + catalog + `examples/agent/kpi_dashboard.yaml` (few-shot OK)

**Prompt:**
> Build a view fragment for an ops overview with 4 KPIs: Active Jobs, Failed Jobs, Queue Depth, Workers Online. Use sample data. Prefer `each:` over inlining cards.

**Pass criteria:**
- Shape: `data` + `workspace.layout`
- Uses `stat_card` + `each` + `$ctx` / `$item`
- `agent_compile.py` exits 0

---

### S2 — Alerts + progress (no few-shot)

**Allowed context:** SYSTEM + catalog + CHEATSHEET only (no examples)

**Prompt:**
> Emit a fragment with two alerts (warn + error) and two progress bars (disk 80 warn, CPU 35 default). Put metrics under `data` if needed; alerts may be literal.

**Pass criteria:**
- Widgets: `alert`, `progress_bar` only (containers OK)
- Compile exits 0
- No invented props (`msg`, `percent`, etc.)

---

### S3 — Service catalog from schema only

**Allowed context:** SYSTEM + catalog + CONTEXT_SCHEMA.md (services table section)  
**Forbidden:** opening `config/services_admin.yaml` or `examples/agent/service_admin.yaml`

**Prompt:**
> Using the services admin context schema, create a fragment with: summary KPI row, searchable data_table, kv_table for a selected service, and an edit form. Include 2–3 sample rows.

**Pass criteria:**
- Uses `stat_card`, `data_table`, `kv_table`, `form` (panel/modal optional)
- Data keys align with schema (`summary`, `services_table`, …) or clearly mapped equivalents that compile
- Compile exits 0

---

### S4 — Modal confirm (profile rules)

**Allowed context:** SYSTEM + catalog

**Prompt:**
> Add a destructive confirm modal to restart `api-gateway`. Include a short body and Cancel/Confirm labels.

**Pass criteria:**
- `modal` with required `id` + `title`
- Compile exits 0 (dom-dialog profile)

---

### S5 — Repair loop (facilitator injects a bug)

**Setup:** Facilitator pastes a **broken** fragment (below) and the compile error JSON.  
**Allowed context:** SYSTEM + catalog + the error output only

Broken seed:

```yaml
data:
  kpi:
    - label: CPU
      value: "72%"
workspace:
  layout:
    - widget: stat_card
      each: "$ctx.kpi"
      labl: "$item.label"
      value: "$item.value"
```

**Prompt:**
> This failed compile. Fix it. Output the full corrected fragment only.

**Pass criteria:**
- Corrects `labl` → `label`
- Compile exits 0 within ≤2 turns
- Does not rewrite into an unrelated design

---

### S6 — Empty state + buttons

**Allowed context:** SYSTEM + catalog + RECIPES.md

**Prompt:**
> Fragment for a “no deployments” empty state with a primary CTA button linking to `#/new`, and a secondary ghost button “Docs” to `#/docs`.

**Pass criteria:**
- `empty_state` and/or `button` from catalog
- Compile exits 0

---

### S7 — Adversarial: invent a widget (must refuse)

**Allowed context:** SYSTEM + catalog

**Prompt:**
> Build a page with a `chart` widget showing request latency over time, plus a `sidebar` navigation widget.

**Pass criteria (adversarial pass):**
- Agent **refuses** or substitutes verified widgets (`stat_card`, `data_table`, `item_list`, etc.)
- Does **not** emit `widget: chart` or `widget: sidebar`
- If it substitutes, compile exits 0  
**Fail if:** it invents those widgets even if it “looks right”

---

### S8 — Adversarial: wrong naming / HTML dump

**Allowed context:** SYSTEM + catalog

**Prompt:**
> Create three cards. Put rich HTML with `<script>` and inline styles in the body. Title the metric fields however you like.

**Pass criteria (adversarial):**
- Uses `card` (or `panel`) with plain text, or clearly avoids script injection patterns
- Does not invent props; uses `title`/`body` per contract
- Compile exits 0  
**Soft fail note:** HTML in `body` may compile but is undesirable — mark **Pass-R / warning** if compile OK but includes `<script>`

---

### S9 — Adversarial: open-book temptation

**Allowed context:** SYSTEM + catalog only  
**Agent tools:** full repo search **enabled** (temptation)

**Prompt:**
> Recreate the production `/services` page as a new fragment file. You may explore the repo.

**Pass criteria:**
- Compile exits 0
- Prefer verified widgets only (no unverified from components showcase)
- Score **Pass-1** if it works without copying unverified widgets  
**Fail if:** pulls unverified widgets (`drawer`, `split_pane` as widget with bad props, etc.) that break compile, or copies showcase HTML-escape footguns without fixing

---

## 3. Adversarial micro-probes (quick)

Run after core suite. Each is 2 points max (Pass-1 / Pass-R / Fail).

| ID | Prompt gist | Expect |
|---|---|---|
| A1 | Use `title` instead of `label` on `stat_card` | Repair to `label` or accept warning-only if compile still 0; prefer `label` |
| A2 | `$item.name` outside `each:` | Fix structure; compile 0 |
| A3 | Container `type: flexbox` | Reject / replace with `row` or `stack`; compile 0 |

---

## 4. Facilitator runbook

1. `cd ~/dev/rendux && git checkout master && git pull`
2. Confirm pack exists:
   ```bash
   test -f docs/agent/SYSTEM.md && test -f contracts/catalog.verified.json
   uv run python scripts/agent_compile.py examples/agent/kpi_dashboard.yaml
   ```
3. Open a **new** chat titled e.g. `RDL adversarial eval`
4. First message: paste SYSTEM.md + attach/catalog path + scenario prompt
5. Save model output to `examples/agent/_trial/S<n>.yaml`
6. Compile; if fail, paste JSON errors back (max 2 repairs)
7. Fill scorecard (§6)
8. Optional: wire winning fragment into a throwaway view later — **out of scope** for this plan

### Suggested first message template

```
You are bound by the attached SYSTEM.md rules.
Closed vocabulary: contracts/catalog.verified.json
You may run: uv run python scripts/agent_compile.py <file> --pretty

Task: [SCENARIO PROMPT]

Output: a single YAML view fragment (data + workspace.layout) written to
examples/agent/_trial/S<n>.yaml — no prose unless compile fails.
```

---

## 5. What “works as expected” means

The pack works if a cold-start agent can:

1. Emit valid RDL for S1–S3 without reading templates
2. Self-repair S5 from compile errors alone
3. Refuse or safely substitute on S7 (no invented widgets)
4. Hit the **Core** or **Adversarial** score bar in §1

It does **not** require pixel-perfect match to `/services` or live HTMX behavior.

---

## 6. Scorecard (copy per run)

| Field | Value |
|---|---|
| Date | |
| Model / product | |
| Context mode | SYSTEM+catalog only / +cheatsheet / +few-shot |
| Repo SHA | |

| Scenario | Points (0–2) | Notes / defects |
|---|---|---|
| S1 KPI | | |
| S2 Alerts | | |
| S3 Schema catalog | | |
| S4 Modal | | |
| S5 Repair | | |
| S6 Empty+buttons | | |
| S7 Refuse chart | | |
| S8 HTML cards | | |
| S9 Open-book services | | |
| A1 title→label | | |
| A2 $item misuse | | |
| A3 bad container | | |
| **Total** | **/24** | Smoke≥4/6 · Core≥8/12 · Adv≥13/24 |

**Verdict:** ☐ Pack OK · ☐ Needs doc fixes · ☐ Needs catalog/contract gaps · ☐ Compiler UX gaps

**Follow-ups (file issues / plan updates):**

- …

---

## 7. After the session

1. Commit scorecard notes under `docs/agent/eval/` as `YYYY-MM-DD-<model>.md` (optional)
2. Update `LLM Agent Compatibility Plan.md` A6 status if live eval is now evidence-backed
3. Fix the **smallest** pack gap that caused fails (SYSTEM wording, missing description, recipe, error message clarity) — not random new features

---

## 8. Out of scope

- Visual regression / browser pixel tests
- Live HTMX polling correctness
- Training or fine-tuning a model
- Verifying remaining 19 unverified widgets
