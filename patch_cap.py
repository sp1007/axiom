import re

with open('bootstrap/axiom0/src/own/cap/cap.c', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = r'''static void visit_operand\(CapState \*state, size_t local_count, const AxMirOperand \*op, AxLocation loc, AxDiagSink \*sink, bool report\) \{
    if \(op->kind == AX_MIR_OP_MOVE\) \{
        check_invalidate\(state, local_count, &op->place, loc, sink, report\);
    \}
\}'''

new_code = '''static void visit_operand(CapState *state, size_t local_count, const AxMirOperand *op, AxLocation loc, AxDiagSink *sink, bool report) {
    if (op->kind == AX_MIR_OP_MOVE) {
        check_invalidate(state, local_count, &op->place, loc, sink, report);
        if (op->place.proj_count == 0 && op->place.local.v < local_count) {
            state->caps[op->place.local.v].view = AX_MIR_VIEW_UNKNOWN;
        }
    }
}'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/own/cap/cap.c', 'w', encoding='utf-8') as f:
    f.write(code)
