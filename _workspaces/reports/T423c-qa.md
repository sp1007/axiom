# T423c QA Report

## Round 0

### Summary
Independent QA gate for **T423c** (`Fix — a generic fn called without type arguments inside a closure body fails with AX_TYPE_UNKNOWN`).
All acceptance criteria verified in isolated snapshot `build-snap-T423c/` (HEAD `4ab651547d83`). No blocking findings.

### Code & Test Audit
1. **Orphaned generic `TY_VAR`s in `scan_expr_captures` (`compiler/types/typeck.ax`):**
   - Verified `tc_is_builtin_drop_callee` checks `TY_BUILTIN_DROP` read-only without invoking `lookup_path_type` / `instantiate_path` or mutating `cx.type_vars`.
   - Verified prelude `drop(non_copy)` inside a non-`move` closure still infers `CAP_MOVE` and runs `Drop` exactly once, while user-defined generic fns (`my_generic<T>`) and locally shadowed `let drop = |...|` callables do not trigger `TY_BUILTIN_DROP` or leave orphaned `TY_VAR`s (covered by new QA test `qa_drop_and_shadowing.ax`).
2. **Post-closure `TY_VAR` unification in `finalize_types` (`compiler/types/typeck.ax`):**
   - Verified `k == TY_CLOSURE` deep-resolves `captures`, `param_types`, and `ret_type`, rebuilds `fn_type`, and synchronizes `thir.item_types`, `thir.param_types`, and `thir.symbol_types` on the synthetic `fn_item`.
   - Verified nested closures with deferred parameter + return type unification (`qa_generic_impl_method_closure.ax`, `infer_from_return_type.ax`, `higher_order_generic_fn.ax`).
3. **Closure monomorphization inside generic fns / impls (`compiler/types/typeck.ax`, `compiler/traits/mono.ax`, `compiler/mir/builder.ax`):**
   - Verified `finish_closure_item` attaches enclosing impl + fn `TY_PARAM`s to `TY_CLOSURE.args`/`arg_count` and tags the synthetic `fn_item` in `thir.expr_methods` / `thir.item_types`.
   - Verified `subst_ty_enum_or_closure` collision-safe `closure_id` probing and `mb_bind_closure_mono_in_ty` + `mb_mono_find_or_create` parameter cloning/substitution for multi-word captures (16-byte `Pair16`, 24-byte `Triple24`) across multiple distinct concrete instantiations of a generic `impl<A, B>` method with its own method-level `<C>` (`qa_generic_impl_method_closure.ax`).
4. **Tracked xfail & fiber bundle hygiene:**
   - Verified `tests/std/fiber/closure_generic_infer_xfail.ax` has no `// xfail:` directive and passes in `interp`, `native`, and `native-O1`.
   - `python tests/std/fiber/gen_tests.py --check` -> `OK fiber bundles match live std/fiber`.

### Verification Evidence (inside `build-snap-T423c/` only)

1. **Stage-2 build (`python tools/build_axiomc.py --out build --root . --stage 2`):**
   - `BUILD-AXIOMC OK`: `build/axiomc2.exe` (`size=8686080`, `sha256=464321a6cf51dda9fbc9b424e51b00decc80a11f59ac848a9f643269fa0a8b0f`, matches engineer report).
2. **Targeted T423c + QA adversarial suite (`python tools/axtest.py --compiler build/axiomc2.exe --filter run/closure_generic_infer --filter std/fiber/closure_generic_infer_xfail.ax --no-cache -j 2 --verbose`):**
   - `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
   - Covers all 9 engineer tests, `tests/std/fiber/closure_generic_infer_xfail.ax`, and 2 new QA adversarial tests (`qa_drop_and_shadowing.ax`, `qa_generic_impl_method_closure.ax`).
3. **Native-evidence mutation spot-proof (inside `build-snap-T423c/` only):**
   - Mutated `777\n` -> `999\n` in `build-snap-T423c/tests/run/closure_generic_infer/qa_generic_impl_method_closure.ax` and ran `axtest.py --no-cache`: `[interp]`, `[native]`, and `[native-O1]` all failed with `stdout differs at byte 56` (`TOTAL 3 PASS 0 FAIL 3`, `MUTATED_EXIT=1`).
   - Restored byte-identical (`HASH_MATCH=True`, `SHA256=c612384f838c91f57e807a245696f23a5ee0c4b48c29966b6169d182a6e7e379`) and re-verified `TOTAL 34 PASS 34 FAIL 0`.
4. **Per-task gate (`python tools/taskgate.py --task T423c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423c.json`):**
   - Root `D:/projects/compiler/new lang/build-snap-T423c`, HEAD `4ab651547d83`, wall time `910.8 s`.
   - `own`: `12 ids, 34 results, 34 PASS, 0 FAIL, 0 SKIP, 0 XFAIL` (`WEAK-NATIVE: 0 in the task's own/changed tests`)
   - `affected`: `244 ids, 453 results, 451 PASS, 0 FAIL, 2 SKIP, 0 XFAIL` (derived via `tools/axtest_affected.py` from `compiler/types/typeck.ax`, `compiler/traits/mono.ax`, `compiler/mir/builder.ax`, and regenerated selfhost bundles; 0 unmatched changed files)
   - `smoke` (`seed=3706185114`): `32 ids, 53 results, 53 PASS, 0 FAIL, 0 SKIP, 0 XFAIL`
   - **Total (dedup):** `272 ids, TOTAL 502 PASS 500 FAIL 0 SKIP 2 XFAIL 0` (`TASKGATE T423c exit=0`)
   - `Baseline`: `BASELINE OK` (`Failing ids: none`)
   - `archcheck`: `232 files scanned, 0 violations` (exit 0)
   - `Cache`: `CACHED 252, miss 20, uncacheable 116, stored 18, dep_source exact, verification sample seed=1550585691 n=20 of 136 hits, mismatch none, rejected {}, producer snapshot`
5. **Hygiene:**
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423c` -> 0 `REFUSED`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

### Findings
none

## Files changed

- tests/run/closure_generic_infer/qa_drop_and_shadowing.ax
- tests/run/closure_generic_infer/qa_generic_impl_method_closure.ax

VERDICT: PASS round=0
