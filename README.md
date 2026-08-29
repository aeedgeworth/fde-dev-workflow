# fde-dev-workflow

A spec-driven development workflow for Claude Code, packaged as a plugin.
Built for Databricks and Python work in large monorepos.

Four commands, six skills, three hooks. No orchestrator, no daemon, no Python
package to maintain.

## Install

On any machine:

```bash
claude plugin marketplace add <your-github-user>/fde-dev-workflow
claude plugin install fde@adam-fde
```

That is the whole setup. Skills, commands, agents, and hooks travel with it,
versioned and rollback-able.

## The loop

```
/fde:spec "<rough idea>"     interview  ->  SPEC.md + PLAN.md
/fde:build                   work the ledger, one verified task at a time
/fde:status                  re-run the evidence; report drift
/fde:ship                    validate, review, open the PR
```

## Two files, two lifecycles

Most spec systems rot because they mix durable reasoning with live progress.
This one keeps them apart:

- **`SPEC.md` — why and what.** Problem, scope, non-goals, key decisions with
  rationale, acceptance criteria, risks. Changes rarely. When it does, an entry
  is appended to its **Decision log** rather than history being rewritten.
- **`PLAN.md` — how, and where we are.** An ordered task ledger. Every task
  carries an `evidence:` command that fails before the task and passes after,
  and every checked task carries the commit SHA that did it.

Nothing is recorded in both files. There is no separate backlog index to keep in
sync — `/fde:status` derives it.

## How drift is prevented

Plans go stale when the ledger is *asserted* rather than *checked*. Three
mechanisms:

1. **Evidence, not claims.** A box is only ticked after its command is seen to
   pass. `/fde:status` re-runs all of them and reports failures as defects.
2. **The ledger commits with the code.** Same commit, plus a `Spec:` trailer, so
   claimed work can be verified against real history.
3. **A hard cap of ~15 tasks.** Past that the work is two specs. A ledger nobody
   can hold in their head is one that stops being updated.

## Where specs live

Outside the repo, always — under `$DEV_WORKFLOW_HOME` (default `~/dev-workflow`),
keyed by the repo's git remote:

```
~/dev-workflow/specs/github.com__owner__repo/003-schema-drift-guard/
```

A client monorepo's working tree stays clean, nothing can be committed by
accident, and every worktree and clone of a repo resolves to the same specs.
To carry specs between laptops, `git init` that directory and push it privately.

## Skills

| Skill | What it carries |
| --- | --- |
| `spec-writing` | The standard spec shape and how to size work |
| `repo-conventions` | Match the directory you're editing, not the repo root |
| `clean-code` | Clarity over cleverness, KISS/YAGNI, explicit failure modes |
| `testing` | Behavior over implementation, no redundant cases |
| `git-convention` | Branch, commit, and PR format |
| `databricks-workflow` | Profile discipline, skill routing, verification ladder |

`spec-auditor` is a read-only agent that checks an implementation against its
spec's acceptance criteria — the check on a build that drifted from its own plan.

## Hooks

Advisory, with one exception:

- **SessionStart** — prints the active spec and next task. Silent if this repo
  has no specs.
- **PostToolUse** — formats edited files, but *only* with a formatter the project
  itself configures. No config, no formatting.
- **PreToolUse** — **blocks** production bundle deploys, bundle destroys,
  production Terraform, force-pushes, and pushes to the default branch. Override
  loudly with `FDE_ALLOW_PROD=1`.

## Layout

```
.claude-plugin/marketplace.json     this repo as a marketplace
plugins/fde/
  commands/     spec.md  build.md  status.md  ship.md
  skills/       six SKILL.md files
  agents/       spec-auditor.md
  hooks/        hooks.json  guard.py  session_start.py  autoformat.py
  scripts/      spec_store.py
  templates/    SPEC.md  PLAN.md
```

## Tweaking it

Edit a file, then:

```bash
claude plugin marketplace update adam-fde && claude plugin install fde@adam-fde
```

Skills and commands are plain markdown — the prose *is* the behavior. When
Claude gets something wrong twice, write the rule into the relevant skill rather
than re-prompting.
