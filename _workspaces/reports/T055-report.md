# T055 Report

## Files changed
- bootstrap/axiom0/src/diag/codes/TRAIT.def
- bootstrap/axiom0/src/driver/build_native/build.c
- bootstrap/axiom0/src/driver/mono.c
- bootstrap/axiom0/src/driver/mono.h
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/traits/mono/mono.c
- bootstrap/axiom0/src/traits/mono/mono.h
- bootstrap/axiom0/src/traits/solver.c
- bootstrap/axiom0/src/traits/solver.h
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- bootstrap/axiom0/src/verify/verify.c
- tests/run/drop/qa_drop_call_var.ax
- tests/run/drop/qa_drop_var.ax
- tests/run/trait/dispatch.ax
- tests/ui/drop/qa_drop_call_var.ax
- tests/ui/drop/qa_drop_var.ax
- tests/ui/method/inherent_methods_err.ax
- tests/ui/trait/ambiguity.ax
- tests/ui/trait/missing_impl.ax
- tests/ui/trait/overlap.ax
- tests/ui/trait/qa_bounds.ax
- tests/ui/trait/qa_bounds.stderr
- tests/ui/trait/qa_extra.ax
- tests/ui/trait/qa_overlap_negative.ax
- tests/ui/trait/qa_round4_bounds.ax
- tests/ui/trait/qa_round4_bounds.stderr
- tests/ui/trait/qa_where.ax
- tests/ui/trait/qa_where.stderr

## Mapping
- Trait decls, impls, bounds, where clauses: `tests/ui/trait/qa_bounds.ax`, `tests/ui/trait/qa_where.ax`, `tests/ui/trait/qa_extra.ax`
- solver results PROVEN/DISPROVEN/AMBIGUOUS/OVERFLOW: `tests/ui/trait/ambiguity.ax`, `tests/ui/trait/missing_impl.ax`
- coherence/orphan rules (basic): `tests/ui/trait/overlap.ax`, `tests/ui/trait/qa_overlap_negative.ax`
- static dispatch through monomorphization: `tests/run/trait/dispatch.ax`

STATUS: COMPLETE round=5
