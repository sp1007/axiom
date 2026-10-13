#include "driver/driver.h"
#include "hir/hir.h"
#include "mir/mir.h"
#include "mir/build/build.h"
#include "lir/lir.h"
#include "abi/abi.h"
#include "target/x64/isel/isel.h"
#include "target/x64/frame/frame.h"
#include "target/x64/verify/verify.h"
#include "target/x64/encode/encode.h"
#include "objmodel/objmodel.h"
#include "obj/coff/writer.h"
#include "link/pe/linker.h"
#include "driver/mono.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern const char *ax_opt_build_o;
extern const char *ax_opt_emit;
extern const char *ax_opt_stack_reserve;

static void encode_mi_to_sec(ax_section_t *sec, const AxX64MI *inst, const AxX64FrameLayout *layout, ax_objmodel_t *obj) {
    switch (inst->opcode) {
        case AX_X64_MI_MOV: {
            uint8_t sz = inst->sz ? inst->sz : 8;
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_mov_rr(sec, sz, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_mov_rm(sec, sz, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_mov_mr(sec, sz, inst->ops[0].mem, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_mov_ri(sec, sz, inst->ops[0].reg, inst->ops[1].imm);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_mov_mi(sec, sz, inst->ops[0].mem, (int32_t)inst->ops[1].imm);
            }
            break;
        }
        
        case AX_X64_MI_CMP: {
            uint8_t sz = inst->sz ? inst->sz : 8;
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_cmp_rr(sec, sz, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_cmp_rm(sec, sz, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_cmp_ri(sec, sz, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        }
        case AX_X64_MI_JMP:
            if (inst->ops[0].kind == AX_X64_OP_IMM) {
                ax_x64_jmp(sec, (int32_t)inst->ops[0].imm);
            }
            break;
        case AX_X64_MI_JCC:
            if (inst->ops[0].kind == AX_X64_OP_IMM && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_jcc(sec, (uint8_t)inst->ops[0].imm, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_SETCC:
            if (inst->ops[0].kind == AX_X64_OP_IMM && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_setcc_r(sec, (uint8_t)inst->ops[0].imm, inst->ops[1].reg);
            }
            break;
        case AX_X64_MI_AND:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_and_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_and_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_and_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_OR:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_or_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_or_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_or_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_XOR:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_xor_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_xor_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_xor_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_SHL:
            if (inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_shl_ri(sec, 8, inst->ops[0].reg, (int8_t)inst->ops[1].imm);
            } else if (inst->ops[1].kind == AX_X64_OP_REG && inst->ops[1].reg == AX_REG_RCX) {
                ax_x64_shl_rcl(sec, 8, inst->ops[0].reg);
            }
            break;
        case AX_X64_MI_SHR:
            if (inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_shr_ri(sec, 8, inst->ops[0].reg, (int8_t)inst->ops[1].imm);
            } else if (inst->ops[1].kind == AX_X64_OP_REG && inst->ops[1].reg == AX_REG_RCX) {
                ax_x64_shr_rcl(sec, 8, inst->ops[0].reg);
            }
            break;
        case AX_X64_MI_ADD:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_add_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_add_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_add_mr(sec, 8, inst->ops[0].mem, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_add_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_SUB:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_sub_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_sub_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_sub_mr(sec, 8, inst->ops[0].mem, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_sub_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_IMUL:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_imul_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_imul_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            }
            break;
        case AX_X64_MI_SAR:
            if (inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_sar_ri(sec, 8, inst->ops[0].reg, inst->ops[1].imm);
            } else if (inst->ops[1].kind == AX_X64_OP_REG && inst->ops[1].reg == AX_REG_RCX) {
                ax_x64_sar_rcl(sec, 8, inst->ops[0].reg);
            }
            break;
        case AX_X64_MI_IDIV:
            if (inst->ops[0].kind == AX_X64_OP_REG) {
                ax_x64_idiv_r(sec, 8, inst->ops[0].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM) {
                ax_x64_idiv_m(sec, 8, inst->ops[0].mem);
            }
            break;
        case AX_X64_MI_LEA:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_lea(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            }
            break;
        case AX_X64_MI_RET:
            ax_x64_frame_emit_epilogue(sec, layout);
            ax_x64_ret(sec);
            break;
        default:
            break;

        case AX_X64_MI_CALL:
            if (inst->msg) {
                ax_section_add_bytes(sec, (const uint8_t[]){0xE8, 0, 0, 0, 0}, 5);
                ax_section_add_reloc(sec, sec->bytes_len - 4, AX_RELOC_X86_64_PC32, ax_objmodel_add_symbol(obj, inst->msg, (ax_section_id_t){0}, 0, 0, AX_SYM_EXTERNAL), -4);
            } else if (inst->op_count > 0 && inst->ops[0].kind == AX_X64_OP_REG) {
                ax_x64_call_r(sec, inst->ops[0].reg);
            }
            break;
    }
}

void ax_stage_build_native(AxDriverState *st) {
    if (st->sink.errors > 0) {
        st->failed = true;
        return;
    }

    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    ax_section_id_t my_rdata_sec_id = ax_objmodel_add_section(&obj, ".rdata", AX_SEC_RODATA, AX_SEC_FLAG_READ, 16);
    ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);

    for (const AxMonoInstance *inst = st->mono_instances; inst != NULL; inst = inst->next) { const AxHirItem *item = inst->item;
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = inst->body;
            if (mir_body) {
                const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);
                TypeId ty_id = pty ? *pty : (TypeId){0};
                if (ty_id.v != 0) {
                    const AxType *item_ty = ax_type_get(&st->thir.interner, ty_id);
                    if (item_ty && item_ty->kind == AX_TY_CLOSURE && item_ty->closure.fn_type.v != 0) {
                        ty_id = item_ty->closure.fn_type;
                    }
                }
                if (ty_id.v == 0) {
                    size_t arg_count = 0;
                    for (size_t i = 1; i < mir_body->local_count; i++) {
                        if (mir_body->locals[i].kind == AX_MIR_LOCAL_ARG) arg_count++;
                        else break;
                    }
                    TypeId *param_types = malloc((arg_count ? arg_count : 1) * sizeof(TypeId));
                    for (size_t i = 0; i < arg_count; i++) {
                        param_types[i] = mir_body->locals[i + 1].ty;
                    }
                    AxType dummy;
                    memset(&dummy, 0, sizeof(dummy));
                    dummy.kind = AX_TY_FN;
                    dummy.fn.ret_type = mir_body->locals[0].ty;
                    dummy.fn.param_count = arg_count;
                    dummy.fn.param_types = param_types;
                    ty_id = ax_intern_type(&st->thir.interner, &dummy);
                }
                const AxType *fn_ty = ax_type_get(&st->thir.interner, ty_id);
                AxLirBody *lir_body = ax_lir_lower(mir_body, &st->hir, &st->thir.interner, &st->interner, fn_ty);
                if (lir_body) {
                    ax_lir_lower_abi(lir_body, &st->thir.interner, &ax_abi_win64, fn_ty);

                    AxX64MIBody *mi_body = ax_x64_isel(lir_body, &st->thir.interner);
                    AxX64FrameLayout layout = ax_x64_frame_lower(mi_body, lir_body, &st->thir.interner, &st->hir_arena);

    ax_section_t *rdata_sec = ax_objmodel_get_section(&obj, my_rdata_sec_id);
    for (size_t i = 0; i < mi_body->string_count; i++) {
        AxX64MIStr *str = &mi_body->strings[i];
        uint32_t offset = rdata_sec->bytes_len;
        ax_section_add_bytes(rdata_sec, str->bytes, str->len);
        ax_section_add_byte(rdata_sec, 0); // null terminator for good measure
        
        char sym_name[64];
        snprintf(sym_name, sizeof(sym_name), ".Lstr.%zx.%u", (size_t)mi_body, str->sym_id);
        ax_objmodel_add_symbol(&obj, strdup(sym_name), my_rdata_sec_id, offset, str->len, AX_SYM_GLOBAL);
    }
                    ax_x64_verify(mi_body, &layout);

                    uint64_t func_start = text_sec->bytes_len;

                    // Align function start
                    while (text_sec->bytes_len % 16 != 0) {
                        ax_section_add_byte(text_sec, 0x90); // nop
                    }
                    func_start = text_sec->bytes_len;

                    char name_buf[256];
                    if (inst->mangled_name.v != 0) {
                        StrView name = ax_interner_get(&st->interner, inst->mangled_name);
                        snprintf(name_buf, 256, "%.*s", (int)name.len, name.ptr);
                    } else {
                        snprintf(name_buf, 256, "__ax_fn_%u", (uint32_t)item->fn.symbol.v);
                    }


                    ax_x64_frame_emit_prologue(text_sec, &layout);

                    uint32_t bb_offsets[1024] = {0};
                    struct { uint32_t fixup; uint32_t target; } fixups[1024];
                    uint32_t num_fixups = 0;

                    for (size_t b = 0; b < mi_body->bb_count; b++) {
                        bb_offsets[b] = text_sec->bytes_len;
                        AxX64MIBb *mbb = &mi_body->bbs[b];
                        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
                            if (inst->opcode == AX_X64_MI_JMP) {
                                fixups[num_fixups].fixup = text_sec->bytes_len + 1;
                                fixups[num_fixups].target = inst->ops[0].imm;
                                num_fixups++;
                                ax_x64_jmp(text_sec, 0);
                            } else if (inst->opcode == AX_X64_MI_JCC) {
                                fixups[num_fixups].fixup = text_sec->bytes_len + 2;
                                fixups[num_fixups].target = inst->ops[1].imm;
                                num_fixups++;
                                ax_x64_jcc(text_sec, (uint8_t)inst->ops[0].imm, 0);

                            } else if (inst->opcode == AX_X64_MI_LEA && inst->ops[1].kind == AX_X64_OP_SYM) {
                                if (inst->msg) {
                                    ax_symbol_id_t fn_sym = ax_objmodel_add_symbol(&obj, inst->msg, ax_section_id_t_none(), 0, 0, AX_SYM_EXTERNAL);
                                    ax_x64_lea_sym(text_sec, inst->ops[0].reg, fn_sym);
                                } else {
                                    char sym_name[64];
                                    snprintf(sym_name, sizeof(sym_name), ".Lstr.%zx.%u", (size_t)mi_body, inst->ops[1].sym);
                                    ax_symbol_id_t str_sym = ax_objmodel_add_symbol(&obj, strdup(sym_name), ax_section_id_t_none(), 0, 0, AX_SYM_EXTERNAL);
                                    ax_x64_lea_sym(text_sec, inst->ops[0].reg, str_sym);
                                }
                            } else if (inst->opcode == AX_X64_MI_ASSERT) {
                                fixups[num_fixups].fixup = text_sec->bytes_len + 2;
                                fixups[num_fixups].target = inst->ops[0].imm;
                                num_fixups++;
                                ax_x64_jcc(text_sec, 0x4, 0); // JE over panic block
                                text_sec = ax_objmodel_get_section(&obj, text_sec_id); // Refresh text_sec pointer
                                ax_section_t *rdata_sec = ax_objmodel_get_section(&obj, my_rdata_sec_id);
                                uint32_t str_offset = rdata_sec->bytes_len;
                                const char *msg = inst->msg ? inst->msg : "assertion failed";
                                char formatted_msg[256];
                                snprintf(formatted_msg, sizeof(formatted_msg), "panic: %s\n", msg);
                                uint32_t len = strlen(formatted_msg);
                                ax_section_add_bytes(rdata_sec, (const uint8_t*)formatted_msg, len);
                                ax_section_add_byte(rdata_sec, 0);
                                
                                static int panic_id = 0;
                                char panic_sym_name[64];
                                snprintf(panic_sym_name, sizeof(panic_sym_name), ".Lpanic_%d", panic_id++);
                                ax_symbol_id_t str_sym = ax_objmodel_add_symbol(&obj, strdup(panic_sym_name), my_rdata_sec_id, str_offset, len + 1, AX_SYM_GLOBAL);
                                
                                ax_section_add_byte(text_sec, 0x48); ax_section_add_byte(text_sec, 0x83); ax_section_add_byte(text_sec, 0xEC); ax_section_add_byte(text_sec, 0x20); // sub rsp, 32
                                ax_section_add_byte(text_sec, 0x48); ax_section_add_byte(text_sec, 0x8D); ax_section_add_byte(text_sec, 0x0D);
                                ax_section_add_reloc(text_sec, text_sec->bytes_len, AX_RELOC_X86_64_PC32, str_sym, -4);
                                ax_section_add_bytes(text_sec, (const uint8_t[]){0, 0, 0, 0}, 4);
                                ax_section_add_byte(text_sec, 0x48); ax_section_add_byte(text_sec, 0xC7); ax_section_add_byte(text_sec, 0xC2);
                                ax_section_add_bytes(text_sec, (const uint8_t[]){len & 0xFF, (len >> 8) & 0xFF, (len >> 16) & 0xFF, (len >> 24) & 0xFF}, 4);
                                ax_section_add_bytes(text_sec, (const uint8_t[]){0xE8, 0, 0, 0, 0}, 5);
                                ax_section_add_reloc(text_sec, text_sec->bytes_len - 4, AX_RELOC_X86_64_PC32, ax_objmodel_add_symbol(&obj, "axiom_panic", ax_section_id_t_none(), 0, 0, AX_SYM_EXTERNAL), -4);
                            } else {
                                encode_mi_to_sec(text_sec, inst, &layout, &obj);
                            }
                        }
                    }

                    for (size_t i = 0; i < num_fixups; i++) {
                        uint32_t target_off = bb_offsets[fixups[i].target];
                        uint32_t next_rip = fixups[i].fixup + 4;
                        int32_t rel32 = (int32_t)target_off - (int32_t)next_rip;
                        memcpy(text_sec->bytes + fixups[i].fixup, &rel32, 4);
                    }

                    uint64_t func_size = text_sec->bytes_len - func_start;
                    ax_objmodel_add_symbol(&obj, strdup(name_buf), text_sec_id, func_start, func_size, AX_SYM_GLOBAL);
                    if (strcmp(name_buf, "main") == 0) { ax_objmodel_add_symbol(&obj, strdup("ax_main"), text_sec_id, func_start, func_size, AX_SYM_GLOBAL); }
                }
            }
        }
    }

    if (ax_opt_build_o == NULL) {
        st->failed = true;
        ax_objmodel_free(&obj);
        return;
    }


    ax_section_t *rdata_sec2 = ax_objmodel_get_section(&obj, my_rdata_sec_id);
    if (rdata_sec2->bytes_len == 0) {
        ax_section_add_byte(rdata_sec2, 0);
    }

    if (ax_opt_emit != NULL && strcmp(ax_opt_emit, "obj") == 0) {
        if (!ax_coff_write(&obj, ax_opt_build_o)) {
            st->failed = true;
        }
        ax_objmodel_free(&obj);
        return;
    }

    // Default: write a temporary object file and link it.
    char obj_path[1024];
    snprintf(obj_path, sizeof(obj_path), "%s.obj", ax_opt_build_o);
    
    if (!ax_coff_write(&obj, obj_path)) {
        st->failed = true;
        ax_objmodel_free(&obj);
        return;
    }
    
    ax_objmodel_free(&obj);

    uint32_t stack_res = 1048576;
    if (ax_opt_stack_reserve) {
        stack_res = (uint32_t)strtoul(ax_opt_stack_reserve, NULL, 10);
    }

    const char *inputs[] = { obj_path };
    if (!ax_pe_link(inputs, 1, ax_opt_build_o, stack_res, &st->sink)) {
        st->failed = true;
    }

    // We can clean up the object file if it's temporary, but it's optional.
    // For now we'll just leave it or remove it.
    remove(obj_path);
}


