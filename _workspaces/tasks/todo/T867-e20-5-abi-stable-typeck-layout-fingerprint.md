---
id: T867
title: E20.5 @abi(stable) boundary typechecker, StableStruct/handle layout verifier & AbiFingerprint/ApiFingerprint calculator
phase: P20-build-system-package-ecosystem
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T681, T685, T318, T866]
priority: 217
status: todo
attempts: 0
paths: [compiler/abi/stability, compiler/abi/fingerprint, tests/run/abi_stability]
spec: [spec/SPEC-114-abi-stability-versioning-binary-compat.md, 0104, tasks/0452, tasks/0583, tasks/0739]
covers: [REQ-ECO-8734, REQ-PKG-022, REQ-PKG-024]
---
# T867 — E20.5 @abi(stable) boundary typechecker, StableStruct/handle layout verifier & AbiFingerprint/ApiFingerprint calculator

## Goal
Implement the `@abi(stable, version = "...")` boundary typechecker, extensible struct/opaque-handle layout verifier, and distinct `ApiFingerprint` / `SemanticFingerprint` / `AbiFingerprint` calculators per `spec/SPEC-114-abi-stability-versioning-binary-compat.md`.

## Scope
- Implement `compiler/abi/stability` validating `@abi(stable, version = "...")` and `@opaque` declarations, enforcing that every parameter, return type, and public field across a stable ABI boundary satisfies the Stable Axiom ABI type contract, and emitting structured diagnostics when unstable closures, unrepr'd ADTs, or uninstantiated generics cross a stable binary boundary (`0104 §6-20`, `tasks/0452 §193.6-18`, `tasks/0583 §324.5-22`, `REQ-ECO-8734`).
- Implement `compiler/abi/fingerprint` computing distinct deterministic hashes for `ApiFingerprint` (source signatures), `SemanticFingerprint` (inlined/comptime body semantics), and `AbiFingerprint` (physical sizes, alignments, field offsets, calling conventions, register classes, and `@abi(stable)` versions; `tasks/0452 §193.20-21`, `tasks/0583 §324.2`, `tasks/0739 §493.21-23`, `REQ-PKG-022`, `REQ-PKG-024`).
- Add positive and negative run/diagnostic tests in `tests/run/abi_stability`.

## Acceptance
- [ ] Run and diagnostic tests in `tests/run/abi_stability` verify `@abi(stable)` type checking, rejection of unstable types at stable boundaries, opaque handle layout isolation, and independent `ApiFingerprint` vs `AbiFingerprint` invariance across private implementation edits in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T867-report.md` with exact `## Files changed`.

## Out of scope
- Versioned linker symbol export tables and `axiomc abi-check` SemVer diff CLI (`T868`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T867/build` and `python tools/axtest.py --compiler build-snap-T867/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
