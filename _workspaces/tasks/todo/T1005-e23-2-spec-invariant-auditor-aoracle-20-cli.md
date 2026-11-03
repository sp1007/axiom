---
id: T1005
title: E23.2 Specification-to-compiler invariant auditor, AORACLE-20 stripper & axiomc audit-spec CLI
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1004]
priority: 236
status: todo
attempts: 0
paths: [compiler/conformance/spec_audit, compiler/driver/audit_spec_cmd, tests/selfhost/spec_freeze_audit]
locks: [compiler/driver/cli.ax]
spec: [spec/SPEC-141-global-contradiction-audit-spec-freeze.md, spec/RELEASE-v1.md, 0121, 0150, 0151, tasks/0604]
covers: [REQ-CNF-001, REQ-CORE-021, REQ-TOOL-003]
---
# T1005 — E23.2 Specification-to-compiler invariant auditor, AORACLE-20 stripper & axiomc audit-spec CLI

## Goal
Implement the automated specification-to-compiler contradiction auditor, `SPEC-GAP` / `UNSPECIFIED-COMPILER-BEHAVIOR` detector, production `AORACLE-20` verifier, and `axiomc audit-spec` CLI per `spec/SPEC-141-global-contradiction-audit-spec-freeze.md`.

## Scope
- Implement `SpecDependencyDB`, `ChangeImpactDB`, and the global contradiction auditor in `compiler/conformance/spec_audit`: scanning all `spec/SPEC-*.md` files, `spec/invariants.md`, and `spec/diagnostics.md` to verify that every `AXS-*` rule has a unique ID, zero conflicting semantic definitions, a compiler pass mapping, and linked conformance tests, reporting `SPEC-GAP` or `UNSPECIFIED-COMPILER-BEHAVIOR` on any unlinked rule or undocumented compiler behavior (`REQ-CNF-001`, `AEVOL-16..19`, `tasks/0604 §34-39, §67-72`).
- Implement executable `@spec_example` extraction and verification so code examples inside `spec/SPEC-*.md` compile and pass under the v1.0 compiler (`AEVOL-28`, `tasks/0604 §67-68`).
- Implement the production binary `AORACLE-20` auditor and stripper (`REQ-TOOL-003`, `0121 §309`): verifying that native release artifacts contain zero Semantic Oracle metadata or interpreter-only runtime symbols while preserving lowering semantics (`ACOMPILER-20`, `REQ-CORE-021`, `AAXIOM-001/002`).
- Expose `axiomc audit-spec` (`check|coverage|examples|impact|diff`) in `compiler/driver/audit_spec_cmd` and add selfhost tests in `tests/selfhost/spec_freeze_audit`.

## Acceptance
- [ ] Selfhost tests in `tests/selfhost/spec_freeze_audit` verify `axiomc audit-spec check`, `SPEC-GAP` / `UNSPECIFIED-COMPILER-BEHAVIOR` detection, `@spec_example` compilation, and `AORACLE-20` zero-oracle-metadata verification on native binaries.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1005-report.md` with exact `## Files changed`.

## Out of scope
- Full E23.2 QA contradiction-audit conformance suite (`T1006`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), and `T1004`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1005/build` and `python tools/axtest.py --compiler build-snap-T1005/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
