#include "target/x64/encode/encode.h"

static void emit8(ax_section_t *sec, uint8_t b) {
    ax_section_add_byte(sec, b);
}

static void emit32(ax_section_t *sec, uint32_t d) {
    emit8(sec, d & 0xFF);
    emit8(sec, (d >> 8) & 0xFF);
    emit8(sec, (d >> 16) & 0xFF);
    emit8(sec, (d >> 24) & 0xFF);
}

static void emit64(ax_section_t *sec, uint64_t q) {
    emit32(sec, q & 0xFFFFFFFF);
    emit32(sec, q >> 32);
}

static void emit_sz(ax_section_t *sec, uint8_t sz) {
    if (sz == 2) emit8(sec, 0x66);
}

static void emit_rex_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t reg, ax_x64_reg_t rm) {
    bool w = (sz == 8);
    bool r = (reg >= 8);
    bool b = (rm >= 8);
    bool force = (sz == 1 && ((reg >= 4 && reg != AX_REG_NONE) || (rm >= 4 && rm != AX_REG_NONE)));
    if (w || r || b || force) {
        emit8(sec, 0x40 | (w ? 8 : 0) | (r ? 4 : 0) | (b ? 1 : 0));
    }
}

static void emit_rex_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t reg, ax_x64_mem_t m) {
    bool w = (sz == 8);
    bool r = (reg >= 8);
    bool x = (m.index != AX_REG_NONE && m.index >= 8);
    bool b = (m.base != AX_REG_NONE && m.base >= 8);
    bool force = (sz == 1 && reg >= 4 && reg != AX_REG_NONE);
    if (w || r || x || b || force) {
        emit8(sec, 0x40 | (w ? 8 : 0) | (r ? 4 : 0) | (x ? 2 : 0) | (b ? 1 : 0));
    }
}

static void emit_modrm_sib_disp(ax_section_t *sec, ax_x64_reg_t reg, ax_x64_mem_t m) {
    uint8_t r_bits = (reg == AX_REG_NONE ? 0 : reg) & 7;
    
    if (m.is_rip) {
        emit8(sec, 0x00 | (r_bits << 3) | 5);
        emit32(sec, m.disp);
        return;
    }
    
    bool has_sib = (m.index != AX_REG_NONE) || ((m.base & 7) == 4);
    
    uint8_t mod = 0;
    if (m.disp == 0 && (m.base & 7) != 5) {
        mod = 0;
    } else if (m.disp >= -128 && m.disp <= 127) {
        mod = 1;
    } else {
        mod = 2;
    }
    
    if (has_sib) {
        emit8(sec, (mod << 6) | (r_bits << 3) | 4);
        
        uint8_t scale_bits = 0;
        if (m.scale == 2) scale_bits = 1;
        else if (m.scale == 4) scale_bits = 2;
        else if (m.scale == 8) scale_bits = 3;
        
        uint8_t idx_bits = (m.index == AX_REG_NONE) ? 4 : (m.index & 7);
        uint8_t base_bits = m.base & 7;
        
        emit8(sec, (scale_bits << 6) | (idx_bits << 3) | base_bits);
    } else {
        emit8(sec, (mod << 6) | (r_bits << 3) | (m.base & 7));
    }
    
    if (mod == 1) {
        emit8(sec, m.disp & 0xFF);
    } else if (mod == 2 || (mod == 0 && (m.base & 7) == 5)) {
        emit32(sec, m.disp);
    }
}

static void emit_op_rm(ax_section_t *sec, uint8_t sz, uint8_t op8, uint8_t op, ax_x64_reg_t reg, ax_x64_reg_t rm) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, reg, rm);
    emit8(sec, sz == 1 ? op8 : op);
    emit8(sec, 0xC0 | ((reg & 7) << 3) | (rm & 7));
}

static void emit_op_mem(ax_section_t *sec, uint8_t sz, uint8_t op8, uint8_t op, ax_x64_reg_t reg, ax_x64_mem_t m) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, reg, m);
    emit8(sec, sz == 1 ? op8 : op);
    emit_modrm_sib_disp(sec, reg, m);
}
void ax_x64_mov_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src) { emit_op_rm(sec, sz, 0x88, 0x89, src, dst); }
void ax_x64_mov_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src) { emit_op_mem(sec, sz, 0x8A, 0x8B, dst, src); }
void ax_x64_mov_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src) { emit_op_mem(sec, sz, 0x88, 0x89, src, dst); }
void ax_x64_mov_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int64_t imm) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    if (sz == 1) { emit8(sec, 0xB0 + (dst & 7)); emit8(sec, imm & 0xFF); }
    else if (sz == 8) { emit8(sec, 0xB8 + (dst & 7)); emit64(sec, imm); }
    else { emit8(sec, 0xB8 + (dst & 7)); if (sz == 2) { emit8(sec, imm & 0xFF); emit8(sec, (imm >> 8) & 0xFF); } else emit32(sec, imm); }
}
void ax_x64_mov_mi(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, int32_t imm) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xC6 : 0xC7);
    emit_modrm_sib_disp(sec, 0, dst);
    if (sz == 1) emit8(sec, imm & 0xFF);
    else if (sz == 2) { emit8(sec, imm & 0xFF); emit8(sec, (imm >> 8) & 0xFF); }
    else emit32(sec, imm);
}

void ax_x64_movzx_rr(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_reg_t src) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, src_sz == 1 ? 0xB6 : 0xB7);
    emit8(sec, 0xC0 | ((dst & 7) << 3) | (src & 7));
}
void ax_x64_movzx_rm(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_mem_t src) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, src_sz == 1 ? 0xB6 : 0xB7);
    emit_modrm_sib_disp(sec, dst, src);
}
void ax_x64_movsx_rr(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_reg_t src) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, src_sz == 1 ? 0xBE : 0xBF);
    emit8(sec, 0xC0 | ((dst & 7) << 3) | (src & 7));
}
void ax_x64_movsx_rm(ax_section_t *sec, uint8_t sz, uint8_t src_sz, ax_x64_reg_t dst, ax_x64_mem_t src) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, src_sz == 1 ? 0xBE : 0xBF);
    emit_modrm_sib_disp(sec, dst, src);
}

void ax_x64_lea(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src) {
    emit_op_mem(sec, sz, 0x8D, 0x8D, dst, src);
}

#define DEF_ALU(name, op_rm, op_mr, op_imm, ext) \
void ax_x64_##name##_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src) { \
    emit_op_rm(sec, sz, (op_mr), (op_mr)+1, src, dst); \
} \
void ax_x64_##name##_mr(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst, ax_x64_reg_t src) { \
    emit_op_mem(sec, sz, (op_mr), (op_mr)+1, src, dst); \
} \
void ax_x64_##name##_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src) { \
    emit_op_mem(sec, sz, (op_rm), (op_rm)+1, dst, src); \
} \
void ax_x64_##name##_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, int32_t imm) { \
    emit_sz(sec, sz); \
    emit_rex_rr(sec, sz, AX_REG_NONE, dst); \
    if (sz == 1) { \
        if (dst == AX_REG_RAX) { emit8(sec, (op_imm)); emit8(sec, imm & 0xFF); } \
        else { emit8(sec, 0x80); emit8(sec, 0xC0 | ((ext) << 3) | (dst & 7)); emit8(sec, imm & 0xFF); } \
    } else { \
        if (dst == AX_REG_RAX) { emit8(sec, (op_imm)+1); } \
        else if (imm >= -128 && imm <= 127) { emit8(sec, 0x83); emit8(sec, 0xC0 | ((ext) << 3) | (dst & 7)); emit8(sec, imm & 0xFF); return; } \
        else { emit8(sec, 0x81); emit8(sec, 0xC0 | ((ext) << 3) | (dst & 7)); } \
        if (sz == 2) { emit8(sec, imm & 0xFF); emit8(sec, (imm >> 8) & 0xFF); } else emit32(sec, imm); \
    } \
}

DEF_ALU(add, 0x02, 0x00, 0x04, 0)
DEF_ALU(or,  0x0A, 0x08, 0x0C, 1)
DEF_ALU(and, 0x22, 0x20, 0x24, 4)
DEF_ALU(sub, 0x2A, 0x28, 0x2C, 5)
DEF_ALU(xor, 0x32, 0x30, 0x34, 6)
DEF_ALU(cmp, 0x3A, 0x38, 0x3C, 7)

void ax_x64_test_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_reg_t right) {
    emit_op_rm(sec, sz, 0x84, 0x85, right, left);
}
void ax_x64_test_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, ax_x64_mem_t right) {
    emit_op_mem(sec, sz, 0x84, 0x85, left, right);
}
void ax_x64_test_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t left, int32_t imm) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, AX_REG_NONE, left);
    if (sz == 1) {
        if (left == AX_REG_RAX) { emit8(sec, 0xA8); emit8(sec, imm & 0xFF); }
        else { emit8(sec, 0xF6); emit8(sec, 0xC0 | (left & 7)); emit8(sec, imm & 0xFF); }
    } else {
        if (left == AX_REG_RAX) { emit8(sec, 0xA9); }
        else { emit8(sec, 0xF7); emit8(sec, 0xC0 | (left & 7)); }
        if (sz == 2) { emit8(sec, imm & 0xFF); emit8(sec, (imm >> 8) & 0xFF); } else emit32(sec, imm);
    }
}

void ax_x64_imul_rr(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_reg_t src) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, 0xAF);
    emit8(sec, 0xC0 | ((dst & 7) << 3) | (src & 7));
}
void ax_x64_imul_rm(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, ax_x64_mem_t src) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, dst, src);
    emit8(sec, 0x0F);
    emit8(sec, 0xAF);
    emit_modrm_sib_disp(sec, dst, src);
}

void ax_x64_cqo(ax_section_t *sec) { emit8(sec, 0x48); emit8(sec, 0x99); }
void ax_x64_cdq(ax_section_t *sec) { emit8(sec, 0x99); }

void ax_x64_idiv_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t src) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, AX_REG_NONE, src);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7);
    emit8(sec, 0xF8 | (src & 7)); // 11 111 (7) rm
}
void ax_x64_idiv_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t src) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, AX_REG_NONE, src);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7);
    emit_modrm_sib_disp(sec, 7, src);
}
void ax_x64_div_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t src) {
    emit_sz(sec, sz);
    emit_rex_rr(sec, sz, AX_REG_NONE, src);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7);
    emit8(sec, 0xF0 | (src & 7)); // 11 110 (6) rm
}
void ax_x64_div_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t src) {
    emit_sz(sec, sz);
    emit_rex_rm(sec, sz, AX_REG_NONE, src);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7);
    emit_modrm_sib_disp(sec, 6, src);
}

void ax_x64_neg_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7); emit8(sec, 0xD8 | (dst & 7));
}
void ax_x64_neg_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst) {
    emit_sz(sec, sz); emit_rex_rm(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7); emit_modrm_sib_disp(sec, 3, dst);
}
void ax_x64_not_r(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7); emit8(sec, 0xD0 | (dst & 7));
}
void ax_x64_not_m(ax_section_t *sec, uint8_t sz, ax_x64_mem_t dst) {
    emit_sz(sec, sz); emit_rex_rm(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xF6 : 0xF7); emit_modrm_sib_disp(sec, 2, dst);
}

void ax_x64_shl_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xD2 : 0xD3); emit8(sec, 0xE0 | (dst & 7));
}
void ax_x64_shl_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    if (imm == 1) { emit8(sec, sz == 1 ? 0xD0 : 0xD1); emit8(sec, 0xE0 | (dst & 7)); }
    else { emit8(sec, sz == 1 ? 0xC0 : 0xC1); emit8(sec, 0xE0 | (dst & 7)); emit8(sec, imm); }
}
void ax_x64_shr_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xD2 : 0xD3); emit8(sec, 0xE8 | (dst & 7));
}
void ax_x64_shr_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    if (imm == 1) { emit8(sec, sz == 1 ? 0xD0 : 0xD1); emit8(sec, 0xE8 | (dst & 7)); }
    else { emit8(sec, sz == 1 ? 0xC0 : 0xC1); emit8(sec, 0xE8 | (dst & 7)); emit8(sec, imm); }
}
void ax_x64_sar_rcl(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    emit8(sec, sz == 1 ? 0xD2 : 0xD3); emit8(sec, 0xF8 | (dst & 7));
}
void ax_x64_sar_ri(ax_section_t *sec, uint8_t sz, ax_x64_reg_t dst, uint8_t imm) {
    emit_sz(sec, sz); emit_rex_rr(sec, sz, AX_REG_NONE, dst);
    if (imm == 1) { emit8(sec, sz == 1 ? 0xD0 : 0xD1); emit8(sec, 0xF8 | (dst & 7)); }
    else { emit8(sec, sz == 1 ? 0xC0 : 0xC1); emit8(sec, 0xF8 | (dst & 7)); emit8(sec, imm); }
}

void ax_x64_setcc_r(ax_section_t *sec, ax_x64_cc_t cc, ax_x64_reg_t dst) {
    emit_rex_rr(sec, 1, AX_REG_NONE, dst);
    emit8(sec, 0x0F); emit8(sec, 0x90 + cc); emit8(sec, 0xC0 | (dst & 7));
}
void ax_x64_setcc_m(ax_section_t *sec, ax_x64_cc_t cc, ax_x64_mem_t dst) {
    emit_rex_rm(sec, 1, AX_REG_NONE, dst);
    emit8(sec, 0x0F); emit8(sec, 0x90 + cc); emit_modrm_sib_disp(sec, 0, dst);
}

void ax_x64_jcc(ax_section_t *sec, ax_x64_cc_t cc, int32_t rel32) {
    emit8(sec, 0x0F); emit8(sec, 0x80 + cc); emit32(sec, rel32);
}
void ax_x64_jcc_sym(ax_section_t *sec, ax_x64_cc_t cc, ax_symbol_id_t sym) {
    emit8(sec, 0x0F); emit8(sec, 0x80 + cc);
    ax_section_add_reloc(sec, sec->bytes_len, AX_RELOC_X86_64_PC32, sym, -4);
    emit32(sec, 0);
}
void ax_x64_jmp(ax_section_t *sec, int32_t rel32) {
    emit8(sec, 0xE9); emit32(sec, rel32);
}
void ax_x64_jmp_sym(ax_section_t *sec, ax_symbol_id_t sym) {
    emit8(sec, 0xE9);
    ax_section_add_reloc(sec, sec->bytes_len, AX_RELOC_X86_64_PC32, sym, -4);
    emit32(sec, 0);
}

void ax_x64_call(ax_section_t *sec, int32_t rel32) {
    emit8(sec, 0xE8); emit32(sec, rel32);
}
void ax_x64_call_sym(ax_section_t *sec, ax_symbol_id_t sym) {
    emit8(sec, 0xE8);
    ax_section_add_reloc(sec, sec->bytes_len, AX_RELOC_X86_64_PC32, sym, -4);
    emit32(sec, 0);
}
void ax_x64_call_r(ax_section_t *sec, ax_x64_reg_t dst) {
    emit_rex_rr(sec, 8, AX_REG_NONE, dst);
    emit8(sec, 0xFF); emit8(sec, 0xD0 | (dst & 7));
}
void ax_x64_call_m(ax_section_t *sec, ax_x64_mem_t dst) {
    emit_rex_rm(sec, 8, AX_REG_NONE, dst);
    emit8(sec, 0xFF); emit_modrm_sib_disp(sec, 2, dst);
}

void ax_x64_ret(ax_section_t *sec) { emit8(sec, 0xC3); }

void ax_x64_push_r(ax_section_t *sec, ax_x64_reg_t src) {
    bool r = (src >= 8);
    if (r) emit8(sec, 0x41);
    emit8(sec, 0x50 + (src & 7));
}
void ax_x64_push_m(ax_section_t *sec, ax_x64_mem_t src) {
    bool x = (src.index != AX_REG_NONE && src.index >= 8);
    bool b = (src.base != AX_REG_NONE && src.base >= 8);
    if (x || b) emit8(sec, 0x40 | (x ? 2 : 0) | (b ? 1 : 0));
    emit8(sec, 0xFF); emit_modrm_sib_disp(sec, 6, src);
}
void ax_x64_pop_r(ax_section_t *sec, ax_x64_reg_t dst) {
    bool b = (dst >= 8);
    if (b) emit8(sec, 0x41);
    emit8(sec, 0x58 + (dst & 7));
}
void ax_x64_pop_m(ax_section_t *sec, ax_x64_mem_t dst) {
    bool x = (dst.index != AX_REG_NONE && dst.index >= 8);
    bool b = (dst.base != AX_REG_NONE && dst.base >= 8);
    if (x || b) emit8(sec, 0x40 | (x ? 2 : 0) | (b ? 1 : 0));
    emit8(sec, 0x8F); emit_modrm_sib_disp(sec, 0, dst);
}

void ax_x64_int3(ax_section_t *sec) { emit8(sec, 0xCC); }
void ax_x64_jcc8(ax_section_t *sec, ax_x64_cc_t cc, int8_t rel8) { emit8(sec, 0x70 + cc); emit8(sec, rel8); }
void ax_x64_jmp8(ax_section_t *sec, int8_t rel8) { emit8(sec, 0xEB); emit8(sec, rel8); }
