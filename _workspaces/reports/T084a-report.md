# T084a Report — Port LIR data model and builder to Axiom

## Summary
Ported the Low-level Intermediate Representation (LIR) data model, printer, and MIR-to-LIR lowering pass from C (`bootstrap/axiom0/src/lir/{lir.h,print.c,lower.c}`) to Axiom under `compiler/lir/`, along with unit and end-to-end golden tests under `tests/selfhost/lir/`.

### Modules implemented (`compiler/lir/`)
- `compiler/lir/lir.ax` (776 lines):
  - LIR identifiers (`LirVRegId`, `LirSlotId`, `LirBbId`, `LIR_VREG_NONE`), virtual register metadata (`LirVReg`), stack slot metadata (`LirStackSlot`), and frame requirements (`LirFrameRequirements`).
  - All 35 LIR instruction opcodes (`LIR_INST_CONST` through `LIR_INST_BITNOT`) and payload representation (`LirInst`), all 5 LIR terminator kinds (`LIR_TERM_RETURN`, `LIR_TERM_JMP`, `LIR_TERM_BR`, `LIR_TERM_SWITCH`, `LIR_TERM_ASSERT`, `LIR_TERM_UNREACHABLE`) with switch targets (`LirSwitchTarget`, `LirTerminator`), basic block (`LirBb`), body (`LirBody`), and file (`LirFile`).
  - Arena-backed constructors and mutators (`lir_body_new`, `lir_add_slot`, `lir_new_vreg`, `lir_add_bb`, `lir_emit_inst`) and exact port of `ax_lir_print` (`lir_print_body`, `lir_print_file`) matching `axiom0 inspect --emit=lir`.
- `compiler/lir/builder.ax` (2,169 lines):
  - Exact port of `bootstrap/axiom0/src/lir/lower.c` (`lir_lower_mir_body`, `lir_lower_mir_file`), including:
    - Windows x64 calling convention ABI classification (`needs_indirect_by_size`, incoming/outgoing `abi_arg` and `abi_result` lowering for register, stack, and indirect-by-pointer aggregates, and `max_outgoing_args_bytes` shadow/outgoing stack frame sizing).
    - Place address resolution (`lower_place_addr`) across `MIR_PROJ_DEREF`, `MIR_PROJ_FIELD` (tuples, closures, structs, slices, and enum payload layout via `compiler.types.layout`), `MIR_PROJ_INDEX`, and `MIR_PROJ_DOWNCAST`.
    - Operand and constant evaluation (`lower_operand`, `eval_const_expr_to_addr`, `write_int_to_addr`) for scalars, string literals (`const_str`), arrays, repeats, tuples, structs, enums, slices, and function items (`fn_addr`).
    - All MIR statements (`MIR_STMT_ASSIGN`, `MIR_STMT_NOP`, `MIR_STMT_STORAGE_LIVE`, `MIR_STMT_STORAGE_DEAD`) and rvalues (`MIR_RVALUE_USE`, `MIR_RVALUE_REPEAT`, `MIR_RVALUE_REF`, `MIR_RVALUE_ADDRESS_OF`, `MIR_RVALUE_LEN`, `MIR_RVALUE_CAST` with `zext`/`sext`/`trunc`, `MIR_RVALUE_BINARY_OP`, `MIR_RVALUE_CHECKED_BINARY_OP` with `uadd_overflow`/`sadd_overflow`/`usub_overflow`/`ssub_overflow`/`umul_overflow`/`smul_overflow`, `MIR_RVALUE_NULLARY_OP`, `MIR_RVALUE_UNARY_OP`, `MIR_RVALUE_DISCRIMINANT`, `MIR_RVALUE_AGGREGATE`).
    - All MIR terminators (`MIR_TERM_GOTO`, `MIR_TERM_SWITCH_INT`, `MIR_TERM_RETURN`, `MIR_TERM_UNREACHABLE`, `MIR_TERM_DROP`, `MIR_TERM_CALL` including `@intrinsic` functions `size_of`, `align_of`, `wrapping_add_u64`, `wrapping_mul_u64`, `rotate_left_u64`, `copy_nonoverlapping`, `write_bytes`, `atomic_*`, `print_str`/`println_str`/`eprint_str`/`eprintln_str`/`panic_bounds_check` slice expansion, and indirect/closure calls, plus `MIR_TERM_ASSERT`).
- `compiler/lir/mod.ax` (87 lines):
  - Public module facade re-exporting the LIR data model, printer, and MIR-to-LIR lowering entrypoints.

### Tests (`tests/selfhost/lir/`)
- `tests/selfhost/lir/qa_lir_from_mir.ax`: Programmatic MIR-to-LIR unit test covering constants, checked arithmetic, bitwise/comparison ops, aggregate field projections, array indexing, casts, switches, assertions, and ABI call argument/result lowering.
- `tests/selfhost/lir/qa_lir_from_ax_{a,b,c,d,e}.ax`: End-to-end Axiom source -> Lex -> Parse -> Resolve -> HIR -> Typecheck/THIR -> MIR -> Drop Elaboration -> LIR lowering and `lir_print_body` byte-for-byte golden comparison against `axiom0 inspect --emit=lir` across 12 representative programs (`bitnot`, `calls`, `div_assert`, `first_mir`, `mul_assert`, `qa_eval_order`, `shift_assert`, `short_circuit`, `unary_neg_assert`, and rich multi-function suites covering structs, enums, arrays, slices, casts, function pointers, and builtins).

## Files changed
- compiler/lir/builder.ax
- compiler/lir/lir.ax
- compiler/lir/mod.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax

## Verification
- `python tools/archcheck.py --root .` (in `build-snap-T084a/`): Clean (`0` issues).
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/lir --verbose` (in `build-snap-T084a/`): `18/18 PASS` across `[interp]`, `[native]`, and `[native-O1]`.
- `python tools/axtest.py --compiler build/axiom0.exe` (in `build-snap-T084a/`): Full test suite passes (`0 FAIL`).

STATUS: COMPLETE round=0
