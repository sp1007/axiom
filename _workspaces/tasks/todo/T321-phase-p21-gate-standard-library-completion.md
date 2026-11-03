---
id: T321
title: Phase P21 gate — Standard library completion
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T221, T311, T313, T900, T901, T902, T903, T904, T905, T906, T907, T908, T909, T910, T911, T912, T913, T914, T915, T916, T917, T918, T919, T920, T921, T922, T923, T924, T925, T926, T927, T928, T929, T930, T931, T932, T933, T934, T935]
priority: 321
status: todo
attempts: 0
paths: [tests/conformance/p21, _workspaces/reports/phase-P21-review.md]
spec: [spec/ROADMAP.md, spec/SPEC-120-collections-data-oriented-storage.md, spec/SPEC-121-text-unicode-complete.md, spec/SPEC-122-os-fs-process-signals-ipc.md, spec/SPEC-123-networking-sockets-dns-http.md, spec/SPEC-124-time-clocks-timers.md, spec/SPEC-125-virtual-memory-mmap.md, spec/SPEC-126-serialization-binary-data-model.md, spec/SPEC-127-crypto-primitives-secure-memory.md, spec/SPEC-128-allocators-pool-custom-concurrent.md]
covers: [REQ-STD-171, REQ-STD-172, REQ-STD-173, REQ-STD-174, REQ-STD-175, REQ-STD-177]
---
# T321 — Phase P21 gate: Standard library completion

## Goal
Certify that phase P21 meets the exit criteria of every epic (`E21.1`–`E21.9`) in `spec/ROADMAP.md` §3 and that all
requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all targets supported at this point; run each epic's exit-criterion checks (`tests/conformance/p21/e21_1_collections_soa` through `tests/conformance/p21/e21_9_allocators`, including the `ADR-0034` §8 OI-13 automated Windows ConPTY `WriteConsoleW` check for `Xin chào thế giới` in `e21_3_os_fs_process_ipc`).
- `reqcov.py --phase P21-standard-library-completion`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p21` (index + missing cases added).
- Ask axiom-architect (via report Follow-ups) for the phase review items: spec drift, shortcuts to retire.

## Acceptance
- [ ] Every epic exit criterion (`E21.1`–`E21.9`, including complete `std` API reference coverage, tier-1 target conformance, and the automated ConPTY `WriteConsoleW` verification of `Xin chào thế giới`) demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED; only `xfail` entries for spec gaps with an ADR may remain); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T321-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- Depends on the planning task T221, the P11 gate T311, the P13 gate T313, and every P21 task T900–T935.

## Log
- 2026-10-06 02:31:20 covers += REQ-STD-171, REQ-STD-172, REQ-STD-173, REQ-STD-174, REQ-STD-175, REQ-STD-177 (metadata only)
- 2026-11-03 10:35:00 updated by T221 (wired T311, T313, and all 36 P21 tasks T900–T935 into depends and SPEC-120..SPEC-128 into spec)
