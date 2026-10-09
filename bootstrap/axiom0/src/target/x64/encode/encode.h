#ifndef AX_TARGET_X64_ENCODE_ENCODE_H
#define AX_TARGET_X64_ENCODE_ENCODE_H

#include "objmodel/objmodel.h"

/* Registers */
typedef enum ax_x64_reg {
    AX_REG_RAX = 0, AX_REG_RCX = 1, AX_REG_RDX = 2, AX_REG_RBX = 3,
    AX_REG_RSP = 4, AX_REG_RBP = 5, AX_REG_RSI = 6, AX_REG_RDI = 7,
    AX_REG_R8  = 8, AX_REG_R9  = 9, AX_REG_R10 = 10, AX_REG_R11 = 11,
    AX_REG_R12 = 12, AX_REG_R13 = 13, AX_REG_R14 = 14, AX_REG_R15 = 15,
    AX_REG_NONE = -1
} ax_x64_reg_t;

/* Conditions */
typedef enum ax_x64_cc {
    AX_CC_O = 0x0, AX_CC_NO = 0x1, AX_CC_B = 0x2, AX_CC_AE = 0x3,
    AX_CC_E = 0x4, AX_CC_NE = 0x5, AX_CC_BE = 0x6, AX_CC_A = 0x7,
    AX_CC_S = 0x8, AX_CC_NS = 0x9, AX_CC_P = 0xA, AX_CC_NP = 0xB,
    AX_CC_L = 0xC, AX_CC_GE = 0xD, AX_CC_LE = 0xE, AX_CC_G = 0xF
} ax_x64_cc_t;

/* Memory addressing */
typedef struct ax_x64_mem {
    ax_x64_reg_t base;
    ax_x64_reg_t index; /* AX_REG_NONE if unused */
    uint8_t scale;      /* 1, 2, 4, 8 */
    int32_t disp;
    bool is_rip;
} ax_x64_mem_t;

static inline ax_x64_mem_t ax_x64_mem_base(ax_x64_reg_t base) {
    ax_x64_mem_t m = {base, AX_REG_NONE, 1, 0, false};
    return m;
}

static inline ax_x64_mem_t ax_x64_mem_base_disp(ax_x64_reg_t base, int32_t disp) {
    ax_x64_mem_t m = {base, AX_REG_NONE, 1, disp, false};
    return m;
}

static inline ax_x64_mem_t ax_x64_mem_index(ax_x64_reg_t base, ax_x64_reg_t index, uint8_t scale) {
    ax_x64_mem_t m = {base, index, scale, 0, false};
    return m;
}

static inline ax_x64_mem_t ax_x64_mem_index_disp(ax_x64_reg_t base, ax_x64_reg_t index, uint8_t scale, int32_t disp) {
    ax_x64_mem_t m = {base, index, scale, disp, false};
    return m;
}

static inline ax_x64_mem_t ax_x64_mem_rip(int32_t disp) {
    ax_x64_mem_t m = {AX_REG_NONE, AX_REG_NONE, 1, disp, true};
    return m;
}

/* Instructions */
void ax_x64_mov_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_mov_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_mov_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_mov_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int64_t imm); /* 64-bit imm only when sz=8 */
void ax_x64_mov_mi(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, int32_t imm);

void ax_x64_movzx_rr(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_movzx_rm(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_movsx_rr(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_movsx_rm(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_mem_t src);

void ax_x64_lea(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_lea_sym(ax_section_t *sec, ax_x64_reg_t dst, ax_symbol_id_t sym);

void ax_x64_add_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_add_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_add_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_add_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm);

void ax_x64_sub_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_sub_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_sub_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_sub_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm);

void ax_x64_and_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_and_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_and_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_and_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm);

void ax_x64_or_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_or_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_or_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_or_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm);

void ax_x64_xor_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_xor_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_xor_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src);
void ax_x64_xor_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm);

void ax_x64_cmp_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_reg_t right);
void ax_x64_cmp_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_mem_t right);
void ax_x64_cmp_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t left, ax_x64_reg_t right);
void ax_x64_cmp_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, int32_t imm);

void ax_x64_test_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_reg_t right);
void ax_x64_test_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_mem_t right);
void ax_x64_test_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, int32_t imm);

void ax_x64_imul_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src);
void ax_x64_imul_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src);
void ax_x64_mul_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t src);
void ax_x64_mul_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t src);

void ax_x64_cqo(ax_section_t *sec);
void ax_x64_cdq(ax_section_t *sec);

void ax_x64_idiv_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t src);
void ax_x64_idiv_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t src);
void ax_x64_div_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t src);
void ax_x64_div_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t src);

void ax_x64_neg_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst);
void ax_x64_neg_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst);
void ax_x64_not_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst);
void ax_x64_not_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst);

void ax_x64_shl_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst);
void ax_x64_shl_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm);
void ax_x64_shr_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst);
void ax_x64_shr_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm);
void ax_x64_sar_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst);
void ax_x64_sar_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm);

void ax_x64_setcc_r(ax_section_t *sec, ax_x64_cc_t cc, ax_x64_reg_t dst);
void ax_x64_setcc_m(ax_section_t *sec, ax_x64_cc_t cc, ax_x64_mem_t dst);

void ax_x64_jcc(ax_section_t *sec, ax_x64_cc_t cc, int32_t rel32);
void ax_x64_jcc_sym(ax_section_t *sec, ax_x64_cc_t cc, ax_symbol_id_t sym);
void ax_x64_jmp(ax_section_t *sec, int32_t rel32);
void ax_x64_jmp_sym(ax_section_t *sec, ax_symbol_id_t sym);

void ax_x64_call(ax_section_t *sec, int32_t rel32);
void ax_x64_call_sym(ax_section_t *sec, ax_symbol_id_t sym);
void ax_x64_call_r(ax_section_t *sec, ax_x64_reg_t dst);
void ax_x64_call_m(ax_section_t *sec, ax_x64_mem_t dst);

void ax_x64_ret(ax_section_t *sec);

void ax_x64_push_r(ax_section_t *sec, ax_x64_reg_t src);
void ax_x64_push_m(ax_section_t *sec, ax_x64_mem_t src);
void ax_x64_pop_r(ax_section_t *sec, ax_x64_reg_t dst);
void ax_x64_pop_m(ax_section_t *sec, ax_x64_mem_t dst);

void ax_x64_int3(ax_section_t *sec);

#endif
void ax_x64_jcc8(ax_section_t *sec, ax_x64_cc_t cc, int8_t rel8);
void ax_x64_jmp8(ax_section_t *sec, int8_t rel8);
