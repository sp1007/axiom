#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "target/x64/frame/frame.h"
#include "target/x64/encode/encode.h"

int main(void) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    TypeInterner interner;
    ax_type_interner_init(&interner);
    
    // Create LIR body with exactly 4096 bytes frame
    AxLirBody lir = {0};
    lir.slot_count = 1;
    lir.slots = AX_ARENA_NEW_ARRAY(&arena, AxLirStackSlot, 1);
    
    // To test the exact edge of 4096, we need to consider callee-saved registers (56 bytes),
    // shadow space (32 bytes), and 16-byte alignment of the final frame size.
    // The frame size will always be 8 mod 16. The closest sizes are 4088 and 4104.
    // len = 4056 -> current_offset = 56 + 4056 = 4112. +32 shadow = 4144 (aligned). frame_size = 4144 - 56 = 4088. (<= 4096, no loop)
    AxType arr_ty = { .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 4056 } };
    lir.slots[0].ty = ax_intern_type(&interner, &arr_ty);
    
    lir.vreg_count = 0;
    lir.frame_req.requires_16_byte_alignment = true;
    lir.frame_req.max_outgoing_args_bytes = 0;
    
    AxX64MIBody mi = {0};
    mi.arena = arena;
    mi.bb_count = 0;
    mi.shadow_space = 0;
    
    AxX64FrameLayout layout = ax_x64_frame_lower(&mi, &lir, &interner, &arena);
    assert(layout.frame_size == 4088);
    
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);
    
    ax_x64_frame_emit_prologue(text_sec, &layout);
    
    assert(text_sec->bytes_len > 0);
    bool found_probe = false;
    for (size_t i = 0; i < text_sec->bytes_len - 2; i++) {
        if (text_sec->bytes[i] == 0x85 && text_sec->bytes[i+1] == 0x04 && text_sec->bytes[i+2] == 0x24) {
            found_probe = true;
            break;
        }
    }
    // Spec 0188 §12: "A frame larger than 4096 bytes gets an inline loop"
    assert(!found_probe);
    
    // Now test len = 4057 -> frame_size = 4104 (> 4096, loop)
    AxLirBody lir2 = {0};
    lir2.slot_count = 1;
    lir2.slots = AX_ARENA_NEW_ARRAY(&arena, AxLirStackSlot, 1);
    AxType arr_ty2 = { .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 4057 } };
    lir2.slots[0].ty = ax_intern_type(&interner, &arr_ty2);
    lir2.frame_req.requires_16_byte_alignment = true;
    
    AxX64FrameLayout layout2 = ax_x64_frame_lower(&mi, &lir2, &interner, &arena);
    assert(layout2.frame_size == 4104);
    
    ax_section_id_t text_sec_id2 = ax_objmodel_add_section(&obj, ".text2", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec2 = ax_objmodel_get_section(&obj, text_sec_id2);
    
    ax_x64_frame_emit_prologue(text_sec2, &layout2);
    
    bool found_probe2 = false;
    for (size_t i = 0; i < text_sec2->bytes_len - 2; i++) {
        if (text_sec2->bytes[i] == 0x85 && text_sec2->bytes[i+1] == 0x04 && text_sec2->bytes[i+2] == 0x24) {
            found_probe2 = true;
            break;
        }
    }
    assert(found_probe2);
    
    ax_objmodel_free(&obj);
    return 0;
}
