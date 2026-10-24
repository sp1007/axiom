#include "driver/build_native/data_syms.h"
#include "kernel/base.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void ax_emit_fn_string_data(ax_objmodel_t *obj, ax_section_id_t rdata_sec_id,
                            AxX64MIBody *mi_body, uint32_t fn_ordinal) {
    if (mi_body->string_count == 0) return;

    uint32_t *sym_map = ax_xmalloc(mi_body->string_count * sizeof(uint32_t));
    for (size_t s = 0; s < mi_body->string_count; s++) {
        AxX64MIStr *str = &mi_body->strings[s];
        ax_section_t *rdata_sec = ax_objmodel_get_section(obj, rdata_sec_id);
        uint64_t offset = rdata_sec->bytes_len;
        if (str->len > 0) ax_section_add_bytes(rdata_sec, str->bytes, str->len);
        ax_section_add_byte(rdata_sec, 0); /* NUL terminator */
        while (rdata_sec->bytes_len % 8 != 0) {
            ax_section_add_byte(rdata_sec, 0);
        }
        char sym_name[64];
        snprintf(sym_name, sizeof(sym_name), ".Lstr.%u.%u", fn_ordinal, str->sym_id);
        ax_symbol_id_t sym = ax_objmodel_add_symbol(obj, strdup(sym_name), rdata_sec_id, offset, str->len, AX_SYM_LOCAL);
        sym_map[s] = sym.v;
    }

    for (size_t b = 0; b < mi_body->bb_count; b++) {
        AxX64MIBb *mbb = &mi_body->bbs[b];
        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
            if (inst->opcode == AX_X64_MI_LEA && inst->ops[1].kind == AX_X64_OP_SYM && !inst->msg) {
                for (size_t s = 0; s < mi_body->string_count; s++) {
                    if (inst->ops[1].sym == mi_body->strings[s].sym_id) {
                        inst->ops[1].sym = sym_map[s];
                        break;
                    }
                }
            }
        }
    }
    ax_xfree(sym_map);
}

void ax_panic_sym_name(char *buf, size_t cap, uint32_t n) {
    snprintf(buf, cap, ".Lpanic.%u", n);
}
