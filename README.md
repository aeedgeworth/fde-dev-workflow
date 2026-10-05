# fde-dev-workflow

A lightweight development workflow for Claude Code, Codex, and Cursor, with
optional persistent specs for complex or multi-session work. It is especially
useful for Databricks changes in large monorepos.

The default is deliberately simple: ask the coding agent for an outcome and let
it inspect, implement, verify, and report. Reach for FDE when the work needs a
durable scope boundary, decision record, or resumable execution plan.

## Install

### Claude Code

```bash
claude plugin marketplace add <github-user>/fde-dev-workflow
claude plugin install fde@adam-fde
```

### Codex

Add the repository as a marketplace:

```bash
codex plugin marketplace add <github-user>/fde-dev-workflow
```

Start a new Codex session, open `/plugins`, choose the `adam-fde` marketplace,
and install `fde`. This repository's legacy marketplace file is understood by
both hosts; the plugin itself also has a native `.codex-plugin/plugin.json`.

To bring an existing Claude installation into Codex instead, run `/import` in
Codex CLI, choose Claude Code, and select the FDE plugin and related setup.

### Cursor

Skills, commands, and hooks are the same files. If FDE is already installed in
Claude Code, enable **Include third-party Plugins, Skills, and other configs**
in Cursor and reload the window; Cursor imports that installation directly. Do
not also install a local copy, because Cursor currently loads both sources.

For Cursor-only use or native-plugin development, mirror the plugin into
Cursor's local-plugin root:

```bash
mkdir -p ~/.cursor/plugins/local/fde
rsync -a --delete "$(pwd)/plugins/fde/" ~/.cursor/plugins/local/fde/
```

This uses a real directory because some Cursor builds reject symlinks whose
targets are outside the local-plugin root. It also removes stale files from
earlier versions. Reload the window, then confirm `fde` under Customize. A
`.cursor-plugin/marketplace.json` at the repository root is available if you
later import this repo as a Cursor team marketplace.

Set the same `DEV_WORKFLOW_HOME` for Claude, Codex, and Cursor if they should
share the spec store. Ensure that location is writable under the host's sandbox
policy.

## Choose the lightest useful workflow

### Contained work

Ask directly. A useful request identifies the goal, relevant context or paths,
important constraints, and what must be true when the work is done. No FDE
artifact is required.

### Complex or multi-session work

Claude Code exposes thin command adapters:

```text
/fde:spec "<rough idea>"       create SPEC.md and PLAN.md (--lite | --deep)
/fde:build                     implement the active plan
/fde:status                    resume active work
/fde:status <spec-ref>         reconcile the ledger against repository evidence
/fde:ship --no-pr              validate and review without external actions
/fde:ship                      validate, review, push, and open a PR
```

In Codex, invoke the shared skill directly:

```text
$fde-workflow plan <rough idea>
$fde-workflow build
$fde-workflow resume
$fde-workflow reconcile <spec-ref>
$fde-workflow ship --no-pr
```

Cursor uses the same command files as slash commands (`/spec`, `/build`,
`/status`, `/ship`; the host may prefix the plugin name) and the same
`fde-workflow` skill (`/fde-workflow`).

Planning discovers before it asks. The agent answers what it can from the
repository and, for Databricks work, from read-only workspace queries with an
explicit profile. It then asks only about material unknowns, records reversible
choices as assumptions, and turns questions that only experiment can answer into
time-boxed spike tasks. `--lite` skips the interview; `--deep` keeps interviewing
until every material unknown is settled. Before the plan is handed off,
`spec_store.py check` verifies that every acceptance criterion has a covering
task, and a fresh-context reviewer looks for untestable, ambiguous, or
unsupported statements.

Build mode completes the safe remaining scope by default. Use `--step` when you
want exactly one ledger task and `--commit` when you want the agent to create
coherent commits. Commits are not an implicit side effect of implementation.

## Persistent artifacts

FDE keeps two files with different lifecycles:

- `SPEC.md` records the problem, discovered context, scope, non-goals,
  approach, decisions, assumptions, acceptance criteria, risks, and decision log.
- `PLAN.md` is the mutable ordered ledger of spikes and outcomes, each outcome
  naming the acceptance criteria it covers and its verification.

Specs live outside the client repository under `$DEV_WORKFLOW_HOME`, defaulting
to `~/dev-workflow`, and are keyed by the Git remote:

```text
~/dev-workflow/specs/github.com__owner__repo/003-schema-drift-guard/
```

Because the ledger is external, it is never placed in the code commit. A checked
task records `done: <date> · uncommitted` until its implementation is committed;
the ledger is then updated with the short SHA. The commit's
`Spec: <spec-id> <task-id-list>` trailer provides the reverse link. Set the same
`DEV_WORKFLOW_HOME` for Claude, Codex, and Cursor if they should share the store.
Ensure that location is writable under the host's sandbox policy.

Resume is intentionally cheap. Explicit reconciliation checks recorded SHAs,
`Spec:` trailers, changed paths, and safe local verification commands. Remote
deployments, jobs, migrations, and other stateful checks are never rerun merely
to report status.

## Skills

| Skill | Purpose |
| --- | --- |
| `fde-workflow` | Plan, build, resume, validate, and ship persistent work |
| `databricks-workflow` | Explicit profiles and proportionate local/remote validation |
| `git-convention` | Fallback branch, commit, and PR conventions when the repo is silent |
| `clean-code` | KISS/YAGNI, rule-of-three, explicit behavior, and focused diffs |
| `testing` | Behavioral tests, meaningful red steps, and equivalence-class coverage |
| `repo-conventions` | Discover authoritative local commands and patterns before editing |

The target repository's nearest `CLAUDE.md`, `AGENTS.md`, project configuration,
neighboring code, tests, and CI remain authoritative. FDE does not create or
modify repository instruction files without explicit permission.

## Hooks

Two small hooks are bundled:

- Session start reports the newest non-terminal spec and next task. It is
  silent when no active spec exists and does not create an empty store.
- Before shell execution, the guard blocks common explicit spellings of
  production Databricks or Terraform operations, bundle destruction, unsafe
  force-pushes, and pushes to the detected default branch. Repositories whose
  default branch is `main` or `master` are handled identically (`trunk` is also
  supported).

Claude Code wires these as `SessionStart` and `PreToolUse` (Bash). Cursor
wires the same scripts as `sessionStart` and `beforeShellExecution`.

For an engagement whose only workspace is named production, declare it once so
routine deploys are not treated as promotions — `bundle destroy` stays blocked:

```toml
# ~/dev-workflow/specs/<repo-key>/fde.toml
[safety]
single_workspace = true
```

The command guard is defense-in-depth, not a complete security boundary. Host
sandboxing, approvals, and the instruction that production actions are
user-only remain authoritative. After explicit user authorization, prefix one
command with `FDE_GUARD_OVERRIDE=1` for a loud, transcript-visible override;
later commands remain protected. Formatting is run through each repository's
normal validation commands rather than a silent post-edit hook.

## Layout

```text
.claude-plugin/marketplace.json       marketplace understood by Claude and Codex
.cursor-plugin/marketplace.json        Cursor team-marketplace manifest
plugins/fde/
  .claude-plugin/plugin.json          Claude plugin manifest
  .codex-plugin/plugin.json           Codex plugin manifest
  .cursor-plugin/plugin.json         Cursor plugin manifest
  commands/                           thin command adapters
  skills/                             shared workflow skills
  hooks/                              session orientation and command guard
  scripts/spec_store.py               deterministic external-spec storage
  templates/                          SPEC.md and PLAN.md
tests/                                script and guard regression tests
```

## Develop and verify

After editing the plugin, run:

```bash
python3 -m unittest discover -s tests -v
claude plugin validate .
claude plugin validate plugins/fde
# Only when testing the native Cursor plugin rather than Claude import:
rsync -a --delete "$(pwd)/plugins/fde/" ~/.cursor/plugins/local/fde/
```

Refresh or reinstall the plugin and start a new session before testing changed
skills or hooks. Add durable instructions only after repeated, observed friction;
keep one-off constraints in the request that needs them.
