# T428m report — resolver binds paths inside generic arguments

## Summary (attempt 1, before the unblock — kept as history; see "Round 0b" below for the final state)
`compiler/resolve/resolver.ax` now resolves every generic argument of every path segment, in the scope of the path
that carries it (SPEC-02 AXS-GRM-080). With this fix the bindings reach HIR unchanged: the `--emit=resolved` and
`--emit=hir` goldens show `Foo` bound inside `Option<Foo>`. Qualified arguments (`Option<a.S>`, `Result<b.S, a.S>`)
now resolve, compile and run in all three modes.

The fix exposes **one fallout site in `compiler/`**, which is outside this task's paths/locks: `compiler/interp/frame.ax`
uses `size_of<InterpAlloc>()` without importing `InterpAlloc`. Before the fix the name was never resolved, and typeck's
bare-name walk found it anyway. As the task requires, I did not patch the file in the main tree. The task is
**BLOCKED** on that one-line import.

With the import applied in the snapshot only (to measure the rest of the fallout), stage 2 builds and the fixed point
holds at `-O0` and `-O1`. The sweep results are below.

## Implementation (compiler/resolve/resolver.ax)
- New helper `resolve_generic_args(scope, g)`. Each argument's type goes through `resolve_type`. For an
  associated-type binding `Item = T`, only `T` is resolved; the name `Item` stays unbound (AstGenericArg.name is a
  bare `StrId`, and typeck matches it against the trait).
- New helper `resolve_path_generic_args(scope, segs)`. It runs the helper on **every** segment of a path (not only the
  last one), before the head lookup, so the arguments are resolved even when the head itself is unresolved.
- Call sites:
  - `resolve_path_seg` calls `resolve_path_generic_args` first. This covers every user of `resolve_path_seg`: type
    paths (`resolve_type` → impl self types, trait paths, generic-param bounds, where-clauses, `dyn` bounds,
    supertraits, fields, params, returns, let/cast/closure types), expression paths (`EXPR_PATH`), struct literals
    (`EXPR_STRUCT`) and pattern paths (`PAT_PATH`/`PAT_STRUCT`).
  - `resolve_expr` / `EXPR_POSTFIX` calls `resolve_generic_args` on each postfix segment. This covers method-call
    arguments `x.f<S>()` and `Bag<S>.new` chains.
- `resolve_type` also walks `TYPE_SLICE`'s element (`[S]`, e.g. `Option<*const [S]>`). Before, it skipped the element
  like the generic arguments, which is the same class of bug. Design choice: I included it because a generic
  argument is "a type like any other".
- Kept unchanged:
  - The T447 rule (`F.Output` on a generic parameter stays unbound with no diagnostic; checked in `positions.resolved`).
  - `Self` / `Self.X` handling (`Option<*const Self>` binds to the impl's `Self`).
  - The lowering sentinels. The parser marks `i128`/`u128`/`never` paths as `TYPE_PATH | 128u8`, which
    `resolve_type` does not visit, so no `AX_NAME_UNRESOLVED` is raised for them at all. An unresolved `Future`
    still goes through `lower_path_into`'s `suppress_unresolved_at_span`. Checked: `Option<i128>`, `Option<never>`
    and `Result<u128, Option<i128>>` raise no diagnostic (`unresolved_arg.ax`), and `Option<i128>` runs in all
    modes (`same_name_types`).

## compiler/hir/lower.ax — not changed
`lower_path_into` lowers the last segment's arguments through `lower_generic_args` → `lower_type` →
`lower_path_into`, which reads `get_symbol` / `lower_path_domain` by AST node. Postfix-segment arguments (818–842)
also go through `lower_generic_args`. `Bag<S>.new(..)` parses as `EXPR_PATH Bag<S>` followed by the postfix `.new`,
so its arguments are on the last path segment and reach HIR with their symbol.

The goldens confirm this: `option_local_hir.hir` shows `(TypePath @31 (GenericArg "" (TypePath @25)))`, where HEAD
gives `(TypePath)`.

A multi-segment expression path's **non-last** generic arguments are not represented in `HirPath` at all (it has one
`generic_args`). That was true before this task, and this task does not change it. The resolver binds them, but HIR
has no node that could carry the binding.

## Fallout (new diagnostics caused by correct binding)
| site | diagnostic | cause | owner / fix |
|---|---|---|---|
| `compiler/interp/frame.ax:357` | `AX_NAME_UNRESOLVED` at `InterpAlloc` in `size_of<InterpAlloc>()` | `InterpAlloc` not imported; found before only by typeck's bare-name walk | add `use compiler.interp.value.InterpAlloc` (owner of `compiler/interp`, axiom-semantics) |
| `compiler/interp/frame.ax:366` | same | same | same import |

### Tier-1 non-selfhost sweep
Command, run in `build-snap-T428m` with the stage-2 compiler built with the snapshot-only import
(`_workspaces/T428m_sweep.log`):

`axtest --compiler build/axiomc2.exe --id-file <fullrun non-selfhost-ids, 3125 ids> --gate -j 2 --exclude-requires axiom0-internal --baseline ../_workspaces/baseline-failures.txt`

Result: `TOTAL 6704 PASS 6650 FAIL 10 SKIP 37 XFAIL 7`. 2 of the 10 failures are in the baseline (`run/opt_lto/opt_lto_engine.test`,
`ui/security_profiles/safety_profile_safe_neg.ax`).

`BASELINE NOW PASSING`: `conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax` and
`spawn_affinity_vs_migration.ax`. These are the two T428g ids; they stay listed, because T428g removes them.

The 8 failures outside the baseline:

| id | cause | caused by T428m? | needed fix (outside T428m paths) |
|---|---|---|---|
| `resolve/more.ax` | golden: `(PathSegment "T")` in a generic arg is now `(PathSegment @Sym(76) "T")` (+9 bytes, only change) | yes, intended | re-bless `tests/resolve/more.resolved` |
| `hir/more.test` | golden: generic-arg `(TypePath)` is now `(TypePath @76)` (+4 bytes) | yes, intended | re-bless `tests/hir/more.hir` |
| `typeck/generic/generic_subst.ax` | golden: `(TypePath)` is now `(TypePath @2)` | yes, intended | re-bless `tests/typeck/generic/generic_subst.thir` |
| `typeck/async/async_basic_pos.ax` | golden: generic-arg paths now carry symbols (`(TypePath @82)`, `@2`). `Poll<Self.Output>` now binds `Output` to the trait member, which allocates one member symbol id (existing T153 path), so later local ids shift by 1; the types are unchanged | yes, intended | re-bless `tests/typeck/async/async_basic_pos.thir` |
| `ui/resolve/ui_tests.ax` | line 3 `let x: Unknown<T> = 0` now reports `AX_NAME_UNRESOLVED` twice, for `Unknown` and for the undeclared `T` | yes, correct | add a second `//~ ERROR AX_NAME_UNRESOLVED` on line 3 |
| `ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax` | line 82 `FnOnce<MissingBoundTy>` is now reported by the resolver rather than by typeck's name walk. Resolve errors stop the pipeline before typeck, so the typeck diagnostics expected at lines 90 (×2), 94 and 97 are no longer produced | yes, correct | move `impl<R> Bad<R>` (lines 81–86 and its two uses at the end of `main`) into its own ui test |
| `link/dll/gnu_ld_run.test` | Python traceback in `gnu_ld_run_oracle.py` | **no**: fails identically with the HEAD compiler `axiomc2_O1_642250f08b7af786.exe` | pre-existing; not in the baseline |
| `ui/security_profiles/forbid_unsafe_constructs_neg.ax` | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` at `@at(..)` line 45; the SEC diagnostics are missing | **no**: HEAD gives the same single diagnostic | pre-existing; not in the baseline |

### Selfhost groups of compiler/resolve and compiler/hir
Run with `--gate -j 2` (`_workspaces/T428m_selfhost_resolve.log`, `_workspaces/T428m_selfhost_hir.log`).

`selfhost/resolve/qa_resolve_all`, `selfhost/resolve_hir/qa_resolve_hir_all` and `selfhost/hir/qa_hir_all` build and
run, then exit 1. Their `.ax.in` templates embed a `CORPUS_DATA` copy of the same goldens and ui files listed above,
so they fail for the same intended reasons. Failing groups and cases (decoded from `CORPUS_DATA`):
- `tests/selfhost/resolve/qa_resolve_corpus_pos.ax.in`: case `tests/resolve/more.ax`.
- `tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax.in`: case `tests/ui/resolve/ui_tests.ax`.
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax.in`: case `tests/hir/more.ax`.
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax.in`: case `tests/resolve/more.ax`.
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax.in`: case `tests/ui/resolve/ui_tests.ax`.
- `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax.in`: case `tests/typeck/generic/generic_subst.ax`.
- `tests/selfhost/hir/qa_hir_corpus.ax.in`: case `tests/hir/more.ax`.
- `tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in`: the synthetic cases with generic arguments,
  `synth_drop_and_extern.ax` and `synth_pats_and_postfix.ax`. Their embedded expected HIR lacks the new bindings.

These templates (not the generated bundles) must be refreshed together with the goldens above.

### Proposed fix tasks (for the architect)
1. **compiler/interp** (axiom-semantics): add `use compiler.interp.value.InterpAlloc` to `compiler/interp/frame.ax`.
   This one-line import is required for the stage-2 build; without it `build_axiomc` fails at seeded B.
2. **Golden / test refresh** (frontend or QA), after T428m's resolver change is in:
   - re-bless `tests/resolve/more.resolved`, `tests/hir/more.hir`, `tests/typeck/generic/generic_subst.thir` and
     `tests/typeck/async/async_basic_pos.thir`;
   - fix the annotation in `tests/ui/resolve/ui_tests.ax:3`;
   - split `tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax`;
   - refresh the embedded expectations of the 8 selfhost templates listed above.

   Simplest route: extend T428m's `locks:` with these files (and `compiler/interp/frame.ax`). I can then make all of
   them in a fix round, because each change is mechanical and already verified above.

## Tests (tests/resolve/generic_args_binding/)
- `option_local.ax` (+ `.resolved`): `struct Foo` / `fn f() -> Option<Foo>`. `Foo` is `@Sym(25)` inside the
  `GenericArg`.
- `option_local_hir.ax` (+ `.hir`): the generic-arg `TypePath` carries `@25`.
- `positions.ax` (+ `.resolved`) binds every generic-argument position:
  - an expression path `Bag<S>.new(..)` and a callee `sz<Option<S>>()`;
  - a method call `b.conv<S>(..)`;
  - a bound `F: Future<Output = S>`: `Output` unbound, `S` bound;
  - a projection `Option<F.Output>`: `F` bound, `Output` unbound;
  - the nested `Option<Option<Bag<S>>>`, a slice in an argument `Option<*const [S]>`, and `Option<*const Self>`
    in an impl.
- `same_name_types/` (package; run, `modes: interp native`, exact `stdout:`, exit 0). Modules `a` and `b` each define
  `struct S` with different fields. The test covers:
  - `fn pick(o: Option<a.S>)`, `Result<b.S, a.S>` (both arms), `let bs: Option<b.S>`;
  - nested `Option<Bag<b.S>>` and `Bag<a.S>.new(..)`;
  - `impl Future for ReadyA { type Output = a.S }` with `fn proj<F: Future<Output = a.S>>(o: Option<F.Output>)`
    called as `proj<ReadyA>(..)`;
  - `Option<i128>`.

  It prints `11 5 4 7 100 3 42 2 9`. On HEAD it fails to compile (`AX_NAME_UNRESOLVED` at `Option<a.S>`).
- `unresolved_arg.ax` (ui): a misspelled `Option<Fooo>` and a nested `Result<i32, HashMapp<i32, Foo>>` each give
  `AX_NAME_UNRESOLVED` on that line. The sentinels raise no diagnostic.
- `private_arg/` (ui package):
  - `Option<a.Hidden>` (a private struct) gives `AX_NAME_PRIVATE`;
  - `Option<a.Missing>` gives `AX_NAME_UNRESOLVED`;
  - `Option<a.Shown>` is accepted.
- Against the HEAD compiler (`axiomc2_O1_642250f08b7af786.exe`) all 7 legs FAIL. Against the fixed compiler all 7
  PASS (interp, native, native-O1; WEAK-NATIVE 0).
- Test-writing notes (neither is a T428m defect; both reproduce on HEAD):
  - `Vec` is not in a package's prelude, so the test uses a local generic `Bag<T>`. This is also why
    `Option<Vec<b.S>>` was accepted before: its argument was never resolved.
  - A value of type `Option<never>` gives `AX_TYPE_UNKNOWN` in typeck.
  - `Option<view<[S]>>` / `Option<view<Self>>` fail to parse (`>>` after `view<..>` inside a generic list is not
    split); the test uses `*const` instead.

## Build / fixed point
- `build_axiomc.py --out build --root . --opt both` in `build-snap-T428m` (`_workspaces/T428m_build0.log`):
  seeded A built, then **B failed**. A `check` of the stage-2 bundle with A gives exactly 2 errors, both
  `AX_NAME_UNRESOLVED` at `frame.ax:357/366` (`_workspaces/T428m_checkA.log`).
- With the import added **in the snapshot only** (`_workspaces/T428m_build1.log`):
  - `STAGE1 OK`;
  - `FIXED-POINT (O1) OK` (axiomc2 == axiomc3, sha256 d6b2d87c..);
  - `FIXED-POINT (O0) OK` (sha256 7c869922..);
  - `STAGE0-GUARD OK`;
  - `BUILD-AXIOMC OK`.
- The snapshot-only import was used only for measuring and has been removed again. The main tree's
  `compiler/interp/frame.ax` was never touched.

## Spec deviations / questions
None. AXS-GRM-080 is applied as written.

## Round 0b — after the unblock (`_workspaces/reports/unblock-T428m.md`, task scope item 6)
I applied exactly the fallout fixes the architect allowed; the resolver edits are unchanged.

- **(a)** `compiler/interp/frame.ax`: the single line `use compiler.interp.value.InterpAlloc` (alphabetical
  position, line 55). No other change.
- **(b)** Re-blessed with the snapshot stage-2 compiler (`axtest --bless`, one id each). Diff per file:
  - `tests/resolve/more.resolved`: 1 line, `(PathSegment "T")` → `(PathSegment @Sym(76) "T")` (the `T` of a generic
    argument).
  - `tests/hir/more.hir`: 1 line, `(TypePath)` → `(TypePath @76)`.
  - `tests/typeck/generic/generic_subst.thir`: 1 line, `(TypePath)` → `(TypePath @2)`.
  - `tests/typeck/async/async_basic_pos.thir`: 62 of 272 lines changed, the line count is unchanged, and a script
    classified every changed line:
    - 11 lines only add `@n` to a generic-arg `(TypePath)`;
    - 51 lines are only the +1 shift of local ids ≥ 82 (binding `Poll<Self.Output>` gives the trait member a
      symbol id);
    - 0 other changes.
- **(c)** `tests/ui/resolve/ui_tests.ax`: a second `//~^ ERROR AX_NAME_UNRESOLVED` after line 3 (for the undeclared
  `T`). Later lines shift by one, which matters only for the embedded copies in (e).
- **(d)** I moved `struct Bad<R>` + `impl<R> Bad<R>` and the two `Bad<i64>.bad(..)` calls from
  `qa_adversarial_bounds_reject.ax` into the new `qa_adversarial_bounds_unresolved_fnonce.ax`. The new file expects
  `AX_NAME_UNRESOLVED` at `FnOnce<MissingBoundTy>`, once, even though the method is called twice. The original keeps
  its header (case 4 is now a pointer to the new file) and all 4 typeck expectations: `AX_TYPE_MISMATCH` ×2 at
  `fl.combine`, `AX_TYPE_MISMATCH` at `rn.drive` and `AX_TRAIT_UNSATISFIED_BOUND` at `.accept`. Both files PASS.
- **(e)** The 8 `.ax.in` templates. There is no generator for `CORPUS_DATA`, so I used scratch-only helpers:
  - a reader/writer for `CORPUS_DATA`/`CORPUS_OFF` that round-trips all 8 templates byte-identically and also updates
    the `[N]u8` / `[N]u32` sizes;
  - a "dump" variant of the 3 merged bundles built in the snapshot. Each `verify_case` prints its actual output and
    diagnostics and never fails;
  - a script that replaces each expected blob with the dumped bytes and refuses to write a template outside the locks.

  Steps:
  - The `ui_tests.ax` **source** blob in both `neg_c` templates was first replaced with the new file.
  - The 5 templates not in `locks:` (`resolve/neg_a`, `neg_b`, `resolve_hir/neg_a`, `neg_b`, `neg_d`, `pos_a`,
    `wide_a`) came out byte-unchanged.

  Changed blobs (all bindings only, apart from the expected ui_tests diagnostics):
  - `resolve/qa_resolve_corpus_pos`: `tests/resolve/more.ax` out (+`@Sym(41)` on the generic-arg `T`).
  - `resolve/qa_resolve_corpus_neg_c`:
    - `test_span.ax` out (+`@Sym(2)` on two `i32` generic args);
    - `ui_tests.ax` src and diag (the new `AX_NAME_UNRESOLVED` at 3:20 and +1 on later line numbers; "6 errors").
  - `resolve_hir/qa_resolve_hir_corpus_neg_c`: `test_span.ax` out (`(TypePath @2)` ×2), and `ui_tests.ax` src and
    diag as above.
  - `resolve_hir/qa_resolve_hir_corpus_pos_b`: `tests/hir/more.ax` out (`(TypePath @56)`).
  - `resolve_hir/qa_resolve_hir_corpus_pos_c`: `tests/resolve/more.ax` out (`(TypePath @56)`).
  - `resolve_hir/qa_resolve_hir_corpus_wide_b`: `generic_subst.ax` out (`(TypePath @2)`).
  - `hir/qa_hir_corpus`: `tests/hir/more.ax` out (`(TypePath @41)`).
  - `hir/qa_hir_desugar_and_drop`: `synth_pats_and_postfix.ax` out (`(TypePath @2)` ×2).
    `synth_drop_and_extern.ax` did not change.

  `test_span.ax` is a case the attempt-1 list did not name. It sits inside the two locked `neg_c` templates, and its
  only change is new bindings. After the update the dry run reports every template unchanged.

### Verification (snapshot `build-snap-T428m`, HEAD 1401fb1a = 7ed14320 + a board-only commit)
- `build_axiomc.py --out build --root . --opt both` (Release) (`_workspaces/T428m_build2.log`):
  - `STAGE1 OK`;
  - `FIXED-POINT (O1) OK` (sha256 b5d62469..);
  - `FIXED-POINT (O0) OK` (sha256 43eb6c18..);
  - `STAGE0-GUARD OK`;
  - `BUILD-AXIOMC OK`, exit 0.
- Own tests (`tests/resolve/generic_args_binding`, 7 ids / 9 legs incl. interp, native, native-O1): all PASS,
  WEAK-NATIVE 0.
- `taskgate.py --task T428m --changed @_workspaces/T428m_changed.txt` (the exact list below without the report)
  `--compiler build/axiomc2.exe -j 2` (`_workspaces/T428m_taskgate2.log`):
  - `TOTAL 261 PASS 261 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, archcheck clean, smoke-check OK;
  - `TASKGATE T428m exit=0`;
  - WEAK-NATIVE 0 in own/changed tests.
  - The affected set includes `selfhost/resolve/qa_resolve_all.ax`, `selfhost/resolve_hir/qa_resolve_hir_all.ax`,
    `selfhost/hir/qa_hir_all.ax`, `selfhost/interp/qa_interp_all.ax`, every `bundles_current.test` that embeds the
    resolver, the 4 re-blessed goldens, both ui files and `ui/resolve/ui_tests.ax`.
- The Tier-1 non-selfhost sweep was run in attempt 1 with the same resolver (results above). Its only failures
  caused by T428m are exactly the items fixed in this round, and all of them pass in this gate. The two `e11_5` ids
  pass; they stay listed for T428g. `link/dll/gnu_ld_run.test` is now handled by the baseline (T423j).

## Round 1 - QA finding (`_workspaces/reports/T428m-qa.md`)
- **Finding 1:** `selfhost/typeck/qa_typeck_all.ax` failed in all three modes. The cause was that
  `tests/selfhost/typeck/qa_typeck_a.ax.in` embeds the old expected THIR for `tests/typeck/generic/generic_subst.ax`
  (an unbound `(TypePath)`). My round-0 gate missed it because its `--changed` list left out the regenerated bundles.
- **Fix:** the architect added the template to `locks:`. I refreshed that one embedded case with the same
  binding-only method as the other 8 templates:
  - I extended the scratch `TC_DATA`/`TC_OFF` reader/writer to these array names; it round-trips the template
    byte-identically.
  - I built a dump variant of the snapshot's regenerated `qa_typeck_all.ax` with the snapshot stage-2 compiler.
    Its `run_golden_case` prints the actual THIR and diagnostics.
  - The new bytes come from that real output:
    - `tests/typeck/basic.ax`: output unchanged, 0 diagnostic bytes;
    - `generic_subst.ax`: 370 -> 373 bytes, one line `(TypePath))` -> `(TypePath @2))`, 0 diagnostic bytes.
  - Only that blob, `TC_DATA`'s size (2325 -> 2328, also in `get_sv`/`run_golden_case`) and the `TC_OFF` values
    changed; `TC_OFF` keeps its 7 entries. A second dry run reports both cases unchanged.
- **QA tests:** QA's 5 tests under `tests/resolve/generic_args_binding/` are kept (`qa_unresolved_positions.ax`,
  `qa_shadow_use/`, `qa_nested_qualified/`) and listed below.
- **Snapshot** `build-snap-T428m` (HEAD 54a3b917; no compiler/std/bootstrap change since round 0), refreshed with
  `taskctl.py snapshot T428m`; bundles regenerated (36 generators, 60 files).
  - `build_axiomc.py --out build --root . --opt both --stage 3` (clang, Release; `_workspaces/T428m_build3.log`):
    - axiom0, axiomc1 and stage 2/3 reused by content hash;
    - `FIXED-POINT (O1) OK` b5d62469.. == axiomc3_O1;
    - `FIXED-POINT (O0) OK` 43eb6c18.. == axiomc3_O0;
    - `BUILD-AXIOMC OK`, exit 0.
- **Taskgate** (`_workspaces/T428m_taskgate_r1.log`):

  `taskgate.py --task T428m --changed @_workspaces/T428m_changed_r1.txt --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`

  The change set is the 42 paths from `taskctl changes T428m` plus the 22 `tests/selfhost/generated-files.txt`
  entries that differ from HEAD in the snapshot. That list includes `tests/selfhost/typeck/qa_typeck_all.ax`, so the
  id is selected.
  - own 10 ids / 14 results: all PASS;
  - affected 134 / 263: 262 PASS, 1 SKIP (QA's run had the same SKIP 1);
  - smoke 35 / 58: all PASS;
  - `TOTAL 315 PASS 314 FAIL 0 SKIP 1`; `selfhost/typeck/qa_typeck_all.ax` passes;
  - `BASELINE OK`, archcheck clean, smoke-check OK, unmatched changed files: none;
  - WEAK-NATIVE 0 in own/changed tests;
  - `TASKGATE T428m exit=0`.

## Files changed
- compiler/resolve/resolver.ax
- compiler/interp/frame.ax
- tests/resolve/more.resolved
- tests/hir/more.hir
- tests/typeck/generic/generic_subst.thir
- tests/typeck/async/async_basic_pos.thir
- tests/ui/resolve/ui_tests.ax
- tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax
- tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_unresolved_fnonce.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax.in
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax.in
- tests/selfhost/hir/qa_hir_corpus.ax.in
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in
- tests/selfhost/typeck/qa_typeck_a.ax.in
- tests/resolve/generic_args_binding/option_local.ax
- tests/resolve/generic_args_binding/option_local.resolved
- tests/resolve/generic_args_binding/option_local_hir.ax
- tests/resolve/generic_args_binding/option_local_hir.hir
- tests/resolve/generic_args_binding/positions.ax
- tests/resolve/generic_args_binding/positions.resolved
- tests/resolve/generic_args_binding/unresolved_arg.ax
- tests/resolve/generic_args_binding/same_name_types/axiom.toml
- tests/resolve/generic_args_binding/same_name_types/src/a.ax
- tests/resolve/generic_args_binding/same_name_types/src/b.ax
- tests/resolve/generic_args_binding/same_name_types/src/main.ax
- tests/resolve/generic_args_binding/private_arg/axiom.toml
- tests/resolve/generic_args_binding/private_arg/src/a.ax
- tests/resolve/generic_args_binding/private_arg/src/main.ax
- tests/resolve/generic_args_binding/qa_unresolved_positions.ax
- tests/resolve/generic_args_binding/qa_shadow_use/axiom.toml
- tests/resolve/generic_args_binding/qa_shadow_use/src/a.ax
- tests/resolve/generic_args_binding/qa_shadow_use/src/b.ax
- tests/resolve/generic_args_binding/qa_shadow_use/src/main.ax
- tests/resolve/generic_args_binding/qa_nested_qualified/axiom.toml
- tests/resolve/generic_args_binding/qa_nested_qualified/src/a.ax
- tests/resolve/generic_args_binding/qa_nested_qualified/src/main.ax
- _workspaces/reports/T428m-report.md

STATUS: COMPLETE round=1
