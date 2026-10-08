#include <stdio.h>
#include <assert.h>
#include <signal.h>
#include <stdlib.h>
#include "target/x64/verify/verify.h"
#include "target/x64/frame/frame.h"
#include "target/x64/mir/mi.h"

static void on_abort(int sig) {
    (void)sig;
    _Exit(3);
}

int main(int argc, char **argv) {
    signal(SIGABRT, on_abort);
    
    if (argc < 2) return 0;
    const char *mode = argv[1];
    
    AxArena arena;
    ax_arena_init(&arena, 0);
    
    AxX64MIBody mi = {0};
    mi.arena = arena;
    mi.bbs = AX_ARENA_NEW_ARRAY(&arena, AxX64MIBb, 1);
    mi.bb_count = 1;
    
    AxX64FrameLayout layout = {0};
    layout.frame_size = 0;
    
    if (strcmp(mode, "operand") == 0) {
        AxX64MI *inst = ax_x64_mi_new(&arena, AX_X64_MI_MOV);
        ax_x64_mi_add_op(inst, ax_x64_op_imm(1)); // Invalid dest
        ax_x64_mi_add_op(inst, ax_x64_op_imm(2)); // Invalid src
        mi.bbs[0].first_inst = inst;
        mi.bbs[0].last_inst = inst;
    } else if (strcmp(mode, "align") == 0) {
        mi.shadow_space = 32;
        layout.frame_size = 40; // misaligned! (40+56 = 96? wait 96%16 == 0. Let's use 48. 48+56 = 104 % 16 != 0)
        layout.frame_size = 48;
    } else if (strcmp(mode, "shadow") == 0) {
        mi.shadow_space = 16; // < 32
    } else if (strcmp(mode, "regclass") == 0) {
        AxX64MI *inst = ax_x64_mi_new(&arena, AX_X64_MI_SHL);
        ax_x64_mi_add_op(inst, ax_x64_op_reg(AX_REG_RAX)); // valid dst
        ax_x64_mi_add_op(inst, ax_x64_op_reg(AX_REG_RBX)); // invalid shift register, should be RCX
        mi.bbs[0].first_inst = inst;
        mi.bbs[0].last_inst = inst;
    } else if (strcmp(mode, "framesize") == 0) {
        mi.shadow_space = 32;
        layout.frame_size = 8; // aligned (8+56=64), but < 32
    }
    
    ax_x64_verify(&mi, &layout); // Should ICE!
    
    return 0; // If we reach here, test failed
}
