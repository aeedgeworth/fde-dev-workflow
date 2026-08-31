---
name: databricks-workflow
description: Apply safe Databricks profile selection and choose proportionate local or remote verification for an fde spec. Use when fde work touches Databricks bundles, jobs, pipelines, SQL, apps, ML, or Unity Catalog.
---

# Databricks workflow

Databricks work often crosses local and remote execution. Keep local business
logic easy to test, make the target workspace explicit, and distinguish safe
checks from operations that mutate shared state.

## Profile discipline

**Never auto-select a profile.** Always pass `--profile <name>` explicitly and
let the user choose. A command that silently uses `DEFAULT` may be pointed at a
workspace you did not intend.

```bash
databricks auth profiles                       # what exists
databricks current-user me --profile <name>    # confirm before anything stateful
```

Ask which profile to use once per spec, record it in `SPEC.md`, and use it for
every Databricks command in that spec. Confirm the current user before the first
stateful operation.

## Route into the Databricks skills

When these skills are installed, load `databricks-core` first and then the
matching product skill rather than guessing current CLI or resource behavior:

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

## Verification ladder

Choose the earliest rung that genuinely proves the outcome. Show a failing
regression first when it is meaningful; do not manufacture failure for static
configuration or already-correct supporting behavior.

1. **Pure Python, local pytest.** Parsing, transformation logic, config
   handling, schema decisions. Fastest and fully deterministic — structure code
   so the interesting logic lives here, separable from the Spark session.
   `verify: pytest tests/test_transform.py::test_drops_null_keys`
2. **Spark logic, local session or Databricks Connect.** DataFrame
   transformations against small fixtures.
   `verify: pytest tests/test_pipeline.py -k schema_evolution`
3. **Static validation of config.** Validate bundles, job definitions, or SQL
   without deploying anything.
   `verify: databricks bundle validate --target dev --profile <name>`
4. **Deployed dev behavior.** Deploy to a dev target and run it. This is
   ordinary autonomous work, and may be the only way to prove orchestration and
   permission behavior. Confirm first only when the run mutates state others
   depend on — overwriting a catalog object, altering grants, resizing shared
   compute — or when it carries unusual cost. A workspace named "production" is
   not by itself a reason to stop when it is the engagement's only workspace;
   see the single-workspace note under Safety.
   `verify: databricks bundle run <job> --target dev --profile <name>`
5. **Query against a dev warehouse.** Use for SQL objects, metric views, and
   grants after confirming the profile, warehouse, catalog, and schema.
   `verify: databricks sql query --warehouse <id> --profile <name> -e "..."`

When an outcome needs rungs 4-5, record that its validation is remote and
stateful. Never run it merely to report status. If credentials or authority are
unavailable, report it as not verified rather than passing.

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

- **Never deploy to a production target.** Production workspaces, targets, and
  catalogs are user-only actions. The plugin hook is defense-in-depth, not a
  complete enforcement boundary.
- Confirm before anything that mutates shared state — dropping tables, altering
  grants, overwriting a catalog object, or resizing shared compute.
- Prefer dev catalogs and schemas for everything the loop does. Record the
  catalog and schema in `SPEC.md` so it is visible in review.

**Single-workspace engagements.** Some customers have exactly one workspace, and
it may be named production. There a prod-named bundle target is not a promotion
from a lower environment — it is simply the workspace — and treating it as a
production deploy trains the operator to bypass the guard for routine work.
Declare it once per engagement in `fde.toml` inside that repository's spec-store
directory:

```toml
[safety]
single_workspace = true
```

That stops target *names* being read as a promotion signal for `bundle deploy`
and `bundle run`. It does not relax anything else: `bundle destroy` stays
blocked, and shared-state mutation still needs confirmation. Leave it unset when
the customer has separate dev and prod targets.
