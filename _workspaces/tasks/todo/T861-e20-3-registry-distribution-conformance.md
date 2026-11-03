---
id: T861
title: E20.3 Package registry protocol, .axpkg deterministic archive, offline mirror & binary/interface distribution conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T316, T318, T860]
priority: 211
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_3_registry_distribution]
spec: [spec/SPEC-112-package-registry-distribution.md, tasks/0412, tasks/0665, tasks/0739, tasks/0858, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-024]
---
# T861 — E20.3 Package registry protocol, .axpkg deterministic archive, offline mirror & binary/interface distribution conformance suite

## Goal
Certify E20.3 exit criteria with an end-to-end conformance suite covering `.axpkg` deterministic packaging, local/sparse registry protocols, offline mirrors, multi-repository namespace pinning, and precompiled `.axmeta` binary package distribution.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_3_registry_distribution` verifying:
  - end-to-end `axiomc pkg publish` → sparse registry index update → `axiomc pkg fetch` → workspace build (`REQ-ECO-8736`, `REQ-PKG-024`);
  - immutable package version enforcement and SHA-256 Merkle tampering detection (`tasks/0858 §15-17`);
  - offline repository mirroring (`axiomc pkg mirror`) and air-gapped workspace resolution from a local mirror (`tasks/0858 §9-10`);
  - precompiled `.axmeta` + binary package consumption and multi-repository dependency-confusion prevention;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_3_registry_distribution` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T861-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T861/build` and `python tools/axtest.py --compiler build-snap-T861/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
