---
id: T073a
title: Arenas and typed ID tables (Axiom library for the compiler data model)
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T070, T073]
priority: 105
status: todo
attempts: 0
paths: [std/core/arena, std/collections/idtable, tests/std/arena]
spec: [tasks/0260, 0263, 0172, 0106, 0036, spec/SPEC-00-bootstrap.md]
---
# T073a — Arenas and typed ID tables

## Goal
Give the self-hosted compiler the same data-model foundation axiom0 has in C: arena allocation owned
by a compiler phase and typed ID tables instead of raw pointers (tasks/0260 ABOOT-52..57, 0172
AKERNEL-24).

## Scope
- `Arena`: bump allocation with chunk growth, explicit reset/destroy; arena-owned values follow the
  ownership rules (no escape past arena lifetime — rely on views/capabilities, do not add GC or RC).
- Typed ID newtypes pattern (`struct FileId(u32)`) + `IdTable<Id, T>` (push → Id, get/get_mut via
  views, iteration in insertion order, len); invalid/none id convention matching axiom0 (index 0).
- `Interner<T>` (hash-consing to ids) with deterministic hashing from T073.
- Documentation of how compiler phases use them (mirrors axiom0 kernel/).

## Acceptance
- [ ] Tests: 1M allocations in an arena natively and a 10k interp twin, reset reuses memory, drop of arena frees everything (allocator counters back to zero).
- [ ] IdTable/Interner tests: identity, insertion-order iteration, determinism across runs.
- [ ] A mini "AST in an arena" example built and traversed in interp and native mode.
- [ ] Full test suite passes; report `_workspaces/reports/T073a-report.md` with exact `## Files changed`.

## Out of scope
- Pool / general custom allocators, concurrent arenas (E21.9).

## Notes
- Arena-escape rule: SPEC-11 stored-view rule (T045). Interner hashing comes from T073/T069, so this task depends on T073 (audit A1-03, A3-10).
- Moved from E21.9 into the core because the Axiom compiler cannot be ported without it.
- All Axiom code uses canonical syntax (axiom-syntax).
