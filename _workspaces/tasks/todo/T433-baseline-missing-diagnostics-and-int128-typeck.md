---
id: T433
title: Baseline fix — data-race / unsync-static / unknown-field diagnostics, inverted-slice panic, one-line items, int128 typeck
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452, T432]
priority: 17
status: todo
attempts: 0
timeout_min: 900
paths: [tests/ui/concurrency/data_race, tests/conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax, tests/ui/struct, tests/run/slice/qa_slice_inverted_panic.ax, tests/run/parse/terminator_one_line_items.ax, tests/typeck/int128]
locks: [tests/selfhost, compiler/types/typeck.ax, compiler/own, compiler/verify, compiler/syntax, compiler/mir/builder.ax, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-30-concurrency.md, spec/SPEC-11-capability.md, spec/SPEC-03-core-semantics.md, spec/SPEC-40-integers.md, spec/diagnostics.md]
covers: [REQ-CONC-004, REQ-CONC-065, REQ-SIMD-176]
---
# T433 — Baseline fix: missing diagnostics/panics and int128 typeck

## Goal
The 7 ids listed for T433 in `_workspaces/baseline-failures.txt` pass again: the compiler produces the diagnostics and
panics these tests encode.

## Scope
- Ids: `ui/concurrency/data_race/unsync_static_and_unsafe_reentry.ax`,
  `ui/concurrency/data_race/view_not_share_rejected.ax`,
  `conformance/p11/e11_1_concurrency/ui_unsync_mutable_statics.ax`, `ui/struct/unknown_field.ax` (expected diagnostics
  not produced), `run/slice/qa_slice_inverted_panic.ax`, `run/parse/terminator_one_line_items.ax`,
  `typeck/int128/int128_literals_and_methods.test`.
- For each: run with `-v`, find the commit that broke it (`git log` on the owning compiler area; T402/T406/T416/T429
  are likely), and restore the rule in the compiler. The tests encode spec rules (SPEC-30 `REQ-CONC-004`, SPEC-11
  `view` is not `Share`, `AX_TYPE_UNKNOWN_FIELD`); change a test expectation only if the report quotes the spec rule
  that makes the new output correct.
- `typeck/int128/int128_literals_and_methods.test` may already pass after T452: then only remove its line.
- Fixes are allowed in the locked areas (`compiler/types/typeck.ax`, `compiler/own`, `compiler/verify`,
  `compiler/syntax`, `compiler/mir/builder.ax`); anything else is reported for a split. Each fix gets a regression
  test beside the failing one.
- Regenerate selfhost bundles that embed edited modules; remove the fixed T433 lines from the baseline.

## Acceptance
- [ ] The 7 ids pass in all their modes under `axiomc2.exe` built in `build-snap-T433`.
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  `archcheck.py` clean; every `tests/selfhost/**/bundles_current.test` passes.
- [ ] The fixed lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T433-report.md` with each root cause (breaking commit) and exact `## Files changed`.

## Out of scope
- `std/async`, `tests/std/async` (T422). `bootstrap/axiom0`. `docs/`.

## Notes
- After T432 so prelude naming is settled before typeck diagnostics are restored.
- Build/test in `build-snap-T433` with `tools/build_axiomc.py` and `tools/axtest.py --exclude-requires axiom0-internal -j 2`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
