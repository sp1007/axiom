## Scope to Test Mapping
- if as expression (branch type unification): `tests/run/cfg/if_expr.ax`, `tests/ui/cfg/if_expr_err.ax`, `tests/ui/cfg/qa_if_expr_type_mismatch.ax`
- block values: `tests/run/cfg/block_val.ax`, `tests/ui/cfg/block_val_err.ax`
- loop with `break value`: `tests/run/cfg/loop_break.ax`, `tests/ui/cfg/loop_break_err.ax`, `tests/ui/cfg/qa_break_type_mismatch.ax`, `tests/ui/cfg/qa_loop_break_no_value.ax`
- continue: `tests/run/cfg/continue.ax`, `tests/ui/cfg/continue_err.ax`
- labelled loops (`break`/`continue` to a label): `tests/run/cfg/labeled_loop.ax`, `tests/ui/cfg/labeled_loop_err.ax`
- `never` type from return/break/panic: `tests/run/cfg/never_type.ax`, `tests/ui/cfg/qa_never_coercion_err.ax`
- unreachable code warnings: `tests/ui/cfg/unreachable.ax`

## Files changed
- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/types/typeck.c
- tests/run/cfg/block_val.ax
- tests/run/cfg/continue.ax
- tests/run/cfg/if_expr.ax
- tests/run/cfg/labeled_loop.ax
- tests/run/cfg/loop_break.ax
- tests/run/cfg/never_type.ax
- tests/typeck/basic.thir
- tests/ui/cfg/block_val_err.ax
- tests/ui/cfg/continue_err.ax
- tests/ui/cfg/if_expr_err.ax
- tests/ui/cfg/labeled_loop_err.ax
- tests/ui/cfg/loop_break_err.ax
- tests/ui/cfg/qa_break_type_mismatch.ax
- tests/ui/cfg/qa_if_expr_type_mismatch.ax
- tests/ui/cfg/qa_loop_break_no_value.ax
- tests/ui/cfg/qa_never_coercion_err.ax
- tests/ui/cfg/unreachable.ax

STATUS: COMPLETE round=2
