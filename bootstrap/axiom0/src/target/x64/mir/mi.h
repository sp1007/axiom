#ifndef AX_TARGET_X64_MIR_MI_H
#define AX_TARGET_X64_MIR_MI_H

#include "target/x64/encode/encode.h"
#include "kernel/arena.h"
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

// Machine operand kind
typedef enum AxX64OpKind {
    AX_X64_OP_NONE,
    AX_X64_OP_REG,
    AX_X64_OP_IMM,
    AX_X64_OP_MEM,      // Explicit memory (base + index + disp)
    AX_X64_OP_FRAME,    // Stack slot based on RBP (or RSP after frame lowering)
    AX_X64_OP_SYM,      // Symbol ID
} AxX64OpKind;

typedef struct AxX64Op {
    AxX64OpKind kind;
    union {
        ax_x64_reg_t reg;
        int64_t imm;
        ax_x64_mem_t mem;
        struct {
            uint32_t slot_id;
            int32_t offset;
        } frame;
        uint32_t sym;
    };
} AxX64Op;

// Machine instruction opcodes for x64
typedef enum AxX64MIOpcode {
    AX_X64_MI_MOV,
    AX_X64_MI_ADD,
    AX_X64_MI_SUB,
    AX_X64_MI_IMUL,
    AX_X64_MI_IDIV, // implicit uses/defs
    AX_X64_MI_AND,
    AX_X64_MI_OR,
    AX_X64_MI_XOR,
    AX_X64_MI_SHL,
    AX_X64_MI_SAR,
    AX_X64_MI_SHR,
    AX_X64_MI_LEA,
    AX_X64_MI_CMP,
    AX_X64_MI_JMP,
    AX_X64_MI_JCC,
    AX_X64_MI_CALL,
    AX_X64_MI_ASSERT,
    AX_X64_MI_PUSH,
    AX_X64_MI_POP,
    AX_X64_MI_SETCC,
    AX_X64_MI_RET,
} AxX64MIOpcode;

// Represents a single machine instruction
typedef struct AxX64MI {
    AxX64MIOpcode opcode;
    AxX64Op ops[3];
    uint8_t op_count;
    struct AxX64MI *next;
    const char *msg;
} AxX64MI;

typedef struct AxX64MIBb {
    uint32_t id;
    AxX64MI *first_inst;
    AxX64MI *last_inst;
} AxX64MIBb;

// The MI function body
typedef struct AxX64MIBody {
    AxArena arena;
    AxX64MIBb *bbs;
    size_t bb_count;
    // Frame requirements passed down from LIR
    uint32_t shadow_space;
    uint32_t stack_args_size;
} AxX64MIBody;

// Helpers to create operands
static inline AxX64Op ax_x64_op_reg(ax_x64_reg_t reg) {
    AxX64Op op = { .kind = AX_X64_OP_REG, .reg = reg };
    return op;
}

static inline AxX64Op ax_x64_op_imm(int64_t imm) {
    AxX64Op op = { .kind = AX_X64_OP_IMM, .imm = imm };
    return op;
}

static inline AxX64Op ax_x64_op_frame(uint32_t slot, int32_t offset) {
    AxX64Op op = { .kind = AX_X64_OP_FRAME, .frame = { .slot_id = slot, .offset = offset } };
    return op;
}

static inline AxX64Op ax_x64_op_sym(uint32_t sym) {
    AxX64Op op = { .kind = AX_X64_OP_SYM, .sym = sym };
    return op;
}

static inline AxX64MI *ax_x64_mi_new(AxArena *arena, AxX64MIOpcode opcode) {
    AxX64MI *mi = AX_ARENA_NEW(arena, AxX64MI);
    mi->opcode = opcode;
    mi->op_count = 0;
    mi->next = NULL;
    return mi;
}

static inline void ax_x64_mi_add_op(AxX64MI *mi, AxX64Op op) {
    if (mi->op_count < 3) {
        mi->ops[mi->op_count++] = op;
    }
}

void ax_x64_mi_print(FILE *out, const AxX64MIBody *body);

#endif
