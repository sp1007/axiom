---
id: T428p
title: Fix — `Option<view<[S]>>` / `Option<view<Self>>` fail to parse (the `>>` after a `view<..>` / `mut_view<..>` type in a generic list is not split)
phase: P11-concurrency-async
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 25
status: todo
attempts: 0
paths: [tests/parse/view_in_generic_args]
locks: [compiler/syntax/parse.ax]
spec: [spec/SPEC-02-grammar.md]
covers: [REQ-GRM-151, REQ-GRM-076]
---
# T428p — A capability type closes a generic list like any other type

## Why
Found by the T428m implementer (`_workspaces/reports/T428m-report.md`, "Test-writing notes"); reproduces on HEAD
b8809d48. `Option<view<[S]>>` and `Option<view<Self>>` are rejected by the parser: the `>>` that closes both the
`view<..>` capability type and the enclosing generic list is not split. SPEC-02 AXS-GRM-057 says a closing `>` may
be split from `>>`, `>=`, `>>=`; `compiler/syntax/parse.ax` has `split_gt` (line ~970) and uses it for generic
argument lists (~1121), but the `view<T>` / `mut_view<T>` type parser (`TOK_KW_VIEW` / `TOK_KW_MUT_VIEW`,
`TYPE_VIEW`) apparently expects a plain `TOK_GT`. This is an implementation bug (TYPE A).

## Scope
1. Make the `view<..>` and `mut_view<..>` type forms close through the same split helper as generic argument lists,
   so every nesting of `>`, `>>`, `>=`, `>>=` after a capability type parses (AXS-GRM-057). Check the other
   closing-`>` sites of `parse.ax` (pointer/slice/array element types, `dyn` bounds, turbofish-like expression
   paths) and route any that bypass the helper through it as well.
2. Tests `tests/parse/view_in_generic_args/` (AST golden or `check` + run tests): `Option<view<[S]>>`,
   `Option<mut_view<Self>>` in an impl, `Result<view<S>, Option<view<[u8]>>>` (`>>>`), a `let x: Option<view<S>>= ..`
   (`>>=` split), and a run test (`modes: interp native`, exact `// stdout:`) passing an `Option<view<[i32]>>` to a
   function and reading through it. A negative case: an unbalanced `view<S>>` outside any generic list keeps its
   current diagnostic.

## Acceptance
- [ ] The tests pass (interp, native, native-O1; WEAK-NATIVE 0).
- [ ] Stage-2 build succeeds; stage-2 == stage-3 fixed point at `-O0` and `-O1`.
- [ ] Gate: task tests + affected set (all `tests/parse` and `tests/ui/parse*`) + the selfhost groups of
      `compiler/syntax` + smoke; failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T428p-report.md`: the sites changed, an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428m.md`)
