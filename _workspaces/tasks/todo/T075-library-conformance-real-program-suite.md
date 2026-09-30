---
id: T075
title: Library conformance + real-program suite
phase: P9-stdlib
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: [T074, T073]
priority: 106
status: todo
attempts: 0
paths: [tests/programs, tests/conformance/std]
spec: [0114, 0169]
---
# T075 — Library conformance + real-program suite

## Goal
Prove the language + library can build real software.

## Scope
- Programs: word count, tokenizer, JSON-ish parser, small expression interpreter, sorting benchmarks; run interp + native, leak counters zero.

## Acceptance
- [ ] All programs pass both modes; perf recorded.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T075-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
