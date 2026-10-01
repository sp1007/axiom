---
id: T007
title: Kernel: typed IDs, arena, vec, hashmap, strings, interner, hashing
phase: P1-kernel
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
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
- Unit tests are C files under `tests/unit/kernel/`, compiled into `axiom0-unit` by the T004 glob and run through an `exec` manifest of the runner (T005); neither CMakeLists.txt nor tools/axtest.py is edited.
- The hash algorithm and the HashMap iteration contract (insertion order, also after deletions) are written down in `bootstrap/axiom0/src/kernel/README.md`: std `HashMap` (T073) and `std/core/hash.ax` (T069) must reproduce both bit for bit (ADR-0004 §4). The hash uses only wrapping 64-bit multiply/add/xor/rotate. Reference vectors (key bytes → hash) are written to `tests/unit/kernel/hash_vectors.txt`.

## Acceptance
- [ ] Unit tests for each structure incl. growth, collisions, deletion, iteration order determinism, interner identity.
- [ ] No mutable globals; builds warning-free with gcc and clang.
- [ ] `tests/unit/kernel/hash_vectors.txt` (≥ 32 keys incl. empty, 1 byte, `Xin chào thế giới`, 1 KB) is checked by a unit test; iteration order after delete + reinsert is tested and documented.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T007-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
