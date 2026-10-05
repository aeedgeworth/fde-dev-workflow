# Discovery and requirements

Read this in Plan mode before asking the user anything. Vague requests usually
become concrete once the agent has looked at the real system; questions are for
what looking cannot answer.

## Triage every unknown

For each gap between the request and a buildable spec, decide which kind it is:

| Kind | Example | Action |
| --- | --- | --- |
| **Observable** | Which table holds orders? What is its grain? | Look it up. Record the fact and its source under Context. |
| **Reversible** | File layout, naming, which of two equivalent libraries | Choose, and record it under Assumptions. |
| **Material** | Who consumes the output? What counts as correct? Latency target? | Ask the user. |
| **Unknowable yet** | Will the source API sustain the needed throughput? | Plan a spike task with a timebox. |

Never ask the user something the repository or workspace can answer. Never
silently assume something material.

## Discovery checklist

Repository, always:

- Existing code, jobs, bundles, and tests that already touch the area.
- How similar work was done before (recent commits to neighboring paths).
- Declared environments, targets, and CI gates.

Databricks workspace, when the work reads or writes workspace objects. Load
`databricks-workflow` first, ask which profile to use, and keep every command
read-only:

- **Data:** the candidate source tables, their schema, grain, approximate row
  counts, freshness (latest partition or timestamp), and null or duplicate rates
  on the keys the work will join on. Use `databricks-data-discovery` or a
  bounded `SELECT` against a dev warehouse.
- **Ownership and access:** table owners and whether the current principal can
  read sources and write to the intended target (`databricks-unity-catalog`).
- **Existing assets:** jobs, pipelines, dashboards, apps, or Genie spaces that
  already produce or consume the same data.
- **Lineage:** upstream producers and downstream consumers of the target, from
  system tables when available.

Stop discovery once the remaining unknowns are material or unknowable. Record
what was examined even when it found nothing; "no existing job writes this
table" is a useful fact.

## Interview depth

- **`--lite`**: no interview. Proceed on stated assumptions unless a decision
  truly blocks progress.
- **Default**: one round of at most five questions, all material, each with a
  recommended answer the user can accept.
- **`--deep`**: rounds of three to five questions until every material unknown
  is resolved, assumed with agreement, or planned as a spike. Restate the
  emerging scope between rounds so the user can correct course early.

Ask with the host's structured-question tool when one exists. Offer concrete
options drawn from discovery instead of open prompts: "Daily batch at 06:00
(the source lands at 04:30), or hourly?" beats "How fresh does it need to be?"

## Question bank

Pick what discovery left open; do not ask all of these.

**Outcome**
- Who uses the result, and what decision or action does it drive?
- What does the user do today instead, and what is wrong with it?
- What would make this a failure even if it technically works?

**Correctness**
- Which existing number, report, or system must the output agree with, and to
  what tolerance?
- What is the grain of one output row?
- How should late, duplicate, or malformed input be handled?

**Operation**
- How fresh must the output be, and what happens when it is late?
- Who is alerted when it fails, and who fixes it?
- Expected data volume now and in a year.

**Boundaries**
- Which environments exist, and which may the agent deploy to?
- Who must approve access, schema, or cost changes?
- What is tempting but explicitly out of scope?

**For apps**
- Who are the users, and how do they authenticate?
- Read-only views, or do users write data back?
- What must work on the first screen they see?
