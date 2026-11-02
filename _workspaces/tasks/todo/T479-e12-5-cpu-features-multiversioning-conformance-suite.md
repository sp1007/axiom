---
id: T479
title: E12.5 — CPU feature detection & function multiversioning conformance suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T475, T476, T477, T478, T474]
priority: 169
status: todo
attempts: 0
paths: [tests/conformance/p12/e12_5_multiversioning]
spec: [spec/SPEC-44-cpu-features-multiversioning.md, 0095, tasks/0341, tasks/0344, tasks/0453]
covers: [REQ-SIMD-218, REQ-SIMD-220, REQ-SIMD-224]
---
# T479 — E12.5 — CPU feature detection & function multiversioning conformance suite

## Goal
Certify the `E12.5` CPU feature detection, `@target_feature` safety, and `@multiversion` dispatcher exit criteria across simulated oracle CPU feature profiles and native x86-64 execution.

## Scope
- Create `tests/conformance/p12/e12_5_multiversioning/` verifying: (1) semantic equivalence across all `@multiversion` clones under `--interp-cpu-features=sse2`, `sse4.1`, and `avx2,fma` and native x86-64 (`ASIMD-74`); (2) `CPUID`/`XGETBV` detection consistency; (3) compile-time rejection of unguarded calls to `@target_feature` functions (`ASIMD-71, 72`); and (4) static dispatch resolution when `--target-feature` is specified at compile time (`ASIMD-75`).

## Acceptance
- [ ] All tests in `tests/conformance/p12/e12_5_multiversioning/` pass under `axiomc2.exe` (`0 FAIL`, `WEAK-NATIVE 0`).
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T479-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library production source files.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T479/build` and `python tools/axtest.py --compiler build-snap-T479/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
