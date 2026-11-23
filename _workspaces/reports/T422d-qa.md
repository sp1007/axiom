# T422d QA Gate Report

## Round 0

### Summary
Independent QA verification of **T422d** (`Fix — native .await on a future whose Future impl is generic (impl<T> Future for Wrap<T>) links to an undefined or wrong poll (segfault)`). All acceptance criteria, code-audit checks, three-mode tests (`interp`, `native`, `native-O1`), native-evidence spot-proof, QA adversarial tests, `taskgate`, `taskctl changes`, and `harness_check` passed with zero findings.

### Audit & Acceptance Checks

1. **Report & Scope Hygiene**
   - `_workspaces/reports/T422d-report.md` ends with `STATUS: COMPLETE round=0`.
   - `git grep "native-after: T422d" -- compiler tests std spec tools` -> 0 matches (exit 1).
   - `python tests/std/async/structured/gen_tests.py --check` -> `OK structured bundles match live std/async`.
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T422d` -> 0 `REFUSED` (all 14 implementer files + 1 QA test file staged cleanly).
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

2. **Code Audit (all 6 modified compiler files)**
   - `compiler/traits/solver.ax`: Verified `ImplBindState` + `pattern_ty_matches_target` recursive structural matching and consistent `TY_PARAM` binding at `depth > 0`, `get_impl_deduced_generic_arg` in `impl_bounds_satisfied`, and `TY_COROUTINE` auto-trait inspection (`fields[1..fc]` once lowered; `!coro_def_has_generics` guard pre-lowering).
   - `compiler/traits/mono.ax`: Verified `TY_COROUTINE` handling in `type_contains_param`, `subst_ty_self`, and `deduce_args`.
   - `compiler/types/typeck.ax`: Verified `TY_COROUTINE` generic param interning in `register_item_sig`, post-inference re-indexing in `finalize_types`, and recursive `tc_deduce_impl_args` in `resolve_future_output_ty`.
   - `compiler/mir/builder.ax`: Verified `mb_impl_matches_receiver_exact`, `mir_resolve_poll_callee_mono`, `mb_preserve_orig_item_name` + `MirBody.fn_name` update in `mb_dedup_mono_names`, and `mir_register_synth_poll_inst` deterministic `MonoEngine.next_sym_id` allocation.
   - `compiler/mir/async_lower.ax`: Verified `al_types_structurally_eq` coroutine layout sync, deterministic symbol allocation (`resolve_next_sym_v` replacing pointer-XOR), and `async_resolve_poll_calls_mono`.
   - `compiler/own_mir_verify/session.ax`: Verified `session_own_check_body` saving/restoring `TY_COROUTINE` `args`/`arg_count`, skipping lowering of uninstantiated generic `async fn` templates while still verifying/own-checking them, and the terminating fixpoint loop in `session_lower_all_async`.

3. **Stage-2 Build & Determinism (`build-snap-T422d/`)**
   - `python tools/build_axiomc.py --out build --root . --stage 2` (in `build-snap-T422d/`):
     - `STAGE1 OK`: `axiomc1.exe` (`32539648` bytes, `sha256=88d412ccf57308cf`, reused matching inputs `20884187f38f5a10`)
     - `STAGE2 (O1) OK`: `axiomc2.exe` (`8659456` bytes, `sha256=221e7c1f40d2cdb0237765efbd9575998f83e0ba8012f4143a18339cefa9c3d5`, reused matching inputs `f7977f53774c6b3a`)
     - `BUILD-AXIOMC OK`

4. **QA Adversarial Test Added**
   - Added `tests/run/await_generic_future/qa_adversarial_generic_await.ax` (`modes: interp native`, exact `stdout:`, `WEAK-NATIVE: 0`) exercising:
     1. Multi-parameter generic future `PairFut<A, B>` instantiated as `PairFut<i64, bool>`, `PairFut<bool, i64>`, and `PairFut<i64, i64>` in one program.
     2. Multi-poll generic future (`Poll.Pending` 3 times before `Poll.Ready`) with two live `Drop` resources (`g_outer`, `g_inner`) held across `.await`, verifying exact LIFO drop order (`g_inner g_outer`) and no double-drop/use-after-drop.
     3. Chained generic `async fn` (`gen_outer_no_t_out<T>` -> `gen_inner_no_t_out<T>` -> `SpinWrap<T>.await`) whose `Output` (`i64`) does not mention `T`, called at three distinct `T` types (`i64`, `bool`, `Tag2`).
     4. Sibling nested generic `Future` impls (`impl<T: Copy> Future for Wrap<BoxA<T>>` with `Output = T` vs `impl<T: Copy> Future for Wrap<BoxB<T>>` with `Output = (T, i64)`) in the same program.

5. **3-Mode Own & Structured Async Suite (`build-snap-T422d/`)**
   - Command: `python tools/axtest.py --compiler build/axiomc2.exe --filter run/await_generic_future --filter std/async/structured --no-cache -j 2 --verbose`
   - Result: `TOTAL 65 PASS 65 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 5 `run/await_generic_future/*.ax` tests + all `std/async/structured` tests including `spec34_task_group_example.ax` and `spec34_local_executor_example.ax` passed in `interp`, `native`, `native-O1`).

6. **Native-Evidence Mutation Spot-Proof (`build-snap-T422d/` only)**
   - Mutated expected `// stdout:` (`chained 77 88 99` -> `chained 77 88 98`) in `build-snap-T422d/tests/run/await_generic_future/qa_adversarial_generic_await.ax`:
     - `python tools/axtest.py --compiler build/axiomc2.exe --filter run/await_generic_future/qa_adversarial_generic_await.ax --no-cache -j 2 --verbose` -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed at byte 71, exit 1).
   - Restored byte-identical (`HASH_MATCH:True`, `sha256=221111C0A24021C53016BF458E91F687BD69E93E81823C55A8ED128A0F1BF7D8`) and re-ran:
     - `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`, exit 0.

7. **Per-Task Gate (`build-snap-T422d/`)**
   - Command: `python tools/taskgate.py --task T422d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T422d.json`
   - Result: `TASKGATE T422d exit=0`
   - Wall time: 990.9 s (axtest 969.6 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 23 | 65 | 65 | 0 | 0 | 0 | 0 |
| affected | 255 | 484 | 482 | 0 | 2 | 0 | 226 |
| smoke | 32 | 55 | 55 | 0 | 0 | 0 | 15 |
| **total (dedup)** | 283 | 535 | 533 | 0 | 2 | 0 | 239 |

   - `WEAK-NATIVE`: 15 in the run; 0 in the task's own/changed tests
   - `Baseline`: `BASELINE OK`; `Failing ids: none`
   - `archcheck`: clean (exit 0; 232 files scanned, 0 violations)
   - `smoke-check (tests/smoke.list)`: OK; est. worst-case draw 18 s
   - `Cache`: CACHED 239, miss 12, uncacheable 138, stored 11, dep_source exact, verification sample seed=2116389195 n=20 of 133 hits, mismatch none, rejected `{}`

### Findings
None.

## Files changed

- tests/run/await_generic_future/qa_adversarial_generic_await.ax

## Verdict

VERDICT: PASS round=0
