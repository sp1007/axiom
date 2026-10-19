---
id: T086
title: Stage-1: axiom0 builds axiomc; axiomc passes the full suite
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T085, T134]
priority: 120
status: todo
attempts: 0
paths: [tools/bootstrap.py, tests/selfhost/stage1, tests/perf]
spec: [0167, 0150, tasks/0371]
covers: [REQ-OWN-001, REQ-OWN-002, REQ-OWN-003, REQ-OWN-004, REQ-OWN-005, REQ-OWN-006]
---
# T086 — Stage-1: axiom0 builds axiomc; axiomc passes the full suite

## Goal
The Axiom compiler, written in Axiom, works.

## Scope
- tools/bootstrap.py builds axiomc with axiom0, using `--stack-reserve 67108864` (64 MB, ADR-0003); the runner runs the suite with `--compiler axiomc --exclude-requires axiom0-internal` (C unit tests, encoder tables and C test drivers cannot run against axiomc).

## Acceptance
- [ ] Every test without `requires: axiom0-internal` passes with axiomc1; the report lists the excluded count per kind.
- [ ] `--emit=obj` of axiomc1 and of axiom0 are byte-identical for every tests/run program (the cheapest whole-compiler differential check); any difference is explained and fixed.
- [ ] Budget (ADR-0005 §7): wall time and peak memory of axiom0 → axiomc1 and of the axiomc1 self-compile, with `--time-passes`, recorded in `tests/perf/selfhost.csv` and within the SPEC-20 budget. Over budget → report BLOCKED: the architect applies the regalloc contingency before T087.
- [ ] QA does not patch the compiler: each failure becomes a fix task for the owning port task (filed by the architect); the gate closes only when they are done.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] The per-task build command of axiomc (through `tools/bootstrap.py`, output into `build-snap-<ID>/build`) is stated in the report; T087 turns it into `tools/build_axiomc.py`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T086-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:24:24 covers += REQ-OWN-001, REQ-OWN-002, REQ-OWN-003, REQ-OWN-004, REQ-OWN-005, REQ-OWN-006 (metadata only)
