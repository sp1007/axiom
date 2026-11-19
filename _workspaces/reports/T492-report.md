# T492 report

## Summary
Fixed trait lookup through `use … as Alias` imports (including std traits, user traits, chained `pub use … as` re-exports, and aliases colliding with another trait's name) and retired the `10007` / `10008` / `10009` sentinel `SymbolId` comparisons in `axiomc` (ADR-0043 §2, INV-BOOT-005, REQ-RES-060).

### Root cause & fix
1. **Alias trait lookup (`compiler/hir/hir.ax`, `compiler/hir/lower.ax`, `compiler/traits/solver.ax`)**:
   - A trait reference in HIR carries the trait's collection `SymbolId` while the `HIR_ITEM_TRAIT` node itself was rebound to `Self` during the body pass, so `find_trait_item` falls back to name + defining-module lookup. Previously it read `HirPath.name` (the use-site alias spelling such as `StdOrd` or `MyOrd`), failing with `AX_TYPE_UNKNOWN_FIELD` when looking up trait methods.
   - Added `HirPath.def_name: StrView` in `compiler/hir/hir.ax`.
   - In `compiler/hir/lower.ax` (`lower_path_domain`), extracted the defining item's own name from `resolve_symbol_canonical_name` (stripping the `def_mod + "."` prefix when `def_mod` is non-empty) and copied it into the HIR arena as `dst.def_name`. Also added the `n >= 3` bounds guard before inspecting `mp.ptr[0..2]` for `"std"` and initialized `def_dom`/`def_mod`/`def_name` on empty-segment paths.
   - In `compiler/traits/solver.ax`:
     - `hir_type_path_name_sv` and `find_trait_item` prefer `HirPath.def_name` over the spelled site name whenever `def_name` is present.
     - `impl_trait_matches_target` guards the name fallback with `(tr_sym_v == 0u32 || impl_tr_sym_v == 0u32)` so two distinct traits with the same name never cross-match when both carry resolved symbols; `impl_matches_receiver` and `type_matches_impl_self_exact` similarly guard their name fallback against mismatched non-synthetic symbols.
     - `scope_item_bounds_imply_trait` and `ty_param_allows_trait` recognize `TC_SELF_PARAM_INDEX` (`0xFFFFFF00u32`) in addition to `0xFFFFFFFFu32` so trait default methods calling supertrait methods on `Self` resolve through aliased supertrait bounds.
     - `find_method_in_scope` deduplicates when one match is an instantiated trait default method (`thir.expr_methods` entry at `(ptr | 2)`) and another match is the same trait's raw default method reached through a subtrait impl (`m_body == f_body && m_is_inst != f_is_inst`), preferring the instantiated copy without comparing `SymbolId` values and preserving `find_method`'s ambiguity contract in `tests/selfhost/traits/qa_traits_solver_mono.ax`.
2. **Retiring `10007` / `10008` / `10009` sentinels**:
   - `compiler/hir/lower.ax` (`lower_path_into`): removed `dst.symbol.v = 10009u32;` for unresolved `Future` (when std is not loaded); `dst.symbol.v` stays `0u32` and `dst.def_dom = 2u8` records the std domain explicitly. Updated `find_trait_item` in `compiler/traits/solver.ax` so `site.path.def_dom` is consulted even when `sym.v == 0u32`.
   - `compiler/traits/solver.ax`: removed all `== 10007u32` / `== 10008u32` comparisons in `trait_auto_kind` and `impl_trait_matches_target`, and replaced all recursive `10007u32` / `10008u32` arguments in `type_satisfies_auto_trait` and `find_auto_trait_failure_reason` with `0u32` (since `auto_kind == 1u8` / `2u8` dispatches by `auto_kind` and trait name without reading `tr_sym_v`).
   - `git grep -n -E "1000[789]" -- compiler/` now finds **zero** `SymbolId` comparisons anywhere in `compiler/`. Ten call-site argument literals remain outside T492's `paths`/`locks`:
     - `compiler/driver/pipeline.ax`: lines 1554, 1571 (`10007u32` passed alongside `auto_kind = 1u8` and `send_sv` to `type_satisfies_auto_trait` / `emit_conc_bound_diag`).
     - `compiler/types/typeck.ax`: lines 10688, 10734, 10748, 10902, 10918, 10942, 11390 (`10007u32` with `auto_kind = 1u8`, `send_sv`) and line 11403 (`10008u32` with `auto_kind = 2u8`, `share_sv`).
     - None of these are compared against any `SymbolId`: inside `solver.ax`, `auto_kind == 1u8` / `2u8` ignores `tr_sym_v` completely. Both files are outside T492's `paths`/`locks` (`typeck.ax` is owned by concurrent task `T444`).
3. **Why `axiom0` does not need an AX0-FIX task**:
   - Checked `bootstrap/axiom0/src/types/typeck.c` and `bootstrap/axiom0/src/traits/solver.c`: `axiom0` has no `10007`/`10008`/`10009` sentinels, does not auto-load `std`, matches trait bounds directly by `symbol.v`, and scans all `AX_HIR_ITEM_TRAIT` items on generic-parameter method calls without `axiomc`'s `ty_param_allows_trait` / `find_trait_item` path. `axiom0` is frozen for bootstrapping only and does not exhibit the `axiomc` `AX_TYPE_UNKNOWN_FIELD` bug.

## Files changed
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- compiler/traits/solver.ax
- tests/run/trait_use_alias/alias_collide_other_trait_name.ax
- tests/run/trait_use_alias/std_and_user_alias_bounds.ax
- tests/run/trait_use_alias/unsatisfied_alias_bound_neg.ax

## Tests
All builds and test runs executed in refreshed snapshot `build-snap-T492` (HEAD `a3d22928e491` + T492's 6 files, 36 selfhost bundle generators / 154 files regenerated).

1. **Stage 1–3 self-host build & fixed-point (`python tools/build_axiomc.py --out build --stage 3`)**:
   - `STAGE1 OK`: `axiomc1.exe` (26 894 336 bytes, `sha256=f459a7c9d8fd0ef5`, 98.24s)
   - `STAGE2 (O1) OK`: `axiomc2.exe` (8 308 224 bytes, `sha256=cdb834f954c66e0d`, 236.89s)
   - `STAGE3 (O1) OK`: `axiomc3.exe` (8 308 224 bytes, `sha256=cdb834f954c66e0d`, 107.25s)
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == cdb834f954c66e0d9a6e6a758e50a8829013d28804cab3efb681e5e12a9a3698`
2. **New regression tests (`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/trait_use_alias`)**:
   - `TOTAL 7 PASS 7 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
   - Covers: alias of std trait (`std.core.cmp.Ord as StdOrd`, `StdBaseOrd`, `Eq`), alias of user trait (`tr.Ord as MyOrd`, `Scale as MyScale`, `sub.Eq as MyEq`, `sub.Sorted as MySorted`), alias colliding with another trait's name (`use alpha.First as Second`, `use beta.Second as First`, `use std.core.cmp.Ord as Eq`), generic bounds (inline + `where` + generic impls), `impl Alias for T`, supertrait lists, chained `pub use … as` re-exports, and negative test `unsatisfied_alias_bound_neg.ax` (`AX_TRAIT_UNSATISFIED_BOUND` on both supertrait and generic call).
3. **Mutation proof (`std_and_user_alias_bounds.ax`)**:
   - Changed expected stdout `std -1 1 0` → `std -1 1 1` in the snapshot copy and ran `axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/trait_use_alias/std_and_user_alias_bounds`:
   - `TOTAL 3 PASS 0 FAIL 3` — failed in all three modes `[interp]`, `[native]`, `[native-O1]` (`stdout differs at byte 9`). Restored and verified byte-identical (`4405` bytes).
4. **T164 regression suite (`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/symbol_id_space`)**:
   - `TOTAL 31 PASS 31 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
5. **Selfhost traits unit test (`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter selfhost/traits/qa_traits_solver_mono`)**:
   - `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
6. **Per-task gate (`python tools/taskgate.py --task T492 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`)**:
   - `own`: 3 ids, 7 results, 7 PASS, 0 FAIL
   - `affected`: 163 ids, 364 results, 363 PASS, 0 FAIL, 1 SKIP
   - `smoke`: 30 ids, 47 results, 47 PASS, 0 FAIL
   - `total (dedup)`: 191 ids, `TOTAL 409 PASS 408 FAIL 0 SKIP 1 XFAIL 0`, `Failing ids: none`, `BASELINE OK`
   - `WEAK-NATIVE: 15 in the run; 0 in the task's own/changed tests`
   - `archcheck: clean (exit 0)` (229 files scanned, 0 violations)
   - `TASKGATE T492 exit=0`
7. **Sentinel audit (`git grep -n -E "1000[789]" -- compiler/`)**:
   - 0 symbol-id comparisons remaining; only the 10 unused call-site arguments in `compiler/driver/pipeline.ax` (2) and `compiler/types/typeck.ax` (8) listed above.

## Spec deviations
none

## Follow-ups
- Cleanup: replace the remaining unused `10007u32` / `10008u32` call-site arguments in `compiler/driver/pipeline.ax` (lines 1554, 1571) and `compiler/types/typeck.ax` (lines 10688, 10734, 10748, 10902, 10918, 10942, 11390, 11403) with `0u32` (or drop the redundant `tr_sym_v` parameter for Send/Share checks) once `T444` finishes on `compiler/types/typeck.ax`.

STATUS: COMPLETE round=0
