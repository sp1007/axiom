---
id: T611
title: E15.3 — Loop-invariant code motion (LICM), induction strength reduction, loop unrolling/peeling & iterator fusion
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T610]
priority: 104
status: done
attempts: 1
paths: [compiler/opt/loop_xform, tests/run/opt_loops]
spec: [spec/SPEC-72-loops-scev-bce.md, tasks/0402, tasks/0426, tasks/0470, tasks/0549]
covers: [REQ-OPT-163, REQ-OPT-164, REQ-OPT-165, REQ-OPT-166, REQ-OPT-167, REQ-OPT-168, REQ-OPT-169, REQ-OPT-170, REQ-OPT-171, REQ-OPT-172, REQ-OPT-173, REQ-OPT-174, REQ-OPT-175, REQ-OPT-344, REQ-OPT-354]
started: 2026-11-07 16:14:03
finished: 2026-11-07 21:13:49
---
# T611 — E15.3 — Loop-invariant code motion (LICM), induction strength reduction, loop unrolling/peeling & iterator fusion

## Goal
Implement effect- and `MemorySSA`-verified Loop-Invariant Code Motion (`LICM`), induction variable strength reduction, bounded loop unrolling/peeling/unswitching, and lazy iterator pipeline fusion in `compiler/opt/loop_xform` per `spec/SPEC-72-loops-scev-bce.md`.

## Scope
- Implement `LICM` hoisting invariant pure expressions and `AliasInfo`/`MemorySSA`-proven invariant loads to the loop preheader while blocking hoisting of trapping/panicking expressions across non-executing loops and preserving atomic/volatile/IO barriers.
- Implement induction variable strength reduction (`REQ-OPT-173`, `REQ-OPT-174`), first-iteration loop peeling (enabling downstream BCE), loop unswitching (`REQ-OPT-171`), and cost-bounded full/partial loop unrolling (`REQ-OPT-169`, `REQ-OPT-170`).
- Implement loop versioning with semantically equivalent fallback guards (`REQ-OPT-163..165`) and adjacent loop fusion (`REQ-OPT-166..168`, `REQ-OPT-344`, `REQ-OPT-354`) so chained `std.iter` adapter pipelines (`map`/`filter`/`take`/`fold`) fuse into single scalar loops without intermediate heap allocations.

## Acceptance
- [ ] Differential run and `OptIR` dump tests in `tests/run/opt_loops` verify `LICM`, induction strength reduction, loop peeling/unrolling, and zero-allocation fusion of `std.iter` adapter chains across `--interp` and native `-O2`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T611-report.md` with exact `## Files changed`.

## Out of scope
- SIMD auto-vectorization (`E15.5`, `T616`–`T619`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T611/build` and `python tools/axtest.py --compiler build-snap-T611/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:40:00 created by T215 (P15 phase planning)
- 2026-11-07 16:14:03 started (attempt 1) T611-impl
- 2026-11-07 21:13:49 accepted by QA -> done
