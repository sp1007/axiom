---
id: T423b
title: Native fiber panic containment (Windows x64) — a panic on a fiber stack makes `fiber_resume` return 2 (`FiberState.Panicked`) instead of ending the process
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T423]
priority: 40
status: done
attempts: 1
timeout_min: 480
paths: [std/sys/windows/fiber.ax, tests/std/fiber, std/sys/windows/thread.ax, std/fiber/mod.ax]
locks: []
spec: [spec/SPEC-34-executors-fibers.md, spec/SPEC-54-panic-unwinding.md, spec/SPEC-32-threads-sync.md, spec/decisions/ADR-0046-t423-fiber-followups-and-tracked-xfail.md]
covers: [REQ-CONC-189, REQ-TST-072]
started: 2026-11-22 04:32:11
finished: 2026-11-22 05:18:44
---
# T423b — Native fiber panic containment

## Goal
SPEC-34 AXS-EXEC-054 requires `host.fiber_resume` to return `2` when the fiber panicked (`FiberState.Panicked`), and
AXS-EXEC-055.5 states the native rule. The oracle does this; natively a panic on a Win32 fiber stack reaches the process exit
hook (`std/sys/windows/thread.ax` `win_exit_process_hook`, code 101) and ends the process (T423 report deviation 6 / F1).
`tests/std/fiber/fiber_panic_contained.ax` carries `// native-after: T423b` until this task.

## Scope
- In the native panic path, detect that the current OS thread is running a user fiber (the per-thread running slot of
  `std/sys/windows/fiber.ax`): mark the slot `Panicked`, record result code 2, and `SwitchToFiber` back to the resumer
  (`caller_win_fiber`) instead of `ExitThread`/`ExitProcess`. The panic message is still written to stderr. The panicking
  fiber's live locals are not dropped (AXS-EXEC-053.2). A later `fiber_resume`/`fiber_destroy` of that handle behaves as for a
  terminated fiber (`-4` / destroy succeeds and releases the stack). Main-thread fibers and fibers on spawned threads both work;
  a panic outside any fiber keeps today's behaviour (thread: join `Err`, main: exit 101).
- Hook the fiber check into the exit hook of `std/sys/windows/thread.ax` (lock) or the panic entry the hook uses, without
  changing thread semantics.
- Remove the `// native-after: T423b` line (in `tests/std/fiber/gen_tests.py`, which emits it, and the regenerated
  `fiber_panic_contained.ax`); `grep -rn "native-after: T423b" tests` must be empty.
- New tests `tests/std/fiber/native_panic/*.ax` (`modes: interp native`, exact `stdout`/`exit`): panic in a fiber on the main
  thread then other fibers keep running and the program exits 0; panic in a nested fiber (fiber resumes fiber) returns 2 to its
  direct resumer only; panic in a fiber on a spawned thread, thread joins `Ok`; panic after several yields; `FiberScheduler.run`
  with one panicking fiber completes the others; resume of the panicked fiber afterwards panics deterministically (exit 101).

## Acceptance
- [ ] `fiber_panic_contained` and all new tests pass in interp, native and native-O1 (WEAK-NATIVE 0); interp and native outputs
  are identical; a mutated expectation makes native FAIL.
- [ ] `tests/std/fiber`, `tests/std/thread`, `tests/run/panic*`, `tests/std/async` pass; gate per axiom-qa.md "Per-task gate scope".
- [ ] Report `_workspaces/reports/T423b-report.md` with exact `## Files changed`.

## Out of scope
- Unwinding (running Drop of the panicking fiber's locals; SPEC-54 `--panic unwind`), non-Windows targets, `spec/`, `docs/`.

## Log
- 2026-11-21 created by axiom-architect (triage-t423, ADR-0046 D4; T423 QA F3 / report F1)
- 2026-11-22 04:32:11 started (attempt 1) T423b-impl
- 2026-11-22 05:18:44 accepted by QA -> done
