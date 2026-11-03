---
id: T920
title: E21.6 Canonical virtual memory reserve/commit, page permissions & file memory mapping specification (SPEC-125)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 230
status: todo
attempts: 0
paths: [spec/SPEC-125-virtual-memory-mmap.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0437, tasks/0840]
covers: [REQ-STD-173, REQ-RT-141, REQ-RT-142, REQ-RT-143, REQ-RT-174, REQ-RT-648, REQ-RT-649, REQ-RT-650, REQ-RT-651, REQ-RT-652, REQ-RT-653, REQ-RT-654, REQ-RT-655, REQ-RT-656, REQ-RT-657, REQ-RT-658, REQ-RT-659, REQ-RT-660]
---
# T920 — E21.6 Canonical virtual memory reserve/commit, page permissions & file memory mapping specification (SPEC-125)

## Goal
Consolidate the canonical specification for Axiom's virtual memory and file memory-mapping subsystem—two-phase address-space reservation vs physical page commitment, explicit page permissions, guard pages, and capability-bounded `Mmap`/`MmapMut`—into `spec/SPEC-125-virtual-memory-mmap.md` (`AXS-VMM-*` rule IDs).

## Scope
- Write `spec/SPEC-125-virtual-memory-mmap.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-VMM-NNN` rules.
- Specify the separation between virtual address reservation (`VirtualRegion.reserve`) and physical backing commitment (`commit` / `decommit` via `VirtualAlloc`/`VirtualFree` on Windows and `mmap(PROT_NONE)`/`mprotect`/`madvise` on Linux/macOS; `tasks/0437 §3-18`, `REQ-RT-141`), ensuring integer addresses never carry implicit provenance.
- Specify page protection transitions (`PageProt.None|Read|ReadWrite|ReadExec`, enforcing W^X by rejecting simultaneous `Write + Exec` unless explicitly granted an unsafe JIT capability; `REQ-RT-142`), guard pages, and physical memory pinning (`lock_pages`/`unlock_pages` via `VirtualLock`/`mlock`).
- Specify file-backed and anonymous memory mappings (`Mmap`, `MmapMut`, copy-on-write `MmapCow`, offset/length page alignment, `flush_sync`/`flush_async` durability via `FlushViewOfFile`/`msync`, and lifetime-bound `as_slice() -> view<u8>` / `as_mut_slice() -> mut_view<u8>` so unmapping while a view is live is a compile-time capability error; `tasks/0437 §19-30`, `tasks/0840 §8-16`, `REQ-STD-173`, `REQ-RT-143`, `REQ-RT-174`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-125-virtual-memory-mmap.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-VMM-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T920-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of `VirtualRegion` and `Mmap`/`MmapMut` (`T921`–`T922`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T920/build` and `python tools/axtest.py --compiler build-snap-T920/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
