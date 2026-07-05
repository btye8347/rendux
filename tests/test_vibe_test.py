"""Tests for scripts/vibe_test.py agent eval harness."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_vibe_test_all_fixtures_pass():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "vibe_test.py")],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3/3" in result.stdout
