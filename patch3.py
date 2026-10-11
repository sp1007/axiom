with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. AX_HIR_EXPR_TRY returns from function!
try_old = """        AxMirTerminator ret_term = {0};
        ret_term.kind = AX_MIR_TERM_RETURN;
        ret_term.region = AX_MIR_REGION_UNKNOWN;
        ret_term.view = AX_MIR_VIEW_UNKNOWN;
        ret_term.drop_flag = 0;
        set_terminator(b, b->current_bb, ret_term);"""
try_new = """        b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, NULL, (AxMirBbId){0}, b->current_span);
        AxMirTerminator ret_term = {0};
        ret_term.kind = AX_MIR_TERM_RETURN;
        ret_term.region = AX_MIR_REGION_UNKNOWN;
        ret_term.view = AX_MIR_VIEW_UNKNOWN;
        ret_term.drop_flag = 0;
        set_terminator(b, b->current_bb, ret_term);"""
content = content.replace(try_old, try_new)

# 2. AX_JUMP_RETURN
ret_old = """            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_RETURN;
            set_terminator(b, b->current_bb, term);"""
ret_new = """            b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, NULL, (AxMirBbId){0}, b->current_span);
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_RETURN;
            set_terminator(b, b->current_bb, term);"""
content = content.replace(ret_old, ret_new)

# 3. END of function
end_old = """    if (!b.bbs[b.current_bb.v].is_terminated) {
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_RETURN;
        set_terminator(&b, b.current_bb, term);
    }"""
end_new = """    if (!b.bbs[b.current_bb.v].is_terminated) {
        b.current_bb = build_drop_chain(&b, b.current_bb, b.current_drops, NULL, (AxMirBbId){0}, b.current_span);
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_RETURN;
        set_terminator(&b, b.current_bb, term);
    }"""
content = content.replace(end_old, end_new)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
