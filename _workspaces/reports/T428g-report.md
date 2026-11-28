# T428g report — typeck type lookup by bare name across modules

## Summary

Fixed cross-module bare-name collisions in `compiler/types/typeck.ax` (`lookup_path_type_by_name`, covering `REQ-TYP-072`, `REQ-MOD-003`, `REQ-MOD-064`):

1. **Bound paths (`path.symbol.v != 0 || path.def_dom != 0`) never reach the bare-name walk**: when a resolver-bound path falls through `lookup_path_type` into `lookup_path_type_by_name`, `lookup_path_type_by_name` selects strictly by `symbol` (or by `def_mod` + `def_name` when `symbol == 0 && def_dom != 0`), computes forward-referenced `fn`/`const`/`static` signatures on demand safely, and immediately emits `AX_NAME_UNRESOLVED` if the bound item cannot denote a type/value in `lookup_path_type_by_name` (e.g., bound `trait` or `module` used in type position).
2. **Unbound paths (`symbol == 0 && def_dom == 0`, e.g., synthetic HIR / lowering sentinels / unbound generic-parameter projections)** retain the bare-name fallback across `fn`, `const`/`static`, `struct`, `enum`, and `type`-alias items (skipping shallow `impl` member clones), **preferring the current module's item** (`tc_current_module_anchor`) and **emitting `AX_NAME_UNRESOLVED`** when multiple distinct non-current modules define the name (eliminating silent first-match selection).
3. Removed the two `T428g` baseline entries (`conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax` and `conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax`) and their comment block from `_workspaces/baseline-failures.txt` (leaving `_workspaces/baseline-failures.txt` with 0 active baseline entries).
4. Added comprehensive multi-mode (`interp`, `native`, `native-O1`, `WEAK-NATIVE 0`) run and compile-fail regression suites under `tests/run/same_name_std_types/` and `tests/modules/same_name_types/`.

## HEAD `31b7dd49` Repro Findings (with T428m Landed, Before `typeck.ax` Edit)

Tested against clean Stage-2 `build-snap-T428g/build/axiomc2.exe` on HEAD `31b7dd49` (`sha256=b5d6246920c373277739751bc94ed886c3f0ff3a6167aaa7ecb5387089286e00`):

- **Already passing on HEAD `31b7dd49` thanks to `T428m` binding generic-argument segments**:
  - `tests/run/same_name_std_types/user_string_with_std_io.ax` (user `struct String` alongside `use std.io.read_to_string`)
  - `tests/run/same_name_std_types/user_io_error_with_std_io.ax` (user `struct IoError` alongside `use std.io.read_to_string`)
  - `tests/run/same_name_std_types/both_std_strings.ax` (`use std.text.string.String` + `use std.io.read_to_string` in one program)
  - `tests/modules/same_name_types/mismatch` (`a.S` assigned to `b.S` -> `AX_TYPE_MISMATCH`)
  - `tests/conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax` and `fiber_in_async_and_threads.ax` (`e11_5_executors`: 28/28 PASS across `interp`, `native`, `native-O1`).
- **Still failing on HEAD `31b7dd49` before the `compiler/types/typeck.ax` fix** (reproduced in `tests/modules/same_name_types/`):
  1. **Forward-referenced bound `const`/`static`/`fn` across modules (`tests/modules/same_name_types/ok`)**:
     `main` imports `use w.N` (`pub const N: usize = 4usize` in module `w`, ordered after `main` in `(*cx.hir).items`), while module `a` (ordered before `main`) defines `pub const N: bool = true`. During Pass 1b signature registration of `fn check_const_buf(buf: [N]u8)`, `lookup_path_type` finds `thir_get_item_type(w.N) == 0` and falls through to `lookup_path_type_by_name` with `path.symbol != 0` (`w.N`). On HEAD `31b7dd49`, `lookup_path_type_by_name` ignored `path.symbol`, walked `(*cx.hir).items` by bare name `"N"`, matched `a.N` (`bool`), and **failed in all 3 modes (`interp`, `native`, `native-O1`) with `error[AX_TYPE_ARRAY_SIZE]`**.
  2. **Bound non-type items (`trait`, `module`) used in type position (`tests/modules/same_name_types/bound_non_type_no_fallback`)**:
     `main` imports `use a.S` (`pub trait S`), `use w.T2` (`pub trait T2`), and module `a` (`use a.mk`), while module `b` defines `pub struct S`, `pub struct T2`, and `pub struct a` (none imported in `main`). When `main` writes `fn bad_trait_as_type(v: S)`, `fn bad_forward_trait_as_type(v: T2)`, and `fn bad_mod_as_type(v: a)`, `lookup_path_type` does not handle `HIR_ITEM_TRAIT` / `HIR_ITEM_MODULE` and falls through to `lookup_path_type_by_name` with `path.symbol != 0`. On HEAD `31b7dd49`, `lookup_path_type_by_name` fell through to the bare-name scan and **silently compiled (`rc=0`, 0 diagnostics)** by binding `S`, `T2`, and `a` to unimported `b.S`, `b.T2`, and `b.a`.
  3. **Unbound cross-module collision (`tests/modules/same_name_types/ambiguous_unbound_proj`)**:
     In `fn bad<F: HasOut>(x: F.Output) -> i32` (without `<Output = ...>` equality bound), `F.Output` reaches `lookup_path_type_by_name` unbound (`symbol == 0, def_dom == 0`). When both `module a` and `module b` define `pub enum F` (and `main` defines none), HEAD `31b7dd49` stripped `.Output` to `"F"` in the `HIR_ITEM_ENUM` bare-name branch and **silently compiled (`rc=0`, 0 diagnostics)** by picking the first module's `a.F`.

## Changes in `compiler/types/typeck.ax` and `_workspaces/baseline-failures.txt`

- **`tc_item_matches_def_mod` (`compiler/types/typeck.ax:5275-5312`)**: Exact segment-by-segment comparison of `HirItem.module_path` against `HirPath.def_mod` without allocations.
- **`tc_is_impl_member_clone` (`compiler/types/typeck.ax:5314-5349`)**: Detects shallow top-level clones of `HIR_ITEM_IMPL` members (`fn`, `type` alias, `const`) appended by `hir_postprocess_items` so unmangled associated member names never masquerade as module-level items in `def_mod` or unbound bare-name scans.
- **`tc_current_module_anchor` (`compiler/types/typeck.ax:5351-5380`)**: Identifies the enclosing item (`current_fn`, `current_impl`, or file/span-enclosing top-level item) to determine the current `module_path` during unbound fallback.
- **`tc_resolve_matched_path_item` (`compiler/types/typeck.ax:5382-5470`)**: Shared item-to-`TypeId` resolver for `HIR_ITEM_FN`, `HIR_ITEM_CONST`/`HIR_ITEM_STATIC`, `HIR_ITEM_STRUCT`, `HIR_ITEM_ENUM`, and `HIR_ITEM_TYPE_ALIAS`. When `is_bound` is true and a forward-referenced `fn`/`const`/`static` has not yet been visited in Pass 1b, computes and caches its item type on demand (with `t_error` sentinel guarding against self-referential const/fn cycles).
- **`lookup_path_type_by_name` (`compiler/types/typeck.ax:5472-5760`)**:
  - **Bound branch (`5516-5615`)**: When `path.symbol.v != 0 || path.def_dom != 0`, never enters the bare-name walk. Matches strictly by `symbol` (including enum variants, `extern`/`impl`/`trait` members, and `current_fn` parameters) or by `def_mod` + `def_name` when `symbol == 0 && def_dom != 0`; otherwise emits `AX_NAME_UNRESOLVED`.
  - **Unbound branch (`5657-5760`)**: Reached only when `symbol == 0 && def_dom == 0` (after generic parameter lookup). Scans non-cloned top-level `fn`, `const`/`static`, `struct`, `enum`, and `type`-alias items: immediately prefers a match in `anchor.module_path` (`cur_mod_match`), tracks matches in other modules (`other_mod_match`), and emits `AX_NAME_UNRESOLVED` when more than one distinct non-current module defines the name (`other_mod_ambiguous`).
- **`register_item_sig` (`compiler/types/typeck.ax:13548-13778`)**: Made `HIR_ITEM_FN`, `HIR_ITEM_CONST`, and `HIR_ITEM_STATIC` idempotent when their `thir` item types were already computed on demand during Pass 1b.
- **`_workspaces/baseline-failures.txt`**: Removed `conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax`, `conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax`, and their `T428g` comment block.

## Inventory of Bare-Name Item Scans in `compiler/types/typeck.ax`

1. **`lookup_path_type_by_name` (`5472-5760`)** — `HIR_ITEM_FN`, `HIR_ITEM_CONST`, `HIR_ITEM_STATIC`, `HIR_ITEM_STRUCT`, `HIR_ITEM_ENUM`, `HIR_ITEM_TYPE_ALIAS`: **In scope — fixed in T428g** (bound paths select strictly by `symbol` or `def_mod`+`def_name`; unbound paths prefer current module and emit `AX_NAME_UNRESOLVED` on multi-module ambiguity).
2. **`find_const_item_by_name` (`2344-2358`, called from `eval_const_expr_u128`)** — `HIR_ITEM_CONST`: Reached **only when `sym_v == 0`** (`find_const_item_by_symbol` handles all bound paths with `sym_v != 0`); evaluates integer constant values on unbound unit/synthetic HIR, does not resolve types. Out of scope.
3. **`typeck_extract_fn_sym_from_arg` (`3101-3119`)** — `HIR_ITEM_FN`: Reached **only when `(*arg).path.symbol.v == 0`** (`if sym_v != 0 { return sym_v; }` precedes it) when extracting function-pointer symbols in const/TLS aggregate initializers. Out of scope.
4. **`register_intrinsic_callee` (`4498-4516`)** — `HIR_ITEM_FN`: Fallback when `found_item == 0`, gated by `intrinsic_lookup(name).has_desc || tc_host_thread_intrinsic_kind(view(name)) != 0` (`@intrinsic` / host `@lang` names only). Out of scope (noted in task card).
5. **`tc_impl_assoc_const_ty` (`9153-9183`) & `check_expr_field_or_tuple_idx` (`9230-9250`)** — `HIR_ITEM_CONST` inside `HIR_ITEM_IMPL` / `HIR_ITEM_TRAIT`: Member-name lookup scoped to `impl` blocks whose `self_type` unifies with `base_ty` (or trait associated constants on `TY_PARAM` `T.CONST`), not top-level bare-name path lookup. Out of scope.
6. **`check_expr_method_call` (`10200-10219`)** — `HIR_ITEM_CONST` / `HIR_ITEM_STATIC`: Heuristic `is_type_name` flag check on method-call receivers after symbol check (`10191`); does not resolve a `TypeId` (`check_expr` still typechecks `recv` normally). Out of scope.
7. **`tc_resolve_call_def` (`12042-12063`)** — `HIR_ITEM_FN`: Used by `classify_spawn_call`; returns `find_item_by_symbol` whenever `(*callee).path.symbol.v != 0` and scans by `name_v` **only when `sym_v == 0`**. Out of scope.
8. **`tc_impl_is_lang_drop` (`14060-14097`)** — `HIR_ITEM_TRAIT` / `STRUCT` / `ENUM` / `TYPE_ALIAS` / `USE`: Explicitly module-scoped via `tc_module_path_eq(it, impl_item)` per SPEC-12 AXS-DROP-008 to check whether the impl's own module shadows `Drop`. Module-scoped by design.
9. **`fre_find_drop_fn_for_def` (`18595-18626`) & `fre_type_implements_alloc_trait` (`18628-18684`)** — `HIR_ITEM_IMPL`: Freestanding profile checks matching `def_sym_v == s_sym_v` when `def_sym_v != 0` (with `GlobalAlloc`/`Allocator` trait name check and `def_name_v` fallback for unbound synthetic defs). Out of scope.
10. **`sec_find_mut_static_by_path` (`20977-20993`)** — `HIR_ITEM_STATIC`: Security profile `static mut` check matching `sym_v != 0 && isym == sym_v`, falling back to `iname == name_v` **only when `sym_v == 0`**. Out of scope.

## Build, Fixed-Point & Test Verification (`build-snap-T428g/`)

All builds and test runs were executed exclusively inside `build-snap-T428g/` (`-j 2`):

- **Snapshot**: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T428g` -> `HEAD 31b7dd4 + 24 changed, 0 deleted file(s) of T428g`; `36 generator(s), 60 file(s)` regenerated.
- **Stage 1 -> Stage 2 -> Stage 3 Fixed-Point (`python tools/build_axiomc.py --out build --root . --stage 2`)**:
  - `build/axiomc1.exe`: `34978816` bytes, `sha256=b893dd8c53006e29...`
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 9dbfb30db402a63be0cabc51e79b1eefaae0f463713f93bb13df0e545388e409` (`9366016` bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and `axiomc2` produced byte-identical `.exe` on all 6 smoke programs (O1, incl. `Xin chào thế giới`).
- **Targeted Tests (`--filter run/same_name_std_types --filter modules/same_name_types --filter conformance/p11/e11_5_executors --no-cache -j 2 --verbose`)**:
  - `TOTAL 43 PASS 43 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - Verified all 3 `run/same_name_std_types` programs (`user_string_with_std_io`, `user_io_error_with_std_io`, `both_std_strings`) in `[interp]`, `[native]`, and `[native-O1]`, all 4 `modules/same_name_types` packages (`ok` in `[interp]`, `[native]`, `[native-O1]`; `mismatch`, `bound_non_type_no_fallback`, `ambiguous_unbound_proj` in `[ui]`), and all 28 `conformance/p11/e11_5_executors` cases.
- **Required Suites (`--filter typeck --filter ui --filter modules --filter std --filter conformance/p11 --filter selfhost/typeck --filter bundles_current --baseline _workspaces/baseline-failures.txt -j 2`)**:
  - `TOTAL 1709 PASS 1699 FAIL 0 SKIP 3 XFAIL 7`, `BASELINE OK` (empty baseline), `WEAK-NATIVE 0`.
- **Task Gate (`python tools/taskgate.py --task T428g --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428g.json`)**:
  - `own`: `7 ids / 15 results` (`15 PASS, 0 FAIL`)
  - `affected`: `83 ids / 132 results` (`131 PASS, 0 FAIL, 1 SKIP` — includes `selfhost/typeck/qa_typeck_all.ax`, `selfhost/typeck_traits/qa_typeck_traits_all.ax`, `bundles_current.test`)
  - `smoke`: `35 ids / 54 results` (`54 PASS, 0 FAIL`, seed `1003348679`)
  - `total (dedup)`: `116 ids / 184 results: TOTAL 184 PASS 183 FAIL 0 SKIP 1 XFAIL 0`
  - `WEAK-NATIVE`: `0 in the task's own/changed tests`
  - `Baseline`: `BASELINE OK` (`0` baseline entries), `unmatched changed files: none`
  - `archcheck`: `clean (exit 0) — 252 files scanned, 0 violations`
  - `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 23 s`
  - `TASKGATE T428g exit=0`

## Hygiene Checks

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428g`: exit 0, 24 `stage` entries, `0 REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: exit 0, `HARNESS OK`.
- Line endings verified LF-only across all modified and added files; canonical Axiom syntax (`=` for bindings, `.` for paths, `SPEC-00 §9` self-host subset) verified.

## Spec Deviations

none

## Files changed
- compiler/types/typeck.ax
- _workspaces/baseline-failures.txt
- tests/run/same_name_std_types/user_string_with_std_io.ax
- tests/run/same_name_std_types/user_io_error_with_std_io.ax
- tests/run/same_name_std_types/both_std_strings.ax
- tests/modules/same_name_types/ok/axiom.toml
- tests/modules/same_name_types/ok/src/a.ax
- tests/modules/same_name_types/ok/src/b.ax
- tests/modules/same_name_types/ok/src/w.ax
- tests/modules/same_name_types/ok/src/main.ax
- tests/modules/same_name_types/mismatch/axiom.toml
- tests/modules/same_name_types/mismatch/src/a.ax
- tests/modules/same_name_types/mismatch/src/b.ax
- tests/modules/same_name_types/mismatch/src/main.ax
- tests/modules/same_name_types/bound_non_type_no_fallback/axiom.toml
- tests/modules/same_name_types/bound_non_type_no_fallback/src/a.ax
- tests/modules/same_name_types/bound_non_type_no_fallback/src/b.ax
- tests/modules/same_name_types/bound_non_type_no_fallback/src/w.ax
- tests/modules/same_name_types/bound_non_type_no_fallback/src/main.ax
- tests/modules/same_name_types/ambiguous_unbound_proj/axiom.toml
- tests/modules/same_name_types/ambiguous_unbound_proj/src/a.ax
- tests/modules/same_name_types/ambiguous_unbound_proj/src/b.ax
- tests/modules/same_name_types/ambiguous_unbound_proj/src/main.ax
- _workspaces/reports/T428g-report.md

## Status
STATUS: COMPLETE round=0
