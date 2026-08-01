# RDL Agent Cheatsheet

Full grammar: `docs/rdl-spec-v0.1.md`. Closed widget list: `contracts/catalog.verified.json`.

## View fragment shape

```yaml
data:
  kpi: [{label: CPU, value: "82%", status: ok}]
workspace:
  layout:
    - type: grid
      columns: 4
      children:
        - widget: stat_card
          each: "$ctx.kpi"
          label: "$item.label"
          value: "$item.value"
          status: "$item.status"
```

## Node kinds

| Kind | Keys |
|---|---|
| Widget | `widget`, params…, optional `when`, `each` |
| Container | `type`, `children` (or `primary`/`secondary` for split) |
| Divider | `divider: true` **or** `widget: divider` + optional `label` |
| Heading | `heading`, optional `level` (1–6) |

## Containers

| type | Notes |
|---|---|
| `stack` | vertical; optional `gap` / `space` |
| `row` | horizontal; optional `gap` / `space` |
| `grid` | `columns: 1\|2\|3\|4\|auto`; optional `gap` / `space` |
| `section` | `heading`, `description`, `children`; optional `gap` / `space` |
| `split` | `primary`, `secondary` lists; optional `initial`, `min`, `id` |

**Spacing tokens:** `none | xs | sm | md | lg | xl`  
- `gap` = inward (between children)  
- `space` = outward (block rhythm after this node)  
Defaults are CSS vars (`--rx-gap-default`, `--rx-section-space`, …).

Polling (optional): on a container, `id: ops-kpis` + `poll: 15s` → HTMX refresh of children.

## Sigils

| Form | Meaning |
|---|---|
| `$ctx.key` / `$ctx.a.b` | from `data:` / view_ctx |
| `$item.key` | current `each:` item |
| literals | strings, numbers, bools, lists, maps |

## Verified widgets (21)

`alert` · `badge` · `button` · `card` · `chat` · `chat_message` · `data_table` · `divider` · `empty_state` · `form` · `item_list` · `kv_table` · `modal` · `pagination` · `panel` · `progress_bar` · `stat_card` · `status_badge` · `status_grid` · `tabs` · `timeline`

## Naming

| Role | Prop |
|---|---|
| Section / collection title | `title` |
| Scalar descriptor | `label` |
| Scalar value | `value` |

## Compile

```bash
uv run python scripts/agent_compile.py path/to/fragment.yaml --pretty
```
