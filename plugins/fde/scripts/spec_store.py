#!/usr/bin/env python3
"""Resolve and inspect the local spec store.

Specs never live inside the repo being worked on. They live under
``$DEV_WORKFLOW_HOME`` (default ``~/dev-workflow``), keyed by the repo's
identity, so a client monorepo's working tree stays clean and no spec can be
committed by accident.

The key is derived from the git remote when there is one, so every checkout and
every worktree of the same repo resolves to the same spec folder.

Usage:
    spec_store.py path                 Print the spec store dir for this repo.
    spec_store.py new "<title>"        Create the next spec folder, print its path.
    spec_store.py list                 Print one line per spec: id, status, progress.
    spec_store.py active               Print the path of the most recently touched spec.
    spec_store.py resolve <ref>        Print the path matching an id, slug, or substring.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

CHECKED = re.compile(r"^\s*-\s*\[x\]", re.IGNORECASE | re.MULTILINE)
UNCHECKED = re.compile(r"^\s*-\s*\[ \]", re.MULTILINE)
STATUS_FIELD = re.compile(r"^status:\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def _git(*args: str) -> str | None:
    """Run a git command, returning stripped stdout or None if it fails."""
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True, timeout=5
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def _normalize_remote(url: str) -> str:
    """Reduce a git remote URL to a stable ``host/path`` identity.

    Handles SSH (``git@host:owner/repo.git``) and HTTPS forms, and strips
    credentials, ports, and the ``.git`` suffix so every clone form of one repo
    produces the same key.
    """
    url = url.strip().removesuffix(".git")
    url = re.sub(r"^ssh://", "", url)
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^[^/@]+@", "", url)  # strip user[:password]@
    url = url.replace(":", "/", 1) if "/" not in url.split(":", 1)[0] else url
    url = re.sub(r"/{2,}", "/", url)
    return url.strip("/")


def repo_key() -> str:
    """Return a filesystem-safe identity for the repo containing the cwd.

    Prefers the origin remote so clones and worktrees agree. Falls back to the
    shared git directory, which is stable across worktrees of the same repo.
    """
    remote = _git("remote", "get-url", "origin")
    if remote:
        identity = _normalize_remote(remote)
    else:
        common = _git("rev-parse", "--path-format=absolute", "--git-common-dir")
        if not common:
            raise SystemExit("fde: not inside a git repository")
        root = Path(common).parent
        digest = hashlib.sha256(str(root).encode()).hexdigest()[:8]
        identity = f"local/{root.name}-{digest}"
    return re.sub(r"[^A-Za-z0-9._-]+", "__", identity).strip("_")


def store_root() -> Path:
    """Return the root of the spec store, creating nothing."""
    configured = os.environ.get("DEV_WORKFLOW_HOME")
    return Path(configured).expanduser() if configured else Path.home() / "dev-workflow"


def store_dir() -> Path:
    """Return this repo's spec directory, creating it if needed."""
    path = store_root() / "specs" / repo_key()
    path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(title: str) -> str:
    """Convert a spec title into a short, readable directory slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "-".join(slug.split("-")[:6]) or "spec"


def next_id(directory: Path) -> str:
    """Return the next zero-padded spec number for a store directory."""
    used = [
        int(match.group(1))
        for child in directory.iterdir()
        if child.is_dir() and (match := re.match(r"^(\d{3})-", child.name))
    ]
    return f"{max(used, default=0) + 1:03d}"


def spec_dirs(directory: Path) -> list[Path]:
    """Return spec folders, newest activity first."""
    found = [c for c in directory.iterdir() if c.is_dir() and re.match(r"^\d{3}-", c.name)]
    return sorted(found, key=lambda p: _touched_at(p), reverse=True)


def _touched_at(spec: Path) -> float:
    """Return the most recent mtime across a spec's files."""
    times = [f.stat().st_mtime for f in spec.glob("*.md") if f.is_file()]
    return max(times, default=0.0)


def summarize(spec: Path) -> str:
    """Return a one-line summary: id, status, and ledger progress."""
    plan = spec / "PLAN.md"
    body = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    done, todo = len(CHECKED.findall(body)), len(UNCHECKED.findall(body))

    spec_file = spec / "SPEC.md"
    header = spec_file.read_text(encoding="utf-8")[:800] if spec_file.is_file() else ""
    status = match.group(1).strip() if (match := STATUS_FIELD.search(header)) else "unknown"

    return f"{spec.name:<40} {status:<12} {done}/{done + todo} tasks"


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    command, args = argv[0], argv[1:]
    directory = store_dir()

    if command == "path":
        print(directory)
    elif command == "new":
        if not args:
            raise SystemExit("fde: `new` requires a title")
        spec = directory / f"{next_id(directory)}-{slugify(' '.join(args))}"
        spec.mkdir()
        print(spec)
    elif command == "list":
        specs = spec_dirs(directory)
        if not specs:
            print(f"No specs yet for this repo. Store: {directory}")
            return 0
        for spec in specs:
            print(summarize(spec))
    elif command == "active":
        specs = spec_dirs(directory)
        if not specs:
            raise SystemExit("fde: no specs for this repo yet — run /fde:spec first")
        print(specs[0])
    elif command == "resolve":
        if not args:
            raise SystemExit("fde: `resolve` requires an id, slug, or substring")
        needle = args[0].lower()
        matches = [s for s in spec_dirs(directory) if needle in s.name.lower()]
        if not matches:
            raise SystemExit(f"fde: no spec matching {args[0]!r} in {directory}")
        print(matches[0])
    else:
        raise SystemExit(f"fde: unknown command {command!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
