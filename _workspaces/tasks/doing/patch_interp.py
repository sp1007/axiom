import re

def main():
    path = r"D:\projects\compiler\new lang\bootstrap\axiom0\src\interp\interp.c"
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add AX_MIR_PROJ_INDEX to get_place_ptr
    proj_index_code = """        } else if (proj->kind == AX_MIR_PROJ_FIELD) {
            uint32_t offset = ax_type_field_offset(current_ty, proj->field_idx, &ctx->thir->interner);
            ptr += offset;
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            if (ty->kind == AX_TY_STRUCT) {
                current_ty = ty->strct.fields[proj->field_idx];
            } else if (ty->kind == AX_TY_TUPLE) {
                current_ty = ty->tuple.fields[proj->field_idx];
            }
        } else if (proj->kind == AX_MIR_PROJ_INDEX) {
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            if (ty->kind == AX_TY_ARRAY) {
                uint8_t *idx_ptr = (uint8_t*)&frame->locals[proj->index_local.v];
                TypeId idx_ty = frame->body->locals[proj->index_local.v].ty;
                uint32_t idx_size = ax_type_size(idx_ty, &ctx->thir->interner);
                uint64_t index = 0;
                if (idx_size == 4) index = *(uint32_t*)idx_ptr;
                else if (idx_size == 8) index = *(uint64_t*)idx_ptr;
                
                if (index >= ty->array.len) {
                    fprintf(stderr, "panic: index out of bounds: the len is %llu but the index is %llu\\n", (unsigned long long)ty->array.len, (unsigned long long)index);
                    exit(101); // Standard Rust abort code for panics
                }
                
                uint32_t elem_size = ax_type_size(ty->array.elem, &ctx->thir->interner);
                ptr += index * elem_size;
                current_ty = ty->array.elem;
            }
        }"""
    
    content = re.sub(r'\} else if \(proj->kind == AX_MIR_PROJ_FIELD\) \{.*?\} else if \(ty->kind == AX_TY_TUPLE\) \{\s*current_ty = ty->tuple.fields\[proj->field_idx\];\s*\}\s*\}', proj_index_code, content, flags=re.DOTALL)

    # 2. Update AX_MIR_RVALUE_AGGREGATE for array and add AX_MIR_RVALUE_REPEAT and AX_MIR_RVALUE_LEN
    agg_code = """                    case AX_MIR_RVALUE_AGGREGATE: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty);
                        const AxType *ty = ax_type_get(&ctx->thir->interner, dest_ty);
                        for (size_t i = 0; i < stmt->assign.rvalue.aggregate.operand_count; i++) {
                            uint32_t offset = 0;
                            TypeId field_ty;
                            if (ty->kind == AX_TY_ARRAY) {
                                field_ty = ty->array.elem;
                                offset = i * ax_type_size(field_ty, &ctx->thir->interner);
                            } else {
                                offset = ax_type_field_offset(dest_ty, i, &ctx->thir->interner);
                                field_ty = (ty->kind == AX_TY_STRUCT) ? ty->strct.fields[i] : ty->tuple.fields[i];
                            }
                            uint32_t f_size = ax_type_size(field_ty, &ctx->thir->interner);
                            
                            AxMirOperand *f_op = &stmt->assign.rvalue.aggregate.operands[i];
                            if (f_op->kind == AX_MIR_OP_CONST) {
                                uint64_t val = f_op->constant.val;
                                if (f_size == 1) *(uint8_t*)(dest + offset) = (uint8_t)val;
                                else if (f_size == 2) *(uint16_t*)(dest + offset) = (uint16_t)val;
                                else if (f_size == 4) *(uint32_t*)(dest + offset) = (uint32_t)val;
                                else if (f_size == 8) *(uint64_t*)(dest + offset) = val;
                            } else {
                                TypeId s_ty;
                                uint8_t *src = get_place_ptr(ctx, &frame, &f_op->place, &s_ty);
                                memcpy(dest + offset, src, f_size);
                            }
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_REPEAT: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty);
                        const AxType *ty = ax_type_get(&ctx->thir->interner, dest_ty);
                        
                        TypeId elem_ty = ty->array.elem;
                        uint32_t f_size = ax_type_size(elem_ty, &ctx->thir->interner);
                        
                        uint64_t count_val = 0;
                        if (stmt->assign.rvalue.repeat.count.kind == AX_MIR_OP_CONST) {
                            count_val = stmt->assign.rvalue.repeat.count.constant.val;
                        } else {
                            TypeId dummy;
                            uint8_t *c_ptr = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.repeat.count.place, &dummy);
                            count_val = *(uint64_t*)c_ptr; // assuming usize or u32/u64
                        }
                        
                        AxMirOperand *val_op = &stmt->assign.rvalue.repeat.op;
                        for (uint64_t i = 0; i < count_val; i++) {
                            uint32_t offset = i * f_size;
                            if (val_op->kind == AX_MIR_OP_CONST) {
                                uint64_t val = val_op->constant.val;
                                if (f_size == 1) *(uint8_t*)(dest + offset) = (uint8_t)val;
                                else if (f_size == 2) *(uint16_t*)(dest + offset) = (uint16_t)val;
                                else if (f_size == 4) *(uint32_t*)(dest + offset) = (uint32_t)val;
                                else if (f_size == 8) *(uint64_t*)(dest + offset) = val;
                            } else {
                                TypeId s_ty;
                                uint8_t *src = get_place_ptr(ctx, &frame, &val_op->place, &s_ty);
                                memcpy(dest + offset, src, f_size);
                            }
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_LEN: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty);
                        
                        TypeId arg_ty;
                        get_place_ptr(ctx, &frame, &stmt->assign.rvalue.len, &arg_ty);
                        const AxType *t = ax_type_get(&ctx->thir->interner, arg_ty);
                        
                        uint64_t len = 0;
                        if (t->kind == AX_TY_ARRAY) {
                            len = t->array.len;
                        } else {
                            len = 0; // ICE
                        }
                        
                        uint32_t d_size = ax_type_size(dest_ty, &ctx->thir->interner);
                        if (d_size == 4) *(uint32_t*)dest = (uint32_t)len;
                        else if (d_size == 8) *(uint64_t*)dest = len;
                        goto skip_write;
                    }"""

    content = re.sub(r'case AX_MIR_RVALUE_AGGREGATE: \{.*?goto skip_write;\s*\}', agg_code, content, flags=re.DOTALL)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    main()
