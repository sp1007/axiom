---
id: T006
title: Architecture layer checker tools/archcheck.py
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-qa
depends: [T004]
priority: 12
status: todo
attempts: 0
paths: [tools/archcheck.py, tools/archcheck_rules.txt]
spec: [0263, 0152]
---
# T006 — Architecture layer checker tools/archcheck.py

## Goal
Enforce the layer rules of axiom-c-stage0 automatically.

## Scope
- Parse #include "..." in bootstrap/axiom0/src/**; map files to layers; rules file with the ordered layers and explicit exceptions (objmodel, obj, link, interp, opt).
- Report violations as `file:line: layer X must not include Y`; exit non-zero.
- Also flag: mutable globals outside driver (heuristic: non-const file-scope variables), `printf`/`exit(` outside driver/diag render.

## Acceptance
- [ ] Checker passes on the skeleton; a deliberately bad fixture in tools/tests triggers each rule.
- [ ] Wired into tools/ci.sh.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T006-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
