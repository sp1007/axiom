---
id: T435
title: Baseline fix — selfhost drop bundles (d01..d09) independent of prelude contents
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452, T432]
priority: 14
status: todo
attempts: 0
timeout_min: 900
paths: [tests/selfhost/drop]
locks: [tests/selfhost, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-12-drop.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-089, REQ-BOOT-085]
---
# T435 — Baseline fix: selfhost drop bundles independent of prelude contents

## Goal
The `tests/selfhost/drop` bundles (`qa_drop_d01.ax` .. `qa_drop_d07.ax`, `qa_drop_d09.ax`) pass again in interp,
native and native-O1, and stay green when the implicitly loaded prelude grows.

## Scope
- Observed at HEAD (T421-qa §B, T452 implementer): every bundle returns 300 (`PASS_BUILD` of case 0 differs): the
  Axiom MIR builder output (`compiler/mir/builder.ax`, embedded) differs from the committed C-builder fixtures
  `tests/selfhost/drop/fixtures/*.pre.mir`, e.g. `type#17` vs `type#21`. The +4 shift matches the type items T406/T416
  added to `std/core/prelude.ax`. Confirm the difference is only type-id numbering (or name the real MIR differences).
- Decision ADR-0041 §2 D2: the bundle tests the builder, not the prelude. Make the comparison independent of std
  contents, preferably by (a) building the cases against a pinned, minimal prelude/std root owned by this test
  directory, or (b) canonicalising type ids by first occurrence in both outputs, documented in `gen_drop_tests.py`.
  Regenerate fixtures and bundles only with their generators (`gen_drop_tests.py`, `drop_oracle.test` flow); never
  hand-edit a fixture. If a real builder difference remains, it is a `compiler/mir` bug: stop and report it for a split.
- Run the complete group `selfhost/drop/*` (d10..d12 included) and remove the T435 lines from the baseline.

## Acceptance
- [ ] `selfhost/drop/qa_drop_d01.ax` .. `d07`, `d09` pass in `interp`, `native`, `native-O1` (exit 0, exact checks)
  under `axiomc2.exe` built in `build-snap-T435`; `selfhost/drop/bundles_current.test` and `drop_oracle.test` pass.
- [ ] Mutation proof in the report: one fixture byte changed makes the bundle fail (exit 300) in all three modes.
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0.
- [ ] The T435 lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T435-report.md` with exact `## Files changed`.

## Out of scope
- Editing `compiler/mir` (a builder bug found here becomes a new task). `bootstrap/axiom0` (frozen). `docs/`.

## Notes
- Depends on T432 because a prelude change there would shift the type ids again.
- Build/test in `build-snap-T435` with `tools/build_axiomc.py` and `tools/axtest.py --exclude-requires axiom0-internal`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
