---
id: T601
title: E15.1 — Verified MIR to OptIR lowering, dominance frontier & SSA/MemorySSA construction
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T600]
priority: 94
status: doing
attempts: 1
paths: [compiler/opt/optir, compiler/driver, tests/run/optir_ssa, tests/selfhost/opt, tests/selfhost/driver, tests/selfhost/obj_link_driver]
spec: [spec/SPEC-70-optir-ssa-memoryssa.md, tasks/0315, tasks/0366, tasks/0398, tasks/0794, tasks/0796]
covers: [REQ-OPT-337, REQ-OPT-338, REQ-OPT-340, REQ-OPT-341, REQ-OPT-390, REQ-OPT-391, REQ-OPT-392, REQ-OPT-397, REQ-OPT-398, REQ-OPT-399, REQ-OPT-400, REQ-OPT-401, REQ-OPT-402, REQ-OPT-403]
started: 2026-11-03 08:23:12
agent: T601-impl
---
# T601 — E15.1 — Verified MIR to OptIR lowering, dominance frontier & SSA/MemorySSA construction

## Goal
Implement `OptIR` data structures, Verified MIR → `OptIR` lowering, dominance tree / dominance frontier computation, SSA construction, `MemorySSA` (`MemoryDef`/`MemoryUse`/`MemoryPhi`), and `OptIR` → LIR/MIR reconstruction in `compiler/opt/optir` per `spec/SPEC-70-optir-ssa-memoryssa.md`.

## Scope
- Implement `OptIR` representation in `compiler/opt/optir` preserving source-to-machine debug spans (`REQ-OPT-341`), checked vs wrapping arithmetic semantics, and explicit `Drop`/panic/atomic/volatile barriers (`REQ-OPT-340`).
- Compute CFG predecessors/successors, Cooper-Harvey-Kennedy dominator trees, dominance frontiers, and minimal SSA phi placement for scalar and aggregate-projected locals (`REQ-OPT-337`, `REQ-OPT-338`).
- Construct `MemorySSA` (`LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`) over memory-touching operations, calls, `Drop`, atomics, and `volatile` accesses.
- Implement the three-valued analysis certainty lattice (`Proven`, `Possible`, `Unknown` — `REQ-OPT-390..392`, `REQ-OPT-397..403`) with bounded, deterministic path/range fact propagation and provenance records (`ProofProvenance`).
- Add `inspect --emit=optir` and `--emit=memssa` dumps for deterministic inspection.

## Acceptance
- [ ] Run and dump tests in `tests/run/optir_ssa` verify SSA phi placement, `MemorySSA` def-use chains, `Proven`/`Possible`/`Unknown` certainty tracking, and round-trip equivalence between `--interp` and native codegen.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T601-report.md` with exact `## Files changed`.

## Out of scope
- Pass manager scheduling (`T602`) and scalar optimization passes (`T603`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T601/build` and `python tools/axtest.py --compiler build-snap-T601/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:38:00 created by T215 (P15 phase planning)
- 2026-11-03 08:23:12 started (attempt 1) T601-impl
