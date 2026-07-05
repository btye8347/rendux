# RDL Portability & Governance Plan

**Purpose:** Separate rendux's actual asset — the RDL grammar and widget contract — from its current
implementation (Python / FastAPI / Jinja2 / YAML / HTMX), so the business outcome (agent- and
human-authorable UI, no rebuilding the same widgets per tool) survives a future team choosing a
different stack. Python/FastAPI/Jinja is reference implementation #1, not the moat.

**Non-goal for this plan:** building a second-language renderer now. That becomes tractable only
after Phases 1–5 land (see "Deferred" at the end).

**Scope decision to lock alongside this work:** rendux v1 targets an internal ops/admin dashboard
shell, not a general app framework. The current widget lineup (status_grid, timeline, kv_table,
stepper) already implies this — say it explicitly in HANDOFF.md so future widget additions get
judged against it.

---

## Dependency graph

```
Phase 1 (Widget Contract Manifest)
  ├─→ Phase 2 (RDL Linter)
  ├─→ Phase 4 (Grammar Spec Doc)
  │     └─→ Phase 5 (Conformance Suite)
  │           └─→ Phase 6 (Vibe-Test Harness)  [also needs Phase 2]
  └─→ Phase 6 (needs manifest directly too)

Phase 3 (Strict Mode)      — independent, can run in parallel with anything
Phase 7 (Config Precedence Tests) — independent, low effort, slot in anytime
```

Do Phase 1 first. Everything else that matters depends on it.

---

## Phase 0 — Decisions (no code)

- [ ] Canonical model is JSON-shaped data (plain dicts/lists — what PyYAML already produces).
      YAML stays the human/agent-authoring surface; nothing changes in code, but document this
      explicitly so a future non-YAML frontend (e.g. a JSON-only agent tool call) is understood
      to be equally valid, not a lesser citizen.
- [ ] `version:` at the top of `config/views.yaml` is redefined to mean **grammar version**
      (semver against the RDL spec), decoupled from `pyproject.toml`'s app version. Bump to `0.1.0`
      → stays `0.1.0` until Phase 4 spec doc exists, then this becomes the thing that gets bumped.
- [ ] Add the scope statement above to `HANDOFF.md`.

---

## Phase 1 — Widget Contract Manifest

**Problem it closes:** `rendux/core/layout.py::_render_template` passes any non-reserved key
straight into the Jinja template. There is no declared schema for what `stat_card` or any of the
other 37 widgets actually accepts — a typo'd prop name silently renders blank instead of erroring.
This is the single largest gap versus a typed component API, and it blocks every later phase.

**Work:**

1. New file: `rendux/core/contracts.py` (pure data, no Jinja import) defining one entry per widget:

   ```python
   @dataclass(frozen=True)
   class WidgetContract:
       name: str
       required: dict[str, str]       # prop -> type name ("str", "int", "list", "bool")
       optional: dict[str, str]
       variants: dict[str, list[str]] # e.g. {"status": ["ok", "warn", "error", "info", "default"]}
       accepts_each: bool = True
   ```

2. Backfill by auditing all 38 templates under `rendux/templates/widgets/*.html` — for each,
   record every Jinja variable actually referenced. Cross-check against current usage in
   `config/views.yaml` (the `ops` view exercises stat_card, status_grid, timeline, item_list,
   alert, progress_bar today — start there, they're the best-specified examples).

3. Ship as a `WIDGET_REGISTRY: dict[str, WidgetContract]` importable from one place.

**Acceptance:** every widget referenced anywhere in `config/views.yaml` has a contract entry;
a unit test asserts the registry and the template directory stay in sync (no widget file without
a contract, no contract without a widget file).

---

## Phase 2 — RDL Linter

**Work:**

1. `scripts/lint_rdl.py`, callable as `uv run python scripts/lint_rdl.py config/views.yaml`
   (or wire as a `rendux lint` console-script entry point in `pyproject.toml` later).
2. Validates every layout tree in a view config against the Phase 1 registry:
   - widget name exists in `WIDGET_REGISTRY`
   - all `required` props present on the node (or provided per-item when `each:` is used)
   - unknown props → warning, not failure (forward-compat: a newer widget may accept more)
   - container `type`/`columns`/`gap` — already enforced at render time in `layout.py`; lint
     statically too, so it fails at commit time, not render time
   - `$ctx.*` references — where the target view has a static `data:` block, verify the path
     resolves; where data is injected dynamically (`view_ctx`), skip with a note (can't check
     statically, that's fine, don't force it)
3. Add as a pytest fixture (`tests/test_lint_rdl.py`) so it runs in the existing 88-test suite,
   and as a pre-commit hook if the team uses one.

**Acceptance:** deliberately breaking `config/views.yaml` (rename `label` to `labl` on a
`stat_card` node) makes the lint fail with a clear message, not a silent blank render.

---

## Phase 3 — Strict/Dev Mode

**Work:**

1. `LayoutRenderer.__init__(self, env: Environment, *, strict: bool = False)`.
2. In `_resolve`: when `strict` and a `$ctx.*`/`$item.*` path resolves to `None` because a key
   is genuinely missing (distinguish "missing" from "present but falsy" — don't break existing
   `when:` semantics), raise `LayoutConfigError` instead of returning `None`/`""`.
3. In `_render_template` and `_container`: when `strict`, unknown widget / unknown container type
   raise instead of emitting the placeholder `<div class="alert alert-error">` / HTML comment.
4. Wire a `RENDUX_STRICT=1` env var (or a `demo/main.py` startup flag) that flips this on for
   local dev / CI, off by default in the deployed app so production keeps today's graceful
   degradation.

**Acceptance:** existing 88 tests pass unchanged with `strict=False` (default); a new small test
file exercises `strict=True` and confirms it raises on a deliberately-broken `$ctx` path.

---

## Phase 4 — Grammar Spec Document

**Work:**

1. New file: `docs/rdl-spec-v0.1.md`. Extract the docstring currently at the top of
   `rendux/core/layout.py` (it's already ~90% of a spec — node types, sigils, resolution rules,
   nesting limit, security model) into this standalone doc, written so someone building a
   renderer in a different language could implement conformant behavior from the doc alone,
   without reading the Python source.
2. `layout.py`'s docstring shrinks to a short pointer: "Implements RDL spec v0.1, see
   `docs/rdl-spec-v0.1.md`."
3. The spec doc references the Phase 1 widget contract format explicitly (a widget node's
   `<param>: <value>` section should point at "see widget contracts" rather than re-describing
   ad hoc).

**Acceptance:** a colleague unfamiliar with the codebase can read only `docs/rdl-spec-v0.1.md`
and correctly predict what a given layout snippet renders, without opening `layout.py`.

---

## Phase 5 — Conformance Test Suite

**Work:**

1. New directory: `tests/conformance/` with golden fixtures — each fixture is (layout tree,
   context dict) → expected **structural** assertions, not literal HTML strings. E.g.:
   "given this tree + `{"kpi": [...]}`, expect 4 invocations of widget `stat_card` with resolved
   `label`/`value`/`status` equal to X/Y/Z" — assert against the resolved-params dict the renderer
   would pass to `_render_template`, not the rendered HTML output.
2. This deliberately decouples the fixtures from Jinja/HTML specifics: the assertions are about
   the *grammar layer* (dispatch + resolve), which is the part that's portable. A future
   non-Python renderer only needs to reproduce the same resolved-params behavior, not byte-match
   HTML.
3. Fixtures double as executable examples of the Phase 4 spec doc — link them from it.

**Acceptance:** conformance suite passes against current `layout.py`; it's structured so that
"could someone else's renderer, in principle, pass these same fixtures" is answerable by reading
the test, not by guessing.

---

## Phase 6 — Vibe-Test / Agent Eval Harness

**Work:**

1. Small script (`scripts/vibe_test.py` or similar) that feeds an LLM *only* `docs/rdl-spec-v0.1.md`
   and the Phase 1 widget registry (serialized, not the Python source) and prompts it to produce
   RDL layouts for a handful of target dashboard descriptions (e.g., "a page showing 3 KPI cards
   and a recent-activity timeline").
2. Run each generated layout through the Phase 2 linter and the Phase 3 strict-mode renderer.
3. Record pass/fail and failure modes (wrong prop name, wrong sigil, invalid container type) —
   this is the actual evidence for "agents can author correct RDL from docs alone," replacing the
   assumption with a number.

**Acceptance:** a documented pass rate exists, plus a short list of the top failure modes to feed
back into either the spec doc's clarity or the linter's error messages.

---

## Phase 7 — Config Precedence Pinning

**Work:** new tests (extend `tests/test_views.py` or add `tests/test_config_precedence.py`) that
pin the exact `deep_merge` cascade in `rendux/views/service.py` — shell defaults → view →
surface defaults — as executable spec. Low effort, low risk, no dependency on anything else; slot
this in whenever convenient.

---

## Deferred — not in this plan

**Alternate-language renderer (e.g., Rust) for fast interactive/test-loop iteration.** Only
becomes buildable and independently verifiable once Phase 4 (spec) and Phase 5 (conformance
suite) exist — those two are what let a second renderer prove it's conformant rather than just
"probably compatible." Worth revisiting once compile/startup latency of the Python/Jinja path
is actually a measured bottleneck, not before.

---

## Summary for the implementer

Start with Phase 1 (widget contract manifest) — it's the load-bearing piece everything else reads
from. Phase 3 (strict mode) can be done in parallel by anyone, any time — it's isolated to
`layout.py` and additive. Phases 4→5→6 are a strict pipeline. Phase 7 is a free action, do it
whenever there's a spare hour.