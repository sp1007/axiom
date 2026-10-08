#include "linker.h"
#include "pe_defs.h"
#include "diag/diag.h"
#include "kernel/base.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ALIGN_UP(val, align) (((val) + ((align) - 1)) & ~((align) - 1))

typedef struct {
    char name[9];
    uint32_t characteristics;
    uint8_t *data;
    uint32_t size;
    uint32_t cap;
    uint32_t rva;
    uint32_t raw_ptr;
} MergedSection;

typedef struct {
    char *name;
    MergedSection *sec;
    uint32_t offset;
    bool defined;
} GlobalSymbol;

typedef struct {
    MergedSection *sec;
    uint32_t offset;
    uint16_t type;
    char *sym_name;
    int64_t addend; // read from the object file data
} Reloc;

typedef struct {
    MergedSection *sections[64];
    size_t num_sections;
    GlobalSymbol *globals;
    size_t num_globals;
    size_t cap_globals;
    Reloc *relocs;
    size_t num_relocs;
    size_t cap_relocs;
} LinkerContext;

static char *ax_xstrdup(const char *s) {
    size_t l = strlen(s);
    char *r = ax_xmalloc(l + 1);
    memcpy(r, s, l + 1);
    return r;
}

static void free_linker_context(LinkerContext *ctx) {
    for (size_t i = 0; i < ctx->num_sections; i++) {
        ax_xfree(ctx->sections[i]->data);
        ax_xfree(ctx->sections[i]);
    }
    
    for (size_t i = 0; i < ctx->num_globals; i++) {
        ax_xfree(ctx->globals[i].name);
    }
    if (ctx->globals) ax_xfree(ctx->globals);
    
    for (size_t i = 0; i < ctx->num_relocs; i++) {
        ax_xfree(ctx->relocs[i].sym_name);
    }
    if (ctx->relocs) ax_xfree(ctx->relocs);
}

static MergedSection *get_or_create_section(LinkerContext *ctx, const char *name, uint32_t chars) {
    for (size_t i = 0; i < ctx->num_sections; i++) {
        if (strcmp(ctx->sections[i]->name, name) == 0) {
            ctx->sections[i]->characteristics |= chars;
            return ctx->sections[i];
        }
    }
    MergedSection *sec = ax_xcalloc(1, sizeof(MergedSection));
    ctx->sections[ctx->num_sections++] = sec;
    strncpy(sec->name, name, 8);
    sec->characteristics = chars;
    return sec;
}

static void append_section_data(MergedSection *sec, const uint8_t *data, uint32_t size, uint32_t align, uint32_t *out_offset) {
    uint32_t offset = ALIGN_UP(sec->size, align);
    uint32_t new_size = offset + size;
    if (new_size > sec->cap) {
        uint32_t new_cap = sec->cap == 0 ? 1024 : sec->cap;
        while (new_cap < new_size) new_cap *= 2;
        sec->data = ax_xrealloc(sec->data, new_cap);
        sec->cap = new_cap;
    }
    memset(sec->data + sec->size, 0, offset - sec->size);
    if (data) {
        memcpy(sec->data + offset, data, size);
    } else {
        memset(sec->data + offset, 0, size);
    }
    sec->size = new_size;
    if (out_offset) *out_offset = offset;
}

static GlobalSymbol *add_global(LinkerContext *ctx, const char *name) {
    for (size_t i = 0; i < ctx->num_globals; i++) {
        if (strcmp(ctx->globals[i].name, name) == 0) return &ctx->globals[i];
    }
    if (ctx->num_globals == ctx->cap_globals) {
        ctx->cap_globals = ctx->cap_globals == 0 ? 64 : ctx->cap_globals * 2;
        ctx->globals = ax_xrealloc(ctx->globals, ctx->cap_globals * sizeof(GlobalSymbol));
    }
    GlobalSymbol *sym = &ctx->globals[ctx->num_globals++];
    sym->name = ax_xstrdup(name);
    sym->sec = NULL;
    sym->offset = 0;
    sym->defined = false;
    return sym;
}

static void add_reloc(LinkerContext *ctx, MergedSection *sec, uint32_t offset, uint16_t type, const char *sym_name, int64_t addend) {
    if (ctx->num_relocs == ctx->cap_relocs) {
        ctx->cap_relocs = ctx->cap_relocs == 0 ? 64 : ctx->cap_relocs * 2;
        ctx->relocs = ax_xrealloc(ctx->relocs, ctx->cap_relocs * sizeof(Reloc));
    }
    Reloc *r = &ctx->relocs[ctx->num_relocs++];
    r->sec = sec;
    r->offset = offset;
    r->type = type;
    r->sym_name = ax_xstrdup(sym_name);
    r->addend = addend;
}

static char *read_string(FILE *f, uint32_t offset) {
    long pos = ftell(f);
    fseek(f, offset, SEEK_SET);
    size_t len = 0;
    while (fgetc(f) != '\0') len++;
    char *str = ax_xmalloc(len + 1);
    fseek(f, offset, SEEK_SET);
    fread(str, 1, len + 1, f);
    fseek(f, pos, SEEK_SET);
    return str;
}

bool ax_pe_link(const char *const *input_paths, size_t input_count, const char *output_path, uint32_t stack_reserve, AxDiagSink *diag) {
    LinkerContext ctx = {0};
    if (stack_reserve == 0) stack_reserve = 0x100000;
    
    // Parse objects
    for (size_t i = 0; i < input_count; i++) {
        FILE *f = fopen(input_paths[i], "rb");
        if (!f) {
            if (diag) ax_diag_sink_report(diag, &(AxDiagnostic){.code=AX_LINK_BAD_OBJECT, .severity=AX_DIAG_ERROR, .message="bad object"});
            { free_linker_context(&ctx); return false; }
        }
        
        IMAGE_FILE_HEADER hdr;
        if (fread(&hdr, sizeof(hdr), 1, f) != 1 || hdr.Machine != IMAGE_FILE_MACHINE_AMD64) {
            fclose(f);
            if (diag) ax_diag_sink_report(diag, &(AxDiagnostic){.code=AX_LINK_BAD_OBJECT, .severity=AX_DIAG_ERROR, .message="bad object"});
            { free_linker_context(&ctx); return false; }
        }
        
        IMAGE_SECTION_HEADER *shdrs = ax_xmalloc(hdr.NumberOfSections * sizeof(IMAGE_SECTION_HEADER));
        fread(shdrs, sizeof(IMAGE_SECTION_HEADER), hdr.NumberOfSections, f);
        
        uint32_t str_table_offset = hdr.PointerToSymbolTable + hdr.NumberOfSymbols * 18;
        
        MergedSection **obj_merged_secs = ax_xmalloc((hdr.NumberOfSections + 1) * sizeof(MergedSection*));
        uint32_t *obj_sec_offsets = ax_xmalloc((hdr.NumberOfSections + 1) * sizeof(uint32_t));
        
        obj_merged_secs[0] = NULL;
        obj_sec_offsets[0] = 0;
        
        for (uint16_t s = 0; s < hdr.NumberOfSections; s++) {
            char name[9] = {0};
            if (shdrs[s].Name[0] == '/') {
                uint32_t str_off = atoi((char*)shdrs[s].Name + 1);
                char *str = read_string(f, str_table_offset + str_off);
                strncpy(name, str, 8);
                ax_xfree(str);
            } else {
                strncpy(name, (char*)shdrs[s].Name, 8);
            }
            
            MergedSection *msec = get_or_create_section(&ctx, name, shdrs[s].Characteristics);
            obj_merged_secs[s + 1] = msec;
            
            uint8_t *data = NULL;
            if (shdrs[s].SizeOfRawData > 0) {
                data = ax_xmalloc(shdrs[s].SizeOfRawData);
                long pos = ftell(f);
                fseek(f, shdrs[s].PointerToRawData, SEEK_SET);
                fread(data, 1, shdrs[s].SizeOfRawData, f);
                fseek(f, pos, SEEK_SET);
            }
            
            uint32_t align = 1;
            uint32_t align_flag = (shdrs[s].Characteristics & 0x00F00000) >> 20;
            if (align_flag > 0) align = 1 << (align_flag - 1);
            
            uint32_t offset = 0;
            append_section_data(msec, data, shdrs[s].SizeOfRawData, align, &offset);
            obj_sec_offsets[s + 1] = offset;
            if (data) ax_xfree(data);
        }
        
        char **sym_names = ax_xmalloc(hdr.NumberOfSymbols * sizeof(char*));
        MergedSection **sym_secs = ax_xmalloc(hdr.NumberOfSymbols * sizeof(MergedSection*));
        uint32_t *sym_offsets = ax_xmalloc(hdr.NumberOfSymbols * sizeof(uint32_t));
        
        fseek(f, hdr.PointerToSymbolTable, SEEK_SET);
        for (uint32_t s = 0; s < hdr.NumberOfSymbols; s++) {
            IMAGE_SYMBOL sym;
            fread(&sym, sizeof(sym), 1, f);
            
            char *name = NULL;
            if (sym.N.Name.Zeroes == 0) {
                name = read_string(f, str_table_offset + sym.N.Name.Offset);
            } else {
                name = ax_xmalloc(9);
                strncpy(name, (char*)sym.N.ShortName, 8);
                name[8] = '\0';
            }
            sym_names[s] = name;
            
            if (sym.SectionNumber > 0) {
                sym_secs[s] = obj_merged_secs[sym.SectionNumber];
                sym_offsets[s] = obj_sec_offsets[sym.SectionNumber] + sym.Value;
                
                if (sym.StorageClass == IMAGE_SYM_CLASS_EXTERNAL) {
                    GlobalSymbol *g = add_global(&ctx, name);
                    if (g->defined) {
                        char msg[256]; snprintf(msg, sizeof(msg), "duplicate symbol: %s", name);
                        if (diag) ax_diag_sink_report(diag, &(AxDiagnostic){.code=AX_LINK_DUPLICATE_SYMBOL, .severity=AX_DIAG_ERROR, .message=ax_xstrdup(msg)});
                        
                        ax_xfree(name);
                        for (uint32_t clean_s = 0; clean_s < s; clean_s++) {
                            if (sym_names[clean_s]) ax_xfree(sym_names[clean_s]);
                        }
                        ax_xfree(sym_names); ax_xfree(sym_secs); ax_xfree(sym_offsets);
                        ax_xfree(obj_merged_secs); ax_xfree(obj_sec_offsets); ax_xfree(shdrs);
                        fclose(f);

                        { free_linker_context(&ctx); return false; }
                    }
                    g->defined = true;
                    g->sec = sym_secs[s];
                    g->offset = sym_offsets[s];
                }
            } else {
                sym_secs[s] = NULL;
                sym_offsets[s] = 0;
            }
            
            for (uint8_t a = 0; a < sym.NumberOfAuxSymbols; a++) {
                IMAGE_SYMBOL aux;
                fread(&aux, sizeof(aux), 1, f);
                sym_names[s + 1 + a] = NULL;
            }
            s += sym.NumberOfAuxSymbols;
        }
        
        // Relocations
        for (uint16_t s = 0; s < hdr.NumberOfSections; s++) {
            if (shdrs[s].NumberOfRelocations == 0) continue;
            IMAGE_RELOCATION *rels = ax_xmalloc(shdrs[s].NumberOfRelocations * sizeof(IMAGE_RELOCATION));
            long pos = ftell(f);
            fseek(f, shdrs[s].PointerToRelocations, SEEK_SET);
            fread(rels, sizeof(IMAGE_RELOCATION), shdrs[s].NumberOfRelocations, f);
            fseek(f, pos, SEEK_SET);
            
            MergedSection *msec = obj_merged_secs[s + 1];
            uint32_t msec_base = obj_sec_offsets[s + 1];
            
            for (uint16_t r = 0; r < shdrs[s].NumberOfRelocations; r++) {
                uint32_t off = msec_base + rels[r].VirtualAddress;
                int64_t addend = 0;
                if (rels[r].Type == IMAGE_REL_AMD64_ADDR64) {
                    memcpy(&addend, msec->data + off, 8);
                } else {
                    int32_t addend32 = 0;
                    memcpy(&addend32, msec->data + off, 4);
                    addend = addend32;
                }
                char *sym_name = sym_names[rels[r].SymbolTableIndex];
                add_reloc(&ctx, msec, off, rels[r].Type, sym_name, addend);
            }
            ax_xfree(rels);
        }
        
        for (uint32_t s = 0; s < hdr.NumberOfSymbols; s++) {
            if (sym_names[s]) ax_xfree(sym_names[s]);
        }
        ax_xfree(sym_names); ax_xfree(sym_secs); ax_xfree(sym_offsets);
        ax_xfree(obj_merged_secs); ax_xfree(obj_sec_offsets); ax_xfree(shdrs);
        fclose(f);
    }
    
    // Add axiom_start
    MergedSection *text_sec = get_or_create_section(&ctx, ".text", IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ);
    uint32_t axiom_start_offset = 0;
    uint8_t start_code[] = {
        0x48, 0x83, 0xEC, 0x28,       // sub rsp, 40
        0xE8, 0x00, 0x00, 0x00, 0x00, // call main
        0x8B, 0xC8,                   // mov ecx, eax
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, // call [rip + IAT_ExitProcess]
        0xCC                          // int3
    };
    append_section_data(text_sec, start_code, sizeof(start_code), 16, &axiom_start_offset);
    add_reloc(&ctx, text_sec, axiom_start_offset + 5, IMAGE_REL_AMD64_REL32, "main", -4);
    
    uint8_t panic_code[] = {
        0x56, 0x53, 0x48, 0x83, 0xEC, 0x48, 0x48, 0x89, 0xCB, 0xB9, 0xF4, 0xFF, 0xFF, 0xFF, 0x48, 0x89, 0xD6,
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00,
        0x4C, 0x8D, 0x4C, 0x24, 0x38, 0x49, 0x89, 0xF0, 0x48, 0x89, 0xDA, 0x48, 0xC7, 0x44, 0x24, 0x20, 0x00, 0x00, 0x00, 0x00, 0x48, 0x89, 0xC1,
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00,
        0xB9, 0x65, 0x00, 0x00, 0x00,
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00,
        0xCC
    };
    uint32_t panic_offset;
    append_section_data(text_sec, panic_code, sizeof(panic_code), 16, &panic_offset);
    add_reloc(&ctx, text_sec, panic_offset + 19, IMAGE_REL_AMD64_REL32, "__IAT_GetStdHandle", -4);
    add_reloc(&ctx, text_sec, panic_offset + 48, IMAGE_REL_AMD64_REL32, "__IAT_WriteFile", -4);
    add_reloc(&ctx, text_sec, panic_offset + 59, IMAGE_REL_AMD64_REL32, "__IAT_ExitProcess", -4);
    
    GlobalSymbol *panic_sym = add_global(&ctx, "axiom_panic");
    panic_sym->defined = true; panic_sym->sec = text_sec; panic_sym->offset = panic_offset;
    
    // Build Import Directory
    MergedSection *idata_sec = get_or_create_section(&ctx, ".idata", IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE);
    uint32_t idata_base = 0;
    
    uint8_t idata_buf[256] = {0};
    uint32_t i_off = 0;
    
    IMAGE_IMPORT_DESCRIPTOR desc = {0};
    uint32_t desc_offset = i_off;
    memcpy(idata_buf + i_off, &desc, 20); i_off += 20; // desc kernel32
    memset(idata_buf + i_off, 0, 20); i_off += 20;     // desc null
    
    uint32_t ilt_offset = i_off;
    i_off += 32; // ILT (4x qword)
    uint32_t iat_offset = i_off;
    i_off += 32; // IAT (4x qword)

    uint32_t hint_exit = i_off;
    idata_buf[i_off++] = 0; idata_buf[i_off++] = 0;
    strcpy((char*)idata_buf + i_off, "ExitProcess"); i_off += 12;
    uint32_t hint_getstd = i_off;
    idata_buf[i_off++] = 0; idata_buf[i_off++] = 0;
    strcpy((char*)idata_buf + i_off, "GetStdHandle"); i_off += 13;
    uint32_t hint_write = i_off;
    idata_buf[i_off++] = 0; idata_buf[i_off++] = 0;
    strcpy((char*)idata_buf + i_off, "WriteFile"); i_off += 10;

    uint32_t dll_name_offset = i_off;
    strcpy((char*)idata_buf + i_off, "KERNEL32.dll"); i_off += 13;
    i_off = ALIGN_UP(i_off, 8);
    
    append_section_data(idata_sec, idata_buf, i_off, 8, &idata_base);
    
    // RVA assignment (Layout)
    uint32_t file_align = 0x200;
    uint32_t sec_align = 0x1000;
    uint32_t current_rva = sec_align;
    uint32_t current_raw = ALIGN_UP(64 + 4 + 20 + 240 + ctx.num_sections * 40, file_align);
    
    for (size_t i = 0; i < ctx.num_sections; i++) {
        ctx.sections[i]->rva = current_rva;
        ctx.sections[i]->raw_ptr = current_raw;
        current_rva = ALIGN_UP(current_rva + ctx.sections[i]->size, sec_align);
        current_raw = ALIGN_UP(current_raw + ctx.sections[i]->size, file_align);
    }
    
    text_sec = get_or_create_section(&ctx, ".text", 0);
    idata_sec = get_or_create_section(&ctx, ".idata", 0);

    // Now we know RVAs, patch idata
    uint32_t idata_rva = idata_sec->rva + idata_base;
    IMAGE_IMPORT_DESCRIPTOR *pdesc = (IMAGE_IMPORT_DESCRIPTOR*)(idata_sec->data + idata_base + desc_offset);
    pdesc->OriginalFirstThunk = idata_rva + ilt_offset;
    pdesc->Name = idata_rva + dll_name_offset;
    pdesc->FirstThunk = idata_rva + iat_offset;
    
    uint64_t rva_exit = idata_rva + hint_exit;
    uint64_t rva_getstd = idata_rva + hint_getstd;
    uint64_t rva_write = idata_rva + hint_write;

    memcpy(idata_sec->data + idata_base + ilt_offset, &rva_exit, 8);
    memcpy(idata_sec->data + idata_base + ilt_offset + 8, &rva_getstd, 8);
    memcpy(idata_sec->data + idata_base + ilt_offset + 16, &rva_write, 8);

    memcpy(idata_sec->data + idata_base + iat_offset, &rva_exit, 8);
    memcpy(idata_sec->data + idata_base + iat_offset + 8, &rva_getstd, 8);
    memcpy(idata_sec->data + idata_base + iat_offset + 16, &rva_write, 8);
    
    // Reloc for call [rip + IAT_ExitProcess]
    uint32_t call_exit_offset = axiom_start_offset + 13;
    add_reloc(&ctx, text_sec, call_exit_offset, IMAGE_REL_AMD64_REL32, "__IAT_ExitProcess", -4);
    
    GlobalSymbol *iat_exit = add_global(&ctx, "__IAT_ExitProcess");
    iat_exit->defined = true; iat_exit->sec = idata_sec; iat_exit->offset = idata_base + iat_offset;
    
    GlobalSymbol *iat_getstd = add_global(&ctx, "__IAT_GetStdHandle");
    iat_getstd->defined = true; iat_getstd->sec = idata_sec; iat_getstd->offset = idata_base + iat_offset + 8;

    GlobalSymbol *iat_write = add_global(&ctx, "__IAT_WriteFile");
    iat_write->defined = true; iat_write->sec = idata_sec; iat_write->offset = idata_base + iat_offset + 16;

    
    // Apply relocations
    for (size_t i = 0; i < ctx.num_relocs; i++) {
        Reloc *r = &ctx.relocs[i];
        GlobalSymbol *sym = add_global(&ctx, r->sym_name);
        if (!sym->defined) {
            if (diag) ax_diag_sink_report(diag, &(AxDiagnostic){.code=AX_LINK_UNDEFINED_SYMBOL, .severity=AX_DIAG_ERROR, .message="undefined symbol"});
            { free_linker_context(&ctx); return false; }
        }
        
        uint32_t sym_rva = sym->sec->rva + sym->offset;
        uint32_t reloc_rva = r->sec->rva + r->offset;
        
        if (r->type == IMAGE_REL_AMD64_REL32 || (r->type >= IMAGE_REL_AMD64_REL32_1 && r->type <= IMAGE_REL_AMD64_REL32_5)) {
            int64_t val = (int64_t)sym_rva - (int64_t)reloc_rva + r->addend;
            int32_t val32 = (int32_t)val;
            memcpy(r->sec->data + r->offset, &val32, 4);
        } else if (r->type == IMAGE_REL_AMD64_ADDR64) {
            uint64_t val = 0x140000000ULL + sym_rva + r->addend;
            memcpy(r->sec->data + r->offset, &val, 8);
        } else if (r->type == IMAGE_REL_AMD64_ADDR32NB) {
            int32_t val32 = sym_rva + r->addend;
            memcpy(r->sec->data + r->offset, &val32, 4);
        }
    }
    
    // Write PE file
    FILE *out = fopen(output_path, "wb");
    if (!out) { free_linker_context(&ctx); return false; }
    
    // DOS Header
    uint8_t dos[64] = {0};
    dos[0] = 'M'; dos[1] = 'Z';
    dos[0x3C] = 64; // e_lfanew
    fwrite(dos, 1, 64, out);
    
    // PE Signature
    fwrite("PE\0\0", 1, 4, out);
    
    IMAGE_FILE_HEADER fhdr = {0};
    fhdr.Machine = IMAGE_FILE_MACHINE_AMD64;
    fhdr.NumberOfSections = ctx.num_sections;
    fhdr.SizeOfOptionalHeader = 240;
    fhdr.Characteristics = IMAGE_FILE_EXECUTABLE_IMAGE | IMAGE_FILE_LARGE_ADDRESS_AWARE | IMAGE_FILE_DEBUG_STRIPPED;
    fwrite(&fhdr, sizeof(fhdr), 1, out);
    
    IMAGE_OPTIONAL_HEADER64 ohdr = {0};
    ohdr.Magic = 0x020B;
    ohdr.AddressOfEntryPoint = text_sec->rva + axiom_start_offset;
    ohdr.ImageBase = 0x140000000ULL;
    ohdr.SectionAlignment = sec_align;
    ohdr.FileAlignment = file_align;
    ohdr.MajorOperatingSystemVersion = 6;
    ohdr.MajorSubsystemVersion = 6;
    ohdr.SizeOfImage = current_rva;
    ohdr.SizeOfHeaders = ALIGN_UP(64 + 4 + 20 + 240 + ctx.num_sections * 40, file_align);
    ohdr.Subsystem = IMAGE_SUBSYSTEM_WINDOWS_CUI;
    ohdr.DllCharacteristics = IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA | IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE | IMAGE_DLLCHARACTERISTICS_NX_COMPAT | IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE;
    ohdr.SizeOfStackReserve = stack_reserve;
    ohdr.SizeOfStackCommit = 0x1000;
    ohdr.SizeOfHeapReserve = 0x100000;
    ohdr.SizeOfHeapCommit = 0x1000;
    ohdr.NumberOfRvaAndSizes = 16;
    
    ohdr.SizeOfCode = text_sec->size;
    ohdr.BaseOfCode = text_sec->rva;
    
    ohdr.SizeOfInitializedData = 0; // approximate
    for (size_t i = 0; i < ctx.num_sections; i++) {
        if (ctx.sections[i]->characteristics & IMAGE_SCN_CNT_INITIALIZED_DATA) {
            ohdr.SizeOfInitializedData += ctx.sections[i]->size;
        }
    }
    
    fwrite(&ohdr, sizeof(ohdr), 1, out);
    
    // Write Data Directories (16)
    IMAGE_DATA_DIRECTORY dirs[16] = {0};
    dirs[1].VirtualAddress = idata_sec->rva + idata_base + desc_offset;
    dirs[1].Size = 40; // 2 descriptors
    dirs[12].VirtualAddress = idata_sec->rva + idata_base + iat_offset;
    dirs[12].Size = 32; // 3 imports + null
    fwrite(dirs, sizeof(IMAGE_DATA_DIRECTORY), 16, out);
    
    // Write Section Headers
    for (size_t i = 0; i < ctx.num_sections; i++) {
        IMAGE_SECTION_HEADER shdr = {0};
        strncpy((char*)shdr.Name, ctx.sections[i]->name, 8);
        shdr.VirtualSize = ctx.sections[i]->size;
        shdr.VirtualAddress = ctx.sections[i]->rva;
        shdr.SizeOfRawData = ALIGN_UP(ctx.sections[i]->size, file_align);
        if (shdr.SizeOfRawData > 0) shdr.PointerToRawData = ctx.sections[i]->raw_ptr;
        shdr.Characteristics = ctx.sections[i]->characteristics;
        fwrite(&shdr, sizeof(shdr), 1, out);
    }
    
    // Write section data
    for (size_t i = 0; i < ctx.num_sections; i++) {
        if (ctx.sections[i]->size > 0) {
            fseek(out, ctx.sections[i]->raw_ptr, SEEK_SET);
            fwrite(ctx.sections[i]->data, 1, ctx.sections[i]->size, out);
            uint32_t padding = ALIGN_UP(ctx.sections[i]->size, file_align) - ctx.sections[i]->size;
            if (padding > 0) {
                uint8_t *pad = ax_xcalloc(1, padding);
                fwrite(pad, 1, padding, out);
                ax_xfree(pad);
            }
        }
    }
    
    fclose(out);
    { free_linker_context(&ctx); return true; }
}
