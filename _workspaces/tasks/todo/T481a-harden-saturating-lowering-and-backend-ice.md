---
id: T481a
title: Follow-up T481 — explicit narrow-operand extension in saturating lowering, ICE diagnostic on the .mir emit path, readable ICE message
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T481]
priority: 20
status: todo
attempts: 0
timeout_min: 300
paths: [tests/run/saturating_native, tests/ui/backend_ice]
locks: [compiler/lir/builder.ax, compiler/lir/lir.ax, compiler/target/x64, compiler/backend/session.ax, compiler/driver/pipeline.ax, tests/selfhost]
spec: [spec/SPEC-40-integers.md, spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md]
covers: [REQ-LIR-007]
---
# T481a — Follow-up T481: harden saturating lowering and backend ICE reporting

## Goal
Remove three weak spots left by T481 (owner review 2026-11-17) before later work builds on them. No behaviour
change for correct programs; native saturating results stay bit-identical to the oracle.

## Scope
1. **Narrow operand cleanup must not depend on an identity op.** `lower_sat_operand` in `compiler/lir/builder.ax`
   emits `LIR_INST_BIT_OR(raw, 0)` at a narrow type only so that isel truncates and re-extends the register. Any
   future LIR simplification `x | 0 → x` would silently bring back dirty upper bits for
   `u8/u16/u32/i8/i16/i32`. Replace it with the explicit sign/zero extension the backend already uses for integer
   casts (reuse the existing cast lowering path; add an LIR extension op only if no explicit form exists, and then
   lower it in `compiler/target/x64`). Leave a comment stating the invariant (operands of the overflow ops are
   canonical 64-bit sign/zero-extended values).
2. **ICE on the `.mir` emit path.** `session_emit_mc_mir_text_opt` (`compiler/backend/session.ax`, used by
   `axiomc --emit=mc <file>.mir`, `compiler/driver/pipeline.ax`) returns `false` on a lowering/verify failure
   without any diagnostic, while the HIR paths now report `AX_ICE_INTERNAL`. Report `AX_ICE_INTERNAL` there too
   (span of the function if available, otherwise `span_none`), so every backend lowering failure gives a message.
3. **Readable ICE message.** `BACKEND_ICE_MSG` is a hand-written byte array; build the message the way other
   diagnostics in `compiler/` build string literals (string literal / existing helper), same text
   `internal compiler error`.

## Acceptance
- `tests/run/saturating_native/*` still pass in interp, native, native-O1 (`WEAK-NATIVE 0`); add one test where
  every narrow width gets its operands from a narrowing cast of a value with dirty upper bits **and** from a
  function parameter / struct field load (not only locals), for all three ops.
- Demonstrate item 1: show (in the report) the LIR for a narrow `saturating_add` before/after — no `BIT_OR … 0`
  remains, an explicit extension is present.
- A UI test under `tests/ui/backend_ice/` (or the existing ICE test pattern) shows `--emit=mc` on a `.mir` input
  that the backend cannot lower prints `AX_ICE_INTERNAL` and exits non-zero; if no such input can be constructed
  without a test hook, cover it with a selfhost unit test instead and say so.
- Regenerate affected selfhost bundles (`gen_*.py --check` clean); task gate per `axiom-qa.md`.
