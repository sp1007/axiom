---
id: T474
title: E12.4 — SIMD backend differential (oracle vs SSE2/AVX2 native) conformance suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T469, T470, T471, T472, T473, T468]
priority: 164
status: todo
attempts: 0
paths: [tests/conformance/p12/e12_4_simd_backend]
spec: [spec/SPEC-43-simd-backend.md, tasks/0403, tasks/0407]
covers: [REQ-SIMD-118, REQ-SIMD-119, REQ-SIMD-120, REQ-SIMD-121, REQ-SIMD-122, REQ-SIMD-123, REQ-SIMD-194, REQ-SIMD-195, REQ-SIMD-196, REQ-SIMD-197, REQ-SIMD-198, REQ-SIMD-199, REQ-SIMD-200, REQ-SIMD-201, REQ-SIMD-202, REQ-SIMD-203, REQ-SIMD-204, REQ-SIMD-205, REQ-SIMD-206, REQ-SIMD-207, REQ-SIMD-280, REQ-SIMD-281, REQ-SIMD-282, REQ-SIMD-283, REQ-SIMD-284, REQ-SIMD-285, REQ-SIMD-331, REQ-SIMD-334]
---
# T474 — E12.4 — SIMD backend differential (oracle vs SSE2/AVX2 native) conformance suite

## Goal
Certify the `E12.4` SIMD backend exit criteria through differential (`--interp` vs native SSE2 and AVX2/FMA) conformance tests, Win64 ABI stress tests, and machine-code encoding verification.

## Scope
- Create `tests/conformance/p12/e12_4_simd_backend/` testing differential execution (`--interp` vs native SSE2 baseline and native AVX2/FMA) across 64-bit, 128-bit, 256-bit, and 512-bit `Vector<T, N>` and `Mask<N>` kernels (dot product, 4x4 matrix multiply, FIR filter, RGBA pixel alpha blend, byte histogram, and masked gather/scatter).
- Verify `XMM6`–`XMM15` callee-saved register preservation across nested Win64 calls with > 16 live vectors, `VZEROUPPER` hygiene, and non-temporal store + `sfence` execution.

## Acceptance
- [ ] All tests in `tests/conformance/p12/e12_4_simd_backend/` pass under `axiomc2.exe` (`0 FAIL`, `WEAK-NATIVE 0`) with bit-identical `--interp` and native x86-64 outputs.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T474-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or standard library production source files.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T474/build` and `python tools/axtest.py --compiler build-snap-T474/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
