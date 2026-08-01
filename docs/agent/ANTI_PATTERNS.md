# RDL Agent Anti-Patterns

| Bad | Why | Fix |
|---|---|---|
| Invent widget `table` / `chart` | Not in verified catalog | Use `data_table`, `stat_card`, etc. |
| Prop typo `labl` / `msg` | Strict lint/render error | Use contract prop names (`label`, `message`) |
| Use `title` on `stat_card` | Deprecated alias (warning) | Use `label` |
| Huge inline `rows:` in layout | Hard to maintain; duplicates data | Put lists under `data:`; reference `$ctx…` |
| `$item.x` outside `each:` | Resolves empty / strict error | Wrap with `each:` or use `$ctx` |
| HTML strings in most props | Escaped or wrong | Prefer text props; HTML only where documented (`tabs.initial_content`, split panels) |
| Unverified widgets from `/components` | Props not enforced; may break | Stick to catalog.verified.json |
| Deep nested grids (5+ levels) | Fragile, hard to repair | Prefer section → grid → widgets |
| Mix shell/routing into layout | Out of scope | RDL is workspace content only |
| Emit Python / Jinja | Wrong layer | YAML fragment only |
| `modal` without `id` | dom-dialog profile requires it | Always set `id` + `title` |
| Pagination `url_pattern` without `{page}` | Broken links | Include `{page}` placeholder |
| `gap: 12px` or inventing sizes | Not in spacing scale | Use `none\|xs\|sm\|md\|lg\|xl` |

## Repair loop

1. Run `agent_compile.py`
2. Read `errors[].path` + `message`
3. Patch only those nodes
4. Recompile (max 2–3 retries)
