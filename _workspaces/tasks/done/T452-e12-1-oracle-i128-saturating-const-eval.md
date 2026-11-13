---
id: T452
title: E12.1 — Oracle 128-bit evaluator, saturating/bit intrinsics & const folding
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T451]
priority: 142
status: done
attempts: 1
timeout_min: 1500
paths: [compiler/interp, compiler/opt, tests/run/int128_interp, tests/opt/int128]
locks: [compiler/interp_opt/session.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/types/typeck.ax, compiler/driver/pipeline.ax, std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-40-integers.md, spec/SPEC-03-core-semantics.md, tasks/0327, tasks/0334]
covers: [REQ-SIMD-176, REQ-SIMD-177, REQ-SIMD-264, REQ-SIMD-265]
started: 2026-11-12 23:28:49
finished: 2026-11-13 16:42:03
---
# T452 — E12.1 — Oracle 128-bit evaluator, saturating/bit intrinsics & const folding

## Goal
Implement exact 128-bit (`i128`/`u128`) arithmetic, saturating operations (`SatAdd`/`SatSub`/`SatMul`), extended bit manipulation intrinsics, and constant folding in the MIR interpreter oracle (`--interp`) and `-O1` optimizer.

## Scope
- Extend `compiler/interp/value.ax` and `compiler/interp/interp.ax` to represent and evaluate `i128` and `u128` values (`(lo: u64, hi: u64)` two's-complement arithmetic) for `+`, `-`, `*`, `/`, `%`, unary `-`, bitwise `&`, `|`, `^`, `~`, shifts `<<`/`>>` (panicking when shift `< 0` or `>= 128`), comparisons, and `IntToInt` casts across all widths `i8..i128` and `u8..u128`.
- Enforce exact checked overflow panics (`arithmetic overflow` on `i128.MIN / -1`, `i128.MIN % -1`, `+`/`-`/`*` out of range; `division by zero` on `/ 0` and `% 0`) in both runtime `--interp` and compile-time `ConstEvaluator` (`AX_CONST_OVERFLOW`, `AX_CONST_DIV_ZERO`).
- Evaluate `MirBinOp.SatAdd`, `SatSub`, `SatMul` and bit intrinsics (`wrapping_add/sub/mul/neg`, `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`, `reverse_bits`) for all integer widths including `i128`/`u128` in `compiler/interp/interp.ax` and `compiler/opt/const_fold.ax`.

## Acceptance
- [ ] `tests/run/int128_interp/*.ax` passes under `--interp` for `i128`/`u128` checked arithmetic, overflow/divzero/shift panics, `SatAdd`/`SatSub`/`SatMul`, bit ops, and `REQ-OWNER-007` Pattern D expressions.
- [ ] `tests/opt/int128/*.ax` (`--emit=mir-opt -O1`) verifies deterministic constant folding of 128-bit and saturating operations without folding away runtime overflow panics.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T452` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T452-report.md` with exact `## Files changed`.

## Out of scope
- LIR and x86-64 native codegen for `i128`/`u128` and saturating ops (`T453`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T452/build` and `python tools/axtest.py --compiler build-snap-T452/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-12 13:07:39 started (attempt 1) T452-impl
- 2026-11-12 21:33:40 requeue: previous session died; resume from files (not charged: attempt refunded)
- 2026-11-12 21:33:50 started (attempt 1) T452-impl
- 2026-11-12 23:28:48 requeue: restart (not charged: attempt refunded)
- 2026-11-12 23:28:49 started (attempt 1) T452-impl
- 2026-11-13 16:42:03 accepted by QA -> done
