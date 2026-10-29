---
id: T151
title: Port typeck parity - generic calls, generic struct/enum literals and variant paths, try operator, and the typeck stack overflow on ranges/for/operator traits
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T146]
priority: 117
status: done
attempts: 1
paths: [compiler/types, compiler/typeck, compiler/typeck_traits, compiler/traits, compiler/resolve, compiler/hir, compiler/mir, tests/run/parity/generics, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, 0129, 0131]
covers: [REQ-TYP-048, REQ-GEN-001, REQ-BLD-030]
timeout_min: 240
started: 2026-10-28 20:57:07
finished: 2026-10-29 09:10:05
---
# T151 — Port typeck parity: generics and the typeck crash

## Goal
The ported type checker accepts and types every generic construct that axiom0 accepts in the
corpus, and never overflows its stack, so the 22 `no-image` programs below build and run under
axiomc exactly as under axiom0.

Confirmed defects (architect probe 2026-10-20):
1. `AX_TYPE_MISMATCH` on generic instantiation: `id(42)` (`tests/run/generic/qa_basic_fn.ax:9`),
   `Pair<i32> { a: 7, b: 3 }` (`generic/qa_pair.ax`), `Wrapper<i32> { value: 10 }`,
   `Box { value: 42 }`, `Container<C> {..}` (`mono/*`), `Option<i32>.Some(42)`,
   `Result<i32, i32>.Err(1)`, `MyOption.Some(Payload {})`, `?` chains (`result/*`), `Option.Some(cur)`
   in a custom iterator (`for/test_for_custom_iter.ax`); `AX_TYPE_OPERATOR` on `val + 1` after `?`
   (`result/test_try_option.ax`).
2. axiomc (64 MB stack) crashes with `0xC00000FD` during `inspect --emit=thir` on
   `tests/run/slice/{sub_range,disjoint_split,qa_slice_*}.ax` (range sub-slicing), 
   `for/test_for_array.ax` (`for x in [10, 20, 30, 40]`) and `trait2/test_ops.ax` (operator
   traits) — unbounded recursion in the ported typeck.

## Scope
- Find each divergence from `bootstrap/axiom0/src/types` (typeck, inference, generic instantiation,
  enum variant paths, `?` desugaring, range/`Range<T>` typing, operator-trait lookup) and make the port
  follow axiom0; diagnose the recursion (a reduced repro in the report) and remove it.
- `inspect --emit=thir` of every program below equals axiom0's with type ids normalised (type
  interning order itself is T156's).

## Acceptance
- [ ] `tests/run/parity/generics/` (`modes: interp native`, values by hand): `generic_fn.ax` (`id`,
      a two-parameter generic fn, a generic called with two different types — prints both results),
      `generic_struct_enum.ax` (generic struct literal + field sum, `Option<i32>.Some`/`None` matched,
      `Result` `?` propagation returning the error value as exit code), `range_slice.ax` (`s[1..3]`
      length and element sum, `for x in [1, 2, 3]` sum). Pass with axiom0 and are identical under the
      e2e oracle.
- [ ] No corpus program makes the natively built axiomc exit with `0xC00000FD` (checked over the e2e
      corpus run; the report states the root cause of the recursion).
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 22 entries of
      the plan table (`for/test_for_array.ax`, `for/test_for_custom_iter.ax`, `generic/*` 2,
      `mono/*` 5, `result/*` 5, `slice/{disjoint_split,qa_slice_bounds_panic,qa_slice_chained_panic,
      qa_slice_inverted_panic,qa_slice_len_empty,qa_slice_open_ranges,sub_range}.ax`,
      `trait2/test_ops.ax`); an entry left with a residual cause is updated in place and the cause is
      named in Follow-ups; no entry is added.
- [ ] Full suite passes in `build-snap-T151` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T151-report.md` with exact `## Files changed` and the removed
      registry paths.

## Out of scope
- Closures and fn pointers (T152); trait method symbols/default methods/associated types (T153).

## Notes
- Model opus: type inference and instantiation need design judgement when the port's structure
  differs from axiom0's.
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-28 20:57:07 started (attempt 1) T151-impl
- 2026-10-29 09:10:05 accepted by QA -> done
