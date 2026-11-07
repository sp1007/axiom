---
id: T621
title: E15.6 — Whole-program closed-world reachability, cross-module LTO inlining/specialization & generic deduplication
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T614, T620]
priority: 115
status: done
attempts: 1
paths: [compiler/opt/lto, tests/run/opt_lto]
spec: [spec/SPEC-75-lto-wpo-section-gc-pgo.md, tasks/0355, tasks/0409, tasks/0580, tasks/0594]
covers: [REQ-OPT-271, REQ-OPT-272, REQ-OPT-273, REQ-OPT-274, REQ-OPT-275, REQ-OPT-276, REQ-OPT-277, REQ-OPT-278, REQ-OPT-279, REQ-OPT-280, REQ-OPT-281, REQ-OPT-282, REQ-OPT-375, REQ-OPT-376, REQ-OPT-379, REQ-OPT-380]
started: 2026-11-07 22:27:55
finished: 2026-11-08 01:35:24
---
# T621 — E15.6 — Whole-program closed-world reachability, cross-module LTO inlining/specialization & generic deduplication

## Goal
Implement `--lto` whole-program reachability analysis, cross-module `OptIR` summary serialization, cross-module inlining/constant propagation/escape/devirtualization, and generic monomorphization deduplication in `compiler/opt/lto`.

## Scope
- Implement summary-based and full cross-module `OptIR` LTO (`compiler/opt/lto`, `REQ-OPT-375`, `REQ-OPT-376`, `REQ-OPT-379`, `REQ-OPT-380`) preserving partitionable incremental compilation when `--lto` is off or in thin-summary mode.
- Compute closed-world reachability from executable/library roots (`main`, `@entry`, `@export`, reflection roots, FFI callbacks) and perform cross-module inlining, constant propagation, escape analysis, alias propagation, and proven closed-world devirtualization (`REQ-OPT-271..278`).
- Deduplicate semantically and representationally identical generic instantiations across modules while preserving distinct observable function addresses when taken (`ALTO-30..33`).

## Acceptance
- [ ] Differential run and dump tests in `tests/run/opt_lto` verify cross-module inlining, closed-world `dyn Trait` devirtualization, generic deduplication, and preservation of `@export`/FFI/atomic/volatile roots under `--lto`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T621-report.md` with exact `## Files changed`.

## Out of scope
- Linker section GC, ICF, and PGO profile generation/consumption (`T622`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T621/build` and `python tools/axtest.py --compiler build-snap-T621/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:43:00 created by T215 (P15 phase planning)
- 2026-11-07 22:27:55 started (attempt 1) T621-impl
- 2026-11-08 01:35:24 accepted by QA -> done
