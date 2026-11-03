---
id: T551
title: E14.1 — Comptime functions, blocks, const generics & comptime capability checking
phase: P14-comptime-2-0-reflection-genera
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T550]
priority: 171
status: todo
attempts: 0
paths: [compiler/ast, compiler/parser, compiler/hir, compiler/sema, tests/ui/comptime, tests/selfhost]
spec: [spec/SPEC-60-comptime-2-0.md, 0102, 0140, tasks/0340, tasks/0346, tasks/0509]
covers: [REQ-CTM-008, REQ-CTM-009, REQ-CTM-010, REQ-CTM-011, REQ-CTM-044, REQ-CTM-046, REQ-CTM-047, REQ-CORE-698, REQ-CORE-699, REQ-CORE-700, REQ-CORE-701, REQ-CORE-702, REQ-CORE-703, REQ-CORE-704, REQ-CORE-705, REQ-CORE-706, REQ-CORE-707, REQ-CORE-708, REQ-CORE-709, REQ-CORE-710, REQ-CORE-711, REQ-CORE-712, REQ-CORE-2150, REQ-CORE-2151, REQ-CORE-2152, REQ-CORE-2153, REQ-CORE-2154, REQ-CORE-2155, REQ-CORE-2156, REQ-CORE-2157, REQ-CORE-2158, REQ-CORE-2159, REQ-CORE-2160, REQ-CORE-2161, REQ-CORE-2162, REQ-CORE-2163, REQ-CORE-2164, REQ-CORE-2165, REQ-CORE-2166, REQ-CORE-2167, REQ-CORE-2168, REQ-CORE-2169]
---
# T551 — E14.1 — Comptime functions, blocks, const generics & comptime capability checking

## Goal
Implement surface parsing, HIR lowering, and semantic/capability verification for `comptime fn`, `comptime { ... }` blocks, `comptime` parameters, and sandboxed compile-time authority per `spec/SPEC-60-comptime-2-0.md`.

## Scope
- Extend `compiler/ast`, `compiler/parser`, and `compiler/hir` to support `comptime fn`, `comptime { ... }` expression blocks, and `comptime` function/type parameters (`[T, comptime N: usize]`).
- Enforce unified type checking, ownership, and capability rules inside `comptime` contexts in `compiler/sema`, rejecting undeclared external capabilities (ambient filesystem, network, process environment, wall-clock time, or arbitrary FFI calls) with `AX_CTM_CAPABILITY_DENIED` (`REQ-CTM-044, 047`, `COMPTIME-38..42`).
- Enforce the compile-time vs runtime effect boundary and verify that `unsafe` blocks inside `comptime` do not bypass comptime sandbox restrictions (`ACOMP2-36..49`, `COMPTIME-40`).

## Acceptance
- [ ] Positive and negative UI tests in `tests/ui/comptime` verify `comptime fn`, `comptime { ... }` blocks, `comptime` parameters, sandboxed capability enforcement, and `unsafe`-in-comptime boundaries.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T551-report.md` with exact `## Files changed`.

## Out of scope
- Full MIR comptime heap/drop evaluation and value lifting (`T552`) and partial evaluation (`T553`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T551/build` and `python tools/axtest.py --compiler build-snap-T551/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:20:00 created by T214 (P14 phase planning)
