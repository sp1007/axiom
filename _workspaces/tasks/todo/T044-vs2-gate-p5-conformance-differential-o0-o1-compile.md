---
id: T044
title: VS2 gate: P5 conformance + differential -O0/-O1 + compiler perf baseline
phase: P5-language
owner: axiom-qa
reviewer: axiom-architect
depends: [T042, T043]
priority: 64
status: todo
attempts: 0
paths: [tests/conformance/vs2, tools/ci.sh, tools/perf.py]
spec: [0114, 0022, 0263, 0152]
---
# T044 — VS2 gate: P5 conformance + differential -O0/-O1 + compiler perf baseline

## Goal
Lock in the language-core milestone.

## Scope
- Port applicable E2E consistency cases (0114) and stress tests (0022); differential at both levels; tools/perf.py records `--time-passes` for a benchmark set into _workspaces/artifacts/perf.csv.

## Acceptance
- [ ] All pass; QA seam review; perf baseline recorded.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T044-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
