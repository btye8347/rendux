"""Load RDL widget contracts and interaction profiles from JSON files."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from rendux.paths import contracts_dir, templates_dir

# Resolved at import for backward-compatible module constants.
CONTRACTS_ROOT = contracts_dir()
WIDGETS_DIR = CONTRACTS_ROOT / "widgets"
PROFILES_DIR = CONTRACTS_ROOT / "profiles"
GRAMMAR_PATH = CONTRACTS_ROOT / "rdl-grammar.json"
WIDGETS_TEMPLATE_DIR = templates_dir() / "widgets"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_grammar() -> dict[str, Any]:
    return _load_json(GRAMMAR_PATH)


@lru_cache(maxsize=1)
def load_profiles() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for path in sorted(PROFILES_DIR.glob("*.json")):
        data = _load_json(path)
        profiles[data["name"]] = data
    return profiles


@lru_cache(maxsize=1)
def load_widget_registry() -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in sorted(WIDGETS_DIR.glob("*.json")):
        data = _load_json(path)
        registry[data["name"]] = data
    return registry


def list_widget_template_names() -> set[str]:
    return {p.stem for p in WIDGETS_TEMPLATE_DIR.glob("*.html")}


def canonical_prop_names(contract: dict[str, Any]) -> dict[str, str]:
    """Map alias -> canonical prop name for a widget contract."""
    mapping: dict[str, str] = {}
    for name, spec in contract.get("props", {}).items():
        mapping[name] = name
        for alias in spec.get("aliases", []):
            mapping[alias] = name
    return mapping


def normalize_widget_props(widget: str, props: dict[str, Any]) -> dict[str, Any]:
    """Rewrite alias prop names to canonical names (e.g. title -> label)."""
    registry = load_widget_registry()
    contract = registry.get(widget)
    if not contract or contract.get("status") != "verified":
        return props
    alias_map = canonical_prop_names(contract)
    normalized: dict[str, Any] = {}
    for key, value in props.items():
        canonical = alias_map.get(key, key)
        if canonical in normalized and canonical != key:
            continue
        normalized[canonical] = value
    return normalized
