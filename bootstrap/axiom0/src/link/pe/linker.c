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
    char *sym_name;  // NULL when the target is defined in the same object (bound by symbol index)
    MergedSection *dsec;  // same-object target (ADR-0035 section 2): section + offset, no name lookup
    uint32_t doffset;
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

#ifdef _WIN32
#define ax_stricmp _stricmp
#else
#include <strings.h>
#define ax_stricmp strcasecmp
#endif

typedef struct ImportFunc {
    char *name;
    char *full_sym;
    uint32_t hint_offset;
    uint32_t iat_offset;
    uint32_t thunk_offset;
} ImportFunc;

typedef struct ImportDll {
    char *dll_name;
    ImportFunc *funcs;
    size_t num_funcs;
    size_t cap_funcs;
    uint32_t desc_offset;
    uint32_t ilt_offset;
    uint32_t iat_offset;
    uint32_t dll_name_offset;
} ImportDll;

static char *ax_xstrdup(const char *s) {
    size_t l = strlen(s);
    char *r = ax_xmalloc(l + 1);
    memcpy(r, s, l + 1);
    return r;
}

static void free_import_dlls(ImportDll *dlls, size_t num_dlls) {
    if (!dlls) return;
    for (size_t d = 0; d < num_dlls; d++) {
        for (size_t f = 0; f < dlls[d].num_funcs; f++) {
            if (dlls[d].funcs[f].name) ax_xfree(dlls[d].funcs[f].name);
            if (dlls[d].funcs[f].full_sym) ax_xfree(dlls[d].funcs[f].full_sym);
        }
        if (dlls[d].funcs) ax_xfree(dlls[d].funcs);
        if (dlls[d].dll_name) ax_xfree(dlls[d].dll_name);
    }
    ax_xfree(dlls);
}

static ImportDll *find_or_add_dll(ImportDll **dlls, size_t *num_dlls, size_t *cap_dlls, const char *name) {
    char norm[256];
    size_t len = strlen(name);
    if (len >= 4 && (ax_stricmp(name + len - 4, ".dll") == 0)) {
        snprintf(norm, sizeof(norm), "%s", name);
    } else {
        snprintf(norm, sizeof(norm), "%s.dll", name);
    }
    if (ax_stricmp(norm, "kernel32.dll") == 0) {
        strcpy(norm, "KERNEL32.dll");
    }

    for (size_t i = 0; i < *num_dlls; i++) {
        if (ax_stricmp((*dlls)[i].dll_name, norm) == 0) {
            return &(*dlls)[i];
        }
    }

    if (*num_dlls == *cap_dlls) {
        *cap_dlls = *cap_dlls == 0 ? 8 : (*cap_dlls * 2);
        *dlls = ax_xrealloc(*dlls, *cap_dlls * sizeof(ImportDll));
    }
    ImportDll *d = &(*dlls)[(*num_dlls)++];
    memset(d, 0, sizeof(*d));
    d->dll_name = ax_xstrdup(norm);
    return d;
}

static ImportFunc *add_import_func(ImportDll *dll, const char *func_name, const char *full_sym) {
    for (size_t i = 0; i < dll->num_funcs; i++) {
        if (strcmp(dll->funcs[i].name, func_name) == 0) {
            if (!dll->funcs[i].full_sym && full_sym) {
                dll->funcs[i].full_sym = ax_xstrdup(full_sym);
            }
            return &dll->funcs[i];
        }
    }
    if (dll->num_funcs == dll->cap_funcs) {
        dll->cap_funcs = dll->cap_funcs == 0 ? 16 : (dll->cap_funcs * 2);
        dll->funcs = ax_xrealloc(dll->funcs, dll->cap_funcs * sizeof(ImportFunc));
    }
    ImportFunc *f = &dll->funcs[dll->num_funcs++];
    memset(f, 0, sizeof(*f));
    f->name = ax_xstrdup(func_name);
    f->full_sym = full_sym ? ax_xstrdup(full_sym) : NULL;
    return f;
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
        if (ctx->relocs[i].sym_name) ax_xfree(ctx->relocs[i].sym_name);
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
    r->dsec = NULL;
    r->doffset = 0;
    r->addend = addend;
}

// Relocation whose target symbol is defined in the same object (SectionNumber > 0): bound by the
// symbol-table index at load time, whatever its name or storage class (ADR-0035 section 2).
static void add_reloc_direct(LinkerContext *ctx, MergedSection *sec, uint32_t offset, uint16_t type, MergedSection *dsec, uint32_t doffset, int64_t addend) {
    if (ctx->num_relocs == ctx->cap_relocs) {
        ctx->cap_relocs = ctx->cap_relocs == 0 ? 64 : ctx->cap_relocs * 2;
        ctx->relocs = ax_xrealloc(ctx->relocs, ctx->cap_relocs * sizeof(Reloc));
    }
    Reloc *r = &ctx->relocs[ctx->num_relocs++];
    r->sec = sec;
    r->offset = offset;
    r->type = type;
    r->sym_name = NULL;
    r->dsec = dsec;
    r->doffset = doffset;
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
                sym_secs[s + 1 + a] = NULL;
                sym_offsets[s + 1 + a] = 0;
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
                uint32_t tgt = rels[r].SymbolTableIndex;
                if (tgt < hdr.NumberOfSymbols && sym_secs[tgt] != NULL) {
                    add_reloc_direct(&ctx, msec, off, rels[r].Type, sym_secs[tgt], sym_offsets[tgt], addend);
                } else {
                    const char *tgt_name = tgt < hdr.NumberOfSymbols ? sym_names[tgt] : NULL;
                    add_reloc(&ctx, msec, off, rels[r].Type, tgt_name ? tgt_name : "", addend);
                }
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
    uint8_t start_code[] = { 0x53, 0x55, 0x48, 0x83, 0xEC, 0x38, 0x31, 0xED, 0x48, 0xC7, 0xC1, 0xF5, 0xFF, 0xFF, 0xFF, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x48, 0x89, 0xC1, 0x48, 0x8D, 0x54, 0x24, 0x30, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x85, 0xC0, 0x74, 0x0D, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x89, 0xC5, 0xB9, 0xE9, 0xFD, 0x00, 0x00, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0xE8, 0x00, 0x00, 0x00, 0x00, 0x89, 0xC3, 0x85, 0xED, 0x74, 0x08, 0x89, 0xE9, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x89, 0xD9, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0xCC };
    append_section_data(text_sec, start_code, sizeof(start_code), 16, &axiom_start_offset);
    add_reloc(&ctx, text_sec, axiom_start_offset + 17, IMAGE_REL_AMD64_REL32, "__IAT_GetStdHandle", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 31, IMAGE_REL_AMD64_REL32, "__IAT_GetConsoleMode", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 41, IMAGE_REL_AMD64_REL32, "__IAT_GetConsoleOutputCP", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 54, IMAGE_REL_AMD64_REL32, "__IAT_SetConsoleOutputCP", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 59, IMAGE_REL_AMD64_REL32, "main", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 73, IMAGE_REL_AMD64_REL32, "__IAT_SetConsoleOutputCP", 0);
    add_reloc(&ctx, text_sec, axiom_start_offset + 81, IMAGE_REL_AMD64_REL32, "__IAT_ExitProcess", 0);

    
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
    add_reloc(&ctx, text_sec, panic_offset + 19, IMAGE_REL_AMD64_REL32, "__IAT_GetStdHandle", 0);
    add_reloc(&ctx, text_sec, panic_offset + 48, IMAGE_REL_AMD64_REL32, "__IAT_WriteFile", 0);
    add_reloc(&ctx, text_sec, panic_offset + 59, IMAGE_REL_AMD64_REL32, "__IAT_ExitProcess", 0);
    
    GlobalSymbol *panic_sym = add_global(&ctx, "axiom_panic");
    panic_sym->defined = true; panic_sym->sec = text_sec; panic_sym->offset = panic_offset;
    

    uint8_t print_code[] = {
        0x53, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x89, 0xCB, 0x48, 0xC7, 0xC1, 0xF5, 0xFF, 0xFF, 0xFF,
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00,
        0x48, 0x89, 0xC1, 0x48, 0x8B, 0x13, 
        0x4C, 0x8B, 0x43, 0x08, 0x90, 0x90, 
        0x4C, 0x8D, 0x4C, 0x24, 0x28,
        0x48, 0xC7, 0x44, 0x24, 0x20, 0x00, 0x00, 0x00, 0x00,
        0xFF, 0x15, 0x00, 0x00, 0x00, 0x00,
        0x48, 0x83, 0xC4, 0x30, 0x5B, 0xC3
    };
    uint32_t print_offset;
    append_section_data(text_sec, print_code, sizeof(print_code), 16, &print_offset);
    add_reloc(&ctx, text_sec, print_offset + 17, IMAGE_REL_AMD64_REL32, "__IAT_GetStdHandle", 0);
    add_reloc(&ctx, text_sec, print_offset + 49, IMAGE_REL_AMD64_REL32, "__IAT_WriteFile", 0);
    
    GlobalSymbol *print_sym = add_global(&ctx, "__ax_host_print");
    print_sym->defined = true; print_sym->sec = text_sec; print_sym->offset = print_offset;


    uint8_t print_int_code[] = {
        0x53, 0x56, 0x57, 0x48, 0x83, 0xEC, 0x30, 0x48, 0x89, 0xC8, 0x48, 0x8D, 0x7C, 0x24, 0x20, 0xC6, 0x07, 0x00, 0x48, 0xC7, 0xC3, 0x0A, 0x00, 0x00, 0x00, 0x48, 0x89, 0xFE, 0x48, 0x85, 0xC0, 0x79, 0x03, 0x48, 0xF7, 0xD8, 0x48, 0x31, 0xD2, 0x48, 0xF7, 0xF3, 0x80, 0xC2, 0x30, 0x48, 0xFF, 0xCE, 0x88, 0x16, 0x48, 0x85, 0xC0, 0x75, 0xED, 0x48, 0x85, 0xC9, 0x79, 0x06, 0x48, 0xFF, 0xCE, 0xC6, 0x06, 0x2D, 0x48, 0xC7, 0xC1, 0xF5, 0xFF, 0xFF, 0xFF, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x48, 0x89, 0xC1, 0x48, 0x89, 0xF2, 0x49, 0x89, 0xF8, 0x49, 0x29, 0xF0, 0x4C, 0x8D, 0x4C, 0x24, 0x28, 0x48, 0xC7, 0x44, 0x24, 0x20, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x15, 0x00, 0x00, 0x00, 0x00, 0x48, 0x83, 0xC4, 0x30, 0x5F, 0x5E, 0x5B, 0xC3
    };
    uint32_t print_int_offset;
    append_section_data(text_sec, print_int_code, sizeof(print_int_code), 16, &print_int_offset);
    add_reloc(&ctx, text_sec, print_int_offset + 75, IMAGE_REL_AMD64_REL32, "__IAT_GetStdHandle", 0);
    add_reloc(&ctx, text_sec, print_int_offset + 107, IMAGE_REL_AMD64_REL32, "__IAT_WriteFile", 0);
    
    GlobalSymbol *print_int_sym = add_global(&ctx, "__ax_host_print_int");
    print_int_sym->defined = true; print_int_sym->sec = text_sec; print_int_sym->offset = print_int_offset;

    // Build Import Directory dynamically
    ImportDll *import_dlls = NULL;
    size_t num_import_dlls = 0;
    size_t cap_import_dlls = 0;

    // 1. Base KERNEL32 imports
    ImportDll *k32 = find_or_add_dll(&import_dlls, &num_import_dlls, &cap_import_dlls, "KERNEL32.dll");
    add_import_func(k32, "ExitProcess", NULL);
    add_import_func(k32, "GetStdHandle", NULL);
    add_import_func(k32, "WriteFile", NULL);
    add_import_func(k32, "SetConsoleOutputCP", NULL);
    add_import_func(k32, "GetConsoleMode", NULL);
    add_import_func(k32, "GetConsoleOutputCP", NULL);

    // 2. Discover DLL imports from relocations
    for (size_t i = 0; i < ctx.num_relocs; i++) {
        const char *sname = ctx.relocs[i].sym_name;
        if (!sname || !sname[0]) continue;

        bool is_defined = false;
        for (size_t g = 0; g < ctx.num_globals; g++) {
            if (ctx.globals[g].defined && strcmp(ctx.globals[g].name, sname) == 0) {
                is_defined = true;
                break;
            }
        }
        if (is_defined) continue;

        // Undefined symbol: check if DLL$func or __IAT_
        const char *target = sname;
        if (strncmp(target, "__IAT_", 6) == 0) {
            target += 6;
        }

        const char *dollar = strchr(target, '$');
        if (dollar) {
            size_t dlen = (size_t)(dollar - target);
            char dll_buf[128];
            if (dlen >= sizeof(dll_buf)) dlen = sizeof(dll_buf) - 1;
            memcpy(dll_buf, target, dlen);
            dll_buf[dlen] = '\0';
            const char *fname = dollar + 1;
            ImportDll *dll = find_or_add_dll(&import_dlls, &num_import_dlls, &cap_import_dlls, dll_buf);
            add_import_func(dll, fname, target);
        } else if (strncmp(sname, "__IAT_", 6) == 0) {
            ImportDll *dll = find_or_add_dll(&import_dlls, &num_import_dlls, &cap_import_dlls, "KERNEL32.dll");
            add_import_func(dll, target, NULL);
        }
    }

    // 3. Emit thunks for each imported function into text_sec
    for (size_t d = 0; d < num_import_dlls; d++) {
        ImportDll *dll = &import_dlls[d];
        for (size_t f = 0; f < dll->num_funcs; f++) {
            ImportFunc *fn = &dll->funcs[f];
            
            char iat_sym_name[256];
            snprintf(iat_sym_name, sizeof(iat_sym_name), "__IAT_%s", fn->name);

            uint8_t thunk[] = { 0xFF, 0x25, 0x00, 0x00, 0x00, 0x00 }; // jmp [rip + disp32]
            uint32_t thunk_off = 0;
            append_section_data(text_sec, thunk, sizeof(thunk), 8, &thunk_off);
            fn->thunk_offset = thunk_off;

            add_reloc(&ctx, text_sec, thunk_off + 2, IMAGE_REL_AMD64_REL32, iat_sym_name, 0);

            GlobalSymbol *g_fn = add_global(&ctx, fn->name);
            if (!g_fn->defined) {
                g_fn->defined = true;
                g_fn->sec = text_sec;
                g_fn->offset = thunk_off;
            }
            if (fn->full_sym) {
                GlobalSymbol *g_full = add_global(&ctx, fn->full_sym);
                if (!g_full->defined) {
                    g_full->defined = true;
                    g_full->sec = text_sec;
                    g_full->offset = thunk_off;
                }
            }
        }
    }

    // 4. Construct .idata buffer
    MergedSection *idata_sec = get_or_create_section(&ctx, ".idata", IMAGE_SCN_CNT_INITIALIZED_DATA | IMAGE_SCN_MEM_READ | IMAGE_SCN_MEM_WRITE);
    uint32_t idata_base = 0;

    uint32_t idata_cap = 65536;
    uint8_t *idata_buf = ax_xcalloc(1, idata_cap);
    uint32_t i_off = 0;

    // 4a. Descriptors
    uint32_t desc_offset = i_off;
    for (size_t d = 0; d < num_import_dlls; d++) {
        import_dlls[d].desc_offset = i_off;
        i_off += sizeof(IMAGE_IMPORT_DESCRIPTOR);
    }
    // Null terminating descriptor
    i_off += sizeof(IMAGE_IMPORT_DESCRIPTOR);

    // 4b. ILTs
    for (size_t d = 0; d < num_import_dlls; d++) {
        import_dlls[d].ilt_offset = i_off;
        i_off += (uint32_t)((import_dlls[d].num_funcs + 1) * 8);
    }

    // 4c. IATs (all contiguous)
    uint32_t all_iats_start = i_off;
    for (size_t d = 0; d < num_import_dlls; d++) {
        import_dlls[d].iat_offset = i_off;
        for (size_t f = 0; f < import_dlls[d].num_funcs; f++) {
            import_dlls[d].funcs[f].iat_offset = i_off + (uint32_t)(f * 8);
        }
        i_off += (uint32_t)((import_dlls[d].num_funcs + 1) * 8);
    }
    uint32_t all_iats_size = i_off - all_iats_start;

    // 4d. Hint/Names
    for (size_t d = 0; d < num_import_dlls; d++) {
        for (size_t f = 0; f < import_dlls[d].num_funcs; f++) {
            import_dlls[d].funcs[f].hint_offset = i_off;
            idata_buf[i_off++] = 0;
            idata_buf[i_off++] = 0;
            size_t nlen = strlen(import_dlls[d].funcs[f].name);
            memcpy(idata_buf + i_off, import_dlls[d].funcs[f].name, nlen + 1);
            i_off += (uint32_t)(nlen + 1);
            if (i_off & 1) i_off++;
        }
    }

    // 4e. DLL Names
    for (size_t d = 0; d < num_import_dlls; d++) {
        import_dlls[d].dll_name_offset = i_off;
        size_t nlen = strlen(import_dlls[d].dll_name);
        memcpy(idata_buf + i_off, import_dlls[d].dll_name, nlen + 1);
        i_off += (uint32_t)(nlen + 1);
        if (i_off & 1) i_off++;
    }

    i_off = ALIGN_UP(i_off, 8);
    append_section_data(idata_sec, idata_buf, i_off, 8, &idata_base);
    ax_xfree(idata_buf);

    // 5. Define __IAT_* global symbols
    for (size_t d = 0; d < num_import_dlls; d++) {
        for (size_t f = 0; f < import_dlls[d].num_funcs; f++) {
            ImportFunc *fn = &import_dlls[d].funcs[f];
            char iat_sym[256];
            snprintf(iat_sym, sizeof(iat_sym), "__IAT_%s", fn->name);
            GlobalSymbol *g = add_global(&ctx, iat_sym);
            g->defined = true;
            g->sec = idata_sec;
            g->offset = idata_base + fn->iat_offset;

            if (fn->full_sym) {
                snprintf(iat_sym, sizeof(iat_sym), "__IAT_%s", fn->full_sym);
                GlobalSymbol *g2 = add_global(&ctx, iat_sym);
                g2->defined = true;
                g2->sec = idata_sec;
                g2->offset = idata_base + fn->iat_offset;
            }
        }
    }

    // 6. RVA assignment (Layout)
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

    // 7. Patch .idata with computed RVAs
    uint32_t idata_rva = idata_sec->rva + idata_base;
    for (size_t d = 0; d < num_import_dlls; d++) {
        ImportDll *dll = &import_dlls[d];
        IMAGE_IMPORT_DESCRIPTOR *pdesc = (IMAGE_IMPORT_DESCRIPTOR*)(idata_sec->data + idata_base + dll->desc_offset);
        pdesc->OriginalFirstThunk = idata_rva + dll->ilt_offset;
        pdesc->Name = idata_rva + dll->dll_name_offset;
        pdesc->FirstThunk = idata_rva + dll->iat_offset;

        for (size_t f = 0; f < dll->num_funcs; f++) {
            uint64_t hint_rva = (uint64_t)(idata_rva + dll->funcs[f].hint_offset);
            memcpy(idata_sec->data + idata_base + dll->ilt_offset + f * 8, &hint_rva, 8);
            memcpy(idata_sec->data + idata_base + dll->iat_offset + f * 8, &hint_rva, 8);
        }
    }


    
    // Apply relocations
    for (size_t i = 0; i < ctx.num_relocs; i++) {
        Reloc *r = &ctx.relocs[i];
        uint32_t sym_rva;
        if (r->dsec) {
            sym_rva = r->dsec->rva + r->doffset;
        } else {
            GlobalSymbol *sym = add_global(&ctx, r->sym_name);
            if (!sym->defined) {
                if (diag) ax_diag_sink_report(diag, &(AxDiagnostic){.code=AX_LINK_UNDEFINED_SYMBOL, .severity=AX_DIAG_ERROR, .message=r->sym_name});
                { free_import_dlls(import_dlls, num_import_dlls); free_linker_context(&ctx); return false; }
            }
            sym_rva = sym->sec->rva + sym->offset;
        }
        
        uint32_t reloc_rva = r->sec->rva + r->offset;
        
        if (r->type == IMAGE_REL_AMD64_REL32 || (r->type >= IMAGE_REL_AMD64_REL32_1 && r->type <= IMAGE_REL_AMD64_REL32_5)) {
            int64_t val = (int64_t)sym_rva - (int64_t)reloc_rva - 4 + r->addend;
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
    if (!out) { free_import_dlls(import_dlls, num_import_dlls); free_linker_context(&ctx); return false; }
    
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
    dirs[1].Size = (uint32_t)((num_import_dlls + 1) * sizeof(IMAGE_IMPORT_DESCRIPTOR));
    dirs[12].VirtualAddress = idata_sec->rva + idata_base + all_iats_start;
    dirs[12].Size = all_iats_size;
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
    free_import_dlls(import_dlls, num_import_dlls);
    { free_linker_context(&ctx); return true; }
}
