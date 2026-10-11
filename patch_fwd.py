with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    content = f.read()

forward_decls = """static void push_drop(Builder *b, AxMirPlace place, TypeId ty);
static bool type_needs_drop(Builder *b, TypeId ty);
static AxMirBbId build_drop_chain(Builder *b, AxMirBbId current_bb, DropNode *from, DropNode *to, AxMirBbId target_bb, AxLocation loc);
"""

content = content.replace("static AxMirBbId build_pat_match_inner(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail);", forward_decls + "static AxMirBbId build_pat_match_inner(Builder *b, AxMirBbId current_bb, AxMirPlace place, const AxHirPat *pat, AxMirBbId bb_fail);")

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(content)
