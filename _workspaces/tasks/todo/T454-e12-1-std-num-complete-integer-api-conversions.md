---
id: T454
title: E12.1 — std.core.num complete integer API, fallible TryFrom/TryInto & endian byte conversions
phase: P12-numeric-floating-point-simd
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452, T453]
priority: 144
status: todo
attempts: 0
paths: [std/core/num.ax, std/core/convert.ax, std/text/fmt/int.ax, tests/std/num]
locks: [std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-40-integers.md, tasks/0327, tasks/0334, tasks/0431]
covers: [REQ-SIMD-211, REQ-SIMD-241, REQ-SIMD-242]
---
# T454 — E12.1 — std.core.num complete integer API, fallible TryFrom/TryInto & endian byte conversions

## Goal
Complete `std/core/num.ax`, `std/core/convert.ax`, and `std/text/fmt/int.ax` across all 12 integer types (`i8..i128`, `u8..u128`, `isize`, `usize`) with checked/wrapping/saturating/overflowing families, bit operations, endian byte arrays, and `From`/`TryFrom` conversions.

## Scope
- Extend `std/core/num.ax` for `i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize` with associated constants (`MIN`, `MAX`, `BITS`) and complete method families: `checked_add/sub/mul/div/rem/neg/shl/shr/abs/pow`, `saturating_add/sub/mul/neg/abs/pow`, `wrapping_add/sub/mul/div/rem/neg/shl/shr/abs/pow`, and `overflowing_add/sub/mul/neg/shl/shr`.
- Add bit manipulation and endian byte conversion methods on all 12 integer types: `swap_bytes`, `reverse_bits`, `leading_zeros`, `trailing_zeros`, `leading_ones`, `trailing_ones`, `count_ones`, `count_zeros`, `rotate_left`, `rotate_right`, `is_power_of_two`, `next_power_of_two`, `to_le_bytes`, `from_le_bytes`, `to_be_bytes`, `from_be_bytes`, `to_ne_bytes`, `from_ne_bytes`.
- Create `std/core/convert.ax` with `From<T>`, `Into<T>`, `TryFrom<T>`, `TryInto<T>`, and `TryFromIntError`, implementing lossless widening `From` and range-checked fallible `TryFrom` across integer pairs (`tasks/0431 §172.5-8`).
- Extend `std/text/fmt/int.ax` to format and parse `i128` and `u128` in decimal, hexadecimal (`0x`), binary (`0b`), and octal (`0o`).

## Acceptance
- [ ] `tests/std/num/*.ax` passes under both `--interp` and native x86-64 (`WEAK-NATIVE 0`) for all 12 integer widths, covering `checked_*`, `saturating_*`, `wrapping_*`, `overflowing_*`, bit ops, endian byte arrays, `From`/`TryFrom`, and `i128`/`u128` string formatting/parsing.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T454` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T454-report.md` with exact `## Files changed`.

## Out of scope
- Floating-point formatting/parsing (`T460`).

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T454/build` and `python tools/axtest.py --compiler build-snap-T454/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
