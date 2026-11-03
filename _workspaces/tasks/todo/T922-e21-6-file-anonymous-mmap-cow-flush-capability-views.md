---
id: T922
title: E21.6 File-backed & anonymous Mmap/MmapMut, copy-on-write, flush_sync & capability-bounded views
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T920, T921]
priority: 232
status: todo
attempts: 0
paths: [std/vmem/mmap, std/vmem/advice, tests/run/std_vmem_mmap]
spec: [spec/SPEC-125-virtual-memory-mmap.md, tasks/0437, tasks/0840]
covers: [REQ-STD-173, REQ-RT-143, REQ-RT-174, REQ-RT-676, REQ-RT-677, REQ-RT-678, REQ-RT-679, REQ-RT-680, REQ-RT-681, REQ-RT-682, REQ-RT-683, REQ-RT-684, REQ-RT-685, REQ-RT-686, REQ-RT-687, REQ-RT-688, REQ-RT-689, REQ-RT-690]
---
# T922 — E21.6 File-backed & anonymous Mmap/MmapMut, copy-on-write, flush_sync & capability-bounded views

## Goal
Implement file-backed and anonymous `Mmap`, `MmapMut`, and `MmapCow` with `flush_sync`/`flush_async`, paging advice, and capability-bounded `view<u8>`/`mut_view<u8>` access in `std.vmem` per `spec/SPEC-125-virtual-memory-mmap.md`.

## Scope
- Implement `std/vmem/mmap` (`MmapOptions`, read-only `Mmap`, read-write shared `MmapMut`, private copy-on-write `MmapCow` backed by `CreateFileMappingW`/`MapViewOfFileEx`/`FlushViewOfFile`/`UnmapViewOfFile` on Windows and `mmap`/`msync`/`munmap` on Linux/macOS; `REQ-STD-173`, `REQ-RT-143`, `REQ-RT-174`).
- Bind `Mmap.as_slice(self: view<Mmap>) -> view<u8>` and `MmapMut.as_mut_slice(self: mut_view<MmapMut>) -> mut_view<u8>` to the mapping owner's capability lifetime so dropping or unmapping `Mmap` while a byte slice view is live is rejected at compile time.
- Implement `std/vmem/advice` (`MmapAdvice.Normal|Sequential|Random|WillNeed|DontNeed` via `PrefetchVirtualMemory`/`DiscardVirtualMemory` and `madvise`).
- Add run and compile-fail UI tests in `tests/run/std_vmem_mmap`.

## Acceptance
- [ ] Run tests in `tests/run/std_vmem_mmap` verify file-backed `Mmap` reads, `MmapMut` writes persisted via `flush_sync()`, `MmapCow` private copy-on-write isolation (underlying file unchanged), and sub-range offset mappings in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T922-report.md` with exact `## Files changed`.

## Out of scope
- GPU device memory mappings (`P22 E22.2`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T922/build` and `python tools/axtest.py --compiler build-snap-T922/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
