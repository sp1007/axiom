# T445a report

## Summary
### Root cause
1. **Missing per-arm / `if let` drop scopes in `compiler/mir/builder.ax`**:
   - In `HIR_EXPR_MATCH` and `HIR_EXPR_IF` (`let_pat != 0`), pattern-binding locals were allocated via `mb_new_local` and pushed onto `b.current_drops`, but neither `HIR_EXPR_MATCH` arms nor `HIR_EXPR_IF` then-branches recorded/unwound `b.current_drops` down to the arm's base drop chain (`arm_base_drops`) at the end of the arm. Consequently, by-value bindings leaked out of their lexical arm scope into `b.current_drops` of the enclosing block (or function when the enclosing body had no inner block unwind).
2. **Interleaved refutable pattern testing, guard evaluation, and payload moves**:
   - `mb_build_pat_match` allocated `MIR_LOCAL_USER` locals and emitted `Move` assignments while testing refutable sub-patterns and **before** evaluating arm guards (`if cond`). A refutable sibling mismatch (`(Some(x), 1)` on `(Some(d), 2)`) or a failing guard moved the payload prematurely instead of inspecting bindings by view (`ADR-0047` §2 / `SPEC-12 AXS-DROP-009` §2).
3. **Eager temporary copy/move of droppable local scrutinees & single-boolean local drop flags (`compiler/mir/builder.ax`, `compiler/mir/drop.ax`)**:
   - `mb_build_match_scrutinee` and `HIR_EXPR_MATCH` lowered local place scrutinees (`p`, `p.f`, `p.0`) into a temporary local, moving the entire scrutinee instead of leaving unbound fields in the original place (`AXS-DROP-009` §5).
   - `compiler/mir/drop.ax` tracked only a single boolean drop flag per original local (`DropFlags`), clearing the entire local's flag on any projected field/variant move (`op.place.proj_count > 0`), which suppressed dropping remaining unmoved fields of partially moved local places and temporary scrutinees (`AXS-DROP-003`, `AXS-DROP-009` §5).

### What was built
1. **Per-arm, `if let`, `while let`, and `let ... else` drop scopes (`compiler/mir/builder.ax`)**:
   - Opened a drop scope per `match` arm (`HIR_EXPR_MATCH`) and `if let` then-branch (`HIR_EXPR_IF`): at arm/then fallthrough, `mb_build_drop_chain(b, b.current_drops, arm_base_drops, bb_end, sp)` drops any inner arm temporaries and the arm's initialized pattern bindings in reverse order of left-to-right pattern declaration (`AXS-DROP-009` §1, §4), then restores `b.current_drops` and `b.sym_map_count`.
   - Early exits (`return`, `break`, `continue`, `?`) walk `b.current_drops` down to `0` or `ls.drop_scope`, so keeping arm bindings on `b.current_drops` strictly during the arm body drops them on every early-exit edge (`AXS-DROP-009` §1). `HIR_EXPR_WHILE` (`let_pat != 0`) drops pattern bindings at the end of each iteration and on `continue`/`break` (`AXS-DROP-009` §4).
   - `desugar_let_else` (`typeck.ax`) rewrites `let P = e else { B };` into `HIR_STMT_EXPR` wrapping a `HIR_EXPR_MATCH` while preserving `stmt.else_block != 0` and `stmt.pat != 0`; `mir_build_stmt` marks that `match` via `b.let_else_match` (and `HIR_STMT_LET` with `else_blk != 0` preserves `ok_drops`) so `let` and `let ... else` bindings remain live until the end of the enclosing block (`AXS-DROP-009` §6), while any temporary initializer's unbound parts drop at statement end.
2. **Three-phase refutable pattern & guard lowering (`compiler/mir/builder.ax`)**:
   - Split refutable pattern matching into Phase 1 `mb_pat_test_in_place` (discriminant, literal, range, and OR-pattern tests only — zero user locals or payload moves), Phase 2 `mb_pat_register_guard_places` (aliases pattern symbols directly to scrutinee sub-places during `if cond` evaluation without moving, wired into `mir_build_lvalue`, `mb_build_expr_as_operand_raw`, `mb_expr_is_local_place`, and `HIR_EXPR_CLOSURE`), and Phase 3 `mb_pat_bind_in_place` (allocates `MIR_LOCAL_USER` locals left-to-right and moves/copies payloads only after pattern + guard succeed).
3. **In-place droppable place scrutinees & `SubDropFlags` (`compiler/mir/builder.ax`, `compiler/mir/drop.ax`)**:
   - Widened `mb_build_match_scrutinee` and `HIR_EXPR_MATCH` so droppable local places (`p`, `p.f`, `p.0`) and `view`/`mut_view` deref places (`self.guard`) match in place, preserving `scrut_expr.span` on arm 0's top-level discriminant read for `AX_MOVE_USE_AFTER_MOVE`, and falling back to a temporary scrutinee on `view`/`mut_view` deref places only when `mb_match_has_moving_guard` detects a guard moving a non-`Copy` binding.
   - Added `SubDropFlags` (`TY_U8` root-init + per-leaf flags) in `compiler/mir/drop.ax` exclusively for original locals `1..orig_local_count-1` that undergo a projected move/copy or drop (without raw deref or dynamic index). Moved leaves clear their leaf flag (`0u8`), reassignments re-arm leaf flags (`1u8`), and root drops check `init_flag` before running nested compound/variant drops and clear `init_flag` on exit to `target_v`. Functions without partial moves emit byte-identical MIR.

### Existing tests updated for ADR-0047
- `tests/std/async/structured/src/resource_governor_limits.axsrc` (and regenerated `tests/std/async/structured/resource_governor_limits.ax` via `python tests/std/async/structured/gen_tests.py`): added `is_lease_ok(r: view<Result<ResourceLease, ResourceError>>) -> bool` in section 4 so `l1`, `l2`, `l3` are checked by `view` without moving the `ResourceLease` values into match-arm bindings, keeping all three leases alive until block end (`current_usage == 3` inside the block, `0` after).
- `tests/run/own_mut_view_fields/match_field_reinit_drop.ax`: updated expected `stdout` (`8\n9\n7\n1\n...` -> `8\n9\n1\n7\n...`) because `g` in `replace_guard` now drops at the end of its `Option.Some(g)` arm before `emit_digit(7u8)`.
- `tests/run/pattern_multi_binding/qa_adv_drop_paths.ax`: updated expected `stdout` in `reuse()` and `generic()` where by-value arm bindings `a, b` now drop at the end of their `match` arms rather than at function exit.
- `tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax`: updated the guard to consume `g` by move (`if take_guard(g)`) so the test continues verifying `AX_MOVE_USE_AFTER_MOVE` on a moving guard over a `mut_view` scrutinee (under `ADR-0047` §2, a non-moving guard `if g.id == 9u8` binds by view and no longer moves).

## Files changed
- compiler/mir/builder.ax
- compiler/mir/drop.ax
- tests/run/drop_arm_scope/arm_before_next_stmt.ax
- tests/run/drop_arm_scope/early_exits_arm.ax
- tests/run/drop_arm_scope/guard_fail_no_move_no_drop.ax
- tests/run/drop_arm_scope/guard_temp_and_diverge_edges.ax
- tests/run/drop_arm_scope/if_let_and_while_let.ax
- tests/run/drop_arm_scope/let_and_let_else_block_scope.ax
- tests/run/drop_arm_scope/moved_out_in_arm.ax
- tests/run/drop_arm_scope/nested_and_or_patterns.ax
- tests/run/drop_arm_scope/scrutinee_place_partial_move.ax
- tests/run/drop_arm_scope/scrutinee_temporary_partial_move.ax
- tests/run/drop_arm_scope/try_in_arm.ax
- tests/run/drop_arm_scope/two_bindings_reverse_order.ax
- tests/run/own_mut_view_fields/match_field_reinit_drop.ax
- tests/run/pattern_multi_binding/qa_adv_drop_paths.ax
- tests/std/async/structured/resource_governor_limits.ax
- tests/std/async/structured/src/resource_governor_limits.axsrc
- tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax

## Tests
All builds and tests executed inside `build-snap-T445a/` (refreshed on `HEAD 4070d7776d28`):
- Stage-2/3 bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 5c4649c30c7f4b3115534fabcd833694310498827e1cd8e4769cbb65b754c32f` (9,119,744 bytes).
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`).
- Structured async bundle check (`python tests/std/async/structured/gen_tests.py --check`): `OK structured bundles match live std/async` (exit 0).
- New `tests/run/drop_arm_scope/*.ax` suite (`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter drop_arm_scope`):
  - `TOTAL 33 PASS 33 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
  - Mutation liveness spot-proof on `arm_before_next_stmt.ax` (`drop 10\ndrop 1` -> `drop 1\ndrop 10` inside snapshot): `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed), restored -> `TOTAL 3 PASS 3 FAIL 0`.
- Updated `locks:` tests (`match_field_reinit_drop`, `qa_adv_drop_paths`, `qa_guard_arm_view_place_move`, `resource_governor_limits`): `TOTAL 13 PASS 13 FAIL 0` (`WEAK-NATIVE 0`).
- Full `tests/run/` + `tests/std/{async/structured,fiber,thread,sync,collections}` (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --filter run/ --filter std/async/structured --filter std/fiber --filter std/thread --filter std/sync --filter std/collections`):
  - `TOTAL 3437 PASS 3427 FAIL 0 SKIP 4 XFAIL 6`.
- Per-task gate (`python tools/taskgate.py --task T445a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TASKGATE T445a exit=0`: `own` 11 ids (`33 PASS / 0 FAIL`), `affected` 177 ids (`352 PASS / 0 FAIL / 2 SKIP`, including `mir`, `verify`, `selfhost/{mir,drop,interp,own_mir_verify,driver,backend,lir,opt,verify}`), `smoke` 32 ids (`53 PASS / 0 FAIL`); deduplicated `TOTAL 405 PASS 403 FAIL 0 SKIP 2 XFAIL 0`.
  - `WEAK-NATIVE`: `0` in own/changed tests; `BASELINE OK`; `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`; `smoke-check`: OK.

## Spec deviations
none (`x @ P` pattern syntax is not part of `spec/SPEC-02-grammar.md` v0.1, where `@` denotes attributes only; nested struct/tuple/enum patterns, reordered field patterns, and nested OR-patterns are covered in `tests/run/drop_arm_scope/nested_and_or_patterns.ax`).

## Follow-ups
- Optional resolver follow-up (outside `T445a` scope/locks): `compiler/resolve/resolver.ax` (`PAT_OR`, line 1117) calls `resolve_pat_inner(..., or_pats, ..., mut_view(base_env))` which walks `(*cur).next` across all sibling OR-alternatives inside `base_env`, causing OR-patterns that introduce bindings (`Left(x) | Right(x)`) to emit `AX_NAME_DUPLICATE_BINDING`. MIR lowering in `compiler/mir/builder.ax` is already prepared to share `MirLocalId`s across OR-pattern alternatives once name resolution/typeck support bindings in `PAT_OR`.

## Round 1
### QA F1 fix & condition-temporary audit (`compiler/mir/builder.ax`)
- **Fixed F1 (`match` guard temporary leak on guard-false / guard-true edges)**:
  - Added `mb_unwind_cond_temps` and wired it into both the top-level `HIR_PAT_OR` arm guard loop and the plain arm guard block in `HIR_EXPR_MATCH`: records `guard_base_drops = b.current_drops` before `mb_build_expr_as_operand(mut_view(*b), guard, mut_view(g_op))`; when `!b.is_diverged` and `b.current_drops != guard_base_drops`, materialises `g_op` into a scalar `bool` temporary if `g_op` has projections (`proj_count > 0`, e.g. `mk_flag().flag`) so field reads execute before destructors without triggering `AX_VERIFY_USE_AFTER_MOVE`, emits `mb_build_drop_chain` down to `guard_base_drops`, and restores `b.current_drops = guard_base_drops` before `mb_emit_switch_single`.
  - Handled diverging guards (`return`, `break`, `continue`, `?`): if `guard` diverges unconditionally (`b.is_diverged == true`), restores `b.current_drops = guard_base_drops` without allocating an unreachable `bb_guard_ok`/`bb_alt_ok` or emitting dead `mb_pat_bind_in_place` moves (and marks `bb_arm_body` `MIR_TERM_UNREACHABLE` if all OR-pattern guard alternatives diverge); if `guard` uses `?` (`Result<bool, D>`), unwinds the temporary `Result` container on `Ok` and drops live guard/scrutinee/outer locals on `Err`.
- **Audited `if let`, `while let`, `let ... else`, and `while` condition/pattern-test paths**:
  - `mb_pat_test_in_place` and `mb_pat_register_guard_places` allocate only scalar (`u32`/`bool`/`view<T>`) temporaries; `if let`, `while let`, and `let ... else` scrutinee temporaries sit below `then_base_drops` / `scrut_drops` / `else_base_drops` and unwind cleanly on every edge.
  - Also wired `mb_unwind_cond_temps` into `HIR_EXPR_WHILE` (`let_pat == 0`) down to `pat_drops` before `mb_emit_switch_single` so droppable temporaries created inside a `while` condition drop cleanly on both `body_bb` and `exit_bb` edges (zero-instruction no-op when `cond` allocates no droppable temporaries).
- **Added regression test**:
  - `tests/run/drop_arm_scope/guard_temp_and_diverge_edges.ax`: covers top-level `HIR_PAT_OR` (`1 | 2 if ...`) guards with droppable temporaries (failing & matching), projected `bool` field from a droppable temporary whose `Drop` mutates the field, multiple guard temporaries (LIFO reverse drop order) and short-circuit `&&`/`||` inside a loop, `?` (`Result<bool, D>`) and unconditional `return` inside a `match` guard, and `while` condition droppable temporaries.

### Round 1 verification (`build-snap-T445a/`, `HEAD 4070d7776d28`)
- Stage-2/3 bootstrap (`python tools/build_axiomc.py --out build --root . --stage 3`):
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 5442bf2ebef981e4af85a53f4628be5359a125a702871a07e6c17c85df291699` (9,121,792 bytes).
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`).
- Structured async bundle check (`python tests/std/async/structured/gen_tests.py --check`): `OK structured bundles match live std/async` (exit 0).
- Full `drop_arm_scope` suite (`python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter drop_arm_scope`, all 14 tests incl. `qa_adv_guard_temp_drop.ax`, `qa_adv_arm_drop_seams.ax`, and `guard_temp_and_diverge_edges.ax`):
  - `TOTAL 42 PASS 42 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
  - Mutation liveness spot-proof on `guard_temp_and_diverge_edges.ax` (`drop 36\ndrop 35` -> `drop 35\ndrop 36` inside snapshot): `TOTAL 3 PASS 0 FAIL 3`, restored -> `TOTAL 3 PASS 3 FAIL 0`.
- Per-task gate (`python tools/taskgate.py --task T445a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T445a.json`):
  - `TASKGATE T445a exit=0`: `own` 14 ids (`42 PASS / 0 FAIL`), `affected` 180 ids (`361 PASS / 0 FAIL / 2 SKIP`), `smoke` 33 ids (`56 PASS / 0 FAIL`); deduplicated `TOTAL 417 PASS 415 FAIL 0 SKIP 2 XFAIL 0`.
  - `WEAK-NATIVE`: `0` in own/changed tests; `BASELINE OK`; `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`; `smoke-check`: OK.
- `taskctl.py changes T445a` (0 `REFUSED` lines, 0 unlisted files) & `harness_check.py` (`HARNESS OK`).

STATUS: COMPLETE round=1
