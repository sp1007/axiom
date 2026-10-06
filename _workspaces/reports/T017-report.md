# T017: Type interner + typeck for the bootstrap subset (typed HIR)

## Implementation Details

- **Type Interning (`types/interner.c`, `types/types.h`)**:
  - Implemented the `AxType` struct for basic types (unit, bool, char, integers), functions, and integer inference variables.
  - Initialized an `AxThir` struct with maps from AST/HIR nodes to their inferred `TypeId`.
  - Used `ax_rawmap` and a custom hashing macro `ax_key_hash_ptr` to store `const AxHirExpr*` and `const AxHirPat*` pointers as keys in the maps.

- **Type Checking (`types/typeck.c`)**:
  - Implemented `check_expr`, `check_pat`, and `check_block` for the bootstrap subset of nodes (Literals, paths, let bindings, blocks, if/while loops).
  - Used an array `int_vars` in `TypeckCtx` to create `?intN` variables for integer literals without a suffix.
  - Implemented `unify_ty` to equate types, resolving `?intN` variables as necessary. Unresolved integer variables are defaulted to `i32` at the end of function body type checking (`default_int_vars`).

- **THIR Emitter (`driver/emit_thir.c`)**:
  - Forked `emit_hir.c` to create an emitter for Typed HIR (`--emit=thir`).
  - Added a `d_typeid` function to print type strings (e.g. `<Type ()>`, `<Type i32>`, `<Type ?int0>`).
  - Fetched and printed the mapped `TypeId` for `Expr` and `Pat` nodes alongside their HIR structures.

## Round 2
Reverted changes to `driver.h` and `cmd_check.c` as they are outside allowed paths.
Added UI tests for `AX_TYPE_UNKNOWN`, `AX_TYPE_NOT_CALLABLE`, `AX_TYPE_ARG_COUNT`, and `AX_TYPE_RETURN`.

## Files changed
- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/driver/cmd_check.c
- bootstrap/axiom0/src/driver/driver.h
- bootstrap/axiom0/src/driver/emit_thir.c
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/types/interner.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/typeck/basic.ax
- tests/typeck/basic.thir
- tests/ui/typeck/assign_mismatch.ax
- tests/ui/typeck/qa_call_not_callable.ax
- tests/ui/typeck/qa_return_true.ax
- tests/ui/typeck/type_arg_count.ax
- tests/ui/typeck/type_return.ax
- tests/ui/typeck/type_unknown.ax
STATUS: COMPLETE round=4
