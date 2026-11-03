---
id: T675
title: E16.6 — Binary .wasm module/object writer, internal WASM bytecode validator, linker & std.sys.wasi
phase: P16-targets-platforms
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T313, T674]
priority: 118
status: todo
attempts: 0
paths: [compiler/target/wasm32/encode, compiler/obj/wasm, compiler/link/wasm, std/sys/wasi, tests/obj/wasm, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link]
spec: [spec/SPEC-86-wasm32-backend.md, 0220, tasks/0523, tasks/0784]
covers: [REQ-TGT-226, REQ-TGT-227, REQ-TGT-228, REQ-TGT-229, REQ-TGT-245, REQ-TGT-246, REQ-TGT-247, REQ-TGT-248, REQ-TGT-249, REQ-TGT-250, REQ-TGT-251, REQ-TGT-252, REQ-TGT-253, REQ-TGT-260, REQ-TGT-261, REQ-TGT-262, REQ-TGT-263, REQ-TGT-266, REQ-TGT-267, REQ-TGT-268, REQ-TGT-269, REQ-TGT-271]
---
# T675 — E16.6 — Binary .wasm module/object writer, internal WASM bytecode validator, linker & std.sys.wasi

## Goal
Implement the binary `.wasm` encoder, internal WASM stack-type/control-flow bytecode validator (`AWASM-63..64`), relocatable WASM object/archive writer, `.wasm` module linker, and `std/sys/wasi` (`wasi_snapshot_preview1`) host layer.

## Scope
- Implement the binary `.wasm` instruction encoder and internal bytecode validator in `compiler/target/wasm32/encode`:
  - Encode WASM opcodes and unsigned/signed LEB128 immediates deterministically.
  - Validate every function body before binary emission (`AWASM-63..64`): operand stack type checking across `block`/`loop`/`if`/`else`/`end`, polymorphic stack state after unconditional `br`/`return`/`unreachable`, local index bounds, alignment power-of-two checks on loads/stores, and linear-memory/table index validity.
- Implement WASM relocatable object files and object archives in `compiler/obj/wasm` (`linking` custom section with symbol table and `R_WASM_FUNCTION_INDEX_LEB`, `R_WASM_TABLE_INDEX_SLEB`, `R_WASM_MEMORY_ADDR_LEB`/`SLEB`/`I32` relocations).
- Implement the `.wasm` module linker in `compiler/link/wasm`: merge `Type`, `Import`, `Function`, `Table` (`__indirect_function_table`), `Memory` (`memory`), `Global` (`__stack_pointer`, `__heap_base`, `__data_end`), `Export`, `Element`, `Code`, and passive/active `Data` sections, strip unreferenced functions/globals from exports roots (`AWASM-56..58, 78`), and emit `_start` (command) or `_initialize` (reactor/library).
- Implement `std/sys/wasi` over `wasi_snapshot_preview1` (`fd_read`, `fd_write`, `fd_close`, `fd_fdstat_get`, `fd_filestat_get`, `path_open`, `path_create_directory`, `path_unlink_file`, `fd_readdir`, `args_sizes_get`/`args_get`, `environ_sizes_get`/`environ_get`, `clock_time_get`, `proc_exit`, and linear-memory `memory.grow` bump/freelist heap).
- Add tests in `tests/obj/wasm`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link`.

## Acceptance
- [ ] `axiomc build --target wasm32` emits deterministic, internally validated `.wasm` modules and object archives that pass the internal WASM validator and execute on WASI runtimes (`wasmtime` / `wasmer` / built-in test runner when available).
- [ ] Positive and negative tests in `tests/obj/wasm`, `tests/selfhost/encode`, `tests/selfhost/obj`, and `tests/selfhost/link` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T675-report.md` with exact `## Files changed`.

## Out of scope
- Full WASM32 conformance suite (`T676`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom code uses canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 08:41:00 created by T216 (P16 phase planning)
