---
id: T668a
title: E16.4 — Capability-safe Apple Objective-C runtime layer (std.ffi.objc) & ARC integration
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T666, T667]
priority: 112
status: todo
attempts: 0
paths: [std/ffi/objc, compiler/target/aarch64, tests/run/objc, tests/mock/libobjc]
spec: [spec/SPEC-84-macos-aarch64-macho.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TGT-314, REQ-FFI-097]
---
# T668a — E16.4 — Capability-safe Apple Objective-C runtime layer (std.ffi.objc) & ARC integration

## Goal
Implement `std.ffi.objc` providing capability-safe Apple Objective-C runtime bindings, exact-cast `objc_msgSend` AAPCS64 trampolines, `ObjcStrong<T>` automatic reference counting, scoped `AutoreleasePool`, an FFI exception barrier, and a Windows mock `libobjc` test harness.

## Scope
- Implement `std.ffi.objc` defining opaque reference types (`id`, `Class`, `SEL`), selector registration (`sel_registerName`), and class lookup (`objc_getClass`).
- Implement AAPCS64 Darwin `objc_msgSend` trampolines in `std/ffi/objc` enforcing exact function-pointer signatures matching message parameters and returns (preventing Darwin variadic ABI register mismatches).
- Implement `ObjcStrong<T>` smart pointer wrapping Objective-C instances with RAII `objc_retain` on clone and `objc_release` on `Drop`.
- Implement `AutoreleasePool.run` providing a deterministic lexically scoped autorelease context (`objc_autoreleasePoolPush` / `objc_autoreleasePoolPop`).
- Wrap Objective-C invocations with a zero-cost exception barrier (`@try/@catch` or `objc_begin_catch`) ensuring Objective-C NSExceptions cannot unwind across the Axiom FFI boundary.
- Provide a host Windows mock `libobjc` DLL and Mach-O `__objc_selrefs`/`__objc_classlist` structural validation tests.

## Acceptance
- [ ] Run tests in `tests/run/objc` verify `ObjcStrong<T>` retain/release lifecycle, message dispatch, and autorelease pool draining using the mock `libobjc` runtime on Windows and real macOS AArch64.
- [ ] Mach-O structural tests verify emitted Objective-C symbol references in the Mach-O binary.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T668a-report.md` with exact `## Files changed`.

## Out of scope
- Objective-C++ or Swift interoperability (handled separately).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), depends on P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T668a/build` and `python tools/axtest.py --compiler build-snap-T668a/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:10:00 created by axiom-architect (ADR-0039 P16 Apple ObjC runtime expansion)
