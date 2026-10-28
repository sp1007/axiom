---
id: T150
title: Port intrinsic table and raw-pointer typing to compiler/ (lockstep with T134) - address_of, null, size_of, needs_drop, pointer arithmetic
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T146]
priority: 116
status: done
attempts: 1
paths: [compiler/types, compiler/typeck, compiler/mir, compiler/lir, compiler/verify, compiler/driver/pipeline.ax, tests/run/parity/intrinsics, tests/selfhost]
spec: [spec/decisions/ADR-0004-self-host-subset-additions.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-TYP-065, REQ-BLD-030]
started: 2026-10-27 22:48:07
finished: 2026-10-28 13:17:24
---
# T150 — Port intrinsics and raw-pointer typing

## Goal
The ported compiler recognises exactly the intrinsic table that T134 introduced in axiom0, types
the builtin intrinsics the same way, lowers them the same way, and never compiles or calls a
placeholder intrinsic body. Every `tests/run/ptr`, `native_ptr`, `ffi` and `host` program builds and
behaves under axiomc as under axiom0.

Confirmed defects (architect probe 2026-10-20):
1. `address_of(x)`, `address_of_mut(x)`, `null<T>()`, `null_mut<T>()` are rejected with
   `AX_TYPE_MISMATCH` (`tests/run/ptr/*`, `native_ptr/*`, `ffi/*`, `host/io/*`, `host/fs/clock.ax`):
   21 `no-image` entries.
2. `tests/run/ptr/layout_intrinsics.ax` (`different-behaviour`): axiomc emits functions `size_of`,
   `align_of`, `needs_drop` from the placeholder bodies (`{ 0 }`, `{ false }`) and calls them; the
   image exits 1.
3. `tests/run/host/heap/alloc.ax`: `*(p + i) = ...` on `*mut u8` + `usize` fails
   `AX_VERIFY_TYPE_MISMATCH` (pointer arithmetic typing/verification).

## Scope
- Port T134's single intrinsic table (name, signature class, lowering class) into `compiler/` and use
  it at the same places as axiom0 (typeck retyping, MIR builder lowering of wrapping/bit ops, assert,
  panic, host-call renaming, skip of placeholder bodies); an unknown `@intrinsic` gets
  `AX_TYPE_UNKNOWN_INTRINSIC` like axiom0.
- Raw-pointer typing and pointer arithmetic exactly as axiom0 (typeck, verifier, LIR lowering).
- Re-run the registry programs listed below; programs that move to another divergence class keep a
  line with the new stage/behaviour and are named in Follow-ups.

## Acceptance
- [ ] `tests/run/parity/intrinsics/` (`modes: interp native`, values derived by hand from SPEC-03 /
      layout rules): `layout.ax` (exits 0 only if `size_of<i32>()==4`, `align_of<i64>()==8`,
      `size_of<[4]i32>()==16`, `needs_drop<i32>()==false`, `needs_drop<HasDrop>()==true`, prints each
      value), `ptr_roundtrip.ax` (`address_of_mut` of an array element, write through `p + 2`, read
      back and print), `wrapping.ax` (T134's repro `783`). Pass with axiom0 and are identical under the
      e2e oracle.
- [ ] A selfhost test built from the real ported modules shows `@intrinsic fn frobnicate(a: u32) -> u32
      { 0 }` is rejected with `AX_TYPE_UNKNOWN_INTRINSIC` at the same span as axiom0.
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 22 sole-cause
      entries of the plan table (`tests/run/ffi/*` 2, `host/fs/clock.ax`, `host/heap/alloc.ax`,
      `host/io/*` 4, `native_ptr/*` 3, `ptr/*` 11), plus `host/fs/{dir,file_io,metadata}.ax` and
      `numeric/intrinsic_ops.ax` if T155 has already landed (otherwise T155 removes them); no entry is added.
- [ ] Full suite passes in `build-snap-T150` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T150-report.md` with exact `## Files changed` and the removed
      registry paths.

## Out of scope
- New intrinsics or pointer features beyond what axiom0 accepts (E13.1).

## Notes
- T134 delivered the axiom0 half and explicitly left `compiler/` to a follow-up; this is it
  (ADR-0034 §2 lockstep is satisfied across T134 + T150 because both land before T086).
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-27 03:21:55 started (attempt 1) T150-impl
- 2026-10-27 22:47:52 requeue: recover: previous session agent died (not charged: attempt refunded)
- 2026-10-27 22:48:07 started (attempt 1) T150-impl
- 2026-10-28 13:17:24 accepted by QA -> done
