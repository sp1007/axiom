---
id: T126a
title: Fix incomplete slice features
phase: P6-ownership
owner: axiom-backend
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T126]
priority: 70
status: doing
paths: [src, tests]
spec: []
attempts: 1
started: 2026-10-12 09:45:13
---
# T126a — Fix incomplete slice features

## Goal
Fix slice implementation bugs that were left incomplete by T126.

## Scope
- Fix Native mode slice bounds panicking (exits with 0 instead of 101) in `qa_slice_bounds_panic.ax` and `qa_slice_inverted_panic.ax`.
- Fix `AX_TYPE_UNKNOWN_FIELD` on `.len` access in `qa_slice_open_ranges.ax` and `sub_range.ax`.
- Remove `xfail: T126` and `native-after: T126` from these slice tests.

## Acceptance
- The tests pass without xfail.

## Log
- 2026-10-12 09:45:13 started (attempt 1) 
