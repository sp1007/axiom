---
id: T476
title: E12.5 — TargetDesc feature hierarchy, @target_feature attribute checking & call-site legality verifier
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T475, T464]
priority: 166
status: todo
attempts: 0
paths: [compiler/hir, compiler/types, compiler/verify, compiler/driver, tests/ui/simd/target_feature]
locks: [compiler/diag/code.ax, tests/selfhost]
spec: [spec/SPEC-44-cpu-features-multiversioning.md, spec/SPEC-04-core-extensibility.md, 0095, tasks/0344, tasks/0453]
covers: [REQ-SIMD-051, REQ-SIMD-079, REQ-SIMD-243, REQ-SIMD-256]
---
# T476 — E12.5 — TargetDesc feature hierarchy, @target_feature attribute checking & call-site legality verifier

## Goal
Implement the x86-64 `TargetDesc` feature implication DAG, `--target-feature` CLI option, `@target_feature` attribute lowering, and compile-time call-site and target-intrinsic legality checking.

## Scope
- Populate the x86-64 feature table and implication closure (`avx2 => avx => sse4.2 => sse4.1 => ssse3 => sse3 => sse2`, `fma => avx`) in `compiler/` and add `--target-feature=+feat,-feat` to `compiler/driver/opts.ax`.
- Lower `@target_feature("...")` in `compiler/hir/lower.ax` and `compiler/types/typeck.ax` into the `TargetFeature` attribute side table (`AXS-EXT-032`) and function signature `target_features` bitmask (`AXS-EXT-022`), rejecting unknown feature names (`AX_TARGET_UNKNOWN_FEATURE`) or applying `@target_feature` to non-function items (`AX_TARGET_INVALID_ATTRIBUTE`).
- Enforce in `compiler/types/typeck.ax` and `compiler/verify/verifier.ax` that calling a `@target_feature` function or target-specific `std.arch.x86_64` intrinsic from a function without those features enabled is rejected with `AX_TARGET_FEATURE_MISMATCH` unless inside an `unsafe` block or guarded by a dominating `is_x86_feature_detected` check.

## Acceptance
- [ ] `tests/ui/simd/target_feature/*.ax` verifies diagnostics `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_INVALID_ATTRIBUTE`, and `AX_TARGET_FEATURE_MISMATCH` on unguarded calls, while accepting calls inside matching `@target_feature` functions, `unsafe` blocks, or feature-detected branches.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T476` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T476-report.md` with exact `## Files changed`.

## Out of scope
- Runtime `CPUID`/`XGETBV` intrinsics (`T477`) and `@multiversion` clone/dispatcher generation (`T478`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T476/build` and `python tools/axtest.py --compiler build-snap-T476/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
