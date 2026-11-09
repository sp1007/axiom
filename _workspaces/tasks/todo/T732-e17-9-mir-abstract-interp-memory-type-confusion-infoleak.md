---
id: T732
title: E17.9 — MIR abstract interpretation pass for memory safety, type confusion & padding infoleaks
phase: P17-debugging-runtime-introspectio
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T731, T720]
priority: 203
status: todo
attempts: 0
paths: [compiler/analysis/zeroday, compiler/mir, tests/ui/zeroday_memory]
spec: [spec/SPEC-151-zero-day-static-analysis.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-CORE-034, REQ-DBG-116]
---
# T732 — E17.9 — MIR abstract interpretation pass for memory safety, type confusion & padding infoleaks

## Goal
Implement the first pass of the MIR abstract interpretation engine detecting memory corruption, integer overflow in allocation sizes, pointer escapes, union type confusion, and uninitialized padding infoleaks.

## Scope
- In `compiler/analysis/zeroday`, implement forward dataflow abstract interpretation over MIR CFGs:
  * Detect integer arithmetic overflowing prior to memory allocation functions (`malloc`, `alloc`, `Vec.with_capacity`), reporting `AX_VERIFY_UNCHECKED_ALLOC_OVERFLOW`.
  * Detect 64-bit to 32-bit integer truncation prior to slice indexing or length operations, reporting `AX_VERIFY_TRUNCATING_LEN_CAST`.
  * Track raw pointer allocation and deallocation states along control-flow paths; flag dereference after free with `AX_UNSAFE_STATIC_USE_AFTER_FREE` and multiple deallocations with `AX_UNSAFE_STATIC_DOUBLE_FREE`.
  * Track stack local address taking; detect escaping pointers returned from functions or stored into longer-lived heap places with `AX_UNSAFE_STACK_PTR_ESCAPE`.
  * Detect untagged `union` variant reads without discriminant checking or active-type proof, reporting `AX_UNSAFE_UNION_TYPE_CONFUSION`.
  * Detect passing struct instances containing uninitialized padding bytes to foreign `extern "C"` functions, reporting `AX_FFI_UNINIT_PADDING_LEAK`.

## Acceptance
- [ ] Negative UI tests in `tests/ui/zeroday_memory` verify precise static detection and diagnostics for all 6 memory/infoleak vulnerability classes.
- [ ] Positive tests verify that safe patterns (checked arithmetic, verified bounds, valid pointer lifecycles) pass without false positives.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T732-report.md` with exact `## Files changed`.

## Out of scope
- Filesystem/command taint analysis and SARIF emission (`T733`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T732/build` and `python tools/axtest.py --compiler build-snap-T732/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 static zero-day analysis expansion)
