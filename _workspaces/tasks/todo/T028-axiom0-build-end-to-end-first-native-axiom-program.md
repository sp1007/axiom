---
id: T028
title: `axiom0 build` end to end: first native Axiom program
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T025, T027, T016]
priority: 45
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver/build_native, tests/run/native]
spec: [0152, 0263, 0186]
---
# T028 — `axiom0 build` end to end: first native Axiom program

## Goal
`fn main() -> i32 { return 42 }` compiles to a Windows exe that exits with 42 — First Native Axiom Program.

## Scope
- Wire MIR→LIR→x64→COFF→PE in the driver; `--features` advertises `native`; runner enables native mode for run tests.

## Acceptance
- [ ] All tests/run/basic pass in native mode as well as interp.
- [ ] Exit-42 test is green both ways.
- [ ] Cross-link oracle (T026): for every tests/run/basic program, `--emit=obj` linked by `gcc` gives the same exit code and stdout as our own PE output (SKIP when gcc is absent); a mismatch pinpoints our linker vs our object file.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T028-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
