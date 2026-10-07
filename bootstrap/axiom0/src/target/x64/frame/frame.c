#include "frame.h"
#include "types/types.h"
#include "target/x64/encode/encode.h"

AxX64FrameLayout ax_x64_frame_lower(AxX64MIBody *body, const AxLirBody *lir, TypeInterner *interner, AxArena *arena) {
    AxX64FrameLayout layout = {0};
    layout.slot_count = lir->slot_count + lir->vreg_count;
    if (layout.slot_count > 0) {
        layout.slot_offsets = AX_ARENA_NEW_ARRAY(arena, int32_t, layout.slot_count);
    }
    
    int32_t current_offset = 0;
    
    for (size_t i = 0; i < lir->slot_count; i++) {
        uint32_t size = ax_type_size(lir->slots[i].ty, interner);
        uint32_t align = ax_type_align(lir->slots[i].ty, interner);
        if (size < 8) size = 8;
        if (align < 8) align = 8;
        current_offset = (current_offset + size + align - 1) & ~(align - 1);
        layout.slot_offsets[i] = -current_offset;
    }
    
    for (size_t i = 0; i < lir->vreg_count; i++) {
        uint32_t size = ax_type_size(lir->vregs[i].ty, interner);
        uint32_t align = ax_type_align(lir->vregs[i].ty, interner);
        if (size < 8) size = 8;
        if (align < 8) align = 8;
        current_offset = (current_offset + size + align - 1) & ~(align - 1);
        layout.slot_offsets[lir->slot_count + i] = -current_offset;
    }
    
    current_offset += body->shadow_space;
    
    if (lir->frame_req.requires_16_byte_alignment || true) {
        current_offset = (current_offset + 15) & ~15;
    }
    
    layout.frame_size = current_offset;
    
    for (size_t b = 0; b < body->bb_count; b++) {
        AxX64MIBb *mbb = &body->bbs[b];
        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
            for (int op_idx = 0; op_idx < inst->op_count; op_idx++) {
                if (inst->ops[op_idx].kind == AX_X64_OP_FRAME) {
                    uint32_t slot_id = inst->ops[op_idx].frame.slot_id;
                    int32_t offset = inst->ops[op_idx].frame.offset;
                    int32_t total_disp = layout.slot_offsets[slot_id] + offset;
                    
                    inst->ops[op_idx].kind = AX_X64_OP_MEM;
                    inst->ops[op_idx].mem.base = AX_REG_RBP; // 5
                    inst->ops[op_idx].mem.index = AX_REG_NONE;
                    inst->ops[op_idx].mem.scale = 1;
                    inst->ops[op_idx].mem.disp = total_disp;
                    inst->ops[op_idx].mem.is_rip = false;
                }
            }
        }
    }
    
    return layout;
}

void ax_x64_frame_emit_prologue(ax_section_t *sec, const AxX64FrameLayout *layout) {
    ax_x64_push_r(sec, AX_REG_RBP);
    ax_x64_mov_rr(sec, 8, AX_REG_RBP, AX_REG_RSP);
    
    if (layout->frame_size > 0) {
        if (layout->frame_size > 4096) {
            ax_x64_mov_ri(sec, 8, AX_REG_RAX, layout->frame_size);
            int32_t probe_start = sec->bytes_len;
            ax_x64_sub_ri(sec, 8, AX_REG_RSP, 4096);
            ax_x64_mem_t rsp_mem = ax_x64_mem_base(AX_REG_RSP);
            ax_x64_test_rm(sec, 4, AX_REG_RAX, rsp_mem);
            ax_x64_sub_ri(sec, 8, AX_REG_RAX, 4096);
            ax_x64_cmp_ri(sec, 8, AX_REG_RAX, 4096);
            int32_t jump_source = sec->bytes_len + 2;
            int32_t rel = probe_start - jump_source;
            ax_x64_jcc8(sec, AX_CC_A, (int8_t)rel);
            ax_x64_sub_rr(sec, 8, AX_REG_RSP, AX_REG_RAX);
        } else {
            ax_x64_sub_ri(sec, 8, AX_REG_RSP, layout->frame_size);
        }
    }
}

void ax_x64_frame_emit_epilogue(ax_section_t *sec, const AxX64FrameLayout *layout) {
    if (layout->frame_size > 0) {
        ax_x64_mov_rr(sec, 8, AX_REG_RSP, AX_REG_RBP);
    }
    ax_x64_pop_r(sec, AX_REG_RBP);
}
