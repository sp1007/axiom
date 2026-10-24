#include "driver/driver.h"
#include "driver/build_native/data_syms.h"
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
#include "types/layout/layout.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// duplicate the encoder logic here to emit the object model
static void encode_mi_to_sec(ax_section_t *sec, const AxX64MI *inst, const AxX64FrameLayout *layout, ax_objmodel_t *obj) {
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
        
        case AX_X64_MI_CMP:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_cmp_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_MEM) {
                ax_x64_cmp_rm(sec, 8, inst->ops[0].reg, inst->ops[1].mem);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_cmp_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
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
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_and_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_OR:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_or_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_IMM) {
                ax_x64_or_ri(sec, 8, inst->ops[0].reg, (int32_t)inst->ops[1].imm);
            }
            break;
        case AX_X64_MI_XOR:
            if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_REG) {
                ax_x64_xor_rr(sec, 8, inst->ops[0].reg, inst->ops[1].reg);
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
            } else if (inst->ops[0].kind == AX_X64_OP_REG && inst->ops[1].kind == AX_X64_OP_SYM) {
                if (inst->msg) {
                    ax_symbol_id_t sym = {0};
                    for (ax_symbol_id_t sid = ax_symbol_table_t_first(&obj->symbols);
                         ax_symbol_id_t_is_some(sid);
                         sid = ax_symbol_table_t_after(&obj->symbols, sid)) {
                        ax_symbol_t *s = ax_symbol_table_t_get(&obj->symbols, sid);
                        if (s->name && strcmp(s->name, inst->msg) == 0) {
                            sym = sid;
                            break;
                        }
                    }
                    if (!ax_symbol_id_t_is_some(sym)) {
                        sym = ax_objmodel_add_symbol(obj, inst->msg, ax_section_id_t_none(), 0, 0, AX_SYM_EXTERNAL);
                    }
                    ax_x64_lea_sym(sec, inst->ops[0].reg, sym);
                } else {
                    ax_x64_lea_sym(sec, inst->ops[0].reg, (ax_symbol_id_t){ inst->ops[1].sym });
                }
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
            }
            break;
    }
}

typedef struct StrRelocLoc {
    size_t offset;
} StrRelocLoc;

static void find_str_locations(TypeId ty_id, const TypeInterner *interner, size_t base_offset, StrRelocLoc **locs, size_t *count, size_t *cap) {
    if (ty_id.v == interner->t_str.v) {
        if (*count == *cap) {
            *cap = *cap ? *cap * 2 : 16;
            *locs = realloc(*locs, *cap * sizeof(StrRelocLoc));
        }
        (*locs)[(*count)++].offset = base_offset;
        return;
    }
    const AxType *ty = ax_type_get(interner, ty_id);
    if (!ty) return;
    if (ty->kind == AX_TY_ARRAY) {
        TypeId elem_ty = ty->array.elem;
        uint32_t fa = ax_type_align(elem_ty, interner);
        uint32_t fs = ax_type_size(elem_ty, interner);
        uint32_t stride = (fs + fa - 1) & ~(fa - 1);
        for (uint64_t i = 0; i < ty->array.len; i++) {
            find_str_locations(elem_ty, interner, base_offset + (size_t)i * stride, locs, count, cap);
        }
    } else if (ty->kind == AX_TY_STRUCT) {
        for (size_t i = 0; i < ty->strct.field_count; i++) {
            uint32_t field_off = ax_type_field_offset(ty_id, i, interner);
            find_str_locations(ty->strct.fields[i], interner, base_offset + field_off, locs, count, cap);
        }
    } else if (ty->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < ty->tuple.field_count; i++) {
            uint32_t field_off = ax_type_field_offset(ty_id, i, interner);
            find_str_locations(ty->tuple.fields[i], interner, base_offset + field_off, locs, count, cap);
        }
    }
}

static const char *get_const_table_sym_name(const struct AxHir *hir, struct StrInterner *str_in, uint32_t sym_v) {
    if (sym_v != 0 && hir && str_in) {
        for (const struct AxHirItem *it = hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_CONST && it->const_decl.symbol.v == sym_v) {
                if (it->const_decl.name.v != 0) {
                    StrView sv = ax_interner_get(str_in, it->const_decl.name);
                    char *name = malloc(sv.len + 32);
                    snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                    return name;
                }
                break;
            }
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const struct AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_CONST && m->const_decl.symbol.v == sym_v) {
                        if (m->const_decl.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->const_decl.name);
                            char *name = malloc(sv.len + 32);
                            snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                            return name;
                        }
                        break;
                    }
                }
            }
            if (it->kind == AX_HIR_ITEM_TRAIT) {
                for (const struct AxHirItem *m = it->trait.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_CONST && m->const_decl.symbol.v == sym_v) {
                        if (m->const_decl.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->const_decl.name);
                            char *name = malloc(sv.len + 32);
                            snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                            return name;
                        }
                        break;
                    }
                }
            }
        }
    }
    char *name = malloc(32);
    snprintf(name, 32, ".Lconst_%u", sym_v);
    return name;
}

typedef struct ConstTableToEmit {
    AxSymbolId sym;
    char *sym_name;
    AxConstValue *cval;
    uint8_t *data;
    size_t size;
    size_t align;
    size_t reloc_count;
    size_t *reloc_offsets;
    const uint8_t **reloc_str_ptrs;
    uint64_t *reloc_str_lens;
    bool is_duplicate;
    uint32_t duplicate_of_idx;
    uint32_t emitted_offset;
} ConstTableToEmit;

static int compare_const_tables(const void *a, const void *b) {
    const ConstTableToEmit *ta = (const ConstTableToEmit *)a;
    const ConstTableToEmit *tb = (const ConstTableToEmit *)b;
    return strcmp(ta->sym_name, tb->sym_name);
}

static bool are_const_tables_identical(const ConstTableToEmit *a, const ConstTableToEmit *b) {
    if (a->size != b->size) return false;
    if (a->align != b->align) return false;
    if (a->reloc_count != b->reloc_count) return false;
    for (size_t r = 0; r < a->reloc_count; r++) {
        if (a->reloc_offsets[r] != b->reloc_offsets[r]) return false;
        if (a->reloc_str_lens[r] != b->reloc_str_lens[r]) return false;
        if (a->reloc_str_lens[r] > 0) {
            if (memcmp(a->reloc_str_ptrs[r], b->reloc_str_ptrs[r], (size_t)a->reloc_str_lens[r]) != 0) {
                return false;
            }
        }
    }
    if (a->size > 0 && memcmp(a->data, b->data, a->size) != 0) return false;
    return true;
}

static void emit_const_tables(AxDriverState *st, ax_objmodel_t *obj, ax_section_id_t rdata_sec_id) {
    AxSymbolId *syms = NULL;
    size_t sym_count = 0;
    size_t sym_cap = 0;

    for (const AxHirItem *item = st->hir.items; item != NULL; item = item->next) {
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir = ax_mir_build(item, &st->thir, &st->hir_arena);
            if (!mir) continue;
            for (size_t i = 0; i < mir->local_count; i++) {
                if (mir->locals[i].kind == AX_MIR_LOCAL_CONST) {
                    AxSymbolId sym = mir->locals[i].const_sym;
                    bool exists = false;
                    for (size_t s = 0; s < sym_count; s++) {
                        if (syms[s].v == sym.v) { exists = true; break; }
                    }
                    if (!exists) {
                        if (sym_count == sym_cap) {
                            sym_cap = sym_cap ? sym_cap * 2 : 16;
                            syms = realloc(syms, sym_cap * sizeof(AxSymbolId));
                        }
                        syms[sym_count++] = sym;
                    }
                }
            }
        }
    }

    if (sym_count == 0) {
        free(syms);
        return;
    }

    ConstTableToEmit *tables = calloc(sym_count, sizeof(ConstTableToEmit));
    size_t table_count = 0;

    for (size_t s = 0; s < sym_count; s++) {
        AxSymbolId sym = syms[s];
        AxConstValue *cval = AxSymbolConstMap_get(&st->thir.symbol_consts, sym);
        if (!cval || cval->kind != AX_CONST_AGGREGATE || !cval->aggregate.data) continue;

        ConstTableToEmit *entry = &tables[table_count++];
        entry->sym = sym;
        entry->sym_name = (char*)get_const_table_sym_name(&st->hir, &st->interner, sym.v);
        entry->cval = cval;
        entry->size = cval->aggregate.size;
        entry->align = cval->aggregate.align ? cval->aggregate.align : 8;
        entry->data = malloc(entry->size ? entry->size : 1);
        memcpy(entry->data, cval->aggregate.data, entry->size);

        StrRelocLoc *locs = NULL;
        size_t loc_count = 0, loc_cap = 0;
        find_str_locations(cval->ty, &st->thir.interner, 0, &locs, &loc_count, &loc_cap);

        entry->reloc_count = loc_count;
        if (loc_count > 0) {
            entry->reloc_offsets = malloc(loc_count * sizeof(size_t));
            entry->reloc_str_ptrs = malloc(loc_count * sizeof(const uint8_t*));
            entry->reloc_str_lens = malloc(loc_count * sizeof(uint64_t));
            for (size_t k = 0; k < loc_count; k++) {
                size_t off = locs[k].offset;
                entry->reloc_offsets[k] = off;
                entry->reloc_str_ptrs[k] = *(const uint8_t**)(cval->aggregate.data + off);
                entry->reloc_str_lens[k] = *(uint64_t*)(cval->aggregate.data + off + 8);
                memset(entry->data + off, 0, 8);
            }
            free(locs);
        }
    }
    free(syms);

    if (table_count == 0) {
        free(tables);
        return;
    }

    qsort(tables, table_count, sizeof(ConstTableToEmit), compare_const_tables);

    for (size_t i = 0; i < table_count; i++) {
        for (size_t j = 0; j < i; j++) {
            if (are_const_tables_identical(&tables[j], &tables[i])) {
                tables[i].is_duplicate = true;
                tables[i].duplicate_of_idx = (uint32_t)j;
                break;
            }
        }
    }

    ax_section_t *rdata_sec = ax_objmodel_get_section(obj, rdata_sec_id);
    int s_cstr_counter = 0; /* per object (ADR-0035 section 1), never process-wide */

    for (size_t i = 0; i < table_count; i++) {
        ConstTableToEmit *entry = &tables[i];
        if (entry->is_duplicate) {
            entry->emitted_offset = tables[entry->duplicate_of_idx].emitted_offset;
            ax_objmodel_add_symbol(obj, strdup(entry->sym_name), rdata_sec_id, entry->emitted_offset, entry->size, AX_SYM_GLOBAL);
            continue;
        }

        ax_symbol_id_t *str_syms = entry->reloc_count ? malloc(entry->reloc_count * sizeof(ax_symbol_id_t)) : NULL;
        for (size_t k = 0; k < entry->reloc_count; k++) {
            const uint8_t *s_bytes = entry->reloc_str_ptrs[k];
            uint64_t s_len = entry->reloc_str_lens[k];
            uint32_t s_offset = rdata_sec->bytes_len;
            if (s_bytes && s_len > 0) {
                ax_section_add_bytes(rdata_sec, s_bytes, s_len);
            }
            ax_section_add_byte(rdata_sec, 0);
            while (rdata_sec->bytes_len % 8 != 0) {
                ax_section_add_byte(rdata_sec, 0);
            }
            char cstr_name[64];
            snprintf(cstr_name, sizeof(cstr_name), ".Lcstr_%d", s_cstr_counter++);
            str_syms[k] = ax_objmodel_add_symbol(obj, strdup(cstr_name), rdata_sec_id, s_offset, s_len, AX_SYM_GLOBAL);
        }

        while (rdata_sec->bytes_len % entry->align != 0) {
            ax_section_add_byte(rdata_sec, 0);
        }
        entry->emitted_offset = rdata_sec->bytes_len;

        for (size_t k = 0; k < entry->reloc_count; k++) {
            ax_section_add_reloc(rdata_sec, entry->emitted_offset + entry->reloc_offsets[k], AX_RELOC_X86_64_64, str_syms[k], 0);
        }
        if (str_syms) free(str_syms);

        if (entry->size > 0) {
            ax_section_add_bytes(rdata_sec, entry->data, entry->size);
        }

        ax_objmodel_add_symbol(obj, strdup(entry->sym_name), rdata_sec_id, entry->emitted_offset, entry->size, AX_SYM_GLOBAL);
    }

    for (size_t i = 0; i < table_count; i++) {
        free(tables[i].sym_name);
        free(tables[i].data);
        if (tables[i].reloc_count > 0) {
            free(tables[i].reloc_offsets);
            free(tables[i].reloc_str_ptrs);
            free(tables[i].reloc_str_lens);
        }
    }
    free(tables);
}

static int run_emit_obj(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=obj <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    ax_pipeline_run(&st, AX_STAGE_TYPECK);
    if (st.failed) {
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_DIAG;
    }
    
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);
    ax_section_id_t rdata_sec_id = ax_objmodel_add_section(&obj, ".rdata", AX_SEC_RODATA, AX_SEC_FLAG_READ, 16);
    
    emit_const_tables(&st, &obj, rdata_sec_id);
    uint32_t fn_ordinal = 0;
    
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
                    
                    /* same code path as `axiom0 build` (ADR-0035 section 1) */
                    ax_emit_fn_string_data(&obj, rdata_sec_id, mi_body, fn_ordinal++);

                    uint64_t func_start = text_sec->bytes_len;
                    while (text_sec->bytes_len % 16 != 0) {
                        ax_section_add_byte(text_sec, 0x90);
                    }
                    func_start = text_sec->bytes_len;
                    
                    StrView name = ax_interner_get(&st.interner, item->fn.name);
                    char name_buf[256];
                    snprintf(name_buf, 256, "%.*s", (int)name.len, name.ptr);
                    
                    ax_x64_frame_emit_prologue(text_sec, &layout);
                    
                    for (size_t b = 0; b < mi_body->bb_count; b++) {
                        AxX64MIBb *mbb = &mi_body->bbs[b];
                        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
                            encode_mi_to_sec(text_sec, inst, &layout, &obj);
                        }
                    }
                    
                    uint64_t func_size = text_sec->bytes_len - func_start;
                    ax_objmodel_add_symbol(&obj, strdup(name_buf), text_sec_id, func_start, func_size, AX_SYM_GLOBAL);
                }
            }
        }
    }
    
    char temp_path[1024];
    snprintf(temp_path, sizeof(temp_path), "%s.obj", path);
    ax_coff_write(&obj, temp_path);
    ax_objmodel_free(&obj);
    
    // Copy the file contents to stdout since inspect dumps to stdout
    FILE *f = fopen(temp_path, "rb");
    if (f) {
        char buf[4096];
        size_t n;
        while ((n = fread(buf, 1, sizeof(buf), f)) > 0) {
            fwrite(buf, 1, n, io->out);
        }
        fclose(f);
    }
    remove(temp_path);
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return AX_EXIT_OK;
}

const AxEmitter axemit_obj = {
    "obj",
    "Emit COFF object file",
    run_emit_obj
};


