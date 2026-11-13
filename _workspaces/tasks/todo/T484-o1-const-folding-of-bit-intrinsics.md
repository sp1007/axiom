---
id: T484
title: E12.1 — -O1 constant folding of bit intrinsics (rotate, clz, ctz, popcount, bswap, reverse_bits, wrapping_neg) incl. 128-bit
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 145
status: todo
attempts: 0
timeout_min: 600
paths: [tests/opt/bit_intrinsics_fold]
locks: [compiler/opt, compiler/mir/builder.ax, compiler/mir/mir.ax, compiler/interp, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-40-integers.md]
covers: [REQ-SIMD-177, REQ-SIMD-265]
---
# T484 — -O1 folding of bit intrinsics

## Goal
At `-O1`, a bit intrinsic whose operands are constants folds to one constant (T452 Scope bullet 3, not delivered:
T452-qa FINDING-2; ADR-0042 §4), with results identical to the oracle.

## Scope
- Today the MIR builder expands `rotate_left/right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`,
  `reverse_bits`, `wrapping_neg` into shift/mask sequences over temporaries (`inspect --emit=mir-opt -O1` of
  `1u128.reverse_bits()` leaves ~40 statements) and -O1 does not propagate constants through locals.
- Choose one (record the choice): (a) the MIR builder emits a single intrinsic rvalue that the folder evaluates (with
  the oracle's `u128_*_raw` helpers) and the LIR builder expands; or (b) local constant propagation before the fold
  pass. (a) is preferred if it keeps MIR smaller; it then needs LIR lowering of the new node (native results must
  stay identical).
- Tests `tests/opt/bit_intrinsics_fold/*` (`mir-opt -O1` shows one constant per intrinsic, all widths 8..128; run
  results equal across interp O0, interp -O1, native O0/O1 with exact `// stdout:`).
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] Each intrinsic with constant operands folds at -O1 (golden MIR) and gives the oracle's value.
- [ ] `tests/opt`, `tests/run/intrinsics`, `tests/run/int128_interp` (interp legs) pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new run tests.
- [ ] Report `_workspaces/reports/T484-report.md` with exact `## Files changed`.

## Out of scope
- 128-bit native codegen (T453), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §4; T452-qa FINDING-2)
