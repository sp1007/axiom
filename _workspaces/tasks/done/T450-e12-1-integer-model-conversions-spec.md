---
id: T450
title: E12.1 — Canonical integer model, 128-bit arithmetic & conversion specification (SPEC-40)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T212]
priority: 140
status: done
attempts: 1
paths: [spec/SPEC-40-integers.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-03-core-semantics.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, 0157, 0175, 0245, tasks/0327, tasks/0334, tasks/0431]
covers: [REQ-OWNER-007, REQ-SIMD-085, REQ-SIMD-101, REQ-SIMD-102, REQ-SIMD-103, REQ-SIMD-104, REQ-SIMD-105, REQ-SIMD-106, REQ-SIMD-156]
started: 2026-11-03 07:13:34
finished: 2026-11-03 07:37:21
---
# T450 — E12.1 — Canonical integer model, 128-bit arithmetic & conversion specification (SPEC-40)

## Goal
Consolidate the full integer arithmetic, 128-bit width (`i128`/`u128`), bit manipulation, conversion taxonomy (`COERCION`, `CAST`, `TRY_CAST`, `BITCAST`), and multi-width integer expression promotion rules (`REQ-OWNER-007` integer sub-lattice) into canonical `spec/SPEC-40-integers.md` (`AXS-INT-*` rule IDs).

## Scope
- Write `spec/SPEC-40-integers.md` starting with a Vietnamese `## Tóm tắt` section and stable `AXS-INT-NNN` rules.
- Specify 128-bit signed and unsigned integer types (`i128`, `u128`: size 16, alignment 16, two's-complement representation, literal suffixes `i128`/`u128`, range checks `-2^127..=2^127-1` and `0..=2^128-1`, Windows x64 ABI passing, and LIR register-pair lowering contract per `SPEC-04 AXS-EXT-020/024/050`).
- Specify the complete arithmetic families across all 12 integer widths (`i8..i128`, `u8..u128`, `isize`, `usize`): default checked operators (`+`, `-`, `*`, `/`, `%`, unary `-`), `wrapping_*`, `saturating_*` (`MIR_RVALUE_BINARY_OP` `SatAdd`/`SatSub`/`SatMul`), `checked_*` returning `Option<T>`, and `overflowing_*` returning `(T, bool)`.
- Specify the complete bit-operation and endian conversion suite (`swap_bytes`, `reverse_bits`, `leading_zeros`, `trailing_zeros`, `leading_ones`, `trailing_ones`, `count_ones`, `count_zeros`, `rotate_left`, `rotate_right`, `is_power_of_two`, `next_power_of_two`, `to_le_bytes`, `from_le_bytes`, `to_be_bytes`, `from_be_bytes`, `to_ne_bytes`, `from_ne_bytes`).
- Specify the four conversion classes (`tasks/0431 §172.1-14`): lossless `From`/`Into`, fallible `TryFrom`/`TryInto` (`TryFromIntError`), explicit `as` cast (`CAST`), and bit-preserving `BITCAST` (`ANUM-41, 91`).
- Specify the pure-integer portion of the `REQ-OWNER-007` deterministic numeric promotion lattice (`i8/u8 -> i16/u16 -> i32/u32 -> i64/isize` and unsuffixed `IntVar` literal unification across nested arithmetic, bitwise/shift, array-index, and comparison expressions), enforcing the architectural invariant that all promotions happen exclusively in `typeck` + HIR->MIR lowering (`MIR_RVALUE_CAST`) so MIR/LIR/x64 instructions remain 100% homogeneous.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and cross-reference `spec/SPEC-03-core-semantics.md`.

## Acceptance
- [ ] `spec/SPEC-40-integers.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-INT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated consistently with `SPEC-40`.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T450-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or standard library implementation (handled by `T451`–`T454`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T450/build` and `python tools/axtest.py --compiler build-snap-T450/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 07:13:34 started (attempt 1) 
- 2026-11-03 07:37:21 accepted by QA -> done
