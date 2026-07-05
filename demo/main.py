from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rendux.core.layout import LayoutRenderer
from rendux.core.registries import register_core_services
from rendux.core.themes import ThemeService
from rendux.views.routes import router as views_router
from rendux.views.service import ViewConfigService

from demo.ops_context import build_ops_view_ctx

PACKAGE_ROOT = Path(__file__).resolve().parent
RENDUX_ROOT  = PACKAGE_ROOT.parent / "rendux"
PROJECT_ROOT = PACKAGE_ROOT.parent

templates = Jinja2Templates(
    directory=[
        str(RENDUX_ROOT / "templates"),
        str(PACKAGE_ROOT / "templates"),
    ]
)


def _static_version() -> str:
    asset = RENDUX_ROOT / "static" / "css" / "app.css"
    return str(asset.stat().st_mtime_ns) if asset.exists() else "1"


def create_app() -> FastAPI:
    templates.env.globals["static_version"] = _static_version()

    app = FastAPI(title="RendUX Demo", version="0.1.0")

    registries = register_core_services()
    app.state.services   = registries.services
    app.state.capabilities = registries.capabilities
    app.state.adapters   = registries.adapters
    app.state.templates  = templates

    views_service = ViewConfigService.from_yaml(PROJECT_ROOT / "config" / "views.yaml")
    views_service.compile_models()
    app.state.services.register("views", views_service)

    theme_service = ThemeService.from_yaml(PROJECT_ROOT / "config" / "themes.yaml")
    app.state.services.register("themes", theme_service)

    renderer = LayoutRenderer(
        templates.env,
        strict=os.environ.get("RENDUX_STRICT", "").lower() in ("1", "true", "yes"),
    )
    app.state.services.register("layout_renderer", renderer)

    templates.env.globals["theme_list"]       = theme_service.list_themes()
    templates.env.globals["custom_theme_css"] = theme_service.generate_css()

    app.mount("/static", StaticFiles(directory=RENDUX_ROOT / "static"), name="static")
    app.include_router(views_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rendux-demo", "version": "0.1.0"}

    @app.get("/api/themes", response_class=JSONResponse)
    def api_themes(request: Request) -> JSONResponse:
        svc: ThemeService = request.app.state.services.get("themes")
        return JSONResponse({"themes": svc.list_themes()})

    # ── views — template path is read from views.yaml, not hardcoded ────────

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return _render_view(request, "home", "Home")

    @app.get("/components", response_class=HTMLResponse)
    def components(request: Request) -> HTMLResponse:
        return _render_view(request, "components", "Components")

    @app.get("/ops", response_class=HTMLResponse)
    def ops(request: Request) -> HTMLResponse:
        views: ViewConfigService = request.app.state.services.get("views")
        static = views.view_data("ops")
        return _render_view(
            request,
            "ops",
            "Operations",
            view_ctx=build_ops_view_ctx(static),
        )

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request) -> HTMLResponse:
        return _render_view(request, "about", "About")

    # ── partials ─────────────────────────────────────────────────────────────

    @app.get("/partials/tab/{tab_id}", response_class=HTMLResponse)
    def tab_partial(request: Request, tab_id: str) -> HTMLResponse:
        template_map = {
            "overview": "partials/tab_overview.html",
            "config":   "partials/tab_config.html",
            "code":     "partials/tab_code.html",
        }
        tmpl = template_map.get(tab_id)
        if not tmpl:
            return HTMLResponse("<p>Tab not found.</p>", status_code=404)
        return templates.TemplateResponse(request, tmpl, {})

    @app.get("/partials/toast", response_class=HTMLResponse)
    def toast_partial(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request, "widgets/toast.html",
            {
                "message": request.query_params.get("message", "Action complete."),
                "variant": request.query_params.get("variant", "success"),
                "title":   request.query_params.get("title", ""),
            },
        )

    return app


def _render_view(
    request: Request,
    view_id: str,
    title: str,
    view_ctx: dict | None = None,
) -> HTMLResponse:
    """
    Render a view — auto-detects declarative layout vs explicit template.

    ``view_ctx`` lets route handlers inject request-time data into the RDL
    render context so that ``$ctx.*`` references resolve correctly.  It is
    merged after ``view.data`` (static YAML data), so route-level data wins.
    """
    svc: ViewConfigService = request.app.state.services.get("views")
    shell = svc.get_shell_view(view_id)
    ws    = svc.resolve_workspace(view_id)

    if ws["kind"] == "layout":
        renderer: LayoutRenderer = request.app.state.services.get("layout_renderer")
        # Build render context: template globals < YAML data: block < caller data
        render_ctx = {
            **dict(templates.env.globals),
            **svc.view_data(view_id),
            **(view_ctx or {}),
        }
        layout_html        = renderer.render(ws["value"], render_ctx)
        workspace_template = "workspaces/_declarative.html"
        ctx = {"view_shell": shell, "title": title, "layout_html": layout_html}
    else:
        workspace_template = ws["value"]
        ctx = {"view_shell": shell, "title": title}

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, workspace_template, ctx)

    return templates.TemplateResponse(
        request,
        "chrome/shells/default.html",
        {**ctx, "workspace_template": workspace_template},
    )


app = create_app()
