# T422b report — fn-pointer field call (FU-2), oracle stdout on step-limit (FU-K)

## Summary
FU-2 had two causes; both are fixed (`compiler/hir/lower.ax` was added to the task's `locks` by the orchestrator).

1. **Frontend (`compiler/hir/lower.ax`, `lower_postfix`).** `(x.f)(args)` / `((*vt).wake)(data)` was lowered to a
   method call, because the parser's `EXPR_PAREN` is stripped before the `POSTFIX_CALL` check; typeck then reported
   `AX_TYPE_UNKNOWN_FIELD` (the `(h.f)()` failure noted in the T422a QA). `lower_postfix` now records whether the AST
   head was a parenthesised expression (`head_grouped`, cleared after the first segment) and only builds
   `HIR_EXPR_METHOD_CALL` for an ungrouped `x.f(args)`; a grouped field callee stays `HIR_EXPR_CALL` with the field
   expression as callee. (The grouping flag is computed through a local: the inline form
   `(unsafe { (*(*e).head).kind })` makes stage 0 ICE with `TypeInterner: invalid id 0`.)
2. **Backend (`compiler/lir/builder.ax`, `lower_call_terminator`).** The callee type of an indirect call was taken from
   the root local of the callee place and ignored projections. For `fs[1](8)`, `(*p)(6)`, `(o.f)(x)` the root local is
   an array / pointer / struct, so the call fell into the "synthesised callee type" path and linked `__ax_fn_0`
   (`AX_LINK_UNDEFINED_SYMBOL`) or used a wrong signature (native `panic: arithmetic overflow`). A callee place with
   `proj_count > 0` now uses `get_place_type`.

## FU-K (oracle stdout on step-limit): not reproducible at HEAD, pinned by a test
`driver_execute_run` returns 124 normally and `driver_main` flushes the buffered stdout (`flush_buf_to_stdio`) after
`driver_run_args`, also when the run ends with the step-limit error. Evidence (snapshot compiler, HEAD + this change):
- a main-thread hang with `--step-limit 50` .. `2000`: `before the hang\n42\n` is written before the diagnostic;
- 30000 numbers printed, then a hang: all 168896 bytes appear;
- a spawned thread that hangs: `main start / main waiting / child start` appear before the error.
No change in `compiler/interp` is needed. `tests/run/interp_step_limit_flush/prefix_before_limit.ax` (interp only,
`exit: 124`, exact `stdout:`, `stderr-contains: step limit exceeded`) guards it. The original T422 observation was
probably a limit hit before the output was produced or `2>&1 | head` truncation.

## Tests
`tests/run/fn_ptr_field_call/` (all `// test: run`, exact `stdout:`, interp / native / native-O1; 15 results, all PASS,
WEAK-NATIVE 0):
- `field_of_struct.ax` (`(o.add)(5, 6)` and via a local), `through_pointer.ax` (`((*vt).wake)(data)` on a raw pointer),
  `nested.ax` (`(o.inner.f)(7)`, `(arr[1].f)(8)`): frontend + backend.
- `index_callee.ax` (`fs[1](8)`), `deref_callee.ax` (`(*p)(6)`): backend only (no parentheses needed).
Mutation evidence: with a compiler without the lir fix `index_callee` fails native and native-O1
(`interp exit 0, native exit 101`); without the lower fix the three field tests fail in every mode with
`AX_TYPE_UNKNOWN_FIELD`.
Not added: a tuple-index callee (`(5, g)` with a fn-pointer local fails resolution with `AX_NAME_UNRESOLVED`, and
tuple-struct constructors are not callable at HEAD; both unrelated, not fixed here).

## Results (snapshot `build-snap-T422b`, HEAD 75e5990 + the files below)
- `python tools/build_axiomc.py --out build`: stage1/2/3 OK, fixed point OK (`_workspaces/T422b_build6.log`).
- `python tools/taskgate.py --task T422b --compiler build/axiomc2.exe -j 2` (`_workspaces/T422b_taskgate2.log`):
  `TOTAL 256 PASS 256 FAIL 0 SKIP 0 XFAIL 0`, `Failing ids: none`, baseline OK, archcheck clean (0 violations),
  WEAK-NATIVE 0 in the task's own/changed tests.
- A first gate run (`_workspaces/T422b_taskgate.log`) showed 15 `selfhost/*/bundles_current.test` failures: not a
  product bug. `taskctl snapshot` skips a file that is only under `locks:`, so I copied `compiler/hir/lower.ax` into
  the snapshot by hand after its bundles had been generated; I regenerated the bundles inside the snapshot
  (`bundles.py regen --root build-snap-T422b`) and the second run is clean. The main-tree bundles were not touched;
  `taskctl accept` regenerates them from the final sources.

## Files changed
- compiler/hir/lower.ax
- compiler/lir/builder.ax
- tests/run/fn_ptr_field_call/field_of_struct.ax
- tests/run/fn_ptr_field_call/through_pointer.ax
- tests/run/fn_ptr_field_call/nested.ax
- tests/run/fn_ptr_field_call/index_callee.ax
- tests/run/fn_ptr_field_call/deref_callee.ax
- tests/run/interp_step_limit_flush/prefix_before_limit.ax
- _workspaces/reports/T422b-report.md

STATUS: COMPLETE round=0
