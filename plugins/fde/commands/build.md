---
description: Implement the next unchecked tasks from a spec's ledger, with evidence
argument-hint: "[spec-ref] [--worktree] [--task T3] [--all]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite
---

# /fde:build

Work the task ledger in `PLAN.md`. One task at a time, each finished and proven
before the next begins.

## 1. Resolve the spec

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_store.py" resolve "<ref>"   # or `active` with no ref
```

Read `SPEC.md` in full and `PLAN.md` in full. If the spec has open questions
that block the next task, stop and ask rather than guessing.

## 2. Set up the workspace

- Default: work in the current checkout on a branch named per the
  `git-convention` skill.
- `--worktree`: create an isolated worktree for this spec instead. Before you
  do, check whether the project needs local state that a fresh worktree will not
  have — a `.venv`, `.env`, `node_modules`, or a config file that is gitignored.
  Say what you found and set it up, or recommend against the worktree.

## 3. Load the working skills

Load `repo-conventions`, `clean-code`, and `testing`. For Databricks work also
load `databricks-workflow`. Follow the conventions of the **directory you are
editing**, not the repo root.

## 4. Work the ledger

For each task (the next unchecked one, or `--task`, or all with `--all`):

1. Restate the task's outcome and its evidence command.
2. **Run the evidence command first** and confirm it fails. If it already
   passes, the task is either done or badly specified — say which, and fix the
   ledger before writing code.
3. Implement the smallest change that satisfies the task. Stay inside the
   `touches:` paths; if you need to go outside them, say so and update the line.
4. Run the evidence command until it passes. Then run the surrounding test file
   or module to confirm nothing nearby broke.
5. Commit per the `git-convention` skill. The ledger update goes in the **same
   commit** as the code — that is what keeps them from drifting.
6. Update the task line in place:

   ```
   - [x] **T3** <outcome>
     - evidence: `<command>`
     - touches: `<paths>`
     - done: <YYYY-MM-DD> · <short SHA>
   ```

Stop after each task and report, unless `--all` was passed.

## 5. Handle divergence

When the code disagrees with the spec — an approach does not work, a decision
turns out wrong, scope needs to move — do **not** silently follow the code:

1. Append a dated entry to `SPEC.md`'s **Decision log** saying what changed and
   why.
2. Amend the affected section of `SPEC.md`.
3. Adjust the remaining ledger tasks.
4. Tell the user what moved, in one or two sentences.

## 6. Report

Print the tasks completed, the evidence that passed, remaining task count, and
the next task. When the ledger is fully checked, print `Next: /fde:ship`.

## Rules

- Never check a box whose evidence command you have not just seen pass.
- Never mark a task done because it "looks right" — the evidence is the standard.
- If you cannot make the evidence pass after two genuine attempts, stop, leave
  the box unchecked, and report what you learned and what you would try next.
