"""Chat widget + /chat demo."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from starlette.testclient import TestClient

from demo.main import create_app
from rendux.core.agent_compile import compile_fragment
from rendux.core.layout import LayoutRenderer
from rendux.core.lint_rdl import lint_views_file
from rendux.views.service import ViewConfigService

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIEWS_PATH = PROJECT_ROOT / "config" / "views.yaml"


def test_chat_view_passes_strict_lint():
    errors = [i for i in lint_views_file(VIEWS_PATH, strict=True) if i.level == "error"]
    assert errors == [], "\n".join(f"{e.path}: {e.message}" for e in errors)


def test_chat_http_renders_thread_and_composer():
    client = TestClient(create_app())
    response = client.get("/chat")
    assert response.status_code == 200
    assert "widget-chat" in response.text
    assert "chat-composer" in response.text
    assert "What widgets are verified" in response.text
    assert 'hx-post="/partials/chat/send"' in response.text


def test_chat_send_appends_message_pair():
    client = TestClient(create_app())
    response = client.post(
        "/partials/chat/send",
        data={"message": "Hello RendUX"},
    )
    assert response.status_code == 200
    assert "chat-message-user" in response.text
    assert "Hello RendUX" in response.text
    assert "chat-message-assistant" in response.text
    assert "Echo (demo)" in response.text


def test_chat_strict_render():
    svc = ViewConfigService.from_yaml(VIEWS_PATH)
    ws = svc.resolve_workspace("chat")
    renderer = LayoutRenderer(
        Environment(
            loader=FileSystemLoader(str(PROJECT_ROOT / "rendux" / "templates")),
            autoescape=True,
        ),
        strict=True,
    )
    html = renderer.render(ws["value"], svc.view_data("chat"))
    assert "chat-message-streaming" in html
    assert "demo-chat" in html


def test_chat_fragment_compiles():
    import yaml

    fragment = yaml.safe_load((PROJECT_ROOT / "config" / "chat_demo.yaml").read_text())
    report = compile_fragment(fragment)
    assert report["ok"] is True, report["errors"]
