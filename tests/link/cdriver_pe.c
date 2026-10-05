#include "link/pe/linker.h"
#include "objmodel/objmodel.h"
#include "obj/coff/writer.h"
#include "diag/diag.h"
#include "kernel/base.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

AxDiagSink diag;
void ax_diag_sink_init(AX_MAYBE_UNUSED AxDiagSink *sink) { (void)sink; }
void ax_diag_sink_free(AX_MAYBE_UNUSED AxDiagSink *sink) { (void)sink; }
void ax_diag_sink_report(AX_MAYBE_UNUSED AxDiagSink *sink, const AxDiagnostic *d) {
    (void)sink;
    printf("DIAG: %s\n", d->message);
}
void test_link_pe(void) {
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);

    ax_section_id_t text_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text = ax_objmodel_get_section(&obj, text_id);

    // mov eax, 42 (B8 2A 00 00 00)
    // ret (C3)
    uint8_t code[] = { 0xB8, 0x2A, 0x00, 0x00, 0x00, 0xC3 };
    ax_section_add_bytes(text, code, sizeof(code));

    ax_objmodel_add_symbol(&obj, "main", text_id, 0, sizeof(code), AX_SYM_GLOBAL);

    ax_coff_write(&obj, "main42.obj");
    ax_objmodel_free(&obj);

    const char *inputs[] = { "main42.obj" };
    if (!ax_pe_link(inputs, 1, "main42.exe", 0x100000, &diag)) {
        printf("FAIL: linker failed\n");
        exit(1);
    }

    int code_ret = system(".\\main42.exe");
    if (code_ret != 42) {
        printf("FAIL: main42.exe exit code was %d, expected 42\n", code_ret);
        exit(1);
    }
    printf("main42.exe linked and returned 42!\n");
    
    if (!ax_pe_link(inputs, 1, "main42_bigstack.exe", 67108864, &diag)) {
        printf("FAIL: linker failed for big stack\n");
        exit(1);
    }
    printf("main42_bigstack.exe linked!\n");

    // Negative test: undefined symbol
    ax_objmodel_t obj2;
    ax_objmodel_init(&obj2);
    ax_section_id_t text2_id = ax_objmodel_add_section(&obj2, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text2 = ax_objmodel_get_section(&obj2, text2_id);
    ax_section_add_bytes(text2, code, sizeof(code));
    ax_objmodel_add_symbol(&obj2, "main", text2_id, 0, sizeof(code), AX_SYM_GLOBAL);
    
    // Add relocation to an undefined symbol
    ax_symbol_id_t undef_sym = ax_objmodel_add_symbol(&obj2, "undefined_func", (ax_section_id_t){0}, 0, 0, AX_SYM_EXTERNAL);
    ax_section_add_reloc(text2, 1, AX_RELOC_X86_64_PC32, undef_sym, 0);

    ax_coff_write(&obj2, "undef.obj");
    ax_objmodel_free(&obj2);

    const char *inputs2[] = { "undef.obj" };
    if (ax_pe_link(inputs2, 1, "undef.exe", 0x100000, &diag)) {
        printf("FAIL: linker succeeded with undefined symbol\n");
        exit(1);
    }
    printf("undef.obj failed to link as expected!\n");

    // Negative test: duplicate symbol
    ax_objmodel_t obj3;
    ax_objmodel_init(&obj3);
    ax_section_id_t text3_id = ax_objmodel_add_section(&obj3, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *text3 = ax_objmodel_get_section(&obj3, text3_id);
    ax_section_add_bytes(text3, code, sizeof(code));
    ax_objmodel_add_symbol(&obj3, "main", text3_id, 0, sizeof(code), AX_SYM_GLOBAL);
    // Add another symbol with the same name
    ax_objmodel_add_symbol(&obj3, "main", text3_id, 0, sizeof(code), AX_SYM_GLOBAL);
    
    ax_coff_write(&obj3, "dup.obj");
    ax_objmodel_free(&obj3);

    const char *inputs3[] = { "dup.obj" };
    if (ax_pe_link(inputs3, 1, "dup.exe", 0x100000, &diag)) {
        printf("FAIL: linker succeeded with duplicate symbol\n");
        exit(1);
    }
    printf("dup.obj failed to link as expected!\n");
}

int main(void) {
    ax_diag_sink_init(&diag);
    test_link_pe();
    printf("PASS\n");
    ax_diag_sink_free(&diag);
    return 0;
}
