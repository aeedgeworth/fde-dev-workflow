#!/usr/bin/env python3
"""PreToolUse guard for irreversible operations.

Blocks a small, deliberate set of commands whose cost is asymmetric: a
production deploy, a destructive bundle teardown, a force-push, or a push
straight to the default branch. Everything else passes untouched.

The override is loud, not silent: set FDE_ALLOW_PROD=1 and the command runs
with a warning recorded in the transcript.

Exit 0 allows; exit 2 blocks and sends the reason back to Claude.
"""

from __future__ import annotations

import json
import os
import re
import sys

# (compiled pattern, what it protects against). Ordered most-specific first.
BLOCKED: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"databricks\s+bundle\s+(?:deploy|run|destroy)\b[^|;&]*?(?:--target|-t)\s+(prod\w*|production)", re.I),
        "deploys or runs a Databricks bundle against a production target",
    ),
    (
        re.compile(r"databricks\s+bundle\s+destroy\b", re.I),
        "tears down deployed Databricks bundle resources",
    ),
    (
        re.compile(r"\bterraform\s+(?:apply|destroy)\b(?![^|;&]*-auto-approve\s*=\s*false)[^|;&]*\bprod", re.I),
        "applies Terraform against production",
    ),
    (
        re.compile(r"\bgit\s+push\b[^|;&]*?(?:--force(?!-with-lease)|\s-f\b)", re.I),
        "force-pushes, which can destroy commits others have pulled "
        "(use --force-with-lease if you must rewrite your own branch)",
    ),
    (
        re.compile(r"\bgit\s+push\b[^|;&]*?\b(?:origin|upstream)\s+(?:HEAD:)?(?:main|master)\b", re.I),
        "pushes directly to the default branch (open a pull request instead)",
    ),
]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # Never break the session over an unreadable payload.

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    for pattern, description in BLOCKED:
        if not pattern.search(command):
            continue
        if os.environ.get("FDE_ALLOW_PROD") == "1":
            print(
                f"fde guard: OVERRIDDEN — this command {description}. "
                "FDE_ALLOW_PROD=1 is set, so it is being allowed. Confirm this is intended.",
                file=sys.stderr,
            )
            return 0
        print(
            f"fde guard: blocked. This command {description}.\n"
            "This is a user-only action. Stop and ask the user to run it themselves, "
            "or propose a non-production alternative (a dev target, a pull request). "
            "Do not attempt to rephrase the command to get around this guard.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
