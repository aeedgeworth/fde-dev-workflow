---
spec: {{ID}}
updated: {{DATE}}
---

# Plan: {{TITLE}}

Ordered task ledger. One line of work per task, each with the verification that
proves it. Keep this under ~15 tasks — if it grows past that, the work wants to
be two specs, not a longer list.

Checked tasks carry `done: <date> · <short-sha|uncommitted>`. Repository commits
link back with a `Spec:` trailer. The external ledger records the SHA after the
commit succeeds; it is never part of the code commit itself.

## Tasks

- [ ] **T1** <one-sentence observable outcome>
  - verify: `<safe command that demonstrates the outcome, when one exists>`
  - paths: `<expected paths, optional>`

- [ ] **T2** <outcome>
  - verify: `<command or concise manual check>`
  - paths: `<expected paths, optional>`

When complete, check the task and add:

```text
  - done: <YYYY-MM-DD> · <short-sha|uncommitted>
```

## Notes

<!-- Scratch space for the current build: things discovered, dead ends, and
     anything that should graduate into the spec's Decision log. -->
