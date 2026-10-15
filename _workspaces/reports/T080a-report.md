# T080a Report — Port resolver and module graph to Axiom

## Summary
- Ported the Stage-0 C11 name and module resolver (`bootstrap/axiom0/src/resolve/resolve.h`, `bootstrap/axiom0/src/resolve/resolve.c`, and `bootstrap/axiom0/src/driver/emit_resolved.c`) to pure Axiom under `compiler/resolve/`:
  - `compiler/resolve/symtab.ax`: `Symbol`, `NodeMap` (open-addressed pointer-to-`SymbolId` hash table), `SymEnv` (open-addressed `StrId`-to-`Symbol` hash table), `NamingCtx`, and `ResolveMap` (`node_map`, `module_access_nodes`, `extern_nodes`, canonical symbol naming `record_symbol_naming`, `resolve_symbol_module_path`, `resolve_symbol_canonical_name`).
  - `compiler/resolve/rib.ax`: `Scope`, `LabelScope`, `Module`, `VisitedImport`, lexical scope rib allocation (`push_scope`), loop label push/lookup (`push_label`, `find_label_in_scope`), and scope/module cleanup (`free_allocated_scopes`, `free_allocated_modules`).
  - `compiler/resolve/resolver.ax`: Three-pass name and module resolver (`resolve_file`, `resolve_file_into`) covering top-level item/module collection, recursive `use` tree import resolution with cycle detection (`AX_NAME_IMPORT_CYCLE`), visibility enforcement (`VIS_PRIVATE`, `VIS_PUB`, `VIS_PUB_PACKAGE`, `VIS_PUB_MODULE`, `AX_NAME_PRIVATE`), prelude population, item/type/pattern/expression/statement resolution, and canonical S-expression resolved AST emission (`emit_resolved`).
  - `compiler/resolve/mod.ax`: Package re-exports for `compiler.resolve`.
- Created the differential test suite under `tests/selfhost/resolve/` verifying byte-for-byte parity on both resolved AST output (`--emit=resolved`) and human diagnostics across all 5 positive fixtures (`tests/resolve/*.ax`) and all 15 negative UI fixtures (`tests/ui/resolve/*.ax`) in `[interp]`, `[native]`, and `[native-O1]` modes (12/12 test runs PASS).
- Verified `python tools/archcheck.py` (188 files scanned, 0 violations).

## Files changed
- compiler/resolve/mod.ax
- compiler/resolve/resolver.ax
- compiler/resolve/rib.ax
- compiler/resolve/symtab.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax

STATUS: COMPLETE round=0
