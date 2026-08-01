from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from rendux import __version__
from rendux.core.layout import LayoutConfigError, LayoutRenderer
from rendux.integration import configure_app, create_templates, render_view
from rendux.views.service import ViewConfigService

from demo.ops_context import build_ops_view_ctx

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

templates = create_templates(PACKAGE_ROOT / "templates")


def create_app() -> FastAPI:
    app = FastAPI(title="RendUX Demo", version=__version__)

    configure_app(
        app,
        views_yaml=PROJECT_ROOT / "config" / "views.yaml",
        themes_yaml=PROJECT_ROOT / "config" / "themes.yaml",
        templates=templates,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rendux-demo", "version": __version__}

    @app.get("/api/themes", response_class=JSONResponse)
    def api_themes(request: Request) -> JSONResponse:
        svc = request.app.state.services.get("themes")
        return JSONResponse({"themes": svc.list_themes()})

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return render_view(request, "home", "Home", templates=templates)

    @app.get("/components", response_class=HTMLResponse)
    def components(request: Request) -> HTMLResponse:
        return render_view(request, "components", "Components", templates=templates)

    @app.get("/services", response_class=HTMLResponse)
    def services(request: Request) -> HTMLResponse:
        return render_view(request, "services", "Services", templates=templates)

    @app.get("/chat", response_class=HTMLResponse)
    def chat(request: Request) -> HTMLResponse:
        return render_view(request, "chat", "Chat", templates=templates)

    @app.get("/ops", response_class=HTMLResponse)
    def ops(request: Request) -> HTMLResponse:
        return render_view(
            request,
            "ops",
            "Operations",
            view_ctx=_ops_view_ctx(request),
            templates=templates,
        )

    @app.get("/about", response_class=HTMLResponse)
    def about(request: Request) -> HTMLResponse:
        return render_view(request, "about", "About", templates=templates)

    @app.get("/partials/ops/{fragment_id}", response_class=HTMLResponse)
    def ops_partial(request: Request, fragment_id: str) -> HTMLResponse:
        views: ViewConfigService = request.app.state.services.get("views")
        renderer: LayoutRenderer = request.app.state.services.get("layout_renderer")
        ws = views.resolve_workspace("ops")
        if ws["kind"] != "layout":
            return HTMLResponse("Not found", status_code=404)

        try:
            html = renderer.render_fragment(
                ws["value"],
                fragment_id,
                _ops_render_ctx(request),
            )
        except LayoutConfigError:
            return HTMLResponse("Not found", status_code=404)
        return HTMLResponse(html)

    @app.get("/partials/tab/{tab_id}", response_class=HTMLResponse)
    def tab_partial(request: Request, tab_id: str) -> HTMLResponse:
        template_map = {
            "overview": "partials/tab_overview.html",
            "config": "partials/tab_config.html",
            "code": "partials/tab_code.html",
        }
        tmpl = template_map.get(tab_id)
        if not tmpl:
            return HTMLResponse("<p>Tab not found.</p>", status_code=404)
        return templates.TemplateResponse(request, tmpl, {})

    @app.get("/partials/toast", response_class=HTMLResponse)
    def toast_partial(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "widgets/toast.html",
            {
                "message": request.query_params.get("message", "Action complete."),
                "variant": request.query_params.get("variant", "success"),
                "title": request.query_params.get("title", ""),
            },
        )

    @app.post("/partials/chat/send", response_class=HTMLResponse)
    async def chat_send(request: Request) -> HTMLResponse:
        """Demo host endpoint — append user + mock assistant bubbles."""
        form = await request.form()
        text = str(form.get("message") or "").strip()
        if not text:
            return HTMLResponse("", status_code=204)

        now = datetime.now().strftime("%H:%M")
        user_id = uuid.uuid4().hex[:8]
        asst_id = uuid.uuid4().hex[:8]
        user_html = templates.env.get_template("widgets/chat_message.html").render(
            id=user_id,
            role="user",
            content=text,
            time=now,
            status="complete",
        )
        asst_html = templates.env.get_template("widgets/chat_message.html").render(
            id=asst_id,
            role="assistant",
            content=f"Echo (demo): {text}",
            time=now,
            meta="assistant",
            status="complete",
        )
        return HTMLResponse(user_html + asst_html)

    return app


def _ops_view_ctx(request: Request) -> dict:
    views: ViewConfigService = request.app.state.services.get("views")
    return build_ops_view_ctx(views.view_data("ops"))


def _ops_render_ctx(request: Request) -> dict:
    views: ViewConfigService = request.app.state.services.get("views")
    return {
        **dict(templates.env.globals),
        **views.view_data("ops"),
        **_ops_view_ctx(request),
    }


app = create_app()
