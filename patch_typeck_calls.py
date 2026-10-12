import re

with open("bootstrap/axiom0/src/types/typeck.c", "r") as f:
    text = f.read()

# Fix old calls
text = text.replace("lookup_path_type(cx, &pat->struct_pat.path)", "lookup_path_type(cx, &pat->struct_pat.path, NULL)")
text = text.replace("lookup_path_type(cx, &pat->path.path)", "lookup_path_type(cx, &pat->path.path, NULL)")
text = text.replace("lookup_path_type(cx, &expr->call.callee->path.path)", "lookup_path_type(cx, &expr->call.callee->path.path, NULL)")
text = text.replace("lookup_path_type(cx, &expr->struct_lit.path)", "lookup_path_type(cx, &expr->struct_lit.path, NULL)")

# But wait, I want to capture `gargs` for `pat->struct_pat`, `pat->path`, `expr->struct_lit`.
# Let's replace the whole block for each to capture and insert to `substs` maps.

# 1. pat->struct_pat
pat_struct = """
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &pat->struct_pat.path, &gargs);
            if (gargs.count > 0) {
                AxPatSubstMap_insert(&cx->thir->pat_substs, pat, gargs);
            }
"""
text = re.sub(r"TypeId path_ty = lookup_path_type\(cx, &pat->struct_pat\.path, NULL\);", pat_struct.strip(), text)

# 2. pat->path
pat_path = """
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &pat->path.path, &gargs);
            if (gargs.count > 0) {
                AxPatSubstMap_insert(&cx->thir->pat_substs, pat, gargs);
            }
"""
text = re.sub(r"TypeId path_ty = lookup_path_type\(cx, &pat->path\.path, NULL\);", pat_path.strip(), text)

# 3. expr->struct_lit
expr_struct = """
            AxGenericArgs gargs = {0};
            TypeId path_ty = lookup_path_type(cx, &expr->struct_lit.path, &gargs);
            if (gargs.count > 0) {
                AxExprSubstMap_insert(&cx->thir->expr_substs, expr, gargs);
            }
"""
text = re.sub(r"TypeId path_ty = lookup_path_type\(cx, &expr->struct_lit\.path, NULL\);", expr_struct.strip(), text)

# What about `expr->call.callee->path`? The call itself doesn't have a path, the callee does. The `gargs` should probably be stored on the callee? The replacement I did earlier for `expr->path.path` already covers `AX_HIR_EXPR_PATH`, which `callee` is. So when `check_expr(cx, expr->call.callee, ...)` runs, it will process the `AX_HIR_EXPR_PATH` and populate `expr_substs`. Wait, `lookup_path_type(cx, &expr->call.callee->path.path)` inside `check_expr_kind`'s `AX_HIR_EXPR_CALL` is just doing `resolve_ty` to peek at the type! We should just pass `NULL` there.

with open("bootstrap/axiom0/src/types/typeck.c", "w") as f:
    f.write(text)
