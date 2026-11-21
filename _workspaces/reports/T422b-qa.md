# T422b QA

## Round 0

### Scope / change-set check
- `taskctl.py changes T422b` (before my tests): stages exactly the 9 files of the report (lower.ax, builder.ax, 6 tests, report); no REFUSED line.
  The 5 tests I added show as REFUSED until they are listed in a `## Files changed` list: they are listed below.
- Sources in the snapshot are byte-identical to the main tree (`diff -q` on both compiler files and the test dir).
- Diff reviewed: `compiler/hir/lower.ax` (+8/-1, `head_grouped` flag in `lower_postfix`), `compiler/lir/builder.ax` (+4, callee place with `proj_count > 0` uses `get_place_type`). No change to bootstrap/axiom0, tools, CMake, diag codes. No new diagnostics, no BOOTSTRAP-SHORTCUT.
- Both files are inside `locks:` (the orchestrator added `compiler/hir/lower.ax`); shared-file check OK.

### Build (clean)
- Removed `build-snap-T422b/build`, `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release` + `cmake --build`: 132/132 steps, 0 warnings (`_workspaces/T422b_qa_stage0.log`).
- `python tools/build_axiomc.py --out build --force`: STAGE1 OK, STAGE2 (O1) OK, `BUILD-AXIOMC OK` sha256 10a6d434d7d6ad3c (`_workspaces/T422b_qa_axiomc.log`).
- `taskctl snapshot T422b`: "bundles regenerated: 36 generator(s), 60 file(s)", no BUNDLES FAILED. Selfhost `bundles_current.test` all 35 PASS (the engineer's earlier 15 failures were the hand-copy artefact, not reproducible after a fresh snapshot).

### Gate (`taskgate.py --task T422b ... -j 2 --no-cache`, `_workspaces/T422b_qa_taskgate.log`, exit 0)
- Change set 36 files (incl. regenerated bundles + my 5 tests). Parts: own 11 ids / 29 results PASS; affected 161 ids / 226 results (214 PASS, 12 SKIP); smoke 31 ids / 48 results PASS. Total `TOTAL 271 PASS 259 FAIL 0 SKIP 0 XFAIL 0` apart from the SKIPs: `SKIP 12`.
- Affected-set derivation as printed: lir map (`tests/run/native`, `selfhost/lir`), hir map (`selfhost/hir`), generator-check of every bundle embedding `compiler.hir.lower` / `compiler.lir.builder` (selfhost/* bundles_current + drop_oracle), changed selfhost qa tests. UNMATCHED none, UNRESOLVED none, MAP-NOTE none, DEFERRED none. The 12 SKIPs are the `requires: axiom0-internal` tests excluded by the gate flag (smoke picks e.g. encode/mc/obj/unit/mir ids); not an effect of the change.
- Failing ids: none; baseline OK; archcheck clean (230 files, 0 violations). Cache: CACHED 0, mismatch none.
- WEAK-NATIVE: 3 in the run (pre-existing, outside this task), 0 in the task's own/changed tests.
- I also re-ran by hand with `--no-cache`: `run/native` + `diff/` 142/142 PASS, all `bundles_current`/`drop_oracle` 35/35 PASS, selfhost abi/hir/lir qa 9/9 PASS.

### Acceptance criteria
1. FU-2 repro prints the same output in all modes: `tests/run/fn_ptr_field_call` 5 engineer tests x (interp, native, native-O1) = 15/15 PASS with exact `// stdout:` (native leg compares exact bytes). `through_pointer.ax` is the literal `((*vt).wake)(data)` repro.
2. FU-K: NOT a code change. I verified the evidence independently with the snapshot compiler: `run --interp --step-limit 2000 prefix_before_limit.ax` -> stdout `before the hang\n42\n` (captured via redirect to a file), exit 124, stderr `AX_DRIVER_INTERP_STEP_LIMIT`. Extra: a panic (`arithmetic overflow`) after a print flushes the prefix; a recursive printer under `--step-limit 5000` and under `--max-call-depth 20` prints the numbers before the STEP_LIMIT / STACK_LIMIT error. So every fatal oracle error already flushes (`driver_main` -> `flush_buf_to_stdio`, `compiler/driver/pipeline.ax:7383`). The task scope says "flush ... before reporting" and the acceptance says "FU-K test shows the prefix before the error": the pinning test satisfies the acceptance, and "not reproducible at HEAD + regression test" is a legitimate outcome of a Fix task (the report documents the evidence). The test is interp-only with a valid reason line (the step limit exists only in the oracle) and checks exact stdout, exit 124 and stderr-contains.
3. Gate per axiom-qa.md: done above. Report has exact `## Files changed`.

### Native-evidence (step 4a)
- All 5 engineer run tests and my 4 run tests have exact `stdout:` and exit values: native legs compare observable output.
- Mutation proof (snapshot only, restored afterwards): changed `// stdout: 101` to `102` in `qa_method_vs_field.ax`; `axtest --no-cache qa_method_vs_field` gave FAIL in interp, native and native-O1 ("stdout differs at byte 2"); restored, 3/3 PASS.
- Cross-mode bytes: every new test has an exact stdout, so interp and native outputs are equal by construction.

### Adversarial probes (step 5; tests added in the main tree)
Parenthesised-callee change in `lower_postfix`:
- `qa_method_vs_field.ax`: struct with both a method `go` and a fn-pointer field `go`. `s.go(1)` and `(s).go(1)` stay method calls (101); `(s.go)(3)` and `((s).go)(3)` call the field (6). All modes PASS. This proves the head_grouped flag is cleared after the first segment.
- `qa_chain_and_nested_parens.ax`: `((m.mk)(0))(8)`, `(m.mk)(0)(8)`, `((g))(4)`, `(((m.mk))(0))(5)`, `(g)(10)`: all PASS in 3 modes.
- `qa_closure_in_field.ax`: non-capturing closure coerced into a fn-pointer field, `(h.f)(3)`, and `(hs[0].f)(9)` on an array of structs: PASS in 3 modes.
- `qa_generic_and_view.ax`: `Holder<i32>` / `Holder<i64>` (two instantiations), `(o.f)(x)` through `view<Ops>` and `mut_view<Ops>` parameters: PASS in 3 modes.
- `qa_noncallable_field_ui.ax` (`// test: ui`): `(s.n)(1)` -> `AX_TYPE_NOT_CALLABLE`, `(s.missing)(1)` -> `AX_TYPE_UNKNOWN_FIELD`, `s.n(1)` (ungrouped, field is not a method) -> `AX_TYPE_UNKNOWN_FIELD`: PASS, so a non-callable grouped callee is diagnosed and not silently turned into a method call.
- Backend half (`lower_call_terminator`): `fs[1](8)`, `(*p)(6)`, nested field, array-element field all covered by the engineer's tests and mine in native and native-O1.

### Findings
No FAIL findings.

### Notes / Follow-ups (not FAILs, for the architect)
- Pre-existing, unrelated to this change (no parentheses involved): indexing a non-`Copy` array of structs twice to read a fn-pointer field moves the array: `let a = hs[0].f; let b = hs[1].f;` gives `AX_MOVE_USE_AFTER_MOVE` (fn pointers are `Copy`, so reading the field should not move `hs`). Repro on the snapshot compiler: `struct H { f: fn(i32) -> i32 }`, `let hs: [2]H = [...]`, two consecutive `let x = hs[i].f;`. I kept my test at one use per array. An ownership/move-analysis task is suggested.
- FU-K was not reproducible; the original T422 report's observation is probably a limit hit before the output was produced or `2>&1 | head` truncation (as the engineer says). No further action.
- `taskctl snapshot` ignores a file that is only under `locks:` (engineer had to copy lower.ax by hand): harness behaviour already recorded 2026-11-18; the orchestrator should add `compiler/hir/lower.ax` to `paths:` or rely on the main-tree copy for the accept (accept regenerates bundles from the final sources).

## Files changed
- tests/run/fn_ptr_field_call/qa_method_vs_field.ax
- tests/run/fn_ptr_field_call/qa_chain_and_nested_parens.ax
- tests/run/fn_ptr_field_call/qa_closure_in_field.ax
- tests/run/fn_ptr_field_call/qa_generic_and_view.ax
- tests/run/fn_ptr_field_call/qa_noncallable_field_ui.ax
- _workspaces/reports/T422b-qa.md

VERDICT: PASS round=0
