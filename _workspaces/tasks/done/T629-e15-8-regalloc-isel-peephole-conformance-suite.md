---
id: T629
title: E15.8 — Register allocation, instruction selection & post-RA machine optimization conformance suite
phase: P15-optimizer-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T628]
priority: 92
status: done
attempts: 1
paths: [tests/conformance/p15/e15_8_regalloc_isel]
spec: [spec/SPEC-77-regalloc-machine-opt.md, 0182, 0235, 0237, 0252, tasks/0553, tasks/0557, tasks/0559]
covers: [REQ-OPT-371, REQ-OPT-372]
started: 2026-11-04 22:10:05
finished: 2026-11-04 23:49:59
---
# T629 — E15.8 — Register allocation, instruction selection & post-RA machine optimization conformance suite

## Goal
Certify E15.8 exit criteria with an end-to-end differential and machine-verifier conformance suite covering linear-scan register allocation, spill/reload under extreme register pressure, complex instruction selection, branchless if-conversion, and post-RA machine peephole optimization.

## Scope
- Create differential conformance tests in `tests/conformance/p15/e15_8_regalloc_isel` verifying:
  - high-pressure live ranges (>32 simultaneous live locals across nested loops and calls), fixed-register clobbers (`div`/`rem`, variable shifts), and callee-saved register restoration (`RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15`);
  - `lea` scaled-index addressing, branchless `cmov` diamonds, and post-RA peephole transformations (`REQ-OPT-371`, `REQ-OPT-372`) passing the Machine IR verifier;
  - exact observable equivalence between `--interp`, `-O0`, `-O1`, and `-O2` on all register-pressure and flag-clobber edge cases.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p15/e15_8_regalloc_isel` pass in `--interp` and native `-O0`/`-O1`/`-O2` modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T629-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T629/build` and `python tools/axtest.py --compiler build-snap-T629/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:30 created by T215 (P15 phase planning)
- 2026-11-04 22:10:05 started (attempt 1) T629-impl
- 2026-11-04 23:49:59 accepted by QA -> done
