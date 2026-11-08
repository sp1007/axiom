---
id: T864
title: E20.4 Dependency capability-escalation auditor, Ed25519 package/toolchain signature verifier, provenance attestation & axiomc trust CLI
phase: P20-build-system-package-ecosystem
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T859, T862, T863]
priority: 214
status: todo
attempts: 0
paths: [std/pkg/trust, compiler/driver/trust_cmd, tests/run/pkg_supply_chain]
spec: [spec/SPEC-113-hermetic-builds-supply-chain-trust.md, tasks/0590, tasks/0449, tasks/0772, tasks/1065]
covers: [REQ-PKG-022, REQ-PKG-024]
---
# T864 — E20.4 Dependency capability-escalation auditor, Ed25519 package/toolchain signature verifier, provenance attestation & axiomc trust CLI

## Goal
Implement the transitive dependency capability-escalation auditor, Ed25519 package and toolchain signature verifier, SLSA-style build provenance attestation emitter, and `axiomc trust|audit` CLI per `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`.

## Scope
- Implement `std/pkg/trust` verifying Ed25519 signatures on `.axpkg` archives and toolchain bundles (`tasks/0590 §21-24`, `tasks/0772 §550.8-10`), auditing the dependency trust graph against workspace `[trust.policy]` capability grants (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`; `tasks/0449 §8-11`), and generating signed/content-addressed provenance attestation manifests (`tasks/0590 §20`, `tasks/0772 §550.5, 12`).
- Implement `compiler/driver/trust_cmd` providing `axiomc trust keygen|sign|verify`, `axiomc audit` (capability escalation and unverified dependency check), and `axiomc provenance` CLI subcommands (`REQ-PKG-022`, `REQ-PKG-024`).
- Add run tests in `tests/run/pkg_supply_chain`.

## Acceptance
- [ ] Run tests in `tests/run/pkg_supply_chain` verify Ed25519 package signing and tamper rejection, capability-escalation detection when a transitive package uses undeclared `unsafe`/`ffi`, and provenance attestation generation in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T864-report.md` with exact `## Files changed`.

## Out of scope
- ABI compatibility diffing (`T866`–`T869`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T864/build` and `python tools/axtest.py --compiler build-snap-T864/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
