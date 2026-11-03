---
id: T923
title: E21.6 Virtual memory reservation, page protection, guard pages & Mmap conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T922]
priority: 233
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_6_vmem_mmap]
spec: [spec/SPEC-125-virtual-memory-mmap.md, tasks/0437, tasks/0840]
covers: [REQ-STD-173, REQ-RT-141, REQ-RT-142, REQ-RT-143, REQ-RT-174, REQ-RT-691, REQ-RT-692, REQ-RT-693, REQ-RT-694, REQ-RT-695, REQ-RT-696, REQ-RT-697, REQ-RT-698, REQ-RT-699, REQ-RT-700]
---
# T923 — E21.6 Virtual memory reservation, page protection, guard pages & Mmap conformance suite

## Goal
Certify E21.6 exit criteria with an end-to-end virtual memory and memory-mapping conformance suite covering `VirtualRegion` reserve/commit/decommit, W^X page permissions, file/anonymous `Mmap`/`MmapMut`/`MmapCow`, and capability-lifetime safety.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_6_vmem_mmap` verifying reserve-vs-commit separation (`REQ-RT-141`), W^X protection transitions (`REQ-RT-142`), and `Mmap`/`MmapMut`/`MmapCow` durability and isolation (`REQ-STD-173`, `REQ-RT-143`, `REQ-RT-174`).
- Verify compile-time rejection of dangling `view<u8>` slices outliving `Mmap` unmap/`Drop`.
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_6_vmem_mmap` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T923-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T923/build` and `python tools/axtest.py --compiler build-snap-T923/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
