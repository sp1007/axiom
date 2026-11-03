---
id: T1004
title: E23.2 Frozen semantic boundary verifier, @language("1.0") edition guard & black_box intrinsic
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T091]
priority: 235
status: todo
attempts: 0
paths: [compiler/semantics/freeze_audit, compiler/hir/language_edition, std/hint, tests/ui/semantic_freeze]
locks: [compiler/semantics/typeck.ax, compiler/mir/verifier.ax, compiler/opt/pipeline.ax, compiler/diag/codes.ax]
spec: [spec/SPEC-141-global-contradiction-audit-spec-freeze.md, spec/RELEASE-v1.md, 0121, 0150, 0151, tasks/0604]
covers: [REQ-CNF-001, REQ-CORE-021, REQ-CORE-022, REQ-CAP-055, REQ-CONC-097, REQ-CORE-3137, REQ-CORE-3138]
---
# T1004 — E23.2 Frozen semantic boundary verifier, @language("1.0") edition guard & black_box intrinsic

## Goal
Implement the frozen v1.0 semantic boundary verifier, `@language("1.0")` / `edition = "1.0"` compatibility & deprecation engine, and `std.hint.black_box<T>` intrinsic per `spec/SPEC-141-global-contradiction-audit-spec-freeze.md`.

## Scope
- Implement `@language("1.0")`, `axiom.toml` `edition = "1.0"`, and distinct version identity tracking (`Language Version`, `Compiler Version`, `Language Edition`, `Standard Library Version`, `ABI Version`, `Package Version`, `Target Version`) in `compiler/hir/language_edition` (`AEVOL-01..30`, `REQ-CORE-3137`, `REQ-CORE-3138`, `0150 §28-38`, `tasks/0604 §1-27`).
- Implement `@deprecated(since = "...", replacement = "...", removal = "...")` machine-readable metadata and `AX_DEPR_*` warnings with replacement hints, plus `@feature("...")` experimental feature gating that prevents experimental features from altering frozen v1.0 Core semantics (`0150 §31`, `tasks/0602 §56`, `tasks/0604 §12-15, §26-30`).
- Implement the cross-axis contradiction-audit verifier in `compiler/semantics/freeze_audit`: enforcing `ACAP-31` (capability validity is strictly independent of optimization level; `REQ-CAP-055`, `0151 §5`), `AUNSAFE-56/57` (full ownership and capability verification immediately resumes after exiting an `unsafe` block; `0151 §56`), `ACOMP-24/25` (comptime determinism and rejection of undeclared external state; `0151 §56`), `AOWN-30/31`, `ACAP-30`, `ACONC-29/30`, `AASYNC-30`, `REQ-CONC-097`, and `ACOMPILER-20` (preserving semantics across lowering phases and rejecting ambiguous semantics with `AX_FRZ_*` diagnostics; `REQ-CORE-021`, `REQ-CORE-022`, `REQ-CNF-001`).
- Implement `std.hint.black_box<T>(x: T) -> T` in `std/hint` and lower it across MIR, OptIR, LIR, and the Oracle interpreter as an opaque value-and-provenance barrier that prevents dead-code/constant folding without bypassing ownership or capability verification (`0151 §56`).
- Add positive and negative UI diagnostic tests in `tests/ui/semantic_freeze`.

## Acceptance
- [ ] UI and run tests in `tests/ui/semantic_freeze` verify `@language("1.0")` / `edition` enforcement, `@deprecated` diagnostics, `@feature` isolation, `ACAP-31` optimization-level invariance, `AUNSAFE-56/57` post-unsafe verification resumption, and `std.hint.black_box<T>`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1004-report.md` with exact `## Files changed`.

## Out of scope
- Specification-to-compiler invariant auditor and `axiomc audit-spec` CLI (`T1005`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), and `T091`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1004/build` and `python tools/axtest.py --compiler build-snap-T1004/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
