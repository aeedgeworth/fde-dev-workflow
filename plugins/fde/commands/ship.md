---
description: Verify, review, and open a PR for a completed spec
argument-hint: "[spec-ref] [--partial] [--no-pr]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
---

# /fde:ship

Take a finished spec from "the tests pass on my branch" to "there is a PR a
reviewer can actually evaluate."

## 1. Confirm the work is done

1. Resolve the spec and read `SPEC.md` and `PLAN.md`.
2. Run the `/fde:status` reconciliation. **Do not ship over drift.** If tasks are
   drifted or unrecorded, stop and report — unless `--partial` was passed, in
   which case say plainly in the PR body what is unfinished and why.
3. Check every acceptance criterion in `SPEC.md` against the implementation and
   tick the boxes you can prove. An unticked criterion blocks shipping unless
   the user waives it.

## 2. Validate

Run the project's real commands, discovered via the `repo-conventions` skill —
not guessed ones. Typically lint, type-check, then tests.

- Run the full test suite for the package you touched, not just your new tests.
- Fix what you broke. If a pre-existing failure is unrelated to this spec, say
  so explicitly with evidence rather than fixing it here.

## 3. Review

Run `/code-review` against the branch diff. Then:

1. Triage every finding: fix it, or record why it does not apply.
2. Apply the fixes and re-run validation.
3. For anything you consciously chose not to fix, add a line to the PR body.

For work touching auth, secrets, customer data, or Unity Catalog grants, also
run `/security-review`.

## 4. Ship

Follow the `git-convention` skill for branch name, commit messages, and PR
format. Then:

1. Push the branch and confirm it is not `main`.
2. Open the PR with `gh pr create`, body built from `SPEC.md`:
   - **Summary** — the Problem section, compressed to 2-3 bullets.
   - **Approach** — a short paragraph, plus any Decision log entries added
     during the build.
   - **Verification** — the acceptance criteria with their status, and the
     commands a reviewer can run.
   - **Not included** — the Non-goals, plus anything deferred or waived.
3. Do **not** merge.

## 5. Close the loop

1. Set `status: shipped` in `SPEC.md`'s frontmatter and append a Decision log
   entry with the PR URL.
2. If the build taught you something durable about this repo — a convention, a
   gotcha, a command that is not discoverable — write it into the repo's nearest
   `CLAUDE.md` rather than leaving it in this session. Say what you added.
3. Print the PR URL.

## Rules

- Never push to `main` or force-push a shared branch.
- Never deploy to a production target from this command.
- The PR body is written for a reviewer who has not read the spec and cannot
  see it — it lives outside the repo. Include what they need inline.
