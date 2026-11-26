---
id: T502
title: E13.1 — Oracle strict-provenance & UB detector (use-after-free, unaligned, uninit, REQ-OWNER-008 round-trip)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T501]
priority: 152
status: done
attempts: 1
paths: [compiler/interp, tests/run/unsafe/oracle_ub]
locks: [compiler/target/x64/frame.ax]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/SPEC-77-regalloc-machine-opt.md, spec/decisions/ADR-0052-x64-frame-meta-trailer-contract.md, 0071, 0044, tasks/0339]
covers: [REQ-OWNER-008, REQ-CAP-001, REQ-CAP-002, REQ-CAP-005, REQ-CAP-007, REQ-CAP-019, REQ-CAP-037, REQ-CAP-038, REQ-CAP-041, REQ-CAP-048, REQ-FFI-027, REQ-FFI-038, REQ-FFI-044, REQ-FFI-045, REQ-CAP-059, REQ-CAP-078, REQ-CAP-084, REQ-CAP-087, REQ-CAP-088, REQ-CAP-091, REQ-CAP-095, REQ-CAP-098, REQ-CAP-103, REQ-CAP-111, REQ-FFI-085, REQ-FFI-088, REQ-CAP-124, REQ-CAP-126, REQ-CAP-133, REQ-MIR-142, REQ-CAP-145, REQ-FFI-128]
started: 2026-11-26 05:57:15
unblocks: 1
finished: 2026-11-26 11:19:49
---
# T502 — E13.1 — Oracle strict-provenance & UB detector (use-after-free, unaligned, uninit, REQ-OWNER-008 round-trip)

## Goal
Extend the MIR oracle (`--interp`) with strict pointer provenance tags, deterministic UB detection, and `REQ-OWNER-008` fixed/dynamic address table evaluation.

## Scope
- Tag every oracle allocation and pointer value in `compiler/interp` with an allocation ID, bounds, alignment, mutability permission, and per-byte initialization state.
- Detect and deterministically diagnose UB in `--interp`: dereferencing dangling/freed pointers, out-of-bounds pointer arithmetic or loads/stores, unaligned accesses on non-packed types, and reading uninitialized memory. (`UB-06`, violating `view`/`mut_view<T>` locks through raw pointers, needs capability last-use facts and moved to T542.)
- Every `AX_UNSAFE_INTERP_UB` carries the SPEC-50 AXS-UNS-015 `data.ub_kind` string as a structured data entry (`Diagnostic.data` / `DiagDataEntry`, already used by e.g. `compiler/build/*` and emitted by `compiler/diag/json.ax`), not only in the message text.
- **Unblock round 1 (architect, ADR-0052):** fix the latent out-of-bounds read the UB-04 detector found in `compiler/target/x64/frame.ax` (lock) by implementing the frame-metadata trailer contract of SPEC-77 AXS-RA-026 item 4: add `pub const X64_FRAME_META_WORDS: usize = 5` and one helper `frame_alloc_slot_offsets(arena, slot_count) -> *mut i32` (allocates `(slot_count + X64_FRAME_META_WORDS) << 2` bytes, zero-fills the 5 trailer words; null when `slot_count == 0` as today), and use it in `x64_frame_lower_baseline_in_arena`, `x64_frame_lower_raw` and `x64_frame_lower_opt_in_arena` (replacing its inline `+ 5u32`). No other change to `frame.ax`; native output stays byte-identical.
- Implement oracle evaluation for **`REQ-OWNER-008`**: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` fixed-address placement for `static`, `let`, and `fn`, including dynamic expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`) and round-trip assertions (`fn_addr(isr) == 0x2000_0000usize`).

## Acceptance
- [ ] Oracle UB tests in `tests/run/unsafe/oracle_ub` catch use-after-free, out-of-bounds raw pointer deref, unaligned deref, uninitialized read, and provenance forgery with deterministic diagnostics.
- [ ] Oracle round-trip tests pass for `fn_addr(isr) == 0x2000_0000usize`, `static_addr(REG) == base + 0x100`, and `address_of(v) as usize` on `@addr(<expr>)` `static`, `let`, and `fn` declarations.
- [ ] Negative tests pin `data.ub_kind` (one per kind exercised) through the JSON diagnostic output or an equivalent structured check.
- [ ] `selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax` passes in all modes with the ADR-0052 fix; no `x64_frame_*` builder allocates `slot_offsets` other than through `frame_alloc_slot_offsets`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`). If the detector flags further latent reads in compiler/std code outside `paths:`/`locks:`, list each site in "Spec deviations" and block (the architect files fix tasks); never weaken the detector to pass.
- [ ] Report `_workspaces/reports/T502-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T502/build` and `python tools/axtest.py --compiler build-snap-T502/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 01:58:00 created by T213 (P13 phase planning)
- 2026-11-26 00:15:38 started (attempt 1) T502-impl
- 2026-11-26 04:21:34 block: impl done; gate fails selfhost/obj_link_driver/qa_obj_link_driver_smoke: new UB detector flags real OOB read in compiler/target/x64/frame.ax (slot_offsets alloc n*4, x64_frame_has_meta probes 5 words past); one-line fix outside T502 paths
- 2026-11-26 architect unblock: ADR-0052 (frame-metadata trailer is part of the slot_offsets allocation contract, SPEC-77 AXS-RA-026 item 4); lock compiler/target/x64/frame.ax added; add data.ub_kind data entries (Diagnostic already has `data`); UB-06 + REQ-CAP-071 moved to T542; item-scope `@addr` static with initializer stays with T526/T528/T540 (`_workspaces/reports/unblock-T502.md`)
- 2026-11-26 04:28:33 unblocked (cycle 1) 
- 2026-11-26 05:57:15 started (attempt 1) T502-impl
- 2026-11-26 11:19:49 accepted by QA -> done
