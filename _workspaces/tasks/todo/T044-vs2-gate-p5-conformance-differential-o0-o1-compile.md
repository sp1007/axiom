---
id: T044
title: P5 gate: language core conformance + differential -O0/-O1 + compiler perf baseline
phase: P5-language
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T042, T043]
priority: 64
status: todo
attempts: 0
paths: [tests/conformance/p5, tools/ci.sh, tools/perf.py, tests/perf]
spec: [0114, 0022, 0263, 0152]
---
# T044 — P5 gate: language core conformance + differential -O0/-O1 + compiler perf baseline

## Goal
Lock in the language-core milestone.

## Scope
- Port applicable E2E consistency cases (0114) and stress tests (0022) into tests/conformance/p5; differential at both levels.
- tools/perf.py records `--time-passes` for the named benchmark set `tests/perf/bench/*.ax` into `tests/perf/baseline.csv` (committed; columns: file, pass, milliseconds, commit) — `_workspaces/artifacts` is git-ignored and is not used for baselines.

## Acceptance
- [ ] All pass; QA seam review; `tests/perf/baseline.csv` committed with one row per benchmark and pass.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T044-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Named "P5 gate" (not VS2): in the ladder 0263 §51, VERTICAL SLICE #2 is self-hosting (T087). Name map in SPEC-00 (T003).
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
