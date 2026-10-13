---
id: T061b
title: Native catch-up: raw pointers and memory intrinsics
phase: P7-abstraction
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T061a, T059]
priority: 81
status: done
attempts: 1
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, tests/run/ptr, tests/run/native_ptr]
spec: [0162, 0183, 0003, 0009]
covers: []
started: 2026-10-13 13:26:45
finished: 2026-10-13 14:19:56
---
# T061b — Native catch-up: raw pointers and memory intrinsics

## Goal
Raw-pointer programs and the memory intrinsics of T061a run natively with the same results as the oracle.

## Scope
- Pointer reads/writes/offsets and casts lowered onto LIR loads, stores and address arithmetic; pointers to array elements and struct fields.
- Intrinsics: `size_of`/`align_of` as constants per instance; `ptr_copy` (overlap-safe), `ptr_copy_nonoverlapping`, `ptr_write_bytes` as inline loops or `rep movsb`/`rep stosb`; `forget`; `drop_in_place<T>` as a call of the instance's drop glue; `needs_drop<T>` as a constant; `unreachable`.
- Remove every `// native-after: T061b` directive from tests/run/ptr (ADR-0005 §1).

## Acceptance
- [ ] Differential green for tests/run/ptr; `grep -rn "native-after: T061b" tests` prints nothing.
- [ ] Native tests of overlapping `ptr_copy` in both directions and of a 1 MB `ptr_write_bytes`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061b-report.md` with exact `## Files changed`.

## Out of scope
- Oracle-only checks (out-of-bounds, dangling, misaligned) stay interp tests; provenance (E13.1).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-13 13:26:45 started (attempt 1) 
- 2026-10-13 14:19:56 accepted by QA -> done
