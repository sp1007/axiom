---
id: T157
title: AX0-FIX-06 capability checker - raw pointers hold no capability, view locals die before scope-end owner drops (axiom0 + port)
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T147]
priority: 0
status: done
attempts: 1
paths: [bootstrap/axiom0/src/own/cap, compiler/own/cap.ax, tests/run/parity/cap, tests/ui/cap, tests/selfhost]
spec: [spec/SPEC-11-capability.md, spec/SPEC-12-drop.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md, spec/decisions/ADR-0034-oracle-independence.md, 0160]
covers: [REQ-OWN-002, REQ-OWN-159]
timeout_min: 240
started: 2026-10-24 07:22:56
finished: 2026-10-24 11:31:21
---
# T157 — AX0-FIX-06: capability false positives at scope end

## Goal
Both compilers accept the valid programs of SPEC-11 AXS-CAP-008/009 and still reject real
owner-outlives violations (AXS-CAP-004), with identical diagnostics. Since T141 made structs with
only scalar/pointer fields droppable, these false positives hit ordinary code (the T141 engineer had
to rewrite a test to avoid them).

Confirmed defects (T141 report "Follow-up", T141 QA N5 and round-0 note; architect probe
2026-10-23):
1. `let mut b = S {}; let p: *mut S = unsafe { address_of_mut(b) };` with `impl Drop for S`:
   `AX_CAP_OUTLIVES_OWNER` at the function's closing position. axiomc (`compiler/own/cap.ax`)
   rejects it; a pre-T141 `build/axiom0.exe` rejects it too (fieldless `S`); the T141 engineer saw
   axiom0 accept the scalar-field case — establish the HEAD behaviour of both first.
2. `let a = S {}; let va: view<S> = view(a);` with droppable `S`: `AX_CAP_OUTLIVES_OWNER` at function
   end in axiom0 (and presumably axiomc). Valid by AXS-CAP-009 (`va` dies before `a` is dropped).
Likely cause: the checker treats the scope-end `Drop` of the owner as invalidating a capability whose
liveness is the whole scope, and/or records `AddressOf` as an active view.

## Scope
- axiom0 `bootstrap/axiom0/src/own/cap/` and the port `compiler/own/cap.ax`, in lockstep
  (ADR-0034 §2): `AddressOf` takes an ephemeral capability for its own statement only (AXS-CAP-008);
  a view local is active until its last use and never past its own `StorageDead`/scope end, which
  precede the drops of owners declared earlier (AXS-CAP-009). Diagnostic position and text identical
  in both compilers.
- If the fix needs MIR facts the checker does not have (liveness, storage markers), say so in the
  report and take them from the existing MIR; do not change MIR construction (T149's area).
- Regenerate selfhost bundles that embed `compiler/own/cap.ax` with their generators; list each in
  the report (ADR-0034 §2).

## Acceptance
- [ ] `tests/run/parity/cap/raw_ptr_of_drop_local.ax` (`modes: interp native`, hand-written
      `stdout:`): `address_of_mut` and `address_of` on locals of a scalar-field and a fieldless
      `impl Drop` type, a store through the pointer, then a read of the owner and its scope-end drop
      (destructor prints) — accepted by axiom0 and axiomc.
- [ ] `tests/run/parity/cap/view_local_of_drop_owner.ax` (`modes: interp native`): `let va: view<S> =
      view(a)` and `let mv: mut_view<S> = mut_view(b)` on droppable owners, used, then function end;
      also inside a nested block and before an early `return`; destructor output order pinned.
- [ ] `tests/ui/cap/view_outlives_drop_owner.ax`: a view assigned in an inner block to an outer
      `view<D>` local and used after the block — still `AX_CAP_OUTLIVES_OWNER` (with a droppable
      `D` and with `i32`), same span in both compilers (axiomc_e2e compares diagnostics bytes).
- [ ] Every existing `tests/ui/cap/**` and `tests/ui/own/**` expectation is unchanged.
- [ ] axiomc_e2e: no REGRESSION; `known_divergent.txt` gains no entry (ADR-0035 §4).
- [ ] Full suite passes in `build-snap-T157` with native legs; gcc and clang builds warning-free;
      archcheck clean.
- [ ] Report `_workspaces/reports/T157-report.md` with exact `## Files changed`, the root cause in
      each compiler and the regenerated bundles.

## Out of scope
- Assignment drop rule (done in T141, recorded as SPEC-12 AXS-DROP-007); index auto-deref (E14.5).
- Stored-view/arena escape analysis beyond the cases above.

## Notes
- AX0-FIX chain (ADR-0034 §2, §5): priority 0, runs alone; after T147, before T158.
- axiomc for probes: `python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py <axiom0> <tmp> <root>`.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale and is not evidence.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-24 07:22:56 started (attempt 1) T157-impl
- 2026-10-24 11:31:21 accepted by QA -> done
