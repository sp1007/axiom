---
id: T714
title: E17.4 Debugger contract, Natvis/GDB/LLDB visualizers & symbolication conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T713]
priority: 185
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_4_debugger_symbolication]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0100, 0147, tasks/0811, tasks/1055]
covers: [REQ-DBG-116, REQ-DBG-118, REQ-DBG-120]
---
# T714 — E17.4 Debugger contract, Natvis/GDB/LLDB visualizers & symbolication conformance suite

## Goal
Certify the E17.4 and P17 debugger exit criteria: step-through debugging on Windows and Linux, inline/async frame reconstruction, semantic type visualization, and symbolication accuracy.

## Scope
- Create `tests/conformance/p17/e17_4_debugger_symbolication` covering:
-   - Step-through debugging script tests (breakpoints by `file:line` and function name, `next`/`step`/`finish`, local variable inspection, and backtrace inspection on Windows PE/PDB and Linux ELF/DWARF binaries).
-   - Logical inline stack expansion (3-level inlined function chain at `-O2`) and `async fn` suspension-point stack reconstruction.
-   - Natvis and GDB/LLDB visualizer verification for `String` (`"Xin chào thế giới"`), `Vec<i64>`, `HashMap<String, i32>`, `Option<T>`, `Result<T, E>`, and `@secret` redaction.
-   - `axiomc symbolicate` accuracy and binary/debug build-ID mismatch detection (`ADEBUG-96`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_4_debugger_symbolication` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T714-report.md` with exact `## Files changed`.

## Out of scope
- Profiler (`T718`) and sanitizer (`T722`) conformance.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
