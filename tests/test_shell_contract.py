from __future__ import annotations

from fastapi.testclient import TestClient

from demo.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_home_view_renders_app_shell():
    client = _client()
    response = client.get("/")
    assert response.status_code == 200
    assert 'class="app-shell"' in response.text


def test_home_view_renders_workspace():
    client = _client()
    response = client.get("/")
    assert 'id="workspace"' in response.text


def test_home_view_renders_nav():
    client = _client()
    response = client.get("/")
    assert 'class="shell-nav"' in response.text
    assert "Home" in response.text
    assert "Components" in response.text
    assert "About" in response.text


def test_all_views_render_shell():
    client = _client()
    for path in ("/", "/components", "/about"):
        response = client.get(path)
        assert response.status_code == 200
        assert 'class="app-shell"' in response.text, path


def test_all_views_set_active_view_attribute():
    client = _client()
    cases = [("/", "home"), ("/components", "components"), ("/about", "about")]
    for path, view_id in cases:
        response = client.get(path)
        assert f'data-active-view="{view_id}"' in response.text, path


def test_all_views_set_shell_attribute():
    client = _client()
    for path in ("/", "/components", "/about"):
        response = client.get(path)
        assert 'data-shell="default"' in response.text, path


def test_htmx_request_returns_partial_only():
    client = _client()
    response = client.get("/", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert 'class="app-shell"' not in response.text
    assert 'widget-stat-card' in response.text


def test_htmx_components_returns_partial():
    client = _client()
    response = client.get("/components", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert 'class="app-shell"' not in response.text
    assert "Widget Library" in response.text


def test_health_endpoint():
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "rendux-demo"
