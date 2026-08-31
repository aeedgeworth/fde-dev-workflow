---
description: Resume active work or reconcile a spec ledger against repository evidence
argument-hint: "[spec-ref]"
allowed-tools: Bash, Read, Glob, Grep, Skill
---

# /fde:status

Load the `fde-workflow` skill.

- With no arguments, run its lightweight **Resume** mode and do not re-run
  historical verification.
- With `$ARGUMENTS`, run its read-only **Reconcile** mode for that spec. Re-run
  only safe local checks; never execute remote or stateful verification merely
  to report status.
