#include "mi.h"

static const char *const opc_names[] = {
    [AX_X64_MI_MOV] = "mov",
    [AX_X64_MI_ADD] = "add",
    [AX_X64_MI_SUB] = "sub",
    [AX_X64_MI_IMUL] = "imul",
    [AX_X64_MI_IDIV] = "idiv",
    [AX_X64_MI_AND] = "and",
    [AX_X64_MI_OR] = "or",
    [AX_X64_MI_XOR] = "xor",
    [AX_X64_MI_SHL] = "shl",
    [AX_X64_MI_SAR] = "sar",
    [AX_X64_MI_SHR] = "shr",
    [AX_X64_MI_LEA] = "lea",
    [AX_X64_MI_RET] = "ret",
};

static const char *const reg_names[] = {
    [0] = "rax", [1] = "rcx", [2] = "rdx", [3] = "rbx",
    [4] = "rsp", [5] = "rbp", [6] = "rsi", [7] = "rdi",
    [8] = "r8", [9] = "r9", [10] = "r10", [11] = "r11",
    [12] = "r12", [13] = "r13", [14] = "r14", [15] = "r15"
};

static void print_op(FILE *out, const AxX64Op *op) {
    switch (op->kind) {
        case AX_X64_OP_REG:
            fprintf(out, "%s", reg_names[op->reg]);
            break;
        case AX_X64_OP_IMM:
            fprintf(out, "%lld", (long long)op->imm);
            break;
        case AX_X64_OP_MEM:
            // Assuming simple [base + offset] for now
            fprintf(out, "[%s", reg_names[op->mem.base]);
            if (op->mem.index != 0) { // Assume 0 means no index? wait, 4 is RSP which is usually no index in SIB
                fprintf(out, " + %s*%d", reg_names[op->mem.index], 1 << op->mem.scale);
            }
            if (op->mem.disp != 0) {
                if (op->mem.disp > 0) fprintf(out, " + %d", op->mem.disp);
                else fprintf(out, " - %d", -op->mem.disp);
            }
            fprintf(out, "]");
            break;
        case AX_X64_OP_FRAME:
            if (op->frame.offset >= 0) {
                fprintf(out, "[frame#%u + %d]", op->frame.slot_id, op->frame.offset);
            } else {
                fprintf(out, "[frame#%u - %d]", op->frame.slot_id, -op->frame.offset);
            }
            break;
        case AX_X64_OP_NONE:
            break;
    }
}

void ax_x64_mi_print(FILE *out, const AxX64MIBody *body) {
    fprintf(out, "frame_req: shadow=%u args_size=%u\n", body->shadow_space, body->stack_args_size);
    for (size_t i = 0; i < body->bb_count; i++) {
        AxX64MIBb *bb = &body->bbs[i];
        fprintf(out, "bb%u:\n", bb->id);
        AxX64MI *mi = bb->first_inst;
        while (mi) {
            fprintf(out, "  %s", opc_names[mi->opcode]);
            for (int j = 0; j < mi->op_count; j++) {
                if (j > 0) fprintf(out, ", ");
                else fprintf(out, " ");
                print_op(out, &mi->ops[j]);
            }
            fprintf(out, "\n");
            mi = mi->next;
        }
    }
}
