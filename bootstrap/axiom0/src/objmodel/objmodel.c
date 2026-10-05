#include "objmodel/objmodel.h"

void ax_objmodel_init(ax_objmodel_t *obj) {
    ax_section_table_t_init(&obj->sections);
    ax_symbol_table_t_init(&obj->symbols);
}

void ax_objmodel_free(ax_objmodel_t *obj) {
    for (ax_section_id_t id = ax_section_table_t_first(&obj->sections);
         ax_section_id_t_is_some(id);
         id = ax_section_table_t_after(&obj->sections, id)) {
        ax_section_t *sec = ax_section_table_t_get(&obj->sections, id);
        ax_xfree(sec->bytes);
        ax_xfree(sec->relocs);
    }
    ax_section_table_t_free(&obj->sections);
    ax_symbol_table_t_free(&obj->symbols);
}

ax_section_id_t ax_objmodel_add_section(ax_objmodel_t *obj, const char *name, ax_section_kind_t kind, uint32_t flags, uint32_t align) {
    ax_section_t sec = {0};
    sec.name = name;
    sec.kind = kind;
    sec.flags = flags;
    sec.align = align;
    ax_section_id_t id = ax_section_table_t_push(&obj->sections, sec);
    ax_section_table_t_get(&obj->sections, id)->id = id;
    return id;
}

ax_section_t *ax_objmodel_get_section(ax_objmodel_t *obj, ax_section_id_t id) {
    return ax_section_table_t_get(&obj->sections, id);
}

void ax_section_add_byte(ax_section_t *sec, uint8_t byte) {
    if (sec->bytes_len == sec->bytes_cap) {
        sec->bytes = (uint8_t *)ax_grow_array(sec->bytes, &sec->bytes_cap, sizeof(uint8_t), sec->bytes_len + 1);
    }
    sec->bytes[sec->bytes_len++] = byte;
}

void ax_section_add_bytes(ax_section_t *sec, const uint8_t *bytes, size_t len) {
    if (sec->bytes_len + len > sec->bytes_cap) {
        sec->bytes = (uint8_t *)ax_grow_array(sec->bytes, &sec->bytes_cap, sizeof(uint8_t), sec->bytes_len + len);
    }
    for (size_t i = 0; i < len; i++) {
        sec->bytes[sec->bytes_len++] = bytes[i];
    }
}

void ax_section_add_reloc(ax_section_t *sec, uint32_t offset, ax_reloc_kind_t kind, ax_symbol_id_t symbol_id, int64_t addend) {
    if (sec->relocs_len == sec->relocs_cap) {
        sec->relocs = (ax_reloc_t *)ax_grow_array(sec->relocs, &sec->relocs_cap, sizeof(ax_reloc_t), sec->relocs_len + 1);
    }
    ax_reloc_t *r = &sec->relocs[sec->relocs_len++];
    r->offset = offset;
    r->kind = kind;
    r->symbol_id = symbol_id;
    r->addend = addend;
}

ax_symbol_id_t ax_objmodel_add_symbol(ax_objmodel_t *obj, const char *name, ax_section_id_t section_id, uint64_t value, uint64_t size, ax_symbol_linkage_t linkage) {
    ax_symbol_t sym = {0};
    sym.name = name;
    sym.section_id = section_id;
    sym.value = value;
    sym.size = size;
    sym.linkage = linkage;
    ax_symbol_id_t id = ax_symbol_table_t_push(&obj->symbols, sym);
    ax_symbol_table_t_get(&obj->symbols, id)->id = id;
    return id;
}

ax_symbol_t *ax_objmodel_get_symbol(ax_objmodel_t *obj, ax_symbol_id_t id) {
    return ax_symbol_table_t_get(&obj->symbols, id);
}
