---
id: T423e
title: Fix — the "self entry" placeholder rewrite is keyed by fn name: two `__ax_thread_self_entry` in different modules run the wrong entry
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T423]
priority: 50
status: todo
attempts: 0
timeout_min: 480
paths: [tests/run/self_entry_placeholder]
locks: [compiler/interp/interp.ax, compiler/lir/builder.ax, compiler/mir/builder.ax, std/thread/mod.ax, std/fiber/mod.ax, tests/std/fiber/gen_tests.py]
spec: [spec/SPEC-32-threads-sync.md, spec/SPEC-34-executors-fibers.md, spec/decisions/ADR-0046-t423-fiber-followups-and-tracked-xfail.md]
covers: [REQ-TST-072]
---
# T423e — Self-entry placeholder resolved by identity, not by name

## Goal
A generic trampoline cannot be used as a function value (T422a FU-J), so std.thread passes "the enclosing function" as an
entry through a placeholder fn `__ax_thread_self_entry` whose *name* the interpreter (`is_self_entry_fn_item`) and the LIR
builder (`is_fiber_self_entry_name` / thread equivalent) rewrite. With a second same-named placeholder in another module
(std.fiber, bundled after std.thread) the wrong entry runs: `Completed` without a result in interp, access violation natively
(T423 report F4, QA note). T423 works around it with a second name `__ax_fiber_self_entry`.

## Scope
- Isolate the root cause (name-keyed lookup in the interp/LIR rewrite, or in resolve/mono picking the first item of that name)
  with a minimal two-module repro, then key the rewrite by item identity — e.g. a marker attribute/lang item on the placeholder,
  or the resolved item id of the placeholder within the enclosing module — so any number of modules may declare a placeholder.
- Same behaviour in interp and native; no name list in the compiler.
- If the fix allows it, make std.fiber use the common mechanism (one placeholder per module, either name); regenerate the fiber
  bundles with `python tests/std/fiber/gen_tests.py` (`--check` passes).
- Tests `tests/run/self_entry_placeholder/*.ax` (exact stdout, `modes: interp native`): two and three modules each with their own
  placeholder used from generic trampolines, bundled in both orders; a plain fn of that name that is not a placeholder is a normal
  fn.

## Acceptance
- [ ] New tests pass in interp, native and native-O1 (WEAK-NATIVE 0); `tests/std/thread`, `tests/std/fiber`, `tests/std/async`
  pass; selfhost interp/lir/mir groups pass; gate per axiom-qa.md "Per-task gate scope".
- [ ] Report `_workspaces/reports/T423e-report.md` with the root cause and exact `## Files changed`.

## Out of scope
- Generic functions as function values (T422a FU-J), `spec/`, `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-21 created by axiom-architect (triage-t423, ADR-0046; T423 QA follow-up 4 / report F4)
