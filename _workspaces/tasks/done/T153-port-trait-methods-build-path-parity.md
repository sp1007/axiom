---
id: T153
title: Port trait items parity - method symbols, default-method instances, derive, associated types in axiomc build
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T151]
priority: 117
status: done
attempts: 1
paths: [compiler/resolve, compiler/types, compiler/typeck_traits, compiler/traits, compiler/driver/pipeline.ax, compiler/mir/builder.ax, compiler/backend, tests/run/parity/traits, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0032-unblock-t131-drop-destructors.md, 0133]
covers: [REQ-TRT-005, REQ-TRT-006, REQ-TRT-012, REQ-BLD-030]
started: 2026-10-30 01:04:35
unblocks: 1
finished: 2026-10-30 05:29:00
---
# T153 — Port trait items parity in the build path

## Goal
Trait impl methods, default methods, derived methods and associated types are resolved, instantiated
and named in axiomc's `build` exactly as in axiom0, so every `tests/run/trait2` program links and
runs identically.

Confirmed defects (architect probe 2026-10-20):
1. `tests/run/trait2/test_default_override.ax` (`different-behaviour`, axiomc image exits 1): the
   default `hello` for `DefaultUser` is not instantiated (4 vs 5 defined symbols) and methods are
   emitted under the bare name `hello`, so `d.hello()` links to `CustomUser`'s `hello` (100, not 42).
2. `trait2/test_default_method.ax`: `AX_LINK_UNDEFINED_SYMBOL hello`; `trait2/test_derive.ax`:
   `AX_LINK_DUPLICATE_SYMBOL hash` (derived methods share a bare symbol).
3. `trait2/test_assoc_items.ax`: `fn get(self: view<Self>) -> Self.Item;` fails
   `AX_NAME_UNRESOLVED` (associated-type path in a trait signature).

## Scope
- Port the method-symbol mangling, default-method instantiation per implementing type, derive
  expansion naming and `Self.<Assoc>` resolution so that the function list, symbol names and code
  equal axiom0's. If axiom0's own scheme can produce colliding names for these programs, fix both
  (ADR-0034 §2, §6 `$` reserved form).

## Acceptance
- [ ] `tests/run/parity/traits/` (`modes: interp native`, values by hand): `default_vs_override.ax`
      (two types, one overriding a default method, a third type with a same-named inherent method;
      prints each result), `derive_two_types.ax` (two structs deriving the same trait, results
      printed), `assoc_type.ax` (trait with `Self.Item` return, two impls). Pass with axiom0 and are
      identical under the e2e oracle.
- [ ] `known_divergent.txt` shrinks by every entry that becomes identical — at least the 4 entries of
      the plan table (`tests/run/trait2/{test_assoc_items,test_default_method,test_default_override,
      test_derive}.ax`); no entry is added.
- [ ] Full suite passes in `build-snap-T153` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T153-report.md` with exact `## Files changed` and the removed
      registry paths.

## Out of scope
- `dyn Trait` (T058); operator-trait typing crash (T151).
- Semantic per-implementing-type instantiation of default bodies (a default body calling a required
  method must bind it to the implementing type; axiom0, port and interpreter all bind the first impl
  today) — that is a lockstep axiom0+port fix, T161 (AX0-FIX-09). T153 keeps parity with axiom0's
  current behaviour.

## Unblock (2026-10-30, architect, unblock-T153)
- `compiler/mir/builder.ax` added to `paths:` (no todo/doing task owns it concurrently: T156 depends
  on T153; T058/T089 are post-self-host). Apply the `mb_build_expr_as_operand` FIELD→CONST-item case
  from the attempt-1 report (mirrors axiom0 `mir/build/builder.c`), regenerate every selfhost bundle
  named by `tests/selfhost/*/bundles_current.test`, remove `tests/run/trait2/test_assoc_items.ax`
  from `known_divergent.txt`, and finish the full suite in `build-snap-T153` (not yet claimed).
- Keep the attempt-1 changes already in the working tree (pipeline.ax, resolver.ax, parity tests,
  bundles, registry edits).

## Notes
- After T151 (shares typeck paths; generic default methods need instantiation).
- ADR-0035 §4: remove registry lines explicitly; adding is forbidden.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-29 22:34:11 started (attempt 1) T153-impl
- 2026-10-29 23:06:49 requeue: recovered: previous session ended during impl (not charged: attempt refunded)
- 2026-10-29 23:07:00 started (attempt 1) T153-impl
- 2026-10-30 01:01:00 block: needs compiler/mir/builder.ax (outside paths) for associated-const Type.CONST stack overflow; patch in report
- 2026-10-30 01:02:55 unblocked (cycle 1) 
- 2026-10-30 01:04:35 started (attempt 1) T153-impl
- 2026-10-30 05:29:00 accepted by QA -> done
