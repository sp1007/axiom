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
attempts: 1
paths: [tests/driver, bootstrap/axiom0/src/driver/build_native, tests/run/native, bootstrap/axiom0/src/driver/emit_obj.c]
locks: [bootstrap/axiom0/src/target/x64/mir/mi.c, bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/target/x64/mir/frame.c, bootstrap/axiom0/src/target/x64/isel/isel.c, bootstrap/axiom0/src/types/typeck.c]
spec: [0152, 0263, 0186]
covers: [REQ-OWNER-006]
started: 2026-10-08 05:09:13
unblocks: 0
---
# T028 â€” `axiom0 build` end to end: first native Axiom program

## Goal
`fn main() -> i32 { return 42 }` compiles to a Windows exe that exits with 42 â€” First Native Axiom Program.

## Scope
- Wire MIRâ†’LIRâ†’x64â†’COFFâ†’PE in the driver; `--features` advertises `native`; runner enables native mode for run tests.
- `axiom0 build --emit=obj` (emitter file `src/driver/emit_obj.c`) and `--stack-reserve <bytes>` forwarded to the linker.

## Acceptance
- [ ] Every tests/run/basic program **without** a `native-after` directive passes in native mode as well as interp â€” the VS1 set of 0263 Â§51 (constants, arithmetic without traps, locals, `return`). Nothing from T033/T037 (branches, calls, traps) is implemented here (ADR-0005 Â§1).
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
- 2026-10-08 00:36:42 started (attempt 1) T028-impl
- 2026-10-08 01:32:10 block: buggy frame.c and isel.c cause memory corruption and SIB pointer bugs; need locks for bootstrap/axiom0/src/target/x64/mir/frame.c and bootstrap/axiom0/src/target/x64/isel/isel.c to fix them properly
- 2026-10-08 01:32:40 unblocked (cycle 1) 
- 2026-10-08 01:33:21 started (attempt 1) T028-impl
- 2026-10-08 05:07:45 block: typeck.c crashes on omitted return types in build_ok.test; need lock for bootstrap/axiom0/src/typeck/typeck.c
- 2026-10-08 05:08:19 unblocked (cycle 2) 
- 2026-10-08 05:09:13 started (attempt 1) T028-impl
- 2026-10-08 05:31:20 block: need paths for tests/driver and locks for bootstrap/axiom0/src/target/x64/mir/mi.c to fix build_ok.test and mi.c print_op AX_REG_NONE bug
- 2026-10-08 05:31:21 parked: unblock cap reached (unblocks=2, failed unblock agents=0); needs the owner


