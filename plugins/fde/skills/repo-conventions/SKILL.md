---
name: repo-conventions
description: Discover the authoritative local build, test, style, and architecture conventions before editing an unfamiliar repository or monorepo area. Use when the relevant package conventions are not already known.
---

# Repository conventions

Convention is local. Inspect the area being changed before writing code; the
nearest reliable evidence wins.

Read, in order:

1. `CLAUDE.md`, `AGENTS.md`, or other instruction files from the repository root
   down to the target directory.
2. The nearest project configuration such as `pyproject.toml`, `package.json`,
   `go.mod`, `Makefile`, or `justfile` for actual format, lint, type-check, build,
   and test commands.
3. Two or three neighboring implementation files and the nearest tests for
   naming, layout, error handling, logging, typing, fixtures, and abstraction
   level. Match their comment density too — code that explains dramatically more
   or less than its neighbours reads as foreign regardless of correctness.
4. Relevant CI configuration and recent commits to the target path when local
   practice or enforced checks remain unclear.

Before editing, be able to state the applicable commands, source/test layout,
important boundaries, and any conflict between instruction sources. In a
monorepo, use the package-level command for the inner loop and reserve broader
validation for handoff.

Do not create or modify `CLAUDE.md`, `AGENTS.md`, dependencies, formatter
configuration, or other repository-wide policy merely because something was
undocumented. Report the discovery and ask before making it durable.
