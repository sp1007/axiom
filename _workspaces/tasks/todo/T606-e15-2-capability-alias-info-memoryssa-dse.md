---
id: T606
title: E15.2 — Capability-aware AliasInfo, provenance disjointness & MemorySSA store-to-load/DSE optimization
phase: P15-optimizer-2-0
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T601, T602, T605]
priority: 99
status: todo
attempts: 0
paths: [compiler/opt/alias, compiler/opt/memopt, tests/run/opt_alias]
locks: [compiler/opt/mod.ax, compiler/opt/optir/mod.ax, tests/selfhost/opt]
spec: [spec/SPEC-71-alias-escape-promotion.md, 0226, tasks/0366, tasks/0395, tasks/0486, tasks/0548]
covers: [REQ-OPT-312, REQ-OPT-313, REQ-OPT-314, REQ-OPT-347, REQ-OPT-358, REQ-OPT-365, REQ-OPT-366]
---
# T606 — E15.2 — Capability-aware AliasInfo, provenance disjointness & MemorySSA store-to-load/DSE optimization

## Goal
Implement the `AliasInfo` query engine exporting verified capability disjointness and place provenance into `OptIR`, together with `MemorySSA`-backed store-to-load forwarding, redundant load elimination, and dead store elimination (DSE) in `compiler/opt/alias` and `compiler/opt/memopt`.

## Scope
- Export verified disjoint mutable capability regions (`mut_view<T>`, disjoint sub-range/field splits) and immutable `view<T>` stability facts from `compiler/own` into `compiler/opt/alias` (`REQ-OPT-358`, `REQ-OPT-365`, `REQ-OPT-366`), keeping unknown raw-pointer / FFI aliasing conservative (`MayAlias`).
- Integrate `AliasInfo` with `MemorySSA` clobber walking to implement store-to-load forwarding, redundant load caching across non-clobbering calls/stores, and Dead Store Elimination (DSE) in `compiler/opt/memopt`.
- Enforce strict barriers for `Atomic` operations (`REQ-OPT-312`), `Volatile`/`Mmio` accesses (`REQ-OPT-313`), foreign calls (`REQ-OPT-314`), and zero-copy buffer lifetimes (`REQ-OPT-347`).

## Acceptance
- [ ] Differential run and dump tests in `tests/run/opt_alias` verify `NoAlias`/`MustAlias`/`MayAlias` derivation, store-to-load forwarding across disjoint `mut_view` writes, DSE of overwritten non-observable stores, and preservation of `volatile`/atomic/raw-pointer stores.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T606-report.md` with exact `## Files changed`.

## Out of scope
- Escape analysis and heap-to-stack/register promotion (`T607`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T606/build` and `python tools/axtest.py --compiler build-snap-T606/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:39:00 created by T215 (P15 phase planning)
