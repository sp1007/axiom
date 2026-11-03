---
id: T674
title: E16.6 — WASM32 TargetDesc, CFG structuring (block/loop/if/br_table), SSA stackification & shadow stack
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T313, T654, T655, T673]
priority: 117
status: todo
attempts: 0
paths: [compiler/target/wasm32/isel, compiler/abi/wasm32, tests/mc/wasm32_stackify, tests/selfhost/abi, tests/selfhost/isel]
spec: [spec/SPEC-86-wasm32-backend.md, tasks/0523, tasks/0784]
covers: [REQ-TGT-231, REQ-TGT-232, REQ-TGT-233, REQ-TGT-234, REQ-TGT-235, REQ-TGT-236, REQ-TGT-237, REQ-TGT-238, REQ-TGT-239, REQ-TGT-240, REQ-TGT-241, REQ-TGT-242, REQ-TGT-243, REQ-TGT-244, REQ-TGT-254, REQ-TGT-255, REQ-TGT-256, REQ-TGT-257, REQ-TGT-258, REQ-TGT-259, REQ-TGT-304]
---
# T674 — E16.6 — WASM32 TargetDesc, CFG structuring (block/loop/if/br_table), SSA stackification & shadow stack

## Goal
Implement the `wasm32` `TargetDesc`, `CallConv.Wasm` shadow-stack and ABI pass, arbitrary-CFG-to-structured-WASM control-flow reconstruction, and SSA-to-operand-stack stackification in `compiler/abi/wasm32` and `compiler/target/wasm32/isel`.

## Scope
- Implement `CallConv.Wasm` in `compiler/abi/wasm32`: 32-bit pointer layout (`usize`/`isize` = `i32`), scalar argument/return lowering, hidden `sret` linear-memory pointer parameter for multi-value/composite returns, 16-byte aligned `__stack_pointer` shadow-stack frame allocation/deallocation for address-taken locals and views, and `call_indirect` table index lowering for `FnPtr` and `dyn` vtables.
- Implement `wasm32` CFG structuring and instruction selection in `compiler/target/wasm32/isel`:
  - Reconstruct structured WASM control flow (`block`, `loop`, `if`/`else`, `br`, `br_if`, `br_table`, `return`) from arbitrary LIR CFGs, including irreducible loop dispatch legalization (`AWASM-65..68`).
  - Stackify single-use SSA expression trees directly onto the WASM operand stack (`local.get`, `local.set`, `local.tee`) and allocate interference-free typed WASM locals (`i32`, `i64`, `f32`, `f64`, `v128`) for multi-use values (`AWASM-69..70`).
  - Lower checked integer arithmetic, 128-bit integer pairs, IEEE-754 floats, `simd128` vectors (when enabled), and atomic memory ops (`memory.atomic.wait32`/`notify`, `i32.atomic.rmw.*` when `+atomics` is enabled).
- Add unit and selfhost tests in `tests/mc/wasm32_stackify`, `tests/selfhost/abi`, and `tests/selfhost/isel`.

## Acceptance
- [ ] Arbitrary LIR CFGs (nested loops, early returns, `match` jump tables, irreducible regions) lower to valid structured WASM instructions with balanced operand stacks.
- [ ] Positive and negative tests in `tests/mc/wasm32_stackify`, `tests/selfhost/abi`, and `tests/selfhost/isel` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T674-report.md` with exact `## Files changed`.

## Out of scope
- Binary `.wasm` encoding, internal bytecode validator, linker, and `std.sys.wasi` (`T675`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:41:00 created by T216 (P16 phase planning)
