from __future__ import annotations

from rendux.core.mapper import DataMapper


def test_resolve_path():
    data = {
        "user": {"profile": {"first_name": "Alice"}},
        "tags": ["admin", "editor"],
    }
    assert DataMapper.resolve_path(data, "user.profile.first_name") == "Alice"
    assert DataMapper.resolve_path(data, "tags.0") == "admin"
    assert DataMapper.resolve_path(data, "tags.1") == "editor"
    assert DataMapper.resolve_path(data, "tags.2") is None
    assert DataMapper.resolve_path(data, "user.profile.last_name") is None
    assert DataMapper.resolve_path(data, "$") == data


def test_map_list():
    raw_data = {
        "tasks": [
            {"task_id": 101, "task_title": "Fix bug", "details": "High priority bug", "priority": "high"},
            {"task_id": 102, "task_title": "Write test", "details": "Integration tests", "priority": "medium"},
        ]
    }
    mappings = {
        "items_path": "tasks",
        "id": "task_id",
        "title": "task_title",
        "description": "details",
        "tags": [{"path": "priority", "label": "Priority"}],
    }

    mapped = DataMapper.map_list(raw_data, mappings)
    assert len(mapped) == 2
    assert mapped[0] == {
        "id": "101",
        "title": "Fix bug",
        "description": "High priority bug",
        "meta": None,
        "subtext": None,
        "open_url": None,
        "data_attrs": {},
        "tags": [{"name": "Priority", "value": "high"}],
    }
    assert mapped[1]["id"] == "102"


def test_map_grid():
    raw_data = [
        {
            "category": "infra",
            "name": "Infrastructure",
            "services": [{"id": "dns", "name": "CoreDNS", "state": "RUNNING"}],
        }
    ]
    mappings = {
        "group_id": "category",
        "group_label": "name",
        "items_path": "services",
        "item_id": "id",
        "item_label": "name",
        "item_status_tags": [{"path": "state", "name": "state"}],
    }

    mapped = DataMapper.map_grid(raw_data, mappings)
    assert len(mapped) == 1
    assert mapped[0]["id"] == "infra"
    assert mapped[0]["label"] == "Infrastructure"
    assert len(mapped[0]["items"]) == 1
    assert mapped[0]["items"][0] == {
        "id": "dns",
        "label": "CoreDNS",
        "description": None,
        "subtext": None,
        "status_tags": [{"name": "state", "value": "RUNNING"}],
        "open_url": None,
        "has_details": True,
        "data_attrs": {},
    }
