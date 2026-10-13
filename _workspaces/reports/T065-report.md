# T065 — FFI: extern "C"/"system", @repr(C), DLL imports

## Files changed
- `bootstrap/axiom0/src/abi/lower.c`
- `bootstrap/axiom0/src/diag/codes/FFI.def`
- `bootstrap/axiom0/src/driver/pipeline.c`
- `bootstrap/axiom0/src/hir/lower.c`
- `bootstrap/axiom0/src/interp/interp.c`
- `bootstrap/axiom0/src/link/pe/linker.c`
- `bootstrap/axiom0/src/lir/lower.c`
- `bootstrap/axiom0/src/resolve/resolve.c`
- `bootstrap/axiom0/src/resolve/resolve.h`
- `bootstrap/axiom0/src/target/x64/isel/isel.c`
- `tests/run/ffi/interp_extern_rejected.ax`
- `tests/run/ffi/process_id.ax`
- `tests/run/ffi/repr_c_struct.ax`
- `tests/run/ffi/tick_count.ax`
- `tests/run/ffi/write_file.ax`
- `tests/ui/ffi/unsafe_extern.ax`

## Summary of Changes
1. **Diagnostic**: Added `AX_FFI_NOT_IN_ORACLE` in `bootstrap/axiom0/src/diag/codes/FFI.def`.
2. **Resolution**: In `bootstrap/axiom0/src/resolve/resolve.c` Pass 1, added iteration over `AX_ITEM_EXTERN_BLOCK` members to declare symbols in the module scope and export map.
3. **HIR Lowering**: In `bootstrap/axiom0/src/hir/lower.c`, propagated the extern block's ABI and `@link(...)` attributes to all member items.
4. **Driver Pipeline**: In `bootstrap/axiom0/src/driver/pipeline.c` `stage_hir`, linked extern block members into the main HIR item list so they are visible to typeck, unsafe checking, and MIR builder.
5. **Interpreter**: In `bootstrap/axiom0/src/interp/interp.c`, added a check in `eval_call` for `func->fn.abi.v != 0` to report `AX_FFI_NOT_IN_ORACLE` and fail with exit code 1 as required by ADR-0002. Also updated `find_func_by_symbol` to search extern block members.
6. **ABI Lowering**: In `bootstrap/axiom0/src/abi/lower.c`, updated `body->frame_req.max_outgoing_args_bytes` to include `call_sig.stack_args_size` for functions with 5+ arguments (e.g. `WriteFile`).
7. **LIR Lowering**: In `bootstrap/axiom0/src/lir/lower.c` `get_fn_sym_name`, formatted symbol names as `<dll>$<func>` when `@link("<dll>")` is present on an extern function, or defaulted to `KERNEL32.dll$<func>`.
8. **PE Linker**: In `bootstrap/axiom0/src/link/pe/linker.c`, implemented dynamic Import Directory (`.idata`) and import thunks (`jmp [rip + __IAT_*]`) in `.text` for arbitrary DLL functions referenced by relocations.
9. **x64 Instruction Selection**: In `bootstrap/axiom0/src/target/x64/isel/isel.c`, fixed multi-byte copy loops in ABI args, return value, load, and store to advance `i` by `chunk` instead of `8`, preventing truncation of non-8-byte aligned aggregate data (e.g. UTF-8 strings).
10. **Tests**:
    - `tests/run/ffi/tick_count.ax`: Native run calling `GetTickCount64`.
    - `tests/run/ffi/process_id.ax`: Native run calling `GetCurrentProcessId`.
    - `tests/run/ffi/write_file.ax`: Native run calling `WriteFile` printing `Xin chào thế giới\n` byte-exact.
    - `tests/run/ffi/repr_c_struct.ax`: Native run calling `GetSystemTime` with `@repr(C)` struct by pointer.
    - `tests/run/ffi/interp_extern_rejected.ax`: Interpreter run verifying `AX_FFI_NOT_IN_ORACLE` with exit code 1.
    - `tests/ui/ffi/unsafe_extern.ax`: UI test verifying `AX_UNSAFE_REQUIRED` when calling unsafe extern function without `unsafe`.

STATUS: COMPLETE round=0
