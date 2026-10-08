---
id: T029
title: VS1 gate: differential interp vs native, determinism
phase: P4-native
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T028, T022]
priority: 46
status: todo
attempts: 0
paths: [tests/diff, tests/conformance/vs1, tools/ci.sh, tests/mc/frame, tests/mir/build]
locks: [bootstrap/axiom0/src/driver/emit_obj.c]
spec: [0263, 0152, 0145]
started: 2026-10-08 06:58:59
unblocks: 1
---
# T029 — VS1 gate: differential interp vs native, determinism

## Goal
Establish the three-level oracle (MIR interp / native / agreement) as a permanent CI guard.

## Scope
- Differential suite: every run test whose native mode is enabled (no `native-after`) is executed in both modes and compared; determinism check (build twice, compare bytes) in CI. The first ABI test `add(20, 22)` belongs to T033 (0263 §51: calls come after VS#1).

## Acceptance
- [ ] CI runs differential + determinism; QA report documents seams MIR↔LIR↔MC↔COFF↔PE reviewed.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T029-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-08 06:58:59 started (attempt 1) T029-impl
- 2026-10-08 07:10:59 block: need locks for bootstrap/axiom0/src/driver/emit_obj.c and paths for tests/mc/frame, tests/mir/build to fix PE determinism timestamp and failing C tests
- 2026-10-08 07:11:23 unblocked (cycle 1) 
