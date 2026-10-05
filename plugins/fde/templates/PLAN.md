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

Each delivery task names the acceptance criteria it advances with `covers:`;
every criterion in SPEC.md needs at least one covering task. A **spike**
answers a question that blocks a decision: it has a timebox instead of a verify
step, records its answer in the spec's Decision log, and may rewrite the tasks
after it. Put spikes first. `spec_store.py check` enforces this structure.

## Tasks

- [ ] **T1** Spike: <question whose answer changes the plan>
  - timebox: <e.g. 1 hour, or one session>
  - resolves: <assumption or open question it settles>

- [ ] **T2** <one-sentence observable outcome>
  - covers: AC1
  - verify: `<safe command that demonstrates the outcome, when one exists>`
  - paths: `<expected paths, optional>`

- [ ] **T3** <outcome>
  - covers: AC2
  - verify: `<command or concise manual check>`
  - paths: `<expected paths, optional>`

When complete, check the task and add:

```text
  - done: <YYYY-MM-DD> · <short-sha|uncommitted>
```

## Notes

<!-- Scratch space for the current build: things discovered, dead ends, and
     anything that should graduate into the spec's Decision log. -->
