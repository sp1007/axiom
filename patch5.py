with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

loop_old1 = """        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = loop_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->loop.label;"""
loop_new1 = """        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = loop_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->loop.label;
        b->loops[b->loop_count].drop_scope = b->current_drops;"""
content = content.replace(loop_old1, loop_new1)

loop_old2 = """        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = cond_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->while_expr.label;"""
loop_new2 = """        b->loops[b->loop_count].break_bb = exit_bb;
        b->loops[b->loop_count].continue_bb = cond_bb;
        b->loops[b->loop_count].dest = dest;
        b->loops[b->loop_count].label = expr->while_expr.label;
        b->loops[b->loop_count].drop_scope = b->current_drops;"""
content = content.replace(loop_old2, loop_new2)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
