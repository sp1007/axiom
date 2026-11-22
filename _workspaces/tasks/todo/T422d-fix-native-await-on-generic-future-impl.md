---
id: T422d
title: Fix — native `.await` on a future whose `Future` impl is generic (`impl<T> Future for Wrap<T>`) links to an undefined or wrong `poll` (segfault)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T422c]
priority: 15
status: todo
attempts: 0
timeout_min: 480
paths: [compiler/mir/builder.ax, compiler/types/typeck.ax, tests/run/await_generic_future]
locks: []
spec: [spec/SPEC-34-executors-fibers.md]
covers: [REQ-TST-072]
---
# T422d — native `.await` on a generic `Future` impl

## Goal
Reported by T422c-impl (2026-11-22). `.await` on a value whose `Future` impl is generic over its type parameters fails in
native mode, while the interpreter is correct and a concrete `impl Future for Wrap<i64>` works natively:

```
struct Wrap<T> { pub v: T, pub n: i32 }
impl<T> Future for Wrap<T> { type Output = Result<T, Er>; fn poll(...) { ... Poll.Ready(Result.Ok(self.v)) } }
async fn outer() -> i64 { let r = Wrap { v: 41i64, n: 2i32 }.await; ... }
main: block_on(outer())
```

- Standalone: `AX_LINK_UNDEFINED_SYMBOL poll` (the monomorphised `Wrap<i64>.poll` instance is never emitted or is
  referenced under an unmangled name).
- Inside a std bundle: links to a different `poll` and segfaults.

Impact: the SPEC-34 §6.2 example (`group.join_all().await`, `handle.await` inside an async fn) passes in interp and crashes
natively; T422c marks the native legs of the affected spec-example tests `// native-after: T422d`.

## Scope
- Find where the await lowering (MIR builder / mono) resolves the `poll` callee for the awaited type and make it request the
  monomorphised instance of a generic impl method (same path as ordinary generic method calls).
- The paths list is a best guess; if the fix lives elsewhere (e.g. `compiler/lir/builder.ax`, the mono collector), report
  BLOCKED naming the file so the orchestrator widens paths.
- Tests `tests/run/await_generic_future/` (interp, native, native-O1, exact `stdout:`): the repro; two instances
  (`Wrap<i64>`, `Wrap<bool>`) awaited in one program; nested generic future (`Wrap<Wrap2<T>>`); await inside a generic async fn.
- Remove the `// native-after: T422d` markers T422c added (grep) and confirm those tests pass natively.

## Acceptance
- All new tests pass in three modes; the previously marked SPEC-34 example tests pass natively; taskgate clean.
