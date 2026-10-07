#ifndef AX_TARGET_X64_FRAME_FRAME_H
#define AX_TARGET_X64_FRAME_FRAME_H

#include "target/x64/mir/mi.h"
#include "lir/lir.h"
#include "objmodel/objmodel.h"
#include <stdint.h>

typedef struct AxX64FrameLayout {
    int32_t *slot_offsets; // Offsets from RBP
    uint32_t slot_count;
    uint32_t frame_size;
} AxX64FrameLayout;

AxX64FrameLayout ax_x64_frame_lower(AxX64MIBody *body, const AxLirBody *lir, TypeInterner *interner, AxArena *arena);
void ax_x64_frame_emit_prologue(ax_section_t *sec, const AxX64FrameLayout *layout);
void ax_x64_frame_emit_epilogue(ax_section_t *sec, const AxX64FrameLayout *layout);

#endif
