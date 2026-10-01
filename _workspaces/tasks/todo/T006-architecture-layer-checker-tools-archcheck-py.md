---
id: T006
title: Architecture layer checker tools/archcheck.py
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T004]
priority: 12
status: todo
attempts: 0
paths: [tools/archcheck.py, tools/archcheck_rules.txt, tools/tests/archcheck]
spec: [0263, 0152]
---
# T006 — Architecture layer checker tools/archcheck.py

## Goal
Enforce the layer rules of axiom-c-stage0 automatically.

## Scope
- Parse #include "..." in bootstrap/axiom0/src/**; map files to layers; rules file with the ordered layers and explicit exceptions (objmodel is a low layer usable by target/x64, obj, link; obj/link never include MIR/HIR; interp never includes target; opt never includes syntax).
- Report violations as `file:line: layer X must not include Y`; exit non-zero.
- Also flag: mutable globals outside driver (heuristic: non-const file-scope variables), `printf`/`exit(` outside driver/diag render.
- Rules from ADR-0004 §8 and ADR-0005 §2: `types` never includes `interp` (const evaluation goes through the evaluator interface declared in `types`); a diagnostic code `AX_<AREA>_*` is registered only in `diag/codes/<AREA>.def`, and nothing is registered outside `diag/codes/`.

## Acceptance
- [ ] Checker passes on the skeleton; a deliberately bad fixture in tools/tests/archcheck triggers each rule.
- [ ] Runs from tools/ci.sh through the hook T004 pre-wired (this task does not edit the CI scripts).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T006-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
