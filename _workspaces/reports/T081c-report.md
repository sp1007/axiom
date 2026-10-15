# T081c — Port Pattern Exhaustiveness and Reachability Checker to Axiom

## Summary
- Ported the Stage-0 Maranget usefulness/exhaustiveness algorithm (`bootstrap/axiom0/src/types/exhaust/exhaust.h`, `exhaust.c`) to pure Axiom in `compiler/types/exhaust.ax` and updated `compiler/types/mod.ax`.
- Implemented `PatMatrix` and `PatRow` construction over `HirPat` (`PAT_WILD`, `PAT_BIND`, `PAT_LIT`, `PAT_RANGE`, `PAT_TUPLE`, `PAT_STRUCT`, `PAT_ENUM`, `PAT_OR`, `PAT_ARRAY`), constructor specialization (`specialize`), default matrix construction (`default_matrix`), `is_useful`, integer range gap splitting, and `check_match_exhaustiveness` / `check_let_irrefutable`.
- Added selfhost verification suite `tests/selfhost/types/qa_types_exhaust.ax`.

## Verification
- `python tools/axtest.py selfhost/types/qa_types_exhaust.ax`: PASS across `[interp]`, `[native]`, and `[native-O1]`.
- `python tools/archcheck.py`: 0 violations.
