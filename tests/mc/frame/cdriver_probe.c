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
    
    // Create LIR body with large slot
    AxLirBody lir = {0};
    lir.slot_count = 1;
    lir.slots = AX_ARENA_NEW_ARRAY(&arena, AxLirStackSlot, 1);
    
    // Create an array type of 65536 bytes
    AxType arr_ty = { .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 65536 } };
    lir.slots[0].ty = ax_intern_type(&interner, &arr_ty);
    
    lir.vreg_count = 0;
    lir.frame_req.requires_16_byte_alignment = true;
    lir.frame_req.max_outgoing_args_bytes = 0;
    
    AxX64MIBody mi = {0};
    mi.arena = arena;
    mi.bb_count = 0;
    mi.shadow_space = 0;
    
    AxX64FrameLayout layout = ax_x64_frame_lower(&mi, &lir, &interner, &arena);
    
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    ax_section_id_t text_sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec = ax_objmodel_get_section(&obj, text_sec_id);
    
    ax_x64_frame_emit_prologue(text_sec, &layout);
    
    // We emitted prologue for a 65536 byte frame.
    // The probe loop touches pages. Let's verify by just printing bytes.
    // We'll also just check the size of the emitted code.
    assert(text_sec->bytes_len > 0);
    bool found_probe = false;
    for (size_t i = 0; i < text_sec->bytes_len - 2; i++) {
        if (text_sec->bytes[i] == 0x85 && text_sec->bytes[i+1] == 0x04 && text_sec->bytes[i+2] == 0x24) {
            found_probe = true;
            break;
        }
    }
    assert(found_probe);
    
    // Now let's try a 4000 byte frame
    AxLirBody lir2 = {0};
    lir2.slot_count = 1;
    lir2.slots = AX_ARENA_NEW_ARRAY(&arena, AxLirStackSlot, 1);
    AxType arr_ty2 = { .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 4000 } };
    lir2.slots[0].ty = ax_intern_type(&interner, &arr_ty2);
    
    AxX64FrameLayout layout2 = ax_x64_frame_lower(&mi, &lir2, &interner, &arena);
    
    ax_objmodel_t obj2;
    ax_objmodel_init(&obj2);
    ax_section_id_t text_sec_id2 = ax_objmodel_add_section(&obj2, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text_sec2 = ax_objmodel_get_section(&obj2, text_sec_id2);
    
    ax_x64_frame_emit_prologue(text_sec2, &layout2);
    
    assert(text_sec2->bytes_len > 0);
    // The second one shouldn't have the loop, so it's much shorter
    assert(text_sec2->bytes_len < text_sec->bytes_len);
    
    ax_objmodel_free(&obj);
    ax_objmodel_free(&obj2);
    
    printf("cdriver_probe passed\n");
    return 0;
}
