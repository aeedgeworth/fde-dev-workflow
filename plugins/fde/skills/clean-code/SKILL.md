---
name: clean-code
description: Code quality standard — clarity over cleverness, KISS/YAGNI, explicit behavior and failure modes, design before nontrivial work. Use when writing or reviewing non-trivial code, deciding whether to extract an abstraction, or judging whether a change is too clever. Triggers on implementing a feature, refactoring, code review, "is this over-engineered", or introducing a new abstraction or dependency.
---

# Clean code

The codebase outlives whoever wrote it. Optimize for the person reading this in
eighteen months with no context, not for the fewest lines today.

## Clarity over cleverness

- Obvious names. A name that needs a comment to explain it is the wrong name.
- Small, cohesive functions doing one thing at one level of abstraction.
- Straightforward control flow. Early returns over nested conditionals. No
  cleverness that saves three lines and costs a reader five minutes.
- **Structure mirrors the business problem.** Someone who understands the domain
  but not this codebase should recognize the shape of it.

If a reviewer would have to reconstruct your reasoning to check the code is
correct, rewrite it or explain it in a comment — preferably the former.

## KISS and YAGNI

- Build what is needed now. Speculative generality is the most expensive kind of
  wrong: it is load-bearing before it is validated.
- **Rule of three.** Extract a shared abstraction on the *third* real occurrence,
  not the second, and only once the repeated pattern is genuinely the same. Two
  similar things are often two things.
- Prefer duplication over the wrong abstraction. Duplication is cheap to fix;
  a bad abstraction spreads through every call site.
- Every new dependency, config option, and layer needs a reason a colleague would
  accept. "It might be useful" is not one.

Actively push back when a request implies speculative structure — state the
concern briefly, then build what the user confirms.

## Make behavior explicit

For anything non-trivial, be able to state: inputs, outputs, failure modes, side
effects, and what owns the state.

- **Fail early and loudly** on invalid input or impossible state. A function that
  quietly returns a default for bad input hides the bug until it surfaces
  somewhere unrelated.
- **Errors must identify what happened and how to diagnose it.** Include the
  offending value, the operation, and enough context to locate it. `ValueError:
  invalid config` is a bug report someone else has to reproduce; `ValueError:
  catalog 'acme_prod' not found; checked profile 'adam'` is one they can act on.
- Side effects belong in named, obvious places. A function called `get_x` that
  writes to disk is a trap.
- Make illegal states unrepresentable where the language allows it cheaply.

## Design before implementing

For meaningful architectural choices — a new component, a data model, an
integration boundary, anything hard to reverse — write it down before coding:
the problem, constraints, alternatives considered, the decision, its trade-offs,
and how you would roll it back.

In this workflow that lives in `SPEC.md`'s **Key decisions**. Elsewhere, a short
ADR or design doc in the repo. The output is not ceremony — it is the record
that stops the same argument being re-litigated in six months.

## Treat code as a long-lived product

Favor maintainability, correctness, and operability over short-term speed.
Concretely, when the two conflict:

- Prefer the version a new team member could modify safely.
- Prefer explicit over implicit, even when implicit is shorter.
- Leave the surrounding code no worse. Do not opportunistically rewrite it
  either — unrelated refactors buried in a feature PR make review harder and
  bisection useless.
