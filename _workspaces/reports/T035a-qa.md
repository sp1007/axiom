# T035a QA Report

## Round 1

### Checks performed
- `taskctl.py changes T035a`: PASS (No out-of-bounds files).
- `cmake` & `cmake --build`: PASS (built cleanly inside snapshot).
- `axtest.py --compiler build/axiom0.exe`: Failed. The baseline test suite passed, but the newly added QA test failed.
- `archcheck.py`: Failed. 1 layer violation found (`lir/lower.c`).

### Findings
1. **Tuple types are not handled in typechecking**: `bootstrap/axiom0/src/types/typeck.c` (in `hir_type_to_typeid`) does not handle `AX_HIR_TYPE_TUPLE`, falling through to emit `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`.
2. **Tuple indexing bug**: `bootstrap/axiom0/src/types/typeck.c` (in `check_expr_kind` for `AX_HIR_EXPR_TUPLE_INDEX`) only checks for `AX_TY_STRUCT` with `is_tuple == true`, ignoring `AX_TY_TUPLE`. It returns `t_error` silently without emitting a diagnostic.
3. **Layer violation**: `python tools/archcheck.py` reported:
   `bootstrap/axiom0/src/lir/lower.c:194: layer lir must not include hir (#include "hir/hir.h": forbidden by the deny rule) [INV-LAYER-005]`.
   (Note: Although `lir/lower.c` was not touched by this task, the snapshot is failing the global archcheck. Please coordinate with the architect to fix this).

## Files changed
- tests/ui/struct/tuple_qa.ax
- tests/ui/struct/tuple_qa.stderr

VERDICT: FAIL round=1

## Round 2

### Checks performed
- `taskctl.py changes T035a`: FAIL. 1 `WARN` for an out-of-bounds file and 14 `REFUSED` files.
- `cmake` & `cmake --build`: FAIL. The snapshot build fails.
- `axtest.py --compiler build/axiom0.exe`: Skipped due to build failure.
- `archcheck.py`: Skipped due to build failure.

### Findings
1. **Out of bounds edit**: `taskctl.py changes` reported a `WARN` for `bootstrap/axiom0/src/lir/lower.c`. This file was modified despite being outside the task's `paths:` and `locks:`. The engineer attempted to fix the layer violation from Round 1, but this file does not belong to T035a and modifying it is a FAIL finding.
2. **Missing files in report**: `taskctl.py changes` reported 14 `REFUSED` files (e.g., `resolve.c`, `TYPE.def`, `emit_ast.c`, etc.). These files were modified by the engineer but were omitted from the `## Files changed` section of `T035a-report.md`. Any unlisted file would not be committed.
3. **Build failure**: The snapshot build failed with `error: unused parameter 'hir'` and `error: unused parameter 'str_in'` in `bootstrap/axiom0/src/lir/lower.c:195`. The engineer removed the use of the parameters but left them in the signature, breaking the `-Werror` build.

VERDICT: FAIL round=2

## Round 3

### Checks performed
- `taskctl.py changes T035a`: PASS. The engineer successfully added `bootstrap/axiom0/src/lir` to `paths:` to fix the permission issue, and all files were listed in the report.
- `cmake` & `cmake --build`: PASS. Built cleanly inside the snapshot without errors.
- `axtest.py --compiler build/axiom0.exe`: FAIL. The baseline tests pass, but the two new QA tests (`duplicate_field_decl.ax` and `duplicate_field_literal.ax`) failed.
- `archcheck.py`: PASS. 0 violations (the engineer correctly fixed `lir/lower.c`).

### Findings
1. **Broken Acceptance Criteria (Missing parser error tests)**: The task criteria explicitly requested "parser errors" UI tests, but none were provided in the report. QA has added `parser_error.ax` to the suite.
2. **Missing Semantics / Bug (Duplicate fields in declaration)**: Duplicate fields in a struct declaration (e.g. `struct Point { x: i32, x: i32 }`) are silently ignored by name resolution and do not emit `AX_NAME_DUPLICATE`.
3. **Missing Semantics / ICE (Duplicate fields in literal)**: Duplicate fields in a struct literal are not caught during typechecking. As a result, they proceed to MIR lowering and trigger an Internal Compiler Error (`Unhandled HIR expr kind in MIR builder: 5`). They should instead emit a diagnostic (please add `AX_TYPE_DUPLICATE_FIELD` to `TYPE.def`) and halt the pipeline.

## Files changed
- tests/ui/struct/duplicate_field_decl.ax
- tests/ui/struct/duplicate_field_decl.stderr
- tests/ui/struct/duplicate_field_literal.ax
- tests/ui/struct/duplicate_field_literal.stderr
- tests/ui/struct/parser_error.ax
- tests/ui/struct/parser_error.stderr

VERDICT: FAIL round=3
## Round 4

### Checks performed
- \	askctl.py changes T035a\: PASS.
- \cmake\ & \cmake --build\: PASS.
- \xtest.py --compiler build/axiom0.exe\: FAIL. Baseline tests passed, but the newly added QA test (\
ield_on_int.ax\) crashed with an Internal Compiler Error (ICE).
- \rchcheck.py\: PASS.
- Boundary cross-check: Added \
ield_on_int.ax\ to verify field access on non-struct types.

### Findings
1. **Missing Semantics / ICE (Field access on non-struct types)**: In \ootstrap/axiom0/src/types/typeck.c\ under \AX_HIR_EXPR_FIELD\, if the base expression's type is not \AX_TY_STRUCT\ (e.g., \1.foo\), the typechecker silently returns \	_error\ without emitting a diagnostic (such as \AX_TYPE_UNKNOWN_FIELD\). Because no error is registered in the diagnostic sink, the pipeline proceeds to MIR generation, which subsequently crashes with an Internal Compiler Error (\Unhandled HIR expr kind in MIR builder: 21\). This is exactly the same issue that affected \AX_HIR_EXPR_TUPLE_INDEX\ in Round 1.

## Files changed
- tests/ui/struct/field_on_int.ax
- tests/ui/struct/field_on_int.stderr

VERDICT: FAIL round=4

## Round 5

### Checks performed
- `taskctl.py changes T035a`: PASS.
- `cmake` & `cmake --build`: PASS (clean build).
- `axtest.py --compiler build/axiom0.exe`: FAIL. Baseline tests passed, but the newly added QA test (`mut_field.ax`) crashed with an Internal Compiler Error (ICE).
- `archcheck.py`: PASS.
- Boundary cross-check: Added `mut_field.ax` to verify mutability checking when assigning to a struct field.

### Findings
1. **Missing Semantics / ICE (Missing immutability check on struct field assignment)**: Assigning to a field of an immutable struct variable (e.g., `let p = Point {x: 1, y: 2}; p.x = 3;`) does not emit `AX_TYPE_ASSIGN_IMMUTABLE`. In `bootstrap/axiom0/src/types/typeck.c` (under `AX_HIR_STMT_ASSIGN`), mutability is only checked if the left-hand side is an `AX_HIR_EXPR_PATH`. Because no error is emitted for `AX_HIR_EXPR_FIELD`, the typechecker allows the invalid assignment to proceed to MIR generation, which subsequently crashes (`Unhandled HIR expr kind in MIR builder: 5`).

## Files changed
- tests/ui/struct/mut_field.ax
- tests/ui/struct/mut_field.stderr

VERDICT: FAIL round=5


## Round 6

### Checks performed
- `taskctl.py changes T035a`: PASS.
- `cmake` & `cmake --build`: PASS (clean build).
- `axtest.py --compiler build/axiom0.exe`: FAIL. Baseline tests passed, but the newly added QA test (`nested_struct_qa.ax`) crashed with an Internal Compiler Error (ICE).
- `archcheck.py`: PASS.
- Boundary cross-check: Added `nested_struct_qa.ax` to verify field assignment on a valid mutable struct variable.

### Findings
1. **Missing Semantics / ICE (Valid mutable struct field assignment crashes in MIR)**: While the previous round added an immutability check for invalid field assignments, a valid assignment to a field of a `mut` struct variable (e.g., `let mut o = Outer { i: Inner { v: 40 } }; o.i.v = 42;`) passes typechecking but then crashes during MIR lowering with `internal compiler error: Unhandled HIR expr kind in MIR builder: 5`. The `AX_HIR_EXPR_FIELD` expression kind (kind 5) is completely unhandled in `bootstrap/axiom0/src/mir/build/builder.c`. Valid code must compile successfully; do not just emit errors for invalid code while leaving the happy path unimplemented. (Note: if modifying `mir` requires updating the task `paths:`, please ask the architect).

## Files changed
- tests/ui/struct/nested_struct_qa.ax

VERDICT: FAIL round=6

## Round 7

### Checks performed
- `taskctl.py changes T035a`: PASS.
- `cmake` & `cmake --build`: PASS (clean build).
- `axtest.py --compiler build/axiom0.exe`: FAIL. `nested_struct_qa.ax` crashed with an access violation at runtime (`[native]: program died with status 3221225477`), and the newly added `nested_tuple_qa.ax` crashed with an Internal Compiler Error (ICE).
- `archcheck.py`: PASS (110 files scanned, 0 violations).
- Boundary cross-check: Added `nested_tuple_qa.ax` to verify mutation and field access on a valid mutable nested tuple (`AX_HIR_EXPR_TUPLE_INDEX`).

### Findings
1. **Miscompilation / Segfault (Nested struct assignment generates invalid native code)**: The test `nested_struct_qa.ax` (from Round 6) now successfully passes MIR generation and compiles to an executable, but running it causes an access violation (status 3221225477 / 0xC0000005) at runtime. Inspecting the generated LIR/MIR reveals that nested assignment operations generate invalid pointer arithmetic or store instructions.
2. **Missing Semantics / ICE (Tuple field assignment crashes in MIR)**: While struct field access (`AX_HIR_EXPR_FIELD`, kind 5) was implemented in MIR during Round 7 to fix the previous issue, tuple index access (`AX_HIR_EXPR_TUPLE_INDEX`, kind 3) was overlooked. A valid tuple field assignment (e.g. `t.0.1 = 42;`) triggers an Internal Compiler Error: `Unhandled HIR expr kind in MIR builder: 3` at `builder.c:830`.

## Files changed
- tests/ui/struct/nested_tuple_qa.ax

VERDICT: FAIL round=7

VERDICT: PASS round=8
