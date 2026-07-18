"""Helpers for embedding RendUX in a host FastAPI application."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rendux.core.layout import LayoutRenderer
from rendux.core.registries import register_core_services
from rendux.core.themes import ThemeService
from rendux.paths import static_dir, templates_dir
from rendux.views.routes import router as views_router
from rendux.views.service import ViewConfigService


def create_templates(
    *extra_dirs: Path | str,
) -> Jinja2Templates:
    """Jinja environment with RendUX templates first, then host overrides."""
    directories = [str(templates_dir()), *[str(p) for p in extra_dirs]]
    return Jinja2Templates(directory=directories)


def configure_app(
    app: FastAPI,
    *,
    views_yaml: Path | str,
    themes_yaml: Path | str | None = None,
    templates: Jinja2Templates | None = None,
    extra_template_dirs: list[Path | str] | None = None,
    strict: bool | None = None,
    mount_static_at: str | None = "/static",
    include_views_api: bool = True,
) -> Jinja2Templates:
    """Wire RendUX services onto a FastAPI app.

    Parameters
    ----------
    views_yaml:
        Host app path to ``views.yaml`` (and its ``include:`` fragments).
    themes_yaml:
        Optional themes config. If omitted, theme list/CSS stay empty.
    templates:
        Existing Jinja2Templates; created if omitted.
    strict:
        LayoutRenderer strict mode. Defaults to ``RENDUX_STRICT`` env.
    mount_static_at:
        Mount point for RendUX static assets, or ``None`` to skip.
    include_views_api:
        Include the built-in ``/api/views…`` router.
    """
    if templates is None:
        templates = create_templates(*(extra_template_dirs or []))

    if not hasattr(app.state, "services"):
        registries = register_core_services()
        app.state.services = registries.services
        app.state.capabilities = registries.capabilities
        app.state.adapters = registries.adapters

    app.state.templates = templates

    views_service = ViewConfigService.from_yaml(Path(views_yaml))
    views_service.compile_models()
    app.state.services.register("views", views_service)

    if themes_yaml is not None:
        theme_service = ThemeService.from_yaml(Path(themes_yaml))
        app.state.services.register("themes", theme_service)
        templates.env.globals["theme_list"] = theme_service.list_themes()
        templates.env.globals["custom_theme_css"] = theme_service.generate_css()
    else:
        templates.env.globals.setdefault("theme_list", [])
        templates.env.globals.setdefault("custom_theme_css", "")

    if strict is None:
        strict = os.environ.get("RENDUX_STRICT", "").lower() in ("1", "true", "yes")
    app.state.services.register("layout_renderer", LayoutRenderer(templates.env, strict=strict))

    asset = static_dir() / "css" / "app.css"
    templates.env.globals["static_version"] = (
        str(asset.stat().st_mtime_ns) if asset.exists() else "1"
    )

    if mount_static_at:
        app.mount(mount_static_at, StaticFiles(directory=static_dir()), name="static")

    if include_views_api:
        app.include_router(views_router)

    return templates


def render_view(
    request: Request,
    view_id: str,
    title: str,
    *,
    view_ctx: dict[str, Any] | None = None,
    templates: Jinja2Templates | None = None,
) -> HTMLResponse:
    """Render a configured view (layout or template workspace).

    ``view_ctx`` is merged after YAML ``data:`` (route-level wins).
    """
    tmpl = templates or request.app.state.templates
    svc: ViewConfigService = request.app.state.services.get("views")
    shell = svc.get_shell_view(view_id)
    ws = svc.resolve_workspace(view_id)

    if ws["kind"] == "layout":
        renderer: LayoutRenderer = request.app.state.services.get("layout_renderer")
        render_ctx = {
            **dict(tmpl.env.globals),
            **svc.view_data(view_id),
            **(view_ctx or {}),
        }
        layout_html = renderer.render(ws["value"], render_ctx)
        workspace_template = "workspaces/_declarative.html"
        ctx: dict[str, Any] = {
            "view_shell": shell,
            "title": title,
            "layout_html": layout_html,
        }
    else:
        workspace_template = ws["value"]
        ctx = {"view_shell": shell, "title": title}

    if request.headers.get("HX-Request"):
        return tmpl.TemplateResponse(request, workspace_template, ctx)

    return tmpl.TemplateResponse(
        request,
        "chrome/shells/default.html",
        {**ctx, "workspace_template": workspace_template},
    )


def view_route(
    view_id: str,
    title: str,
    *,
    view_ctx_factory: Callable[[Request], dict[str, Any] | None] | None = None,
) -> Callable[..., HTMLResponse]:
    """Build a FastAPI endpoint that renders ``view_id``."""

    def endpoint(request: Request) -> HTMLResponse:
        ctx = view_ctx_factory(request) if view_ctx_factory else None
        return render_view(request, view_id, title, view_ctx=ctx)

    endpoint.__name__ = f"rendux_view_{view_id}"
    endpoint.__doc__ = f"RendUX view: {view_id}"
    return endpoint
