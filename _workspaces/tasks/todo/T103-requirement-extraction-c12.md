---
id: T103
title: Requirement extraction C12 (core)
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
depends: [T003]
priority: 27
status: todo
attempts: 0
paths: [spec/requirements/raw/C12.md]
spec: [spec/requirements/chunks/C12.txt]
---
# T103 — Requirement extraction C12 (core)

## Goal
Extract every normative goal, decision, invariant and required behaviour from the documents listed in
`spec/requirements/chunks/C12.txt` (C12 kind=core files=34 size_mb=2.0) into a provisional requirements table, mapped to
existing board tasks or marked GAP, so that nothing the corpus concluded is silently lost.

## Scope
- Skim each listed file (headings, conclusions, invariants, MUST/phải statements, rule IDs); read decision passages in full.
- Write `spec/requirements/raw/C12.md`: six-column table (id RQ-C12-NNN | area | tier | statement | sources | status), then `## Conflicts` and `## Files skimmed`.
- Tier every row v1-core / v1-full / post-v1 as defined in the procedure.

## Acceptance
- [ ] Every file in the chunk manifest is accounted for in `## Files skimmed` (skimmed / unreadable).
- [ ] Every row has sources with section references and a status (task ids or GAP).
- [ ] Rows are deduplicated within the chunk (one row may cite many docs).
- [ ] Report `_workspaces/reports/T103-report.md` with exact `## Files changed`.

## Out of scope
- Final ids, cross-chunk dedup, creating tasks (T110/T111 do that). Do not edit the board.

## Notes
- Procedure: `.claude/skills/axiom-spec-index/references/requirements-extraction.md` (Phase A).
- Normative sources only: specs/, tasks/, others/, init prompt. `docs/base/discussions/` is brainstorming — do not extract from it.
- Map to existing tasks with `python .claude/skills/axiom-tasks/scripts/taskctl.py list`.
- All code in statements uses canonical syntax (`=`, `.`).
