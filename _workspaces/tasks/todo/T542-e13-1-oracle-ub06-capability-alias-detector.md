---
id: T542
title: E13.1 — Oracle UB-06 capability-alias detector (raw-pointer access to view/mut_view-locked regions)
phase: P13-low-level-systems-unsafe-frees
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T502]
priority: 153
status: todo
attempts: 0
paths: [tests/run/unsafe/oracle_ub_alias]
locks: [compiler/interp, compiler/own]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/decisions/ADR-0034-oracle-independence.md, 0071, tasks/0339]
covers: [REQ-CAP-071]
---
# T542 — E13.1 — Oracle UB-06 capability-alias detector

## Why
T502 delivered the strict-provenance UB detector (UB-01..05, UB-07, UB-12) but not `UB-06` (SPEC-50 AXS-UNS-014,
AXS-UNS-015 table): a raw-pointer write to a region read-locked by an active `view<T>`, or any raw-pointer access
to a region uniquely locked by an active `mut_view<T>` not derived from it. The lock lasts from `MakeView` /
`MakeMutView` to the capability's **semantic last use** (AXS-UNS-007), and the oracle has no last-use facts. A
lexical lock (until scope end) would reject valid NLL-style programs, so T502 left it out
(`_workspaces/reports/T502-report.md`, design item 5; `_workspaces/reports/unblock-T502.md`).

## Scope
1. Provide the oracle with per-capability last-use facts. Preferred: the MIR capability/ownership analysis
   (`compiler/own`) already computes the live range of each `MakeView`/`MakeMutView` result; expose it as a
   per-body side table (capability local → set of MIR locations where it is live) that `compiler/interp` reads.
   The oracle must not re-derive liveness by its own heuristics (ADR-0034: the oracle checks the model, it does not
   re-implement the analysis it is checking); if the facts are missing for a body, the oracle does not lock.
2. In `compiler/interp`, record an active lock `(alloc id, byte range, mode, capability local)` at
   `MakeView`/`MakeMutView` and release it when execution leaves the capability's live range. On every raw-pointer
   load/store/`ptr_copy`/`ptr_write_bytes`, report `AX_UNSAFE_INTERP_UB` with `data.ub_kind =
   "capability_alias_violation"` (exit 125) when the accessed bytes overlap a lock and the access is not permitted:
   - `view` lock: writes are UB, reads are allowed;
   - `mut_view` lock: reads and writes through a pointer **not derived from** that `mut_view` are UB. A pointer
     derived from the capability (`address_of` / cast of the `mut_view`'s place) carries the capability's tag and
     is allowed.
   - Interior-mutable sub-regions (`UnsafeCell`, `Atomic`, `Volatile`, `Mmio`) are exempt (AXS-UNS-014).
3. Tests in `tests/run/unsafe/oracle_ub_alias`: positive cases (raw access after the capability's last use while it
   is still lexically in scope; pointer derived from the `mut_view`; read through raw pointer under a `view`;
   `UnsafeCell` sub-region) and negative cases (raw write under an active `view`; raw read and raw write under an
   active `mut_view` via an unrelated pointer; access inside a loop where the capability is used again later).
   Each negative test pins the message, the span and `ub_kind`.

## Acceptance
- [ ] All tests in `tests/run/unsafe/oracle_ub_alias` pass in `--interp`; native modes carry
      `// native-after:` only where native has no UB check (UB tests are oracle-only by design).
- [ ] No false positive across the suite: the affected and smoke sets plus `tests/run/unsafe`, `tests/run/own*`,
      `tests/mir/unsafe` and the selfhost interp/driver bundles pass. Any compiler/std code the detector flags is
      reported in "Spec deviations" with the exact site (the architect files the fix task); the detector is not
      weakened to hide it.
- [ ] Report `_workspaces/reports/T542-report.md` with exact `## Files changed`.

## Out of scope
- Static rejection of the same programs (the borrow/capability checker already owns that); native UB checks;
  editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13. All compiler changes live in `compiler/` within the `SPEC-00 §9` self-host subset.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T542/build` and
  `python tools/axtest.py --compiler build-snap-T542/build/axiomc2.exe --exclude-requires axiom0-internal`).
- Canonical syntax (`axiom-syntax`): `=` for binding/assignment, `.` for paths.

## Log
- 2026-11-26 created by architect (unblock of T502, `_workspaces/reports/unblock-T502.md`)
