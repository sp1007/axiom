with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add DropNode struct and update Builder/LoopContext
struct_decl = """
typedef struct DropNode {
    AxMirPlace place;
    AxLocation location;
    struct DropNode *next;
} DropNode;

typedef struct LoopContext {
    AxMirBbId break_bb;
    AxMirBbId continue_bb;
    AxMirPlace dest;
    StrId label;
    DropNode *drop_scope;
} LoopContext;
"""
import re
content = re.sub(r'typedef struct LoopContext \{.*?\} LoopContext;', struct_decl, content, flags=re.DOTALL)
content = content.replace('    size_t var_cap;\n} Builder;', '    size_t var_cap;\n    DropNode *current_drops;\n} Builder;')

# 2. Add `type_needs_drop` and `push_drop` and `build_drop_chain` AFTER `set_terminator`
new_helpers = """
static bool type_needs_drop(Builder *b, TypeId ty) {
    if (ty.v == 0) return false;
    const AxType *t = ax_type_get(&b->thir->interner, ty);
    if (t->kind == AX_TY_STRUCT || t->kind == AX_TY_ENUM || t->kind == AX_TY_TUPLE || t->kind == AX_TY_ARRAY || t->kind == AX_TY_SLICE) {
        return true;
    }
    return false;
}

static void push_drop(Builder *b, AxMirPlace place, TypeId ty) {
    if (type_needs_drop(b, ty)) {
        DropNode *node = ax_arena_alloc_array(b->arena, 1, sizeof(DropNode), _Alignof(DropNode));
        node->place = place;
        node->location = b->current_span;
        node->next = b->current_drops;
        b->current_drops = node;
    }
}

static AxMirBbId build_drop_chain(Builder *b, AxMirBbId current_bb, DropNode *from, DropNode *to, AxMirBbId target_bb, AxLocation loc) {
    DropNode *curr = from;
    while (curr != to) {
        AxMirBbId next_bb = add_bb(b);
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_DROP;
        term.location = loc;
        term.drop.place = curr->place;
        term.drop.target = next_bb;
        term.drop.unwind = (AxMirBbId){0};
        set_terminator(b, current_bb, term);
        current_bb = next_bb;
        curr = curr->next;
    }
    if (target_bb.v != 0) {
        AxMirTerminator term = {0};
        term.kind = AX_MIR_TERM_GOTO;
        term.goto_target = target_bb;
        term.location = loc;
        set_terminator(b, current_bb, term);
    }
    return current_bb;
}
"""
idx = content.find('static TypeId get_expr_type(Builder *b, const AxHirExpr *expr)')
content = content[:idx] + new_helpers + content[idx:]

# 3. Add push_drop inside add_local
old_add_local = """    b->locals[id.v].mut = mut;
    b->locals[id.v].location = b->current_span;
    return id;"""
new_add_local = """    b->locals[id.v].mut = mut;
    b->locals[id.v].location = b->current_span;
    if (kind != AX_MIR_LOCAL_RETURN) {
        AxMirPlace place = { id, NULL, 0, AX_MIR_REGION_UNKNOWN, AX_MIR_VIEW_UNKNOWN, 0 };
        push_drop(b, place, ty);
    }
    return id;"""
content = content.replace(old_add_local, new_add_local)

# 4. AX_HIR_EXPR_TRY returns from function
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

# 5. AX_JUMP_RETURN
ret_old = """            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_RETURN;
            set_terminator(b, b->current_bb, term);"""
ret_new = """            b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, NULL, (AxMirBbId){0}, b->current_span);
            AxMirTerminator term = {0};
            term.kind = AX_MIR_TERM_RETURN;
            set_terminator(b, b->current_bb, term);"""
content = content.replace(ret_old, ret_new)

# 6. END of function
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

# 7. break jump
break_old = """                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->break_bb;
                set_terminator(b, b->current_bb, term);"""
break_new = """                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->break_bb, b->current_span);"""
content = content.replace(break_old, break_new)

# 8. continue jump
continue_old = """                AxMirTerminator term = {0};
                term.kind = AX_MIR_TERM_GOTO;
                term.goto_target = target->continue_bb;
                set_terminator(b, b->current_bb, term);"""
continue_new = """                b->current_bb = build_drop_chain(b, b->current_bb, b->current_drops, target->drop_scope, target->continue_bb, b->current_span);"""
content = content.replace(continue_old, continue_new)

# 9. loops
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
