---
id: T144
title: Selfhost bundle freshness - every bundle is regenerated from HEAD compiler/ sources and checked
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T085, T146]
priority: 115
status: todo
attempts: 0
paths: [tests/selfhost]
spec: [spec/decisions/ADR-0034-oracle-independence.md, spec/SPEC-20-selfhost.md, tasks/0361]
covers: [REQ-TST-089]
timeout_min: 240
---
# T144 — Selfhost bundle freshness checks

## Goal
Every selfhost test that embeds code from `compiler/` embeds the code at HEAD, and a test fails as
soon as `compiler/` and the bundle diverge, so that the selfhost evidence is about the code axiomc is
actually built from (ADR-0034 §1; audit OI-11).

Audit OI-11: `tests/selfhost/kernel/qa_kernel_hash.ax` differs from `compiler/kernel/hash.ax`;
`tests/selfhost/drop/gen_drop_tests.py` says its front end comes from "copies QA accepted with T082a,
because the compiler/ front-end files at HEAD do not build together"; only 3 of 9 generators have a
`check` mode and only drop has a manifest (`drop_oracle.test`).

## Scope
- Every generator under `tests/selfhost/**/gen_*.py` gains a `check` mode (regenerate into a temp
  dir and byte-compare with the committed bundles and goldens) and a manifest
  `tests/selfhost/<area>/bundles_current.test` that runs it (pattern:
  `tests/unit/kernel/hash_vectors_current.test`). Generators read `compiler/` at HEAD; private copies
  of compiler modules inside generator directories are removed.
- Hand-written bundles under `tests/selfhost` that embed a `compiler/` module are either converted to
  generated bundles (embedding the real module) or reduced to test-only code that does not
  re-declare compiler functions; the report lists each with its decision.
- Regenerate all bundles from HEAD; goldens produced by axiom0 are regenerated with the fresh
  snapshot build. Every changed golden is explained. If HEAD modules do not build together (the
  `gen_drop_tests.py` caveat), the failure is listed in `## Follow-ups` (module, error) — the
  architect files the port fix task, which T086 then depends on; the stale copy is not kept as a
  workaround.

## Acceptance
- [ ] Every `gen_*.py` under `tests/selfhost` has `check`; each area with a generator has a
      `bundles_current.test`; all pass in `build-snap-T144`.
- [ ] Negative check in the report: editing one function in a `compiler/` module embedded by a bundle
      makes that area's `bundles_current.test` FAIL.
- [ ] No file under `tests/selfhost` re-declares a `compiler/` function with a different body
      (script or grep evidence in the report).
- [ ] Full suite passes in `build-snap-T144` with native legs.
- [ ] Report `_workspaces/reports/T144-report.md` with exact `## Files changed`.

## Out of scope
- Fixing port code under `compiler/` (follow-ups); new selfhost coverage.

## Notes
- Depends on T085 (its `tests/selfhost/obj_link_driver` generator) and T146 (last task regenerating
  selfhost bundles before T086; T134, T140, T141 precede it). T086 depends on this task.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.

## Log
