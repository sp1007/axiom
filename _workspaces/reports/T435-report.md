# T435 Report: Baseline fix — selfhost drop bundles (d01..d12) independent of prelude contents

## Summary

Fixed `tests/selfhost/drop/qa_drop_d01.ax` .. `qa_drop_d12.ax` (11 bundles), `tests/selfhost/drop/bundles_current.test`, and `tests/selfhost/drop/drop_oracle.test` so that all 13 tests in `selfhost/drop/` pass in `interp`, `native`, and `native-O1` (`WEAK-NATIVE 0`) and are hermetically isolated from future growth of the live `std/core/prelude.ax` (`ADR-0041 §2 D2`, `ADR-0042 §1`).

## Root Cause Diagnosis

1. **Bundle runtime mismatch (`exit 300` on `qa_drop_d01` .. `qa_drop_d12`)**:
   - Inspecting the actual vs expected MIR across all 12 fixtures (`d01_scope_exit` .. `d12_scalar_destructor`) confirmed **zero** MIR builder or drop elaboration differences; every diff was a uniform `+4` shift on user struct/enum `TypeId`s (`type#17` -> `type#21`, `type#18` -> `type#22`, etc.).
   - `tests/selfhost/drop/harness_main.ax.in` calls `session_append_std_prelude` (`compiler/resolve_hir/session.ax`), which appends the fixed in-memory `STD_CORE_DATA` (`<std>/core/option.ax`, `<std>/core/result.ax`, `<std>/core/prelude.ax`, `<std>/core/host.ax`) to the **end** of `parse_res.ast.items`.
   - In C `axiom0` (`bootstrap/axiom0/src/types/typeck.c`, which generated `fixtures/*.pre.mir` and `*.drop.mir`), Pass 1a iterates `hir_file.items` in a single pass, interning the fixture's user structs/enums first (`type#17 .. type#(16+U)`), followed by `Option<T>` (`2` types) and `Result<T, E>` (`2` types), and then Pass 2 body types (`type#(16+U+5)..`).
   - After commit `84e792c9` (`T429`), `compiler/types/typeck.ax` (`typeck_pass1a`) splits Pass 1a into `Pass 1a (prelude)` (items where `tc_item_is_prelude_or_std` is true, i.e. `module_path` starts with `"std"`) followed by `Pass 1a (user)`. That hoisted `Option<T>` and `Result<T, E>` (`4` types) ahead of the fixture's own structs/enums, shifting user `TypeId`s by `+4` while leaving Pass 2 body `TypeId`s (`U + 4 == 4 + U`) unchanged.
2. **C oracle sensitivity to live `std/core/prelude.ax` (`drop_oracle.test` / `gen_drop_tests.py`)**:
   - `tests/selfhost/drop/gen_drop_tests.py` (`oracle_output`) invoked `ct_selfhost_drop_cdriver_drop_oracle --std-root std`, loading the live P11 `std/core/prelude.ax` (`Poll<T>`, `RawWaker`, `RawWakerVTable`, `Waker`, `Context`, `Future`), which shifted Pass-2 `TypeId`s in `d03`, `d07`, `d08` and triggered an ICE in frozen `axiom0` on `d09_closures.ax`.

## Hermetic Fix & Reuse Pattern for `T441`

1. **Pinned minimal std root for the C oracle (`tests/selfhost/drop/std_minimal/core/*.ax`)**:
   - Added `tests/selfhost/drop/std_minimal/core/{option.ax,result.ax,prelude.ax,host.ax}` (marked `// test: helper` on line 1 so `tools/axtest.py` ignores them during test discovery) matching the fixed `STD_CORE_DATA` table in `compiler/resolve_hir/session.ax`.
   - Updated `tests/selfhost/drop/gen_drop_tests.py` (`oracle_output` and `cmd_goldens`) to pass `--std-root tests/selfhost/drop/std_minimal` instead of `std`.
2. **Pre-typeck prelude `module_path` demotion in `harness_main.ax.in` (`demote_prelude_hir_module_paths`)**:
   - In `tests/selfhost/drop/harness_main.ax.in`, added `demote_prelude_hir_module_paths(view(hir), fid.v)` immediately after `session_lower_hir` and before `session_typeck_into`:
     ```axiom
     fn demote_prelude_hir_module_paths(hir: view<HirFile>, main_fid_v: u32) {
         if main_fid_v == 0u32 {
             return;
         }
         let mut it: *mut HirItem = hir.items;
         while (it as usize) != 0 {
             let it_file = unsafe { (*it).span.file.v };
             if it_file != 0u32 && it_file != main_fid_v {
                 unsafe {
                     (*it).module_path.count = 0;
                 }
             }
             it = unsafe { (*it).next };
         }
     }
     ```
   - Because `session_resolve_ast_into` has already resolved prelude bindings and assigned `10000+` std `SymbolId`s, clearing `module_path.count` on non-main-file `HirItem`s before `session_typeck_into` only affects `tc_item_is_prelude_or_std` in `typeck_pass1a`, restoring single-pass `hir.items` registration order (user structs/enums first, then appended `STD_CORE_DATA` items) while keeping `bytes_equal` 100% byte-for-byte strict across the entire MIR output.
   - **Reuse instructions for `T441`**: Both `tests/selfhost/own_mir_verify/harness_mir_diff.ax.in` (`qa_own_mir_diff_drop_b.ax`) and `tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in` (`qa_interp_opt_diff_mir_b.ax`) use the identical `session_append_std_prelude` -> `session_resolve_ast_into` -> `session_lower_hir` -> `session_typeck_into` pipeline and fail on `m03_aggregates` / `o02_cfg_cleanup` with the exact same `+4` user `TypeId` shift (`type#17` -> `type#21`). Calling `demote_prelude_hir_module_paths(view(hir), fid.v)` before `session_typeck_into` in those two harness templates (and regenerating their bundles) resolves both `T441` failures directly.

## Verification

1. **Oracle & bundle freshness checks**:
   - `python tests/selfhost/drop/gen_drop_tests.py check --oracle build-snap-T435/build/tests/ct_selfhost_drop_cdriver_drop_oracle.exe` -> `OK drop oracle goldens (12 fixtures)` (exit `0`).
   - `python tests/selfhost/drop/gen_drop_tests.py --check` -> all 11 `qa_drop_d*.ax` bundles up to date (exit `0`).
2. **1-byte fixture mutation proof**:
   - Temporarily mutated 1 byte at offset 53 (`type#17` -> `type#18`) in `build-snap-T435/tests/selfhost/drop/fixtures/d01_scope_exit.pre.mir`, regenerated `qa_drop_d01.ax` in `build-snap-T435`, and ran `axtest.py`:
     - `FAIL selfhost/drop/qa_drop_d01.ax [interp]: exit code 300, expected 0`
     - `FAIL selfhost/drop/qa_drop_d01.ax [native]: exit code 300, expected 0`
     - `FAIL selfhost/drop/qa_drop_d01.ax [native-O1]: exit code 300, expected 0`
     - `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0`
   - Restored `build-snap-T435` via `taskctl.py snapshot T435` immediately afterwards.
3. **Full `selfhost/drop/` suite (`interp`, `native`, `native-O1`)**:
   - `python tools/axtest.py --root build-snap-T435 --compiler build-snap-T435/build/axiomc2.exe --build-dir build-snap-T435/build --no-cache -j 2 selfhost/drop/` -> `TOTAL 35 PASS 35 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).

## Files changed

- _workspaces/baseline-failures.txt
- tests/selfhost/drop/gen_drop_tests.py
- tests/selfhost/drop/harness_main.ax.in
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/drop/std_minimal/core/host.ax
- tests/selfhost/drop/std_minimal/core/option.ax
- tests/selfhost/drop/std_minimal/core/prelude.ax
- tests/selfhost/drop/std_minimal/core/result.ax

## Status

STATUS: COMPLETE round=0
