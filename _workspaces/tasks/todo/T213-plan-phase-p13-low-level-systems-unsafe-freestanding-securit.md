---
id: T213
title: Plan phase P13 — Low-level systems, unsafe, freestanding, security (expand roadmap epics into tasks)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T087]
priority: 6
status: todo
attempts: 0
paths: [_workspaces/tasks/todo, spec/requirements/CATALOG.md, spec/ROADMAP.md]
spec: [spec/ROADMAP.md, spec/requirements/CATALOG.md]
---
# T213 — Plan phase P13: Low-level systems, unsafe, freestanding, security

## Goal
Expand the epics of phase P13 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P13 epics), catalogue rows with `EPIC(E13.*)`, the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T500`–`T549`, titles `E13.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T313 depend on every new task; convert catalogue `EPIC(E13.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.
- Add `depends` on the gate task of every phase ROADMAP lists as a prerequisite of an epic (for example E15.5 tasks depend on T312); take ids with `taskctl.py new-id --phase <P>`.

## Acceptance
- [ ] Every new task file passes `taskctl.py lint`; `taskctl.py validate` OK, `reqcov.py --strict` exits 0 and `harness_check.py` exits 0.
- [ ] Every P13 epic has tasks; gate T313 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T213-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.
- Carry-over (ADR-0034 §8, audit 2026-10-19 OI-12): plan an external Windows x64 ABI oracle before FFI breadth — a gcc-built test DLL (`gcc -shared`) exporting functions with 1..8 mixed-width arguments and structs of size 1/2/3/4/8/12/16/24 by value and return, called via `@link`, plus a gcc `offsetof`/`sizeof` table for `@repr(C)` layouts; `tests/mc/isel/cdriver_abi*.c` must not rely on `assert()` under NDEBUG.

