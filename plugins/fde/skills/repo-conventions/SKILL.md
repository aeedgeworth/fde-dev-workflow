---
name: repo-conventions
description: Detect and follow the local conventions of the directory you are editing, rather than the repo root's. Use before writing or modifying code in any unfamiliar repo, and always in a monorepo where different areas follow different rules. Triggers on starting work in a new repo or package, "match existing style", "what are the conventions here", or any edit in a large or multi-language repository.
---

# Repo conventions

A large monorepo is not one codebase. It is several, sharing a git remote, often
with different eras of convention layered on top of each other. Code that
matches the repo root but not its own directory reads as foreign and gets
rejected in review.

**The rule: match your neighbors, not the root.** Convention is local, and the
nearest evidence wins.

## Detect before you write

Run this from the directory you are about to edit. It is cheap, and it prevents
the most common class of rejected change.

```bash
# Where am I, and what owns this area?
git rev-parse --show-toplevel
find . -maxdepth 0 -o -name "CLAUDE.md" -o -name "AGENTS.md" -o -name "README.md" | head

# Walk up for the nearest instructions and project config
D=$PWD; R=$(git rev-parse --show-toplevel)
while [ "$D" != "$R" ] && [ "$D" != "/" ]; do
  ls "$D"/{CLAUDE.md,AGENTS.md,pyproject.toml,package.json,setup.cfg,go.mod,Makefile,justfile} 2>/dev/null
  D=$(dirname "$D")
done
ls "$R"/{CLAUDE.md,AGENTS.md,pyproject.toml,package.json,Makefile,justfile,.pre-commit-config.yaml} 2>/dev/null
```

Then read, in this order, stopping when you have your answer:

1. **The nearest `CLAUDE.md` or `AGENTS.md`** walking up from your file. Claude
   Code loads these automatically as you touch files — but read them
   deliberately when starting in a new area.
2. **The nearest project config** — `pyproject.toml`, `package.json`,
   `setup.cfg`, `go.mod`. This tells you the real lint, format, type-check, and
   test commands. Never guess them; a wrong `pytest` invocation in a monorepo
   usually means you ran the wrong package's suite.
3. **The two or three files closest to the one you are changing.** These are the
   strongest signal. Read them for import style, error handling, naming, logging,
   docstring format, and how much abstraction is normal here.
4. **The nearest test directory**, for how tests are named, structured, and what
   fixtures already exist.

## What to extract

Before your first edit, be able to answer:

- **Commands** — how do I lint, format, type-check, and test *this package*?
- **Layout** — where does source live, where do tests live, and what is the
  naming convention for each?
- **Idiom** — what does error handling look like here? Logging? Config? Are type
  hints used consistently, or not at all?
- **Density** — how much do these files comment, and how large are the functions?
  Match it. Code that is dramatically more or less commented than its neighbors
  reads as machine-written.
- **Boundaries** — what does this package import, and what imports it? Changing a
  shared module has a blast radius the local tests will not catch.

State what you found in a few bullets before writing code. If two sources
conflict, the nearer one wins, and say that you noticed the conflict.

## Monorepo-specific traps

- **A repo-root test command may run 40 packages.** Find the one that runs
  yours, and use it for the inner loop.
- **Style varies by era.** A directory last touched three years ago may use
  patterns the repo has since abandoned. Match the directory unless it is
  actively being migrated — check recent commits to that path with
  `git log --oneline -10 -- <path>`.
- **Shared modules are not yours to reshape.** If a change wants an edit to a
  widely imported module, count the callers with `grep`/Grep first and say what
  you found before proceeding.
- **CI may enforce something no local config mentions.** Check `.github/workflows`
  or equivalent for the checks that actually gate merge.

## Write it down

When you discover a convention that was not discoverable — an undocumented
command, a non-obvious layout rule, a gotcha that cost you a cycle — add it to
the **nearest** `CLAUDE.md`, creating one in that package if needed. Root
`CLAUDE.md` is for repo-wide truth only; package-level facts belong next to the
package, where they will be loaded exactly when relevant and nowhere else.
