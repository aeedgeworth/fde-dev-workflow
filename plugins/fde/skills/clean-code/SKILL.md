---
name: clean-code
description: Apply Adam's maintainability standard during non-trivial implementation, refactoring, or code review. Use when choosing abstractions, dependencies, failure behavior, or structure; do not trigger for mechanical edits.
---

# Clean code

Optimize for a future reader changing the code safely, while matching the target
repository's local conventions.

## Prefer the smallest honest design

- Build the behavior needed now. Reject speculative layers, configuration, and
  dependencies whose only justification is possible future use.
- Treat the rule of three as a heuristic: wait for repeated, genuinely identical
  needs before extracting shared machinery. Two similar cases may still be
  different concepts.
- Prefer a little duplication over an abstraction that hides important
  differences or makes callers harder to understand.
- Keep unrelated cleanup out of the change. A focused diff is easier to review,
  revert, and bisect.

## Make behavior obvious

- Use names and control flow that expose intent without reconstructing the
  author's reasoning. Prefer early returns to deep nesting.
- Keep functions cohesive and at one level of abstraction; do not split them
  merely to satisfy a size rule.
- Make inputs, outputs, side effects, ownership, and failure modes explicit.
- Fail early on invalid state. Errors should name the failed operation and the
  relevant value or context needed to diagnose it.

For a consequential, hard-to-reverse design choice, state the alternatives, the
trade-off, and how you would roll it back before implementation. A decision with
no stated way back is not yet ready to implement. Use the repository's existing
design-record convention, or the active FDE spec when one exists.
