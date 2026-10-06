---
id: T069
title: core library v1 (Axiom source)
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T056, T060, T059, T061, T061b]
priority: 100
status: todo
attempts: 0
paths: [std/core, tests/std/core]
spec: [0169, 0170, 0219, tasks/0303, tasks/0305, tasks/0353]
covers: [REQ-STD-170]
---
# T069 — core library v1 (Axiom source)

## Goal
The OS-independent core every Axiom program can use.

## Scope
- Primitive methods (min/max/abs/checked_*/wrapping_*), Option/Result combinators, cmp/ops traits, mem (size_of, align_of, swap, replace, take), intrinsics declarations, panic/assert/debug_assert.
- `wrapping_*`, `rotate_*`, bit-count methods wrap the T034 intrinsics; `char.from_u32(n) -> Option<char>` as library code over the checked cast (ADR-0006 §2); `Eq`/`Ord`/`Hash` for tuples up to arity 4 (ADR-0004 §6).
- `Hash` trait and `std/core/hash.ax`: the documented 64-bit hash of axiom0 `kernel/` (T007) — identical output for the reference vectors `tests/unit/kernel/hash_vectors.txt`.
- Does not touch `std/core/option.ax`, `result.ax`, `prelude.ax` beyond adding combinators and exports (they exist since T054b/T060).

## Acceptance
- [ ] tests/std/core run tests (interp + native), incl. Option/Result combinators taking closures, `mem.swap/replace/take`, the hash reference vectors, tuple ordering.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T069-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Depends on T059 (closures natively, for the combinators) and T061b (pointer intrinsics natively, for `mem`); the earlier T056+T060 dependency let it start too early (audit A1-03).
- Starts as soon as the language features it needs exist (ROADMAP R8), not after the whole P7 gate.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:20 covers += REQ-STD-170 (metadata only)
