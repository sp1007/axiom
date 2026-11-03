---
id: T921
title: E21.6 VirtualRegion reserve/commit/decommit, page protection (R/RW/RX), guard pages & memory locking
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T920]
priority: 231
status: todo
attempts: 0
paths: [std/vmem/region, std/vmem/protect, tests/run/std_vmem_region]
spec: [spec/SPEC-125-virtual-memory-mmap.md, tasks/0437, tasks/0840]
covers: [REQ-STD-173, REQ-RT-141, REQ-RT-142, REQ-RT-661, REQ-RT-662, REQ-RT-663, REQ-RT-664, REQ-RT-665, REQ-RT-666, REQ-RT-667, REQ-RT-668, REQ-RT-669, REQ-RT-670, REQ-RT-671, REQ-RT-672, REQ-RT-673, REQ-RT-674, REQ-RT-675]
---
# T921 — E21.6 VirtualRegion reserve/commit/decommit, page protection (R/RW/RX), guard pages & memory locking

## Goal
Implement `VirtualRegion` address-space reservation, sub-range commit/decommit, W^X-enforced page protection transitions, guard pages, and page locking in `std.vmem` per `spec/SPEC-125-virtual-memory-mmap.md`.

## Scope
- Implement `std/vmem/region` (`page_size()`, `allocation_granularity()`, move-only `VirtualRegion` with `reserve(bytes)`, `commit(offset, len, PageProt)`, `decommit(offset, len)`, and deterministic release via `VirtualFree(..., MEM_RELEASE)` / `munmap` on `Drop`; `REQ-RT-141`, `REQ-STD-173`).
- Implement `std/vmem/protect` (`PageProt` enum enforcing W^X by default, `protect(offset, len, PageProt)` via `VirtualProtect`/`mprotect`, `allocate_guarded_Arena` with leading/trailing `PageProt.None` guard pages, and `lock_pages`/`unlock_pages` via `VirtualLock`/`VirtualUnlock` and `mlock`/`munlock`; `REQ-RT-142`).
- Provide deterministic simulated page-table tracking in the oracle so uncommitted/unmapped or read-only page violations are caught in both `--interp` and native modes.
- Add run tests in `tests/run/std_vmem_region`.

## Acceptance
- [ ] Run tests in `tests/run/std_vmem_region` verify `page_size()`/`allocation_granularity()`, multi-megabyte `VirtualRegion.reserve` with selective sub-page `commit`/`decommit`, W^X policy enforcement, and `Drop` unmapping in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T921-report.md` with exact `## Files changed`.

## Out of scope
- File-backed `Mmap`/`MmapMut` and `MmapAdvice` (`T922`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T921/build` and `python tools/axtest.py --compiler build-snap-T921/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
