---
id: T682
title: E16.8 — @cfg(...) predicate evaluator, target-matrix conditional HIR pruning & host-vs-target isolation
phase: P16-targets-platforms
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T654, T681]
priority: 125
status: todo
attempts: 0
paths: [compiler/hir/cfg, compiler/driver/cross, tests/run/cfg_target, tests/ui/cfg, tests/selfhost/hir, tests/selfhost/driver]
spec: [spec/SPEC-88-cross-compilation-platform-layer.md, spec/SPEC-04-core-extensibility.md, tasks/0453, tasks/0587]
covers: [REQ-TOOL-001, REQ-TGT-319, REQ-TGT-321, REQ-TGT-322, REQ-TGT-323]
---
# T682 — E16.8 — @cfg(...) predicate evaluator, target-matrix conditional HIR pruning & host-vs-target isolation

## Goal
Implement `@cfg(...)` conditional compilation predicate evaluation and pre-resolution HIR pruning in `compiler/hir/cfg`, and enforce strict host-vs-target isolation and target-matrix build orchestration in `compiler/driver/cross`.

## Scope
- Implement `@cfg(...)` parsing, schema validation, and evaluation against the active session's `TargetDesc`, `Profile`, and `TargetFeatureSet` in `compiler/hir/cfg`:
  - Support `target_arch`, `target_os`, `target_env`, `target_abi`, `target_endian`, `target_pointer_width`, `target_feature`, `profile`, `debug_assertions`, and `all(...)` / `any(...)` / `not(...)`.
  - Emit `AX_NAME_INVALID_CFG_PREDICATE` on unknown `@cfg` keys or malformed combinators.
  - Prune false `@cfg`-gated items, struct fields, enum variants, `impl` blocks, and statements after parsing and before name resolution so inactive target-specific code is syntactically checked without polluting the active target's symbol table.
- Implement `compiler/driver/cross`:
  - Route `--target <triple>`, `--sysroot <dir>`, and `--target-sdk <dir>` into the compilation session and include `TargetFingerprint` in all query/codegen cache keys (`ABACKEND-94`).
  - Ensure `size_of`, `align_of`, `usize`/`isize` bounds, and endianness in `const`/comptime evaluation query `session.target` (`wasm32` = 32-bit, 64-bit targets = 64-bit) rather than host pointer sizes.
- Add positive and negative tests in `tests/run/cfg_target`, `tests/ui/cfg`, `tests/selfhost/hir`, and `tests/selfhost/driver`.

## Acceptance
- [ ] `@cfg(...)` predicates select the right items/fields per `--target` and reject unknown keys or syntax errors inside inactive `@cfg` arms.
- [ ] Cross-compiling a program containing `const PTR_BYTES: usize = size_of.<usize>()` for `--target wasm32` on a 64-bit Windows/Linux host evaluates `PTR_BYTES` to `4`.
- [ ] Positive and negative tests in `tests/run/cfg_target`, `tests/ui/cfg`, `tests/selfhost/hir`, and `tests/selfhost/driver` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T682-report.md` with exact `## Files changed`.

## Out of scope
- Hermetic cross-target import stubs and `std.os.*` library modules (`T683`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:43:00 created by T216 (P16 phase planning)
