"""Filesystem locations for the installed or editable RendUX package."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

# rendux/ package directory (contains templates/, static/, …)
_PACKAGE_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def package_dir() -> Path:
    """Return the ``rendux`` package directory."""
    return _PACKAGE_DIR


@lru_cache(maxsize=1)
def templates_dir() -> Path:
    """Jinja templates shipped with RendUX (widgets, chrome, workspaces)."""
    return _PACKAGE_DIR / "templates"


@lru_cache(maxsize=1)
def static_dir() -> Path:
    """Static assets (CSS, JS, vendor)."""
    return _PACKAGE_DIR / "static"


@lru_cache(maxsize=1)
def contracts_dir() -> Path:
    """Widget contracts + grammar.

    Resolution order:
    1. ``rendux/contracts`` — wheel install (force-included) or future in-tree layout
    2. ``<repo>/contracts`` — editable checkout (contracts live at repo root)
    """
    bundled = _PACKAGE_DIR / "contracts"
    if bundled.is_dir() and (bundled / "widgets").is_dir():
        return bundled
    repo_root = _PACKAGE_DIR.parent / "contracts"
    if repo_root.is_dir() and (repo_root / "widgets").is_dir():
        return repo_root
    raise FileNotFoundError(
        "RendUX contracts not found. Expected rendux/contracts (installed) "
        "or <repo>/contracts (editable)."
    )


def catalog_verified_path() -> Path:
    """Path to the LLM closed-vocabulary catalog."""
    return contracts_dir() / "catalog.verified.json"
