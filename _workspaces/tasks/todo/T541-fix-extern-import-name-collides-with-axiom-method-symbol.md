---
id: T541
title: Fix — native link: an `extern` import named like an Axiom method (`bind`, `shutdown`) collides with the method's symbol
phase: P13-low-level-systems-unsafe-frees
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 160
status: todo
attempts: 0
paths: [tests/link/extern_method_name_clash]
locks: [compiler/lir/builder.ax, compiler/link/pe.ax, compiler/backend/session.ax, std/sys/windows/iocp.ax]
spec: [spec/SPEC-50-unsafe-ub-ffi.md, spec/SPEC-35-async-io.md]
covers: [REQ-ABI-018]
---
# T541 — Extern import names must not collide with Axiom method symbols

## Why
T427 (`_workspaces/reports/T427-report.md`, T427-qa.md §8) could not declare ws2_32 `bind` / `shutdown` as static
`extern "system"` functions: in the native link they collided with std methods of the same name
(`AsyncTcpListener.bind`, `AsyncUdpSocket.bind`, `Reactor.shutdown`, …). The workaround in
`std/sys/windows/iocp.ax` resolves both at run time with `GetModuleHandleA`/`GetProcAddress`
(`win_ws2_bind`/`win_ws2_shutdown`). That hides a real backend bug: any FFI binding whose C name equals some
Axiom method name anywhere in the program can mis-link silently.

## Rule (architect, triage 2026-11-25)
Only `extern` imports and `@no_mangle` items own verbatim symbol names. Every Axiom-defined function and method
gets a module- (and for methods, type-) qualified symbol that can never equal a verbatim C name. Two Axiom items
can never resolve to the same symbol; an `extern` import and an Axiom item with the same simple name are distinct
symbols.

## Scope
1. Reproduce in `tests/link/extern_method_name_clash/`: a program with an `impl` method `bind` (and a free function
   or method `shutdown`) that also calls an `extern` import of the same name from a system DLL (or a local
   `.obj` fixture), checking observable results natively (stdout + exit code) and in `--interp`.
2. Find where the symbol names are formed (`get_fn_sym_name` / `lb_format_fn_item_sym_name` in
   `compiler/lir/builder.ax`, import-symbol handling in `compiler/link/pe.ax`, `compiler/backend/session.ax`) and fix
   the root cause per the rule above. Do not special-case `bind`/`shutdown`.
3. Remove the workaround from `std/sys/windows/iocp.ax`: declare `bind`/`shutdown` as normal ws2_32 externs and drop
   `win_ws2_bind`/`win_ws2_shutdown` + the `GetProcAddress` lookup. `tests/std/async/io` and
   `tests/std/async/reactor` must still pass in all modes.

## Acceptance
- [ ] New link test passes natively (`-O0` and `-O1`) and in `--interp`; it fails (mis-link or wrong output) on HEAD.
- [ ] `iocp.ax` workaround removed; `tests/std/async/**` and `tests/link/**` pass.
- [ ] Normal gate (selfhost groups of the touched compiler modules included). Report `_workspaces/reports/T541-report.md`
      with an exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T427 accept, `_workspaces/reports/triage-2026-11-25-T427.md`)
