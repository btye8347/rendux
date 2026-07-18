"""Packaging and public API smoke tests for 0.1 beta."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from starlette.testclient import TestClient

import rendux
from rendux.core.contracts import load_widget_registry
from rendux.integration import configure_app, render_view
from rendux.paths import catalog_verified_path, contracts_dir, static_dir, templates_dir

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_version_is_beta():
    assert rendux.__version__ == "0.1.0b1"


def test_paths_resolve():
    assert templates_dir().is_dir()
    assert (templates_dir() / "widgets" / "stat_card.html").is_file()
    assert static_dir().is_dir()
    assert (static_dir() / "css" / "app.css").is_file()
    assert contracts_dir().is_dir()
    assert (contracts_dir() / "widgets" / "stat_card.json").is_file()
    assert catalog_verified_path().is_file()


def test_registry_loads_via_paths():
    registry = load_widget_registry()
    assert "stat_card" in registry
    assert registry["stat_card"]["status"] == "verified"


def test_configure_app_and_render_consumer_example():
    app = FastAPI()
    configure_app(
        app,
        views_yaml=PROJECT_ROOT / "examples" / "consumer" / "config" / "views.yaml",
    )

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        return render_view(request, "home", "Consumer Home")

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200, response.text
    assert "Consumer app" in response.text
    assert "Private dependency" in response.text


def test_wheel_build_includes_contracts():
    dist = PROJECT_ROOT / "dist"
    # Clean only our test artifacts if present; uv build writes here
    result = subprocess.run(
        [sys.executable, "-m", "hatchling", "build"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Fallback: uv build
        result = subprocess.run(
            ["uv", "build"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
    assert result.returncode == 0, result.stdout + result.stderr

    wheels = list(dist.glob("rendux-*.whl"))
    assert wheels, "expected a wheel in dist/"
    import zipfile

    with zipfile.ZipFile(wheels[-1]) as zf:
        names = zf.namelist()
    assert any(n.startswith("rendux/contracts/widgets/") for n in names)
    assert any(n.endswith("stat_card.json") for n in names)
    assert any("templates/widgets/stat_card.html" in n for n in names)
