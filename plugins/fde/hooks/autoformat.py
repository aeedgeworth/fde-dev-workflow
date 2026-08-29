#!/usr/bin/env python3
"""PostToolUse formatter.

Formats a file after an edit, but only with a formatter the project itself has
configured. Reformatting a client monorepo with a tool it does not use produces
an enormous, unreviewable diff — so absence of config means we do nothing.

Always silent on success and never blocks.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PY_SUFFIXES = {".py", ".pyi"}
JS_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".json", ".md"}


def _find_up(start: Path, name: str) -> Path | None:
    """Return the nearest ancestor file with this name, or None."""
    for directory in [start, *start.parents]:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def _ruff_configured(path: Path) -> bool:
    """Return whether the nearest pyproject.toml opts into ruff."""
    pyproject = _find_up(path.parent, "pyproject.toml")
    if pyproject is None:
        return _find_up(path.parent, "ruff.toml") is not None
    try:
        config = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return "ruff" in config.get("tool", {})


def _prettier_configured(path: Path) -> bool:
    """Return whether the project declares a prettier configuration."""
    for name in (".prettierrc", ".prettierrc.json", ".prettierrc.yaml", "prettier.config.js"):
        if _find_up(path.parent, name):
            return True
    package = _find_up(path.parent, "package.json")
    if package is None:
        return False
    try:
        return "prettier" in json.loads(package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False


def _run(command: list[str], path: Path) -> None:
    """Run a formatter, ignoring any failure — formatting is never fatal."""
    try:
        subprocess.run([*command, str(path)], capture_output=True, timeout=10, check=False)
    except (subprocess.SubprocessError, OSError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    raw = payload.get("tool_input", {}).get("file_path")
    if not isinstance(raw, str):
        return 0

    path = Path(raw)
    if not path.is_file():
        return 0

    if path.suffix in PY_SUFFIXES and shutil.which("ruff") and _ruff_configured(path):
        _run(["ruff", "format", "--quiet"], path)
    elif path.suffix in JS_SUFFIXES and _prettier_configured(path) and shutil.which("npx"):
        _run(["npx", "--no-install", "prettier", "--write", "--log-level", "silent"], path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
