#!/usr/bin/env python3
"""Best-effort shell guard for high-cost commands.

This hook catches common explicit spellings. It complements the host sandbox,
approval policy, and workflow instructions; it is not a complete security
boundary. Exit 0 allows a command and exit 2 blocks it.

Claude Code sends ``tool_input.command`` (PreToolUse). Cursor sends a top-level
``command`` (beforeShellExecution). Both include ``cwd``.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

SHELL_BOUNDARY = re.compile(r"(?:\r?\n|&&|\|\||[;|])")
PROD_TARGET = re.compile(
    r"(?:--target|-t)(?:\s+|=)(?:prod(?:uction)?(?:[-_][\w.-]+)?)\b", re.I
)
DEFAULT_NAMES = ("main", "master", "trunk")
ONE_COMMAND_OVERRIDE = re.compile(r"^\s*FDE_GUARD_OVERRIDE=1(?:\s+|$)")


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None


def _current_branch(cwd: Path) -> str | None:
    return _git(cwd, "branch", "--show-current")


def _default_branches(cwd: Path) -> set[str]:
    remote_head = _git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if remote_head:
        return {remote_head.rsplit("/", 1)[-1]}
    return {
        name
        for name in DEFAULT_NAMES
        if _git(cwd, "show-ref", "--verify", f"refs/heads/{name}")
    }


def _tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _push_positionals(segment: str) -> list[str] | None:
    tokens = _tokens(segment)
    try:
        push_index = tokens.index("push")
    except ValueError:
        return None
    return [token for token in tokens[push_index + 1 :] if not token.startswith("-")]


def _git_pushes_current_branch(segment: str, cwd: Path) -> bool:
    positional = _push_positionals(segment)
    if positional is None:
        return False

    current = _current_branch(cwd)
    defaults = _default_branches(cwd)
    if not current or current not in defaults:
        return False

    tokens = _tokens(segment)
    if "--tags" in tokens or any(token.startswith("refs/tags/") for token in tokens):
        return False

    if len(positional) <= 1:
        return True
    return any(
        token in {"HEAD", current}
        or any(token.startswith(f"HEAD:{default}") for default in defaults)
        or any(token.startswith(f"{current}:{default}") for default in defaults)
        for token in positional[1:]
    )


def _git_pushes_explicit_default(segment: str, cwd: Path) -> bool:
    positional = _push_positionals(segment)
    if positional is None or len(positional) <= 1:
        return False

    protected = _default_branches(cwd) or set(DEFAULT_NAMES)
    for refspec in positional[1:]:
        refspec = refspec.removeprefix("+")
        destination = refspec.rsplit(":", 1)[-1]
        branch = destination.removeprefix("refs/heads/")
        if branch in protected:
            return True
    return False


def _single_workspace(cwd: Path) -> bool:
    """Return whether this engagement declares one Databricks workspace.

    A customer may have a single workspace that is *named* production. There, a
    prod-named bundle target is ordinary work rather than a promotion, and
    blocking it would train the operator to bypass the guard entirely. Opt in
    per engagement with ``[safety] single_workspace = true`` in ``fde.toml``
    inside that repository's spec-store directory.

    Any failure to read the setting returns False, keeping the strict default.
    """
    try:
        from spec_store import store_dir  # imported lazily; the common path never needs it

        config = store_dir(cwd=cwd) / "fde.toml"
        if not config.is_file():
            return False
        return bool(tomllib.loads(config.read_text(encoding="utf-8")).get("safety", {}).get("single_workspace"))
    except Exception:
        return False


def blocked_reason(command: str, cwd: Path) -> str | None:
    """Return a human-readable block reason for a recognized risky command."""
    for segment in filter(str.strip, SHELL_BOUNDARY.split(command)):
        if ONE_COMMAND_OVERRIDE.search(segment):
            continue

        if re.search(r"\bdatabricks\s+bundle\s+destroy\b", segment, re.I):
            return "tears down deployed Databricks bundle resources"

        if (
            re.search(r"\bdatabricks\s+bundle\b.*\b(?:deploy|run)\b", segment, re.I)
            and PROD_TARGET.search(segment)
            and not _single_workspace(cwd)
        ):
            return "deploys or runs a Databricks bundle against an explicit production target"

        if (
            re.search(r"\bterraform\b.*\b(?:apply|destroy)\b", segment, re.I)
            and re.search(r"\bprod(?:uction)?\b", segment, re.I)
        ):
            return "applies or destroys Terraform with an explicit production reference"

        if not re.search(r"\bgit\b.*\bpush\b", segment, re.I):
            continue
        if re.search(r"(?:^|\s)(?:--force(?!-with-lease)(?:=\S+)?|-f)(?=\s|$)", segment):
            return "force-pushes without --force-with-lease"
        if _git_pushes_explicit_default(segment, cwd) or _git_pushes_current_branch(
            segment, cwd
        ):
            return "pushes directly to the repository's default branch"

    return None


def payload_command(payload: object) -> str:
    """Return the shell command from a Claude or Cursor hook payload."""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str) and command.strip():
            return command
    command = payload.get("command")
    return command if isinstance(command, str) else ""


def payload_cwd(payload: object) -> Path:
    """Return the working directory from a Claude or Cursor hook payload."""
    if not isinstance(payload, dict):
        return Path.cwd()
    raw = payload.get("cwd")
    if isinstance(raw, str) and raw.strip():
        return Path(raw)
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        raw = tool_input.get("working_directory") or tool_input.get("cwd")
        if isinstance(raw, str) and raw.strip():
            return Path(raw)
    return Path.cwd()


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    command = payload_command(payload)
    if not command.strip():
        return 0

    override_used = any(
        ONE_COMMAND_OVERRIDE.search(segment)
        for segment in filter(str.strip, SHELL_BOUNDARY.split(command))
    )
    if override_used:
        print(
            "fde guard: OVERRIDDEN for this command by FDE_GUARD_OVERRIDE=1. "
            "Confirm that explicit user authorization is recorded in the transcript.",
            file=sys.stderr,
        )

    cwd = payload_cwd(payload)
    if reason := blocked_reason(command, cwd):
        print(
            f"fde guard: blocked because this command {reason}.\n"
            "This hook is defense-in-depth. Stop and ask the user to perform the "
            "operation, or use a non-production branch or target.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
