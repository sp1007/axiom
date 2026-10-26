# T148 Report — `axiomc` `build` Path and `inspect` Lowering Call ABI Parity (`AX0-FIX-06`)

## Summary

Fixed `AX0-FIX-06` so that `axiomc`'s `build` pipeline (`build`, `build --emit=obj`) and both compilers' `inspect --emit=lir|mi|mc|obj` stages run drop elaboration, resolve callee `MIR_CONST_FN` function types on every MIR body, and pass each item's `fn_ty` (with a `MIR_LOCAL_ARG` fallback when `item_types` has no entry, e.g. for monomorphized or synthetic functions) to `lir_lower` and `lir_lower_abi`.

Key changes:
1. **`compiler/backend/session.ax` & `compiler/backend/mod.ax`**:
   - Added and exported `backend_resolve_body_call_types` and `backend_resolve_item_fn_ty` (including a `MIR_LOCAL_ARG` fallback matching `bootstrap/axiom0/src/driver/build.c`).
   - Updated `session_compile_and_emit_lir`, `session_emit_mi_from_hir`, `session_emit_mc_from_hir`, `session_emit_mi_file`, `session_emit_mc_file`, and `session_emit_objmodel_hir` to run drop elaboration (`run_drop_elab = true`), resolve callee `MIR_CONST_FN` function types, and pass `fn_ty` to `lir_lower_ext` and `lir_lower_abi_in_arena`.
2. **`compiler/driver/pipeline.ax`**:
   - Updated `emit_lir_stage`, `emit_mi_stage`, `emit_mc_stage`, and `emit_backend_objmodel` to run drop elaboration (`run_drop_elab = true`), call `backend_resolve_body_call_types`, and pass `backend_resolve_item_fn_ty` to `lir_lower_ext` and `lir_lower_abi_in_arena`.
3. **`compiler/lir/builder.ax`**:
   - Aligned `MIR_TERM_CALL` return-type and void-return handling with `bootstrap/axiom0/src/lir/lower.c`: when `has_fn_ty` is true, `ret_ty` is taken from `(*fn_ty).fn.ret_type` instead of `body.locals[dest_id].ty` (which is `void` when a call's return value is discarded, such as `let _ = prelude_loaded()`), and `is_ret_void` checks `(ret_ty_ptr as usize) == 0 || (*ret_ty_ptr).kind == TY_VOID`.
4. **`bootstrap/axiom0/src/driver/emit_lir.c`, `emit_mi.c`, `emit_mc.c`, `emit_obj.c`**:
   - Switched `emit_lir.c`, `emit_mi.c`, and `emit_mc.c` from `ax_mir_build` to `ax_pipeline_get_mir(item)` so drop elaboration runs on `inspect --emit=lir|mi|mc`.
   - Added `resolve_mir_call_types` and `resolve_item_fn_ty` (with `AX_MIR_LOCAL_ARG` fallback) to `emit_lir.c`, `emit_mi.c`, `emit_mc.c`, and `emit_obj.c`, passing `fn_ty` to `ax_lir_lower` and `ax_lir_lower_abi`.
   - Added `AX_X64_MI_SHR` and `_rm` forms of `AND`/`OR`/`XOR` to `encode_mi_to_sec` in `emit_obj.c` to match `build.c` and `compiler/target/x64/frame.ax`.
5. **Regression Test & Selfhost Test Bundles**:
   - Added `tests/run/parity/build_abi/drop_reads_self.ax` (`modes: interp native`) with hand-derived `// stdout:` testing destructors (`impl Drop for ...`) that read and print scalar fields of `self` (`OneField`, `TwoWidths`, parameter drop, temporary drop, and block-scope drop).
   - Regenerated all affected selfhost bundles (`tests/selfhost/abi/*`, `tests/selfhost/lir/*`, `tests/selfhost/backend/*`, `tests/selfhost/driver/*`, `tests/selfhost/obj_link_driver/*`).

## Files changed

- `bootstrap/axiom0/src/driver/emit_lir.c`
- `bootstrap/axiom0/src/driver/emit_mc.c`
- `bootstrap/axiom0/src/driver/emit_mi.c`
- `bootstrap/axiom0/src/driver/emit_obj.c`
- `compiler/backend/mod.ax`
- `compiler/backend/session.ax`
- `compiler/driver/pipeline.ax`
- `compiler/lir/builder.ax`
- `tests/run/parity/build_abi/drop_reads_self.ax`
- `tests/selfhost/abi/qa_abi_lir_lower.ax`
- `tests/selfhost/backend/harness_backend_diff_lir.ax.in`
- `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`
- `tests/selfhost/backend/harness_backend_unit.ax.in`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_a.ax`
- `tests/selfhost/lir/qa_lir_from_ax_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_c.ax`
- `tests/selfhost/lir/qa_lir_from_ax_d.ax`
- `tests/selfhost/lir/qa_lir_from_ax_e.ax`
- `tests/selfhost/lir/qa_lir_from_mir.ax`
- `tests/selfhost/lir/qa_lir_seam_edge.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`

## Verification

### 1. Build & Architecture Verification
- `cmake --build build-snap-T148/build --clean-first` (GCC `Debug`): **0 warnings, 0 errors**.
- `python tools/archcheck.py`: **192 files scanned, 0 violations**.

### 2. Test Suites
- `tests/run/parity/build_abi/drop_reads_self.ax`:
  - `python tools/axtest.py --compiler build-snap-T148/build/axiom0.exe --suite run --filter parity/build_abi`: **3/3 PASS** (`[interp]`, `[native]`, `[native-O1]`).
  - `axiom0 build --emit=obj` vs `axiomc build --emit=obj`: **byte-identical** (`8706 == 8706` bytes).
- `tests/run/drop/*`:
  - `python tools/axtest.py --compiler build-snap-T148/build/axiom0.exe --suite run --filter drop`: **69/69 PASS** (`[interp]`, `[native]`, `[native-O1]`).
  - All 21 non-divergent `tests/run/drop/*` cases produce **100% byte-identical `.obj` files** between `axiom0` and `axiomc`.
- Selfhost test suites:
  - `bundles_current.test`: **34/34 PASS**
  - `selfhost/obj_link_driver` (including `axiomc_e2e.test`): **9/9 PASS**
  - `selfhost/backend`: **17/17 PASS**
  - `selfhost/abi`: **10/10 PASS**
  - `selfhost/driver`: **14/14 PASS**
  - `selfhost/lir`: **22/22 PASS**

### 3. `known_divergent.txt` & Evidence for Remaining `tests/run/drop/*` Entries (`T149`)
Every `tests/run/drop/*` entry not listed in `known_divergent.txt` is 100% byte-identical between `axiom0` and `axiomc`. The only two `tests/run/drop/*` entries in `tests/selfhost/obj_link_driver/known_divergent.txt` (`tests/run/drop/array_elem_assign_drop.ax` and `tests/run/drop/qa_t141_r1_assign_places.ax`) already have identical `S$drop` function bodies and identical `S$drop` call ABI in `.text`, and differ only because of `T149` (`compiler/mir/builder.ax` array index cast temporaries, outside `T148`'s `paths:`):

1. **`inspect --emit=mir` diff on `tests/run/drop/array_elem_assign_drop.ax` (`ax_main`)**:
   ```diff
            _8 = const 1;
            _9 = const 3;
   -        _11 = copy _8 as type#15;
   -        _10 = copy _11 < copy _9;
   +        _10 = copy _8 < copy _9;
            assert(copy _10 == true, "index out of bounds") -> [return: bb1, unwind: bb2];
   ```
2. **`inspect --emit=mir` diff on `tests/run/drop/qa_t141_r1_assign_places.ax` (`ax_main`)**:
   ```diff
        bb2: {
            _8 = const 2;
   -        _10 = copy _7 as type#15;
   -        _9 = copy _10 < copy _8;
   +        _9 = copy _7 < copy _8;
            assert(copy _9 == true, "index out of bounds") -> [return: bb3, unwind: bb4];
        }
   ```
3. **`inspect --emit=lir` and `objdump -d -r` on `<S$drop>` and its call sites**:
   - Both `axiom0` and `axiomc` emit identical LIR call sequences (`abi_arg 0, v...; call S$drop; v... = abi_result 0;`) and identical `<S$drop>` machine code in `.text` (passing `self: mut_view<S>` in `%rcx` at `13: 48 89 4d a8 mov %rcx,-0x58(%rbp)` and reading `(*self).v` before calling `emit_digit`).


STATUS: COMPLETE round=0
