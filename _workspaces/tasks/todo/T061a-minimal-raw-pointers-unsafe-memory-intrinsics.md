---
id: T061a
title: Minimal raw pointers, unsafe blocks and memory intrinsics (self-host subset)
phase: P7-abstraction
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T051, T054b]
priority: 80
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/types, bootstrap/axiom0/src/own/unsafe, bootstrap/axiom0/src/mir, bootstrap/axiom0/src/interp, tests/run/ptr, tests/ui/ptr]
locks: [bootstrap/axiom0/src/diag/codes/UNSAFE.def, bootstrap/axiom0/src/diag/codes/TYPE.def, bootstrap/axiom0/src/driver/pipeline.c]
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
- Intrinsics (declared with `@intrinsic`, per SPEC-04), ordinary generic functions with explicit type
  arguments (hence the dependency on T054b): `size_of<T>()`, `align_of<T>()`, `ptr_copy`,
  `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `forget`, `drop_in_place<T>`, `needs_drop<T>`
  (ADR-0004 §5), `transmute` only if the spec keeps it (else omit), `unreachable`.
- MIR interpreter memory model for raw pointers: allocations as (alloc id, offset) with bounds and
  liveness checks so out-of-bounds, use-after-free and misaligned accesses are reported by the oracle
  (a later E13.1 provenance model plugs into the same representation). Each allocation has a
  synthetic, stable base address aligned to 16 (ADR-0002 §5), so `ptr as usize` alignment arithmetic
  works; `usize as ptr` succeeds only for an address inside a live allocation.
- MIR operations for pointer reads/writes/offsets (parser support for pointer types, `unsafe` and
  `unsafe fn` comes from T012/T015b). Native lowering is T061b.

## Acceptance
- [ ] run tests (interp; they carry `// native-after: T061b`): manual linked list on a fixed array buffer, pointer walk summing an
      array, struct field write through a pointer, `size_of`/`align_of` of scalars, structs and arrays
      match the layout engine.
- [ ] ui tests: deref / arithmetic / unsafe call outside `unsafe` → AX_UNSAFE_REQUIRED.
- [ ] Oracle catches out-of-bounds read, use of a dangling pointer and misaligned access with a clear
      diagnostic (tests expect the failure; these stay `// modes: interp` with the reason "oracle-only check").
- [ ] `drop_in_place<T>` on a value with a destructor runs it exactly once; `needs_drop<i32>()` is false;
      align-up arithmetic through `ptr as usize` round-trips (arena pattern of T073a).
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T061a-report.md` with exact `## Files changed`.

## Out of scope
- Provenance rules, trusted-unsafe audits, lints (E13.1); volatile, unions, packed repr, MMIO (E13.2,
  E13.6); heap allocation itself (T070, through the host intrinsics of T061c); native lowering (T061b).

## Notes
- Critical for T065/T070: std blocks without it. Keep the checker simple and precise.
- Split (ADR-0005 §8): this task is the type/checker/oracle half; T061b is the native half; T061c the host interface (ADR-0002); T061d native constant tables.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
