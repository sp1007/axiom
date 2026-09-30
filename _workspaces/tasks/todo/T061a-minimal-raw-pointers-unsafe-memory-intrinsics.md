---
id: T061a
title: Minimal raw pointers, unsafe blocks and memory intrinsics (self-host subset)
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T051]
priority: 80
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types/ptr, bootstrap/axiom0/src/own/unsafe, bootstrap/axiom0/src/interp/mem, tests/run/ptr, tests/ui/ptr, tests/run/native_ptr]
spec: [0003, 0009, tasks/0260, 0263, spec/SPEC-04-core-extensibility.md, spec/SPEC-00-bootstrap.md]
---
# T061a — Minimal raw pointers, unsafe blocks and memory intrinsics

## Goal
Give library code the minimum unsafe toolkit that `Box`, `Vec`, `String`, arenas and FFI (T065, T070,
T073a) are built from. Without it the self-host std cannot exist. The full unsafe/UB model stays in
E13.1 and volatile/MMIO/packed layout in E13.2 (after self-hosting, ROADMAP R7).

## Scope
- Raw pointer types in the spec's syntax (SPEC-02, e.g. const/mut pointer to T): null, comparison,
  casts to/from `usize`, `&`-free creation from a place inside `unsafe`, offset/add by element count,
  read/write, pointer to array element / struct field.
- `unsafe { }` blocks and `unsafe fn`: dereference, pointer arithmetic and calls to unsafe fns are
  errors outside them (AX_UNSAFE_REQUIRED); ownership/capability checking still applies to safe code
  around them; raw pointers are Copy and carry no ownership.
- Intrinsics (declared with `@intrinsic`, per SPEC-04): `size_of<T>()`, `align_of<T>()`,
  `ptr_copy`, `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `forget`, `transmute` only if the spec
  keeps it (else omit), `unreachable`.
- MIR interpreter memory model for raw pointers: allocations as (alloc id, offset) with bounds and
  liveness checks so out-of-bounds, use-after-free and misaligned accesses are reported by the oracle
  (a later E13.1 provenance model plugs into the same representation).
- Native lowering: pointer ops map onto existing LIR loads/stores/address arithmetic.

## Acceptance
- [ ] run tests (interp + native): manual linked list on a fixed array buffer, pointer walk summing an
      array, struct field write through a pointer, `size_of`/`align_of` of scalars, structs and arrays
      match the layout engine.
- [ ] ui tests: deref / arithmetic / unsafe call outside `unsafe` → AX_UNSAFE_REQUIRED.
- [ ] Oracle catches out-of-bounds read, use of a dangling pointer and misaligned access with a clear
      diagnostic (tests expect the failure).
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T061a-report.md` with exact `## Files changed`.

## Out of scope
- Provenance rules, trusted-unsafe audits, lints (E13.1); volatile, unions, packed repr, MMIO (E13.2,
  E13.6); heap allocation itself (T070 via FFI).

## Notes
- Critical for T065/T070: std blocks without it. Keep the checker simple and precise.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
