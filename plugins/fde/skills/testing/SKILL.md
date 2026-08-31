---
name: testing
description: Design or review tests for changed behavior without coupling them to implementation details or adding redundant cases. Use when adding tests, fixing a regression, or evaluating test quality.
---

# Testing

Test observable contracts: outputs, raised errors, persisted state, and messages
crossing a boundary. Avoid assertions about private helpers or internal call
counts unless that interaction is itself the contract.

## Prove the test matters

- For a new regression or behavior test, run it before the fix and observe the
  meaningful failure. Do not manufacture a red step for documentation,
  configuration-only changes, or behavior already covered elsewhere.
- A test should continue to pass after an implementation-only refactor.
- Mock external trust boundaries such as the network, clock, filesystem, or
  warehouse—not internal seams that the implementation should be free to move.

## Cover distinct behavior, not samples

- Partition inputs into equivalence classes and test representative boundaries:
  empty, one, many, and values immediately around a threshold when relevant.
- Use one test per distinct behavior. Parameterize cases only when the values
  express meaningfully different examples of the same contract.
- Do not test framework or standard-library behavior, trivial containers, or a
  pass-through with no owned logic.
- Delete tests that no longer describe a real requirement. A suite is a liability
  as well as an asset, and a test kept only because removing it feels risky is
  the clearest sign it is testing the wrong thing.
- Prefer concrete expected values. Reimplementing production logic inside the
  expectation can reproduce the same defect.

Keep arrange, act, and assert easy to see. After the focused test passes, run the
surrounding test file or package and report the exact commands and results.
