---
id: T461a
title: Fix — a native program of ~33,000 statements (330 functions × 100 calls) builds but crashes at run time (0xC0000005)
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: []
priority: 70
status: doing
attempts: 1
timeout_min: 300
paths: [tests/build_native/large_program]
locks: [compiler/backend, compiler/lir, compiler/link, compiler/obj]
spec: [spec/SPEC-00-bootstrap.md, spec/SPEC-27-separate-compilation-linker-v2.md]
covers: [REQ-GEN-027, REQ-LAY-129]
started: 2026-11-26 04:21:47
agent: T461a-impl
---
# T461a — Large native programs must run

## Why
`_workspaces/reports/T461-qa.md` N4 (pre-existing, unrelated to std.math): a program of 330 chunk functions with 100
calls each (33,000 statements `pr(plain_f32(from_bits_f32(N)));`, `plain_f32(x) = x * 1.5 + 1.0`, no std.math call)
builds natively but dies with `0xC0000005` at run time and loses its buffered stdout; 66 chunks (6,600 statements)
work. Generator: T461 QA scratchpad `qa461/combo2.py 22 1500` (rebuild it from this description if gone). The oracle
result is the reference. Likely suspects to check in order: a 32-bit/rel32 overflow or truncation in a section size,
relocation or jump-table offset; `.rdata` constant pool or string table growth; the PE image layout
(`SizeOfImage`, section alignment) beyond a fixed buffer; a per-function frame/stack probe error.

## Scope
1. Write a deterministic generator test (`tests/build_native/large_program/`, a `.test` driving a committed Python
   generator, stdlib-only) with sizes 66, 200, 330 and 500 chunks; bisect the size at which it starts failing and
   find the cause with `objdump`/`dumpbin` style checks against the axiom0/axiomc writers.
2. Fix the cause in the owning backend module (list which and why in the report). No limit raise without a check:
   if a format limit is genuinely exceeded, emit a diagnostic instead of a broken image.
3. Compare stdout with `run --interp` for every size (exact equality), and run the 330-chunk case at -O0 and -O1.

## Acceptance
- [ ] All sizes print the same as the oracle at -O0 and -O1; the 330-chunk case fails on HEAD (shown in the report).
- [ ] `tests/build_native/**`, `tests/link*/**`, `tests/obj/**`, `tests/run/native*/**` pass; WEAK-NATIVE 0 for new tests.
- [ ] Normal gate including the selfhost groups of every changed compiler module; stage-2 fixed point holds.
      Report `_workspaces/reports/T461a-report.md` with an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T461-qa.md N4)
- 2026-11-26 04:21:47 started (attempt 1) T461a-impl
