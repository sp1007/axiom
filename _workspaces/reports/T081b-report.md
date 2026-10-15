# T081b — Port Trait Solver and Monomorphizer to Axiom

## Summary
- Ported the Stage-0 trait solver and monomorphizer (`bootstrap/axiom0/src/traits/solver.h`, `solver.c`, `mono.h`, `mono.c`) to pure Axiom in `compiler/traits/solver.ax`, `compiler/traits/mono.ax`, and `compiler/traits/mod.ax`.
- Implemented `TraitEnv` registration for traits and impls, coherence/orphan checking (`trait_register_impl`), built-in `Copy` derivation with cycle guard, recursive obligation solving (`trait_solve`) with depth limit (`AX_TRAIT_SOLVE_DEPTH`), and associated type projection normalization (`trait_normalize`).
- Implemented monomorphization worklist, mangled symbol generation (`mono_mangle_name`), generic HIR AST cloning (`mono_run`), and trait method dispatch specialization.
- Added selfhost verification suite `tests/selfhost/traits/qa_traits_solver_mono.ax`.

## Verification
- `python tools/axtest.py selfhost/traits/qa_traits_solver_mono.ax`: PASS across `[interp]`, `[native]`, and `[native-O1]`.
- `python tools/archcheck.py`: 0 violations.
