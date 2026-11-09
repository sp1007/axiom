---
id: T879
title: E20.8 — Pure-Axiom C99/C11 FFI preprocessor, AST parser & axiom bindgen CLI
phase: P20-build-system-package-ecosystem
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T878, T851]
priority: 229
status: todo
attempts: 0
paths: [compiler/bindgen, compiler/driver, tests/bindgen]
spec: [spec/SPEC-117-polyglot-bindgen-sdk-export.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T879 — E20.8 — Pure-Axiom C99/C11 FFI preprocessor, AST parser & axiom bindgen CLI

## Goal
Implement a self-contained, pure-Axiom C99/C11 preprocessor, AST parser, and `axiom bindgen <header.h> -o <output.ax>` CLI tool that converts C headers into canonical Axiom FFI declarations while cleanly rejecting C++.

## Scope
- In `compiler/bindgen`, implement a pure-Axiom C preprocessor and lexer:
  * Handle `#include`, `#define` (constant numeric expressions, strings, object-like macros), `#ifdef`/`#ifndef`/`#endif`, `#pragma once`.
  * Resolve include search paths passed via `-I <dir>`.
- Implement C99/C11 AST parser:
  * Parse integer types (`int8_t`..`uint64_t`, `size_t`, `int`, `long`, `char`), float types (`float`, `double`), pointer qualifiers (`const*`, `*`), `@repr(C)` structs, untagged `union`s, `enum`s, `typedef`s, and function declarations.
  * Emit corresponding Axiom types and `extern "C" fn` signatures using canonical syntax (`=` and `.`).
  * If C++ keywords (`class`, `template`, `namespace`, `public:`, `virtual`, `constexpr`) are encountered, halt with a clean diagnostic: `AX_FFI_CXX_NOT_SUPPORTED: C++ headers are not supported by axiom bindgen; wrap in extern "C" C99 interface`.
- Expose the CLI subcommand `axiom bindgen <header.h> [-o <out.ax>] [-I <include_dir>]`.

## Acceptance
- [ ] Conformance tests in `tests/bindgen` verify parsing standard C99 headers (`sqlite3.h`, `zlib.h`, standard POSIX/Win32 snippets) into syntactically valid Axiom FFI modules.
- [ ] Negative tests verify that C++ headers are cleanly rejected with `AX_FFI_CXX_NOT_SUPPORTED`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T879-report.md` with exact `## Files changed`.

## Out of scope
- C++ AST or template instantiation.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T879/build` and `python tools/axtest.py --compiler build-snap-T879/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:20:00 created by axiom-architect (ADR-0039 P20 polyglot bindgen/sdk expansion)
