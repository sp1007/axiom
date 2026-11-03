---
id: T673
title: E16.6 — Canonical WASM32 stack-machine backend, CFG stackification, binary .wasm & WASI specification (SPEC-86)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T313, T653]
priority: 116
status: todo
attempts: 0
paths: [spec/SPEC-86-wasm32-backend.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-81-target-desc-isa-conformance.md, 0220, tasks/0453, tasks/0523, tasks/0784]
covers: [REQ-TGT-079, REQ-TGT-207, REQ-TGT-208, REQ-TGT-209, REQ-TGT-210, REQ-TGT-211, REQ-TGT-212, REQ-TGT-213, REQ-TGT-214, REQ-TGT-215, REQ-TGT-216, REQ-TGT-217, REQ-TGT-218, REQ-TGT-219, REQ-TGT-220, REQ-TGT-221, REQ-TGT-222, REQ-TGT-223, REQ-TGT-224, REQ-TGT-225]
---
# T673 — E16.6 — Canonical WASM32 stack-machine backend, CFG stackification, binary .wasm & WASI specification (SPEC-86)

## Goal
Consolidate the canonical specification for Axiom's `wasm32` (`wasm32-freestanding` and `wasm32-wasi`) target backend, structured control-flow reconstruction, SSA-to-operand-stack stackification, linear-memory shadow stack & provenance model, `.wasm` binary module/object archive format, internal bytecode validator, and WASI platform layer into `spec/SPEC-86-wasm32-backend.md` (`AXS-WASM-*` rule IDs).

## Scope
- Write `spec/SPEC-86-wasm32-backend.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-WASM-NNN` rules (`tasks/0523` `AWASM-20..95`, `0220 §10`, `tasks/0784`).
- Specify WASM target classification and memory model (`AWASM-20..36`): `wasm32` uses 32-bit `usize`/`isize` pointers without altering Core pointer/ownership/capability/view semantics; non-address-taken SSA values live in typed WASM locals (`i32`, `i64`, `f32`, `f64`, `v128`) and the virtual operand stack, while address-taken locals, aggregates, `view`/`mut_view` referents, and `sret` buffers reside on an explicit 16-byte aligned linear-memory shadow stack (`global 0: __stack_pointer`).
- Specify arbitrary LIR CFG structuring and stackification (`AWASM-21..23, 65..70`, `ABACKEND-79`): forward branches become `block ... br`, natural loops become `loop ... br`, conditional splits become `if ... else ... end`, multi-way switches become `br_table`, irreducible CFGs are legalized via an explicit dispatch variable + loop/switch state machine, and SSA expressions are tree-scheduled onto the WASM operand stack with local coalescing.
- Specify the WebAssembly Basic C ABI (`CallConv.Wasm`, `AWASM-42..55`): scalar parameters/returns, indirect aggregate `sret` pointer as first parameter, indirect calls (`FnPtr` and `dyn` vtables) via `call_indirect` over `__indirect_function_table`, explicit target features (`sign_ext`, `nontrapping_fptoint`, `bulk_memory`, `simd128`, `atomics`), and panic lowering to `unreachable` trap or WASI diagnostic + `proc_exit(101)`.
- Specify the `.wasm` binary module format (`\0asm\x01\x00\x00\x00`, sections `1..12` plus relocatable `linking` custom section for WASM object archives), mandatory internal stack-type and control-flow bytecode validation before emission (`AWASM-63..64`), and `std.sys.wasi` (`wasi_snapshot_preview1` imports).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-86-wasm32-backend.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-WASM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T673-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of the WASM32 backend (`T674`, `T675`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:41:00 created by T216 (P16 phase planning)
