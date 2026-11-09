---
id: T697
title: E16.13 Canonical iOS AArch64 & iOS Simulator Mach-O target specification (SPEC-150)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313, T665, T681, T685]
priority: 140
status: todo
attempts: 0
paths: [spec/SPEC-150-ios-aarch64-macho.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0193, 0196, 0217, 0220, tasks/0587, tasks/0804, tasks/0805, tasks/0807, tasks/0810, tasks/0518, tasks/0521, tasks/0524, tasks/0846]
covers: [REQ-ECO-163, REQ-ECO-518, REQ-ECO-978, REQ-ECO-983, REQ-ECO-1043, REQ-ECO-1086, REQ-ECO-1120, REQ-ECO-1633, REQ-ECO-2279, REQ-ECO-2280, REQ-OWN-4401, REQ-OWN-4791, REQ-OWN-6006]
---
# T697 — E16.13 Canonical iOS AArch64 & iOS Simulator Mach-O target specification (SPEC-150)

## Goal
Consolidate the canonical specification for Axiom's Apple iOS 64-bit ARM (`aarch64-apple-ios`) and iOS Simulator (`aarch64-apple-ios-sim`) Mach-O targets, SDK sysroot integration, code signing boundaries, and execution model into `spec/SPEC-150-ios-aarch64-macho.md` (`AXS-IOS-*` rule IDs).

## Scope
- Write `spec/SPEC-150-ios-aarch64-macho.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-IOS-NNN` rules (`0193`, `0196`, `0217`, `0220`, `0587`, `0804 §582.126`, `0805 §583.7-81`, `0807 §585.38`, `0810 §588.4-146`, `tasks/0524 §112-113`).
- Specify target identities: canonical `aarch64-apple-ios` (device, `PLATFORM_IOS = 2`) and `aarch64-apple-ios-sim` (simulator, `PLATFORM_IOSSIMULATOR = 7`), aliases `ios-arm64` and `ios-sim-arm64`, CPU subtype `CPU_SUBTYPE_ARM64_ALL`, and minimum deployment target metadata (`LC_BUILD_VERSION` minos/sdk versions).
- Specify the iOS Mach-O binary format and linking rules (`REQ-OWN-4401`, `REQ-OWN-4791`): Mach-O 64-bit object/executable/dylib/framework generation, page size (16KB alignment), `__TEXT`, `__DATA`, `__DATA_CONST`, and `__LINKEDIT` segments, and the code-signing / ad-hoc signature boundary (`LC_CODE_SIGNATURE`, entitlements stubbing, `codesign` tool interop).
- Specify iOS SDK sysroot resolution and framework linking (`REQ-LNK-342`, `REQ-LNK-772`, `REQ-ECO-1043`): discovering Xcode SDK paths (`iPhoneOS.sdk` vs `iPhoneSimulator.sdk`), binding SDK fingerprints, searching system frameworks (`Foundation`, `UIKit`, `Metal`, `QuartzCore`), and disallowing desktop-only Mach APIs.
- Specify the application lifecycle and execution model (`REQ-ECO-518`, `REQ-ECO-8538`): distinguish standalone GUI applications (`UIApplicationMain` entry shim, event loop, suspension/resume events) from libraries/frameworks, avoiding desktop CLI assumptions.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-150-ios-aarch64-macho.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-IOS-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T697-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of iOS backend emitter and Mach-O loader (`T698`).
- Metal graphics/compute pipeline runtime (`E22.5`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), depends on P13 gate `T313` and P16 foundations (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T697/build` and `python tools/axtest.py --compiler build-snap-T697/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 iOS target expansion)
