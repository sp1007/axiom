# T447 report â€” impl generics in associated types (FU-B); overlap check honours concrete type arguments (FU-C)

## Summary
- **FU-B root cause.** HIR post-processing (`compiler/hir/lower.ax`, `hir_postprocess_items`) appends a shallow
  clone of every impl member to the top-level item list. Typeck pass 1b registered the top-level clone of an
  associated type (`type Output = Result<T, E>`) with `current_impl = null`, so `T` (inside generic arguments,
  where the name lookup is used) was `AX_NAME_UNRESOLVED`. The resolver already scoped impl members correctly.
- **FU-B fix (typeck).** `tc_alias_type_in_scope` computes every type-alias type with the alias as the current item
  and, for an impl's associated type or its clone (recognised by the shared `ty` node, `tc_alias_enclosing_impl`),
  the impl's generic scope and `Self` in force. Used by pass-1b registration, on-demand alias lookups (by symbol,
  by index, by name) and the prelude alias pass. The clone reuses the type already computed for the impl member
  (`tc_alias_orig_member`), so an error in an associated type is reported once.
- **`F.Output` projections.** The resolver accepts a trailing `P.Assoc` segment when `P` is a generic parameter
  (previously "name not found in scope"); typeck (`tc_param_assoc_projection`) resolves it from `P`'s bounds â€”
  inline bounds and `where` predicates of the current item, then of the enclosing impl â€” via the binding
  `Trait<Assoc = X>` (`impl<F: Future<Output = T>, T>`: `F.Output` = `T`). Works in associated types, method
  signatures and local annotations. A projection on a non-parameter is still `AX_NAME_UNRESOLVED`.
- **FU-C fix (trait solver).** `traits_check_overlap` now unifies the two impl headers (trait path and self type)
  before reporting: each impl's generics are fresh variables (side 1/side 2 slot arrays, so equal names never
  alias), concrete types must match structurally including type arguments (paths, tuples, slices/arrays,
  view/ptr with mutability), with an occurs check (`W<X, X>` vs `W<*const F, F>` is disjoint) and a depth guard
  that answers "overlap" (conservative). The cheap head prefilter is kept, so blanket `impl<T> Tr for T` headers
  keep their pre-T447 treatment. The diagnostic stays on the later impl's span.

## Tests
- `tests/typeck/impl_generics_assoc/assoc_type_uses_impl_generics.ax` (run, interp + native + native-O1): both
  FU-B repros (`W<F, T>` with `type Output = Result<T, E>`, `GroupNext<T>` with `Option<TaskResult<T>>`),
  `Outer<G, T>` with `type Output = G.Output` and `Poll<G.Output>` consuming W's associated type through the bound,
  `let inner: Poll<F.Output>` in W's `poll`.
- `tests/typeck/impl_generics_assoc/undeclared_name_in_assoc_type_neg.ax` (ui): undeclared `U` in an impl
  associated type â†’ exactly one `AX_NAME_UNRESOLVED`.
- `tests/typeck/impl_generics_assoc/projection_on_non_param_neg.ax` (ui): `Q.Out` on a non-parameter â†’
  `AX_NAME_UNRESOLVED`.
- `tests/ui/trait_overlap_concrete/concrete_args_disjoint.ax` (ui, positive): `W<F, i64>` / `W<F, ()>` /
  `*const i64` / `*mut i64` / tuples / nested `W<i64, bool>` vs `W<i64, i32>` for one trait, `Future` impls for
  `W<F, i64>` and `W<F, ()>`, repeated generic `W<X, X>` vs `W<bool, i64>` and `W<*const F, F>` (occurs check).
- `tests/ui/trait_overlap_concrete/real_overlap_still_reported.ax` (ui, negative): `impl<F, T>` + `impl<F>` with
  `T` free â†’ `AX_TRAIT_OVERLAP` on the later impl's line (also for `Future`), `W<X, X>` vs `W<i64, i64>` â†’
  overlap, `W<X, X>` vs `W<i64, bool>` â†’ no diagnostic.
- On the unpatched HEAD compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O0_85492f880bce94d9.exe`) the run
  test and both overlap tests fail (unresolved `T`/`G.Output`; spurious overlaps); on `build-snap-T447/build/axiomc2.exe`
  all 7 results pass (`--no-cache -j 2`, `WEAK-NATIVE 0`).

## Follow-ups (not in scope)
- `F.Output` for a parameter whose bound has **no** binding (`fn drive<F: Future>(..) -> Poll<F.Output>`) needs a
  projection type normalised at instantiation; still `AX_NAME_UNRESOLVED` (inference/projection work, cf. T448).
- `compiler/types/exhaust.ax`: nested patterns `Poll.Ready(Option.Some(v))` / `Poll.Ready(Option.None)` give a
  spurious `AX_PAT_UNREACHABLE` warning (pre-existing on HEAD); the run test uses helper functions instead.

## Files changed
- compiler/types/typeck.ax
- compiler/traits/solver.ax
- compiler/resolve/resolver.ax
- tests/typeck/impl_generics_assoc/assoc_type_uses_impl_generics.ax
- tests/typeck/impl_generics_assoc/undeclared_name_in_assoc_type_neg.ax
- tests/typeck/impl_generics_assoc/projection_on_non_param_neg.ax
- tests/ui/trait_overlap_concrete/concrete_args_disjoint.ax
- tests/ui/trait_overlap_concrete/real_overlap_still_reported.ax
- _workspaces/reports/T447-report.md

## Verification (build-snap-T447)
- `build_axiomc.py --out build --stage 3`: FIXED-POINT (O1) OK, STAGE0-GUARD OK.
- `axtest typeck/ ui/trait resolve/ -j 2`: TOTAL 81 PASS 81 FAIL 0, WEAK-NATIVE 0.
- `taskgate --task T447 ... -j 2`: exit 0, FAIL 0, BASELINE OK, WEAK-NATIVE 0 in own/changed tests, archcheck 0 violations (axtest TOTAL 265 PASS 264 SKIP 1).

## Status
STATUS: COMPLETE round=0
