---
id: T876
title: E20.6 Hermetic multi-target SDK/sysroot & toolchain archive packager, axiom.lock SDK pinning & axiomc sdk/toolchain CLI
phase: P20-build-system-package-ecosystem
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T316, T318, T856, T874, T875]
priority: 226
status: todo
attempts: 0
paths: [std/sdk/bundle, compiler/driver/sdk_cmd, tests/run/sdk_toolchain_cli]
spec: [spec/SPEC-116-sdk-sysroot-toolchain-distribution.md, tasks/0605, tasks/1034, tasks/0661, tasks/0858]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T876 — E20.6 Hermetic multi-target SDK/sysroot & toolchain archive packager, axiom.lock SDK pinning & axiomc sdk/toolchain CLI

## Goal
Implement the hermetic multi-target SDK/sysroot and `AXTOOLCHAIN` bundle packager/installer, `axiom.lock` SDK fingerprint pinning, and `axiomc sdk` / `axiomc toolchain` CLI commands per `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md`.

## Scope
- Implement `std/sdk/bundle` packaging, verifying, and installing deterministic `.axsdk` and `.axtoolchain` distribution archives (containing target `std` `.axmeta`/`.lib`/`.a`, platform import stubs, target descriptors, and SHA-256 Merkle manifests; `tasks/0605 §4-5, 18-21`, `tasks/1034 §4-7`) and binding `SdkFingerprint` / `ToolchainFingerprint` entries in `axiom.lock` (`REQ-PKG-022`, `REQ-ECO-8736`).
- Implement `compiler/driver/sdk_cmd` providing `axiomc sdk list|install|verify|pack|pin` and `axiomc toolchain list|info|verify|pack` CLI commands.
- Add run tests in `tests/run/sdk_toolchain_cli`.

## Acceptance
- [ ] Run tests in `tests/run/sdk_toolchain_cli` verify deterministic `.axsdk`/`.axtoolchain` bundle creation, offline installation into an isolated toolchain root, `axiom.lock` SDK fingerprint pinning and mismatch rejection, and `axiomc sdk|toolchain` CLI output in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T876-report.md` with exact `## Files changed`.

## Out of scope
- Phase-wide conformance suite (`T877`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T876/build` and `python tools/axtest.py --compiler build-snap-T876/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
