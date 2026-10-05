# fde-dev-workflow

A lightweight development workflow for Claude Code, Codex, and Cursor, with
optional persistent specs for complex or multi-session work. It is especially
useful for Databricks changes in large monorepos.

The default is deliberately simple: ask the coding agent for an outcome and let
it inspect, implement, verify, and report. Reach for FDE when the work needs a
durable scope boundary, decision record, or resumable execution plan.

## Requirements

- **git**. Specs are keyed by the repository's `origin` remote.
- **Python 3.9 or newer** as `python3` on `PATH`. The macOS system Python
  qualifies. Reading the optional `fde.toml` setting needs Python 3.11+; on
  older versions the guard ignores that file and stays at its strict default.
- The **Databricks CLI** with configured profiles, only for Databricks work.

Check with `git --version` and `python3 --version`.

## Install

The repository is public; no GitHub authentication is needed.

### Claude Code

```bash
claude plugin marketplace add aeedgeworth/fde-dev-workflow
claude plugin install fde@adam-fde
claude plugin list            # expect fde@adam-fde, enabled
```

Start a new Claude Code session. `/fde:spec`, `/fde:build`, `/fde:status`, and
`/fde:ship` are then available, and the session-start and command-guard hooks
are active.

### Codex

```bash
codex plugin marketplace add aeedgeworth/fde-dev-workflow
codex plugin add fde@adam-fde
codex plugin list             # expect fde@adam-fde, installed, enabled
```

Start a new Codex session and invoke the skill as `$fde-workflow`. Codex loads
the plugin's skills only: the session-start summary and the command guard are
not active there, so rely on Codex's own sandbox and approval settings.

You can also install interactively from `/plugins` in a Codex session, or run
`/import` to bring over an existing Claude Code installation.

### Cursor

**If Claude Code is installed on the same machine**, install FDE there first,
then in Cursor enable **Include third-party Plugins, Skills, and other
configs** and reload the window. Cursor imports the Claude installation
directly. Do not also install a local copy; Cursor would load both.

**For Cursor alone**, clone the repository and copy the plugin into Cursor's
local-plugin folder:

```bash
git clone https://github.com/aeedgeworth/fde-dev-workflow.git
mkdir -p ~/.cursor/plugins/local/fde
rsync -a --delete fde-dev-workflow/plugins/fde/ ~/.cursor/plugins/local/fde/
```

Reload the window and confirm `fde` appears under Customize. A copy is used
rather than a symlink because some Cursor builds reject symlinks that point
outside the local-plugin folder. A `.cursor-plugin/marketplace.json` at the
repository root is available for importing this repository as a Cursor team
marketplace.

### Share specs between tools and machines

Specs are stored in `~/dev-workflow` by default, separately on each machine. To
share them, set `DEV_WORKFLOW_HOME` to one location in your shell profile:

```bash
# ~/.zshrc or ~/.bashrc — a synced folder or a private git repository
export DEV_WORKFLOW_HOME="$HOME/path/to/shared/dev-workflow"
```

Hosts launched from a GUI rather than a terminal may not read your shell
profile; for Claude Code, also set it in the `env` block of
`~/.claude/settings.json`. The location must be writable under each host's
sandbox policy. File sync does not merge simultaneous edits, so avoid working
on the same spec from two machines at once.

### Update

Hosts install by version, so an update is picked up when the plugin version
changes.

```bash
# Claude Code (restart the session afterwards)
claude plugin marketplace update adam-fde
claude plugin update fde@adam-fde

# Codex (start a new session afterwards)
codex plugin marketplace upgrade adam-fde
codex plugin add fde@adam-fde

# Cursor-only install
git -C fde-dev-workflow pull
rsync -a --delete fde-dev-workflow/plugins/fde/ ~/.cursor/plugins/local/fde/
```

A Cursor install imported from Claude Code updates with Claude Code.

### Uninstall

```bash
claude plugin uninstall fde@adam-fde
codex plugin remove fde@adam-fde
rm -rf ~/.cursor/plugins/local/fde
```

Your specs in `$DEV_WORKFLOW_HOME` are left untouched.

## Choose the lightest useful workflow

### Contained work

Ask directly. A useful request identifies the goal, relevant context or paths,
important constraints, and what must be true when the work is done. No FDE
artifact is required.

### Complex or multi-session work

Claude Code exposes thin command adapters:

```text
/fde:spec [--lite|--deep] "<idea, or path to notes>"   create SPEC.md and PLAN.md
/fde:build [spec-ref]                                  implement the plan
/fde:status                                            resume: list specs and the next task
/fde:status <spec-ref>                                 reconcile the ledger against the repo
/fde:ship --no-pr                                      validate and review without pushing
/fde:ship                                              validate, review, push, and open a PR
```

In Codex, invoke the shared skill directly:

```text
$fde-workflow plan [--lite|--deep] <idea, or path to notes>
$fde-workflow build [spec-ref]
$fde-workflow resume
$fde-workflow reconcile <spec-ref>
$fde-workflow ship --no-pr
```

Cursor uses the same command files as slash commands (`/spec`, `/build`,
`/status`, `/ship`; the host may prefix the plugin name) and the same
`fde-workflow` skill (`/fde-workflow`).

### Starting something new

1. Create the repository and its remote **before** the first spec:
   `git init`, then `git remote add origin <url>`. Specs are filed under the
   `origin` URL; a repository with no remote uses a local key, and adding the
   remote later leaves earlier specs under the old key.
2. Run `/fde:spec --deep "<idea>"` and answer the interview.
3. Read `SPEC.md`. Confirm the Assumptions table and the acceptance criteria;
   this is the cheapest point to correct course.
4. Run `/fde:build`, or `/fde:build --step` to review one task at a time.
5. In later sessions, the session-start hook names the active spec and next
   task; run `/fde:build` to continue.
6. Finish with `/fde:ship --no-pr`, or `/fde:ship` to open a pull request.

The spec, not the conversation, carries the work, so a fresh agent can build a
spec another agent wrote.

### Planning

Planning discovers before it asks. The agent answers what it can from the
repository and, for Databricks work, from read-only workspace queries with an
explicit profile. It then asks only about material unknowns, records reversible
choices as assumptions, and turns questions that only experiment can answer into
time-boxed spike tasks.

- `--lite` skips the interview unless a decision truly blocks progress.
- The default asks one round of at most five questions.
- `--deep` interviews in rounds, with no cap, until every material unknown is
  answered, agreed as an assumption, or planned as a spike.

Before the plan is handed off, `spec_store.py check` verifies that every
acceptance criterion has a covering task, and a fresh-context reviewer looks
for untestable, ambiguous, or unsupported statements.

### Building

Without a spec reference, build, resume, and ship use the most recently edited
spec that is not shipped, complete, abandoned, or cancelled. When a repository
has several open specs, pass one explicitly by number (`004`), slug
(`schema-drift-guard`), or any unique part of the name. An ambiguous reference
is rejected rather than guessed.

Build completes the safe remaining scope by default. Use `--step` for exactly
one ledger task, `--task T3` for a specific one, and `--commit` when you want
the agent to create coherent commits. Commits are not an implicit side effect of
implementation.

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
`Spec: <spec-id> <task-id-list>` trailer provides the reverse link.

Resume is intentionally cheap. Explicit reconciliation checks recorded SHAs,
`Spec:` trailers, changed paths, acceptance-criteria coverage, and safe local
verification commands. Remote deployments, jobs, migrations, and other stateful
checks are never rerun merely to report status.

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

Two small hooks are bundled for Claude Code and Cursor:

- Session start reports the newest non-terminal spec and next task. It is
  silent when no active spec exists and does not create an empty store.
- Before shell execution, the guard blocks common explicit spellings of
  production Databricks or Terraform operations, bundle destruction, unsafe
  force-pushes, and pushes to the detected default branch. Repositories whose
  default branch is `main` or `master` are handled identically (`trunk` is also
  supported).

Claude Code wires these as `SessionStart` and `PreToolUse` (Bash). Cursor
wires the same scripts as `sessionStart` and `beforeShellExecution`. Codex does
not run them.

For an engagement whose only workspace is named production, declare it once so
routine deploys are not treated as promotions — `bundle destroy` stays blocked.
This setting needs Python 3.11+:

```toml
# $DEV_WORKFLOW_HOME/specs/<repo-key>/fde.toml
[safety]
single_workspace = true
```

The command guard is defense-in-depth, not a complete security boundary. It
matches command text, so it can also block a harmless command that merely
contains a risky string, such as an `echo` into a runbook. Host sandboxing,
approvals, and the instruction that production actions are user-only remain
authoritative. After explicit user authorization, prefix one command with
`FDE_GUARD_OVERRIDE=1` for a loud, transcript-visible override; later commands
remain protected. Formatting is run through each repository's normal validation
commands rather than a silent post-edit hook.

## Layout

```text
.claude-plugin/marketplace.json        marketplace understood by Claude and Codex
.cursor-plugin/marketplace.json        Cursor team-marketplace manifest
plugins/fde/
  .claude-plugin/plugin.json           Claude plugin manifest
  .codex-plugin/plugin.json            Codex plugin manifest
  .cursor-plugin/plugin.json           Cursor plugin manifest
  commands/                            thin command adapters
  skills/                              shared workflow skills
  skills/fde-workflow/references/      discovery question bank and spec-review brief
  hooks/                               session orientation and command guard
  scripts/spec_store.py                external spec store: new, list, active, resolve, check
  templates/                           SPEC.md and PLAN.md
tests/                                 script, guard, and manifest regression tests
```

## Develop and release

After editing the plugin, run:

```bash
python3 -m unittest discover -s tests -v
claude plugin validate .
claude plugin validate plugins/fde
# Only when testing the native Cursor plugin rather than Claude import:
rsync -a --delete "$(pwd)/plugins/fde/" ~/.cursor/plugins/local/fde/
```

To release, bump the version in all three manifests together, because hosts
only pick up a new version:

- `plugins/fde/.claude-plugin/plugin.json` and `.cursor-plugin/plugin.json`:
  `X.Y.Z`
- `plugins/fde/.codex-plugin/plugin.json`: `X.Y.Z+codex.<YYYYMMDDHHMMSS>`
- the expected version in `tests/test_manifests.py`

Then push to `main` and update each installation as described under Update.
Add durable instructions only after repeated, observed friction; keep one-off
constraints in the request that needs them.
