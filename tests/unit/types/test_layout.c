#include "unit.h"
#include "types/types.h"
#include "types/layout/layout.h"

AX_TEST(layout_basic) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    
    AxLayout layout = ax_type_layout(interner.t_i32, &interner);
    AX_CHECK(layout.size == 4);
    AX_CHECK(layout.align == 4);
    
    TypeId fields[] = { interner.t_u8, interner.t_u32, interner.t_u16 };
    AxType ty = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)1, .fields = fields, .field_count = 3, .is_repr_c = false } };
    TypeId s_id = ax_intern_type(&interner, &ty);
    
    AxLayout s_layout = ax_type_layout(s_id, &interner);
    AX_CHECK(s_layout.align == 4);
    AX_CHECK(s_layout.size == 8);
    
    AX_CHECK(ax_type_field_offset(s_id, 1, &interner) == 0);
    AX_CHECK(ax_type_field_offset(s_id, 2, &interner) == 4);
    AX_CHECK(ax_type_field_offset(s_id, 0, &interner) == 6);
    
    AxType ty_c = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)2, .fields = fields, .field_count = 3, .is_repr_c = true } };
    TypeId c_id = ax_intern_type(&interner, &ty_c);
    
    AxLayout c_layout = ax_type_layout(c_id, &interner);

    AX_CHECK(c_layout.align == 4);
    AX_CHECK(c_layout.size == 12);
    
    AX_CHECK(ax_type_field_offset(c_id, 0, &interner) == 0);
    AX_CHECK(ax_type_field_offset(c_id, 1, &interner) == 4);
    AX_CHECK(ax_type_field_offset(c_id, 2, &interner) == 8);

    ax_type_interner_free(&interner);
}

AX_TEST(layout_edge) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    
    // Empty struct
    AxType ty_empty = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)3, .fields = NULL, .field_count = 0, .is_repr_c = false } };
    TypeId empty_id = ax_intern_type(&interner, &ty_empty);
    AxLayout empty_layout = ax_type_layout(empty_id, &interner);
    AX_CHECK(empty_layout.size == 0);
    AX_CHECK(empty_layout.align == 1);
    
    // Nested struct
    TypeId fields[] = { interner.t_u8, interner.t_u32, interner.t_u16 };
    AxType ty_inner = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)4, .fields = fields, .field_count = 3, .is_repr_c = true } };
    TypeId inner_id = ax_intern_type(&interner, &ty_inner); // align 4, size 12
    
    TypeId outer_fields[] = { interner.t_u8, inner_id, interner.t_u8 };
    AxType ty_outer = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)5, .fields = outer_fields, .field_count = 3, .is_repr_c = true } };
    TypeId outer_id = ax_intern_type(&interner, &ty_outer);
    
    AxLayout outer_layout = ax_type_layout(outer_id, &interner);
    AX_CHECK(outer_layout.align == 4);
    AX_CHECK(outer_layout.size == 20); // u8(1) + pad(3) + inner(12) + u8(1) + pad(3) = 20
    
    AX_CHECK(ax_type_field_offset(outer_id, 0, &interner) == 0);
    AX_CHECK(ax_type_field_offset(outer_id, 1, &interner) == 4);
    AX_CHECK(ax_type_field_offset(outer_id, 2, &interner) == 16);
    
    ax_type_interner_free(&interner);
}
AX_TEST(layout_qa_extra) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    
    // Test Array
    AxType ty_array = { .kind = AX_TY_ARRAY, .array = { .elem = interner.t_u16, .len = 5 } };
    TypeId array_id = ax_intern_type(&interner, &ty_array);
    AxLayout array_layout = ax_type_layout(array_id, &interner);
    AX_CHECK(array_layout.size == 10);
    AX_CHECK(array_layout.align == 2);
    
    // Test Tuple (sorted like non-repr(C) struct)
    TypeId fields[] = { interner.t_u8, interner.t_u32, interner.t_u16 };
    AxType ty_tuple = { .kind = AX_TY_TUPLE, .tuple = { .fields = fields, .field_count = 3 } };
    TypeId tuple_id = ax_intern_type(&interner, &ty_tuple);
    AxLayout tuple_layout = ax_type_layout(tuple_id, &interner);
    AX_CHECK(tuple_layout.align == 4);
    AX_CHECK(tuple_layout.size == 8);
    AX_CHECK(ax_type_field_offset(tuple_id, 1, &interner) == 0); // u32 is largest align
    AX_CHECK(ax_type_field_offset(tuple_id, 2, &interner) == 4); // u16
    AX_CHECK(ax_type_field_offset(tuple_id, 0, &interner) == 6); // u8

    // Test > 128 fields
    TypeId big_fields[130];
    for (int i = 0; i < 130; i++) big_fields[i] = interner.t_u8;
    AxType ty_big = { .kind = AX_TY_STRUCT, .strct = { .def = (void*)6, .fields = big_fields, .field_count = 130, .is_repr_c = false } };
    TypeId big_id = ax_intern_type(&interner, &ty_big);
    AxLayout big_layout = ax_type_layout(big_id, &interner);
    AX_CHECK(big_layout.size == 130);
    AX_CHECK(big_layout.align == 1);
    AX_CHECK(ax_type_field_offset(big_id, 129, &interner) == 129);

    ax_type_interner_free(&interner);
}
