# T081 — Port typeck + trait solver to Axiom (integration + differential typeck)

## Summary
- Integrated the self-hosted type checker (compiler/types), trait solver, and monomorphizer (compiler/traits) into compiler/typeck/session.ax and compiler/typeck_traits/session.ax with differential testing against xiom0 across 	ests/selfhost/typeck/ and 	ests/selfhost/typeck_traits/.

## Files changed
- compiler/kernel/interner.ax
- compiler/traits/mono.ax
- compiler/typeck/mod.ax
- compiler/typeck/session.ax
- compiler/typeck_traits/mod.ax
- compiler/typeck_traits/session.ax
- compiler/types/exhaust.ax
- compiler/types/mod.ax
- compiler/types/typeck.ax
- compiler/types/types.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax

## Verification
- python tools/axtest.py selfhost/typeck selfhost/typeck_traits: PASS across [interp], [native], and [native-O1].
- python tools/archcheck.py: 0 violations.

STATUS: COMPLETE round=0
