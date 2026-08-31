---
name: git-convention
description: Fallback branch, commit, and pull-request conventions for fde work. Use when creating git history and the target repository does not define a stronger local convention.
---

# Git convention

Follow the target repository's documented and recent conventions first. Use the
shape below only as a personal fallback when the repository is silent.

## Types

Used identically in branch names and commit subjects:

| Type | For |
| --- | --- |
| `feat` | New user-visible capability |
| `fix` | Corrects broken behavior |
| `refactor` | Restructuring with no behavior change |
| `perf` | Behavior unchanged, measurably faster or cheaper |
| `test` | Tests only |
| `docs` | Documentation only |
| `build` | Dependencies, packaging, bundle config |
| `ci` | Pipelines and automation |
| `chore` | Everything else with no production impact |

If a change spans types, pick the one a reader most needs to know about — and
consider whether it should be two commits.

## Branches

```
<type>/<spec-id>-<short-slug>      feat/003-schema-drift-guard
<type>/<short-slug>                fix/genie-space-timeout
```

- Lowercase, hyphens, no underscores. Three to five words in the slug.
- Include the spec id when the work has one — it is how the branch, the ledger,
  and the PR stay connected.
- Discover the repository's default branch; do not assume it is `main`.
- Never commit directly to the default branch. Never force-push a branch someone
  else may have pulled; if you must rewrite your own, use `--force-with-lease`.

## Commits

```
<type>(<scope>): <imperative subject, ≤72 chars, no trailing period>

<body: why this change, and what a reader would otherwise wonder about.
 Wrap at 72. Omit entirely if the subject is genuinely self-explanatory.>

Spec: <spec-id> <task-id>
```

- **Subject is imperative** — "add schema drift guard", not "added" or "adds".
- **Scope** is the package or area (`ingest`, `dabs`, `cli`). Omit if the repo
  does not use scopes; match the repo's existing log either way.
- **The body explains *why*.** The diff already shows what. Good bodies cover:
  the reason this approach over the obvious one, a constraint that is not
  visible in the code, or a consequence a reviewer should check.
- **The `Spec:` trailer links repository history to the external spec.** Include
  it when committing spec-driven work.

**One logical change per commit.** A commit that both fixes a bug and reformats
a file is two commits. Never bundle an unrelated refactor into a feature commit
— it makes review harder and `git bisect` useless.

The ledger lives outside the repository. Update it after verification; never
attempt to include it in the code commit or record a commit's SHA inside that
same commit.

## Pull requests

Title: the commit subject format, without the scope-level noise —
`feat: reject mid-run schema changes with a named error`.

Body:

```markdown
## Summary
2-3 bullets: the problem, and what this does about it.

## Approach
A short paragraph on how, plus any decision made during the build that a
reviewer would otherwise question.

## Verification
- What was run, and what passed — real commands, copy-pasteable.
- Acceptance criteria with status.

## Not included
Deliberate exclusions, deferrals, and anything waived — with the reason.
```

Write for a reviewer who has no access to the spec and was not in the session.
Everything they need to judge the change goes in the body.

- Do not merge your own PR as part of an automated flow — open it and stop.
- Draft PRs are for work that is genuinely incomplete, and say what is missing.
