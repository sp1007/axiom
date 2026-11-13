---
id: T432
title: Baseline fix — prelude/std regressions after the P11 prelude additions (prelude_implicit, async block_on ambiguity, derive, generic method)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452, T434]
priority: 13
status: todo
attempts: 0
timeout_min: 900
paths: [std/core, std/future, std/sync, tests/modules/prelude_implicit, tests/typeck/async, tests/std/core/qa_generic_method.ax, tests/run/trait2, tests/std/channel]
locks: [tests/selfhost, compiler/types/typeck.ax, compiler/resolve, compiler/traits, compiler/driver, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-31-atomics.md, spec/SPEC-33-async.md, spec/SPEC-04-core-extensibility.md, spec/SPEC-61-reflection-derive.md]
covers: [REQ-CONC-014, REQ-ASY-023]
---
# T432 — Baseline fix: prelude/std regressions after the P11 prelude additions

## Goal
The 5 ids listed for T432 in `_workspaces/baseline-failures.txt` pass again, and the implicitly loaded prelude no
longer introduces colliding bare names.

## Scope
- Ids: `modules/prelude_implicit` (`AX_LINK_UNDEFINED_SYMBOL prelude_loaded`), `typeck/async/async_basic_pos.ax`
  (`AX_TRAIT_AMBIGUOUS_METHOD` in `std/future/block_on.ax:16`), `std/core/qa_generic_method.ax`,
  `run/trait2/test_derive.ax`, `std/channel/check_channel_bundles.test` (freshness check of generated std bundles:
  regenerate with its generator once the std sources are fixed).
- ADR-0041 §2 D4: `std/core/prelude.ax` (T406, T416) now declares an atomic-memory `Ordering`, `CasResult`, `Atomic`
  directly, while `std/core/cmp.ax` and `std/sync/atomic.ax` declare their own `Ordering`. Determine whether these
  duplicates cause the ambiguity/derive/generic-method failures. If confirmed: `std.sync.atomic` holds the single
  definition of the memory-ordering enum (SPEC-31), and the prelude keeps only what lang-item lookup needs, under
  non-colliding names or via `pub use`. If lang-item lookup really requires the prelude location, keep it there but
  make the bare name unambiguous and record why in the report (ADR-0041 Revisit).
- `prelude_loaded` undefined at link: find why the prelude function is referenced but not emitted (prelude item
  collection in the build path) and fix at the root; a fix in `compiler/types/typeck.ax`, `compiler/resolve`,
  `compiler/traits` or `compiler/driver` is allowed (locked); other areas are reported for a split.
- Keep the existing atomics/async suites green (`tests/run/atomics`, `tests/mir/atomics`, `tests/ui/concurrency/atomics`,
  `tests/std/async`, `conformance/p11`): they are in the complete run.
- Regenerate selfhost bundles that embed edited modules; remove the T432 lines from the baseline.

## Acceptance
- [ ] The 5 ids pass in all their modes under `axiomc2.exe` built in `build-snap-T432`.
- [ ] Regression test `tests/modules/prelude_implicit/` or `tests/typeck/async/` case: a user file that uses both
  `std.core.cmp.Ordering` and `std.sync.atomic.Ordering` by path compiles and runs (interp + native, exact stdout).
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  `archcheck.py` clean; every `tests/selfhost/**/bundles_current.test` passes.
- [ ] The T432 lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T432-report.md` with each root cause and exact `## Files changed`.

## Out of scope
- `std/async/*` and `tests/std/async/*` (T421 done, T422 running). `bootstrap/axiom0`. `docs/`.

## Notes
- After T434 so the dump goldens are already green and any remaining dump change is attributable to this task.
- Build/test in `build-snap-T432` with `tools/build_axiomc.py` and `tools/axtest.py --exclude-requires axiom0-internal -j 2`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
