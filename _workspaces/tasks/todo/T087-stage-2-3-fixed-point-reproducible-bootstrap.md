---
id: T087
title: Stage-2/3 fixed point + reproducible bootstrap (VS2 of 0263 §51)
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T086]
priority: 121
status: todo
attempts: 0
paths: [tools/bootstrap.py, tools/build_axiomc.py, tests/selfhost/fixedpoint, spec/BOOTSTRAP.md]
spec: [0167, tasks/0473, 0150]
---
# T087 — Stage-2/3 fixed point + reproducible bootstrap (VS2 of 0263 §51, BOOT-36..38)

## Goal
axiomc compiles itself to a fixed point.

## Scope
- axiomc1 (by axiom0) → axiomc2 → axiomc3; axiomc2 and axiomc3 byte-identical; document trust chain and reproduction steps.

## Acceptance
- [ ] Functional equivalence first (tasks/0262 §42): axiomc2 passes the same suite as axiomc1 with identical `--json` diagnostics and run results.
- [ ] The ADR-0034 §3 independent subset (as listed in T086) passes with axiomc2, natively built; fixed-point equality alone (category B) is not accepted as correctness evidence.
- [ ] Fixed point: axiomc2 and axiomc3 are byte-identical, built in two different directories with identical flags, checked at -O0 and at -O1, in CI.
- [ ] No external tool in the chain (ABOOT-74/75): `tools/bootstrap.py` completes the axiomc stages with gcc/ld/as removed from PATH (they are needed only to build axiom0 and for test oracles).
- [ ] Freeze (ROADMAP R3, ADR-0005 §15): `tools/build_axiomc.py --out <dir>` builds the stage-2 compiler for a task (inside its snapshot: `build-snap-<ID>/build`), and the exact command is stated in the report. spec/BOOTSTRAP.md documents the trust chain and the freeze rule: the orchestrator creates the local tag `axiom0-frozen` right after accepting this task (never pushed); from then on `harness_check.py` rejects any commit touching `bootstrap/axiom0` unless it belongs to a task titled `AX0-FIX-<nn> …` (phase `P10-selfhost`, filed by the architect).
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T087-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- After this task the compiler under test is axiomc: the runner's default compiler and tests/README.md are owned by T005 (done) — document the switch in spec/BOOTSTRAP.md and pass `--compiler` explicitly; do not edit tools/axtest.py.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
