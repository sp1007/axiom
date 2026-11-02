---
id: T558
title: E14.2 — Typed @derive expansion engine, provenance tracking & full semantic re-verification
phase: P14-comptime-2-0-reflection-genera
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T557]
priority: 178
status: todo
attempts: 0
paths: [compiler/hir/derive.ax, compiler/sema/derive_check.ax, compiler/mir, tests/ui/derive, tests/mir/derive]
spec: [spec/SPEC-61-reflection-derive.md, tasks/0343, tasks/0509]
covers: [REQ-CORE-640, REQ-CORE-641, REQ-CORE-642, REQ-CORE-643, REQ-CORE-644, REQ-CORE-645, REQ-CORE-646, REQ-CORE-647, REQ-CORE-648, REQ-CORE-649, REQ-CORE-650, REQ-CORE-651, REQ-CORE-652, REQ-CORE-653, REQ-CORE-654, REQ-CORE-655, REQ-CORE-656, REQ-CORE-657, REQ-CORE-658, REQ-CORE-659, REQ-CORE-2143, REQ-CORE-2144, REQ-CORE-2145, REQ-CORE-2146, REQ-CORE-2147, REQ-CORE-2148, REQ-CORE-2149, REQ-CORE-2170, REQ-CORE-2171, REQ-CORE-2172, REQ-CORE-2173, REQ-CORE-2174, REQ-CORE-2175, REQ-CORE-2176, REQ-CORE-2177, REQ-CORE-2178, REQ-CORE-2179]
---
# T558 — E14.2 — Typed @derive expansion engine, provenance tracking & full semantic re-verification

## Goal
Implement the typed `@derive` expansion and code-generation pipeline in `compiler/hir/derive.ax` and `compiler/sema/derive_check.ax` so reflection-based derives produce typed HIR trait implementations that undergo full semantic, ownership, capability, and MIR verification with source provenance.

## Scope
- Replace bootstrap hardcoded derive hooks with the extensible reflection-driven `@derive` engine in `compiler/hir/derive.ax` and `compiler/sema/derive_check.ax`.
- Attach generation provenance (`GenProvenanceId` linking the generated `impl` item and statements to the `@derive(...)` attribute span and offending field/variant span) so diagnostics report both the derive site and the specific un-derivable field (`AMETA-57..60`, `COMPTIME-58..60`).
- Ensure all generated `impl` declarations re-enter normal name resolution, trait solving, type checking, ownership/capability checking, and MIR verification (`AMETA-43..52`, `COMPTIME-63..67`), and diagnose derive cycles or conflicting impls deterministically (`AX_DERIVE_CONFLICT`, `AX_DERIVE_FIELD_BOUND`).

## Acceptance
- [ ] Positive and negative UI/MIR tests in `tests/ui/derive` and `tests/mir/derive` verify typed `@derive` expansion, field-level diagnostic provenance (`AX_DERIVE_FIELD_BOUND`), conflict detection (`AX_DERIVE_CONFLICT`), and full MIR verification of generated `impl` bodies.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T558-report.md` with exact `## Files changed`.

## Out of scope
- Standard library `std.reflect` and reflection-implemented `derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize)` (`T559`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P14 (`P14-comptime-2-0-reflection-genera`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T558/build` and `python tools/axtest.py --compiler build-snap-T558/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:21:00 created by T214 (P14 phase planning)
