---
id: T713
title: E17.4 Natvis/GDB/LLDB semantic visualizers (String/Vec/Option/Result/Async) & axiom symbolicate CLI
phase: P17-debugging-runtime-introspectio
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T217, T316, T712]
priority: 184
status: todo
attempts: 0
paths: [compiler/debug/visualizers, compiler/driver/symbolicate_cmd, std/debug/contract, tests/run/debug/symbolicate]
spec: [spec/SPEC-95-debugger-contract-symbolication.md, 0100, 0147, tasks/0811, tasks/1055]
covers: [REQ-DBG-116, REQ-DBG-118, REQ-DBG-120]
---
# T713 — E17.4 Natvis/GDB/LLDB semantic visualizers (String/Vec/Option/Result/Async) & axiom symbolicate CLI

## Goal
Implement embedded Natvis and GDB/LLDB semantic type visualizers, secret-value redaction, and the axiomc symbolicate / debug inspection CLI.

## Scope
- Implement `compiler/debug/visualizers` generating embedded `.natvis` XML streams in PDB files and `.debug_gdb_scripts` / LLDB formatter scripts in ELF/Mach-O binaries for `str`, `String`, `Vec<T>`, `Slice<T>`, `HashMap<K,V>`, `Option<T>`, `Result<T,E>`, niche-optimized enums, `Future` suspension states, and `<redacted>` masking for `@secret` types (`ADEBUG-89`).
- Implement `std.debug.contract` (panic hook integration with symbolication so panics print demangled source-mapped backtraces when debug info is present) and `compiler/driver/symbolicate_cmd` (`axiomc symbolicate` CLI translating raw hex addresses or `.axcrash` dumps into source-mapped traces).
- Add end-to-end tests in `tests/run/debug/symbolicate`.

## Acceptance
- [ ] Panic backtraces in `-g` builds print demangled function names, `file:line:col`, and expanded inline frames.
- [ ] `axiomc symbolicate` accurately resolves addresses and `.axcrash` dumps across PDB and DWARF v5 binaries, and `@secret` values format as `<redacted>`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T713-report.md` with exact `## Files changed`.

## Out of scope
- Sampling and instrumentation profilers (`E17.5`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
