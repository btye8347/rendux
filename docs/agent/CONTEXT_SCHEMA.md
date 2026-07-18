# Context Schema Convention

Separate **data shape** (owned by the app / human) from **layout** (owned by the LLM).

## Pattern

1. Human defines required `data:` keys and field shapes.
2. LLM emits `data:` examples that match + `workspace.layout` that binds via `$ctx.*`.
3. At runtime, route handlers may override with `view_ctx` (same keys).

## Services admin (living example)

Reference: `config/services_admin.yaml` and `examples/agent/service_admin.yaml`.

| Key | Shape |
|---|---|
| `summary` | `[{label, value, status?}]` |
| `services_table` | `{title, searchable?, table_id?, columns[], rows[]}` |
| `selected_service` | `{title, rows: [{label, value, status?}]}` |
| `edit_form` | `{action?, submit_label?, cancel_href?, fields[]}` |

**Column:** `{key, label, sortable?, align?, badge?, badge_map?}`  
**Form field:** `{name, label, type?, value?, required?, options?, …}`

## Ops dashboard

Reference: `config/views.yaml` → `views.ops.data`.

| Key | Shape |
|---|---|
| `kpi` | `[{label, value, status?, trend?, subtitle?}]` |
| `service_health` | `[{label, status, detail?}]` |
| `recent_events` | `[{title, time?, status?, body?}]` |
| `recent_changes` | `[{title, description?, meta?}]` |

## Agent instructions

When given a schema:

- Put sample rows under `data:` (enough to render).
- Bind layout with `$ctx.<key>` and `each:` / item fields.
- Do not invent extra top-level data keys unless the task allows it.
