---
name: testing
description: Write tests that validate behavior rather than implementation, without redundant cases. Use when adding or reviewing tests, deciding what to test, or when a test suite is brittle, bloated, or breaks on every refactor. Triggers on "write tests", "add test coverage", test review, or tests failing after a pure refactor.
---

# Testing

A test suite has two jobs: catch real defects, and let you refactor without
fear. Tests coupled to implementation do neither — they break when nothing is
wrong and pass when something is.

## Test behavior, not implementation

Test the contract at the boundary: given these inputs and this state, the
observable result is X.

- **Do** assert on return values, raised errors, persisted state, and messages
  sent.
- **Do not** assert that a private helper was called, that a method was invoked
  N times, or that internals are shaped a particular way — unless the call
  itself *is* the contract (an idempotency guarantee, a rate limit, a write that
  must happen exactly once).
- Mock at trust boundaries — the network, the clock, the warehouse — not at
  internal seams. Every internal mock is a guess about structure that a refactor
  will invalidate.

**The refactor test:** rewrite the implementation, keep the behavior. Every test
should still pass. Any test that fails was testing the wrong thing.

## Do not bloat the suite

Redundant cases cost real money — slower runs, more to read, more to update, and
noise that hides the one failure that matters.

- One test per distinct behavior, named for the behavior:
  `test_new_column_fails_with_column_name`, not `test_schema_2`.
- **Cover the boundaries, not the interior.** Empty, one, many, and the edge on
  each side of a threshold. Six values inside the same equivalence class are one
  test, not six — use a parametrized case if the values genuinely differ in
  meaning.
- Do not write a test whose failure you could not act on.
- Do not test the framework, the standard library, or a typed data class's
  ability to hold data.
- Delete tests that no longer describe a real requirement. A suite is a
  liability as well as an asset.

## What deserves a test

In rough priority: the thing the change is *for*; the failure modes the spec
names; the boundaries and edges; the bug you just fixed (as a regression test
that fails without the fix).

What usually does not: trivial getters and pass-throughs, and configuration with
no logic in it.

## Make them readable

- Arrange, act, assert — visibly separated.
- One logical assertion per test. Several `assert` lines checking one outcome is
  fine; two unrelated outcomes is two tests.
- Concrete literals over computed expectations. A test that recomputes the
  expected value with the same logic as the code tests nothing.
- Failure messages should identify the problem without opening the test file.
- Fixtures for genuinely shared setup only. A fixture used once, far from where
  it is defined, is worse than three inline lines.

## Before you claim it passes

Run the test and watch it **fail first** when it is new — a test that has never
failed has not been shown to test anything. Then run the surrounding file or
module, not just your new test, and say which command you ran.
