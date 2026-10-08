#include "obj/coff/writer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint16_t Machine;
    uint16_t NumberOfSections;
    uint32_t TimeDateStamp;
    uint32_t PointerToSymbolTable;
    uint32_t NumberOfSymbols;
    uint16_t SizeOfOptionalHeader;
    uint16_t Characteristics;
} IMAGE_FILE_HEADER;

typedef struct {
    char Name[8];
    uint32_t VirtualSize;
    uint32_t VirtualAddress;
    uint32_t SizeOfRawData;
    uint32_t PointerToRawData;
    uint32_t PointerToRelocations;
    uint32_t PointerToLinenumbers;
    uint16_t NumberOfRelocations;
    uint16_t NumberOfLinenumbers;
    uint32_t Characteristics;
} IMAGE_SECTION_HEADER;

typedef struct {
    uint32_t VirtualAddress;
    uint32_t SymbolTableIndex;
    uint16_t Type;
} IMAGE_RELOCATION;

typedef struct {
    union {
        char ShortName[8];
        struct {
            uint32_t Zeroes;
            uint32_t Offset;
        } Name;
    } N;
    uint32_t Value;
    int16_t SectionNumber;
    uint16_t Type;
    uint8_t StorageClass;
    uint8_t NumberOfAuxSymbols;
} IMAGE_SYMBOL;

#define IMAGE_FILE_MACHINE_AMD64 0x8664

#define IMAGE_SCN_CNT_CODE 0x00000020
#define IMAGE_SCN_CNT_INITIALIZED_DATA 0x00000040
#define IMAGE_SCN_CNT_UNINITIALIZED_DATA 0x00000080
#define IMAGE_SCN_MEM_EXECUTE 0x20000000
#define IMAGE_SCN_MEM_READ 0x40000000
#define IMAGE_SCN_MEM_WRITE 0x80000000

#define IMAGE_SYM_CLASS_EXTERNAL 2
#define IMAGE_SYM_CLASS_STATIC 3

#define IMAGE_REL_AMD64_ADDR64 1
#define IMAGE_REL_AMD64_ADDR32 2
#define IMAGE_REL_AMD64_ADDR32NB 3
#define IMAGE_REL_AMD64_REL32 4

static uint32_t get_align_flag(uint32_t align) {
    switch (align) {
        case 1: return 0x00100000;
        case 2: return 0x00200000;
        case 4: return 0x00300000;
        case 8: return 0x00400000;
        case 16: return 0x00500000;
        case 32: return 0x00600000;
        case 64: return 0x00700000;
        default: return 0;
    }
}

bool ax_coff_write(ax_objmodel_t *obj, const char *path) {
    FILE *f = fopen(path, "wb");
    if (!f) return false;

    uint32_t num_sections = obj->sections.len;
    uint32_t num_symbols = obj->symbols.len;

    // Header sizes
    uint32_t size_of_headers = 20 + 40 * num_sections;
    
    // Layout sections
    uint32_t current_offset = size_of_headers;
    uint32_t *section_data_offsets = calloc(num_sections + 1, sizeof(uint32_t));
    uint32_t *section_reloc_offsets = calloc(num_sections + 1, sizeof(uint32_t));

    for (uint32_t i = 1; i <= num_sections; i++) {
        ax_section_id_t sid = {i};
        ax_section_t *sec = ax_objmodel_get_section(obj, sid);
        if (sec->bytes_len > 0) {
            section_data_offsets[i] = current_offset;
            current_offset += sec->bytes_len;
        }
        if (sec->relocs_len > 0) {
            section_reloc_offsets[i] = current_offset;
            current_offset += sec->relocs_len * 10;
        }
    }

    uint32_t symbol_table_offset = current_offset;

    // File header
    IMAGE_FILE_HEADER hdr = {0};
    hdr.Machine = IMAGE_FILE_MACHINE_AMD64;
    hdr.NumberOfSections = num_sections;
    hdr.PointerToSymbolTable = symbol_table_offset;
    hdr.NumberOfSymbols = num_symbols;
    
    fwrite(&hdr.Machine, 2, 1, f);
    fwrite(&hdr.NumberOfSections, 2, 1, f);
    fwrite(&hdr.TimeDateStamp, 4, 1, f);
    fwrite(&hdr.PointerToSymbolTable, 4, 1, f);
    fwrite(&hdr.NumberOfSymbols, 4, 1, f);
    fwrite(&hdr.SizeOfOptionalHeader, 2, 1, f);
    fwrite(&hdr.Characteristics, 2, 1, f);

    // Build string table
    uint32_t strtab_size = 4;
    for (uint32_t i = 1; i <= num_symbols; i++) {
        ax_symbol_id_t sym_id = {i};
        ax_symbol_t *sym = ax_objmodel_get_symbol(obj, sym_id);
        if (strlen(sym->name) > 8) {
            strtab_size += strlen(sym->name) + 1;
        }
    }

    // Section headers
    for (uint32_t i = 1; i <= num_sections; i++) {
        ax_section_id_t sid = {i};
        ax_section_t *sec = ax_objmodel_get_section(obj, sid);
        IMAGE_SECTION_HEADER shdr = {0};
        
        size_t name_len = strlen(sec->name);
        if (name_len <= 8) {
            strncpy(shdr.Name, sec->name, 8);
        } else {
            strncpy(shdr.Name, sec->name, 8);
        }
        
        uint32_t virtual_size = sec->bytes_len;
        if (sec->kind == AX_SEC_BSS) {
            for (uint32_t j = 1; j <= num_symbols; j++) {
                ax_symbol_id_t sym_id = {j};
                ax_symbol_t *sym = ax_objmodel_get_symbol(obj, sym_id);
                if (sym->section_id.v == sid.v) {
                    uint32_t end = (uint32_t)(sym->value + sym->size);
                    if (end > virtual_size) {
                        virtual_size = end;
                    }
                }
            }
            shdr.SizeOfRawData = virtual_size;
        } else {
            shdr.SizeOfRawData = sec->bytes_len;
        }
        shdr.PointerToRawData = section_data_offsets[i];
        shdr.PointerToRelocations = section_reloc_offsets[i];
        shdr.NumberOfRelocations = sec->relocs_len;
        
        uint32_t chars = get_align_flag(sec->align);
        if (sec->kind == AX_SEC_CODE) chars |= IMAGE_SCN_CNT_CODE;
        else if (sec->kind == AX_SEC_DATA || sec->kind == AX_SEC_RODATA) chars |= IMAGE_SCN_CNT_INITIALIZED_DATA;
        else if (sec->kind == AX_SEC_BSS) chars |= IMAGE_SCN_CNT_UNINITIALIZED_DATA;
        
        if (sec->flags & AX_SEC_FLAG_EXEC) chars |= IMAGE_SCN_MEM_EXECUTE;
        if (sec->flags & AX_SEC_FLAG_READ) chars |= IMAGE_SCN_MEM_READ;
        if (sec->flags & AX_SEC_FLAG_WRITE) chars |= IMAGE_SCN_MEM_WRITE;
        
        shdr.Characteristics = chars;
        
        fwrite(shdr.Name, 1, 8, f);
        fwrite(&shdr.VirtualSize, 4, 1, f);
        fwrite(&shdr.VirtualAddress, 4, 1, f);
        fwrite(&shdr.SizeOfRawData, 4, 1, f);
        fwrite(&shdr.PointerToRawData, 4, 1, f);
        fwrite(&shdr.PointerToRelocations, 4, 1, f);
        fwrite(&shdr.PointerToLinenumbers, 4, 1, f);
        fwrite(&shdr.NumberOfRelocations, 2, 1, f);
        fwrite(&shdr.NumberOfLinenumbers, 2, 1, f);
        fwrite(&shdr.Characteristics, 4, 1, f);
    }

    // Section data & relocations
    for (uint32_t i = 1; i <= num_sections; i++) {
        ax_section_id_t sid = {i};
        ax_section_t *sec = ax_objmodel_get_section(obj, sid);
        if (sec->bytes_len > 0) {
            // Apply addends for COFF inline relocation addends
            uint8_t *patched_bytes = malloc(sec->bytes_len);
            memcpy(patched_bytes, sec->bytes, sec->bytes_len);
            
            for (size_t r = 0; r < sec->relocs_len; r++) {
                ax_reloc_t *rel = &sec->relocs[r];
                if (rel->kind == AX_RELOC_X86_64_PC32 || rel->kind == AX_RELOC_X86_64_PLT32) {
                    int32_t addend32 = (int32_t)rel->addend;
                    memcpy(patched_bytes + rel->offset, &addend32, 4);
                } else if (rel->kind == AX_RELOC_X86_64_32 || rel->kind == AX_RELOC_X86_64_GOT32) {
                    int32_t addend32 = (int32_t)rel->addend;
                    memcpy(patched_bytes + rel->offset, &addend32, 4);
                } else if (rel->kind == AX_RELOC_X86_64_64) {
                    int64_t addend64 = rel->addend;
                    memcpy(patched_bytes + rel->offset, &addend64, 8);
                }
            }
            fwrite(patched_bytes, 1, sec->bytes_len, f);
            free(patched_bytes);
        }
        
        if (sec->relocs_len > 0) {
            for (size_t r = 0; r < sec->relocs_len; r++) {
                ax_reloc_t *rel = &sec->relocs[r];
                IMAGE_RELOCATION coff_rel = {0};
                coff_rel.VirtualAddress = rel->offset;
                coff_rel.SymbolTableIndex = rel->symbol_id.v - 1; // 0-based index
                
                if (rel->kind == AX_RELOC_X86_64_PC32 || rel->kind == AX_RELOC_X86_64_PLT32) {
                    coff_rel.Type = IMAGE_REL_AMD64_REL32;
                } else if (rel->kind == AX_RELOC_X86_64_64) {
                    coff_rel.Type = IMAGE_REL_AMD64_ADDR64;
                } else if (rel->kind == AX_RELOC_X86_64_32) {
                    coff_rel.Type = IMAGE_REL_AMD64_ADDR32NB;
                }
                
                fwrite(&coff_rel.VirtualAddress, 4, 1, f);
                fwrite(&coff_rel.SymbolTableIndex, 4, 1, f);
                fwrite(&coff_rel.Type, 2, 1, f);
            }
        }
    }

    // Symbol table
    uint32_t current_strtab_offset = 4;
    for (uint32_t i = 1; i <= num_symbols; i++) {
        ax_symbol_id_t sym_id = {i};
        ax_symbol_t *sym = ax_objmodel_get_symbol(obj, sym_id);
        IMAGE_SYMBOL sym_rec = {0};
        
        size_t len = strlen(sym->name);
        if (len <= 8) {
            strncpy(sym_rec.N.ShortName, sym->name, 8);
        } else {
            sym_rec.N.Name.Zeroes = 0;
            sym_rec.N.Name.Offset = current_strtab_offset;
            current_strtab_offset += len + 1;
        }
        
        sym_rec.Value = (uint32_t)sym->value;
        sym_rec.SectionNumber = sym->section_id.v == 0 ? 0 : (int16_t)sym->section_id.v;
        sym_rec.Type = 0;
        
        if (sym->linkage == AX_SYM_EXTERNAL) {
            sym_rec.StorageClass = IMAGE_SYM_CLASS_EXTERNAL;
        } else if (sym->linkage == AX_SYM_GLOBAL) {
            sym_rec.StorageClass = IMAGE_SYM_CLASS_EXTERNAL;
        } else {
            sym_rec.StorageClass = IMAGE_SYM_CLASS_STATIC;
        }
        
        sym_rec.NumberOfAuxSymbols = 0;
        
        fwrite(sym_rec.N.ShortName, 1, 8, f);
        fwrite(&sym_rec.Value, 4, 1, f);
        fwrite(&sym_rec.SectionNumber, 2, 1, f);
        fwrite(&sym_rec.Type, 2, 1, f);
        fwrite(&sym_rec.StorageClass, 1, 1, f);
        fwrite(&sym_rec.NumberOfAuxSymbols, 1, 1, f);
    }

    // String table
    fwrite(&strtab_size, 4, 1, f);
    for (uint32_t i = 1; i <= num_symbols; i++) {
        ax_symbol_id_t sym_id = {i};
        ax_symbol_t *sym = ax_objmodel_get_symbol(obj, sym_id);
        size_t len = strlen(sym->name);
        if (len > 8) {
            fwrite(sym->name, 1, len + 1, f);
        }
    }

    free(section_data_offsets);
    free(section_reloc_offsets);
    fclose(f);
    return true;
}
