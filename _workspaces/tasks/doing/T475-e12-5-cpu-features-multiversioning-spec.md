---
id: T475
title: E12.5 — Canonical CPU feature detection, @target_feature legality & function multiversioning specification (SPEC-44)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T463, T469]
priority: 165
status: doing
attempts: 1
paths: [spec/SPEC-44-cpu-features-multiversioning.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-04-core-extensibility.md]
spec: [spec/SPEC-04-core-extensibility.md, 0095, tasks/0341, tasks/0344, tasks/0347, tasks/0453]
covers: [REQ-SIMD-011, REQ-SIMD-012, REQ-SIMD-013, REQ-SIMD-094, REQ-SIMD-217, REQ-SIMD-219]
started: 2026-11-03 10:14:51
---
# T475 — E12.5 — Canonical CPU feature detection, @target_feature legality & function multiversioning specification (SPEC-44)

## Goal
Consolidate the CPU feature hierarchy (`TargetDesc` feature DAG), `@target_feature` attribute legality rules, `std.arch` runtime CPU feature detection, and `@multiversion` generated dispatcher contract into canonical `spec/SPEC-44-cpu-features-multiversioning.md` (`AXS-CPU-*`).

## Scope
- Write `spec/SPEC-44-cpu-features-multiversioning.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-CPU-NNN` rules.
- Define the x86-64 target feature hierarchy in `TargetDesc` (`SPEC-04 AXS-EXT-060`): baseline `sse`/`sse2` on `x86_64-windows`, optional features `sse3`, `ssse3`, `sse4.1`, `sse4.2`, `popcnt`, `lzcnt`, `bmi1`, `bmi2`, `avx`, `avx2`, `fma`, `avx512f`, their implication DAG (`avx2 -> avx -> sse4.2 -> sse4.1 -> ssse3 -> sse3 -> sse2`), and the `--target-feature=+feat,-feat` CLI option.
- Specify `@target_feature("...")` (`SPEC-04 AXS-EXT-022/032/054/091`): codegen legality vs language semantics invariant (features never alter Core language semantics, `ANUM-29..30`, `ASIMD-71..74`), call-site safety rules (calling a function with narrower caller features requires an `unsafe` block, a dominating `is_x86_feature_detected` branch, or `@multiversion` dispatch; otherwise `AX_TARGET_FEATURE_MISMATCH`), and inliner restrictions.
- Specify `std.arch.is_x86_feature_detected` runtime detection (`CPUID` leaves 1 and 7 plus `XGETBV` OS `XCR0` XMM/YMM/ZMM state check, cached atomically, simulated in the oracle via `--interp-cpu-features`).
- Specify `@multiversion` function multiversioning (`0095 §8`, `tasks/0453 §194.14-15`, `ASIMD-73..78`): syntax, mandatory baseline clone, symbol mangling, deterministic runtime feature-priority dispatcher, static dispatch elimination when compile-time target features satisfy the highest clone, and external ABI preservation.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and `spec/SPEC-04-core-extensibility.md`.

## Acceptance
- [ ] `spec/SPEC-44-cpu-features-multiversioning.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-CPU-NNN` rules, positive/negative canonical Axiom examples, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and `spec/SPEC-04-core-extensibility.md` are updated consistently.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T475-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and library implementation (`T476`–`T478`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T475/build` and `python tools/axtest.py --compiler build-snap-T475/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 10:14:51 started (attempt 1) 
