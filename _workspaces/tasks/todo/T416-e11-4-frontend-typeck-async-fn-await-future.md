---
id: T416
title: E11.4 — Frontend & typeck for async fn, .await, Future/Poll/Waker lang items
phase: P11-concurrency-async
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T415, T089]
priority: 138
status: todo
attempts: 0
paths: [std/future, tests/parse/async, tests/typeck/async]
locks: [compiler/syntax/ast.ax, compiler/syntax/parse.ax, compiler/hir/hir.ax, compiler/hir/lower.ax, compiler/types/types.ax, compiler/types/typeck.ax, compiler/traits/solver.ax, compiler/diag/code.ax, std/core/prelude.ax, tests/selfhost]
spec: [spec/SPEC-33-async.md, 0093, 0127, 0135, 0159, 0202, 0248, tasks/0275, tasks/0297, tasks/0619]
covers: [REQ-ASY-023, REQ-ASY-027, REQ-ASY-044, REQ-ASY-048, REQ-ASY-049, REQ-ASY-050, REQ-ASY-084, REQ-ASY-117, REQ-ASY-118, REQ-ASY-123, REQ-ASY-135, REQ-ASY-139, REQ-ASY-141, REQ-VER-025]
---
# T416 — E11.4 — Frontend & typeck for async fn, .await, Future/Poll/Waker lang items

## Goal
Enable `async fn`, `async { }`, and `.await` in the `axiomc` parser, HIR lowerer, and type checker, and define the `Future`, `Poll<T>`, `Waker`, and `Context` lang items in `std/future`.

## Scope
- Create `std/future/mod.ax` defining `Poll<T>`, `RawWaker`, `RawWakerVTable`, `Waker`, `Context`, and `trait Future { type Output; fn poll(self: mut_view<Self>, cx: mut_view<Context>) -> Poll<Self.Output>; }`, and export `Future` and `Poll` in `std/core/prelude.ax`.
- Accept `async fn` (free functions, inherent methods, trait methods) and `.await` postfix expressions in `compiler/syntax/parse.ax` and lower them in `compiler/hir/lower.ax` (`is_async` flag `AXS-EXT-031`, `Await` expression `AXS-EXT-033`) instead of emitting `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP`.
- Typecheck `async fn` in `compiler/types/typeck.ax` as returning a `Coroutine` (`AXS-EXT-020`) implementing `Future<Output = Ret>`, typecheck `expr.await` by verifying `expr: Future` and yielding `Output` (`REQ-ASY-139`), reject `.await` outside an `async` body (`AX_ASYNC_AWAIT_OUTSIDE_ASYNC`), reject `extern "C" async fn` (`REQ-ASY-123`), support `?` inside `async fn` (`REQ-ASY-050`), and reject unboxed direct/mutual recursive `async fn` state cycles (`AX_ASYNC_RECURSIVE_FUTURE`, `REQ-ASY-044, 117`).

## Acceptance
- [ ] `tests/parse/async/*.ax` golden AST/HIR tests verify `async fn`, generic/trait `async fn`, and chained `.await` expressions.
- [ ] `tests/typeck/async/*.ax` (`ui` + `check`) verifies `Future<Output = T>` typing, `?` operator in `async fn`, `.await` outside `async fn` rejection, non-`Future` `.await` rejection, `extern "C" async fn` rejection, and recursive `async fn` size cycle rejection.
- [ ] `tests/selfhost/bundles_current.test` passes after regenerating affected selfhost bundles.
- [ ] Full test suite passes in `build-snap-T416` under `axiomc2.exe`; `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T416-report.md` with exact `## Files changed`.

## Out of scope
- Live-across-await capability analysis (`T417`) and MIR state-machine transformation (`T088`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T416/build` and `python tools/axtest.py --compiler build-snap-T416/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
