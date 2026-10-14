# T079a Report — Port AST data model to Axiom

## Summary
- Ported the Stage-0 AST data model (`bootstrap/axiom0/src/syntax/ast.h`) and the `inspect --emit=ast` S-expression dumper (`bootstrap/axiom0/src/driver/emit_ast.c`) to Axiom in `compiler/syntax/ast.ax` (1,499 LOC ≤ 1,500, zero multi-statement lines):
  - All AST node structs (`AstDottedName`, `AstVis`, `AstAttr`/`AstAttrArg`, `AstType`/`AstTypePathSegment`, `AstPat`/`AstPatField`, `AstExpr`/`AstPostfixSeg`/`AstFieldInit`/`AstMatchArm`/`AstBlock`, `AstStmt`, `AstGenericParam(s)`/`AstGenericArg(s)`, `AstWherePred`/`AstWhereClause`, `AstParam`, `AstFieldDecl`, `AstVariantDecl`, `AstUseTree`, `AstItem`, `Ast`). C unions are flattened into single structs keyed by `u8` kind constants matching the C enum values.
  - Zero-initialising arena allocators (`alloc_*`), `link_*` list-append helpers, `ast_walk_items`, `ast_format_derive` (derive expansion text), and `ax_ast_render` producing byte-identical output to `axiom0 inspect --emit=ast` (indentation, leading newline, file filter).
- Bootstrap workaround: `axiom0`'s native backend mis-sizes struct-by-value stores into fields (4-byte `StrId` stored as 8 bytes clobbering the adjacent `kind: u8`; >8-byte structs truncated to 8 bytes). All field writes in `ast.ax` use scalar field stores (`.v = ...`, `ast_set_span`) instead. This should be fixed in `axiom0` as a follow-up task.
- Tests in `tests/selfhost/ast/` (self-contained bundles; each hand-constructs AST nodes and checks `ax_ast_render` byte-for-byte against `axiom0 inspect --emit=ast` output for an equivalent source):
  - `qa_ast_types_pats.ax`, `qa_ast_exprs_a.ax`, `qa_ast_exprs_b.ax`, `qa_ast_items.ax`, `qa_ast_derives.ax` — split so each runs in < 3 s under `[interp]`.
- Additional evidence (prepared for T079b): the companion Axiom parser driving `ax_ast_render` matches all 28 `tests/parse/*.ast` goldens natively.

## Verification
- `python tools/axtest.py --compiler bootstrap/axiom0/build/axiom0.exe selfhost`: all PASS in `[interp]`, `[native]`, `[native-O1]`.
- `python tools/archcheck.py`: 0 violations.

## Files changed
- compiler/syntax/ast.ax
- tests/selfhost/ast/qa_ast_derives.ax
- tests/selfhost/ast/qa_ast_exprs_a.ax
- tests/selfhost/ast/qa_ast_exprs_b.ax
- tests/selfhost/ast/qa_ast_items.ax
- tests/selfhost/ast/qa_ast_types_pats.ax

STATUS: COMPLETE round=0
