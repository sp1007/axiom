import re

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
content = re.sub(r'typedef struct LoopContext \{.*?\} LoopContext;', struct_decl, content, flags=re.DOTALL)

content = content.replace('    size_t var_cap;\n} Builder;', '    size_t var_cap;\n    DropNode *current_drops;\n} Builder;')

# 2. Add `type_needs_drop` and `push_drop` and `build_drop_chain` before `add_local`
add_local_idx = content.find('static AxMirLocalId add_local(')
if add_local_idx != -1:
    helpers = """
static bool type_needs_drop(Builder *b, TypeId ty) {
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
    content = content[:add_local_idx] + helpers + content[add_local_idx:]

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
