---
id: T874
title: E20.6 Canonical native SDK, declarative .axsdk sysroot metadata, AXTOOLCHAIN descriptor & toolchain distribution specification (SPEC-116)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 224
status: todo
attempts: 0
paths: [spec/SPEC-116-sdk-sysroot-toolchain-distribution.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-88-cross-compilation-platform-layer.md, spec/SPEC-110-build-graph-driver.md, tasks/0605, tasks/1034, tasks/0661, tasks/0858]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T874 — E20.6 Canonical native SDK, declarative .axsdk sysroot metadata, AXTOOLCHAIN descriptor & toolchain distribution specification (SPEC-116)

## Goal
Consolidate the canonical specification for Axiom's C-free Native SDK (`.axsdk`), declarative platform sysroot metadata, `AXTOOLCHAIN` target/ABI/object-pipeline descriptors, `SdkFingerprint` lockfile pinning, and hermetic toolchain/sysroot bundle distribution into `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` (`AXS-SDK-*` rule IDs).

## Scope
- Write `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-SDK-NNN` rules.
- Specify the strict separation of `Compiler`, `Platform SDK`, and `Sysroot` (`tasks/0605 §1-17`, `tasks/1034 §1-7`): Axiom never hard-codes host OS include/library paths (`C:\Windows`, `/usr/include`) or requires a C compiler/header parser; platform APIs, syscalls, import stubs, CRT startup contracts, and weak/optional OS API availability are described declaratively in `.axsdk` artifacts.
- Specify `AXTOOLCHAIN` target/ABI/object-pipeline descriptors across tier-1 and tier-2 targets (`tasks/1034 §8-24`: `x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `wasm32`, `riscv64-linux`), cryptographic `SdkFingerprint` and `ToolchainFingerprint` hashes, and `axiom.lock` SDK pinning (`tasks/0605 §5, 18-21`, `REQ-PKG-022`).
- Specify hermetic multi-target SDK/sysroot and toolchain archive packaging, offline installation, and `axiomc sdk` / `axiomc toolchain` CLI subcommands (`tasks/0605 §18-21`, `tasks/0858`, `tasks/1034`, `REQ-ECO-8736`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-SDK-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T874-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the `.axsdk` sysroot loader, `AXTOOLCHAIN` registry, and `axiomc sdk|toolchain` CLI (`T875`–`T876`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
