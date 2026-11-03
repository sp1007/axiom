---
id: T456
title: E12.2 — Canonical IEEE-754 floating-point, mixed-type promotion lattice & math specification (SPEC-41)
phase: P12-numeric-floating-point-simd
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T450]
priority: 146
status: done
attempts: 1
paths: [spec/SPEC-41-floating-point.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/SPEC-03-core-semantics.md]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md, spec/requirements/OWNER.md, tasks/0331, tasks/0338, tasks/0345, tasks/0427, tasks/0431, tasks/0469]
covers: [REQ-OWNER-007, REQ-SIMD-108, REQ-SIMD-109, REQ-SIMD-110, REQ-SIMD-163, REQ-SIMD-186, REQ-SIMD-187, REQ-SIMD-188, REQ-SIMD-189]
started: 2026-11-03 07:51:56
finished: 2026-11-03 08:25:20
---
# T456 — E12.2 — Canonical IEEE-754 floating-point, mixed-type promotion lattice & math specification (SPEC-41)

## Goal
Specify canonical `spec/SPEC-41-floating-point.md` (`AXS-FLT-*`), defining `f32`/`f64` IEEE-754 semantics, the complete `REQ-OWNER-007` Complex Mixed-Type Expression Matrix promotion lattice and homogeneous `MIR_RVALUE_CAST` lowering contract, Windows x64 XMM ABI rules, float formatting/parsing, and the `std.math` accuracy contract.

## Scope
- Write `spec/SPEC-41-floating-point.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-FLT-NNN` rules.
- Specify `f32` (IEEE-754 binary32, size 4, align 4) and `f64` (IEEE-754 binary64, size 8, align 8), float literals (`1.5`, `1e-5`, `2.5f32`, `3.0f64`, unsuffixed `FloatVar` defaulting to `f64`), strict IEEE-754 default arithmetic (`+`, `-`, `*`, `/`, `%`, unary `-` with round-to-nearest-even), quiet `NaN` propagation, signed zero (`-0.0 == +0.0`, `1.0 / -0.0 == -inf`), and prohibition of implicit fast-math reassociation or uncontracted FMA (`ANUM-43..45, 98`, `ASIMD-40..43`).
- Specify IEEE-754 partial comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=` returning `false` on `NaN` except `!=`) alongside total ordering (`total_cmp`), saturating `FloatToInt` `as` casts (`NaN -> 0`, clamping beyond `[MIN, MAX]`), `IntToFloat` round-to-nearest-even casts, and `to_bits`/`from_bits` bitcasts.
- Specify the full **`REQ-OWNER-007` Complex Mixed-Type Expression Matrix** architectural rule: (1) deterministic numeric promotion lattice (`IntVar` / `FloatVar` literal unification and variable promotions `i8/u8 -> i16/u16 -> i32/u32 -> i64/isize -> f32 -> f64`) across nested arithmetic, bitwise/shift, unary, array-index (`idx + off` coerced to `usize`), call/intrinsic arguments, and relational comparisons; (2) all promotions are resolved exclusively in `typeck` + HIR->MIR lowering and emitted as explicit `MIR_RVALUE_CAST` temporaries before the binary/indexing/comparison operation so MIR, MIR verifier, MIR interpreter, optimizer, LIR, and x86-64 codegen see 100% homogeneous operand types on every instruction (never mixing GPR and XMM or narrow/wide widths in backend isel); (3) normative Patterns A, B, C, and D.
- Specify Windows x64 ABI floating-point rules (`XMM0`–`XMM3` parameter passing, `XMM0` return, `XMM6`–`XMM15` callee-saved 128-bit preservation), shortest round-trip formatting & exact parsing, and the `std.math` ULP accuracy and special-value contract.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and `spec/SPEC-03-core-semantics.md`.

## Acceptance
- [ ] `spec/SPEC-41-floating-point.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-FLT-NNN` rules, complete `REQ-OWNER-007` lattice & Patterns A–D, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`, and `spec/SPEC-03-core-semantics.md` are updated consistently.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T456-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and library implementation (`T457`–`T461`).
- Editing `docs/` or `bootstrap/axiom0/`.

## Notes
- Phase P12 (`P12-numeric-floating-point-simd`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T456/build` and `python tools/axtest.py --compiler build-snap-T456/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:30:00 created by T212 (P12 phase planning)
- 2026-11-03 07:51:56 started (attempt 1) 
- 2026-11-03 08:25:20 accepted by QA -> done
