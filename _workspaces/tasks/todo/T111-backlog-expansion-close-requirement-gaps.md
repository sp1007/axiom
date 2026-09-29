---
id: T111
title: Backlog expansion — close every requirement gap, add covers to all tasks
phase: P0-traceability
owner: axiom-architect
reviewer: axiom-qa
depends: [T110]
priority: 9
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/COVERAGE.md, spec/SPEC-00-bootstrap.md]
spec: [spec/requirements/CATALOG.md, spec/COVERAGE.md]
---
# T111 — Backlog expansion

## Goal
Turn the coverage matrix into a complete plan: every requirement of the normative corpus is planned
by a task, merged, deferred (post-v1 only) or rejected by ADR; every task declares `covers:`.

## Scope
- Phase C of the extraction procedure.
- New tasks for gaps in the right phases (v1-core → P1–P10, v1-full → P11a…P11n sub-phases, post-v1 → P12+ or DEFERRED), one-sitting sized, correct dependencies and owners, acceptance as tests.
- Extend scope of existing todo tasks only where they stay one-sitting sized; never rewrite tasks already in doing/ or done/ — add follow-up tasks instead.
- Update SPEC-00 milestone ladder if phases change.

## Acceptance
- [ ] `taskctl.py validate` OK.
- [ ] `reqcov.py --strict` exits 0 (zero GAP, zero problems).
- [ ] COVERAGE.md updated with final counts (tasks per phase, requirements per tier).
- [ ] Report `_workspaces/reports/T111-report.md` listing new tasks (id, title, phase, covers count) under `## Files changed`.

## Out of scope
- Implementing anything.

## Notes
- Critical board-level task (priority < 10): runs alone, so no agent moves task files while you edit.
- Only discussions/ is non-normative; everything else in docs/base counts.
