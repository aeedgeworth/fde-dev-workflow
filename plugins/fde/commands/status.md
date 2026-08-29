---
description: Reconcile a spec's ledger against reality by re-running its evidence
argument-hint: "[spec-ref]"
allowed-tools: Bash, Read, Glob, Grep
---

# /fde:status

Verify, don't report. A ledger that merely *claims* progress is the thing that
drifts; this command re-derives progress from the repo.

## With no argument — roll-up

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_store.py" list
```

Print the table as-is, then name the most recently touched spec and its next
unchecked task. Stop there.

## With a spec ref — reconcile

1. Resolve and read the spec:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_store.py" resolve "<ref>"
   ```

2. **Re-run the evidence for every checked task.** Report each as pass or fail.
3. **Diff the ledger against git.** For each checked task, confirm its `done:`
   SHA exists and touched files overlapping the task's `touches:` paths:

   ```bash
   git log --oneline -20
   git show --stat --oneline <sha>
   ```

4. **Look for unrecorded work.** Compare the branch diff against the ledger:

   ```bash
   git diff --stat "$(git merge-base HEAD main 2>/dev/null || echo HEAD~10)"
   ```

   Files changed substantially that no task claims are drift too — the ledger is
   missing a task, or someone worked outside the plan.

5. **Check the spec is still true.** Read `SPEC.md`'s acceptance criteria
   against what the code now does. Flag any criterion the implementation has
   quietly outgrown.

## Report

Print exactly these four sections, each with concrete file and task references:

- **Verified** — checked tasks whose evidence still passes.
- **Drifted** — checked tasks whose evidence now fails, or whose commit is
  missing. This is a defect, not a status update; say what to do about it.
- **Unrecorded** — changes in the working tree or branch that no task claims.
- **Remaining** — unchecked tasks, in order, with the next one called out.

End with a one-line verdict: `clean`, or `N drifted / M unrecorded`.

## Rules

- Read-only. Never fix drift here — report it and let `/fde:build` fix it.
- If an evidence command cannot run (missing dependency, no cluster, no
  credentials), say so explicitly rather than counting it as either pass or fail.
