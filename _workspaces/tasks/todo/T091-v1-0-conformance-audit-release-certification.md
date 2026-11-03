---
id: T091
title: E23.2 Global contradiction audit, semantic freeze & v1.0 language specification (SPEC-141)
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322]
priority: 234
status: todo
attempts: 0
paths: [spec/SPEC-141-global-contradiction-audit-spec-freeze.md, spec/RELEASE-v1.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md, spec/decisions]
spec: [0150, 0151, 0121, others/0149, tasks/0602, tasks/0604]
covers: [REQ-CNF-001, REQ-CORE-021, REQ-CORE-022, REQ-TOOL-003, REQ-CAP-055, REQ-CONC-097, REQ-CORE-3137, REQ-CORE-3138]
---
# T091 — E23.2 Global contradiction audit, semantic freeze & v1.0 language specification (SPEC-141)

## Goal
Consolidate the Global Contradiction Audit, Semantic Freeze v1.0, and Language Edition / Evolution contract into `spec/SPEC-141-global-contradiction-audit-spec-freeze.md` (`AXS-FRZ-*` rule IDs) and author the canonical `spec/RELEASE-v1.md` release certification document.

## Scope
- Write `spec/SPEC-141-global-contradiction-audit-spec-freeze.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-FRZ-NNN` rules (`0121 §305-365`, `0150 §28-48`, `0151 §1-63`, `others/0149`, `tasks/0604 §1-76`).
- Audit all cross-cutting semantic axes (`Ownership ↔ Copy/Move/Drop`, `view/mut_view ↔ relocation/await/Send`, `MutexGuard ↔ await`, `Unsafe ↔ provenance/verification resumption`, `Comptime ↔ external state determinism`, `Panic/Unwind ↔ FFI/Drop`, `Capability ↔ optimization invariance`) and freeze the cross-cutting invariants `AAXIOM-001` (Semantic Stability), `AAXIOM-002` (Implementation Freedom), `AOWN-30`, `AOWN-31`, `ACAP-30`, `ACAP-31` (`REQ-CAP-055`), `AMEM-61`, `ACONC-29`, `ACONC-30`, `AASYNC-30`, `ACOMPILER-20` (`REQ-CORE-021`, `REQ-CORE-022`), `AORACLE-20` (`REQ-TOOL-003`), `AUNSAFE-56/57`, `ACOMP-24/25`, `AFERR-44/45`, and `REQ-CONC-097`.
- Specify the separation of `Language Version`, `Compiler Version`, `Language Edition`, `Standard Library Version`, `ABI Version`, `Package Version`, and `Target Version` (`AEVOL-01..30`, `REQ-CORE-3137`, `REQ-CORE-3138`), `@language("1.0")` / `edition = "1.0"`, deprecation lifecycle (`Active` → `Deprecated` → `MigrationRecommended` → `RemovalScheduled` → `Removed`), and `std.hint.black_box<T>` (`0151 §56`).
- Write `spec/RELEASE-v1.md` starting with a Vietnamese `## Tóm tắt` section, recording the global contradiction audit ledger (`REQ-CNF-001`), the frozen v1.0 feature and ABI boundary, and the v1.0 release notes.
- Update `spec/INDEX.md`, `spec/diagnostics.md` (registering `AX_FRZ_*` and `AX_DEPR_*` diagnostic codes), and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-141-global-contradiction-audit-spec-freeze.md` and `spec/RELEASE-v1.md` exist with Vietnamese `## Tóm tắt` sections, numbered `AXS-FRZ-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and complete contradiction-audit tables.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T091-report.md` with exact `## Files changed`.

## Out of scope
- Compiler and stdlib implementation of frozen boundary verifiers, `@language("1.0")`, `std.hint.black_box`, and `axiomc audit-spec` (`T1004`–`T1005`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Roadmap epic E23.2 (`P23-v1-0-conformance-freeze-releas`), depends on `T223` and all P11–P22 phase gates (`T311`–`T322`).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T091/build` and `python tools/axtest.py --compiler build-snap-T091/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-10-06 02:23:55 covers += REQ-CNF-001 (metadata only)
- 2026-11-03 11:15:00 refined by T223 (fixed phase slug to P23-v1-0-conformance-freeze-releas, added P11-P22 gate dependencies T311-T322, scoped SPEC-141 + RELEASE-v1.md, expanded covers)
