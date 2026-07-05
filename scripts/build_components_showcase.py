#!/usr/bin/env python3
"""Generate config/components_showcase.yaml from the components.html widget catalog."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "config" / "components_showcase.yaml"

CODE_BLOCK_SAMPLE = """\
from rendux.core.themes import ThemeService

svc = ThemeService.from_yaml(Path('config/themes.yaml'))
css = svc.generate_css()
themes = svc.list_themes()  # [{id, label}, ...]"""

SPLIT_PRIMARY = (
    "<h3 style='margin:0 0 0.5rem;font-size:0.95rem;'>Primary Panel</h3>"
    "<p style='color:var(--rx-text-2);font-size:0.85rem;margin:0;'>"
    "Drag the handle to resize. This side can hold a file tree, nav list, "
    "config form, or any widget.</p>"
)

SPLIT_SECONDARY = (
    "<h3 style='margin:0 0 0.5rem;font-size:0.95rem;'>Secondary Panel</h3>"
    "<p style='color:var(--rx-text-2);font-size:0.85rem;margin:0;'>"
    "Detail view, preview, or output goes here. Scrolls independently of "
    "the primary side.</p>"
)

TABS_INITIAL = (
    "<p style='padding:0.75rem 0; font-size:0.875rem; color:#4a5563; "
    "margin:0;'>Loading overview…</p>"
)


def build_data() -> dict[str, Any]:
    return {
        "button_variants": [
            {"label": "Primary", "variant": "primary"},
            {"label": "Secondary", "variant": "secondary"},
            {"label": "Ghost", "variant": "ghost"},
            {"label": "Destructive", "variant": "destructive"},
            {"label": "Disabled", "variant": "primary", "disabled": True},
            {"label": "Small", "variant": "secondary", "size": "sm"},
            {"label": "Large", "variant": "primary", "size": "lg"},
            {"label": "Link", "variant": "ghost", "href": "#"},
        ],
        "badge_variants": [
            {"label": "Default"},
            {"label": "Info", "variant": "info"},
            {"label": "Success", "variant": "success", "dot": True},
            {"label": "Warning", "variant": "warn", "dot": True},
            {"label": "Error", "variant": "error"},
        ],
        "tag_variants": [
            {"label": "Default"},
            {"label": "info", "variant": "info"},
            {"label": "success", "variant": "success"},
            {"label": "warn", "variant": "warn"},
            {"label": "error", "variant": "error"},
        ],
        "alert_variants": [
            {"message": "This is an informational message.", "variant": "info"},
            {
                "title": "Operation complete",
                "message": "All services restarted successfully.",
                "variant": "success",
            },
            {
                "title": "Degraded service",
                "message": "Worker queue depth is above threshold.",
                "variant": "warn",
            },
            {
                "title": "Connection failed",
                "message": "Could not reach the database host.",
                "variant": "error",
            },
        ],
        "status_badge_variants": [
            {"status": "ok", "label": "Healthy"},
            {"status": "warn", "label": "Degraded"},
            {"status": "error", "label": "Unreachable"},
            {"status": "unknown", "label": "Not configured"},
        ],
        "avatar_variants": [
            {"name": "Bryan Tye", "size": "sm"},
            {"name": "Bryan Tye", "size": "md"},
            {"name": "Bryan Tye", "size": "lg"},
            {"name": "Ada Lovelace", "size": "md"},
            {"name": "Z", "size": "md"},
        ],
        "progress_bar_variants": [
            {"label": "Storage used", "value": 72, "max": 100},
            {"label": "Memory", "value": 3.1, "max": 8, "variant": "ok"},
            {"label": "CPU", "value": 74, "max": 100, "variant": "warn"},
            {"label": "Error budget", "value": 91, "max": 100, "variant": "error"},
        ],
        "breadcrumb_items": [
            {"label": "Home", "href": "/"},
            {"label": "Components", "href": "/components"},
            {"label": "breadcrumb"},
        ],
        "panel_demo": {
            "title": "Panel title",
            "body": (
                "A panel with a shaded header row. Supports action buttons "
                "in the header."
            ),
            "actions": [
                {"label": "Edit", "href": "#", "variant": "ghost"},
                {"label": "Refresh", "href": "#", "variant": "secondary"},
            ],
        },
        "collapsible_variants": [
            {
                "title": "Collapsed by default",
                "body": (
                    "This content is hidden until the header is clicked. Uses "
                    "the native HTML details element — zero JavaScript."
                ),
            },
            {
                "title": "Open by default",
                "body": (
                    "Pass open=true to start expanded. The browser preserves "
                    "toggle state natively."
                ),
                "open": True,
            },
        ],
        "tabs_demo": {
            "tabs": [
                {
                    "id": "overview",
                    "label": "Overview",
                    "url": "/partials/tab/overview",
                    "active": True,
                },
                {
                    "id": "config",
                    "label": "Config",
                    "url": "/partials/tab/config",
                },
                {"id": "code", "label": "Code", "url": "/partials/tab/code"},
            ],
            "target": "tab-demo-content",
            "initial_content": TABS_INITIAL,
        },
        "toast_buttons": [
            {
                "label": "Success",
                "variant": "secondary",
                "size": "sm",
                "hx_get": (
                    "/partials/toast?variant=success&title=Done"
                    "&message=Operation+completed."
                ),
                "hx_target": "#toast-container",
                "hx_swap": "beforeend",
            },
            {
                "label": "Warning",
                "variant": "secondary",
                "size": "sm",
                "hx_get": (
                    "/partials/toast?variant=warn&title=Warning"
                    "&message=Queue+depth+is+high."
                ),
                "hx_target": "#toast-container",
                "hx_swap": "beforeend",
            },
            {
                "label": "Error",
                "variant": "secondary",
                "size": "sm",
                "hx_get": (
                    "/partials/toast?variant=error&title=Error"
                    "&message=Connection+failed."
                ),
                "hx_target": "#toast-container",
                "hx_swap": "beforeend",
            },
            {
                "label": "Info",
                "variant": "secondary",
                "size": "sm",
                "hx_get": (
                    "/partials/toast?variant=info&message=Nothing+has+changed."
                ),
                "hx_target": "#toast-container",
                "hx_swap": "beforeend",
            },
        ],
        "modal_demo": {
            "id": "demo-modal",
            "title": "Confirm action",
            "trigger_label": "Open modal",
            "body": (
                "Are you sure you want to proceed? This will apply your "
                "changes to the active configuration."
            ),
            "confirm_label": "Apply",
            "cancel_label": "Cancel",
        },
        "skeleton_variants": [{"lines": 3}, {"lines": 5}],
        "pagination_demo": {
            "current": 4,
            "total": 12,
            "url_pattern": "/items?page={page}",
        },
        "form_demo": {
            "action": "#",
            "submit_label": "Save settings",
            "cancel_href": "#",
            "fields": [
                {
                    "type": "text",
                    "name": "service_name",
                    "label": "Service name",
                    "placeholder": "my-service",
                    "required": True,
                    "hint": "Lowercase letters, numbers and hyphens only.",
                },
                {
                    "type": "email",
                    "name": "alert_email",
                    "label": "Alert email",
                    "placeholder": "ops@example.com",
                },
                {
                    "type": "select",
                    "name": "log_level",
                    "label": "Log level",
                    "value": "INFO",
                    "options": [
                        {"value": "DEBUG", "label": "DEBUG"},
                        {"value": "INFO", "label": "INFO"},
                        {"value": "WARN", "label": "WARN"},
                        {"value": "ERROR", "label": "ERROR"},
                    ],
                },
                {
                    "type": "textarea",
                    "name": "notes",
                    "label": "Notes",
                    "placeholder": "Optional notes…",
                    "rows": 3,
                },
                {
                    "type": "checkbox",
                    "name": "enabled",
                    "label": "Enable service on save",
                    "checked": True,
                },
            ],
        },
        "code_block_demo": {
            "language": "python",
            "code": CODE_BLOCK_SAMPLE,
        },
        "tooltip_variants": [
            {"tip": "Default top tooltip", "slot": "Hover (top)"},
            {
                "tip": "Appears below",
                "slot": "Hover (bottom)",
                "position": "bottom",
            },
            {
                "tip": "Appears right",
                "slot": "Hover (right)",
                "position": "right",
            },
            {
                "tip": "Appears left",
                "slot": "Hover (left)",
                "position": "left",
            },
        ],
        "popover_demos": [
            {
                "trigger": "Actions",
                "items": [
                    {"label": "Edit", "icon": "✏️", "href": "#"},
                    {"label": "Duplicate", "icon": "📋", "href": "#"},
                    {"divider": True},
                    {"label": "Delete", "icon": "🗑️", "href": "#", "danger": True},
                ],
            },
            {
                "trigger": "Settings ▾",
                "position": "bottom-end",
                "items": [
                    {"label": "Profile", "href": "#"},
                    {"label": "Preferences", "href": "#"},
                    {"divider": True},
                    {"label": "Sign out", "href": "#"},
                ],
            },
        ],
        "data_table_demo": {
            "title": "Services",
            "searchable": True,
            "columns": [
                {"key": "name", "label": "Name", "sortable": True},
                {"key": "host", "label": "Host"},
                {
                    "key": "status",
                    "label": "Status",
                    "sortable": True,
                    "badge": True,
                    "badge_map": {
                        "ok": "success",
                        "warn": "warn",
                        "error": "error",
                    },
                },
                {"key": "latency", "label": "Latency", "align": "right"},
            ],
            "rows": [
                {
                    "name": "api-gateway",
                    "host": "gw.internal:8080",
                    "status": "ok",
                    "latency": "12ms",
                },
                {
                    "name": "auth-service",
                    "host": "auth.internal:8081",
                    "status": "ok",
                    "latency": "8ms",
                },
                {
                    "name": "job-queue",
                    "host": "queue.internal:5672",
                    "status": "warn",
                    "latency": "45ms",
                },
                {
                    "name": "metrics-agent",
                    "host": "metrics.internal",
                    "status": "ok",
                    "latency": "3ms",
                },
                {
                    "name": "mail-relay",
                    "host": "smtp.internal:587",
                    "status": "error",
                    "latency": "—",
                },
            ],
        },
        "multi_select_demo": {
            "name": "tags",
            "label": "Tags",
            "selected": ["python", "htmx"],
            "options": [
                {"value": "python", "label": "Python"},
                {"value": "fastapi", "label": "FastAPI"},
                {"value": "htmx", "label": "HTMX"},
                {"value": "jinja2", "label": "Jinja2"},
                {"value": "postgres", "label": "PostgreSQL"},
                {"value": "redis", "label": "Redis"},
                {"value": "docker", "label": "Docker"},
            ],
            "hint": "Select all that apply",
        },
        "nav_rail_demos": [
            {
                "active_id": "dash",
                "items": [
                    {"id": "dash", "label": "Dashboard", "icon": "▦", "href": "#"},
                    {
                        "id": "svcs",
                        "label": "Services",
                        "icon": "⬡",
                        "href": "#",
                        "badge": "3",
                    },
                    {"id": "logs", "label": "Logs", "icon": "≡", "href": "#"},
                    {"divider": True},
                    {"id": "config", "label": "Config", "icon": "⚙", "href": "#"},
                    {"id": "users", "label": "Users", "icon": "◉", "href": "#"},
                ],
            },
            {
                "compact": True,
                "active_id": "dash",
                "items": [
                    {"id": "dash", "label": "Dashboard", "icon": "▦", "href": "#"},
                    {"id": "svcs", "label": "Services", "icon": "⬡", "href": "#"},
                    {"id": "logs", "label": "Logs", "icon": "≡", "href": "#"},
                    {"divider": True},
                    {"id": "config", "label": "Config", "icon": "⚙", "href": "#"},
                ],
            },
        ],
        "file_drop_demo": {
            "name": "upload",
            "label": "Drop a config file here or click to browse",
            "hint": "YAML or JSON, max 1MB",
            "accept": ".yaml,.yml,.json",
        },
        "command_palette_demo": {
            "palette_id": "demo",
            "placeholder": "Search commands…",
            "groups": [
                {
                    "label": "Navigation",
                    "items": [
                        {
                            "label": "Go to Home",
                            "icon": "🏠",
                            "href": "/",
                            "shortcut": "G H",
                        },
                        {
                            "label": "Go to Components",
                            "icon": "⬡",
                            "href": "/components",
                            "shortcut": "G C",
                        },
                        {
                            "label": "Go to About",
                            "icon": "ℹ",
                            "href": "/about",
                            "shortcut": "G A",
                        },
                    ],
                },
                {
                    "label": "Theme",
                    "items": [
                        {
                            "label": "Switch to Light",
                            "icon": "☀",
                            "href": "#",
                            "description": "RendUX.setTheme('light')",
                        },
                        {
                            "label": "Switch to Dark",
                            "icon": "☾",
                            "href": "#",
                            "description": "RendUX.setTheme('dark')",
                        },
                        {
                            "label": "System default",
                            "icon": "◑",
                            "href": "#",
                            "description": "Follows OS preference",
                        },
                    ],
                },
            ],
        },
        "tab_bar_demos": [
            {
                "active_tab": "logs",
                "tabs": [
                    {"id": "overview", "label": "Overview", "icon": "▦"},
                    {"id": "logs", "label": "Logs", "icon": "≡", "badge": "12"},
                    {"id": "metrics", "label": "Metrics", "icon": "⬡"},
                    {"id": "alerts", "label": "Alerts", "icon": "⚠"},
                ],
            },
            {
                "variant": "pill",
                "active_tab": "week",
                "tabs": [
                    {"id": "day", "label": "Day"},
                    {"id": "week", "label": "Week"},
                    {"id": "month", "label": "Month"},
                    {"id": "year", "label": "Year"},
                ],
            },
        ],
        "stepper_demos": [
            {
                "steps": [
                    {
                        "label": "Account",
                        "status": "done",
                        "description": "Email & password",
                    },
                    {
                        "label": "Profile",
                        "status": "done",
                        "description": "Display name",
                    },
                    {
                        "label": "Configure",
                        "status": "active",
                        "description": "Settings & preferences",
                    },
                    {"label": "Review", "status": "pending"},
                    {"label": "Confirm", "status": "pending"},
                ],
            },
            {
                "orientation": "vertical",
                "steps": [
                    {
                        "label": "Deploy initiated",
                        "status": "done",
                        "description": "2026-06-28 09:14",
                    },
                    {
                        "label": "Build passed",
                        "status": "done",
                        "description": "3m 42s",
                    },
                    {
                        "label": "Integration tests",
                        "status": "active",
                        "description": "Running…",
                    },
                    {"label": "Production cutover", "status": "pending"},
                ],
            },
        ],
        "timeline_events": [
            {
                "title": "Deployment complete",
                "time": "09:22",
                "status": "ok",
                "body": "v1.4.2 rolled out to all instances.",
                "tags": ["prod", "v1.4.2"],
            },
            {
                "title": "High memory alert",
                "time": "08:51",
                "status": "warn",
                "body": "api-gateway exceeding 85% memory threshold.",
            },
            {
                "title": "Scheduled maintenance",
                "time": "08:00",
                "status": "info",
                "body": "Database index rebuild started.",
            },
            {
                "title": "Build failed",
                "time": "Yesterday",
                "status": "error",
                "body": "Test suite failure in auth-service. Hotfix deployed.",
            },
            {
                "title": "Config updated",
                "time": "Yesterday",
                "status": "default",
            },
        ],
        "drawer_demos": [
            {
                "drawer_id": "demo-right",
                "title": "Service Details",
                "trigger_label": "Open Right Drawer",
                "body": (
                    "Configuration, logs, and service metadata would appear "
                    "here. The drawer body scrolls independently."
                ),
            },
            {
                "drawer_id": "demo-left",
                "side": "left",
                "title": "Navigation",
                "trigger_label": "Open Left Drawer",
                "body": (
                    "A left drawer is useful for navigation panels or "
                    "contextual menus."
                ),
            },
        ],
        "split_pane_demo": {
            "pane_id": "demo",
            "initial_primary": "45%",
            "min_primary": 140,
            "primary": SPLIT_PRIMARY,
            "secondary": SPLIT_SECONDARY,
        },
        "context_menu_demo": {
            "menu_id": "demo",
            "slot": "Right-click anywhere in this zone to open the context menu",
            "items": [
                {"label": "Open", "icon": "↗", "href": "#"},
                {"label": "Edit", "icon": "✏", "href": "#", "shortcut": "E"},
                {"label": "Duplicate", "icon": "⧉", "href": "#", "shortcut": "D"},
                {"divider": True},
                {"label": "Copy path", "icon": "⎘", "href": "#"},
                {"divider": True},
                {
                    "label": "Delete",
                    "icon": "🗑",
                    "href": "#",
                    "danger": True,
                    "shortcut": "⌫",
                },
            ],
        },
        "layout_helper_lines": (
            ".layout-grid-1 / -2 / -3 / -4 / -auto — CSS grid with gap\n"
            ".layout-stack / -sm / -lg — vertical flex column with gap\n"
            ".layout-row — horizontal flex row with wrap"
        ),
    }


def _section(
    heading: str,
    description: str,
    children: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "section",
        "heading": heading,
        "description": description,
        "children": children,
    }


def _each_widget(
    widget: str,
    ctx_key: str,
    props: dict[str, str],
) -> dict[str, Any]:
    node: dict[str, Any] = {"widget": widget, "each": f"$ctx.{ctx_key}"}
    node.update(props)
    return node


def build_layout() -> list[dict[str, Any]]:
    return [
        {"heading": "Widget Library — Tier 1", "level": 1},
        _section(
            "button",
            "Variants: primary, secondary, ghost, destructive. Sizes: sm, md, lg. "
            "Renders as <a> when href is set.",
            [
                {
                    "type": "row",
                    "children": [
                        _each_widget(
                            "button",
                            "button_variants",
                            {
                                "label": "$item.label",
                                "variant": "$item.variant",
                                "size": "$item.size",
                                "disabled": "$item.disabled",
                                "href": "$item.href",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        {
            "type": "grid",
            "columns": 2,
            "children": [
                _section(
                    "badge",
                    "Pill-shaped label. Variants: default, info, success, warn, error. "
                    "Optional dot prefix.",
                    [
                        {
                            "type": "row",
                            "children": [
                                _each_widget(
                                    "badge",
                                    "badge_variants",
                                    {
                                        "label": "$item.label",
                                        "variant": "$item.variant",
                                        "dot": "$item.dot",
                                    },
                                ),
                            ],
                        },
                    ],
                ),
                _section(
                    "tag",
                    "Rectangular inline label. Same variants as badge, distinct shape.",
                    [
                        {
                            "type": "row",
                            "children": [
                                _each_widget(
                                    "tag",
                                    "tag_variants",
                                    {
                                        "label": "$item.label",
                                        "variant": "$item.variant",
                                    },
                                ),
                            ],
                        },
                    ],
                ),
            ],
        },
        {"divider": True},
        _section(
            "alert",
            "Inline banner with icon, optional title, and message. "
            "Variants: info, success, warn, error.",
            [
                {
                    "type": "stack",
                    "children": [
                        _each_widget(
                            "alert",
                            "alert_variants",
                            {
                                "title": "$item.title",
                                "message": "$item.message",
                                "variant": "$item.variant",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        {
            "type": "grid",
            "columns": 2,
            "children": [
                _section(
                    "status_badge",
                    "Dot + label for ok/warn/error/unknown states. Inline use.",
                    [
                        {
                            "type": "stack",
                            "gap": "sm",
                            "children": [
                                _each_widget(
                                    "status_badge",
                                    "status_badge_variants",
                                    {
                                        "status": "$item.status",
                                        "label": "$item.label",
                                    },
                                ),
                            ],
                        },
                    ],
                ),
                _section(
                    "avatar",
                    "User icon from image or initials. Sizes: sm, md, lg.",
                    [
                        {
                            "type": "row",
                            "children": [
                                _each_widget(
                                    "avatar",
                                    "avatar_variants",
                                    {
                                        "name": "$item.name",
                                        "size": "$item.size",
                                    },
                                ),
                            ],
                        },
                    ],
                ),
            ],
        },
        {"divider": True},
        _section(
            "progress_bar",
            "Labeled fill bar. Variants: default, ok, warn, error.",
            [
                {
                    "type": "stack",
                    "children": [
                        _each_widget(
                            "progress_bar",
                            "progress_bar_variants",
                            {
                                "label": "$item.label",
                                "value": "$item.value",
                                "max": "$item.max",
                                "variant": "$item.variant",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "breadcrumb",
            "Path trail with / separator. Last item has no link.",
            [
                {
                    "widget": "breadcrumb",
                    "items": "$ctx.breadcrumb_items",
                },
            ],
        ),
        {"divider": True},
        {
            "type": "grid",
            "columns": 2,
            "children": [
                _section(
                    "card",
                    "Surface container with optional title and body text.",
                    [
                        {
                            "widget": "card",
                            "title": "Card title",
                            "body": (
                                "A simple card with a title and body. Use as a "
                                "base container for grouped content."
                            ),
                        },
                    ],
                ),
                _section(
                    "panel",
                    "Titled panel with distinct header, optional action buttons "
                    "in header.",
                    [
                        {
                            "widget": "panel",
                            "title": "$ctx.panel_demo.title",
                            "body": "$ctx.panel_demo.body",
                            "actions": "$ctx.panel_demo.actions",
                        },
                    ],
                ),
            ],
        },
        {"divider": True},
        _section(
            "empty_state",
            "Zero-data placeholder with optional call-to-action.",
            [
                {
                    "widget": "empty_state",
                    "title": "No results found",
                    "message": (
                        "Try adjusting your filters or add a new entry."
                    ),
                    "action_label": "Add entry",
                    "action_href": "#",
                },
            ],
        ),
        {"widget": "divider", "label": "Layout primitives below"},
        _section(
            "layout helpers",
            "CSS classes only — no widget template. Apply directly to wrapper divs.",
            [
                {
                    "widget": "code_block",
                    "language": "text",
                    "code": "$ctx.layout_helper_lines",
                },
            ],
        ),
        {"widget": "divider", "label": "Tier 2 — HTMX-assisted"},
        _section(
            "collapsible",
            "Native <details>/<summary> — no JS, no HTMX. Open state persists on page.",
            [
                {
                    "type": "stack",
                    "gap": "sm",
                    "children": [
                        _each_widget(
                            "collapsible",
                            "collapsible_variants",
                            {
                                "title": "$item.title",
                                "body": "$item.body",
                                "open": "$item.open",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "tabs",
            "HTMX tab bar — each tab loads its panel from a partial URL on demand.",
            [
                {
                    "widget": "tabs",
                    "tabs": "$ctx.tabs_demo.tabs",
                    "target": "$ctx.tabs_demo.target",
                    "initial_content": "$ctx.tabs_demo.initial_content",
                },
            ],
        ),
        {"divider": True},
        _section(
            "toast",
            "Ephemeral notification injected into the shell's toast container via "
            "HTMX OOB swap.",
            [
                {
                    "type": "row",
                    "children": [
                        _each_widget(
                            "button",
                            "toast_buttons",
                            {
                                "label": "$item.label",
                                "variant": "$item.variant",
                                "size": "$item.size",
                                "hx_get": "$item.hx_get",
                                "hx_target": "$item.hx_target",
                                "hx_swap": "$item.hx_swap",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "modal",
            "Native HTML <dialog> element. No JS framework needed — just showModal() "
            "on trigger click.",
            [
                {
                    "widget": "modal",
                    "id": "$ctx.modal_demo.id",
                    "title": "$ctx.modal_demo.title",
                    "trigger_label": "$ctx.modal_demo.trigger_label",
                    "body": "$ctx.modal_demo.body",
                    "confirm_label": "$ctx.modal_demo.confirm_label",
                    "cancel_label": "$ctx.modal_demo.cancel_label",
                },
            ],
        ),
        {"divider": True},
        _section(
            "skeleton",
            "Animated loading placeholder. Use as a placeholder while HTMX loads "
            "real content.",
            [
                {
                    "type": "grid",
                    "columns": 2,
                    "children": [
                        _each_widget(
                            "skeleton",
                            "skeleton_variants",
                            {"lines": "$item.lines"},
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "pagination",
            "Prev/next + numbered pages. HTMX-optional via target param. "
            "Ellipsis at range edges.",
            [
                {
                    "widget": "pagination",
                    "current": "$ctx.pagination_demo.current",
                    "total": "$ctx.pagination_demo.total",
                    "url_pattern": "$ctx.pagination_demo.url_pattern",
                },
            ],
        ),
        {"divider": True},
        _section(
            "form",
            "Form wrapper with labeled fields. Types: text, email, password, "
            "textarea, select, checkbox. HTMX-submittable via hx_post.",
            [
                {
                    "widget": "form",
                    "action": "$ctx.form_demo.action",
                    "submit_label": "$ctx.form_demo.submit_label",
                    "cancel_href": "$ctx.form_demo.cancel_href",
                    "fields": "$ctx.form_demo.fields",
                },
            ],
        ),
        {"divider": True},
        _section(
            "theme_switcher",
            "Light / System / Dark toggle plus any custom themes from "
            "config/themes.yaml. Persists to localStorage. Anti-FOUC applied on "
            "page load.",
            [{"widget": "theme_switcher"}],
        ),
        {"divider": True},
        {"heading": "Widget Library — Tier 3", "level": 1},
        _section(
            "code_block",
            "Syntax-labeled code block with one-click copy. Language label from "
            "language param. Copy button resets after 1.5s.",
            [
                {
                    "widget": "code_block",
                    "language": "$ctx.code_block_demo.language",
                    "code": "$ctx.code_block_demo.code",
                },
            ],
        ),
        {"divider": True},
        _section(
            "tooltip",
            "Pure-CSS tooltip via data-tip + pseudo-elements. Positions: top "
            "(default), bottom, left, right. No JS.",
            [
                {
                    "type": "row",
                    "children": [
                        _each_widget(
                            "tooltip",
                            "tooltip_variants",
                            {
                                "tip": "$item.tip",
                                "slot": "$item.slot",
                                "position": "$item.position",
                            },
                        ),
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "popover",
            "Positioned dropdown using native <details>. Supports menu items list "
            "or free-form body. Positions: bottom-start (default), bottom-end, "
            "top-start, top-end.",
            [
                {
                    "type": "row",
                    "children": [
                        {
                            "widget": "popover",
                            "each": "$ctx.popover_demos",
                            "trigger": "$item.trigger",
                            "position": "$item.position",
                            "items": "$item.items",
                        },
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "data_table",
            "Sortable, searchable table. Client-side search via JS; server-side "
            "sort via HTMX when sort_url is set. Supports badge columns via "
            "badge_map.",
            [
                {
                    "widget": "data_table",
                    "title": "$ctx.data_table_demo.title",
                    "searchable": "$ctx.data_table_demo.searchable",
                    "columns": "$ctx.data_table_demo.columns",
                    "rows": "$ctx.data_table_demo.rows",
                },
            ],
        ),
        {"divider": True},
        _section(
            "multi_select",
            "Filterable checkbox list. Filter input narrows options client-side. "
            "Works as a standard form field via name param.",
            [
                {
                    "widget": "multi_select",
                    "name": "$ctx.multi_select_demo.name",
                    "label": "$ctx.multi_select_demo.label",
                    "selected": "$ctx.multi_select_demo.selected",
                    "options": "$ctx.multi_select_demo.options",
                    "hint": "$ctx.multi_select_demo.hint",
                },
            ],
        ),
        {"divider": True},
        _section(
            "nav_rail",
            "Vertical sidebar navigation. Full and compact (icon-only) variants. "
            "Supports badges, dividers, and HTMX partial loading via hx_get.",
            [
                {
                    "type": "row",
                    "children": [
                        {
                            "widget": "nav_rail",
                            "each": "$ctx.nav_rail_demos",
                            "active_id": "$item.active_id",
                            "compact": "$item.compact",
                            "items": "$item.items",
                        },
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "file_drop",
            'Drag-and-drop file zone backed by a native <input type="file">. '
            "Highlights on drag-over. Shows selected filenames. No external deps.",
            [
                {
                    "widget": "file_drop",
                    "name": "$ctx.file_drop_demo.name",
                    "label": "$ctx.file_drop_demo.label",
                    "hint": "$ctx.file_drop_demo.hint",
                    "accept": "$ctx.file_drop_demo.accept",
                },
            ],
        ),
        {"divider": True},
        _section(
            "command_palette",
            "Keyboard-driven command search. Opens on ⌘K or the trigger button. "
            "Arrow keys navigate, Enter follows the link, Escape closes. "
            "Filtered client-side.",
            [
                {
                    "widget": "command_palette",
                    "palette_id": "$ctx.command_palette_demo.palette_id",
                    "placeholder": "$ctx.command_palette_demo.placeholder",
                    "groups": "$ctx.command_palette_demo.groups",
                },
            ],
        ),
        {"divider": True},
        _section(
            "tab_bar",
            "Standalone tab bar, decoupled from content. Underline (default) and "
            "pill variants. HTMX partial-swap or href routing.",
            [
                {
                    "type": "stack",
                    "gap": "sm",
                    "children": [
                        {
                            "widget": "tab_bar",
                            "each": "$ctx.tab_bar_demos",
                            "active_tab": "$item.active_tab",
                            "variant": "$item.variant",
                            "tabs": "$item.tabs",
                        },
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "stepper",
            "Multi-step progress indicator. Horizontal (default) and vertical "
            "orientations. Step statuses: done, active, pending, error.",
            [
                {
                    "type": "stack",
                    "children": [
                        {
                            "widget": "stepper",
                            "each": "$ctx.stepper_demos",
                            "orientation": "$item.orientation",
                            "steps": "$item.steps",
                        },
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "timeline",
            "Vertical event stream. Status nodes: ok, warn, error, info, default. "
            "Optional tags via tag widget inclusion.",
            [
                {
                    "widget": "timeline",
                    "events": "$ctx.timeline_events",
                },
            ],
        ),
        {"divider": True},
        _section(
            "drawer",
            "Slide-in side panel using native <dialog>. Click outside or ✕ to close. "
            "Left and right variants. Animated entry.",
            [
                {
                    "type": "row",
                    "children": [
                        {
                            "widget": "drawer",
                            "each": "$ctx.drawer_demos",
                            "drawer_id": "$item.drawer_id",
                            "side": "$item.side",
                            "title": "$item.title",
                            "trigger_label": "$item.trigger_label",
                            "body": "$item.body",
                        },
                    ],
                },
            ],
        ),
        {"divider": True},
        _section(
            "split_pane",
            "Draggable two-panel layout. Drag the center handle to resize. Min/max "
            "constraints via min_primary / max_primary params.",
            [
                {
                    "widget": "split_pane",
                    "pane_id": "$ctx.split_pane_demo.pane_id",
                    "initial_primary": "$ctx.split_pane_demo.initial_primary",
                    "min_primary": "$ctx.split_pane_demo.min_primary",
                    "primary": "$ctx.split_pane_demo.primary",
                    "secondary": "$ctx.split_pane_demo.secondary",
                },
            ],
        ),
        {"divider": True},
        _section(
            "context_menu",
            "Right-click positioned menu. Stays within viewport. Escape or "
            "click-outside to dismiss. Supports danger items and keyboard shortcuts.",
            [
                {
                    "widget": "context_menu",
                    "menu_id": "$ctx.context_menu_demo.menu_id",
                    "slot": "$ctx.context_menu_demo.slot",
                    "items": "$ctx.context_menu_demo.items",
                },
            ],
        ),
    ]


def _resolve_ctx_list(data: dict[str, Any], ref: str) -> list[Any] | None:
    if not ref.startswith("$ctx."):
        return None
    keys = ref[len("$ctx.") :].split(".")
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value if isinstance(value, list) else None


def count_widgets(
    nodes: list[dict[str, Any]],
    data: dict[str, Any],
) -> int:
    total = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        if node.get("divider") is True:
            continue
        if "heading" in node and "type" not in node:
            continue
        if "widget" in node:
            each_ref = node.get("each")
            if isinstance(each_ref, str):
                items = _resolve_ctx_list(data, each_ref)
                total += len(items) if items is not None else 1
            else:
                total += 1
            continue
        if node.get("type") in {"stack", "row", "grid", "section", "split"}:
            children = node.get("children", [])
            if node.get("type") == "split":
                children = node.get("primary", []) + node.get("secondary", [])
            total += count_widgets(children, data)
    return total


def build_showcase() -> dict[str, Any]:
    data = build_data()
    layout = build_layout()
    return {"data": data, "workspace": {"layout": layout}}


def main() -> int:
    showcase = build_showcase()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        yaml.safe_dump(
            showcase,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=100,
        ),
        encoding="utf-8",
    )
    widget_count = count_widgets(showcase["workspace"]["layout"], showcase["data"])
    print(f"Wrote {OUTPUT} ({widget_count} widget invocations in layout)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
