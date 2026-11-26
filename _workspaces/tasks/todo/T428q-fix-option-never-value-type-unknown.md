---
id: T428q
title: Fix — a value of type `Option<never>` (e.g. `let o: Option<never> = Option.None`) gives AX_TYPE_UNKNOWN in typeck
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T428m]
priority: 30
status: todo
attempts: 0
paths: [tests/run/never_in_generic_args]
locks: [compiler/types/typeck.ax, compiler/hir/lower.ax]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-02-grammar.md]
covers: [REQ-TYP-041, REQ-CORE-017]
---
# T428q — `never` is an ordinary type argument

## Why
Found by the T428m implementer (`_workspaces/reports/T428m-report.md`, "Test-writing notes"); reproduces on HEAD
b8809d48: building a value of type `Option<never>` stops typeck with `AX_TYPE_UNKNOWN`. SPEC-03 AXS-SEM-015 makes
`never` a type (no values, size 0, coerces to every type), and SPEC-02 AXS-GRM-080 makes any type a valid generic
argument, so `Option<never>` is a valid type whose only value is `None`. `never` reaches HIR through a lowering
sentinel in `lower_path_into` (`compiler/hir/lower.ax`); inside a generic argument the sentinel's type is probably
not mapped to the builtin `never` TypeId (or substitution drops it). Depends on T428m, which changes how paths inside
generic arguments are bound and keeps the sentinels working there. Implementation bug (TYPE A).

## Scope
1. Find where the `never` argument is lost (lowering of the sentinel inside generic arguments, typeck type-path
   lookup, or generic substitution) and fix it at the source; change only the files in `locks:` that the fix needs.
2. Tests `tests/run/never_in_generic_args/` (`modes: interp native`, exact `// stdout:`): `let o: Option<never> =
   Option.None` matched with `None =>` only (exhaustive: `Some(_)` of `never` is uninhabited, or, if the
   exhaustiveness checker requires the arm, an arm whose body is `unreachable()` — say which in the report);
   `Result<i32, never>` returned from a function and matched; a generic `fn id<T>(x: T) -> T` called with
   `Option<never>`; `size_of<Option<never>>()` printed (a defined value, documented in the report). A ui test: a
   mismatched use (`let n: i32 = o`) gives the normal `AX_TYPE_MISMATCH`, not `AX_TYPE_UNKNOWN`.

## Acceptance
- [ ] The tests pass (interp, native, native-O1; WEAK-NATIVE 0).
- [ ] Stage-2 build succeeds; stage-2 == stage-3 fixed point at `-O0` and `-O1`.
- [ ] Gate: task tests + affected set (grep of the changed functions; `tests/typeck/**` with `never`) + the selfhost
      groups of every changed module + smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T428q-report.md`: root cause (file:function), the fix, an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428m.md`)
