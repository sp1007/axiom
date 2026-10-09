import re

def main():
    path = r"D:\projects\compiler\new lang\bootstrap\axiom0\src\mir\build\builder.c"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Forward declare build_expr_as_operand
    if "static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr);" not in content:
        content = content.replace("static AxMirPlace build_place(Builder *b, const AxHirExpr *expr) {", 
                                  "static AxMirOperand build_expr_as_operand(Builder *b, const AxHirExpr *expr);\nstatic AxMirPlace build_place(Builder *b, const AxHirExpr *expr) {")

    # 2. Fix b->db issue
    bad_str = "StrView callee_name = ax_source_db_span_text(b->db, expr->call.callee->span);"
    if bad_str in content:
        fix = """            TypeId callee_ty = get_expr_type(b, expr->call.callee);
            if (TypeId_is_none(callee_ty) || ax_type_get(&b->thir->interner, callee_ty)->kind == AX_TY_ERROR) {"""
        content = content.replace("StrView callee_name = ax_source_db_span_text(b->db, expr->call.callee->span);\n            if (ax_sv_eq_cstr(callee_name, \"len\")) {", fix)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
