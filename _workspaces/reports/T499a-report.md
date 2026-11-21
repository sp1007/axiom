# T499a report — tuple expressions naming a variable

## Round 0

### Root causes
1. **Resolver (`compiler/resolve/resolver.ax`, `resolve_expr`)**: the expression walk had a branch for every AST expression
   kind except `EXPR_TUPLE` (the `rd_expr` dumper had one, the resolver walk did not). The elements of `(a, b, ...)` were never
   visited, so every name inside a tuple expression stayed unbound in the `ResolveMap`. Literals do not need a binding, which is why
   only literal tuples worked. The parser was correct (`inspect --emit=ast` shows `ExprTuple (ExprPath x) (ExprLiteral)`).
2. **Why a local gave `AX_NAME_UNRESOLVED` and a parameter crashed**: HIR lowering produced an `ExprPath` with symbol 0. Typeck
   (`lookup_path_type_by_name`) has a by-name fallback that matches the current function's parameters by name and returns the
   parameter's type without a symbol. For a `let` local there is no such fallback, so typeck reported `AX_NAME_UNRESOLVED`; for a
   parameter the path was typed but stayed symbol-less, and typeck itself then crashed later on that node (`inspect --emit=thir`
   exits 127 with the pre-fix compiler; QA saw 0xC00000FD). With the resolver fix every name in a tuple expression is bound, so
   neither path is reached from source any more.

### Fix
- `resolve_expr` now walks `EXPR_TUPLE` elements (same list walk as `EXPR_ARRAY`). One branch, no other module changed.
- Decision: the typeck by-name parameter fallback is left as is (not in scope to redesign; it may serve symbol-less synthetic HIR
  from desugarings, and removing it risks regressions far from this task). With the resolver gap closed there is no known source
  input that reaches it with a user name; recorded as follow-up 2.

### Tests
- `tests/run/tuple_expr_names/locals_params.ax`: let locals, parameters (incl. the `s64` repro, annotated `(i64, i32)`),
  unannotated, mixed literal/variable, `(x,)` one-tuple.
- `tests/run/tuple_expr_names/return_and_args.ax`: tail return, `return (v, true)`, call argument `sum((a, b))`, `(a, a)` (T498 QA
  repro that exited 127), the T454 `(total, true)` repro.
- `tests/run/tuple_expr_names/fields_calls_nested.ax`: struct fields, call results, nested tuples of variables, tuple built from
  another tuple's elements with an annotated nested type.
- `tests/run/tuple_expr_names/match_and_destructure.ax`: `let (a, b) = (y, x)`, `match (a, b)` with literal/binding/wildcard arms.
- `tests/ui/tuple_expr_names/unknown_name.ax`, `unknown_name_param.ax`: unknown name in a tuple still `AX_NAME_UNRESOLVED`, exact
  line:col pinned with `stderr-contains` (the second one is next to a parameter in an annotated tuple: diagnostic, no crash).
- `tests/ui/tuple_expr_names/element_mismatch.ax`: `(s64, flag)` into `(i64, i32)` gives `AX_TYPE_MISMATCH`.
- `tests/std/num/tuple_names_xfail.ax`: `xfail` line removed (passes interp + native, its declared modes); comment updated.
- All run tests have exact `// stdout:` and run in interp / native / native-O1.

### Verification (snapshot `build-snap-T499a`, HEAD ce6d671 + T499a)
- `python tools/build_axiomc.py --out build --stage 3`: stage 1 OK, `FIXED-POINT (O1) OK` (axiomc2 == axiomc3, sha256 70d7a6d2...),
  `STAGE0-GUARD OK`.
- Both task repros: `run --interp` and native print `4` / `5`, exit 0 (were `AX_NAME_UNRESOLVED` / exit 127).
- `axtest -j 2 --no-cache run/tuple_expr_names ui/tuple_expr_names std/num/tuple_names`: TOTAL 18 PASS 18, WEAK-NATIVE 0.
- `tools/taskgate.py --task T499a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --no-cache`:
  `TOTAL 175 PASS 174 FAIL 0 SKIP 1 XFAIL 0`, `BASELINE OK`, failing ids none, `archcheck: 232 files scanned, 0 violations`,
  `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`, `TASKGATE T499a exit=0` (log `_workspaces/T499a_taskgate.log`).
- Acceptance groups, `axtest -j 2 --no-cache --exclude-requires axiom0-internal`:
  - `run`: `TOTAL 2997 PASS 2997 FAIL 0` (WEAK-NATIVE 125, all pre-existing, none under `tuple_expr_names`; log `_workspaces/T499a_run.log`).
  - `ui std/num selfhost/{hir,resolve,resolve_hir,typeck,typeck_traits,types}`: `TOTAL 628 PASS 615 FAIL 2 SKIP 1 XFAIL 10`, WEAK-NATIVE 0
    (log `_workspaces/T499a_suites.log`). The 2 FAILs `ui/slice/iter_move.ax` and `ui/slice/qa_slice_iter_move.ax` (missing
    `AX_CAP_OUTLIVES_OWNER` after `consume(arr)` of a `[4]u8` that a view borrows) are pre-existing: the HEAD-input seed compiler
    `_workspaces/artifacts/compiler-cache/axiomc2_O1_1bd4d542497166fe.exe` fails both identically. Probably from T498 (fixed arrays of
    Copy are Copy, so `consume(arr)` no longer moves `arr`); not in the baseline file — follow-up 4.

### Spec deviations / questions
- None for this fix.

### Follow-ups (pre-existing, not caused by T499a)
1. **Exhaustiveness of tuple patterns** (`compiler/types/exhaust.ax`, not in this task's locks): `match (1i64, 2i64) { (p, q) => p + q }`
   and `match t { (p, _) => p }` report `AX_PAT_NON_EXHAUSTIVE` although an all-binding tuple pattern is irrefutable (also with
   literal scrutinees, so independent of this bug). `match_and_destructure.ax` adds a trailing `_` arm to work around it.
2. **Typeck by-name parameter fallback** (`compiler/types/typeck.ax` `lookup_path_type_by_name`, end): types a symbol-less path that
   matches a parameter name, after which typeck crashes on the node. Any future resolver gap would turn into a compiler crash instead of
   `AX_NAME_UNRESOLVED`; suggest the fallback either bind the parameter symbol or report the error, after checking which synthetic
   HIR relies on it.
3. `std/core/num.ax` `pair_T` workaround can now be removed (std follow-up, out of scope).
4. `ui/slice/iter_move.ax`, `ui/slice/qa_slice_iter_move.ax` fail at HEAD ce6d671 without T499a (see Verification); the test
   expectation or the T498 Copy rule needs an architect decision (a Copy array passed by value while viewed is not a move).

## Files changed
- compiler/resolve/resolver.ax
- tests/run/tuple_expr_names/locals_params.ax
- tests/run/tuple_expr_names/return_and_args.ax
- tests/run/tuple_expr_names/fields_calls_nested.ax
- tests/run/tuple_expr_names/match_and_destructure.ax
- tests/ui/tuple_expr_names/unknown_name.ax
- tests/ui/tuple_expr_names/unknown_name_param.ax
- tests/ui/tuple_expr_names/element_mismatch.ax
- tests/std/num/tuple_names_xfail.ax
- _workspaces/reports/T499a-report.md

STATUS: COMPLETE round=0
