---
id: T698
title: E16.13 aarch64-apple-ios & aarch64-apple-ios-sim TargetDesc, Mach-O LC_BUILD_VERSION & iOS SDK sysroot linker
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T216, T313, T666, T686, T690, T697]
priority: 141
status: todo
attempts: 0
paths: [compiler/target/aarch64_ios, compiler/obj/macho_ios, compiler/link/ios, tests/target/ios, tests/link/ios]
locks: [compiler/target/desc.ax, compiler/link/macho.ax]
spec: [spec/SPEC-150-ios-aarch64-macho.md, 0196, 0220, tasks/0804, tasks/0810, tasks/0524]
covers: [REQ-ECO-978, REQ-ECO-983, REQ-ECO-1043, REQ-ECO-1086, REQ-OWN-4401, REQ-OWN-4791]
---
# T698 — E16.13 aarch64-apple-ios & aarch64-apple-ios-sim TargetDesc, Mach-O LC_BUILD_VERSION & iOS SDK sysroot linker

## Goal
Implement the `aarch64-apple-ios` and `aarch64-apple-ios-sim` targets in `TargetDesc`, emit Mach-O 64-bit binaries with valid `LC_BUILD_VERSION` platform tags, and resolve iOS SDK sysroots and framework imports in the linker.

## Scope
- Define `TargetDesc` entries in `compiler/target/aarch64_ios` and `compiler/target/desc.ax` for `aarch64-apple-ios` and `aarch64-apple-ios-sim` (`SPEC-150 AXS-IOS-001..005`), configuring 16KB page size, ARM64 AAPCS calling convention with Apple ABI variant (pointer authentication / PAC ignored or nop-spaced for v1, varargs on stack), and platform constants.
- Implement iOS Mach-O load command emission in `compiler/obj/macho_ios` and `compiler/link/macho.ax`: `LC_BUILD_VERSION` with `platform = 2` (iOS) or `platform = 7` (iOS Simulator), minos version, SDK version, `LC_SOURCE_VERSION`, and page-aligned segment layout.
- Implement iOS SDK sysroot discovery and framework search in `compiler/link/ios`: locating `iPhoneOS.sdk` / `iPhoneSimulator.sdk` via `xcrun --sdk iphoneos --show-sdk-path` or environment variable `AXIOM_IOS_SDK_PATH`, handling `-F` framework search paths, and emitting dylib load commands (`LC_LOAD_DYLIB`) for standard iOS system libraries (`libSystem.B.dylib`, `libc++.dylib`).
- Implement ad-hoc code-signature slot generation (`LC_CODE_SIGNATURE`) for simulator Mach-O outputs to allow simulator execution without paid developer certificates.
- Add object emission, load command inspection, and linker tests in `tests/target/ios` and `tests/link/ios`.

## Acceptance
- [ ] Tests in `tests/target/ios` verify `aarch64-apple-ios` and `aarch64-apple-ios-sim` emit valid Mach-O headers with correct `cputype`, `cpusubtype`, and `LC_BUILD_VERSION` platform numbers (2 and 7).
- [ ] Linker tests in `tests/link/ios` verify resolution of iOS SDK paths and framework dependencies into valid standalone simulator binaries and static libraries (`.a`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T698-report.md` with exact `## Files changed`.

## Out of scope
- iOS application lifecycle host shim and simulator harness (`T699`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), depends on P13 gate `T313` and Mach-O baseline `T666` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T698/build` and `python tools/axtest.py --compiler build-snap-T698/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 iOS target expansion)
