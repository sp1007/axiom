# T019 report
## Summary
Implemented the basic THIR -> MIR builder (`ax_mir_build`) for a subset of features (locals, temps, arithmetic, comparisons, short-circuit, if, while, loop, break, continue, return, calls).
Hooked up the builder in `emit_mir.c` so that it parses `.ax` files, extracts type information, and correctly runs and prints the built MIR.
Added golden tests verifying the control flow constructions and evaluation orders.

## Files changed
- bootstrap/axiom0/src/driver/emit_mir.c
- bootstrap/axiom0/src/mir/build/build.h
- bootstrap/axiom0/src/mir/build/builder.c
- tests/mir/build/calls.ax
- tests/mir/build/calls.mir
- tests/mir/build/control_flow.ax
- tests/mir/build/control_flow.mir
- tests/mir/build/first_mir.ax
- tests/mir/build/first_mir.mir
- tests/mir/build/short_circuit.ax
- tests/mir/build/short_circuit.mir

## Tests
- `tests/mir/build/first_mir.ax`: `return 40 + 2` -> `const/const/add/return`.
- `tests/mir/build/calls.ax`: tests function calls.
- `tests/mir/build/control_flow.ax`: tests `if`, `while`, `break`, loops.
- `tests/mir/build/short_circuit.ax`: tests `&&` and `||`.

## Spec deviations
- For evaluation of variables (`AX_HIR_EXPR_PATH`), `AX_MIR_OP_COPY` is aggressively used for all non-constant paths pending ownership elaboration.
- The `return 40 + 2` is evaluated as `_0 = const 40 + const 2;` rather than strictly evaluating individual literal constants into temporaries (since operands take constants directly).

## Follow-ups
None.

STATUS: COMPLETE round=0
