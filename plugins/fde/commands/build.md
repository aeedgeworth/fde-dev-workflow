---
description: Implement an external spec's remaining work and verify the outcomes
argument-hint: "[spec-ref] [--task T3] [--step] [--commit] [--worktree]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, TodoWrite
---

# /fde:build

Load the `fde-workflow` skill and run its **Build** mode with `$ARGUMENTS`.

Work through the safe remaining scope by default. `--step` limits the run to one
task, and `--commit` explicitly requests coherent commits with `Spec:` trailers.
