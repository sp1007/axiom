---
id: T880
title: E20.8 — ForeignInterface IR & multi-language SDK emitters (C99, Python, Swift, Kotlin, TypeScript)
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T879, T867]
priority: 230
status: todo
attempts: 0
paths: [compiler/sdk, tests/sdk]
spec: [spec/SPEC-117-polyglot-bindgen-sdk-export.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T880 — E20.8 — ForeignInterface IR & multi-language SDK emitters (C99, Python, Swift, Kotlin, TypeScript)

## Goal
Implement the `ForeignInterface` intermediate representation and five foreign-language SDK emitters lowering exported Axiom types and functions to idiomatic C99, Python ctypes, Swift, Kotlin JNI, and TypeScript declarations.

## Scope
- In `compiler/sdk`, define the `ForeignInterface` data structure extracted from compiled Axiom packages containing `@export` and `extern "C"` items: functions, structs, enums, type aliases, and documentation docstrings.
- Implement language emitters:
  * **C99**: Emit clean `.h` header with `#ifndef`, standard integer includes, `@repr(C)` structs with exact field padding, and function prototypes.
  * **Python**: Emit zero-dependency `.py` module using standard `ctypes`, mapping `c_int`, `c_void_p`, `Structure`, and automatic `.dll` / `.so` / `.dylib` loading.
  * **Swift**: Emit Clang `module.modulemap` and Swift wrapper struct converting Swift types (`String`, `Data`) to Axiom FFI slices.
  * **Kotlin / Android**: Emit Kotlin `.kt` class with `System.loadLibrary` and external methods, plus accompanying C JNI bridge functions (`Java_<class>_<method>`).
  * **TypeScript / WASM**: Emit `.d.ts` type declarations and ESM wrapper loading WebAssembly instances or Node.js native addons.

## Acceptance
- [ ] Golden tests in `tests/sdk` verify emitted foreign source files for each language against reference codebases.
- [ ] Round-trip integration tests verify compiling an Axiom library and successfully loading and invoking it from Python and C99 without memory corruption.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T880-report.md` with exact `## Files changed`.

## Out of scope
- Third-party package publishing (pip/npm upload); generation is purely local file emission.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T880/build` and `python tools/axtest.py --compiler build-snap-T880/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:20:00 created by axiom-architect (ADR-0039 P20 polyglot bindgen/sdk expansion)
