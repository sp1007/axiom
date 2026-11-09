---
id: T675a
title: E16.6 — WASM SIMD128 (0xFD) lowering, std.ffi.wasm_js & TypeScript/WIT definition export
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T674, T675]
priority: 119
status: todo
attempts: 0
paths: [compiler/target/wasm32, std/ffi/wasm_js, tests/run/wasm_simd, tests/run/wasm_js]
spec: [spec/SPEC-86-wasm32-backend.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-TGT-226, REQ-TGT-245]
---
# T675a — E16.6 — WASM SIMD128 (0xFD) lowering, std.ffi.wasm_js & TypeScript/WIT definition export

## Goal
Implement WebAssembly `SIMD128` (`0xFD` prefix) vector lowering for `LirType.V128`, the `std.ffi.wasm_js` JavaScript host interop library, and CLI type definition exports (`--emit-ts-defs`, `--emit-wit`).

## Scope
- In `compiler/target/wasm32`, lower `LirType.V128` operations to WebAssembly 128-bit vector instructions (`0xFD` prefix opcodes: `v128.load`, `v128.store`, `i32x4.add`, `i32x4.mul`, `f32x4.add`, `f32x4.mul`, `v128.any_true`, `i8x16.shuffle`).
- Implement `std.ffi.wasm_js` providing `@wasm_import` and `@wasm_export` attributes, `JsValue` opaque handle management, and linear-memory string slice conversions (`JsString.to_view_str`, `JsString.from_str`).
- In `compiler/driver`, implement `--emit-ts-defs` producing TypeScript `.d.ts` declaration files for `@wasm_export` functions, and `--emit-wit` producing WebAssembly Interface Type (WIT) package documents.

## Acceptance
- [ ] Conformance tests in `tests/run/wasm_simd` verify `SIMD128` vector execution under Node.js / V8 with exact numerical results.
- [ ] Run tests in `tests/run/wasm_js` verify JS function calls, callback passing, and string marshaling through `std.ffi.wasm_js`.
- [ ] Golden tests verify accurate `.d.ts` and `.wit` output files matching exported Axiom signatures.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T675a-report.md` with exact `## Files changed`.

## Out of scope
- WebAssembly 64-bit memory / memory64 (reserved for post-v1).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`), depends on P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T675a/build` and `python tools/axtest.py --compiler build-snap-T675a/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:10:00 created by axiom-architect (ADR-0039 P16 WASM SIMD/JS expansion)
