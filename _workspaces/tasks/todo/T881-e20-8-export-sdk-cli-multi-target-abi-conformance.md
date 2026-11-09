---
id: T881
title: E20.8 — CLI axiom build --export-sdk & multi-language foreign ABI conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T880]
priority: 231
status: todo
attempts: 0
paths: [compiler/driver, tests/conformance/p20/e20_8_polyglot_sdk]
spec: [spec/SPEC-117-polyglot-bindgen-sdk-export.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-ECO-8736, REQ-PKG-022]
---
# T881 — E20.8 — CLI axiom build --export-sdk & multi-language foreign ABI conformance suite

## Goal
Implement the `axiom build --export-sdk[=<lang>]` CLI command and certify E20.8 exit criteria with a comprehensive multi-language foreign ABI conformance suite.

## Scope
- Integrate `--export-sdk` into `axiom build` in `compiler/driver`:
  * Supports flags `--export-sdk=c`, `--export-sdk=python`, `--export-sdk=swift`, `--export-sdk=kotlin`, `--export-sdk=ts`, or `--export-sdk=all`.
  * Outputs packaged client SDK trees into `dist/sdk/<lang>/`.
- Create conformance suite in `tests/conformance/p20/e20_8_polyglot_sdk`:
  * Build a shared library (`.dll` on Windows, `.so` on Linux, `.dylib` on macOS).
  * Run external Python test runner invoking the shared library via `ctypes` verifying integers, floats, structs, strings, and callback functions.
  * Run C compiler (GCC/Clang/MSVC) compiling test program against emitted `.h` verifying identical struct offsets and calling convention alignment.
  * Verify differential agreement between native builds and mock oracle executions.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_8_polyglot_sdk` pass on host platform.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T881-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T881/build` and `python tools/axtest.py --compiler build-snap-T881/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:20:00 created by axiom-architect (ADR-0039 P20 polyglot bindgen/sdk expansion)
