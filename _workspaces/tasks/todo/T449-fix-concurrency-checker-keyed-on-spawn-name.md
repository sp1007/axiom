---
id: T449
title: Fix — concurrency checker is keyed on the callee spelling `spawn`, not on the spawn contract (FU-E)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452]
priority: 24
status: todo
attempts: 0
timeout_min: 600
paths: [compiler/own/unsafe.ax, tests/ui/concurrency/spawn_contract]
locks: [compiler/types/typeck.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-30-concurrency.md, spec/SPEC-34-executors-fibers.md]
covers: [REQ-TST-072, REQ-TST-035]
---
# T449 — Fix: spawn checks follow the declared contract, not the name

## Goal
The `Send`/`Share`/escaping-view checks of thread and task spawning apply to the functions SPEC-30/34 designate
(lang item / attribute on the std spawn entry points), with correct handling of generic by-value arguments, `view`
arguments and raw-pointer locals; a method merely named `spawn` is not checked (T422 FU-E; ADR-0042 §2).

## Scope
- FU-E repro (T422 report): any call spelled `spawn` is checked; by-value generic arguments are reported as shared
  views (`AX_CONC_VIEW_NOT_SHARE`) unless `Share`; `view` arguments give `AX_CONC_ESCAPING_VIEW`; a raw-pointer local
  passed through a call nested in the arguments gives `AX_CONC_VIEW_NOT_SHARE`. Renaming the method removes the
  diagnostics, so the check is textual.
- Mark the spawn entry points (std thread/async) with the mechanism SPEC-30 names (or, if the spec names none, an
  `@lang`/attribute on the std declarations; record the choice in the report under "Spec deviations" for the
  architect); check generic by-value arguments against `Send` (not `Share`) after substitution.
- UI tests `tests/ui/concurrency/spawn_contract/*`: a user method `spawn` is not checked; real `std.thread.spawn` with a
  non-`Send` capture still fails; generic by-value `Send` argument accepted.
- The existing `ui/concurrency/data_race/*` expectations are T433's; do not change them.

## Acceptance
- [ ] The repros behave as above; every existing `tests/ui/concurrency/*` result is unchanged (baseline ids excepted).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T449-report.md` with exact `## Files changed`.

## Out of scope
- `std/` (a std attribute needed for the mechanism is a one-line edit allowed only in the spawn declarations, list it
  in the report), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-E)
