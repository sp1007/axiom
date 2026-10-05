#ifndef AX_OBJMODEL_OBJMODEL_H
#define AX_OBJMODEL_OBJMODEL_H

#include "kernel/kernel.h"

AX_DEFINE_ID(ax_section_id_t);
AX_DEFINE_ID(ax_symbol_id_t);

typedef enum ax_section_kind {
    AX_SEC_CODE,
    AX_SEC_DATA,
    AX_SEC_RODATA,
    AX_SEC_BSS
} ax_section_kind_t;

typedef enum ax_section_flags {
    AX_SEC_FLAG_NONE = 0,
    AX_SEC_FLAG_EXEC = 1 << 0,
    AX_SEC_FLAG_WRITE = 1 << 1,
    AX_SEC_FLAG_READ = 1 << 2
} ax_section_flags_t;

typedef enum ax_reloc_kind {
    AX_RELOC_NONE,
    AX_RELOC_X86_64_PC32,
    AX_RELOC_X86_64_32,
    AX_RELOC_X86_64_64,
    AX_RELOC_X86_64_GOT32,
    AX_RELOC_X86_64_PLT32
} ax_reloc_kind_t;

typedef struct ax_reloc {
    uint32_t offset;
    ax_reloc_kind_t kind;
    ax_symbol_id_t symbol_id;
    int64_t addend;
} ax_reloc_t;

typedef struct ax_section {
    ax_section_id_t id;
    const char *name;
    ax_section_kind_t kind;
    uint32_t flags;
    uint32_t align;
    uint8_t *bytes;
    size_t bytes_len;
    size_t bytes_cap;
    ax_reloc_t *relocs;
    size_t relocs_len;
    size_t relocs_cap;
} ax_section_t;

AX_DEFINE_ID_TABLE(ax_section_table_t, ax_section_id_t, ax_section_t);

typedef enum ax_symbol_linkage {
    AX_SYM_LOCAL,
    AX_SYM_GLOBAL,
    AX_SYM_EXTERNAL
} ax_symbol_linkage_t;

typedef struct ax_symbol {
    ax_symbol_id_t id;
    const char *name;
    ax_section_id_t section_id; /* None if external/absolute */
    uint64_t value;             /* offset in section, or absolute value */
    uint64_t size;
    ax_symbol_linkage_t linkage;
} ax_symbol_t;

AX_DEFINE_ID_TABLE(ax_symbol_table_t, ax_symbol_id_t, ax_symbol_t);

typedef struct ax_objmodel {
    ax_section_table_t sections;
    ax_symbol_table_t symbols;
} ax_objmodel_t;

void ax_objmodel_init(ax_objmodel_t *obj);
void ax_objmodel_free(ax_objmodel_t *obj);

ax_section_id_t ax_objmodel_add_section(ax_objmodel_t *obj, const char *name, ax_section_kind_t kind, uint32_t flags, uint32_t align);
ax_section_t *ax_objmodel_get_section(ax_objmodel_t *obj, ax_section_id_t id);
void ax_section_add_byte(ax_section_t *sec, uint8_t byte);
void ax_section_add_bytes(ax_section_t *sec, const uint8_t *bytes, size_t len);
void ax_section_add_reloc(ax_section_t *sec, uint32_t offset, ax_reloc_kind_t kind, ax_symbol_id_t symbol_id, int64_t addend);

ax_symbol_id_t ax_objmodel_add_symbol(ax_objmodel_t *obj, const char *name, ax_section_id_t section_id, uint64_t value, uint64_t size, ax_symbol_linkage_t linkage);
ax_symbol_t *ax_objmodel_get_symbol(ax_objmodel_t *obj, ax_symbol_id_t id);

#endif /* AX_OBJMODEL_OBJMODEL_H */
