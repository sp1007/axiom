# T080b Report — Port HIR data model and lowering to Axiom

## Summary
- Ported the High-level Intermediate Representation (HIR) data model, S-expression emitter, and AST-to-HIR lowering pass (`bootstrap/axiom0/src/hir/hir.h`, `bootstrap/axiom0/src/driver/emit_hir.c`, and `bootstrap/axiom0/src/hir/lower.c`) to pure Axiom under `compiler/hir/`:
  - `compiler/hir/hir.ax`: Full HIR node hierarchy (`HirFile`, `HirItem`, `HirStmt`, `HirExpr`, `HirPat`, `HirType`, `HirBlock`, `HirParam`, `HirFieldDecl`, `HirVariantDecl`, `HirGenericParam`, `HirWherePred`, `HirMatchArm`, `HirFieldInit`, `HirPatField`, `HirPath`, `HirPathSegment`), binary/unary/assignment/jump operator tags, and canonical S-expression HIR emission (`emit_hir`).
  - `compiler/hir/lower.ax`: Full AST-to-HIR lowering (`lower_file`), including `for .. in start..end` / `start..=end` loop desugaring to `let mut __iter` + `while`, compound assignment (`+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`) desugaring, postfix call/method-call/field/index/try/tuple-index lowering, module-qualified path vs method call disambiguation via `ResolveMap.module_access_nodes`, `extern` block item flattening, and `Drop::drop` registration (`drop_fns`).
  - `compiler/hir/mod.ax`: Package re-exports for `compiler.hir`.
- Created the unit and differential HIR test suite under `tests/selfhost/hir/`:
  - `qa_hir_corpus.ax` (`[interp]`, `[native]`, `[native-O1]`): differential parity against `axiom0 inspect --emit=hir` across all 6 HIR fixtures (`tests/hir/*.ax`).
  - `qa_hir_desugar_and_drop.ax` (`[interp]`, `[native]`, `[native-O1]`): differential parity on `for`-loop desugaring, all 10 compound assignments, `Drop::drop` registration, `extern "C"` flattening, module-qualified calls, pattern destructuring, `?` operator, and `AX_PARSE_UNSUPPORTED` diagnostics.
- Verified `python tools/archcheck.py` (0 violations) and all 6 test runs in `tests/selfhost/hir/` pass.

## Files changed
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- compiler/hir/mod.ax
- tests/selfhost/hir/qa_hir_corpus.ax
- tests/selfhost/hir/qa_hir_desugar_and_drop.ax

STATUS: COMPLETE round=0
