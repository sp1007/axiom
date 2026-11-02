---
id: T415
title: E11.4 — Canonical async/await, Future & state-machine specification (SPEC-33)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T400]
priority: 137
status: todo
attempts: 0
paths: [spec/SPEC-33-async.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0093, 0127, 0135, 0159, 0161, 0201, 0202, 0248, tasks/0275, tasks/0297, tasks/0619]
covers: [REQ-CONC-020, REQ-CONC-024, REQ-CONC-096, REQ-ASY-022, REQ-ASY-024, REQ-ASY-026, REQ-ASY-033, REQ-ASY-039, REQ-ASY-045, REQ-ASY-055, REQ-ASY-085, REQ-ASY-092, REQ-ASY-100, REQ-ASY-103, REQ-ASY-104, REQ-ASY-105, REQ-ASY-116, REQ-ASY-119, REQ-ASY-120, REQ-ASY-122, REQ-ASY-124, REQ-ASY-125, REQ-ASY-126, REQ-ASY-127, REQ-ASY-137, REQ-ASY-138, REQ-ASY-144, REQ-ASY-145, REQ-ASY-146, REQ-ASY-147, REQ-CONC-146, REQ-CONC-191, REQ-CONC-217]
---
# T415 — E11.4 — Canonical async/await, Future & state-machine specification (SPEC-33)

## Goal
Write canonical `spec/SPEC-33-async.md` (`AXS-ASY-*` rule IDs) specifying `Future<T>`, `Poll<T>`, `Waker`, `async fn`, `.await`, live-across-await analysis, state-machine MIR lowering, and deterministic cancellation drop.

## Scope
- Write `spec/SPEC-33-async.md` with a Vietnamese `## Tóm tắt` section and numbered `AXS-ASY-NNN` rules.
- Specify `Future` as a zero-overhead control-flow and storage transformation without mandatory heap allocation, without `Pin`, and without a mandatory runtime or executor (`0093`, `0127`, `0202`).
- Define `Poll<T> = Ready(T) | Pending`, `Waker` / `RawWaker` / `Context`, and the `Future` lang-item trait (`fn poll(self: mut_view<Self>, cx: mut_view<Context>) -> Poll<Self.Output>`).
- Specify live-across-await analysis (`0127 §9-18`, `tasks/0619`): only values live across a suspension boundary are stored in the Future state; locals dead before `.await` are dropped before suspension; `view<T>`, `mut_view<T>`, and synchronous lock guards (`MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`) are rejected across `.await` in v1.0; `Future: Send` is determined solely from parameters + live-across-await fields; `Future` is `!Share`.
- Specify state-machine lowering (`Suspend` terminator -> structural state enum/struct + generated `poll` + per-state `Drop` glue for cancellation) and oracle lifecycle trace events (`POLL`, `SUSPEND`, `RESUME`, `WAKE`, `COMPLETE`, `CANCEL_DROP`).
- Register `AX_ASYNC_*` diagnostics in `spec/diagnostics.md`, invariants in `spec/invariants.md`, and `SPEC-33` in `spec/INDEX.md`.

## Acceptance
- [ ] `spec/SPEC-33-async.md` exists with a Vietnamese `## Tóm tắt`, `AXS-ASY-NNN` rule IDs, state-machine layout diagrams/examples, and source citations.
- [ ] `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` are updated.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T415-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or std code changes (handled by `T416`, `T417`, `T088`, `T418`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T415/build` and `python tools/axtest.py --compiler build-snap-T415/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
