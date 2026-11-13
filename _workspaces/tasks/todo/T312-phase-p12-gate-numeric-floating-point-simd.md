---
id: T312
title: Phase P12 gate — Numeric, floating point & SIMD
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T212, T450, T451, T452, T453, T454, T455, T456, T457, T458, T459, T460, T461, T462, T463, T464, T465, T466, T467, T468, T469, T470, T471, T472, T473, T474, T475, T476, T477, T478, T479, T480, T481, T482, T483, T484]
priority: 312
status: todo
attempts: 0
paths: [tests/conformance/p12, _workspaces/reports/phase-P12-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-40-integers.md, spec/SPEC-41-floating-point.md, spec/SPEC-42-simd.md, spec/SPEC-43-simd-backend.md, spec/SPEC-44-cpu-features-multiversioning.md]
---
# T312 — Phase P12 gate: Numeric, floating point & SIMD

## Goal
Certify that phase P12 meets the exit criteria of every epic (`E12.1`–`E12.5`) in `spec/ROADMAP.md` §3 and that all 335 requirements mapped to the phase (`T450`–`T479`, including `REQ-OWNER-007`) are implemented and verified with differential equivalence between the MIR interpreter oracle and native Windows x86-64 execution.

## Scope
- Run the full suite on `axiomc2.exe` (`--exclude-requires axiom0-internal`) and run each P12 epic's exit-criterion conformance suite (`tests/conformance/p12/e12_1_integers` through `tests/conformance/p12/e12_5_multiversioning` and `tests/run/numeric/mixed_expr_matrix`).
- Verify `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P12-numeric-floating-point-simd` and `reqcov.py --strict`: every requirement mapped to P12 is implemented (`done`) with 0 gaps and 0 problems.
- Collect the phase conformance summary into `tests/conformance/p12/` and write the phase review `_workspaces/reports/phase-P12-review.md` (starting with a Vietnamese `## Tóm tắt` section).

## Acceptance
- [ ] Every epic exit criterion (`E12.1` 128-bit & saturating/bit/conversion conformance, `E12.2` `REQ-OWNER-007` complex mixed-type expression matrix Patterns A–D + IEEE-754 float/XMM ABI/`std.math` conformance, `E12.3` portable `Vector<T, N>`/`Mask<N>`/`TensorView` conformance, `E12.4` SSE2/AVX2/FMA differential interp/native vector conformance, `E12.5` CPU feature detection & `@multiversion` dispatcher conformance) is demonstrated with commands and results in the QA report.
- [ ] Full suite green under `axiomc2.exe` (`0 FAIL`, `WEAK-NATIVE 0` on all P12 tests; gate rule R9: PASS or BLOCKED); `reqcov.py --strict`, `harness_check.py`, and `archcheck.py` exit 0.
- [ ] `_workspaces/reports/phase-P12-review.md` and `_workspaces/reports/T312-report.md` written with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task `T212` and all expanded P12 tasks `T450`–`T479` (30 spec/implementation/conformance tasks across `E12.1`–`E12.5`).

## Log
- 2026-11-03 00:30:00 updated depends to include T450-T479 in T212 (P12 phase planning)
