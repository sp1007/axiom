---
id: T477
title: E12.5 — Runtime CPU feature detection (CPUID/XGETBV) in std.arch & oracle feature simulation
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T476, T473]
priority: 167
status: todo
attempts: 0
paths: [std/arch/detect.ax, compiler/interp, tests/std/arch_detect, tests/selfhost]
locks: [std/arch/x86_64.ax, compiler/target/x64/isel.ax, compiler/target/x64/encode.ax, compiler/driver/opts.ax, compiler/interp_opt/session.ax, tests/selfhost]
spec: [spec/SPEC-44-cpu-features-multiversioning.md, 0095, tasks/0341, tasks/0344, tasks/0453]
covers: [REQ-SIMD-095, REQ-SIMD-257]
---
# T477 — E12.5 — Runtime CPU feature detection (CPUID/XGETBV) in std.arch & oracle feature simulation

## Goal
Implement x86-64 `cpuid_count` and `xgetbv` intrinsics (native x86-64 emission + configurable `--interp-cpu-features` oracle simulation) and `std/arch/detect.ax` (`is_x86_feature_detected`).

## Scope
- Add `cpuid_count(leaf: u32, subleaf: u32) -> CpuidResult` and `xgetbv(xcr: u32) -> u64` intrinsics in `std/arch/x86_64.ax`, emit native `CPUID` (`0F A2`, preserving `RBX`) and `XGETBV` (`0F 01 D0`) in `compiler/target/x64/isel.ax` and `encode.ax`, and simulate them deterministically in `compiler/interp/` controlled by `--interp-cpu-features=<list>` (defaulting to `sse2,sse3,ssse3,sse4.1,sse4.2,popcnt,lzcnt,bmi1,bmi2,avx,avx2,fma`).
- Create `std/arch/detect.ax` providing `is_x86_feature_detected(feature: Str) -> bool` and fast feature-bit queries (`has_sse2`, `has_sse41`, `has_avx`, `has_avx2`, `has_fma`, `has_bmi1`, `has_bmi2`, `has_popcnt`, `has_lzcnt`, `has_avx512f`), verifying both CPUID feature bits and OS `XCR0` (`(xcr0 & 0x6) == 0x6` for AVX/AVX2/FMA YMM state, `(xcr0 & 0xE6) == 0xE6` for AVX-512).

## Acceptance
- [ ] `tests/std/arch_detect/*.ax` passes under `--interp` (testing `--interp-cpu-features=sse2` vs `--interp-cpu-features=sse2,sse4.1,avx,avx2,fma`) and native x86-64 execution (`WEAK-NATIVE 0`).
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T477` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T477-report.md` with exact `## Files changed`.

## Out of scope
- `@multiversion` automatic clone and dispatcher generation (`T478`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T477/build` and `python tools/axtest.py --compiler build-snap-T477/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
