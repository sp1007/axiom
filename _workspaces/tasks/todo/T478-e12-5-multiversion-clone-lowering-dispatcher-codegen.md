---
id: T478
title: E12.5 — Function multiversioning (@multiversion) clone lowering & dispatcher codegen
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T477]
priority: 168
status: todo
attempts: 0
paths: [compiler/hir, compiler/mir, compiler/lir, compiler/target/x64, tests/mir/multiversion, tests/run/simd/multiversion, tests/selfhost]
locks: [compiler/types/typeck.ax, compiler/backend/session.ax, tests/selfhost]
spec: [spec/SPEC-44-cpu-features-multiversioning.md, 0095, tasks/0341, tasks/0344, tasks/0453]
covers: [REQ-SIMD-221, REQ-SIMD-222, REQ-SIMD-223]
---
# T478 — E12.5 — Function multiversioning (@multiversion) clone lowering & dispatcher codegen

## Goal
Implement `@multiversion("avx2,fma", "sse4.1")` / `@target_feature` function multiversioning, compiling per-feature specialized clones plus a baseline fallback and emitting a deterministic runtime/compile-time dispatcher.

## Scope
- Lower `@multiversion(...)` functions in `compiler/hir/lower.ax`, `compiler/types/typeck.ax`, and `compiler/mir/builder.ax` into specialized per-feature clone bodies (`<fn>$mv$avx2_fma`, `<fn>$mv$sse4_1`, `<fn>$mv$default`) carrying their respective `target_features` sets (`SPEC-04 AXS-EXT-022/054`).
- Propagate per-function `target_features` through `compiler/lir/` and `compiler/target/x64/isel.ax` so each clone selects instructions legal for its feature set (e.g., `YMM` AVX2/FMA in the `avx2,fma` clone, `XMM` SSE4.1 in the `sse4.1` clone, and baseline SSE2 in the default clone) while preserving identical external ABI at the public symbol (`ASIMD-78`).
- Generate the deterministic dispatcher body for the public function symbol: when compile-time `--target-feature` statically satisfies the highest specialized clone, tail-call/inline it directly (`ASIMD-75, 76`); otherwise dispatch via `std.arch.detect` in descending feature priority order (`avx2+fma` -> `sse4.1` -> `default`).

## Acceptance
- [ ] `tests/mir/multiversion/*.ax` (`inspect --emit=mir` and `--emit=lir`) verifies clone synthesis, per-clone `target_features`, and static dispatch elimination when `--target-feature=+avx2,+fma` is passed.
- [ ] `tests/run/simd/multiversion/*.ax` passes under `--interp` (across `--interp-cpu-features=sse2`, `sse4.1`, and `avx2,fma`) and native x86-64 execution (`WEAK-NATIVE 0`), producing bit-identical results across all clones (`ASIMD-74`).
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T478` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T478-report.md` with exact `## Files changed`.

## Out of scope
- Cross-module LTO multiversion clone pruning (`Phase 15 E15.6`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T478/build` and `python tools/axtest.py --compiler build-snap-T478/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
