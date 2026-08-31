---
description: Validate and review a completed spec, optionally pushing and opening a PR
argument-hint: "[spec-ref] [--partial] [--no-pr]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
---

# /fde:ship

Load the `fde-workflow` skill and run its **Ship** mode with `$ARGUMENTS`.

Honor `--no-pr` strictly: validate and review without pushing or creating a pull
request. Never merge or perform a production deployment.
