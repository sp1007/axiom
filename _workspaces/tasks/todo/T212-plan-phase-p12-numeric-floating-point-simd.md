---
id: T212
title: Plan phase P12 — Numeric, floating point & SIMD (expand roadmap epics into tasks)
phase: P12-numeric-floating-point-simd
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
# T212 — Plan phase P12: Numeric, floating point & SIMD

## Goal
Expand the epics of phase P12 listed in `spec/ROADMAP.md` §3 into concrete board tasks following the
standard in ROADMAP §4, so that this phase looks exactly like every other phase and nothing outside
the roadmap is invented.

## Scope
- Read ROADMAP §3 (P12 epics), catalogue rows with `EPIC(E12.*)` (including `REQ-OWNER-007`: unsuffixed integer literals like `1`, `2` inside `f32`/`f64` expressions such as `let a: f64 = 123.45; let b: f64 = (a + 1)/2 + a*a/6.0` infer `f32`/`f64` directly from context without suffixes or `as` casts when exactly representable), the epics' sources, and the gate reports of the phases this one depends on.
- Create 3–10 tasks per epic with ids in `T450`–`T499`, titles `E12.x <short title>`, owners by area, narrow `paths`, `spec:`, `covers:`, acceptance as tests; a spec task first where `spec/` lacks the area; a QA conformance task per epic exit criterion.
- Implementation happens in `compiler/` (Axiom) and `std/` — axiom0 is frozen (ROADMAP R3).
- Make gate task T312 depend on every new task; convert catalogue `EPIC(E12.*)` statuses to task ids.
- Scope not covered by an epic → ADR + new epic in ROADMAP (and change-log entry), never a stray task.
- Add `depends` on the gate task of every phase ROADMAP lists as a prerequisite of an epic (for example E15.5 tasks depend on T312); take ids with `taskctl.py new-id --phase <P>`.

## Acceptance
- [ ] Every new task file passes `taskctl.py lint`; `taskctl.py validate` OK, `reqcov.py --strict` exits 0 and `harness_check.py` exits 0.
- [ ] Every P12 epic has tasks; gate T312 depends on all of them.
- [ ] ROADMAP change log records the expansion (task count per epic).
- [ ] Report `_workspaces/reports/T212-report.md` listing new tasks under `## Files changed`.

## Out of scope
- Implementing anything; tasks of other phases.

## Notes
- Critical board task (priority < 10): runs alone.

