# T015 Report: HIR data model + AST->HIR lowering

## Summary
- Defined `hir.h` with the HIR data models (all node kinds reserved up front).
- Implemented `lower.c` and `lower.h` to convert `AxAst` into `AxHir`.
- Replaced name bindings with `AxSymbolId` using `AxResolveMap`.
- Desugared compound assignments, else-if chains, and explicit postfix expressions (including explicit method-call node support).
- Out-of-scope T012 constructs produce the `AX_NAME_NOT_YET_SUPPORTED` diagnostic properly.
- Created `emit_hir.c` in `bootstrap/axiom0/src/driver/` to enable `inspect --emit=hir`.
- Configured `COVERAGE.md` to map tested AST variants to golden snapshot tests.
- Wrote valid and testing-oriented test cases in `tests/hir/` which correctly run under the `axtest.py` test framework and verify the data mapping limits.

## Files changed
- `bootstrap/axiom0/src/driver/emit_hir.c`
- `bootstrap/axiom0/src/hir/hir.h`
- `bootstrap/axiom0/src/hir/lower.c`
- `bootstrap/axiom0/src/hir/lower.h`
- `tests/hir/COVERAGE.md`
- `tests/hir/basic.ax`
- `tests/hir/basic.hir`
- `tests/hir/control.ax`
- `tests/hir/control.hir`
- `tests/hir/exprs.ax`
- `tests/hir/exprs.hir`
- `tests/hir/pats.ax`
- `tests/hir/pats.hir`
- `tests/hir/types.ax`
- `tests/hir/types.hir`

STATUS: COMPLETE round=0
