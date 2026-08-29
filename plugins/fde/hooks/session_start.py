#!/usr/bin/env python3
"""SessionStart orientation.

Prints the active spec and its next unchecked task, so a resumed session knows
where it left off without re-reading the ledger. Silent when this repo has no
specs — most sessions are not spec-driven, and an empty banner is noise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

try:
    from spec_store import CHECKED, UNCHECKED, spec_dirs, store_dir
except ImportError:
    sys.exit(0)

NEXT_TASK = re.compile(r"^\s*-\s*\[ \]\s*(.+)$", re.MULTILINE)


def main() -> int:
    try:
        directory = store_dir()
        specs = spec_dirs(directory)
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
        lines.append(f"{len(specs) - 1} other spec(s) in this repo — /fde:status for the roll-up.")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
