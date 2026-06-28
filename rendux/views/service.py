from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


class ViewConfigError(ValueError):
    pass


def deep_merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict1)
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ViewConfigService:
    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._views = _require_mapping(config, "views")
        self._compiled: dict[str, dict[str, Any]] = {}

    @classmethod
    def from_yaml(cls, path: Path) -> "ViewConfigService":
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ViewConfigError("View config must be a mapping.")
        _validate_top_level(data)
        return cls(data)

    def list_views(self) -> list[dict[str, Any]]:
        return [_view_with_id(view_id, view) for view_id, view in self._views.items()]

    def get_view(self, view_id: str) -> dict[str, Any]:
        try:
            view = self._views[view_id]
        except KeyError as exc:
            raise KeyError(view_id) from exc
        return _view_with_id(view_id, view)

    def get_config(self) -> dict[str, Any]:
        return self._config

    def workspace_template(self, view_id: str) -> str | None:
        """Return the explicit template path for a view, or None."""
        ws = self._workspace(view_id)
        return ws.get("template") if ws else None

    def workspace_layout(self, view_id: str) -> list | None:
        """Return the RDL layout node list for a view, or None."""
        ws = self._workspace(view_id)
        if not ws:
            return None
        layout = ws.get("layout")
        return layout if isinstance(layout, list) else None

    def _workspace(self, view_id: str) -> dict[str, Any] | None:
        view = self._views.get(view_id)
        if not isinstance(view, dict):
            return None
        ws = view.get("workspace")
        return ws if isinstance(ws, dict) else None

    def get_surface_defaults(self) -> dict[str, Any]:
        return _surface_defaults(self._surfaces())

    def list_surfaces(self) -> list[dict[str, Any]]:
        surfaces = self._surfaces()
        return [
            _surface_with_id(surface_id, surface, self.get_surface_defaults())
            for surface_id, surface in surfaces.items()
            if surface_id != "defaults"
        ]

    def get_surface(self, surface_id: str) -> dict[str, Any]:
        surfaces = self._surfaces()
        try:
            surface = surfaces[surface_id]
        except KeyError as exc:
            raise KeyError(surface_id) from exc
        if surface_id == "defaults":
            raise KeyError(surface_id)
        return _surface_with_id(surface_id, surface, self.get_surface_defaults())

    def get_surface_by_param(self, param_name: str, param_value: str) -> dict[str, Any] | None:
        for surface in self.list_surfaces():
            if surface["params"].get(param_name) == param_value:
                return surface
        return None

    def _surfaces(self) -> dict[str, Any]:
        surfaces = self._config.get("surfaces", {})
        if not isinstance(surfaces, dict):
            raise ViewConfigError("Surface declarations must be a mapping.")
        return surfaces

    def get_routes(self) -> dict[str, str]:
        routes = {}
        for view_id, view in self._views.items():
            if isinstance(view, dict):
                routes[view_id] = _normalized_route(view_id, view)
            else:
                routes[view_id] = f"/views/{view_id}"
        return routes

    def get_shell_view(self, view_id: str) -> dict[str, Any]:
        view = self.get_view(view_id)
        shell_default = self._config.get("shell", {})
        if not isinstance(shell_default, dict):
            raise ViewConfigError("Shell config must be a mapping.")

        shell_id = str(shell_default.get("id", "default"))
        merged = deep_merge(shell_default, view)
        merged["shell_id"] = shell_id
        merged["active_view"] = view
        merged["routes"] = self.get_routes()
        merged["nav_items"] = self._build_nav_items()
        merged["surfaces"] = self.list_surfaces()
        return merged

    def get_shell_fallback(self, view_id: str) -> dict[str, Any]:
        fallback_view = {
            "id": view_id,
            "label": "View not found",
            "route": f"/views/{view_id}",
        }
        shell_default = self._config.get("shell", {})
        if not isinstance(shell_default, dict):
            shell_default = {}

        shell_id = str(shell_default.get("id", "default"))
        merged = deep_merge(shell_default, fallback_view)
        merged["shell_id"] = shell_id
        merged["active_view"] = fallback_view
        merged["routes"] = self.get_routes()
        merged["nav_items"] = self._build_nav_items()
        merged["surfaces"] = self.list_surfaces()
        return merged

    def compile_models(self) -> None:
        self._compiled.clear()
        for view_id in self._views:
            self._compiled[view_id] = self._compile_view(view_id)

    def get_compiled(self, view_id: str) -> dict[str, Any]:
        try:
            return self._compiled[view_id]
        except KeyError as exc:
            raise KeyError(view_id) from exc

    def _compile_view(self, view_id: str) -> dict[str, Any]:
        shell = self.get_shell_view(view_id)
        compiled: dict[str, Any] = deepcopy(shell)

        workspace = compiled.get("workspace", {})
        if isinstance(workspace, dict):
            contrib = workspace.get("contribution", {})
            if isinstance(contrib, dict):
                compiled["_workspace_primitive"] = contrib.get("primitive")
                compiled["_workspace_mappings"] = contrib.get("mappings", {})
                compiled["_workspace_capability"] = contrib.get("capability")
                compiled["_workspace_params"] = contrib.get("params", {})

        return compiled

    def _build_nav_items(self) -> list[dict[str, str]]:
        items = []
        for view_id, view in self._views.items():
            if not isinstance(view, dict):
                continue
            items.append({
                "id": view_id,
                "label": str(view.get("label", view_id)),
                "route": _normalized_route(view_id, view),
            })
        return items


def _validate_top_level(data: dict[str, Any]) -> None:
    for key in ("version", "shell", "views"):
        if key not in data:
            raise ViewConfigError(f"View config missing required section: {key}")
    _require_mapping(data, "views")


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ViewConfigError(f"View config section must be a mapping: {key}")
    return value


def _view_with_id(view_id: str, view: Any) -> dict[str, Any]:
    if not isinstance(view, dict):
        raise ViewConfigError(f"View declaration must be a mapping: {view_id}")
    return {"id": view_id, **view}


def _surface_defaults(surfaces: dict[str, Any]) -> dict[str, Any]:
    defaults = surfaces.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ViewConfigError("Surface defaults must be a mapping.")
    return {
        "open_mode": str(defaults.get("open_mode", "controlled_wrapper")),
        "frame_mode": str(defaults.get("frame_mode", "allow_declared")),
        "fallback": str(defaults.get("fallback", "external_link")),
    }


def _surface_with_id(
    surface_id: str,
    surface: Any,
    defaults: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(surface, dict):
        raise ViewConfigError(f"Surface declaration must be a mapping: {surface_id}")
    params = surface.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ViewConfigError(f"Surface params must be a mapping: {surface_id}")
    return {
        "id": surface_id,
        "label": str(surface.get("label", surface_id)),
        "type": str(surface.get("type", "controlled_surface")),
        "source_url": str(surface.get("source_url", "")),
        "trust_level": str(surface.get("trust_level", "unknown")),
        "interaction": str(surface.get("interaction", "read_only")),
        "frame_mode": str(surface.get("frame_mode", defaults["frame_mode"])),
        "allowed_actions": _string_list(surface_id, "surface.allowed_actions", surface.get("allowed_actions", [])),
        "fallback": str(surface.get("fallback", defaults["fallback"])),
        "params": {str(key): value for key, value in params.items()},
        "defaults": defaults,
    }


def _string_list(view_id: str, field: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ViewConfigError(f"View {field} must be a list: {view_id}")
    return [str(item) for item in value]


def _normalized_route(view_id: str, view: dict[str, Any] | None) -> str:
    if view is None:
        return f"/views/{view_id}"
    route = str(view.get("route", ""))
    if route.startswith("/"):
        return route
    return f"/views/{view_id}"
