# T081a — Port Type Model, Interner, Substitution, Unifier, and Layout to Axiom

## Summary
- Ported the Stage-0 type system core (`bootstrap/axiom0/src/types/types.h`, `types.c`, `layout/layout.h`, `layout/layout.c`) to pure Axiom in `compiler/types/types.ax` and `compiler/types/layout.ax`.
- Implemented `TypeInterner`, canonical FNV-1a type hashing, primitive type pre-interning (`TY_ERROR`..`TY_STR`), structural interning for pointers, slices, arrays, views, tuples, functions, closures, structs, enums, type parameters, inference variables, and projections.
- Implemented union-find unification (`type_unify`, `type_resolve`), generic substitution (`type_substitute`), type formatting (`type_format`), and target layout calculation (`type_layout`, struct field offsets, enum tag/payload layout, cycle detection).
- Added selfhost verification suite `tests/selfhost/types/qa_types_layout.ax`.

## Verification
- `python tools/axtest.py selfhost/types/qa_types_layout.ax`: PASS across `[interp]`, `[native]`, and `[native-O1]`.
- `python tools/archcheck.py`: 0 violations.
