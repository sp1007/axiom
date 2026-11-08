---
id: T865
title: E20.4 Hermetic build sandbox, cross-directory/cross-machine bit-for-bit reproducibility & supply-chain trust conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T864]
priority: 215
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_4_hermetic_supply_chain]
spec: [spec/SPEC-113-hermetic-builds-supply-chain-trust.md, tasks/0590, tasks/0449, tasks/0772, tasks/0661, tasks/1065]
covers: [REQ-PKG-022, REQ-PKG-024]
---
# T865 — E20.4 Hermetic build sandbox, cross-directory/cross-machine bit-for-bit reproducibility & supply-chain trust conformance suite

## Goal
Certify E20.4 exit criteria with an end-to-end conformance suite covering hermetic build sandboxing, bit-for-bit reproducibility across distinct host environments/directories, Ed25519 package signing, provenance attestations, and dependency capability-escalation enforcement.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_4_hermetic_supply_chain` verifying:
  - bit-for-bit identical executables, libraries, `.axmeta`, and `.axpkg` outputs when building a multi-package workspace under two distinct filesystem paths, environment variable sets, locales, and worker counts (`REQ-PKG-022`, `REQ-PKG-024`, `tasks/0590 §17-19`);
  - hermetic sandbox blocking of filesystem escape, ambient env access, and network access during build;
  - dependency capability-escalation rejection (`axiomc audit`) when a dependency attempts `unsafe` or `ffi` without workspace trust grant (`tasks/0449 §8-11`);
  - Ed25519 signature verification, tampered archive rejection, and provenance attestation round-trip (`tasks/0772 §550.8-18`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_4_hermetic_supply_chain` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T865-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T865/build` and `python tools/axtest.py --compiler build-snap-T865/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
