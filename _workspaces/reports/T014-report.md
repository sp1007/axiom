# T014: Name resolution: scope graph, dotted paths, prelude stub

## Work Done
- Defined `AxSymbolId` and `AxResolveMap` side-table in `resolve.h`.
- Implemented `ax_resolve` pass in `resolve.c` with a two-phase AST visitor (Phase A for declarations, Phase B for bodies) to populate `AxResolveMap`.
- Added primitive types (e.g. `i32`, `bool`) into a prelude scope.
- Cloned `emit_ast.c` logic into `emit_resolved.c` and hooked into `AxResolveMap` to emit `@Sym(X)` output.
- Handled disambiguation of DottedChain for `AX_EXPR_POSTFIX` and `AX_TYPE_PATH`.
- Supported Enum Variant paths lookup.
- Fixed `bootstrap/axiom0/src/syntax/parse.c` to actually parse `AxAstVariantDecl` instead of skipping them.
- Created unit tests in `tests/resolve` and UI diagnostics tests in `tests/ui/resolve`.
- Created Enum Variant golden tests and verified output.

## Files changed
- bootstrap/axiom0/src/syntax/parse.c
- bootstrap/axiom0/src/resolve/resolve.h
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/driver/emit_resolved.c
- tests/resolve/R01_basic.ax
- tests/resolve/R01_basic.resolved
- tests/resolve/enum_variant.ax
- tests/resolve/enum_variant.resolved
- tests/resolve/simple.ax
- tests/resolve/simple.resolved
- tests/ui/resolve/E01_unknown.ax
- tests/ui/resolve/E01_unknown.test
- tests/ui/resolve/E02_duplicate.ax
- tests/ui/resolve/E02_duplicate.test
- tests/ui/resolve/W01_shadow_module.ax
- tests/ui/resolve/W01_shadow_module.test
- tests/ui/resolve/duplicate_item.ax
- tests/ui/resolve/duplicate_item.test
- tests/ui/resolve/field_access.ax
- tests/ui/resolve/field_access.test
- tests/ui/resolve/shadowing_error.ax
- tests/ui/resolve/shadowing_error.test
- tests/ui/resolve/unknown_name.ax
- tests/ui/resolve/unknown_name.test
- tests/ui/resolve/use_before_let.ax
- tests/ui/resolve/use_before_let.test

STATUS: COMPLETE
