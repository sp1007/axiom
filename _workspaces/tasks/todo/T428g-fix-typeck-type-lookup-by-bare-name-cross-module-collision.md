---
id: T428g
title: Fix — typeck resolves a type path by bare item name across all modules (same-named structs of different modules collide)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a, T428m]
priority: 12
status: todo
attempts: 0
timeout_min: 240
paths: [tests/modules/same_name_types, tests/run/same_name_std_types]
locks: [compiler/types/typeck.ax, _workspaces/baseline-failures.txt]
spec: [spec/SPEC-03-core-semantics.md, spec/SPEC-02-grammar.md]
covers: [REQ-TYP-072, REQ-MOD-003, REQ-MOD-064]
started: 2026-11-26 10:14:53
unblocks: 1
---
# T428g — A type name must resolve to the item the resolver bound, never to the first same-named item

## Why
`_workspaces/reports/unblock-T428a.md`: two P11 conformance tests (`conformance/p11/e11_5_executors/
spawn_affinity_vs_migration.ax`, `fiber_in_async_and_threads.ax`) cannot compile against live std, and are admitted to
`_workspaces/baseline-failures.txt` with this task as fix task. Minimal repros (fail with the HEAD compiler, live std):
```
use std.io.read_to_string
struct String { x: i32 }
fn main() -> i32 { let s = String { x: 0i32 }; s.x }
```
-> `AX_TYPE_MISMATCH` at `std/io/io.ax:264` (`return Result.Ok(string_new());`). The same with a user `struct IoError`
(error at `std/io/io.ax:161`), and with `use std.text.string.String` + `use std.io.read_to_string` (std.io and
std.text.string both define `String`; `std.thread` imports one, `std.asyn.executor` -> `std.asyn.reactor` -> `std.io`
the other). A user `fn string_new` does **not** collide, so the defect is in type-path lookup.

Root cause (read, to be confirmed): `compiler/types/typeck.ax` `lookup_path_type_by_name` walks `(*cx.hir).items` of
the whole program and returns the first `HIR_ITEM_STRUCT` (and the first fn/const/static) whose bare name equals the
path's last segment. It ignores the resolver's binding already present on the path (`HirPath.symbol`, `def_dom`,
`def_mod`, `def_name`, T164/T492, ADR-0043 §2). Struct identity is `def + args` (T444), so picking another module's
`String` yields a different type. This violates nominal identity (REQ-TYP-072) and "a module is a namespace" (REQ-MOD-003).

## Scope
Revised 2026-11-26 (`_workspaces/reports/unblock-T428g.md`): attempt 1 showed that the paths reaching the bare-name walk
are generic-argument paths the resolver never bound. **T428m** (frontend) makes the resolver bind them; HIR lowering
already carries the binding, so after T428m those paths take typeck's symbol-indexed branch of `lookup_path_type`.
1. First re-run the repros and the planned tests on HEAD with T428m in. Record which still fail; typeck work is only what
   remains after the binding exists.
2. In `compiler/types/typeck.ax` `lookup_path_type_by_name` (fn, const/static, struct, enum and type-alias branches):
   - a path with a binding (`symbol != 0` or `def_dom != 0`) never reaches the bare-name walk; if one still does, select
     the item by `symbol` (or `def_mod` + `def_name`), never by bare name;
   - the bare-name walk stays only for paths that truly have no resolver binding (synthetic HIR, lowering sentinels);
     there prefer the current module's item, and when more than one module defines that name and none is the current
     module, do not pick one: emit `AX_NAME_UNRESOLVED` (no silent first match).
   - inventory the other bare-name item scans (attempt 1 found `register_intrinsic_callee`, intrinsic names only, out of
     scope) and list each one in the report.
3. Do not change the resolver or the HIR shape (T428m owns them). A bound path that typeck still mistypes is a typeck
   bug and is fixed here; a path that is still unbound where it should be bound is reported as `BLOCKED` against T428m.
4. Tests (`modes: interp native`, exact `// stdout:`):
   - `tests/run/same_name_std_types/`: the three repros above compile and run (user `String`, user `IoError`, both std
     `String`s imported in one program, values of each type created and used).
   - `tests/modules/same_name_types/`: a package with modules `a` and `b` each defining `struct S` and `fn mk() -> S`
     with different fields, used together from `main` (also as `Option<a.S>` / `Result<b.S, a.S>` generic args); and a
     compile-fail case assigning `a.S` to `b.S` (`AX_TYPE_MISMATCH`).
5. Remove the two lines naming `T428g` (and their comment block) from `_workspaces/baseline-failures.txt` once both
   e11_5 tests pass in all their modes.

## Acceptance
- [ ] The repros fail on HEAD (shown in the report) and pass after the fix in interp, native and native-O1; WEAK-NATIVE 0.
- [ ] `conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax` and `fiber_in_async_and_threads.ax` pass in all
      modes; their baseline lines are removed.
- [ ] `tests/typeck/**`, `tests/ui/**`, `tests/modules/**`, `tests/std/**`, `tests/conformance/p11/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/types`; fixed point of the stage-2 build holds.
      Report `_workspaces/reports/T428g-report.md` with an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`)
- 2026-11-26 10:14:53 started (attempt 1) T428g-impl
- 2026-11-26 10:40:50 block: root cause in resolver: resolve_type/resolve_path_seg never bind generic_args segments (Result<String, IoError>, Option<a.S> get symbol=0), so typeck falls back to bare-name walk; needs a frontend resolver task first
- 2026-11-26 10:43:43 unblocked (cycle 1) 
