# T083a report

## Summary
Ported the MIR step execution interpreter and host interface oracle (`bootstrap/axiom0/src/interp/interp.c`, `interp.h`, `host.c`, `host.h`) to canonical Axiom under `compiler/interp/` and added standalone unit and execution parity test suites under `tests/selfhost/interp/`:

- **`compiler/interp/value.ax`**: Implemented `InterpValue`, `InterpAlloc`, `MirBodyEntry`/`MirBodyMap`, `InterpConstEvalCtx`, and `InterpCtx`; synthetic address allocator and pointer provenance/bounds/alignment/liveness validation (`interp_register_alloc`, `interp_ctx_alloc_zeroed`, `interp_ctx_dealloc`, `interp_find_synth_addr`, `interp_resolve_synth_ptr`, `interp_validate_raw_ptr`, `interp_validate_ptr_arith`); constant allocation registration; step-limit, stack-limit, FFI-not-in-oracle, and unsafe UB diagnostic reporting (`AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT`, `AX_FFI_NOT_IN_ORACLE`, `AX_UNSAFE_INTERP_UB`).
- **`compiler/interp/oracle.ax`**: Implemented the host intrinsic oracle (`interp_host_init`, `interp_host_cleanup`, `interp_eval_host_intrinsic`) supporting `heap_alloc`, `heap_free`, `write`, `read`, `open`, `close`, `exit_process`, `args_count`, `arg_len`, `arg_copy`, `env_len`, `env_copy`, and `monotonic_ns`, routing through `std.core.host` and tracking heap allocations in `InterpCtx`.
- **`compiler/interp/frame.ax`**: Implemented `CallFrame` allocation and registration (`frame_init`, `frame_cleanup`), `MirBodyMap` lookup/insertion (`mir_body_map_init`, `mir_body_map_free`, `mir_body_map_insert`, `mir_body_map_get_by_item`, `mir_body_map_get_by_sym`), and full MIR place projection address resolution (`get_local_ptr`, `get_place_ptr`, `eval_operand`) for `DEREF`, `FIELD` (structs, tuples, closures, downcast enums), `INDEX` (with runtime bounds checking and panic), `SUB_SLICE` (with runtime range checking and panic), and `DOWNCAST`.
- **`compiler/interp/interp.ax`**: Implemented two's-complement and 16-bit chunked wrapping 64-bit arithmetic/overflow helpers (`w_add_u64_ovf`, `w_sub_u64_ovf`, `w_mul_u64_ovf`, `s_add_ovf`, `s_sub_ovf`, `s_mul_ovf`, `s_div_ovf`, `s_rem_ovf`), `eval_rvalue` (`USE`, `REF`, `BINARY_OP`, `OVERFLOWS_BINARY_OP`, `UNARY_OP`, `CAST`, `DISCRIMINANT`, `LEN`, `AGGREGATE`, `REPEAT`), `exec_mir_stmt`, `exec_mir_body` (`RETURN`, `GOTO`, `SWITCH_INT`, `ASSERT`, `CALL`, `DROP`, `UNREACHABLE`), `eval_call` (builtins `print`, `print_int`, `len`, `drop`, `size_of`, `align_of`, `needs_drop`, `address_of`, `address_of_mut`, `is_null`, `null`, `null_mut`, `ptr_add`, `ptr_sub`, `ptr_copy`, `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `drop_in_place`, `forget`; `@intrinsic` functions `assert`, `panic`, `unreachable`, `wrapping_add*`, `wrapping_sub*`, `wrapping_mul*`, `wrapping_neg*`, `rotate_left*`, `rotate_right*`, `leading_zeros*`, `trailing_zeros*`, `count_ones*`; host oracle dispatch; FFI oracle check; recursive user function and closure calls with on-demand HIR->MIR lowering and drop elaboration), `exec_drop_in_place`, `interp_run`, and comptime evaluator `interp_eval_const_expr_into`.
- **`compiler/interp/mod.ax`**: Re-exported the public `compiler.interp` API.
- **`tests/selfhost/interp/`**: Added `gen_interp_tests.py`, `unit_main.ax.in` -> `qa_interp_unit.ax`, `exec_a_main.ax.in` -> `qa_interp_exec_a.ax`, and `exec_b_main.ax.in` -> `qa_interp_exec_b.ax`, testing value/allocation/frame/place/arithmetic/oracle helpers, control flow, recursion, aggregates/projections/views, builtin intrinsics and captured stdout parity (`"fib=2\nsum=150\n"`), on-demand HIR->MIR lowering, panics (`101`), unsafe raw pointer UB (`125` + `AX_UNSAFE_INTERP_UB`), step/stack limits (`124` + `AX_DRIVER_INTERP_STEP_LIMIT` / `AX_DRIVER_INTERP_STACK_LIMIT`), non-whitelisted FFI (`1` + `AX_FFI_NOT_IN_ORACLE`), and comptime constant evaluation (`AX_CONST_DIV_ZERO`, `AX_CONST_OVERFLOW`).

## Files changed
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp/mod.ax
- compiler/interp/oracle.ax
- compiler/interp/value.ax
- tests/selfhost/interp/exec_a_main.ax.in
- tests/selfhost/interp/exec_b_main.ax.in
- tests/selfhost/interp/gen_interp_tests.py
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp/unit_main.ax.in

## Tests
- `python tests/selfhost/interp/gen_interp_tests.py`
- `python tools/axtest.py -v selfhost/interp` -> `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0` (`qa_interp_unit.ax`, `qa_interp_exec_a.ax`, `qa_interp_exec_b.ax` all pass `[interp]`, `[native]`, and `[native-O1]`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T083a`
- `python tools/archcheck.py` -> `archcheck: 188 files scanned, 0 violations`
- Snapshot build & test in `build-snap-T083a`: `python tools/axtest.py --compiler build/axiom0.exe selfhost/interp` -> `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0`

## Spec deviations
none

## Follow-ups
- Stage-0 `bootstrap/axiom0/src/interp/interp.c` (`eval_call` lines 478, 523-620): `ctx->call_depth++` is incremented at the start of `eval_call`, and early returns for inline `@intrinsic` functions (`assert`, `wrapping_add*`, `wrapping_sub*`, `wrapping_mul*`, `wrapping_neg*`, `rotate_left*`, `rotate_right*`, `leading_zeros*`, `trailing_zeros*`, `count_ones*`) return without `ctx->call_depth--`. This leaves `ctx->call_depth` mismatched during the caller's `exec_mir_body` frame cleanup loop (`ctx->allocs[a].call_depth == ctx->call_depth`), leaving freed `frame.storage` pointers marked `is_live = true` in `ctx->allocs`. Fixed in the ported `compiler/interp/interp.ax` via `ret_call(ctx, ok)`.
- Stage-0 `bootstrap/axiom0/src/driver/build_native/build.c` (lines 131-163): `AX_X64_MI_MUL` (emitted by `isel.c` line 254 for 64-bit `AX_LIR_INST_UMUL_OVERFLOW`, i.e., `u64 * u64` and `usize * usize`) is not handled in `build.c` (`default: break;`), causing `SETCC B` to inspect stale `CF` in `RFLAGS` from preceding instructions. Worked around in `compiler/interp/` and `tests/selfhost/interp/` by using 16-bit signed chunk multiplication (`(x as i64) * (y as i64)`) and `interp_mul_usize`.

STATUS: COMPLETE round=0
