---
name: databricks-workflow
description: How to run the spec-driven loop against Databricks — profile discipline, which Databricks skill to load for which task, and the verification ladder that gives each ledger task a runnable evidence command. Use when a spec touches Databricks, before writing DABs, jobs, pipelines, notebooks, SQL, or Unity Catalog changes. Triggers on Databricks work of any kind inside /fde:spec, /fde:build, or /fde:ship.
---

# Databricks workflow

Databricks work breaks the normal inner loop: the code often cannot run on your
laptop, so "write a test and watch it fail" needs deliberate design. This skill
covers how to keep evidence runnable anyway, and how to route into the
Databricks skills you already have installed.

## Profile discipline

**Never auto-select a profile.** Always pass `--profile <name>` explicitly and
let the user choose. A command that silently uses `DEFAULT` may be pointed at a
workspace you did not intend.

```bash
databricks auth profiles                       # what exists
databricks current-user me --profile <name>    # confirm before anything stateful
```

Ask which profile to use once per spec, record it in `SPEC.md`, and use it for
every command in that spec.

## Route into the Databricks skills

Load `databricks-core` first, then the matching product skill — do not
improvise CLI invocations when a skill covers the area:

| Work | Skill |
| --- | --- |
| CLI, auth, profiles, bundles entry point | `databricks-core` |
| Asset bundles, `databricks.yml` | `databricks-dabs` |
| Jobs, Lakeflow, workflows | `databricks-jobs` |
| Declarative pipelines (formerly DLT) | `databricks-pipelines` |
| SQL, warehouses, advanced SQL features | `databricks-dbsql` |
| Finding data, NL questions, SQL generation | `databricks-data-discovery` |
| Governance, grants, system tables, volumes | `databricks-unity-catalog` |
| Apps (AppKit/React) | `databricks-apps` |
| Python-backend apps | `databricks-apps-python` |
| AI/BI dashboards | `databricks-aibi-dashboards` |
| Model serving endpoints | `databricks-model-serving` |
| ML training, feature engineering | `databricks-ml-training` |
| Agent/GenAI evaluation | `databricks-mlflow-evaluation` |
| Vector search, RAG | `databricks-vector-search` |
| Running code on compute | `databricks-execution-compute` |
| Anything not covered above | `databricks-docs` |

## The verification ladder

Every ledger task needs an evidence command that fails before and passes after.
Take the **highest rung that genuinely proves the task**, because each rung down
is slower and less deterministic. Most tasks should sit on rungs 1-3.

1. **Pure Python, local pytest.** Parsing, transformation logic, config
   handling, schema decisions. Fastest and fully deterministic — structure code
   so the interesting logic lives here, separable from the Spark session.
   `evidence: pytest tests/test_transform.py::test_drops_null_keys`
2. **Spark logic, local session or Databricks Connect.** DataFrame
   transformations against small fixtures.
   `evidence: pytest tests/test_pipeline.py -k schema_evolution`
3. **Static validation of config.** Bundles, job definitions, and SQL parse
   without deploying anything.
   `evidence: databricks bundle validate --target dev --profile <name>`
4. **Deployed dev behavior.** Deploy to the dev target and run it. Slower, needs
   credentials, but it is the only proof for orchestration and permissions.
   `evidence: databricks bundle run <job> --target dev --profile <name>`
5. **Query against a dev warehouse.** For SQL objects, metric views, and grants.
   `evidence: databricks sql query --warehouse <id> --profile <name> -e "..."`

When a task can only be verified on rungs 4-5, say so in the ledger. In
`/fde:status`, a rung 4-5 evidence command that cannot run for lack of
credentials is reported as **not verified** — never as passing.

## Design for testability

The single highest-leverage move in Databricks work: **keep business logic out
of the notebook and out of the Spark session.** A transformation that takes and
returns a DataFrame, with the reading and writing at the edges, is testable on
rung 1 or 2. The same logic inline in a notebook cell is only testable on rung 4.

- Put logic in a package; let notebooks and job entry points be thin callers.
- Prefer bundles over ad-hoc workspace state, so the definition is in git and
  reviewable in the PR.
- Treat notebooks as an interface, not a home for logic.

## Safety

- **Never deploy to a production target.** `--target prod`, prod workspaces, and
  prod catalogs are user-only actions. The plugin's PreToolUse guard blocks
  these; do not attempt to work around it.
- Confirm before anything that mutates shared state — dropping tables, altering
  grants, overwriting a catalog object, or resizing shared compute.
- Prefer dev catalogs and schemas for everything the loop does. Record the
  catalog and schema in `SPEC.md` so it is visible in review.
