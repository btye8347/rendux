# RendUX consumers

Known host apps that pin this library. Keep tags stable; document spacing + chat usage.

## Vesta Console (hl homelab)

| | |
|---|---|
| **Path** | `~/dev/homelab/instance/services/vesta-console/` |
| **Pin** | `v0.1.0b2` |
| **Knowledge** | `instance/services/vesta-console/RENDUX.md` |
| **Runtime** | services-01 `:8093` (`console.lab`) |

**Patterns used**

- RDL `gap` / `space` tokens (`md` / `lg`) between KPI grid, status grids, alert
- Fragment poll: `id: fleet-status` + `poll: 20s` + `poll_url` so live tiles refresh without wiping the chat sibling
- Verified `chat` widget with host `POST /partials/c2/send` returning `chat_message` HTML
- `stat_card`, `status_grid`, `data_table`, `alert`

**Host owns:** LiteLLM / hl-ops C2 routing, CONFIRM chrome, probe `view_ctx`.  
**RendUX owns:** shell, widgets, layout spacing, HTMX poll attributes on containers.
