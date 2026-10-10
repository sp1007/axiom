#include "unit.h"
#include "own/own.h"
#include "types/types.h"
#include "kernel/interner.h"

AX_TEST(own_copy_classification) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    
    StrInterner str_in;
    ax_interner_init(&str_in);
    
    AxThir thir;
    memset(&thir, 0, sizeof(thir));
    thir.interner = interner;

    AX_CHECK(ax_type_is_copy(thir.interner.t_u32, &thir, &str_in) == true);
    
    AxType ty_bool = { .kind = AX_TY_BOOL };
    TypeId id_bool = ax_intern_type(&thir.interner, &ty_bool);
    AX_CHECK(ax_type_is_copy(id_bool, &thir, &str_in) == true);
    
    AxType ty_ptr = { .kind = AX_TY_PTR };
    TypeId id_ptr = ax_intern_type(&thir.interner, &ty_ptr);
    AX_CHECK(ax_type_is_copy(id_ptr, &thir, &str_in) == true);
    
    AxType ty_unit = { .kind = AX_TY_UNIT };
    TypeId id_unit = ax_intern_type(&thir.interner, &ty_unit);
    AX_CHECK(ax_type_is_copy(id_unit, &thir, &str_in) == true);

    AxType ty_str = { .kind = AX_TY_STR };
    TypeId id_str = ax_intern_type(&thir.interner, &ty_str);
    AX_CHECK(ax_type_is_copy(id_str, &thir, &str_in) == false);

    // arrays
    AxType ty_array_copy = { .kind = AX_TY_ARRAY, .array = { .elem = thir.interner.t_u16, .len = 5 } };
    TypeId array_copy_id = ax_intern_type(&thir.interner, &ty_array_copy);
    AX_CHECK(ax_type_is_copy(array_copy_id, &thir, &str_in) == true);

    AxType ty_array_not_copy = { .kind = AX_TY_ARRAY, .array = { .elem = id_str, .len = 5 } };
    TypeId array_nc_id = ax_intern_type(&thir.interner, &ty_array_not_copy);
    AX_CHECK(ax_type_is_copy(array_nc_id, &thir, &str_in) == false);

    // tuples
    TypeId fields_c[] = { thir.interner.t_u8, thir.interner.t_u32 };
    AxType ty_tuple_copy = { .kind = AX_TY_TUPLE, .tuple = { .fields = fields_c, .field_count = 2 } };
    TypeId tuple_c_id = ax_intern_type(&thir.interner, &ty_tuple_copy);
    AX_CHECK(ax_type_is_copy(tuple_c_id, &thir, &str_in) == true);
    
    TypeId fields_nc[] = { thir.interner.t_u8, id_str };
    AxType ty_tuple_nc = { .kind = AX_TY_TUPLE, .tuple = { .fields = fields_nc, .field_count = 2 } };
    TypeId tuple_nc_id = ax_intern_type(&thir.interner, &ty_tuple_nc);
    AX_CHECK(ax_type_is_copy(tuple_nc_id, &thir, &str_in) == false);

    // structs
    AxHirItem struct_nc = { .kind = AX_HIR_ITEM_STRUCT, .attrs = NULL };
    AxType ty_struct_nc = { .kind = AX_TY_STRUCT, .strct = { .def = &struct_nc, .fields = NULL, .field_count = 0, .is_repr_c = false } };
    TypeId struct_nc_id = ax_intern_type(&thir.interner, &ty_struct_nc);
    AX_CHECK(ax_type_is_copy(struct_nc_id, &thir, &str_in) == false);

    AxHirAttrArg arg_copy = { .name = ax_intern_cstr(&str_in, "Copy"), .next = NULL };
    AxHirAttr attr_derive = { .name = ax_intern_cstr(&str_in, "derive"), .args = &arg_copy, .next = NULL };
    AxHirItem struct_c = { .kind = AX_HIR_ITEM_STRUCT, .attrs = &attr_derive };
    AxType ty_struct_c = { .kind = AX_TY_STRUCT, .strct = { .def = &struct_c, .fields = NULL, .field_count = 0, .is_repr_c = false } };
    TypeId struct_c_id = ax_intern_type(&thir.interner, &ty_struct_c);
    AX_CHECK(ax_type_is_copy(struct_c_id, &thir, &str_in) == true);

    ax_type_interner_free(&thir.interner);
    ax_interner_free(&str_in);
}
