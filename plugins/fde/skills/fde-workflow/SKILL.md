---
name: fde-workflow
description: Plan, resume, implement, or ship explicitly spec-driven development work using an external SPEC.md and PLAN.md. Use when the user invokes an fde stage, asks for a persistent development plan, or resumes multi-session work. Do not trigger for ordinary contained code changes.
---

# FDE workflow

Use persistent artifacts only when the user explicitly asks for this workflow or
when work genuinely needs to survive multiple sessions. For ordinary changes,
work directly from the request and the repository's own instructions.

The workflow has five modes: **plan**, **build**, **resume**, **reconcile**, and
**ship**. Infer the mode from the request; ask only when it is genuinely
ambiguous.

## Shared rules

- Inspect the repository before asking questions or proposing changes. Read the
  nearest `CLAUDE.md`, `AGENTS.md`, project configuration, neighboring code,
  tests, and relevant CI configuration. Nearer conventions win.
- Treat the user's requested outcome and acceptance criteria as the boundary.
  Do not add adjacent refactors, dependencies, or instruction-file changes
  without agreement.
- Prefer observable verification. Show a regression fail before fixing it when
  that is meaningful; do not manufacture a failing command for documentation,
  configuration, or behavior-preserving work.
- Work autonomously through safe, in-scope tasks. Stop for authority you do not
  have (production, another team's workspace), a material product decision,
  irreversible impact, or a genuine blocker—not after every routine task, and not
  merely because a step calls a remote service you are already authenticated to.
- Never deploy to production, merge a pull request, force-push a shared branch,
  or change repository instruction files without explicit authorization.

## Locate persistent specs

Resolve this skill's plugin root from the location of this `SKILL.md`; the store
helper is `../../scripts/spec_store.py` from the skill directory. Run it with
Python 3:

```text
python3 <plugin-root>/scripts/spec_store.py new "<title>"
python3 <plugin-root>/scripts/spec_store.py active
python3 <plugin-root>/scripts/spec_store.py resolve "<ref>"
python3 <plugin-root>/scripts/spec_store.py list
```

Specs live under `DEV_WORKFLOW_HOME` when set, otherwise under
`~/dev-workflow`. They are external state: they do not belong to the code
repository's commits.

## Plan

Use this mode for `/fde:spec`, `$fde-workflow plan`, or an explicit request for
a persistent spec.

1. Ground the request in the repository and summarize only the facts that
   materially shape the work.
2. Ask one concise set of unresolved, high-impact questions. Prefer stated
   assumptions when a reversible choice is safe. `--lite` skips the interview
   unless a decision truly blocks progress.
3. Create the spec directory with `spec_store.py new`, then copy the plugin's
   `templates/SPEC.md` and `templates/PLAN.md` into it.
4. Write concrete scope, tempting non-goals, the chosen approach, meaningful
   decisions, observable acceptance criteria, and change-specific risks. Use
   `None` when a section genuinely has no content rather than inventing it.
5. Create a short ordered ledger. Each task is an outcome, leaves the repository
   usable, names a verification command when one exists, and stays under roughly
   15 tasks. Split work that is too large to reason about as one change.
6. Report the artifact path, first task, and any remaining blocker.

`SPEC.md` contains durable why/what. `PLAN.md` contains mutable execution state.
Do not duplicate the same fact in both.

## Build

Use this mode for `/fde:build` or `$fde-workflow build`.

1. Resolve the requested spec, or use `active` when no reference is given. Read
   both files fully and set the spec status to `active` when work begins.
2. Load `repo-conventions` when the target area's practices are not already
   known. Apply `clean-code` and `testing` when the task involves non-trivial
   implementation or tests. For Databricks work, load `databricks-workflow`
   before running Databricks commands.
3. Work the next task, a requested task, or the remaining ledger by default.
   `--step` limits the run to one task. `--worktree` explicitly authorizes
   creating an isolated worktree after checking its required local state.
4. Run the narrow verification for each completed outcome and the surrounding
   relevant checks. Mark a task complete only after seeing its verification
   succeed. Record `done: <YYYY-MM-DD> · uncommitted` until the implementation
   has a repository commit.
5. If reality changes scope or a durable decision, update the affected spec
   section and append a dated explanation to the Decision log.
6. Do not create commits unless the user requests them or passes `--commit`.
   When committing, group coherent review units and add a
   `Spec: <spec-id> <task-id-list>` trailer. After the commit succeeds, replace
   `uncommitted` for those tasks with the short commit SHA. The external ledger
   is updated after the commit; it is never included in that repository commit.
   Follow repository conventions; load `git-convention` only when the repository
   is silent.
7. Report completed outcomes, verification performed, and anything remaining.

Two unsuccessful implementation approaches are a cue to reassess and explain
the blocker, not an automatic stopping rule when another safe, informed path is
available.

## Resume

Use this mode when asked for status or where the work left off.

- With no reference, run `spec_store.py list` and identify the active spec.
- With a reference, read its spec and plan, inspect current git state, and report
  completed and remaining outcomes plus the next useful action.
- Do not re-run every historical verification command. Re-run a check only when
  the user asks for reconciliation or current repository changes give a concrete
  reason to doubt it.
- Never run deployments, jobs, migrations, or other stateful operations merely
  to produce a status report.

## Reconcile

Use this mode for `/fde:status <spec-ref>`, `$fde-workflow reconcile`, or an
explicit request to check the ledger against the repository.

1. Resolve and read the spec and plan. Inspect the working tree and branch
   without modifying either.
2. For every checked task with a commit SHA, confirm that the commit exists, its
   message has a `Spec:` trailer naming the spec and task, and its changed files
   overlap the task's declared `paths` when paths were recorded.
3. Treat `done: <date> · uncommitted` as unresolved state. Confirm the task's
   paths are represented in the working-tree or branch diff, but do not call it
   clean until a commit SHA is recorded.
4. Re-run each checked task's `verify` command only when it is safe, local, and
   non-mutating. Never automatically deploy, run a remote job, migrate data,
   alter grants, or invoke another stateful check. Report those as unavailable
   unless the user explicitly authorizes them.
5. Discover the comparison base from the branch upstream or remote default
   branch. If neither exists, use the repository's root commit and state that
   fallback. Never hardcode `main` or assume deep history exists.
6. Compare changed files with all ledger `paths`, and compare the implementation
   with the acceptance criteria and non-goals.

Report **Verified**, **Drifted**, **Unrecorded**, **Unavailable**, and
**Remaining** with task and file references. A missing commit or trailer, a safe
verification failure, or a checked task whose paths are absent is drift—not a
status update.

## Ship

Use this mode for `/fde:ship` or `$fde-workflow ship`.

1. Resolve the spec and confirm unfinished tasks, acceptance criteria, and
   unrecorded branch changes. Do not push or open a pull request while
   task-related changes are uncommitted: ask the user to commit them or run
   Build with `--commit`. `--partial` permits a draft handoff only when the
   unfinished work is stated plainly.
2. Run the repository's real format, lint, type-check, and test commands in the
   appropriate scope. Ask before any verification that mutates shared or remote
   state.
3. Review the branch diff against the request, scope, non-goals, and acceptance
   criteria. Use the host's native code-review workflow when available. Use an
   independent audit only for high-risk changes or when requested.
4. Fix findings caused by this work and re-run affected validation. Distinguish
   unrelated pre-existing failures with evidence.
5. With `--no-pr`, stop after validation and review: do not push or create a
   pull request.
6. Otherwise, confirm the branch is not the default branch, push it, and open a
   pull request. The body must stand alone: summary, approach, verification,
   and explicit exclusions or waivers. Do not merge it.
7. After a PR is successfully opened, set the spec status to `shipped` and add
   its URL to the Decision log. If no PR was requested, leave the status
   `active` and report that the work is ready for handoff.
