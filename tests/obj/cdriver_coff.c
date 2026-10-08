#include "objmodel/objmodel.h"
#include "obj/coff/writer.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void test_basic_obj(void) {
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);

    ax_section_id_t text_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text = ax_objmodel_get_section(&obj, text_id);

    // mov eax, 42 (B8 2A 00 00 00)
    // ret (C3)
    uint8_t code[] = { 0xB8, 0x2A, 0x00, 0x00, 0x00, 0xC3 };
    ax_section_add_bytes(text, code, sizeof(code));

    ax_objmodel_add_symbol(&obj, "main", text_id, 0, sizeof(code), AX_SYM_GLOBAL);

    ax_section_id_t bss_id = ax_objmodel_add_section(&obj, ".bss", AX_SEC_BSS, AX_SEC_FLAG_READ | AX_SEC_FLAG_WRITE, 16);
    ax_objmodel_add_symbol(&obj, "my_bss", bss_id, 0, 8, AX_SYM_GLOBAL);

    ax_coff_write(&obj, "basic.obj");
    ax_objmodel_free(&obj);
}

void test_relocs_obj(void) {
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);

    ax_section_id_t text_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_id_t data_id = ax_objmodel_add_section(&obj, ".data", AX_SEC_DATA, AX_SEC_FLAG_READ | AX_SEC_FLAG_WRITE, 8);
    ax_section_id_t rdata_id = ax_objmodel_add_section(&obj, ".rdata", AX_SEC_RODATA, AX_SEC_FLAG_READ, 8);

    // .rdata
    const char *msg = "Xin chào thế giới";
    ax_section_t *rdata = ax_objmodel_get_section(&obj, rdata_id);
    ax_section_add_bytes(rdata, (const uint8_t*)msg, strlen(msg) + 1);
    ax_symbol_id_t msg_sym = ax_objmodel_add_symbol(&obj, "msg", rdata_id, 0, strlen(msg) + 1, AX_SYM_LOCAL);

    // .data
    // ptr_to_msg: .quad msg
    // my_data_word: .quad 0xdeadbeefc0def00d
    ax_section_t *data = ax_objmodel_get_section(&obj, data_id);
    uint64_t zero = 0;
    ax_section_add_bytes(data, (const uint8_t*)&zero, 8);
    ax_section_add_reloc(data, 0, AX_RELOC_X86_64_64, msg_sym, 0); // ADDR64
    
    uint64_t word = 0xdeadbeefc0def00dULL;
    ax_section_add_bytes(data, (const uint8_t*)&word, 8);
    ax_objmodel_add_symbol(&obj, "my_data_word", data_id, 8, 8, AX_SYM_GLOBAL);
    ax_symbol_id_t ptr_sym = ax_objmodel_add_symbol(&obj, "ptr_to_msg", data_id, 0, 8, AX_SYM_LOCAL);

    // .text
    // main:
    // sub rsp, 40               ; 48 83 EC 28
    // mov rcx, [rip + ptr_to_msg] ; 48 8B 0D <disp32>
    // call check_data           ; E8 <disp32>
    // add rsp, 40               ; 48 83 C4 28
    // ret                       ; C3
    ax_section_t *text = ax_objmodel_get_section(&obj, text_id);
    
    uint8_t sub_rsp[] = { 0x48, 0x83, 0xEC, 0x28 };
    ax_section_add_bytes(text, sub_rsp, sizeof(sub_rsp));
    
    uint8_t mov_rcx[] = { 0x48, 0x8B, 0x0D, 0x00, 0x00, 0x00, 0x00 };
    uint32_t mov_offset = text->bytes_len + sizeof(mov_rcx) - 4;
    ax_section_add_bytes(text, mov_rcx, sizeof(mov_rcx));
    
    uint8_t call[] = { 0xE8, 0x00, 0x00, 0x00, 0x00 };
    uint32_t call_offset = text->bytes_len + sizeof(call) - 4;
    ax_section_add_bytes(text, call, sizeof(call));
    
    uint8_t add_rsp[] = { 0x48, 0x83, 0xC4, 0x28, 0xC3 };
    ax_section_add_bytes(text, add_rsp, sizeof(add_rsp));
    
    ax_symbol_id_t check_data_sym = ax_objmodel_add_symbol(&obj, "check_data", (ax_section_id_t){0}, 0, 0, AX_SYM_EXTERNAL);
    
    // Add relocations for .text
    ax_section_add_reloc(text, mov_offset, AX_RELOC_X86_64_PC32, ptr_sym, -4); // REL32 (RIP relative)
    ax_section_add_reloc(text, call_offset, AX_RELOC_X86_64_PC32, check_data_sym, -4); // REL32
    
    ax_objmodel_add_symbol(&obj, "main", text_id, 0, text->bytes_len, AX_SYM_GLOBAL);

    ax_coff_write(&obj, "relocs.obj");
    ax_objmodel_free(&obj);
}

int main(void) {
    if (system("gcc --version > NUL 2>&1") != 0) {
        printf("SKIP: gcc not on PATH\n");
        return 0;
    }

    test_basic_obj();
    if (system("gcc basic.obj -o basic.exe") != 0) {
        printf("FAIL: gcc failed to link basic.obj\n");
        return 1;
    }
    int code = system(".\\basic.exe");
    if (code != 42) {
        printf("FAIL: basic.exe exit code was %d, expected 42\n", code);
        return 1;
    }

    test_relocs_obj();
    // The test driver runs in build/tests/, so we use ../../tests/obj/fixtures/c_helper.c
    if (system("gcc relocs.obj ../../tests/obj/fixtures/c_helper.c -o relocs.exe") != 0) {
        printf("FAIL: gcc failed to link relocs.obj\n");
        return 1;
    }
    code = system(".\\relocs.exe");
    if (code != 0) {
        printf("FAIL: relocs.exe exit code was %d, expected 0\n", code);
        return 1;
    }

    // Regression test for ADDR32NB
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    ax_section_id_t pdata_id = ax_objmodel_add_section(&obj, ".pdata", AX_SEC_RODATA, AX_SEC_FLAG_READ, 4);
    ax_section_t *pdata = ax_objmodel_get_section(&obj, pdata_id);
    uint32_t zero32 = 0;
    ax_section_add_bytes(pdata, (const uint8_t*)&zero32, 4);
    ax_symbol_id_t dummy_sym = ax_objmodel_add_symbol(&obj, "dummy_func", (ax_section_id_t){0}, 0, 0, AX_SYM_EXTERNAL);
    ax_section_add_reloc(pdata, 0, AX_RELOC_X86_64_32, dummy_sym, 0); // Should map to ADDR32NB
    ax_coff_write(&obj, "addr32nb.obj");
    ax_objmodel_free(&obj);

    printf("PASS\n");
    return 0;
}
