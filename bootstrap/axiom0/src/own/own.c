#include "own/own.h"

bool ax_type_is_copy(TypeId id, const AxThir *thir, const StrInterner *str_in) {
    if (id.v == 0) return false;
    const AxType *ty = ax_type_get(&thir->interner, id);
    if (!ty) return false;
    
    switch ((int)ty->kind) {
        case AX_TY_ERROR: return false;
        case AX_TY_UNIT:
        case AX_TY_NEVER:
        case AX_TY_BOOL:
        case AX_TY_CHAR:
        case AX_TY_I8: case AX_TY_I16: case AX_TY_I32: case AX_TY_I64: case AX_TY_ISIZE:
        case AX_TY_U8: case AX_TY_U16: case AX_TY_U32: case AX_TY_U64: case AX_TY_USIZE:
        case AX_TY_PTR:
        case AX_TY_FN:
        case AX_TY_INT_VAR:
            return true;
        case AX_TY_STR:
            return false;
        case AX_TY_ARRAY:
            return ax_type_is_copy(ty->array.elem, thir, str_in);
        case AX_TY_TUPLE:
            for (size_t i = 0; i < ty->tuple.field_count; i++) {
                if (!ax_type_is_copy(ty->tuple.fields[i], thir, str_in)) return false;
            }
            return true;
        case AX_TY_STRUCT:
        case AX_TY_ENUM: {
            const AxHirItem *def = (ty->kind == AX_TY_STRUCT) ? ty->strct.def : ty->enm.def;
            if (!def) return false;
            for (const AxHirAttr *attr = def->attrs; attr; attr = attr->next) {
                StrView attr_name = ax_interner_get(str_in, attr->name);
                if (attr_name.len == 6 && memcmp(attr_name.ptr, "derive", 6) == 0) {
                    for (const AxHirAttrArg *arg = attr->args; arg; arg = arg->next) {
                        StrView arg_name = ax_interner_get(str_in, arg->name);
                        if (arg_name.len == 4 && memcmp(arg_name.ptr, "Copy", 4) == 0) {
                            return true;
                        }
                    }
                }
            }
            return false;
        }
        default: return false;
    }
}
