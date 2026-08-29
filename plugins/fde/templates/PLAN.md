---
spec: {{ID}}
updated: {{DATE}}
---

# Plan: {{TITLE}}

Ordered task ledger. One line of work per task, each with the evidence that
proves it. Keep this under ~15 tasks — if it grows past that, the work wants to
be two specs, not a longer list.

Checked tasks must carry a `done:` line with the date and commit SHA.
`/fde:status` re-runs the evidence for every checked task and reports drift.

## Tasks

- [ ] **T1** <one-sentence outcome, phrased as a change in behavior>
  - evidence: `<command that passes only when this task is done>`
  - touches: `<paths>`

- [ ] **T2** <outcome>
  - evidence: `<command>`
  - touches: `<paths>`

## Notes

<!-- Scratch space for the current build: things discovered, dead ends, and
     anything that should graduate into the spec's Decision log. -->
