#include "kernel/kernel.h"
#include "objmodel/objmodel.h"
#include "target/x64/encode/encode.h"
#include <stdio.h>
#include <string.h>

static void assert_bytes_eq(const uint8_t *expected, size_t exp_len, const uint8_t *actual, size_t act_len, const char *msg) {
    if (exp_len != act_len) {
        fprintf(stderr, "FAIL: %s\n  Length mismatch: expected %zu, got %zu\n", msg, exp_len, act_len);
        ax_ice_fail(__FILE__, __LINE__, "test failed");
    }
    for (size_t i = 0; i < exp_len; i++) {
        if (expected[i] != actual[i]) {
            fprintf(stderr, "FAIL: %s\n  Byte %zu mismatch: expected %02x, got %02x\n", msg, i, expected[i], actual[i]);
            ax_ice_fail(__FILE__, __LINE__, "test failed");
        }
    }
}

#include "encode_tests.inc"

int main(void) {
    ax_objmodel_t obj;
    ax_objmodel_init(&obj);
    
    // We can also test relocations directly here if needed
    // But encode_tests.inc tests all machine bytes.
    run_encode_tests();

    // QA Boundary test: check branch and relocation encoding
    ax_section_id_t sec_id = ax_objmodel_add_section(&obj, ".text", AX_SEC_CODE, AX_SEC_FLAG_EXEC | AX_SEC_FLAG_READ, 16);
    ax_section_t *sec = ax_objmodel_get_section(&obj, sec_id);
    ax_symbol_id_t sym_id = ax_objmodel_add_symbol(&obj, "my_func", sec_id, 0, 0, AX_SYM_GLOBAL);
    
    ax_x64_call_sym(sec, sym_id);
    ax_x64_jmp(sec, -5); // Jump to itself
    
    uint8_t exp_call[] = {0xE8, 0, 0, 0, 0};
    uint8_t exp_jmp[] = {0xE9, 0xFB, 0xFF, 0xFF, 0xFF}; // -5 is 0xFFFFFFFB
    assert_bytes_eq(exp_call, 5, sec->bytes, 5, "call_sym");
    assert_bytes_eq(exp_jmp, 5, sec->bytes + 5, 5, "jmp -5");
    
    if (sec->relocs_len != 1) {
        fprintf(stderr, "FAIL: expected 1 relocation, got %zu\n", sec->relocs_len);
        ax_ice_fail(__FILE__, __LINE__, "QA test failed");
    }
    if (sec->relocs[0].offset != 1 || sec->relocs[0].kind != AX_RELOC_X86_64_PC32 || sec->relocs[0].symbol_id.v != sym_id.v || sec->relocs[0].addend != -4) {
        fprintf(stderr, "FAIL: bad relocation\n");
        ax_ice_fail(__FILE__, __LINE__, "QA test failed");
    }
    
    ax_objmodel_free(&obj);
    
    printf("PASS\n");
    return 0;
}
