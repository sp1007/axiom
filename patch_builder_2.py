import re

with open('bootstrap/axiom0/src/mir/build/builder.c', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace my old patch (I need to find it and replace it)
old_code = r'''        callee\.constant\.ty = \*AxItemTypeMap_get\(&b->thir->item_types, method_item\);
        
        bool has_self = \(method_item->fn\.params && ax_sv_eq_cstr\(ax_interner_get\(b->str_in, method_item->fn\.params->name\), "self"\)\);
        
        size_t arg_count = has_self \? 1 : 0;
        for \(const AxHirExpr \*arg = expr->method_call\.args; arg; arg = arg->next\) arg_count\+\+;
        
        AxMirOperand \*args = NULL;
        if \(arg_count > 0\) \{
            args = ax_arena_alloc\(b->arena, sizeof\(AxMirOperand\) \* arg_count, _Alignof\(AxMirOperand\)\);
            size_t i = 0;
            if \(has_self\) \{'''

new_code = '''        callee.constant.ty = *AxItemTypeMap_get(&b->thir->item_types, method_item);
        
        size_t explicit_args = 0;
        for (const AxHirExpr *arg = expr->method_call.args; arg; arg = arg->next) explicit_args++;
        
        const AxType *fn_ty = ax_type_get(&b->thir->interner, callee.constant.ty);
        bool has_self = (explicit_args + 1 == fn_ty->fn.param_count);
        
        size_t arg_count = explicit_args + (has_self ? 1 : 0);
        AxMirOperand *args = NULL;
        if (arg_count > 0) {
            args = ax_arena_alloc(b->arena, sizeof(AxMirOperand) * arg_count, _Alignof(AxMirOperand));
            size_t i = 0;
            if (has_self) {'''

code = re.sub(old_code, new_code, code)

with open('bootstrap/axiom0/src/mir/build/builder.c', 'w', encoding='utf-8') as f:
    f.write(code)
