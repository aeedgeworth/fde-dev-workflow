---
description: Interview an idea into a standard two-file spec stored outside the repo
argument-hint: "[--lite] <idea, or path to a rough notes file>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, WebFetch
---

# /fde:spec

Turn a rough idea, OKR, or half-formed task into a **SPEC.md** (why and what) and
a **PLAN.md** (how, and where we are). Both are written to the local spec store,
never into the repo.

The point of this command is that the output shape is *identical every time*.
Follow the agenda below in order even when a section feels obvious — a section
you skip is the one that varies between sessions.

## 1. Parse arguments

- `--lite` → lite mode: no interview, one-page spec, ≤5 tasks. For work you
  already understand and could start today.
- Absent `--lite` → full mode: repo grounding, then a structured interview.
- If an argument is a readable file path, read it as the draft input.
- If `$ARGUMENTS` is empty, ask the user what they want to build before going on.

## 2. Ground in the repo first

Do this **before** asking the user anything. Half the questions answer
themselves here, and the ones that remain are sharper.

1. Load the `repo-conventions` skill and follow it for the area of the repo this
   work touches.
2. Locate the code this change would sit next to. Read enough of it to describe
   the current behavior in your own words.
3. Note the test command, lint command, and how the nearest neighbors are
   structured.
4. If this is Databricks work, load the `databricks-workflow` skill now.

State what you learned in 3-6 bullets before moving on. If the repo already
answers a question on the agenda, record the answer — do not ask it.

## 3. Interview (full mode only)

Use `AskUserQuestion`. Cover this agenda in order, one question set at a time.
Skip any item the repo already answered. Stop early if the user says they are
done.

1. **Problem and trigger** — what breaks today, for whom, and why now.
2. **Scope boundary** — what is explicitly *not* in this change. Push here; a
   vague non-goal is the main cause of plans that sprawl.
3. **Approach trade-off** — where more than one design is viable, present the
   real options with their costs. Recommend one and say why.
4. **Failure modes** — what invalid input or broken state should do, and what
   the error should tell someone diagnosing it at 2am.
5. **Verification** — how we will know it works. Push until every acceptance
   criterion names something runnable.
6. **Blast radius** — what else in the repo could this break, and what existing
   behavior must stay identical.

Question quality rules:

- Do not ask what the code already told you.
- Ask about specifics: "when X happens mid-run, what should Y do?"
- Name your assumptions and ask the user to confirm or correct them.
- Challenge the request when a simpler shape would do — then build what they
  confirm.

## 4. Write the spec

1. Create the folder and capture its path:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/spec_store.py" new "<short title>"
   ```

2. Load the `spec-writing` skill and follow it for section-by-section guidance.
3. Copy `${CLAUDE_PLUGIN_ROOT}/templates/SPEC.md` and `PLAN.md` into the folder,
   substituting `{{ID}}`, `{{TITLE}}`, `{{REPO}}`, `{{MODE}}`, `{{DATE}}`.
4. Fill every section. Replace the guidance comments with real content; do not
   leave a `<!-- ... -->` block or a `TODO` behind.
5. Build the task ledger in `PLAN.md`:
   - Order tasks so each one leaves the repo working.
   - Every task gets an `evidence:` command that fails before and passes after.
   - Cap at ~15 tasks. If the work needs more, say so and propose the split
     rather than writing a longer list.

## 5. Report

Print:

1. The spec folder path.
2. The task count and the first task.
3. Any open question that should be resolved before building.
4. `Next: /fde:build` — or, if you proposed a split, the split instead.

## Rules

- Never write spec artifacts into the repo's working tree.
- Acceptance criteria and evidence commands are the deliverable. A spec whose
  criteria cannot be checked has failed, however well written the prose is.
- In lite mode, still write both files with all sections — just short ones.
