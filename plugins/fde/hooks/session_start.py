#!/usr/bin/env python3
"""SessionStart orientation.

Prints the active spec and its next unchecked task, so a resumed session knows
where it left off without re-reading the ledger. Silent when this repo has no
specs — most sessions are not spec-driven, and an empty banner is noise.

The workspace is resolved from the host's project-directory variable rather than
the process working directory, because a host may launch hooks from the plugin
directory instead of the workspace.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

try:
    from spec_store import CHECKED, UNCHECKED, active_spec_dirs, store_dir
except ImportError:
    sys.exit(0)

NEXT_TASK = re.compile(r"^\s*-\s*\[ \]\s*(.+)$", re.MULTILINE)
PROJECT_DIR_VARS = ("CURSOR_PROJECT_DIR", "CLAUDE_PROJECT_DIR")


def workspace() -> Path | None:
    """Return the host-provided workspace root, or None to use the process cwd."""
    for name in PROJECT_DIR_VARS:
        value = os.environ.get(name)
        if value and Path(value).is_dir():
            return Path(value)
    return None


def main() -> int:
    try:
        directory = store_dir(cwd=workspace())
        specs = active_spec_dirs(directory)
    except (SystemExit, OSError):
        return 0  # Not a git repo, or no store — nothing to say.

    if not specs:
        return 0

    spec = specs[0]
    plan = spec / "PLAN.md"
    body = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    done, todo = len(CHECKED.findall(body)), len(UNCHECKED.findall(body))

    lines = [f"Active spec: {spec.name} — {done}/{done + todo} tasks done ({spec})"]
    if match := NEXT_TASK.search(body):
        lines.append(f"Next task: {match.group(1).strip()}")
    if len(specs) > 1:
        lines.append(
            f"{len(specs) - 1} other active spec(s) in this repo — "
            "run /fde:status for the roll-up."
        )

    text = "\n".join(lines)
    if (
        os.environ.get("FDE_HOOK_HOST") == "cursor"
        or os.environ.get("CURSOR_VERSION")
    ):
        json.dump({"additional_context": text}, sys.stdout)
        print()
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
