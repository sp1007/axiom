#ifndef AX_LIR_LIR_H
#define AX_LIR_LIR_H

#include "kernel/arena.h"
#include "kernel/id.h"
#include "types/types.h"
#include "mir/mir.h"
#include <stdio.h>

AX_DEFINE_ID(AxLirVRegId);
AX_DEFINE_ID(AxLirStackSlotId);
AX_DEFINE_ID(AxLirBbId);

typedef enum AxLirInstKind {
    // Arithmetic & Logic
    AX_LIR_INST_ADD, AX_LIR_INST_SUB, AX_LIR_INST_MUL, AX_LIR_INST_DIV, AX_LIR_INST_REM,
    AX_LIR_INST_BIT_XOR, AX_LIR_INST_BIT_AND, AX_LIR_INST_BIT_OR,
    AX_LIR_INST_SHL, AX_LIR_INST_SHR,
    AX_LIR_INST_NEG, AX_LIR_INST_NOT, AX_LIR_INST_BITNOT,
    // Compare
    AX_LIR_INST_ICMP_EQ, AX_LIR_INST_ICMP_NE, 
    AX_LIR_INST_ICMP_SLT, AX_LIR_INST_ICMP_SLE, AX_LIR_INST_ICMP_SGT, AX_LIR_INST_ICMP_SGE,
    AX_LIR_INST_ICMP_ULT, AX_LIR_INST_ICMP_ULE, AX_LIR_INST_ICMP_UGT, AX_LIR_INST_ICMP_UGE,
    // Memory
    AX_LIR_INST_LOAD,
    AX_LIR_INST_STORE,
    AX_LIR_INST_STACK_ADDR,
    AX_LIR_INST_OFFSET,
    // Constants
    AX_LIR_INST_CONST,
    // Call
    AX_LIR_INST_CALL,
    AX_LIR_INST_ABI_ARG,
    AX_LIR_INST_ABI_RESULT
} AxLirInstKind;

typedef struct AxLirInst {
    AxLirInstKind kind;
    AxLirVRegId dest; // for instructions that produce a result
    union {
        struct {
            AxLirVRegId lhs;
            AxLirVRegId rhs;
        } binary;
        struct {
            AxLirVRegId operand;
        } unary;
        struct {
            AxLirVRegId ptr;
            TypeId ty;
        } load;
        struct {
            AxLirVRegId ptr;
            AxLirVRegId val;
        } store;
        struct {
            AxLirStackSlotId slot;
        } stack_addr;
        struct {
            uint64_t val;
            TypeId ty;
        } constant;
        struct {
            AxLirVRegId callee; // wait, naive call might take symbol or func address
        } call;
        struct {
            uint32_t index;
            AxLirVRegId val;
            uint32_t loc_kind;
            uint32_t loc_reg_or_offset;
        } abi_arg;
        struct {
            uint32_t index;
            uint32_t loc_kind;
            uint32_t loc_reg_or_offset;
        } abi_result;
    };
} AxLirInst;

typedef enum AxLirTerminatorKind {
    AX_LIR_TERM_JMP,
    AX_LIR_TERM_JCC, // jump conditional
    AX_LIR_TERM_SWITCH,
    AX_LIR_TERM_RETURN,
    AX_LIR_TERM_UNREACHABLE,
} AxLirTerminatorKind;

typedef struct AxLirSwitchTarget {
    uint64_t value;
    AxLirBbId target;
} AxLirSwitchTarget;

typedef struct AxLirTerminator {
    AxLirTerminatorKind kind;
    union {
        AxLirBbId jmp_target;
        struct {
            AxLirVRegId cond;
            AxLirBbId then_target;
            AxLirBbId else_target;
        } jcc;
        struct {
            AxLirVRegId cond;
            AxLirSwitchTarget *targets;
            size_t count;
            AxLirBbId otherwise;
        } switch_int;
    };
} AxLirTerminator;

typedef struct AxLirBb {
    AxLirInst *insts;
    size_t inst_count;
    AxLirTerminator terminator;
} AxLirBb;

typedef struct AxLirStackSlot {
    TypeId ty; // naive lowering just uses MIR local type
} AxLirStackSlot;

typedef struct AxLirVReg {
    TypeId ty;
} AxLirVReg;

typedef struct AxLirFrameReq {
    uint32_t max_outgoing_args_bytes;
    bool requires_16_byte_alignment;
} AxLirFrameReq;

typedef struct AxLirBody {
    AxArena arena;
    AxLirStackSlot *slots;
    size_t slot_count;
    AxLirVReg *vregs;
    size_t vreg_count;
    AxLirBb *bbs;
    size_t bb_count;
    AxLirFrameReq frame_req;
} AxLirBody;

AxLirBody *ax_lir_lower(const AxMirBody *mir, TypeInterner *interner);
void ax_lir_print(FILE *out, const AxLirBody *body);

#endif
