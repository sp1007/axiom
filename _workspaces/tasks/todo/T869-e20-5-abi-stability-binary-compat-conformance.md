---
id: T869
title: E20.5 ABI stability tiers, versioned symbol exports, .axmeta binary compatibility & axiomc abi-check conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T316, T318, T868]
priority: 219
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_5_abi_stability_compat]
spec: [spec/SPEC-114-abi-stability-versioning-binary-compat.md, 0104, tasks/0452, tasks/0583, tasks/0739]
covers: [REQ-ECO-8734, REQ-PKG-022, REQ-PKG-024]
---
# T869 — E20.5 ABI stability tiers, versioned symbol exports, .axmeta binary compatibility & axiomc abi-check conformance suite

## Goal
Certify E20.5 exit criteria with an end-to-end conformance suite covering Axiom's three ABI tiers, `@abi(stable)` layout/type contracts, opaque handle evolution, versioned symbol exports, and `axiomc abi-check` SemVer verification.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_5_abi_stability_compat` verifying:
  - `@abi(stable, version = "1.0")` shared library consumption across independent compilations and private field changes behind `@opaque` handles without recompiling downstream consumers (`0104 §11-12`, `tasks/0452 §193.16-17`);
  - compile-time rejection of non-stable types (`Closure`, unrepr'd generics) on `@abi(stable)` exports (`REQ-ECO-8734`);
  - `ApiFingerprint`, `SemanticFingerprint`, and `AbiFingerprint` separation (`tasks/0583 §324.2`, `tasks/0739 §493.21-23`);
  - `axiomc abi-check` SemVer compliance matrix (minor additive passes, silent breaking layout/signature/ownership changes rejected; `REQ-PKG-022`, `REQ-PKG-024`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_5_abi_stability_compat` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T869-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T869/build` and `python tools/axtest.py --compiler build-snap-T869/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
