---
id: T003a
title: Core extensibility contract + exact self-host subset (minimal C scope)
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T003]
priority: 4
status: todo
attempts: 0
paths: [spec/SPEC-04-core-extensibility.md, spec/SPEC-00-bootstrap.md]
spec: [0263, tasks/0260, tasks/0494, 0152, 0056, 0054, 0161, 0162, 0163, spec/ROADMAP.md]
---
# T003a — Core extensibility contract + exact self-host subset

## Goal
Make the C core small, fast and general (ROADMAP R7): axiom0 implements only what self-hosting needs,
but its data models are designed from day one so every later feature (P11–P22) plugs in without
redesign — "implement later ≠ design later" (0263 §42).

## Scope
- SPEC-04-core-extensibility.md: for each core data model — TypeKind, HIR/THIR nodes, MIR
  instructions/terminators/places, LIR, target description, object model, diagnostics — list the
  variants and fields reserved for later epics (async state machines E11.4, atomics & orderings
  E11.2, SIMD/vector types E12.3, raw pointers/volatile/address spaces E13.x, generators E14.3,
  dyn/vtables E14.4, GPU execution domains/device memory E22.x, other targets E16.x, debug info
  E17.x, query engine E18.1, **fixed-address declarations E13.6 / ADR-0001**: item placement
  attribute (overlay | place, const address), `fixed` provenance on places, `Volatile`/`Mmio` volatile
  MIR ops, absolute symbols and address-pinned sections in the object model). Say how each is represented (reserved enum values, extension tables,
  target hooks) and what axiom0 does on encountering it (clear "not supported in Stage-0" diagnostic,
  never a crash).
- SPEC-00-bootstrap.md: add the **exact self-host subset** — the features axiom0 must support to
  compile axiomc — with the rule that anything outside it belongs to post-T087 epics. Justify each
  inclusion by the compiler's needs (tasks/0260 §3-4).
- Artifact kinds as data: object model/driver/linker represent output kind (obj, exe, static lib, dynamic lib + import lib) and object/archive/image format independently; the core emits only obj/exe, E18.7 and E16.10 add writers without redesign (REQ-OWNER-006).
- C-scope budget: rough size target per axiom0 module and the list of forbidden-in-C features.

## Acceptance
- [ ] Every roadmap epic of P11–P22 that touches a core data model has an explicit extension point.
- [ ] Self-host subset list is concrete (feature-by-feature) and every P0–P10 task is consistent with it (list any task scope that should shrink; architect files the change).
- [ ] Report `_workspaces/reports/T003a-report.md` with exact `## Files changed`.

## Out of scope
- Implementing anything.

## Notes
- Critical (priority < 10): runs alone, before the repository skeleton.
