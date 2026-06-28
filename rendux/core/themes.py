from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ThemeService:
    def __init__(self, config: dict[str, Any]) -> None:
        self._themes: dict[str, Any] = config.get("themes", {})

    @classmethod
    def from_yaml(cls, path: Path) -> "ThemeService":
        if not path.exists():
            return cls({})
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(data if isinstance(data, dict) else {})

    def list_themes(self) -> list[dict[str, str]]:
        return [
            {"id": tid, "label": str(theme.get("label", tid))}
            for tid, theme in self._themes.items()
        ]

    def generate_css(self) -> str:
        blocks: list[str] = []
        for tid, theme in self._themes.items():
            variables = theme.get("variables", {})
            if not variables:
                continue
            lines = [f'html[data-theme="{tid}"] {{']
            for var_name, value in variables.items():
                lines.append(f"  {var_name}: {value};")
            lines.append("}")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)
