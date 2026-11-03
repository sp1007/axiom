---
id: T420
title: E11.5 — Canonical executors, structured concurrency & fiber specification (SPEC-34)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T410, T415]
priority: 143
status: done
attempts: 1
paths: [spec/SPEC-34-executors-fibers.md]
locks: [spec/INDEX.md, spec/SPEC-04-core-extensibility.md]
spec: [0202, 0204, 0205, tasks/0277, tasks/0278, tasks/0620, tasks/0621, tasks/0834, tasks/0835, tasks/0836]
covers: [REQ-CONC-023, REQ-ASY-036, REQ-ASY-040, REQ-ASY-051, REQ-ASY-060, REQ-ASY-067, REQ-ASY-068, REQ-ASY-089, REQ-ASY-094, REQ-ASY-149, REQ-CONC-149, REQ-ASY-156, REQ-CONC-200, REQ-ASY-161, REQ-ASY-162, REQ-ASY-163, REQ-ASY-164]
started: 2026-11-03 07:37:44
finished: 2026-11-03 07:51:37
---
# T420 — E11.5 — Canonical executors, structured concurrency & fiber specification (SPEC-34)

## Goal
Write canonical `spec/SPEC-34-executors-fibers.md` (`AXS-EXEC-*` rule IDs) specifying `Task`, `LocalExecutor`, work-stealing `Executor`, `TaskGroup` structured concurrency, async synchronization primitives, `ResourceGovernor`, and stackful `Fiber` execution.

## Scope
- Write `spec/SPEC-34-executors-fibers.md` with a Vietnamese `## Tóm tắt` section and numbered `AXS-EXEC-NNN` rules.
- Specify the strict separation of `Future` (lazy/unscheduled state machine), `Task` (scheduled execution unit with intrusive Task Control Block and atomic wake state machine), and `Executor` (library scheduler outside the language core) (`0202`, `0205`, `tasks/0620`).
- Specify `LocalExecutor` (`spawn_local`, pinning `!Send` tasks to the current thread) vs multi-threaded work-stealing `Executor` (`spawn`, requiring `F: Future + Send` and `F.Output: Send`, local deque + cross-worker stealing).
- Specify `TaskGroup` structured concurrency (child tasks cannot outlive the enclosing group scope, sibling cancellation on failure, panic capture into `TaskResult<T>`, explicit `detach`), `CancellationToken`, `Deadline`/`Timeout`, and `ResourceGovernor` (`tasks/0834`).
- Specify async-aware synchronization (`AsyncMutex<T>`, `AsyncRwLock<T>`, `AsyncSemaphore`, async channels) and their cancellation-safety contracts (`tasks/0621`).
- Specify the stackful `Fiber<T>` model (`0204`, `tasks/0277`): explicit stack storage contract, cooperative `resume`/`yield_now`, non-migratable default thread affinity, and host intrinsics (`host.fiber_*`).
- Update `spec/INDEX.md` and `spec/SPEC-04-core-extensibility.md`.

## Acceptance
- [ ] `spec/SPEC-34-executors-fibers.md` exists with a Vietnamese `## Tóm tắt`, `AXS-EXEC-NNN` rule IDs, task state-transition diagram, and API signatures.
- [ ] `spec/INDEX.md` and `spec/SPEC-04-core-extensibility.md` are updated.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T420-report.md` with exact `## Files changed`.

## Out of scope
- Implementing `std/async` or `std/fiber` (handled by `T421`–`T423`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T420/build` and `python tools/axtest.py --compiler build-snap-T420/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-03 07:37:44 started (attempt 1) 
- 2026-11-03 07:51:37 accepted by QA -> done
