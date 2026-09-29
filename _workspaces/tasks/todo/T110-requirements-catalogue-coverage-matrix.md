---
id: T110
title: Requirements catalogue + coverage matrix (consolidation)
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
depends: [T092, T093, T094, T095, T096, T097, T098, T099, T100, T101, T102, T103, T104, T105, T106, T107, T108, T109]
priority: 8
status: todo
attempts: 0
paths: [spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/decisions]
spec: [spec/requirements/raw]
---
# T110 — Requirements catalogue + coverage matrix

## Goal
Merge the 18 raw extraction tables into one deduplicated catalogue with final requirement ids,
resolve conflicts via ADRs, and publish the coverage matrix of corpus goals vs the board.

## Scope
- Phase B of `.claude/skills/axiom-spec-index/references/requirements-extraction.md`.
- `spec/requirements/CATALOG.md` in the exact format read by `reqcov.py`; `spec/COVERAGE.md` summary (area × tier counts, GAP list, DEFERRED list with reasons, conflict → ADR list).
- Copy every row of `spec/requirements/OWNER.md` into the catalogue unchanged (owner requirements override the corpus; conflicting corpus rows become DUPLICATE/REJECTED referencing them).
- ADRs for every cross-chunk conflict (next free ADR number; ADR-0001 is taken).

## Acceptance
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py` parses the catalogue with zero format problems (GAPs are allowed at this stage).
- [ ] Every raw row is either a catalogue requirement or listed as merged into one (traceable: raw id → REQ id table in COVERAGE.md).
- [ ] Report `_workspaces/reports/T110-report.md` with exact `## Files changed`.

## Out of scope
- Creating tasks (T111).

## Notes
- Critical board-level task (priority < 10): runs alone.
- Keep `spec/requirements/raw/` untouched as audit trail.
