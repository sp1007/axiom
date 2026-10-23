---
id: T158
title: AX0-FIX-07 language Drop identified by resolution, not by a .Drop suffix; hir_postprocess_items and pipeline.c agree on destructor renaming (axiom0 + port)
phase: P10-selfhost
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T157]
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/mir/drop/drop.c, compiler/hir/lower.ax, compiler/mir/drop.ax, tests/run/parity/drop_trait, tests/selfhost]
locks: [bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/types/typeck.c, compiler/types/typeck.ax]
spec: [spec/SPEC-12-drop.md, spec/SPEC-04-core-extensibility.md, spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md, spec/decisions/ADR-0034-oracle-independence.md]
covers: [REQ-DRP-051, REQ-DRP-030]
timeout_min: 180
---
# T158 — AX0-FIX-07: identity of the language `Drop`

## Goal
`impl Drop for T` is a destructor iff the trait path resolves to the prelude lang item `Drop`
(SPEC-12 AXS-DROP-008): the bare name `Drop` with no item named `Drop` declared in or imported into
the module. `impl m.Drop for S` (a user trait) and a shadowing user `trait Drop` are ordinary
traits, in both compilers, with byte-identical output.

Confirmed defect (T141 report round 1, T141 QA notes): in axiom0 the function
`is_drop_trait_name` of `mir/drop/drop.c` and the check in `types/typeck.c`, and in the port
the functions `tc_is_drop_trait_name` (`compiler/types/typeck.ax`) and `compiler/mir/drop.ax` `drop_sv_is_drop_trait` accept any path ending in
`.Drop`. Narrowing them alone (tried in T141 round 1) makes a new obj divergence: the port's T131
shortcut in `compiler/hir/lower.ax` `hir_postprocess_items` renames the impl's `drop` method by the
*last path segment* (`Drop`), while axiom0 `driver/pipeline.c` uses the source text (`traits.Drop`).

## Scope
- Make `hir_postprocess_items` and `pipeline.c` decide "this impl is the language Drop" with the same
  predicate (AXS-DROP-008), then narrow the three/four predicates to it, in lockstep. The destructor
  symbol stays ADR-0034 §6 (`<Type>$drop`); a user trait's `drop` method gets the ordinary method
  symbol.
- Shadowing: a module that declares (or imports) an item named `Drop` makes bare `Drop` refer to
  it. Detect it the same way in both compilers (resolver result if available, otherwise the module's
  item/import names — engineer's choice, TYPE A).
- Regenerate selfhost bundles that embed changed `compiler/` files with their generators; list each.

## Acceptance
- [ ] `tests/run/parity/drop_trait/user_trait_named_drop.ax` (`modes: interp native`, hand-written
      `stdout:`): a module `traits` with `trait Drop { fn drop(self: mut_view<Self>); }`,
      `impl traits.Drop for S` whose `drop` prints, `S` has a scalar field; scope end prints nothing,
      an explicit call `s.drop()` prints once; `S` is `Copy`-able per the normal rules (no destructor).
- [ ] `tests/run/parity/drop_trait/lang_drop_still_works.ax`: bare `impl Drop for S` prints at scope
      end (control).
- [ ] `tests/run/parity/drop_trait/shadowing_trait_drop.ax`: a module-local `trait Drop` shadowing the
      prelude; `impl Drop for S` is the user trait (no scope-end output).
- [ ] Every existing `tests/run/drop/**`, `tests/run/mangle/**`, `tests/ui/drop/**` expectation is
      unchanged; `drop_symbols.test` still pins `$drop`.
- [ ] axiomc_e2e: no REGRESSION; `known_divergent.txt` gains no entry.
- [ ] Full suite passes in `build-snap-T158` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T158-report.md` with exact `## Files changed` and regenerated bundles.

## Out of scope
- Lang-item attributes in `std` (`@lang`) — later (SPEC-04 AXS-EXT-023 reserves the table).
- Capability checker (T157), verifier (T159).

## Notes
- AX0-FIX chain: priority 0, runs alone; after T157, before T159.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
