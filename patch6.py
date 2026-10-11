with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the old ones
old_helpers = """static bool type_needs_drop(Builder *b, TypeId ty) {
    if (ty.v == 0) return false;
    const AxType *t = ax_type_get(&b->thir->interner, ty);
    switch (t->kind) {
        case AX_TY_STRUCT:
        case AX_TY_ENUM:
        case AX_TY_TUPLE:
        case AX_TY_ARRAY:
        case AX_TY_SLICE:
            return true;
        default:
            return false;
    }
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
    AxMirTerminator term = {0};
    term.kind = AX_MIR_TERM_GOTO;
    term.goto_target = target_bb;
    term.location = loc;
    set_terminator(b, current_bb, term);
    return current_bb;
}

"""
content = content.replace(old_helpers, '')

# 2. Add them after `set_terminator`
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

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
