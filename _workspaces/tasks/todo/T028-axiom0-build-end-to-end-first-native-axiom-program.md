---
id: T028
title: `axiom0 build` end to end: first native Axiom program
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T025b, T027, T016]
priority: 45
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver/build_native, tests/run/native, bootstrap/axiom0/src/driver/emit_obj.c]
locks: [bootstrap/axiom0/src/driver/pipeline.c]
spec: [0152, 0263, 0186]
covers: [REQ-OWNER-006]
---
# T028 — `axiom0 build` end to end: first native Axiom program

## Goal
`fn main() -> i32 { return 42 }` compiles to a Windows exe that exits with 42 — First Native Axiom Program.

## Scope
- Wire MIR→LIR→x64→COFF→PE in the driver; `--features` advertises `native`; runner enables native mode for run tests.
- `axiom0 build --emit=obj` (emitter file `src/driver/emit_obj.c`) and `--stack-reserve <bytes>` forwarded to the linker.

## Acceptance
- [ ] Every tests/run/basic program **without** a `native-after` directive passes in native mode as well as interp — the VS1 set of 0263 §51 (constants, arithmetic without traps, locals, `return`). Nothing from T033/T037 (branches, calls, traps) is implemented here (ADR-0005 §1).
- [ ] Exit-42 test is green both ways.
- [ ] Cross-link oracle (T026): for every run test that has native mode enabled, `--emit=obj` linked by `gcc` gives the same exit code and stdout as our own PE output (SKIP when gcc is absent); a mismatch pinpoints our linker vs our object file.
- [ ] `axiom0 build --stack-reserve 67108864` produces an image with that reserve (PE header check).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T028-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:24:25 covers += REQ-OWNER-006 (metadata only)
