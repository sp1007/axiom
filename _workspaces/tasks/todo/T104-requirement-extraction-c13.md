---
id: T104
title: Requirement extraction C13 (core)
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T003]
priority: 28
status: todo
attempts: 0
paths: [spec/requirements/raw/C13.md]
spec: [spec/requirements/chunks/C13.txt]
---
# T104 — Requirement extraction C13 (core)

## Goal
Extract every normative goal, decision, invariant and required behaviour from the documents listed in
`spec/requirements/chunks/C13.txt` (C13 kind=core files=32 size_mb=2.1) into a provisional requirements table, mapped to
existing board tasks or marked GAP, so that nothing the corpus concluded is silently lost.

## Scope
- Skim each listed file (headings, conclusions, invariants, MUST/phải statements, rule IDs); read decision passages in full.
- Write `spec/requirements/raw/C13.md`: six-column table (id RQ-C13-NNN | area | tier | statement | sources | status), then `## Conflicts` and `## Files skimmed`.
- Tier every row v1-core / v1-full / post-v1 as defined in the procedure.
- When a statement says it is built on / uses / requires another requirement, end the statement with `[needs RQ-Cnn-NNN, …]` (T110 turns this into the catalogue `needs` column).

## Acceptance
- [ ] Every file in the chunk manifest is accounted for in `## Files skimmed` (skimmed / unreadable).
- [ ] Every row has sources with section references and a status (task ids or GAP).
- [ ] Rows are deduplicated within the chunk (one row may cite many docs).
- [ ] Report `_workspaces/reports/T104-report.md` with exact `## Files changed`.

## Out of scope
- Final ids, cross-chunk dedup, creating tasks (T110/T111 do that). Do not edit the board.

## Notes
- Procedure: `.claude/skills/axiom-spec-index/references/requirements-extraction.md` (Phase A). Write the raw file incrementally (resume from it on restart).
- Normative sources only: specs/, tasks/, others/, init prompt. `docs/base/discussions/` is brainstorming — do not extract from it.
- Map to existing tasks with `python .claude/skills/axiom-tasks/scripts/taskctl.py list`.
- All code in statements uses canonical syntax (`=`, `.`).
