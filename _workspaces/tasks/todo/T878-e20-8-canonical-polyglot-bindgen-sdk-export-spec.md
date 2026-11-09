---
id: T878
title: E20.8 — Canonical specification for polyglot FFI importer and SDK exporter (SPEC-117)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 228
status: todo
attempts: 0
paths: [spec/SPEC-117-polyglot-bindgen-sdk-export.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-117-polyglot-bindgen-sdk-export.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T878 — E20.8 — Canonical specification for polyglot FFI importer and SDK exporter (SPEC-117)

## Goal
Consolidate the canonical specification for the pure-Axiom C99/C11 header importer (`axiom bindgen`) and the multi-language foreign SDK exporter (`axiom build --export-sdk`) into `spec/SPEC-117-polyglot-bindgen-sdk-export.md` (`AXS-POLY-*` rule IDs).

## Scope
- Write `spec/SPEC-117-polyglot-bindgen-sdk-export.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-POLY-NNN` rules.
- Specify the pure-Axiom C99/C11 preprocessor and AST parser: macro evaluation (arithmetic constants, strings), typedef/struct/union/enum resolution, function prototype conversion to Axiom `extern "C" fn`, and clean compile-time rejection of C++ headers (`class`, `template`, `namespace`) with descriptive error `AX_FFI_CXX_NOT_SUPPORTED`.
- Specify the intermediate representation `ForeignInterface` capturing exported Axiom types, functions, constants, docstrings, and calling conventions (`extern "C"`).
- Specify language emitters lowering `ForeignInterface` to:
  * C99: `.h` header with include guards and `@repr(C)` struct layouts.
  * Python: zero-build `ctypes` wrapper module with native library loader.
  * Swift: Clang module map (`module.modulemap`) and idiomatic Swift wrapper.
  * Kotlin/Android: JNI C glue and idiomatic Kotlin `.kt` class wrappers.
  * TypeScript/WASM: `.d.ts` declaration and ESM loader glue.
- Specify CLI `axiom build --export-sdk=<lang>` and ABI conformance contracts across targets.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-117-polyglot-bindgen-sdk-export.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-POLY-NNN` rules, and language mapping specifications.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T878-report.md` with exact `## Files changed`.

## Out of scope
- C++ header parsing (C++ headers are deliberately out of scope).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T878/build` and `python tools/axtest.py --compiler build-snap-T878/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:20:00 created by axiom-architect (ADR-0039 P20 polyglot bindgen/sdk expansion)
