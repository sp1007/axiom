---
id: T628
title: E15.8 — Better instruction selection, branchless if-conversion & post-RA machine peephole optimization
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T063]
priority: 91
status: doing
attempts: 1
paths: [compiler/lir, compiler/backend/peephole, tests/mc/isel_peephole, compiler/target/x64, tests/selfhost/lir, tests/selfhost/isel, tests/selfhost/encode, tests/selfhost/backend]
spec: [spec/SPEC-77-regalloc-machine-opt.md, 0162, 0237, tasks/0406, tasks/0553, tasks/0559]
covers: [REQ-OPT-034, REQ-OPT-035, REQ-OPT-036, REQ-OPT-205, REQ-OPT-207, REQ-OPT-208, REQ-OPT-369, REQ-OPT-370]
started: 2026-11-03 07:16:36
---
# T628 — E15.8 — Better instruction selection, branchless if-conversion & post-RA machine peephole optimization

## Goal
Implement pattern-matching instruction selection (`lea` scaled addressing, immediate/memory folding, strength-reduced arithmetic), branchless `cmov` if-conversion, and post-RA machine peephole optimizations in `compiler/lir` and `compiler/backend/peephole` per `spec/SPEC-77-regalloc-machine-opt.md`.

## Scope
- Upgrade LIR → Machine IR instruction selection (`compiler/lir`) to fold `base + index * scale + disp` into x64 `lea` and memory operands, fold immediates into arithmetic/comparison instructions, and lower division/modulo by constants and power-of-two operations into shifts/multiplies where overflow semantics permit (`REQ-OPT-205`).
- Implement branchless if-conversion (`cmovcc` / `setcc`, `tasks/0553`, `REQ-OPT-207`, `REQ-OPT-208`, `REQ-OPT-369`, `REQ-OPT-370`) for short pure diamond branches without trapping or memory side effects.
- Implement the post-RA machine peephole optimizer (`compiler/backend/peephole`, `0237`, `REQ-OPT-034..036`): eliminate redundant `mov r, r`, fold `cmp reg, 0` → `test reg, reg` and `mov reg, 0` → `xor reg, reg` (when `EFLAGS` are dead), remove trivial jump-to-next-block edges, and enforce alias/volatile/atomic barriers on any store-to-load peephole.

## Acceptance
- [ ] Machine IR dump and differential run tests in `tests/mc/isel_peephole` verify `lea` addressing, constant-division lowering, branchless `cmov` selection, flag-safe `xor`/`test` peepholes, and preservation of `EFLAGS` on checked-arithmetic `jo`/`jb` traps across `-O1` and `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T628-report.md` with exact `## Files changed`.

## Out of scope
- SIMD vector instruction selection (delivered in P12 `E12.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T628/build` and `python tools/axtest.py --compiler build-snap-T628/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:30 created by T215 (P15 phase planning)
- 2026-11-03 07:16:36 started (attempt 1) 
