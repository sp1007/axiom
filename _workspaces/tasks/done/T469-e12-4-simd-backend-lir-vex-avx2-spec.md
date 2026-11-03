---
id: T469
title: E12.4 — Canonical SIMD backend, LIR vector lowering & SSE2/AVX2 encoding specification (SPEC-43)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T463]
priority: 159
status: done
attempts: 1
paths: [spec/SPEC-43-simd-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-04-core-extensibility.md, 0095, 0162, 0179, 0181, tasks/0403, tasks/0407]
covers: [REQ-SIMD-019, REQ-SIMD-020, REQ-SIMD-021, REQ-SIMD-022, REQ-SIMD-023, REQ-SIMD-024, REQ-SIMD-025, REQ-SIMD-029, REQ-SIMD-030, REQ-SIMD-031, REQ-SIMD-032, REQ-SIMD-033, REQ-SIMD-034, REQ-SIMD-035, REQ-SIMD-036, REQ-SIMD-037, REQ-SIMD-038, REQ-SIMD-039, REQ-SIMD-042, REQ-SIMD-043, REQ-SIMD-046, REQ-SIMD-047, REQ-SIMD-048, REQ-SIMD-049, REQ-SIMD-050]
started: 2026-11-03 09:44:52
finished: 2026-11-03 09:59:24
---
# T469 — E12.4 — Canonical SIMD backend, LIR vector lowering & SSE2/AVX2 encoding specification (SPEC-43)

## Goal
Specify canonical `spec/SPEC-43-simd-backend.md` (`AXS-SBE-*`), defining LIR vector types (`v128`/`v256`/`v512`) and register classes (`Vec128`/`Vec256`/`Vec512`/`Mask`), legalizer splitting/scalarization, Windows x64 vector ABI, x86-64 `0F38`/`0F3A` and 2/3-byte `VEX` encoding, and SSE2/SSE4.1/AVX2/FMA instruction selection.

## Scope
- Write `spec/SPEC-43-simd-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SBE-NNN` rules.
- Define LIR `v128`, `v256`, `v512` types and `Vec128`, `Vec256`, `Vec512`, `Mask` register classes (`SPEC-04 AXS-EXT-050`), plus the `nontemporal` memory flag (`AXS-EXT-051`) and prefetch operations (`ASIMD-68..70`).
- Specify the vector legalizer rules: splitting wider semantic vectors (`v256`, `v512`, or 64-lane vectors) into native 128-bit `Vec128` (`XMM`) register pairs/quads when AVX2 is not enabled, or 256-bit `Vec256` (`YMM`) registers when `avx2` is enabled, and scalarizing operations that lack a direct hardware instruction while preserving exact lane and overflow semantics (`tasks/0403 §82`, `tasks/0407 §35`).
- Specify the Windows x64 vector ABI (`__m128`/`__m256` parameter/return rules, 16/32-byte stack alignment, `XMM6`–`XMM15` preservation, and `VZEROUPPER` before ABI transitions when `YMM` registers are touched).
- Specify the x86-64 `0F 38`, `0F 3A`, 2-byte `C5` VEX, and 3-byte `C4` VEX encoding tables (`AXS-EXT-053`) and SSE2/SSE4.1/AVX2/FMA instruction selection mappings.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-43-simd-backend.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SBE-NNN` rules, encoding tables, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated consistently with `SPEC-43`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T469-report.md` with exact `## Files changed`.

## Out of scope
- Backend implementation (`T470`–`T473`) and loop/SLP auto-vectorization passes (`Phase 15 E15.5`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T469/build` and `python tools/axtest.py --compiler build-snap-T469/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 09:44:52 started (attempt 1) 
- 2026-11-03 09:59:24 accepted by QA -> done
