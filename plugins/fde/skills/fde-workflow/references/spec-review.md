# Spec review

A pre-build review of `SPEC.md` and `PLAN.md` by a reader who did not write
them. The author has the whole conversation in mind and cannot see what the
documents fail to say; the reviewer has only the documents and the repository,
which is exactly what a later build session will have.

## How to run it

Run `spec_store.py check <ref>` first and fix every error. Then:

- **With subagents** (Claude Code, and hosts with an equivalent): start a fresh
  subagent with read-only tools. Give it the two file paths, the repository
  path, and the brief below. Do not summarize the conversation for it.
- **Without subagents:** reread both files from the top as if seeing them for
  the first time and apply the same brief to yourself.

Fix findings the author can resolve alone. Bring the rest to the user as
questions. Record material changes in the Decision log.

## Brief for the reviewer

You review a development spec before any code is written. You never modify
files. Read `SPEC.md` and `PLAN.md` in full, and inspect the repository where a
claim depends on it.

Report findings under these headings, most severe first, each quoting the
section it concerns:

- **Untestable** — an acceptance criterion with no observable check, or one
  that relies on a subjective word (fast, clean, robust, intuitive) without a
  threshold.
- **Ambiguous** — a statement two competent engineers would implement
  differently. Give both readings.
- **Unsupported** — a fact under Context with no source, or a claim about the
  repository or data that the repository contradicts.
- **Hidden assumption** — something the plan depends on that appears in neither
  Context nor Assumptions.
- **Gap** — a scope item no task delivers, a task that delivers nothing in
  scope, or a risk with no mitigation.
- **Misordered** — a task that depends on a later one, or a spike scheduled
  after the work it should inform.

For each finding, propose concrete replacement text. If a section is sound, say
nothing about it. End with one line: `ready to build` or
`N findings block building`.
