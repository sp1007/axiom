---
id: T075
title: Library conformance + real-program suite
phase: P9-stdlib
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T074b, T073, T073a, T062, T071b]
priority: 107
status: todo
attempts: 0
paths: [tests/programs, tests/conformance/std, tools/gen_large.py, tests/perf]
spec: [0114, 0169]
---
# T075 — Library conformance + real-program suite

## Goal
Prove the language + library can build real software.

## Scope
- Programs: word count, tokenizer, JSON-ish parser, small expression interpreter, sorting benchmarks; run interp + native, leak counters zero.
- **Scale test** (ADR-0005 §7): `tools/gen_large.py` generates a valid program of about 100k lines (many modules, deep generics, long functions, 200-arm matches, 500-deep expression nesting, large constant tables) with a fixed seed.

## Acceptance
- [ ] All programs pass both modes; leak counters zero; timings recorded in `tests/perf/programs.csv` (committed).
- [ ] axiom0 (Release) compiles the generated 100k-line program in < 30 s and < 2 GB, and the result runs correctly natively (interp on a 5k-line variant); time per pass recorded in `tests/perf/scale.csv`. Over budget → report BLOCKED with the per-pass profile.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T075-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
