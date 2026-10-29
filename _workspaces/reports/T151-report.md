# T151 report — Port typeck parity: generics and the typeck/MIR stack overflow

## Summary
- **Eliminated all `0xC00000FD` stack-overflow crashes in `axiomc`** (`0` crashes across all `518` corpus programs in `axiomc_e2e`). Diagnosed the unbounded mutual recursion in `compiler/mir/builder.ax` (`mir_build_expr` <-> `mb_build_expr_as_operand` on range sub-slice `HIR_EXPR_INDEX` and `Index` operator-trait `HIR_EXPR_INDEX` nodes) and lowered both forms directly without re-entering `mir_build_expr` on the same `HirExpr`.
- **Generic function & struct/enum monomorphisation and MIR lowering (`compiler/mir/builder.ax`, `compiler/traits/mono.ax`, `compiler/hir/{hir,lower}.ax`, `compiler/types/types.ax`):**
  - Added HIR deep-cloning + type/symbol instantiation (`mb_clone_item` / `mb_prepare_mono`) aligned with `bootstrap/axiom0/src/mir/mir_build.c`: pre-scans generic call sites, generic struct literals, generic enum variant paths, impl blocks (`Impl<T>` and `Impl<Trait> for Type<T>`), operator traits (`Add`/`Sub`/`Mul`/`Div`/`Rem`/`BitAnd`/`BitOr`/`BitXor`/`Shl`/`Shr`, `PartialEq`/`PartialOrd`, `Neg`/`Not`, `Index`), `IntoIterator`/`Iterator` for `for` loops, `?` (`HIR_EXPR_TRY` on `Option<T>` / `Result<T, E>`), and generic `Drop` glue (`drop_in_place$<MangledType>`) in topological dependency order, allocating fresh post-resolve `SymbolId`s seeded from `rmap.next_symbol_v` (`HirItem.resolve_next_sym_v`) so symbol numbering matches `axiom0`.
  - Matched `mono_find_instance` (`compiler/traits/mono.ax`) by `orig.symbol` in addition to `orig` pointer identity so cloned HIR call sites deduplicate against existing `MonoInstance` entries (`mono/qa_dedup_mangling.ax`).
  - Lowered binary operator traits (`mb_build_op_trait_binary`), unary operator traits (`Neg`/`Not`), `Index` trait calls (`mb_build_index_special_expr`), and range sub-slices (`mb_build_range_subslice_lvalue`, supporting `a..b`, `a..=b`, `a..`, `..b`, `..=b`, `..` with `RangeBounds` checks and slice fat-pointer construction) to match `axiom0`'s MIR/LIR/COFF output byte-for-byte.
  - Outlined heavy `MirRvalue`/`MirOperand` lowering helpers (`mb_build_range_subslice_lvalue`, `mb_build_op_trait_binary`, `mb_build_index_special_expr`) out of recursive `mir_build_lvalue` / `mb_build_binary_expr` / `mir_build_expr` frames so native selfhost bundles fit comfortably within the default 1 MB Win64 stack.
- **Resolver & THIR dump parity (`compiler/resolve/resolver.ax`, `compiler/types/typeck.ax`):**
  - Matched `bootstrap/axiom0/src/resolve/resolve.c:552-555` in `resolver.ax` (`resolve_type` only recurses on `TYPE_VIEW || TYPE_PTR`, leaving `TYPE_SLICE` element path lookup to `typeck` as in `axiom0`), eliminating `resolved`/`hir`/`thir` stage divergence on slice view signatures.
  - Matched `axiom0` THIR printer (`emit_thir` in `compiler/types/typeck.ax`) on generic function calls (emitting uninstantiated `TY_FN` callee types on inferred generic `ExprPath` callees), integer array-length literals in `HIR_TYPE_ARRAY`, original unmangled `HirItem` names (via `thir_get_orig_item_name`), skipping synthetic monomorphised clones (`span.file.v == 0xFFFFFFFE`), and `AX_TYPE_UNREACHABLE` diagnostic text (`interp`-safe `[21]u8` table).
- **Selfhost interp bundler fix (`tests/selfhost/interp/gen_interp_tests.py`):**
  - Rewrote `use std.core.host.` -> `use host_intrinsics.` in `bundle_one` on `main_src` (matching `bundle_common.py`) so symbol growth past `SymbolId` 10,000 in `qa_interp_exec_a.ax` does not collide with `axiom0`'s internal `std` symbol table (`>= 10000`).

## Stack overflow root cause (`0xC00000FD`)
- **Minimal reproducers:**
  1. Range sub-slice:
     ```axiom
     fn main() {
         let a = [1, 2];
         let _s = a[0..1];
     }
     ```
  2. `Index` operator trait:
     ```axiom
     struct B { v: i32 }
     impl Index<usize> for B {
         type Output = i32;
         fn index(self: view<B>, _i: usize) -> i32 { self.v }
     }
     fn main() -> i32 {
         let b = B { v: 0 };
         b[0]
     }
     ```
- **Exact call cycle:**
  - Note that `axiomc`'s pipeline runs MIR construction (`mir_build_module`) before `STAGE_OWN` / `build` (and during `inspect` stages past `thir`, or whenever driver phases invoke ownership/MIR). In `HEAD:compiler/mir/builder.ax`:
    1. `mir_build_expr` checked `if ek == HIR_EXPR_LITERAL || ... || ek == HIR_EXPR_INDEX` and unconditionally delegated `expr` to `mb_build_expr_as_operand(b, expr, out_op)`.
    2. Inside `mb_build_expr_as_operand`:
       - When `(*expr).index_arg` had `kind == HIR_EXPR_RANGE` (all slice sub-range programs and array `for` loops whose std iterator uses sub-slicing), `(*idx_arg).kind != HIR_EXPR_RANGE` evaluated to `false`, leaving `is_lval_cand = false`.
       - When `thir_get_expr_method(b.thir, expr)` was non-null (`Index` operator trait in `tests/run/trait2/test_ops.ax`), the `vp == 0 && mp == 0` lvalue fast-path was skipped.
    3. Both paths fell through to the fallback at the bottom of `mb_build_expr_as_operand`, which allocated a temporary `tmp_pl` and called `mir_build_expr(b, expr, tmp_pl, true)` on the **exact same `HIR_EXPR_INDEX` pointer**, mutually recursing `mir_build_expr -> mb_build_expr_as_operand -> mir_build_expr` without progress until exhausting the 64 MB stack (`0xC00000FD`).
  - **Fix:** `mb_build_index_special_expr` handles `Index` trait calls (emitting a `MIR_TERM_CALL` to the resolved `index` method with auto-borrow of `self` when required) and `HIR_EXPR_RANGE` sub-slices (delegating directly to `mir_build_lvalue` -> `mb_build_range_subslice_lvalue` and borrowing the resulting sub-slice place) before `mir_build_expr` ever enters `mb_build_expr_as_operand`; `mb_build_expr_as_operand` only treats plain non-range, non-method `HIR_EXPR_INDEX` as an lvalue candidate.

## Parity registry (`known_divergent.txt`)
Shrank `tests/selfhost/obj_link_driver/known_divergent.txt` from **23** entries (at `HEAD 3a369f5`) to **7** entries (**16 removed**, **2 updated in place**, **0 added**). All 22 programs from the T151 plan table (14 still in `known_divergent.txt` at `HEAD` plus 8 `mono/*` and `result/*` entries already removed prior to `HEAD`), plus 2 bonus entries (`closure/fn_traits.ax`, `trait2/test_derive.ax`) and `native_enum/01-simple.ax`, are now byte-for-byte `EQUAL` under `axiomc_e2e_oracle.py` AND byte-for-byte identical under `inspect --emit=thir`:

- **Removed from `known_divergent.txt` (16):**
  - `tests/run/closure/fn_traits.ax`
  - `tests/run/for/test_for_array.ax`
  - `tests/run/for/test_for_custom_iter.ax`
  - `tests/run/generic/qa_basic_fn.ax`
  - `tests/run/generic/qa_pair.ax`
  - `tests/run/mono/qa_dedup_mangling.ax`
  - `tests/run/native_enum/01-simple.ax`
  - `tests/run/slice/disjoint_split.ax`
  - `tests/run/slice/qa_slice_bounds_panic.ax`
  - `tests/run/slice/qa_slice_chained_panic.ax`
  - `tests/run/slice/qa_slice_inverted_panic.ax`
  - `tests/run/slice/qa_slice_len_empty.ax`
  - `tests/run/slice/qa_slice_open_ranges.ax`
  - `tests/run/slice/sub_range.ax`
  - `tests/run/trait2/test_derive.ax`
  - `tests/run/trait2/test_ops.ax`
- **Updated in place (2):**
  - `tests/run/closure/generic_fns.ax`: `thir	different-behaviour` -> `mir	same-behaviour` (generic instantiation and THIR now match `axiom0`, and the compiled executable now runs identically to `axiom0`; residual byte diff starts at `mir` closure lowering, out of scope -> `T152`).
  - `tests/run/trait2/test_default_override.ax`: `mir	different-behaviour` -> `mir	no-image` (THIR matches; residual failure is trait default/override method symbol mangling in `mir`, out of scope -> `T153`).

## Tests
- Added 3 canonical Axiom parity tests (`modes: interp native`, hand-derived `stdout` and `exit`):
  - `tests/run/parity/generics/generic_fn.ax`: `id<T>` called at `i32` (`42`) and `bool` (`true` -> `1`), two-parameter `pick_first<A, B>` called at `(i32, bool)` (`17`) and `(i64, i32)` (`500`), exit `0`.
  - `tests/run/parity/generics/generic_struct_enum.ax`: `Pair<i32, i32> { first: 12, second: 30 }` sum (`42`), `Option<i32>.Some(7)` (`7`) and `Option<i32>.None` (`-1`) matched, and `Result<i32, i32>` `?` propagation (`step_ok(10)?` = `15` -> `step_err(15 + 8)?` propagating `Err(23)` as exit code `23`).
  - `tests/run/parity/generics/range_slice.ax`: `s[1..3]` on `[10, 20, 30, 40, 50]` printing `len(sub)` = `2` and `sub[0] + sub[1]` = `50`, plus `for x in [1, 2, 3]` sum = `6`, exit `0`.
- Verified byte-for-byte `inspect --emit=thir` equality (`0` diffs across all `28` target programs: the 16 newly-`EQUAL` registry programs, the remaining 4 `mono/*` and 5 `result/*` programs, and the 3 new `tests/run/parity/generics/*.ax` tests).
- Regenerated all 92 affected selfhost bundles across all 34 `tests/selfhost/**/bundles_current.test` suites (`--check` clean on all 34).

## Spec deviations
none

## Follow-ups
The 7 remaining entries in `tests/selfhost/obj_link_driver/known_divergent.txt` belong entirely to existing planned tasks:
- **T152 (Closures and fn pointers):**
  - `tests/run/closure/fn_pointers.ax` (`thir	no-image`)
  - `tests/run/closure/generic_fns.ax` (`mir	same-behaviour`)
  - `tests/run/closure/qa_fn_ptr_args.ax` (`thir	no-image`)
  - `tests/run/closure/syntax.ax` (`mir	same-behaviour`)
- **T153 (Trait method symbols, default methods, and associated types):**
  - `tests/run/trait2/test_assoc_items.ax` (`resolved	no-image`)
  - `tests/run/trait2/test_default_method.ax` (`mir	no-image`)
  - `tests/run/trait2/test_default_override.ax` (`mir	no-image`)

## Verification
- Build in `build-snap-T151/build`: `ninja -C build-snap-T151/build` clean (0 warnings).
- Architecture boundary check: `python tools/archcheck.py` -> `192 files scanned, 0 violations`.
- End-to-end differential oracle (`selfhost/obj_link_driver/axiomc_e2e.test`):
  `AXIOMC-E2E programs=518 equal=511 known_divergent=7 built=2036 rejected=8 obj_equal=1020 exe_equal=1016 run_equal=510` (`0` `0xC00000FD` crashes across the entire 518-program corpus).
- Full test suite in `build-snap-T151` (`python build-snap-T151/tools/axtest.py --compiler build-snap-T151/build/axiom0.exe -j 1`):
  `TOTAL 2844 PASS 2844 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 165`).

## Files changed
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- compiler/mir/builder.ax
- compiler/resolve/resolver.ax
- compiler/traits/mono.ax
- compiler/types/typeck.ax
- compiler/types/types.ax
- tests/run/parity/generics/generic_fn.ax
- tests/run/parity/generics/generic_struct_enum.ax
- tests/run/parity/generics/range_slice.ax
- tests/selfhost/abi/qa_abi_boundary_seam.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/abi/qa_abi_win64_classify.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/cap/qa_own_cap.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
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
- tests/selfhost/hir/qa_hir_corpus.ax
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax
- tests/selfhost/interp/gen_interp_tests.py
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own/qa_own_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_a.ax
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/types/qa_types_exhaust.ax
- tests/selfhost/types/qa_types_layout.ax
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

STATUS: COMPLETE round=0
