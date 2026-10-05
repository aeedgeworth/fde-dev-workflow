#!/usr/bin/env python3
"""Resolve and inspect the external FDE spec store.

Specs live under ``$DEV_WORKFLOW_HOME`` (default ``~/dev-workflow``), keyed by
the current repository's origin remote. The helper never writes to the target
repository.

Usage:
    spec_store.py path                 Print the spec store dir for this repo.
    spec_store.py new "<title>"        Create the next spec folder and print it.
    spec_store.py list                 Print every spec with status and progress.
    spec_store.py active               Print the most recently touched open spec.
    spec_store.py resolve <ref>        Resolve an id, slug, or unique substring.
    spec_store.py check [ref]          Lint a spec: AC coverage, fields, leftovers.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

CHECKED = re.compile(r"^\s*-\s*\[x\]", re.IGNORECASE | re.MULTILINE)
UNCHECKED = re.compile(r"^\s*-\s*\[ \]", re.MULTILINE)
STATUS_FIELD = re.compile(r"^status:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
SPEC_NAME = re.compile(r"^(\d{3})-(.+)$")
TERMINAL_STATUSES = {"abandoned", "cancelled", "complete", "shipped"}
CRITERION = re.compile(r"^\s*-\s*\[[ xX]\]\s*\**(AC\d+)\**[:.]?[ \t]*(.*)$", re.MULTILINE)
TASK = re.compile(r"^\s*-\s*\[[ xX]\]\s*\*\*(T\d+)\*\*\s*(.*)$")
TASK_FIELD = re.compile(r"^\s+-\s*([a-z]+):\s*(.*)$")
PLACEHOLDER = re.compile(
    r"\{\{[A-Z]+\}\}|<(?:one-sentence|outcome|question|safe command|command or|expected paths)[^>]*>"
)
MAX_TASKS = 15


def _git(*args: str, cwd: Path | None = None) -> str | None:
    """Run a git command, returning stripped stdout or ``None`` on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return result.stdout.strip() or None


def _normalize_remote(raw_url: str) -> str:
    """Reduce common Git remote forms to a credential-free ``host/path``."""
    raw_url = raw_url.strip()

    if "://" in raw_url:
        parsed = urlsplit(raw_url)
        host = parsed.hostname or "local"
        path = parsed.path
    else:
        without_user = re.sub(r"^[^/@]+@", "", raw_url)
        scp = re.fullmatch(r"([^/:]+):(.+)", without_user)
        if scp:
            host, path = scp.groups()
        else:
            path_obj = Path(without_user).expanduser()
            host, path = "local", str(path_obj)

    normalized_path = re.sub(r"/{2,}", "/", path).strip("/").removesuffix(".git")
    return f"{host.lower()}/{normalized_path}".strip("/")


def repo_key(cwd: Path | None = None) -> str:
    """Return a filesystem-safe repository identity for ``cwd``."""
    remote = _git("remote", "get-url", "origin", cwd=cwd)
    if remote:
        identity = _normalize_remote(remote)
    else:
        common = _git(
            "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=cwd
        )
        if not common:
            raise SystemExit("fde: not inside a git repository")
        root = Path(common).parent
        digest = hashlib.sha256(str(root).encode()).hexdigest()[:8]
        identity = f"local/{root.name}-{digest}"
    return re.sub(r"[^A-Za-z0-9._-]+", "__", identity).strip("_")


def store_root() -> Path:
    """Return the configured root without creating it."""
    configured = os.environ.get("DEV_WORKFLOW_HOME")
    return Path(configured).expanduser() if configured else Path.home() / "dev-workflow"


def store_dir(*, create: bool = False, cwd: Path | None = None) -> Path:
    """Return this repository's spec directory, optionally creating it."""
    path = store_root() / "specs" / repo_key(cwd)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def slugify(title: str) -> str:
    """Convert a title into a short readable directory slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "-".join(slug.split("-")[:6]) or "spec"


def next_id(directory: Path) -> str:
    """Return the next zero-padded spec number."""
    used = [
        int(match.group(1))
        for child in directory.iterdir()
        if child.is_dir() and (match := SPEC_NAME.match(child.name))
    ]
    return f"{max(used, default=0) + 1:03d}"


def _touched_at(spec: Path) -> float:
    """Return the most recent modification time across a spec's Markdown."""
    times = [file.stat().st_mtime for file in spec.glob("*.md") if file.is_file()]
    return max(times, default=0.0)


def spec_dirs(directory: Path) -> list[Path]:
    """Return all spec folders, newest activity first."""
    if not directory.is_dir():
        return []
    found = [
        child
        for child in directory.iterdir()
        if child.is_dir() and SPEC_NAME.match(child.name)
    ]
    return sorted(found, key=_touched_at, reverse=True)


def spec_status(spec: Path) -> str:
    """Read a spec's frontmatter status."""
    spec_file = spec / "SPEC.md"
    header = spec_file.read_text(encoding="utf-8")[:800] if spec_file.is_file() else ""
    return match.group(1).strip().lower() if (match := STATUS_FIELD.search(header)) else "unknown"


def active_spec_dirs(directory: Path) -> list[Path]:
    """Return non-terminal specs, newest activity first."""
    return [
        spec
        for spec in spec_dirs(directory)
        if spec_status(spec) not in TERMINAL_STATUSES
    ]


def summarize(spec: Path) -> str:
    """Return a one-line status and ledger-progress summary."""
    plan = spec / "PLAN.md"
    body = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    done, todo = len(CHECKED.findall(body)), len(UNCHECKED.findall(body))
    return f"{spec.name:<40} {spec_status(spec):<12} {done}/{done + todo} tasks"


def create_spec(directory: Path, title: str) -> Path:
    """Create a uniquely numbered spec directory."""
    directory.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    while True:
        spec = directory / f"{next_id(directory)}-{slug}"
        try:
            spec.mkdir()
        except FileExistsError:
            continue
        return spec


def resolve_spec(directory: Path, ref: str) -> Path:
    """Resolve ``ref`` exactly where possible and reject ambiguous substrings."""
    needle = ref.lower()
    specs = spec_dirs(directory)

    exact = [
        spec
        for spec in specs
        if spec.name.lower() == needle
        or spec.name.lower().split("-", 1)[0] == needle
        or spec.name.lower().split("-", 1)[1] == needle
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        names = ", ".join(spec.name for spec in exact)
        raise SystemExit(f"fde: ambiguous spec reference {ref!r}: {names}")

    matches = [spec for spec in specs if needle in spec.name.lower()]
    if not matches:
        raise SystemExit(f"fde: no spec matching {ref!r} in {directory}")
    if len(matches) > 1:
        names = ", ".join(spec.name for spec in matches)
        raise SystemExit(f"fde: ambiguous spec reference {ref!r}: {names}")
    return matches[0]


def parse_tasks(plan_text: str) -> list[dict[str, object]]:
    """Return ledger tasks with their indented ``- field: value`` lines.

    A field belongs to the nearest task above it; any unindented line ends the
    task, so prose and code fences between tasks are never read as fields.
    """
    tasks: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for line in plan_text.splitlines():
        if match := TASK.match(line):
            current = {"id": match.group(1), "title": match.group(2), "fields": {}}
            tasks.append(current)
        elif current is not None and (field := TASK_FIELD.match(line)):
            current["fields"][field.group(1)] = field.group(2).strip()  # type: ignore[index]
        elif line and not line[0].isspace():
            current = None
    return tasks


def _is_spike(task: dict[str, object]) -> bool:
    return str(task["title"]).lower().startswith("spike")


def check_spec(spec: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a spec's structural readiness to build.

    Errors mean the spec cannot be traced: a criterion no task delivers, a task
    citing a criterion that does not exist, or unfilled template text. Warnings
    are judgment calls the reviewer should look at but may accept.
    """
    spec_file, plan_file = spec / "SPEC.md", spec / "PLAN.md"
    spec_text = spec_file.read_text(encoding="utf-8") if spec_file.is_file() else ""
    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.is_file() else ""
    errors: list[str] = []
    warnings: list[str] = []

    for name, text in (("SPEC.md", spec_text), ("PLAN.md", plan_text)):
        for number, line in enumerate(text.splitlines(), start=1):
            if PLACEHOLDER.search(line):
                errors.append(f"{name}:{number}: unfilled template text: {line.strip()}")

    criteria = {match.group(1): match.group(2).strip() for match in CRITERION.finditer(spec_text)}
    if not criteria:
        errors.append("SPEC.md: no acceptance criteria (expected `- [ ] AC1 <statement>`)")
    for criterion, statement in criteria.items():
        if not statement:
            errors.append(f"SPEC.md: {criterion} has no statement")

    tasks = parse_tasks(plan_text)
    if not tasks:
        errors.append("PLAN.md: no tasks (expected `- [ ] **T1** <outcome>`)")
    if len(tasks) > MAX_TASKS:
        warnings.append(f"PLAN.md: {len(tasks)} tasks; past {MAX_TASKS} the work usually wants two specs")

    covered: set[str] = set()
    for task in tasks:
        fields: dict[str, str] = task["fields"]  # type: ignore[assignment]
        cited = set(re.findall(r"AC\d+", fields.get("covers", "")))
        for unknown in sorted(cited - criteria.keys()):
            errors.append(f"PLAN.md: {task['id']} covers {unknown}, which SPEC.md does not define")
        covered |= cited
        if _is_spike(task):
            if not fields.get("timebox"):
                warnings.append(f"PLAN.md: spike {task['id']} has no timebox")
        elif not fields.get("verify"):
            warnings.append(f"PLAN.md: {task['id']} has no verify step")

    for criterion in sorted(criteria.keys() - covered, key=lambda c: int(c[2:])):
        errors.append(f"PLAN.md: no task covers {criterion}")

    return errors, warnings


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    command, args = argv[0], argv[1:]
    directory = store_dir(create=command == "new")

    if command == "path":
        print(directory)
    elif command == "new":
        if not args:
            raise SystemExit("fde: `new` requires a title")
        print(create_spec(directory, " ".join(args)))
    elif command == "list":
        specs = spec_dirs(directory)
        if not specs:
            print(f"No specs yet for this repo. Store: {directory}")
            return 0
        for spec in specs:
            print(summarize(spec))
    elif command == "active":
        specs = active_spec_dirs(directory)
        if not specs:
            raise SystemExit("fde: no active specs for this repo — run /fde:spec first")
        print(specs[0])
    elif command == "resolve":
        if not args:
            raise SystemExit("fde: `resolve` requires an id, slug, or substring")
        print(resolve_spec(directory, args[0]))
    elif command == "check":
        if args:
            spec = resolve_spec(directory, args[0])
        elif specs := active_spec_dirs(directory):
            spec = specs[0]
        else:
            raise SystemExit("fde: no active specs for this repo — pass a spec reference")
        errors, warnings = check_spec(spec)
        for error in errors:
            print(f"error: {error}")
        for warning in warnings:
            print(f"warning: {warning}")
        if not errors:
            print(f"ok: {spec.name} is traceable ({len(warnings)} warning(s))")
        return 1 if errors else 0
    else:
        raise SystemExit(f"fde: unknown command {command!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
