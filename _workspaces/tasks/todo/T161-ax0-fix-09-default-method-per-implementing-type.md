---
id: T161
title: AX0-FIX-09 trait default methods instantiated per implementing type - Self-calls in a default body bind to the implementing impl (axiom0 + port + interpreter)
phase: P10-selfhost
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T153]
priority: 117
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver/mono.c, bootstrap/axiom0/src/driver/mono.h, bootstrap/axiom0/src/traits, compiler/traits, tests/run/parity/trait_default, tests/selfhost]
locks: [bootstrap/axiom0/src/types/typeck.c, bootstrap/axiom0/src/driver/pipeline.c, bootstrap/axiom0/src/mir/build/builder.c, compiler/types/typeck.ax, compiler/typeck_traits, compiler/driver/pipeline.ax, compiler/mir/builder.ax, compiler/interp, tests/selfhost/obj_link_driver/known_divergent.txt]
spec: [spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0035-axiomc-parity-symbols.md, 0133]
covers: [REQ-TRT-005, REQ-TRT-011]
timeout_min: 300
---
# T161 — AX0-FIX-09: trait default methods instantiated per implementing type

## Goal
A trait default method behaves, for every implementing type that does not override it, exactly as if
its body had been written in that type's impl with `Self` = the implementing type (0133 §8, §9,
§14; REQ-TRT-005, REQ-TRT-011). Fixed in axiom0 **and** the port under `compiler/` in lockstep
(ADR-0034 §2), in the interpreter and natively.

Confirmed defect (T153 report, 2026-10-30): a default body is compiled once, not per implementing
type, so a method call on `self` inside it binds to the first impl for every type:

```
trait Base {
    fn base(self: view<Self>) -> i32;
    fn twice(self: view<Self>) -> i32 { self.base() * 2 }
}
```
With `A.base() = 9` and `B.base() = 10`, `b.twice()` gives 18 instead of 20 — in axiom0, in the port
and in the interpreter (so parity tests cannot see it). axiom0 entry points:
`types/typeck.c` `find_trait_default_method` (~871, call sites ~886, ~948), `driver/mono.c`
instance list; port: `compiler/traits/solver.ax` `find_trait_default_method`,
`compiler/traits/mono.ax` (~1113), `compiler/driver/pipeline.ax` trait-member instance emission
(added by T153).

## Scope
- Default-method instances are keyed by (trait member, implementing type); method calls and `Self`
  paths inside the body (`self.m()`, `Self.CONST`, `Self.Item`, supertrait methods) resolve against
  that type's impl. Same rule in typeck, mono, the MIR builder and the interpreter.
- Symbols: each instance gets a distinct, deterministic name derived from the existing method-symbol
  scheme (the dedup pass names); if two instances or an instance and a user item could still collide,
  use the ADR-0034 §6 reserved `$` form. axiom0 and the port produce identical names.
- Selfhost bundles and goldens regenerated from the fixed axiom0; each change explained.

## Acceptance
- [ ] `tests/run/parity/trait_default/` (`modes: interp native`, expected `stdout:` written by hand):
      `self_call_per_type.ax` (the program above with three types, one overriding `twice`; prints
      18, 20 and the override), `supertrait_call.ax` (subtrait default calls a supertrait method,
      two implementing types), `generic_default.ax` (default method with its own type parameter used
      by two implementing types), `assoc_const_in_default.ax` (default body reads `Self.CONST` from
      two impls).
- [ ] Every existing `tests/run/trait2/**` and `tests/run/parity/traits/**` expectation unchanged.
- [ ] axiomc_e2e: no REGRESSION; `known_divergent.txt` gains no entry.
- [ ] Full suite passes in `build-snap-T161` with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T161-report.md` with exact `## Files changed` and regenerated bundles.

## Out of scope
- `dyn Trait` vtables (T058); trait specialization (REQ-TRT-017 forbids it).

## Notes
- Lockstep rule until the freeze after T087 (ROADMAP R3, ADR-0034 §2): axiom0 and port change in the
  same task; the e2e oracle must stay byte-identical.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
