from __future__ import annotations

from logging import getLogger
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from rendux.core.responses import api_envelope

logger = getLogger("rendux.views")

router = APIRouter()


@router.get("/api/views")
def views(request: Request) -> dict[str, Any]:
    service = request.app.state.services.get("views")
    view_list = service.list_views() if service else []
    return api_envelope(
        capability="views",
        operation="list",
        data={"views": view_list},
        source="rendux.views",
        count=len(view_list),
    )


@router.get("/api/views/{view_id}")
def view(request: Request, view_id: str) -> dict[str, Any]:
    service = request.app.state.services.get("views")
    if not service:
        raise HTTPException(status_code=404, detail="View service not available")
    try:
        view_config = service.get_view(view_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="View not found") from exc
    return api_envelope(
        capability="views",
        operation="get",
        data={"view": view_config},
        source="rendux.views",
    )


@router.get("/views/{view_id}", response_class=HTMLResponse)
def view_fallback(request: Request, view_id: str) -> HTMLResponse:
    service = request.app.state.services.get("views")
    status_code = 200

    try:
        view_config = service.get_view(view_id) if service else None
        if not view_config:
            raise KeyError(view_id)
        shell = service.get_shell_view(view_id)
    except KeyError:
        status_code = 404
        shell = service.get_shell_fallback(view_id) if service else {
            "shell_id": "default",
            "active_view": {"id": view_id},
            "nav_items": [],
            "routes": {},
            "surfaces": [],
        }
        return request.app.state.templates.TemplateResponse(
            request,
            "chrome/shells/default.html",
            {
                "view_shell": shell,
                "title": "View not found",
            },
            status_code=status_code,
        )

    return request.app.state.templates.TemplateResponse(
        request,
        "chrome/shells/default.html",
        {
            "view_shell": shell,
            "title": shell.get("label", view_id),
        },
        status_code=status_code,
    )
