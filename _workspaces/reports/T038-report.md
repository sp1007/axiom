# Task T038 - Enums + match + exhaustiveness

## Round 1
The original implementation added exhaustiveness checking for matches on enums, but missed a safety check in `typeck.c`. When an empty match block (a match with no arms) was encountered, the return type of the match expression defaulted to `TypeId_none()`. This cascaded into a compiler ICE because `ax_type_get` crashed when it received an invalid type ID (`TypeId_none()`).

## Round 2
Fixed the ICE by giving the empty match expression an explicit type. If the match block is empty (no arms), its type defaults to `never` instead of `none`. If there are arms but they all have error types, it defaults to `error`. This correctly propagates `never` or `error` outwards, averting the ICE, while still correctly reporting `AX_PAT_NON_EXHAUSTIVE`. The newly added `exhaustiveness_missing_all.ax` test now safely emits the exhaustiveness error without crashing.

## Round 3
Fixed a type safety violation in `typeck.c` where patterns of kind `AX_HIR_PAT_STRUCT` and `AX_HIR_PAT_PATH` were not checking if their resolved path type successfully unifies with the expected type. They now correctly enforce that `unify_ty` matches the pattern type and the expected type. Additionally, we added support for `AX_TY_ENUM` inside `check_expr` for `AX_HIR_EXPR_STRUCT` to correctly type check expression instantiations of enum variants with fields (e.g., `Enum.Variant { field: value }`). Both tests `exhaustiveness_wrong_enum.ax` and `exhaustiveness_wrong_enum_struct.ax` now pass correctly by emitting `AX_TYPE_MISMATCH`.

## Files changed
- bootstrap/axiom0/src/diag/codes/PAT.def
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/types/interner.c
- bootstrap/axiom0/src/types/layout/layout.c
- bootstrap/axiom0/src/types/layout/layout.h
- bootstrap/axiom0/src/types/match/exhaust.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/run/enum/exhaustiveness.ax
- tests/run/enum/exhaustiveness_wildcard.ax
- tests/run/enum/run_enum.ax
- tests/ui/enum/enum_cast_payload.ax
- tests/ui/enum/exhaustiveness_missing.ax
- tests/ui/enum/exhaustiveness_missing_all.ax
- tests/ui/enum/exhaustiveness_missing_multiple.ax
- tests/ui/enum/exhaustiveness_missing_payload.ax
- tests/ui/enum/exhaustiveness_wrong_enum.ax
- tests/ui/enum/exhaustiveness_wrong_enum_struct.ax
STATUS: COMPLETE round=3
