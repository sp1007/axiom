---
id: T699
title: E16.13 iOS UIApplication / CAMetalLayer host bootstrap shim, simulator test harness & target conformance suite
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T216, T313, T668, T684, T698]
priority: 142
status: todo
attempts: 0
paths: [std/sys/ios, tests/conformance/p16/e16_13_ios_target]
locks: [std/sys/mod.ax]
spec: [spec/SPEC-150-ios-aarch64-macho.md, tasks/0805, tasks/0807, tasks/0846, tasks/0524]
covers: [REQ-ECO-163, REQ-ECO-518, REQ-ECO-2280, REQ-OWN-6006]
---
# T699 — E16.13 iOS UIApplication / CAMetalLayer host bootstrap shim, simulator test harness & target conformance suite

## Goal
Implement the iOS runtime platform shim (`std/sys/ios`) supporting `UIApplication` / `CAMetalLayer` windowing bootstrap, provide an automated iOS Simulator test execution harness, and certify complete iOS target conformance.

## Scope
- Implement `std/sys/ios`: iOS entry-point shim (`UIApplicationMain`), application delegate event lifecycle forwarding (application did finish launching, will resign active, did enter background, will terminate), and main UI window initialization hosting a `CAMetalLayer` for graphics.
- Implement the iOS Simulator test execution harness in `tools/test_ios_sim.py`: packaging test executables into minimal `.app` bundles, creating basic `Info.plist`, booting an iOS Simulator via `xcrun simctl boot`, installing and launching the test binary, streaming stdout/stderr, and collecting exit codes.
- Implement headless / non-interactive CLI fallback for unit test suites on simulator so tests run deterministically without user interaction.
- Create the E16.13 iOS target conformance suite in `tests/conformance/p16/e16_13_ios_target` verifying basic integer arithmetic, memory allocation, string printing, file sandboxing, and Mach-O execution parity against the host.

## Acceptance
- [ ] Conformance tests in `tests/conformance/p16/e16_13_ios_target` pass under simulator harness (or structural Mach-O simulator verification on platforms lacking Xcode).
- [ ] `std/sys/ios` compiles and correctly defines entry point, event forwarding, and `CAMetalLayer` binding.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T699-report.md` with exact `## Files changed`.

## Out of scope
- Metal shader compilation and host driver (`E22.5`).
- App Store submission, provisioning profiles, and code signing with Apple Developer IDs.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), closes Epic E16.13.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T699/build` and `python tools/axtest.py --compiler build-snap-T699/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-09 21:45:00 created by architect (ADR-0038 iOS target expansion)
