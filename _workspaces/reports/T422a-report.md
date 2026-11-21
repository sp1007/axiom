# T422a report

Fix for T422 FU-A (`a.f < b.g` parsed as generic arguments) and FU-J (generic function `g<F>` unusable as a value).

## Summary

### FU-A (parser, `compiler/syntax/parse.ax`)
`parse_dot_suffix` parsed `.name<` with the non-speculative `parse_generic_args`, which reports errors (`AX_PARSE_EXPECTED_TOKEN: Expected '>'`)
and, when the list was not followed by `(`, rewound only the position (not split `>>` tokens). It now uses `try_generic_args` with a new
follow mode `GENERIC_ARGS_FOLLOW_CALL` (only `(` without a line break commits). A failed tentative parse reports nothing and restores
split tokens, so `other.deadline_ns < self.deadline_ns {` and `x.n < y.n >> 1` are comparisons. `x.m<u32>(1)` still is a generic method call.

### FU-J (parser + MIR builder)
- Parser: a path expression `g<F>` whose generic list is followed by a call/dot (as before) **or by an expression terminator**
  (`;` `,` `)` `]` `}` EOF, or a line break when the list has exactly one argument) now commits to generic arguments
  (new follow mode `GENERIC_ARGS_FOLLOW_VALUE`). `a < b > <terminator>` can never be a comparison (the `>` would have no right
  operand), so the widening is safe. `a < b > c` (operand on the same line) is still `AX_PARSE_CHAINED_COMPARISON`; `f(a < b, c >` + newline + `d)`
  stays two comparisons (line-break follower only for one argument).
- Typeck needed no change: `check_expr_flow_or_cast` already records the explicit/inferred substitutions in `expr_substs` for a path
  and `instantiate_path` gives the instantiated `fn` type.
- MIR (`compiler/mir/builder.ax`): the "redirect the function constant to the monomorphized instance" block that lived inline in the
  call lowering was extracted unchanged into `mb_redirect_generic_fn_const` and is now also applied when a path to a function is
  lowered as a value operand. Before, `g<u32>` as a value kept the generic symbol (all instantiations behaved like one: `size_of<T>()`
  printed 8 for every T). Works in interp, native and native-O1. As a bonus an inferred generic function value (`let f: fn(i32) -> i32 = id;`)
  now also lowers to its instance.

## Tests
- `tests/parse/generic_args_ambiguity/`: goldens `field_lt_comparison`, `field_lt_shift`, `method_generic_call` (generic method call and the
  documented commit of `v.len < a > (b)`), `fn_value` (values in let/argument/array, no-semicolon newline form, call, `f < g` comparison),
  `chained_comparison` (+ `.test` asserting `AX_PARSE_CHAINED_COMPARISON`, exit 1), `field_lt_no_diag.test` (exit 0).
- `tests/run/generic_fn_value/`: `fn_value_basic` (`id<i32>`, as argument, `twice<i32>`), `fn_value_two_instances` (distinct `size_of<T>`
  per instantiation, `tag<T>` formed inside generic `make<T>`), `fn_value_nested_generic` (`id<Box2<i32>>` with split `>>`, field `<` shift).
  Each has exact `// stdout:`; modes interp, native, native-O1 (WEAK-NATIVE 0).

## Results (in `build-snap-T422a`, Release stage 0, `axiomc2.exe` built from the snapshot, `-j 2`)

- Own tests: 10 ids / 16 results, 16 PASS (interp, native, native-O1 for the run tests), WEAK-NATIVE 0.
- `python tools/taskgate.py --task T422a ...`: exit 0, archcheck clean (229 files, 0 violations), `TOTAL 493 PASS 491 FAIL 0 SKIP 2 XFAIL 0`
  (own 16, affected 445 incl. the selfhost groups of `compiler/syntax` and `compiler/mir`, smoke 51), wall time 1194 s. No failing id, so
  failing ids are a subset of the baseline. The 2 SKIPs are pre-existing skips in the affected set.
- Stage-1/2/3 bootstrap of `axiomc` with the changed parser and MIR builder: BUILD-AXIOMC OK, stage-0 guard identical.
- Pre-existing issue noted (not caused here): `tests/selfhost/**` bundle files appeared in the snapshot change set because the snapshot
  regenerates them; they are not listed below (harness-owned).

## Spec deviations / questions (for the architect)
1. **AXS-GRM-056 follower set widened** (the "wider follower set" row in SPEC-02 section 12): in addition to `(`, `.`, `{`, generic
   arguments in expression position commit when followed by `;` `,` `)` `]` `}` end of input, or (single argument only) a line
   break. Rationale above; needed for `let f: fn(..) = g<F>;`.
2. **After `.name`, generic arguments commit only when followed by `(`** (no `.`/`{`), i.e. a field access followed by `<` is never generic. A call-like
   `v.len < a > (b)` still commits to `len<a>(b)` per the commit rule. SPEC-02 only says "after a `Name` segment"; this is the
   implemented form of "field access never takes generic arguments" except for the call form.
3. Method values `x.f<T>` (without call) are not supported (not requested).
4. Known issue from T445 QA (`>>` in nested generics): the paths touched here (`.name<...>` and path values) split `>>` correctly and roll the split
   back on failure (tests `fn_value_nested_generic`, `field_lt_shift`). Other contexts were not investigated (out of scope).
5. `bootstrap/axiom0` (C stage 0, frozen) was not changed; compiler sources must not use the new value form until stage 0 parses it.

## Files changed
- compiler/syntax/parse.ax
- compiler/mir/builder.ax
- tests/parse/generic_args_ambiguity/chained_comparison.ax
- tests/parse/generic_args_ambiguity/chained_comparison.ast
- tests/parse/generic_args_ambiguity/chained_comparison_diag.test
- tests/parse/generic_args_ambiguity/field_lt_comparison.ax
- tests/parse/generic_args_ambiguity/field_lt_comparison.ast
- tests/parse/generic_args_ambiguity/field_lt_no_diag.test
- tests/parse/generic_args_ambiguity/field_lt_shift.ax
- tests/parse/generic_args_ambiguity/field_lt_shift.ast
- tests/parse/generic_args_ambiguity/fn_value.ax
- tests/parse/generic_args_ambiguity/fn_value.ast
- tests/parse/generic_args_ambiguity/method_generic_call.ax
- tests/parse/generic_args_ambiguity/method_generic_call.ast
- tests/run/generic_fn_value/fn_value_basic.ax
- tests/run/generic_fn_value/fn_value_two_instances.ax
- tests/run/generic_fn_value/fn_value_nested_generic.ax

STATUS: COMPLETE round=0
