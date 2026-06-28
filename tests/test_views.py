from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rendux.views.service import ViewConfigError, ViewConfigService
from demo.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "views.yaml"
FIXTURE_GOOD = Path(__file__).parent / "fixtures" / "views_good.yaml"


def test_view_config_service_loads_configured_views():
    service = ViewConfigService.from_yaml(CONFIG_PATH)

    views = service.list_views()

    assert {v["id"] for v in views} == {"home", "components", "ops", "about"}
    home = next(v for v in views if v["id"] == "home")
    assert home["label"] == "Home"
    assert home["route"] == "/"


def test_view_config_service_rejects_missing_version():
    with pytest.raises(ViewConfigError):
        ViewConfigService({})


def test_view_config_service_rejects_missing_views():
    with pytest.raises(ViewConfigError):
        ViewConfigService({"version": "0.1.0"})


def test_view_config_service_accepts_shell_configured_template():
    service = ViewConfigService.from_yaml(CONFIG_PATH)
    config = deepcopy(service.get_config())
    config["shell"]["template"] = "chrome/shells/blank.html"

    shell = ViewConfigService(config).get_shell_view("home")

    assert shell["template"] == "chrome/shells/blank.html"


def test_view_config_service_injects_active_view_routes_and_nav():
    service = ViewConfigService.from_yaml(CONFIG_PATH)

    shell = service.get_shell_view("home")

    assert shell["active_view"]["id"] == "home"
    assert shell["routes"]["home"] == "/"
    assert shell["shell_id"] == "default"
    assert any(item["id"] == "home" for item in shell["nav_items"])
    assert any(item["id"] == "components" for item in shell["nav_items"])
    assert any(item["id"] == "about" for item in shell["nav_items"])


def test_view_config_service_builds_not_found_shell_model():
    service = ViewConfigService.from_yaml(CONFIG_PATH)

    shell = service.get_shell_fallback("missing-view")

    assert shell["active_view"]["id"] == "missing-view"
    assert shell["active_view"]["label"] == "View not found"
    assert shell["routes"]["home"] == "/"


def test_views_json_route_lists_views():
    client = TestClient(create_app())

    response = client.get("/api/views")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api"]["capability"] == "views"
    assert payload["api"]["operation"] == "list"
    assert payload["meta"]["source"] == "rendux.views"
    assert payload["meta"]["mcp"]["tool_name"] == "rendux.views.list"
    assert payload["errors"] == []
    view_ids = {v["id"] for v in payload["data"]["views"]}
    assert view_ids == {"home", "components", "ops", "about"}


def test_single_view_json_route_returns_view_config():
    client = TestClient(create_app())

    response = client.get("/api/views/home")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api"]["capability"] == "views"
    assert payload["api"]["operation"] == "get"
    assert payload["meta"]["mcp"]["tool_name"] == "rendux.views.get"
    assert payload["data"]["view"]["id"] == "home"


def test_single_view_json_route_returns_404_for_unknown_view():
    client = TestClient(create_app())

    response = client.get("/api/views/not-a-view")

    assert response.status_code == 404


def test_view_fallback_renders_shell_for_unknown_view():
    client = TestClient(create_app())

    response = client.get("/views/not-a-view")

    assert response.status_code == 404
    assert 'class="app-shell"' in response.text
    assert 'id="workspace"' in response.text
