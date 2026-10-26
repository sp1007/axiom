# T154 Report: Backend Parity — Narrow-Value Extension, `-O1` / Closure Build Path, Const-Table `.rdata` Layout, and `__ax_host_print_int` Shadow Space

## Summary of Changes

### 1. Narrow-Value Sign/Zero Extension (`AX_TY_INT_VAR` / `TY_INT_VAR` Defaulted `i32`)
- **Root Cause**:
  - Per `SPEC-03` §3.1, unconstrained integer inference variables (`AX_TY_INT_VAR` / `TY_INT_VAR`) default to signed 32-bit `i32` (`4` bytes).
  - In `AX_LIR_INST_LOAD` (`bootstrap/axiom0/src/target/x64/isel/isel.c:576`) and `LIR_INST_LOAD` (`compiler/target/x64/isel.ax:1612`), `is_signed` checked `AX_TY_I8 | AX_TY_I16 | AX_TY_I32 | AX_TY_I64 | AX_TY_ISIZE` (`TY_I8 | TY_I16 | TY_I32 | TY_I64 | TY_ISIZE`) but omitted `AX_TY_INT_VAR` (`TY_INT_VAR`). Consequently, 4-byte loads of defaulted `i32` values (such as tuple destructuring fields `let (a, b) = (-1, -2)` or array elements `[-1, -2, -300000]`) emitted 32-bit zero-extending `mov r32, [mem]` instead of sign-extending `movsxd r64, dword ptr [mem]`.
  - In `AX_MIR_RVALUE_CAST` (`bootstrap/axiom0/src/interp/interp.c:1118`), `src_signed` / `src_bits` handled `AX_TY_I32` (`src_signed = true; src_bits = 32;`) but omitted `AX_TY_INT_VAR`, causing `--interp` casts of defaulted `i32` values to `i64` (`a0 as i64`) to zero-extend `0xFFFFFFFF` (`4294967295`) instead of sign-extending `-1`.
- **Fix**:
  - Added `|| t->kind == AX_TY_INT_VAR` to `AX_LIR_INST_LOAD` in `bootstrap/axiom0/src/target/x64/isel/isel.c`.
  - Imported `TY_INT_VAR` and added `|| tk == TY_INT_VAR` to `LIR_INST_LOAD` in `compiler/target/x64/isel.ax`.
  - Added `case AX_TY_INT_VAR:` alongside `case AX_TY_I32:` in `AX_MIR_RVALUE_CAST` in `bootstrap/axiom0/src/interp/interp.c`.
  - Added `tests/run/parity/backend/narrow_negative.ax` covering negative values across defaulted `i32`, `i32`, `i16`, `i8`, and high-bit `u32` in tuple destructuring, nested tuples, and struct fields across `interp`, `native` (`-O0`), and `native-O1` (`-O1`), verified byte-identical between `axiom0` and `axiomc`.

### 2. `-O1` LIR / Backend Path & Anonymous Closure Build Parity
- **Root Cause**:
  - `tests/run/struct/simple.ax` was already byte-identical at `-O0` and `-O1` after `T141` fixed `mir_type_needs_drop` for 0-field `struct Empty {}`.
  - For closure programs (`tests/run/closure/{closure_types,qa_move_capture,capture_modes,qa_mixed_captures}.ax`, `tests/run/native_p7/qa_closure_capture.ax`), `bootstrap/axiom0/src/driver/build_native/build.c:459-510` emits anonymous closure `HIR_ITEM_FN` items (`(*fn_item).name.v == 0`, `(*fn_item).symbol.v != 0`) into `.text` under the fallback symbol name `__ax_fn_<symbol.v>` and synthesizes their `AxType` (`TY_FN`) from the item's parameters and return type when not present in the top-level symbol table.
  - In `compiler/backend/session.ax` (`session_emit_objmodel_hir` and `session_compile_and_emit_objmodel`) and `compiler/driver/pipeline.ax` (`driver_build_compile_module_Native`), anonymous closure `HIR_ITEM_FN` items were skipped when `(*fn_item).name.v == 0`, causing `pe_link` to fail with an unresolved symbol on `__ax_fn_<id>`.
- **Fix**:
  - Added `backend_alloc_anon_fn_sym` (`__ax_fn_<symbol.v>`) and `backend_resolve_item_fn_ty` in `compiler/backend/session.ax` and wired both `compiler/backend/session.ax` and `compiler/driver/pipeline.ax` to emit anonymous closure functions into `.text` with their resolved/synthesized `AxType` signature.
  - All 5 closure tests (`closure_types.ax`, `qa_move_capture.ax`, `capture_modes.ax`, `qa_mixed_captures.ax`, `qa_closure_capture.ax`) are now 100% byte-identical between `axiom0` and `axiomc` at `-O0` and `-O1`.

### 3. Const Tables with `Str` (`ADR-0004` & `ADR-0035` §1)
- **Root Cause**:
  - In `bootstrap/axiom0/src/interp/interp.c`, `AX_MIR_RVALUE_AGGREGATE` (lines 687–696) and `AX_MIR_RVALUE_REPEAT` (lines 726–735) only handled `AX_MIR_CONST_INT` (`f_size` 1/2/4/8) when materializing `AX_MIR_OP_CONST` operands into aggregate memory (`dest + offset`). When a `const` array or struct aggregate contained `Str` literals (`AX_MIR_CONST_STR`, `f_size == 16`), the 16-byte `Str` slot in `cval.agg_data` was left zeroed (`ptr = NULL, len = 0`), causing `.rdata` const tables in `build.c` / `emit_obj.c` to emit zero lengths and no `.Lconst_<sym>.str.<off>` relocations.
  - Additionally, `bootstrap/axiom0/src/link/pe/linker.c:738` and `compiler/link/pe.ax:291-294` set `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE | IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA` (`0x8160`) on fixed-base (`ImageBase = 0x140000000`) PE32+ executables that have no `.reloc` base-relocation directory (`dirs[5] = {0, 0}`). When Windows ASLR relocated the image away from `0x140000000`, `IMAGE_REL_AMD64_ADDR64` 64-bit pointers in `.rdata` (used for `Str.ptr` inside `const` tables) still pointed at `0x140000000 + sym_rva`, causing `WriteFile` to fail with `ERROR_NOACCESS` when printing `Str` slices loaded from `.rdata` `const` tables.
- **Fix**:
  - Updated `AX_MIR_RVALUE_AGGREGATE` and `AX_MIR_RVALUE_REPEAT` in `bootstrap/axiom0/src/interp/interp.c` to write `constant.str.bytes` (at `dest + offset`) and `constant.str.len` (at `dest + offset + 8`) when `f_ty.v == interp->thir->interner.t_str.v` and `f_size == 16`.
  - Updated `ohdr.DllCharacteristics` in `bootstrap/axiom0/src/link/pe/linker.c` and `ohdr.dll_characteristics` in `compiler/link/pe.ax` in lockstep to `IMAGE_DLLCHARACTERISTICS_NX_COMPAT | IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE` (`0x8100`) for fixed-base PE32+ executables without `.reloc`.
  - Added `tests/run/parity/backend/const_table_str.ax` testing `const` tables of `Str` (including empty `""`) and `const` tables of structs mixing `Str` and signed/unsigned scalars, printing both string contents and lengths across `interp`, `native`, and `native-O1`, verified byte-identical between `axiom0` and `axiomc`.

### 4. Native `__ax_host_print_int` Win64 Shadow-Space Clobber
- **Root Cause**:
  - In `bootstrap/axiom0/src/link/pe/linker.c` (`print_int_code[]`) and `compiler/link/import.ax` (`AXIOM_PRINT_INT_CODE`), `__ax_host_print_int` allocated `sub rsp, 0x30` and placed the end of its ASCII digit buffer at `lea rdi, [rsp + 0x20]`, growing downward into `[rsp + 0x09 .. 0x20]`.
  - It then called `GetStdHandle(STD_OUTPUT_HANDLE)` BEFORE copying the digits to `WriteFile`. Under the Win64 ABI, `[rsp + 0x00 .. 0x1F]` inside the callee `GetStdHandle` (after `call` pushes the 8-byte return address) corresponds to the caller's `[rsp + 0x00 .. 0x1F]` 32-byte shadow space (`home space`), which `GetStdHandle` is permitted to overwrite, corrupting the formatted digits in `r8`/`rdx`!
- **Fix**:
  - Updated `print_int_code[]` in `bootstrap/axiom0/src/link/pe/linker.c` and `AXIOM_PRINT_INT_CODE` in `compiler/link/import.ax` in lockstep: increased stack frame allocation from `0x30` to `0x50` (`sub rsp, 0x50` / `add rsp, 0x50`, maintaining 16-byte stack alignment after 3 pushes + 8-byte return address) and moved the digit buffer end to `lea rdi, [rsp + 0x48]`, keeping all formatted digits (`[rsp + 0x34 .. 0x48]`) strictly above the `[rsp + 0x00 .. 0x2F]` Win64 shadow space + 5th stack argument slot.

### 5. Selfhost Bundles, `known_divergent.txt` Shrink, and Proof for Remaining Array-Indexing Entries
- Updated `tests/selfhost/link/qa_pe_linker_diff.ax.in` expected PE32+ words and regenerated selfhost bundles for `isel`, `link`, `backend`, `driver`, and `obj_link_driver`.
- Updated `tests/selfhost/obj_link_driver/known_divergent.txt`:
  - Removed 8 XPASS entries that are now 100% byte-identical between `axiom0` and `axiomc`:
    - `tests/run/closure/capture_modes.ax`
    - `tests/run/closure/closure_types.ax`
    - `tests/run/closure/qa_mixed_captures.ax`
    - `tests/run/closure/qa_move_capture.ax`
    - `tests/run/for/test_range_standalone.ax`
    - `tests/run/mono/qa_test_basic.ax`
    - `tests/run/native_p7/qa_closure_capture.ax`
    - `tests/run/pattern/qa_destructure.ax`
  - Upgraded 4 entries from `no-image`/`different-behaviour` to `same-behaviour`:
    - `tests/run/closure/syntax.ax`
    - `tests/run/comptime/qa_table_struct_str.ax`
    - `tests/run/comptime/table_str.ax`
    - `tests/run/native_const/qa_table_str_empty_and_multitables.ax`
- **Evidence for why the 5 `[N]T` array-indexing files (`array_basics.ax`, `qa_nested_arrays.ax`, `qa_table_struct_str.ax`, `table_str.ax`, `qa_table_str_empty_and_multitables.ax`) still differ in `.text` bytes (MIR builder outside `T154`'s `paths:`)**:
  - Comparing `objdump -s -r -t --section=.rdata` between `axiom0 build --emit=obj` and `axiomc build --emit=obj` on all 5 files (`array_basics.ax`, `qa_nested_arrays.ax`, `qa_table_struct_str.ax`, `table_str.ax`, and `qa_table_str_empty_and_multitables.ax`) confirms **zero differences** — the `.rdata` section bytes, `IMAGE_REL_AMD64_ADDR64` relocations, and `.Lconst_*` / `.Lconst_*.str.*` symbols are 100% byte-identical between `axiom0` and `axiomc`.
  - Furthermore, all 5 files now execute with identical exit code and stdout (`same-behaviour`).
  - Their `.text` section bytes differ solely because `bootstrap/axiom0/src/mir/build/builder.c` and `compiler/mir/builder.ax` (owned by `T153`, outside `T154`'s `paths:`) emit different MIR local counts for `AX_HIR_EXPR_INDEX` (`arr[idx]`):
    1. In `bootstrap/axiom0/src/mir/build/builder.c:914-960`, array bounds-check lowering unconditionally allocates an extra `t_usize` cast temporary `u_idx` (`_8 = copy _5 as type#15; _7 = copy _8 < copy _6;`), whereas `compiler/mir/builder.ax` omits the redundant cast temporary when the index operand already has type `usize` (`_7 = copy _5 < copy _6;`).
    2. In `bootstrap/axiom0/src/mir/build/builder.c:617-639`, `build_place` on `AX_HIR_EXPR_PATH` for an `AX_CONST_AGGREGATE` (`KEYWORDS[0]`, `KEYWORDS[1]`, ...) caches the `AX_MIR_LOCAL_CONST` local in `b->var_map` on first use (`_4 = const 0` in `bb0`), whereas `compiler/mir/builder.ax` allocates a fresh `MIR_LOCAL_CONST` local (`_4`, `_12`, `_20`, ...) per `HIR_EXPR_PATH` occurrence.
    3. Because each MIR local maps 1-to-1 to a LIR stack slot (`slot0..slotN`), the differing MIR local count shifts the stack frame size (`sub rsp, ...`) and `[rbp - disp]` displacements in `.text`.

## Verification
- `python tools/archcheck.py`: `192 files scanned, 0 violations`.
- `cmake --build build-snap-T154/build --clean-first`: 0 warnings, 0 errors.
- `python tools/axtest.py --compiler build-snap-T154/build/axiom0.exe --root build-snap-T154 -j 1` across:
  - `parity/backend`: 6/6 PASS (`const_table_str.ax`, `narrow_negative.ax` in `interp`, `native`, `native-O1`).
  - `bundles_current`: 34/34 PASS.
  - `selfhost/isel`: 13/13 PASS.
  - `selfhost/link`: 9/9 PASS.
  - `selfhost/backend`: 17/17 PASS.
  - `selfhost/driver`: 17/17 PASS.
  - `selfhost/obj_link_driver`: 7/7 PASS (including `axiomc_e2e.test`: `programs=500 equal=419 known_divergent=81`).
  - `mc/`, `lir/`, `link/`, `opt/`, `driver/`: 175/175 PASS (including `tests/link/objdump_validate.test`).
  - `run/{array,pattern,struct,closure,comptime,native_const,method,native_str,str,parity}`: 210/210 PASS.

## Files changed
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/link/pe/linker.c
- bootstrap/axiom0/src/target/x64/isel/isel.c
- compiler/backend/session.ax
- compiler/driver/pipeline.ax
- compiler/link/import.ax
- compiler/link/pe.ax
- compiler/target/x64/isel.ax
- tests/run/parity/backend/const_table_str.ax
- tests/run/parity/backend/narrow_negative.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_linker_diff.ax.in
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax

STATUS: COMPLETE round=0
