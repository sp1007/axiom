---
id: T622
title: E15.6 — Linker section GC (COMDAT/dead stripping), Identical Code Folding (ICF) & deterministic PGO instrumentation/use pipeline
phase: P15-optimizer-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T621]
priority: 116
status: todo
attempts: 0
paths: [compiler/opt/pgo, compiler/link/gc_icf, tests/run/opt_pgo_gc]
spec: [spec/SPEC-04-core-extensibility.md, spec/SPEC-75-lto-wpo-section-gc-pgo.md, tasks/0355, tasks/0408, tasks/0410, tasks/0581, tasks/0594, tasks/0595, tasks/0597]
covers: [REQ-OPT-236, REQ-OPT-237, REQ-OPT-238, REQ-OPT-239, REQ-OPT-240, REQ-OPT-241, REQ-OPT-283, REQ-OPT-284, REQ-OPT-285, REQ-OPT-286, REQ-OPT-287, REQ-OPT-288, REQ-OPT-289, REQ-OPT-290, REQ-OPT-291, REQ-OPT-377, REQ-OPT-378, REQ-OPT-383, REQ-OPT-384]
---
# T622 — E15.6 — Linker section GC (COMDAT/dead stripping), Identical Code Folding (ICF) & deterministic PGO instrumentation/use pipeline

## Goal
Implement linker section garbage collection (`COMDAT` / dead function and data stripping), safe Identical Code Folding (`ICF`), and the deterministic AOT Profile-Guided Optimization (`--pgo-gen` / `--pgo-use`) pipeline in `compiler/link/gc_icf` and `compiler/opt/pgo`.

## Scope
- Emit per-symbol `comdat` / subsection graphs (`SPEC-04 AXS-EXT-071`) and implement deterministic mark-sweep section GC and safe `ICF` in `compiler/link/gc_icf`, stripping unreachable functions, `.rdata` constants, and unused runtime components (`REQ-OPT-283..290`).
- Implement deterministic counter instrumentation (`--pgo-gen`), canonical profile file serialization/merging with CFG hash provenance (`REQ-OPT-291`, `REQ-OPT-383`, `REQ-OPT-384`), and profile-guided profitability weighting (`--pgo-use=<path>`) in `compiler/opt/pgo` (`REQ-OPT-377`, `REQ-OPT-378`).
- Feed PGO branch/call/loop weights into inlining thresholds, specialization, loop unrolling/peeling, hot/cold block splitting, and branch layout (`REQ-OPT-236..241`) while gracefully downgrading stale function hashes with a warning.

## Acceptance
- [ ] Differential run and binary-inspection tests in `tests/run/opt_pgo_gc` verify dead function/data stripping, safe `ICF`, deterministic byte-identical builds under `--pgo-use`, and stale-profile fallback without altering observable program semantics.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T622-report.md` with exact `## Files changed`.

## Out of scope
- Benchmark suite and CI regression gate (`E15.7`, `T624`–`T626`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T622/build` and `python tools/axtest.py --compiler build-snap-T622/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:43:00 created by T215 (P15 phase planning)
