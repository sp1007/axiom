---
id: T499d
title: E12.2 follow-up — @thread_local float initializer expressions & float constants with fieldless enums
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: []
priority: 160
status: todo
attempts: 0
paths: [tests/run/float_const_tls, tests/ui/float_const_tls]
locks: [compiler/types/typeck.ax, compiler/interp_opt/session.ax, compiler/backend/session.ax, spec/SPEC-41-floating-point.md]
spec: [spec/SPEC-41-floating-point.md, spec/SPEC-04-core-extensibility.md]
covers: [REQ-OWNER-007, REQ-CORE-2278]
---
# T499d — Float TLS initializer expressions & fieldless-enum float constants

## Why
T458b follow-ups (`_workspaces/reports/T458b-qa.md` "Follow-ups", `T458b-report.md` D1/D2):
- D2: a `@thread_local` float initializer must be a literal or a negated literal, because TLS initial values are
  folded in typeck, which has no soft-float. `@thread_local static X: f64 = 0.5 * 2.0;` is
  `AX_TYPE_INVALID_TLS_DECL`, while the same initializer on a plain `static`/`const` is accepted. This is an
  inconsistency in the const-initialisation rule, recorded as temporary in SPEC-41 §1 item 4.
- D1 coverage gap: "floats inside enums" holds only with fieldless enums, and no test pins a float constant used
  together with a fieldless enum (e.g. a `const` struct with an `f32` field and a fieldless enum field, a `match` on
  a fieldless enum constant selecting float constants). Payload-enum constants are a general feature, moved to T552.

## Scope
1. Evaluate `@thread_local` initializers that contain float arithmetic through the same constant-evaluation path
   T458b uses for `static`/`const` (session evaluation with the IEEE-754 evaluator, or deferral via the MIR operand
   marker), so any initializer valid for a `static` of the same type is valid for a `@thread_local`. Bits must be
   identical in `--interp` and native (`-O0`, `-O1`).
2. Tests: `tests/run/float_const_tls/` (scalar and aggregate TLS with `0.5 * 2.0`, `-(1.0 / 3.0)`, `f32` rounding
   case, a TLS initializer referencing a float `const`, run-time write then read; exact stdout of `to_bits`), and
   fieldless-enum + float constant cases; `tests/ui/float_const_tls/` for what stays rejected (non-constant
   initializer, e.g. a function call → `AX_TYPE_INVALID_TLS_DECL`).
3. SPEC-41 §1 item 4: replace the temporary "`@thread_local` float initializers" bullet with the final rule (same
   constant-initializer rule as `static`).

## Acceptance
- [ ] New run tests pass in `--interp`, native `-O0` and `-O1` with exact stdout (`WEAK-NATIVE` 0).
- [ ] New UI tests pass; existing `tests/run/float_const`, `tests/ui/float_const`, TLS tests unchanged and passing.
- [ ] SPEC-41 bullet updated.
- [ ] Normal gate (selfhost groups of touched compiler modules included). Report `_workspaces/reports/T499d-report.md`
      with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T427/T458b accept, `_workspaces/reports/triage-2026-11-25-T427.md`)
