# T499b report — tuple patterns in the exhaustiveness checker

## Summary
Implemented a column-wise usefulness checker (Maranget, SPEC-03) for `match` on tuple scrutinees in
`compiler/types/exhaust.ax` (`match_check_tuple_exhaustiveness`) and routed tuple scrutinees to it from the
live checker `tc_match_check_exhaustiveness` in `compiler/types/typeck.ax`.

Per `unblock-T499b`:
1. Applied the 5-line routing patch to `compiler/types/typeck.ax` (`use compiler.types.exhaust.match_check_tuple_exhaustiveness`
   and early return in `tc_match_check_exhaustiveness` when `match_check_tuple_exhaustiveness` handles a `TY_TUPLE` scrutinee).
   Removing the duplicate scalar/enum checker in `typeck.ax` is deferred to follow-up task `T499c`.
2. Removed the workaround `_` arm from `tests/run/tuple_expr_names/match_and_destructure.ax` and added positive
   (`tests/run/exhaust_tuple/*.ax`) and negative (`tests/ui/exhaust_tuple/*.ax`) test suites.
3. Removed the stale `// xfail: T454 ...` directive from `tests/std/num/static_dispatch_xfail.ax` and verified
   it passes in `interp`, `native`, and `native-O1`.

## Design (`compiler/types/exhaust.ax` & `compiler/types/typeck.ax`)
- Each matrix row is a vector of patterns. A null pattern is a wildcard, used for fields that
  specialisation introduces. The type of each column picks its constructor family:
  - SINGLE: a tuple or struct. It has one constructor, with one field per element or per declared
    field. Struct patterns are matched by field name, and a missing field counts as a wildcard.
  - BOOL: `false` and `true`.
  - ENUM: one constructor per variant. The variant index comes from `thir_get_pat_variant`, which typeck
    records for PATH and STRUCT patterns. The payload is taken from the `HIR_PAT_TUPLE` payload or from
    named struct-variant fields.
  - INT: integers of 64 bits or fewer, and `char`. Literal and range patterns become intervals in a
    biased unsigned encoding, which keeps the order of signed values. They are split into disjoint
    segments at every interval boundary, so the complete-signature test is exact for
    `i8`/`u8`/…/`u64`/`isize`/`usize`. The `char` domain is `0..=0x10FFFF`.
  - OPAQUE: `i128`/`u128`, unresolved and other types. Only wildcards and bindings cover these.
- Or-patterns are expanded, both at the top level of an arm and nested inside a column. A guarded arm is
  checked for reachability but never adds to the covering matrix.
- A conservative fallback applies whenever the checker cannot classify a pattern. An unknown pattern in
  the matrix covers nothing, so the checker may over-report non-exhaustiveness and never under-reports
  it. An unknown pattern under test is assumed useful, so it never produces a false unreachable warning.
- Diagnostics:
  - `AX_PAT_NON_EXHAUSTIVE` is reported at the span of the match expression, as before.
  - `AX_PAT_UNREACHABLE` is a warning. It is reported for each top-level alternative that the earlier
    unguarded alternatives already cover. This replaces the old rule that only fired after a top-level
    `_` or binding arm, and it is a strict superset of that rule.
- `tc_match_check_exhaustiveness` in `compiler/types/typeck.ax` delegates `TY_TUPLE` scrutinees to
  `match_check_tuple_exhaustiveness`; `exhaust.match_check_exhaustiveness` also sends tuples through the
  same path so `exhaust.ax` stays self-consistent. Non-tuple scrutinees continue using the existing
  scalar/enum checker until `T499c`.
- Decisions:
  - `let (a, b) = t` was already accepted as irrefutable (`typeck.is_pat_irrefutable` recurses into
    tuples); covered in `tests/run/exhaust_tuple/nested_and_enums.ax`.
  - `if let` / `while let` lower to `HIR_EXPR_IF` / `HIR_EXPR_WHILE` and do not invoke
    `tc_match_check_exhaustiveness`; `if let` with a tuple pattern is covered in `nested_and_enums.ax`.

## Files changed
- compiler/types/exhaust.ax
- compiler/types/typeck.ax
- tests/ui/exhaust_tuple/bool_pair_missing.ax
- tests/ui/exhaust_tuple/enum_pair_missing_none_none.ax
- tests/ui/exhaust_tuple/int_range_gap.ax
- tests/ui/exhaust_tuple/payload_and_nested_missing.ax
- tests/ui/exhaust_tuple/unreachable_arms.ax
- tests/run/exhaust_tuple/bool_pairs.ax
- tests/run/exhaust_tuple/ints_and_calls.ax
- tests/run/exhaust_tuple/nested_and_enums.ax
- tests/run/tuple_expr_names/match_and_destructure.ax
- tests/std/num/static_dispatch_xfail.ax
- _workspaces/reports/T499b-report.md

## Tests
All builds and test runs were executed inside `build-snap-T499b/` (`HEAD 49e3f942` + 13 T499b files + 60 regenerated selfhost bundles):

1. Stage-2/3 compiler build:
   `python tools/build_axiomc.py --out build --root . --stage 2` -> `BUILD-AXIOMC OK`.
   - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == bd30530c3d58159d8b50988b654c5300f57ca5d6959adfc10ac01cf775a1ed19` (9,034,752 bytes, seeded `B==C`).
   - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`).
2. Own and changed tests (`--no-cache`):
   `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter exhaust_tuple --filter tuple_expr_names --filter std/num/static_dispatch_xfail -j 2 --verbose`
   -> `TOTAL 43 PASS 43 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
   - Verified `run/exhaust_tuple/*`, `run/tuple_expr_names/*`, and `std/num/static_dispatch_xfail.ax` PASS across `interp`, `native`, and `native-O1` with exact `stdout:`.
   - Verified `ui/exhaust_tuple/*` report exact `AX_PAT_NON_EXHAUSTIVE` and `AX_PAT_UNREACHABLE` diagnostics.
3. Per-task gate (`taskgate.py` at `-j 2`):
   `python tools/taskgate.py --task T499b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   -> `TASKGATE T499b exit=0` (`wall time: 1205.6 s`).
   - `axtest`: `TOTAL 185 PASS 184 FAIL 0 SKIP 1 XFAIL 0` (`own` 10 ids / 20 results; `affected` 82 ids / 133 results incl. `selfhost/typeck`, `selfhost/typeck_traits`, `selfhost/types/qa_types_exhaust.ax`, and all affected selfhost bundles; `smoke` 33 ids / 54 results; 113 dedup ids).
   - `BASELINE OK`, `Failing ids: none`, `WEAK-NATIVE: 0` in own/changed tests.
   - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
   - `smoke-check (tests/smoke.list): OK`, `unmatched changed files: none`.
4. Full `tests/ui/`, `tests/run/`, and `tests/std/num/` suites (`--gate -j 2`):
   `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --gate --baseline _workspaces/baseline-failures.txt --filter ui/ --filter run/ --filter std/num/ -j 2`
   -> `TOTAL 3617 PASS 3610 FAIL 0 SKIP 0 XFAIL 7`, `BASELINE OK`.
5. Board & harness hygiene:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T499b` -> exit 0, 13 files staged, 0 `REFUSED`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

## Spec deviations
none

## Follow-ups
- `T499c` (already filed in `unblock-T499b`): route all scrutinee kinds through `compiler/types/exhaust.ax`, delete the duplicate `tc_match_check_exhaustiveness` copy in `compiler/types/typeck.ax`, and close the bare-enum refutable-payload gap (`Some(1)` + `None`).

STATUS: COMPLETE round=0
