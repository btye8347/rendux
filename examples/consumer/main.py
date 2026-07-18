"""Minimal FastAPI host using RendUX as an installed package."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from rendux.integration import configure_app, render_view

ROOT = Path(__file__).resolve().parent

app = FastAPI(title="RendUX Consumer Example")
configure_app(app, views_yaml=ROOT / "config" / "views.yaml")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return render_view(request, "home", "Consumer Home")
