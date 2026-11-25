---
id: T461b
title: Typeck — method call on an unsuffixed numeric literal (`1.0.exp()`, `1.max(2)`) defaults the receiver first (ADR-0051)
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 80
status: todo
attempts: 0
timeout_min: 180
paths: [tests/run/numeric_literal_receiver, tests/ui/numeric_literal_receiver]
locks: [compiler/types/typeck.ax]
spec: [spec/decisions/ADR-0051-numeric-literal-method-receiver.md, spec/SPEC-41-floating-point.md, spec/SPEC-01-lexical.md]
covers: [REQ-TYP-123, REQ-EXP-009]
---
# T461b — Literal method receivers

## Why
`_workspaces/reports/T461-qa.md` N5: `1.0.exp()` is rejected with `AX_TYPE_UNKNOWN_FIELD` while `let x = 1.0; x.exp()`
works. The lexer is correct (SPEC-01 AXS-LEX-056); typeck looks the method up while the receiver type is still a
`FloatVar`. ADR-0051 / SPEC-41 AXS-FLT-003 item 2 ("Literal method receivers"): default the receiver (`f64` / `i32`)
at lookup time.

## Scope
1. In `compiler/types/typeck.ax`, at method-call, field-access and associated-item lookup on a receiver whose type is an
   unconstrained `FloatVar` / `IntVar`, unify it with `f64` / `i32` first. Nothing else changes (no backward inference
   from argument types).
2. Tests (`modes: interp native`, exact `// stdout:`) in `tests/run/numeric_literal_receiver/`: `1.0.exp()`,
   `2.0.sqrt()`, `(-1.5).abs()`, `0.5.to_bits()` printed as bits, `1.max(2)`, `-3.abs()` per SPEC-03 precedence (show
   what it parses as), a receiver already constrained by context (`let y: f32 = 2.0; (1.0 + y).sqrt()` is `f32`).
   Compile-fail in `tests/ui/numeric_literal_receiver/`: `1.max(2i64)` -> `AX_TYPE_MISMATCH`.

## Acceptance
- [ ] New tests pass in interp, native and native-O1, WEAK-NATIVE 0; the run cases fail on HEAD.
- [ ] `tests/typeck/**`, `tests/ui/**`, `tests/std/float*/**`, `tests/std/math/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/types`. Report `_workspaces/reports/T461b-report.md` with an
      exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T461-qa.md N5; ADR-0051)
