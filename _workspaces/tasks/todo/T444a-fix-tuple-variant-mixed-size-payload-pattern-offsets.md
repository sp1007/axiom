---
id: T444a
title: Fix — tuple-variant payload with mixed field sizes binds the wrong bytes in patterns (`Pair(7u8, 9u64)` as `Pair(a, _)` gives a = 0)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T444]
priority: 22
status: todo
attempts: 0
timeout_min: 600
paths: [tests/run/enum_payload_mixed]
locks: [compiler/types/layout.ax, compiler/mir/builder.ax, compiler/interp, compiler/lir/builder.ax]
spec: [spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-LAY-136, REQ-TST-072]
---
# T444a — Fix: mixed-size tuple-variant payload offsets in patterns

## Goal
Every field of an enum variant payload is read and written at the offset the layout engine assigned to it, in
construction, in pattern bindings and in field projections, in the oracle and natively (T444 report F2).

## Scope
- Repro (baseline `axiomc2`, interp and native): `enum Choice { Pair(u8, u64), ... }`, `Choice.Pair(7u8, 9u64)`
  matched as `Choice.Pair(a, _)` binds `a = 0`. The layout engine orders the payload by size (u64 first) while the
  pattern projection reads the u8 at its declared position. Find the single source of truth (the layout's field
  offset table for the variant) and make construction, pattern projection (MIR builder) and the interpreter use it;
  no second ordering rule anywhere.
- Regression tests `tests/run/enum_payload_mixed/*.ax` (interp, native, native-O1, exact `// stdout:`): two- and
  three-field payloads with every size order (u8/u16/u32/u64/pointer/struct), binding each field alone and all
  together (use one-binding-per-arm patterns where T444b is not yet done), nested enum in a struct, enum behind a
  raw pointer, `if let`, and `size_of` of the enum.

## Acceptance
- [ ] All new tests pass in the three modes; WEAK-NATIVE 0.
- [ ] Bootstrap stage 1-3 succeeds (the compiler itself uses payload enums).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T444a-report.md` with the root cause and exact `## Files changed`.

## Out of scope
- `@repr(C)` enum layout contracts, niche optimisation; the use-after-move diagnostic on two bindings (T444b).
- `bootstrap/axiom0` (frozen), `std/`, `docs/`.

## Notes
- If the fix lies outside the listed locks, stop and report (architect widens the locks).
- Canonical syntax (`=`, `.`), see axiom-syntax.

## Log
- 2026-11-17 created by axiom-architect (T444 report F2; ADR-0043 §4)
