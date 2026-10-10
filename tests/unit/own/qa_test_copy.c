#include "unit.h"
#include "own/own.h"
#include "types/types.h"
#include "kernel/interner.h"
#include "diag/diag.h"

AX_TEST(own_copy_classification_qa_edges) {
    TypeInterner interner;
    ax_type_interner_init(&interner);

    StrInterner str_in;
    ax_interner_init(&str_in);

    AxThir thir;
    memset(&thir, 0, sizeof(thir));
    thir.interner = interner;

    /* 1. Invalid / zero TypeId */
    AX_CHECK(ax_type_is_copy((TypeId){0}, &thir, &str_in) == false);

    /* 2. Primitive signed/unsigned and char/never */
    AX_CHECK(ax_type_is_copy(thir.interner.t_i8, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_i16, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_i32, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_i64, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_isize, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_u8, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_u16, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_u64, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_usize, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_char, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_never, &thir, &str_in) == true);
    AX_CHECK(ax_type_is_copy(thir.interner.t_error, &thir, &str_in) == false);

    /* 3. Empty tuple () */
    AxType ty_empty_tuple = { .kind = AX_TY_TUPLE, .tuple = { .fields = NULL, .field_count = 0 } };
    TypeId empty_tuple_id = ax_intern_type(&thir.interner, &ty_empty_tuple);
    AX_CHECK(ax_type_is_copy(empty_tuple_id, &thir, &str_in) == true);

    /* 4. Nested tuple */
    TypeId inner_fields[] = { thir.interner.t_i32, thir.interner.t_bool };
    AxType ty_inner_tuple = { .kind = AX_TY_TUPLE, .tuple = { .fields = inner_fields, .field_count = 2 } };
    TypeId inner_tuple_id = ax_intern_type(&thir.interner, &ty_inner_tuple);

    TypeId outer_c_fields[] = { inner_tuple_id, thir.interner.t_char };
    AxType ty_outer_tuple_c = { .kind = AX_TY_TUPLE, .tuple = { .fields = outer_c_fields, .field_count = 2 } };
    TypeId outer_tuple_c_id = ax_intern_type(&thir.interner, &ty_outer_tuple_c);
    AX_CHECK(ax_type_is_copy(outer_tuple_c_id, &thir, &str_in) == true);

    TypeId outer_nc_fields[] = { inner_tuple_id, thir.interner.t_str };
    AxType ty_outer_tuple_nc = { .kind = AX_TY_TUPLE, .tuple = { .fields = outer_nc_fields, .field_count = 2 } };
    TypeId outer_tuple_nc_id = ax_intern_type(&thir.interner, &ty_outer_tuple_nc);
    AX_CHECK(ax_type_is_copy(outer_tuple_nc_id, &thir, &str_in) == false);

    /* 5. Nested array of array: [[u8; 4]; 2] */
    AxType ty_inner_arr = { .kind = AX_TY_ARRAY, .array = { .elem = thir.interner.t_u8, .len = 4 } };
    TypeId inner_arr_id = ax_intern_type(&thir.interner, &ty_inner_arr);
    AxType ty_outer_arr = { .kind = AX_TY_ARRAY, .array = { .elem = inner_arr_id, .len = 2 } };
    TypeId outer_arr_id = ax_intern_type(&thir.interner, &ty_outer_arr);
    AX_CHECK(ax_type_is_copy(outer_arr_id, &thir, &str_in) == true);

    /* 6. Enums */
    /* 6a. Enum without attributes */
    AxHirItem enum_nc = { .kind = AX_HIR_ITEM_ENUM, .attrs = NULL };
    AxType ty_enum_nc = { .kind = AX_TY_ENUM, .enm = { .def = &enum_nc, .variant_fields = NULL, .variant_field_counts = NULL, .variant_count = 0, .is_repr_c = false } };
    TypeId enum_nc_id = ax_intern_type(&thir.interner, &ty_enum_nc);
    AX_CHECK(ax_type_is_copy(enum_nc_id, &thir, &str_in) == false);

    /* 6b. Enum with @derive(Copy) */
    AxHirAttrArg arg_copy = { .name = ax_intern_cstr(&str_in, "Copy"), .next = NULL };
    AxHirAttr attr_derive_copy = { .name = ax_intern_cstr(&str_in, "derive"), .args = &arg_copy, .next = NULL };
    AxHirItem enum_c = { .kind = AX_HIR_ITEM_ENUM, .attrs = &attr_derive_copy };
    AxType ty_enum_c = { .kind = AX_TY_ENUM, .enm = { .def = &enum_c, .variant_fields = NULL, .variant_field_counts = NULL, .variant_count = 0, .is_repr_c = false } };
    TypeId enum_c_id = ax_intern_type(&thir.interner, &ty_enum_c);
    AX_CHECK(ax_type_is_copy(enum_c_id, &thir, &str_in) == true);

    /* 6c. Enum with chained derive args: @derive(Debug, Copy) */
    AxHirAttrArg arg_copy_2 = { .name = ax_intern_cstr(&str_in, "Copy"), .next = NULL };
    AxHirAttrArg arg_debug = { .name = ax_intern_cstr(&str_in, "Debug"), .next = &arg_copy_2 };
    AxHirAttr attr_derive_multi = { .name = ax_intern_cstr(&str_in, "derive"), .args = &arg_debug, .next = NULL };
    AxHirItem enum_multi = { .kind = AX_HIR_ITEM_ENUM, .attrs = &attr_derive_multi };
    AxType ty_enum_multi = { .kind = AX_TY_ENUM, .enm = { .def = &enum_multi, .variant_fields = NULL, .variant_field_counts = NULL, .variant_count = 0, .is_repr_c = false } };
    TypeId enum_multi_id = ax_intern_type(&thir.interner, &ty_enum_multi);
    AX_CHECK(ax_type_is_copy(enum_multi_id, &thir, &str_in) == true);

    /* 6d. Enum with @derive(Clone) but no Copy */
    AxHirAttrArg arg_clone = { .name = ax_intern_cstr(&str_in, "Clone"), .next = NULL };
    AxHirAttr attr_derive_clone = { .name = ax_intern_cstr(&str_in, "derive"), .args = &arg_clone, .next = NULL };
    AxHirItem enum_clone = { .kind = AX_HIR_ITEM_ENUM, .attrs = &attr_derive_clone };
    AxType ty_enum_clone = { .kind = AX_TY_ENUM, .enm = { .def = &enum_clone, .variant_fields = NULL, .variant_field_counts = NULL, .variant_count = 0, .is_repr_c = false } };
    TypeId enum_clone_id = ax_intern_type(&thir.interner, &ty_enum_clone);
    AX_CHECK(ax_type_is_copy(enum_clone_id, &thir, &str_in) == false);

    /* 7. Struct with non-derive attribute: @repr("C") */
    AxHirAttr attr_repr = { .name = ax_intern_cstr(&str_in, "repr"), .args = NULL, .next = NULL };
    AxHirItem struct_repr = { .kind = AX_HIR_ITEM_STRUCT, .attrs = &attr_repr };
    AxType ty_struct_repr = { .kind = AX_TY_STRUCT, .strct = { .def = &struct_repr, .fields = NULL, .field_count = 0, .is_repr_c = true } };
    TypeId struct_repr_id = ax_intern_type(&thir.interner, &ty_struct_repr);
    AX_CHECK(ax_type_is_copy(struct_repr_id, &thir, &str_in) == false);

    /* 8. Struct/Enum with NULL def */
    AxType ty_struct_null = { .kind = AX_TY_STRUCT, .strct = { .def = NULL, .fields = NULL, .field_count = 0, .is_repr_c = false } };
    TypeId struct_null_id = ax_intern_type(&thir.interner, &ty_struct_null);
    AX_CHECK(ax_type_is_copy(struct_null_id, &thir, &str_in) == false);

    /* 9. MOVE diagnostic check */
    AX_CHECK_EQ_STR(ax_diag_code_default_message(AX_MOVE_USE_AFTER_MOVE), "use of moved value");

    /* 10. AxOwnState enum values */
    AX_CHECK_EQ_INT((int)AX_OWN_UNINIT, 0);
    AX_CHECK_EQ_INT((int)AX_OWN_OWNED, 1);
    AX_CHECK_EQ_INT((int)AX_OWN_MOVED, 2);
    AX_CHECK_EQ_INT((int)AX_OWN_PARTIAL, 3);

    ax_type_interner_free(&thir.interner);
    ax_interner_free(&str_in);
}
