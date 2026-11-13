---
id: T481
title: Fix — native saturating_add/sub/mul wrong on every width u8..i64 (MIR SatAdd/SatSub/SatMul not lowered to LIR)
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452]
priority: 20
status: todo
attempts: 0
timeout_min: 900
paths: [tests/run/saturating_native]
locks: [compiler/lir/builder.ax, compiler/lir/lir.ax, compiler/target/x64, compiler/backend/session.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-40-integers.md, spec/SPEC-04-core-extensibility.md]
covers: [REQ-CORE-230, REQ-LIR-007, REQ-SIMD-264]
---
# T481 — Fix: native saturating arithmetic for 8..64-bit integers

## Goal
`saturating_add`, `saturating_sub`, `saturating_mul` give SPEC-40 results natively (O0 and O1) for `u8, u16, u32,
u64, usize, i8, i16, i32, i64, isize`, matching the oracle bit for bit; T453 then only adds the 128-bit case
(ADR-0042 §3).

## Scope
- Observed (T452-qa FINDING-3, identical with the pre-T452 compiler): every native saturating result is wrong, e.g.
  `0u8.saturating_sub(1u8)` prints 1, `0u8.saturating_mul(1u8)` prints 1, `1u8.saturating_add(255u8)` prints 0.
  `compiler/lir/builder.ax` maps `MIR_BINOP_WRAPPING_*` to LIR ops but has no case for `MIR_BINOP_SAT_ADD/SUB/MUL`
  (values 20..22), so they fall through to a wrong default.
- Lower `MIR_BINOP_SAT_*` per SPEC-40 / REQ-LIR-007 (saturation stays explicit until target legalisation): either an
  LIR saturating op legalised in `compiler/target/x64` (flags + `CMOVcc` to MIN/MAX, sign- or zero-extension for
  8/16-bit) or an explicit LIR expansion (wrapping op + overflow flag + select). Mul: widen or use the overflow flag of
  `IMUL`/`MUL`; signed saturation direction from the operand signs.
- Unknown MIR binop in the LIR builder becomes an internal compiler error (never a silent default); test it if the
  existing ICE test pattern allows.
- Tests `tests/run/saturating_native/*.ax`: per width, a table of edge pairs (0, 1, MAX, MAX-1, MIN, MIN+1, -1) for all
  three ops, printed; modes interp, native, native-O1, exact `// stdout:` derived from SPEC-40 (not from the
  compiler's output).
- Regenerate selfhost bundles that embed edited modules with their generators.

## Acceptance
- [ ] `tests/run/saturating_native/*` pass in all three modes; mutation: one expected value changed fails native.
- [ ] `tests/run/int128_interp/saturating.ax` interp legs still pass (128-bit native stays `native-after: T453`).
- [ ] `tests/lir`, `tests/mc`, `tests/encode`, `selfhost/lir`, `selfhost/backend` pass (baseline ids excepted).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new tests.
- [ ] Report `_workspaces/reports/T481-report.md` with exact `## Files changed`.

## Out of scope
- `i128`/`u128` (T453), std wrappers (T454), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §3; T452-qa FINDING-3)
