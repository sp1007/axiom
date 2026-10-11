with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

# break jump
break_old = """                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->break_bb;
                set_terminator(b, b->current_bb, term);"""
break_new = """                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->break_bb, b->current_span);"""
content = content.replace(break_old, break_new)

# continue jump
continue_old = """                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->continue_bb;
                set_terminator(b, b->current_bb, term);"""
continue_new = """                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->continue_bb, b->current_span);"""
content = content.replace(continue_old, continue_new)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
