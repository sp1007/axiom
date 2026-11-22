# T445a QA report

## Round 0

### Checks performed & evidence
1. **Task changes & harness check** (`python .claude/skills/axiom-tasks/scripts/taskctl.py changes T445a`, `harness_check.py`):
   - Before adding QA tests: 0 `REFUSED` lines, `HARNESS OK`.
   - After listing QA-added tests under `## Files changed` below: re-verified 0 `REFUSED` lines, `HARNESS OK`.
2. **Stage-2/3 bootstrap & fixed point** inside `build-snap-T445a/`:
   - `python tools/build_axiomc.py --out build --root . --stage 3`
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 5c4649c30c7f4b3115534fabcd833694310498827e1cd8e4769cbb65b754c32f` (9,119,744 bytes).
3. **Structured async bundle check** inside `build-snap-T445a/`:
   - `python tests/std/async/structured/gen_tests.py --check` -> `OK structured bundles match live std/async` (exit 0).
4. **Code review** of `compiler/mir/builder.ax` and `compiler/mir/drop.ax`:
   - Verified per-arm (`HIR_EXPR_MATCH`), `if let` (`HIR_EXPR_IF`), `while let` (`HIR_EXPR_WHILE`), and `let ... else` (`b.let_else_match`) drop scopes and 3-phase refutable pattern lowering (`mb_pat_test_in_place` -> `mb_pat_register_guard_places` -> `mb_pat_bind_in_place`).
   - Verified `SubDropFlags` partial-move drop flags in `compiler/mir/drop.ax` (root-init + per-leaf `u8` flags, re-arming on both `MIR_STMT_ASSIGN` and `MIR_TERM_CALL` destinations via `call_pred_plus1`, no-op when no partial moves exist).
   - Found **F1** (below): guard temporaries pushed onto `b.current_drops` during `mb_build_expr_as_operand(mut_view(*b), guard, mut_view(g_op))` are never unwound on the guard-false edge (`bb_next_arm` / `next_or`), causing `AX_VERIFY_MISSING_DROP` when a `match` guard allocates a droppable temporary.
5. **Updated existing tests review**:
   - `tests/std/async/structured/src/resource_governor_limits.axsrc` & `.ax`: `is_lease_ok(view<Result<ResourceLease, ResourceError>>)` inspects leases without moving, preserving section 4's intent (`usage == 2` inside block, `0` after).
   - `tests/run/own_mut_view_fields/match_field_reinit_drop.ax`: `8\n9\n7\n1` -> `8\n9\n1\n7` reflects `g` dropping at the end of `Option.Some(g)` before `emit_digit(7u8)`; reinit/wildcard/`while let` coverage preserved.
   - `tests/run/pattern_multi_binding/qa_adv_drop_paths.ax`: `reuse()` and `generic()` drop arm bindings at arm end rather than function exit; intent preserved.
   - `tests/ui/own_mut_view_receiver/qa_guard_arm_view_place_move.ax`: guard updated to `if take_guard(g)` so the guard moves `g` and continues verifying `AX_MOVE_USE_AFTER_MOVE`.
6. **Boundary cross-check (step 5)**:
   - Added `tests/run/drop_arm_scope/qa_adv_arm_drop_seams.ax` (nested `match`, value-expression `match`, partial move + call/conditional reinit, refutable sibling + failing guard + matching arm, `while let` partial-move temporary scrutinee across `continue`/`break`, conditional move in multi-binding arm, `let ... else` partial-move temporary scrutinee) -> **PASS** in `interp`, `native`, `native-O1`.
   - Added `tests/run/drop_arm_scope/qa_adv_guard_temp_drop.ax` (droppable temporary allocated inside a `match` guard on both plain and OR-pattern arms, failing and succeeding) -> **FAIL** (`AX_VERIFY_MISSING_DROP`, F1).
   - `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter drop_arm_scope`: `TOTAL 39 PASS 36 FAIL 3 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
7. **Native-evidence spot-proof (step 4a)**:
   - Confirmed all 13 tests in `tests/run/drop_arm_scope/` use `// modes: interp native` with exact `// stdout:` (`WEAK-NATIVE: 0` in own/changed tests).
   - Mutated `drop 3\ndrop 2` -> `drop 2\ndrop 3` in `build-snap-T445a/tests/run/drop_arm_scope/qa_adv_arm_drop_seams.ax`:
     - `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter qa_adv_arm_drop_seams`: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed at byte 13).
     - Restored -> `TOTAL 3 PASS 3 FAIL 0`.
8. **Per-task gate (`taskgate.py`)** inside `build-snap-T445a/`:
   - Command: `python tools/taskgate.py --task T445a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T445a.json`
   - `own`: 13 ids (`36 PASS / 3 FAIL`), `affected`: 179 ids (`355 PASS / 3 FAIL / 2 SKIP`), `smoke`: 33 ids (`54 PASS / 0 FAIL`), deduplicated `TOTAL 412 PASS 407 FAIL 3 SKIP 2 XFAIL 0`.
   - `WEAK-NATIVE`: `0` in own/changed tests; `archcheck`: `clean (exit 0) archcheck: 232 files scanned, 0 violations`; `smoke-check`: OK; `Cache`: `mismatch none`.
   - Only failing id outside baseline: `run/drop_arm_scope/qa_adv_guard_temp_drop.ax` (F1).

### Findings

#### F1 (FAIL — regression): Droppable temporaries created inside a `match` guard leak on the guard-false edge (`AX_VERIFY_MISSING_DROP`)
- **Location**: `compiler/mir/builder.ax:10644-10655` (OR-pattern arm guard) and `compiler/mir/builder.ax:10677-10691` (plain arm guard).
- **Expected vs actual**:
  - Expected: Evaluating a `match` guard `if cond` that allocates a droppable temporary (e.g. `if mk(99).id == g.id`) drops that temporary after the guard evaluates (on both the guard-false edge before trying the next arm/OR-alternative, and on the guard-true edge). On baseline `axiom0.exe`, `match 1 { x if mk(99).id == x => ..., _ => ... }` compiles and runs cleanly (`ok\ndrop 99\nafter`).
  - Actual: `mb_build_expr_as_operand(mut_view(*b), guard, mut_view(g_op))` pushes guard temporaries onto `b.current_drops`, then `mb_emit_switch_single` branches directly to `bb_next_arm` (or `next_or`) when the guard is false without unwinding those temporaries; at line 10719 `b.current_drops = arm_base_drops` discards them from the drop chain, leaving the temporary live and undropped on the guard-false path and failing MIR verification with:
    `error[AX_VERIFY_MISSING_DROP]: missing drop for owned local at return`
    (in `interp`, `native`, and `native-O1`).
- **Repro**: `tests/run/drop_arm_scope/qa_adv_guard_temp_drop.ax` (added in main tree and refreshed in `build-snap-T445a/`):
  `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter qa_adv_guard_temp_drop`
- **Suggested fix**: Record `let guard_base_drops = b.current_drops;` before evaluating `guard`; after `mb_build_expr_as_operand(mut_view(*b), guard, mut_view(g_op))` (since `g_op` is `bool`), if `!b.is_diverged && (b.current_drops as usize) != (guard_base_drops as usize)`, emit `mb_build_drop_chain(mut_view(*b), b.current_drops, guard_base_drops, MirBbId { v: 0u32 }, view(sp))` and restore `b.current_drops = guard_base_drops` BEFORE `mb_emit_switch_single` (in both the OR-pattern guard loop and the plain arm guard block).

## Round 1

### Checks performed & evidence
1. **Round 0 F1 fix review (`compiler/mir/builder.ax`)**:
   - Verified `mb_unwind_cond_temps` (`compiler/mir/builder.ax:10535-10558`) is wired into both the top-level `HIR_PAT_OR` arm guard loop (`10678-10694`) and the plain arm guard block (`10731-10749`) in `HIR_EXPR_MATCH`, as well as `HIR_EXPR_WHILE` (`let_pat == 0`, `10897`):
     - Records `guard_base_drops = b.current_drops` before `mb_build_expr_as_operand(mut_view(*b), guard, mut_view(g_op))`.
     - Materialises projected `bool` operands (`cond_op.place.proj_count > 0`) into a fresh scalar `bool` temporary before running destructors so field reads execute before `Drop::drop`.
     - Emits `mb_build_drop_chain` down to `guard_base_drops` and restores `b.current_drops = guard_base_drops` before `mb_emit_switch_single`, unwinding guard temporaries on both guard-false and guard-true edges.
     - Handles unconditionally diverging guards (`b.is_diverged == true`) cleanly: restores `b.current_drops = guard_base_drops`, skips unreachable `bb_alt_ok`/`bb_guard_ok` and dead `mb_pat_bind_in_place` moves, and terminates `bb_arm_body` with `MIR_TERM_UNREACHABLE` when all OR-pattern guard alternatives diverge.
2. **Round 0 regression test integrity (`tests/run/drop_arm_scope/qa_adv_guard_temp_drop.ax`)**:
   - Confirmed `qa_adv_guard_temp_drop.ax` was NOT weakened (exact `// modes: interp native` and exact `// stdout:` across plain guard-false, OR guard-false, and plain guard-true cases) and now passes in `interp`, `native`, and `native-O1`, alongside the engineer's new `guard_temp_and_diverge_edges.ax`.
3. **Round 1 boundary cross-check (step 5)**:
   - Added `tests/run/drop_arm_scope/qa_adv_guard_edges_r1.ax` covering three additional guard-temp / divergence seams:
     1. Top-level OR-pattern arm (`1 | 2 if { let gt = mk(41); return 42; }`) where all guard alternatives diverge unconditionally (`any_alt_ok == false` -> `bb_arm_body` unreachable).
     2. `continue` and `break` inside a `match` guard inside a `while` loop with a loop local, temporary droppable scrutinee, short-circuit `&&` guard temporary, and guard block local (verifying LIFO drops on hit, `continue`, and `break` edges).
     3. Nested `match` inside a `match` guard (inner guard temporary + inner arm binding drop before outer guard finishes; outer scrutinee remains unmoved on guard-false).
   - Refreshed snapshot (`python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T445a`: HEAD `4070d77` + 24 changed files + 60 regenerated selfhost bundle files).
   - Full `drop_arm_scope` suite inside `build-snap-T445a/`:
     `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter drop_arm_scope`
     -> `TOTAL 45 PASS 45 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 15 tests across `interp`, `native`, `native-O1`).
4. **Stage-2/3 bootstrap & fixed point + structured async bundles** inside `build-snap-T445a/`:
   - `python tools/build_axiomc.py --out build --root . --stage 2` -> `STAGE2 (O1) OK`, `BUILD-AXIOMC OK`.
   - `python tools/build_axiomc.py --out build --root . --stage 3` -> `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 5442bf2ebef981e4af85a53f4628be5359a125a702871a07e6c17c85df291699` (9,121,792 bytes).
   - `python tests/std/async/structured/gen_tests.py --check` -> `OK structured bundles match live std/async` (exit 0).
5. **Native-evidence spot-proof (step 4a)**:
   - Mutated `drop 35\ndrop 30` -> `drop 30\ndrop 35` in `build-snap-T445a/tests/run/drop_arm_scope/qa_adv_guard_edges_r1.ax`:
     - `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter qa_adv_guard_edges_r1`: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed at byte 32).
     - Restored -> `TOTAL 3 PASS 3 FAIL 0` (`WEAK-NATIVE 0`).
6. **Per-task gate (`taskgate.py`)** inside `build-snap-T445a/`:
   - Command: `python tools/taskgate.py --task T445a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T445a.json`
   - `TASKGATE T445a exit=0` (wall time 879.9 s, smoke seed `398049508`):
     - `own`: 15 ids (`45 PASS / 0 FAIL / 0 SKIP / 0 XFAIL`)
     - `affected`: 181 ids (`364 PASS / 0 FAIL / 2 SKIP / 0 XFAIL`, including `mir` 46, `verify` 29, `run` 71, `selfhost` 36, `std` 2, `ui` 3)
     - `smoke`: 33 ids (`56 PASS / 0 FAIL / 0 SKIP / 0 XFAIL`)
     - **total (dedup)**: 212 ids, `TOTAL 420 PASS 418 FAIL 0 SKIP 2 XFAIL 0`
   - `WEAK-NATIVE`: `0 in the task's own/changed tests` (3 in the wider run)
   - `Baseline`: `BASELINE OK` (`Failing ids: none`)
   - `archcheck`: `clean (exit 0) archcheck: 232 files scanned, 0 violations`
   - `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 18 s`
   - `Cache`: `CACHED 149, miss 28, uncacheable 101, stored 25, dep_source exact, verification sample seed=1405172649 n=20 of 83 hits, mismatch none, rejected {}, producer snapshot`
7. **Task changes & harness check**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T445a`: 0 `REFUSED` lines, all 3 QA-added files staged.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
None. Round 0 Finding F1 is completely resolved.

## Files changed
- tests/run/drop_arm_scope/qa_adv_arm_drop_seams.ax
- tests/run/drop_arm_scope/qa_adv_guard_temp_drop.ax
- tests/run/drop_arm_scope/qa_adv_guard_edges_r1.ax

VERDICT: PASS round=1
