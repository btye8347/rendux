#!/usr/bin/env python3
"""CI smoke: strict-render the ops layout from config/views.yaml."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from jinja2 import Environment, FileSystemLoader

from rendux.core.layout import LayoutRenderer


def main() -> int:
    ops = yaml.safe_load((ROOT / "config" / "views.yaml").read_text())["views"]["ops"]
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "rendux" / "templates")),
        autoescape=True,
    )
    strict = os.environ.get("RENDUX_STRICT", "").lower() in ("1", "true", "yes")
    LayoutRenderer(env, strict=strict).render(
        ops["workspace"]["layout"],
        ops["data"],
    )
    print("strict ops render OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
