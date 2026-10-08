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
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void encode_mi_to_sec(ax_section_t *sec, const AxX64MI *inst, const AxX64FrameLayout *layout) {
    switch (inst->opcode) {
        case AX_X64_MI_MOV:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_mov_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_mov_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_mov_mr(sec, 8, inst->ops[0].mem, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_mov_ri(sec, 8, inst->ops[0].reg, inst->ops[1].imm);
            } else if (inst->ops[0].kind == AX_X64_OP_MEM && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_mov_mi(sec, 8, inst->ops[0].mem, (int32_t)inst->ops[1].imm);
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
    }
}

static void dump_hex(FILE *out, const uint8_t *bytes, size_t len) {
    for (size_t i = 0; i < len; i++) {
        fprintf(out, "%02x ", bytes[i]);
    }
    fprintf(out, "\n");
}

static int run_emit_mc(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=mc <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    // Check if it's a .mir file
    size_t len = strlen(path);
    if (len >= 4 && strcmp(path + len - 4, ".mir") == 0) {
        AxDriverState st;
        ax_pipeline_init(&st, io);
        st.main_file = path;
        
        ax_pipeline_run(&st, AX_STAGE_SOURCE);
        if (st.failed) {
            ax_pipeline_free(&st);
            free(pos_argv);
            return AX_EXIT_DIAG;
        }
        
        char *text = malloc(st.text.len + 1);
        memcpy(text, st.text.ptr, st.text.len);
        text[st.text.len] = '\0';
        
        AxMirBody *mir_body = ax_mir_parse(text, &st.thir.interner, &st.hir_arena);
        if (mir_body) {
            AxLirBody *lir_body = ax_lir_lower(mir_body, &st.hir, &st.thir.interner, &st.interner, NULL);
            AxType fn_ty = { .kind = AX_TY_FN };
            fn_ty.fn.param_count = 0; 
            fn_ty.fn.ret_type = mir_body->locals[0].ty;
            fn_ty.fn.param_types = NULL;
            ax_lir_lower_abi(lir_body, &st.thir.interner, &ax_abi_win64, &fn_ty);
            
            AxX64MIBody *mi_body = ax_x64_isel(lir_body, &st.thir.interner);
            
            AxX64FrameLayout layout = ax_x64_frame_lower(mi_body, lir_body, &st.thir.interner, &st.hir_arena);
            ax_x64_verify(mi_body, &layout);
            
            ax_objmodel_t obj;
            ax_objmodel_init(&obj);
            ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
            ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);
            
            ax_x64_frame_emit_prologue(text_sec, &layout);
            
                    for (size_t b = 0; b < mi_body->bb_count; b++) {
                        AxX64MIBb *mbb = &mi_body->bbs[b];
                        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
                            encode_mi_to_sec(text_sec, inst, &layout);
                        }
                    }
                    
                    dump_hex(io->out, text_sec->bytes, text_sec->bytes_len);
            
            ax_objmodel_free(&obj);
        }
        
        free(text);
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_OK;
    }

    // AST flow
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    ax_pipeline_run(&st, AX_STAGE_TYPECK);
    if (st.failed) {
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_DIAG;
    }
    
    for (const AxHirItem *item = st.hir.items; item != NULL; item = item->next) {
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = ax_mir_build(item, &st.thir, &st.hir_arena);
            if (mir_body) {
                AxLirBody *lir_body = ax_lir_lower(mir_body, &st.hir, &st.thir.interner, &st.interner, NULL);
                if (lir_body) {
                    const TypeId *pty = AxItemTypeMap_get(&st.thir.item_types, item);
                    const AxType *fn_ty = ax_type_get(&st.thir.interner, *pty);
                    ax_lir_lower_abi(lir_body, &st.thir.interner, &ax_abi_win64, fn_ty);
                    
                    AxX64MIBody *mi_body = ax_x64_isel(lir_body, &st.thir.interner);
                    AxX64FrameLayout layout = ax_x64_frame_lower(mi_body, lir_body, &st.thir.interner, &st.hir_arena);
                    ax_x64_verify(mi_body, &layout);
                    
                    ax_objmodel_t obj;
                    ax_objmodel_init(&obj);
                    ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
                    ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);
                    
                    ax_x64_frame_emit_prologue(text_sec, &layout);
                    
                    for (size_t b = 0; b < mi_body->bb_count; b++) {
                        AxX64MIBb *mbb = &mi_body->bbs[b];
                        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
                            encode_mi_to_sec(text_sec, inst, &layout);
                        }
                    }
                    
                    dump_hex(io->out, text_sec->bytes, text_sec->bytes_len);
                    
                    ax_objmodel_free(&obj);
                }
            }
        }
    }
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return AX_EXIT_OK;
}

const AxEmitter axemit_mc = {
    "mc",
    "dump final machine instructions and hex bytes",
    run_emit_mc
};


