---
id: T877
title: E20.6 Native SDK/sysroot, AXTOOLCHAIN distribution & two-machine lockfile reproducible multi-package workspace conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T865, T876]
priority: 227
status: todo
attempts: 0
paths: [tests/conformance/p20/e20_6_sdk_toolchain_workspace]
spec: [spec/SPEC-116-sdk-sysroot-toolchain-distribution.md, spec/SPEC-110-build-graph-driver.md, spec/SPEC-111-package-manager-resolution-lockfiles.md, spec/SPEC-113-hermetic-builds-supply-chain-trust.md, tasks/0605, tasks/1034, tasks/0661, tasks/0858]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T877 — E20.6 Native SDK/sysroot, AXTOOLCHAIN distribution & two-machine lockfile reproducible multi-package workspace conformance suite

## Goal
Certify E20.6 and the Phase P20 overall exit criterion (`multi-package workspace builds reproducibly from lockfile on two machines`) with an end-to-end conformance suite covering declarative `.axsdk` sysroots, `AXTOOLCHAIN` bundles, and cross-environment reproducible workspace builds from `axiom.lock`.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_6_sdk_toolchain_workspace` verifying:
  - C-free cross-target compilation using declarative `.axsdk` sysroot bundles (`x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `wasm32`) pinned by `SdkFingerprint` in `axiom.lock` (`tasks/0605`, `tasks/1034`, `REQ-ECO-8736`);
  - Phase P20 exit criterion (`ROADMAP.md` §3): building a multi-package workspace (containing library, binary, precompiled `.axmeta`, and dynamic plugin packages) from `axiom.lock` + offline registry mirror inside two completely isolated simulated machine environments (distinct root paths, usernames, temp dirs, environment variables, clock offsets, and thread counts) produces bit-for-bit identical output artifacts (`REQ-PKG-022`);
  - rejection of tampered `axiom.lock` package hashes or mismatched `SdkFingerprint` / `ToolchainFingerprint`;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_6_sdk_toolchain_workspace` pass in `--interp` and native modes with `0 WEAK-NATIVE`, demonstrating bit-for-bit identical multi-package workspace builds from `axiom.lock` across two isolated machine environments.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T877-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated phases; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T877/build` and `python tools/axtest.py --compiler build-snap-T877/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
