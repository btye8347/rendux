# RDL Agent Recipes

Copy and adapt. Full fragments live in `examples/agent/`.

## 1. KPI row

```yaml
data:
  kpi:
    - {label: Active, value: "24", status: ok}
    - {label: Alerts, value: "3", status: warn}
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

## 2. Health + timeline

```yaml
- type: grid
  columns: 2
  children:
    - widget: status_grid
      title: Service Health
      items: "$ctx.service_health"
    - widget: timeline
      events: "$ctx.recent_events"
```

## 3. Table + detail + form (admin)

See `examples/agent/service_admin.yaml` — `data_table` | `kv_table` | `form` | `modal`.

## 4. Alerts stack

```yaml
- type: stack
  children:
    - widget: alert
      variant: warn
      title: Queue depth elevated
      message: Consider scaling workers.
    - widget: progress_bar
      label: Disk — /data
      value: 73
      variant: warn
```

## 5. Empty state

```yaml
- widget: empty_state
  title: No results
  message: Adjust filters or add an entry.
  action_label: Add entry
  action_href: "#"
```

## 6. Confirm modal

```yaml
- widget: modal
  id: restart-confirm
  title: Restart service?
  body: Pods will roll one at a time.
  trigger_label: Restart
  trigger_variant: destructive
  confirm_label: Restart
  cancel_label: Cancel
```

## 7. Buttons row

```yaml
- type: row
  children:
    - widget: button
      each: "$ctx.actions"
      label: "$item.label"
      variant: "$item.variant"
      href: "$item.href"
```
