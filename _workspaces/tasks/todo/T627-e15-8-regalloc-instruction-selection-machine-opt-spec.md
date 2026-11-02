---
id: T627
title: E15.8 — Canonical register allocation, instruction selection & machine optimization specification (SPEC-77)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215]
priority: 89
status: todo
attempts: 0
paths: [spec/SPEC-77-regalloc-machine-opt.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0162, 0182, 0235, 0237, 0252, tasks/0406, tasks/0553, tasks/0557, tasks/0559]
covers: [REQ-OPT-015, REQ-OPT-030, REQ-OPT-031, REQ-OPT-032, REQ-OPT-033, REQ-OPT-197, REQ-OPT-198, REQ-OPT-199, REQ-OPT-200, REQ-OPT-201, REQ-OPT-202]
---
# T627 — E15.8 — Canonical register allocation, instruction selection & machine optimization specification (SPEC-77)

## Goal
Consolidate the canonical specification for linear-scan register allocation, spill/reload generation, callee-saved frame integration, complex instruction selection, branchless if-conversion, and post-RA machine peephole optimization into `spec/SPEC-77-regalloc-machine-opt.md` (`AXS-RA-*` and `AXS-MCOPT-*` rule IDs).

## Scope
- Write `spec/SPEC-77-regalloc-machine-opt.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-RA-NNN` / `AXS-MCOPT-NNN` rules.
- Specify liveness analysis, live intervals with use-positions and loop-depth spill weights (`REQ-OPT-201`, `REQ-OPT-202`), linear-scan register allocation across ABI-driven register classes (`Gpr`, `Xmm`, `Vec128`/`Vec256` — `SPEC-04 AXS-EXT-050/053`), fixed-register precoloring/clobbers (`div`, shifts, calls), move coalescing, spill-slot allocation, and `FrameLayout` callee-saved register save/restore (`0182`, `0235`, `0252`, `tasks/0557`).
- Specify pattern-matching instruction selection (`lea` address modes, memory-operand folding, strength-reduced shifts/multiplies), branchless `cmov`/setcc if-conversion (`tasks/0553`), and microarchitectural latency/throughput cost modeling (`tasks/0406`, `REQ-OPT-197..200`).
- Specify post-RA machine optimization (`0237`, `tasks/0559`, `REQ-OPT-015`, `REQ-OPT-030..033`): redundant move elimination, peephole pattern rewrites, flag-liveness preservation, and strict barriers against eliminating memory-side-effecting, `volatile`, or atomic instructions.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-77-regalloc-machine-opt.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-RA-NNN` / `AXS-MCOPT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T627-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of linear-scan register allocation (`T063`) and instruction selection / peephole passes (`T628`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). Scheduled at `priority: 89` immediately before `T063` (`priority: 90`) so `E15.8` runs first in P15 (`ROADMAP.md` §3: `axiomc` itself becomes fast early).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:44:30 created by T215 (P15 phase planning)
