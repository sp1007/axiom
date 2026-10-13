---
id: T070
title: Allocator, Box<T>, Vec<T>
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T069, T065, T061c]
priority: 101
status: doing
attempts: 1
paths: [std/core/alloc, std/alloc, std/sys/windows/heap.ax, tests/std/alloc, tests/run/host/heap]
spec: [0087, 0106, 0210, tasks/0280, 0045]
covers: [REQ-RT-183]
started: 2026-10-13 19:03:50
---
# T070 — Allocator, Box<T>, Vec<T>

## Goal
Heap memory with explicit ownership.

## Scope
- Allocator trait; the default allocator calls the host heap intrinsics (`host.heap_alloc/realloc/free`, ADR-0002) so it runs under the oracle and natively. Native implementation `__ax_host_heap_*` in `std/sys/windows/heap.ax` over kernel32 `GetProcessHeap`/`HeapAlloc`/`HeapReAlloc`/`HeapFree` (FFI, T065); Box<T>, Vec<T> (push/pop/get/index/views/iteration later, drops elements), allocation-failure policy per spec.
- Stable `sort` / `sort_by` / `sort_by_key` on Vec and mut views; `binary_search`; `dedup`. Needed by the self-hosted compiler (self-host std subset, SPEC-00 / T003a).

## Acceptance
- [ ] Sort is stable and deterministic; tests with duplicate keys: 100k elements natively and a 2k-element interp twin of the same test.
- [ ] run tests incl. drop counts and growth; leak check via allocator counters.
- [ ] `grep -rn "native-after: T070" tests` prints nothing (heap host tests of T061c now pass natively).
- [ ] `Vec<Box<i32>>` drop-count test in both modes (generic drop glue, T054b).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T070-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Both modes are mandatory. The only accepted reason for a `// modes: native` test is "direct FFI is native-only (ADR-0002)"; heavy tests (≥ 100k elements) may be native-only if a small interp twin of the same test exists.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:20 covers += REQ-RT-183 (metadata only)
- 2026-10-13 19:03:50 started (attempt 1) 
