---
id: T875
title: E20.6 Declarative .axsdk sysroot loader, SdkFingerprint verifier, C-free platform import/CRT resolver & AXTOOLCHAIN target registry
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T852, T874]
priority: 225
status: doing
attempts: 1
paths: [compiler/sdk/sysroot, compiler/sdk/toolchain, tests/run/sdk_sysroot]
spec: [spec/SPEC-116-sdk-sysroot-toolchain-distribution.md, spec/SPEC-88-cross-compilation-platform-layer.md, tasks/0605, tasks/1034]
covers: [REQ-ECO-8736, REQ-PKG-022]
started: 2026-11-08 22:52:39
agent: T875-impl
---
# T875 — E20.6 Declarative .axsdk sysroot loader, SdkFingerprint verifier, C-free platform import/CRT resolver & AXTOOLCHAIN target registry

## Goal
Implement the declarative `.axsdk` sysroot loader, `SdkFingerprint` verifier, C-free platform import/CRT startup resolver, and `AXTOOLCHAIN` target pipeline registry per `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md`.

## Scope
- Implement `compiler/sdk/sysroot` loading declarative `.axsdk` manifests and prebuilt target std/import stubs without probing ambient host OS paths or invoking a C compiler (`tasks/0605 §2-17`), checking minimum/target OS API availability gates (`@available(os = ..., min_version = ...)`), and computing cryptographic `SdkFingerprint` digests for build cache keys and `axiom.lock` (`tasks/0605 §5, 11-19`, `REQ-PKG-022`).
- Implement `compiler/sdk/toolchain` managing `AXTOOLCHAIN` target/ABI/object-pipeline descriptors (endianness, pointer width, data model, calling conventions, SIMD/float ABI, and PE64/PE-ARM64/ELF64/Mach-O/WASM32 linker pipelines; `tasks/1034 §4-24`, `REQ-ECO-8736`).
- Add run and negative diagnostic tests in `tests/run/sdk_sysroot`.

## Acceptance
- [ ] Run tests in `tests/run/sdk_sysroot` verify declarative `.axsdk` sysroot loading, rejection of ambient host path fallback when `--sysroot` is hermetic, `SdkFingerprint` verification, API availability gating, and `AXTOOLCHAIN` cross-target pipeline lookup in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T875-report.md` with exact `## Files changed`.

## Out of scope
- SDK/toolchain archive bundling and `axiomc sdk|toolchain` CLI subcommands (`T876`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T875/build` and `python tools/axtest.py --compiler build-snap-T875/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 22:52:39 started (attempt 1) T875-impl
