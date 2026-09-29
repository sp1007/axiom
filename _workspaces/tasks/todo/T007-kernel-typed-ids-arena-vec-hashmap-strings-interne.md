---
id: T007
title: Kernel: typed IDs, arena, vec, hashmap, strings, interner, hashing
phase: P1-kernel
owner: axiom-frontend
reviewer: axiom-qa
depends: [T004, T005]
priority: 13
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/kernel, tests/unit/kernel]
spec: [0153, 0171, 0172, tasks/0533, 0263]
---
# T007 — Kernel: typed IDs, arena, vec, hashmap, strings, interner, hashing

## Goal
Provide the deterministic, allocation-disciplined data structures all compiler phases use.

## Scope
- Typed ID macro pattern + IdTable; Arena (aligned bump, chunks, reset/destroy); Vec (type-safe macro wrapper); HashMap (open addressing, deterministic iteration = insertion order); StrView/StrBuf; StringInterner → StrId; stable 64-bit hash (documented algorithm, independent of platform); UTF-8 decode/validate helpers; AX_ICE and AX_ASSERT.
- Unit test binary axiom0-unit (CMake target) run by the test runner (or ctest) — add a `unit` kind if needed.

## Acceptance
- [ ] Unit tests for each structure incl. growth, collisions, deletion, iteration order determinism, interner identity.
- [ ] No mutable globals; builds warning-free with gcc and clang.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T007-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
