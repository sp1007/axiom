import re

with open('bootstrap/axiom0/src/types/typeck.c', 'r', encoding='utf-8') as f:
    code = f.read()

old_code = r'''            size_t expected_args = fn_ty->fn\.param_count;
            size_t argc = 1; // \+1 for receiver
            for \(const AxHirExpr \*a = expr->method_call\.args; a; a = a->next\) argc\+\+;'''

new_code = '''            size_t expected_args = fn_ty->fn.param_count;
            bool has_self = (method_item->fn.params && ax_sv_eq_cstr(ax_interner_get(cx->str_in, method_item->fn.params->name), "self"));
            size_t argc = has_self ? 1 : 0;
            for (const AxHirExpr *a = expr->method_call.args; a; a = a->next) argc++;'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/types/typeck.c', 'w', encoding='utf-8') as f:
    f.write(code)
