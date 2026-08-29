---
name: spec-writing
description: Write a SPEC.md and PLAN.md in the standard two-file shape — stable why/what separated from a live, verifiable task ledger. Use when creating or revising a spec, writing acceptance criteria, breaking work into tasks, or when a plan has grown stale or too large to track. Triggers on "write a spec", "plan this work", "break this down", "acceptance criteria", or a spec that has drifted from the code.
---

# Spec writing

Two files, deliberately different lifecycles. Most spec systems fail because
they mix them: the durable reasoning gets edited every time a task moves, and
soon nobody trusts either.

- **`SPEC.md` — why and what.** Changes only when scope or a decision changes,
  and when it does, an entry is appended to the Decision log.
- **`PLAN.md` — how, and where we are.** Mutated constantly. Holds the ledger.

Never record the same fact in both. If the plan and the spec disagree about
scope, the spec is wrong and needs a Decision log entry.

## Writing SPEC.md

**Problem.** Observable and specific. "Ingestion silently drops rows when the
source schema adds a column, and we find out days later from a row-count
mismatch" — not "improve ingestion reliability". Name who is hurt and what the
current workaround costs.

**Scope / Non-goals.** Non-goals do the real work. A vague non-goal is the
single biggest cause of a plan that sprawls mid-build. Write the *tempting*
exclusions — the adjacent refactor, the second data source, the config UI — not
the obviously-unrelated ones.

**Approach.** Enough that someone could sketch the design: the components, where
they live in this repo, how control and data flow. Reference real paths. If more
than one approach was viable, the loser belongs in Key decisions, not here.

**Key decisions.** One row per meaningful choice, with the alternative you
rejected and why. This is the section future-you reads when asking "why on earth
is it built like this". A decision with an empty Alternatives column was
probably not a decision.

**Acceptance criteria.** Testable statements about observable behavior.

- Good: "A source column added mid-run fails the job with an error naming the
  column and the table."
- Bad: "Schema changes are handled gracefully."

If you cannot say how you would check one, it is not yet an acceptance
criterion. Push until each names something runnable.

**Risks.** Only risks specific to this change. "The library might have bugs" is
noise. "The backfill rewrites a table other pipelines read, so a mid-backfill
read sees partial data" is a risk.

**Decision log.** Append-only, dated. Every divergence from the plan lands here.
This is what makes a spec that is weeks old still worth reading.

## Writing PLAN.md

A flat, ordered ledger. Each task:

```
- [ ] **T4** Reject a schema change with an error naming the column and table
  - evidence: `pytest tests/ingest/test_schema.py::test_new_column_fails_loudly`
  - touches: `src/ingest/schema.py`, `tests/ingest/test_schema.py`
```

Rules that keep it honest:

- **Every task has an evidence command that fails now and passes after.** No
  evidence, no task. "Refactor the parser" is not a task; "parser handles quoted
  delimiters, proven by `pytest -k quoted`" is.
- **Each task leaves the repo working.** Order so you can stop after any task.
- **One outcome per task**, phrased as a change in behavior, not an activity.
  "Add validation" is an activity. "Invalid config fails at startup with the
  offending key named" is an outcome.
- **Cap at ~15 tasks.** Past that, the work is two specs. Propose the split
  rather than writing a longer list — a ledger nobody can hold in their head is
  a ledger that stops being updated, which is exactly the failure mode this
  design exists to prevent.
- **Checked tasks carry `done: <date> · <sha>`** so `/fde:status` can verify
  rather than trust.

## Lite mode

For work you already understand: same two files, same sections, all short. A
paragraph of Problem, three bullets of Scope, the one decision that matters,
three acceptance criteria, ≤5 tasks. The shape is the point — it is what makes
specs comparable across sessions. Do not drop sections to save time; write one
line instead.

## Sizing

If the interview keeps surfacing new subsystems, or the ledger passes 15 tasks,
or two tasks cannot be ordered because each needs the other — stop. That is one
spec trying to be several. Say so and propose the split.
