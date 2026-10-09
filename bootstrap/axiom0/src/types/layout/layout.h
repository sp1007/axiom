#pragma once
#include "types/types.h"

typedef struct {
    uint32_t size;
    uint32_t align;
} AxLayout;

AxLayout ax_type_layout(TypeId type, const TypeInterner* interner);
uint32_t ax_type_field_offset(TypeId id, size_t field_idx, const TypeInterner *in);
