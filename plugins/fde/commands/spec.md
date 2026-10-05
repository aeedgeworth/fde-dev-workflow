---
description: Create a persistent external spec and execution plan
argument-hint: "[--lite | --deep] <idea, or path to rough notes>"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, Skill, Agent
---

# /fde:spec

Load the `fde-workflow` skill and run its **Plan** mode with `$ARGUMENTS`.

This command explicitly requests persistent `SPEC.md` and `PLAN.md` artifacts.
Discover before asking: answer from the repository and, for Databricks work, the
workspace (read-only, explicit profile) whatever they can answer. Honor `--lite`
and `--deep`; otherwise ask one round of only the material questions discovery
left open. Finish with `spec_store.py check` and a fresh-context spec review.
