---
description: Create a persistent external spec and execution plan
argument-hint: "[--lite] <idea, or path to rough notes>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill
---

# /fde:spec

Load the `fde-workflow` skill and run its **Plan** mode with `$ARGUMENTS`.

This command explicitly requests persistent `SPEC.md` and `PLAN.md` artifacts.
Honor `--lite`; otherwise ask only the material questions the repository and
request do not already answer.
