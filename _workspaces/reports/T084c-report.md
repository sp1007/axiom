# T084c Report — Port x86-64 Instruction Selection & Frame Lowering to Axiom

## Summary

Ported the x86-64 Machine IR (`X64MI`) data model, `.mi` text printer, naive instruction selector (`x64_isel`), Win64 stack frame lowerer (`x64_frame_lower`), prologue/epilogue and `_chkstk`-equivalent page-probe emitter, post-lowering Machine IR verifier (`x64_verify`), and `.mc`/`.obj` emission helpers from `bootstrap/axiom0/src/target/x64/{mir,isel,frame,verify}` and `bootstrap/axiom0/src/driver/{emit_mc.c,emit_obj.c,build_native/build.c}` to Axiom under `compiler/target/x64/`.

## Files changed

- compiler/target/x64/frame.ax
- compiler/target/x64/isel.ax
- compiler/target/x64/mod.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax

## Files Created

1. [`compiler/target/x64/isel.ax`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/isel.ax)
   - **Machine IR Data Model (`X64Op`, `X64MI`, `X64MIBb`, `X64MIStr`, `X64MIBody`)**:
     - Operand kinds `X64_OP_NONE` (`0`), `X64_OP_REG` (`1`), `X64_OP_IMM` (`2`), `X64_OP_MEM` (`3`), `X64_OP_FRAME` (`4`), `X64_OP_SYM` (`5`) and constructors (`x64_op_none`, `x64_op_reg`, `x64_op_imm`, `x64_op_mem`, `x64_op_mem_base`, `x64_op_mem_disp`, `x64_op_mem_rip`, `x64_op_frame`, `x64_op_sym`) plus `AX_X64_*` aliases.
     - Opcodes `X64_MI_MOV` (`0`) through `X64_MI_RET` (`22`) matching `AxX64MIOpcode` in `bootstrap/axiom0/src/target/x64/mir/mi.h`.
     - Arena-allocated instruction list and basic-block constructors (`x64_mi_body_new`, `x64_mi_new`, `x64_mi_emit`, `x64_mi_emit_sz`, `x64_mi_emit1`, `x64_mi_emit0`, `x64_mi_body_add_str`).
   - **Machine IR Printer (`x64_mi_print`, `x64_mi_print_op`, `x64_mi_opcode_name`)**:
     - Byte-for-byte port of `ax_x64_mi_print` from `bootstrap/axiom0/src/target/x64/mir/mi.c` into `DiagBuffer`, formatting `frame_req: shadow=<u32> args_size=<u32>\n`, `bb<id>:\n`, and operands (`reg`, `imm`, `[rip + disp]`, `[base + index*scale +/- disp]`, `[frame#slot +/- offset]`, `sym#id`).
   - **x86-64 Instruction Selection (`x64_isel_in_arena`, `x64_isel`, `ax_x64_isel`)**:
     - Full port of `ax_x64_isel` from `bootstrap/axiom0/src/target/x64/isel/isel.c`:
       - Callee `sret` hidden pointer save (`mov [frame#0 + 0], rcx`) when return slot `#0` is passed indirectly in memory (`size > 8` or non-power-of-two size).
       - Constants (`LIR_INST_CONST`, `LIR_INST_FLOAT_CONST`, `LIR_INST_BOOL_CONST`), string literals (`LIR_INST_STR_CONST` registering `.rdata` symbols starting at `100000` and emitting `LEA [frame#dst], sym#id` + length store at `+8`), and function addresses (`LIR_INST_FN_ADDR`).
       - Binary ALU (`ADD`, `SUB`, `MUL`, `BITAND`, `BITOR`, `BITXOR`) with `emit_trunc` sub-64-bit sign/zero-extension (`SHL`/`SAR` for signed 8/16/32-bit, `AND 0xFF`/`0xFFFF` and `SHL 32`/`SHR 32` for unsigned).
       - Shifts (`SHL`, `SHR`, `SAR`) using `RCX` (`CL`) shift count + `emit_trunc`.
       - Division and remainder (`SDIV`, `SREM`, `UDIV`, `UREM`) with `IDIV` (`RAX` sign-extended into `RDX` via `SAR RDX, 63`).
       - Checked arithmetic overflow intrinsics (`SADD_OVERFLOW`, `SSUB_OVERFLOW`, `SMUL_OVERFLOW` with 32-bit bounds check `[-2147483648, 2147483647]` and 64-bit `SETCC CC_O`, `UADD_OVERFLOW`, `USUB_OVERFLOW`, `UMUL_OVERFLOW` with `MUL` and `SETCC CC_B`/`CC_O`).
       - Integer comparisons (`LIR_INST_ICMP` for `EQ`, `NE`, `SLT`, `SLE`, `SGT`, `SGE`, `ULT`, `ULE`, `UGT`, `UGE`) and unary ops (`NEG`, `NOT`).
       - Win64 ABI argument/parameter lowering (`LIR_INST_ABI_ARG` incoming/outgoing for `ABI_LOC_REG`, `ABI_LOC_STACK`, `ABI_LOC_INDIRECT`), calls (`LIR_INST_CALL` direct symbol and indirect register with `sret` in `RCX` and `max_call_stack_offset` tracking), and call results (`LIR_INST_ABI_RESULT` for register and indirect aggregate copy).
       - Memory operations (`LIR_INST_STACK_ADDR`, `LIR_INST_LOAD` with sign/zero extension and multi-chunk aggregate copy, `LIR_INST_STORE` with multi-chunk aggregate copy, `LIR_INST_MEMCPY`).
       - Terminators (`LIR_TERM_SWITCH`, `LIR_TERM_ASSERT`, `LIR_TERM_JMP`, `LIR_TERM_JCC`, `LIR_TERM_RETURN`).

2. [`compiler/target/x64/frame.ax`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/frame.ax)
   - **Stack Frame Lowering (`X64FrameLayout`, `x64_frame_lower_in_arena`, `x64_frame_lower`, `x64_frame_lower_raw`)**:
     - Enforces Win64 minimum 32-byte shadow space (`shadow_space < 32 -> 32`).
     - Assigns negative RBP-relative offsets starting below the 56-byte callee-saved register area (`RBX`, `RSI`, `RDI`, `R12`–`R15`), skipping `is_const` slots (`offset = 0`), allocating 8-byte aligned slots for LIR locals and VReg spill slots, and rounding `frame_size` so `(56 + frame_size) % 16 == 0`.
     - Rewrites all `X64_OP_FRAME` operands in-place into `X64_OP_MEM` (`[rbp + slot_offset + field_offset]`).
   - **Prologue & Epilogue Emission (`x64_frame_emit_prologue`, `x64_frame_emit_epilogue`)**:
     - Emits standard Win64 prologue (`push rbp; mov rbp, rsp; push rbx..r15`), 4096-byte page-probe loop (`mov r11, frame_size; sub rsp, 4096; test [rsp], eax; sub r11, 4096; cmp r11, 4096; ja -24; sub rsp, r11`) when `frame_size > 4096`, or direct `sub rsp, frame_size` when `0 < frame_size <= 4096`.
     - Emits matching epilogue (`add rsp, frame_size; pop r15..rbx; pop rbp`).
   - **Machine IR Verifier (`x64_verify_checked`, `x64_verify`, `x64_verify_error_msg`)**:
     - Checks all 10 invariant categories from `bootstrap/axiom0/src/target/x64/verify/verify.c` (`X64_VERIFY_ERR_SHADOW_SPACE`, `ALIGNMENT`, `FRAME_SIZE`, `MEM_MEM`, `OPERAND_FORM`, `IMUL_FORM`, `LEA_FORM`, `SHIFT_REG_CLASS`, `SHIFT_FORM`, `IDIV_FORM`), returning diagnostic codes in `x64_verify_checked` and panicking via `ice` in `x64_verify`.
   - **Machine Code & Object Section Emission (`x64_encode_mi_inst`, `x64_emit_mi_body_mc`, `x64_emit_mi_body_obj`, `x64_dump_mc_hex`)**:
     - Encodes lowered `X64MIBody` into a `Section` with basic-block branch fixup resolution (`x64_patch_rel32`), external symbol relocations, and `.mc` hex dump formatting.

3. [`compiler/target/x64/mod.ax`](file:///d:/projects/compiler/new%20lang/compiler/target/x64/mod.ax)
   - Re-exports the public API of `compiler.target.x64.{encode,isel,frame}`.

4. **Self-Host Tests (`tests/selfhost/isel/`)**:
   - [`tests/selfhost/isel/qa_isel_instructions_and_abi.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/isel/qa_isel_instructions_and_abi.ax): Unit tests for `X64MIBody` construction, `.mi` printing, constants/strings/fn_addr, ALU/shift truncation for `i8`/`u8`/`i16`/`u16`/`i32`/`u32`, `icmp` condition codes, `sdiv`/`srem`/`udiv`/`urem`, signed/unsigned overflow intrinsics, Win64 ABI incoming/outgoing args, direct/indirect calls, aggregate loads/stores, and terminators.
   - [`tests/selfhost/isel/qa_frame_layout_and_verify.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/isel/qa_frame_layout_and_verify.ax): Unit tests for `x64_frame_lower` layout invariants (`(frame_size + 56) % 16 == 0`, `is_const` slot skipping, `X64_OP_FRAME -> X64_OP_MEM` rewriting), prologue/epilogue byte sequences (`frame_size == 4096` vs `frame_size == 4104` page probe), all 10 `x64_verify_checked` error codes + positive verification, and `main_42.mc` + multi-block branch fixup encoding.
   - [`tests/selfhost/isel/qa_isel_diff_golden.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/isel/qa_isel_diff_golden.ax): Differential golden test running `lir_lower_win64_abi` -> `x64_isel_in_arena` -> `x64_mi_print` -> `x64_frame_lower_in_arena` -> `x64_verify_checked` -> `x64_emit_mi_body_mc` -> `x64_dump_mc_hex` across 4 golden cases (`vs1_return`, `vs1_locals`, `vs1_arith`, `main_42`) and comparing byte-for-byte against `axiom0` golden `.mi` and `.mc` outputs.
   - [`tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax): Seam and edge-case tests covering string table growth past 16 entries, non-power-of-two small aggregate and closure calls, sub-64-bit load extensions, `.mi` printer edge cases (`INT64_MIN`, displacement-only `[0]`/`[-16]`, `[rip - 32]`, invalid reg `r?`), sub-64-bit division/modulo overflow bounds, memory-operand shift verification, backward branch fixups, and the full Win64 ABI -> Isel -> Frame -> Verify pipeline seam.

## Round 1 Fixes

1. **`x64_mi_add_string` string table growth (`compiler/target/x64/isel.ax:582`)**:
   - Replaced untyped `ptr_copy_nonoverlapping(body.strings as *const X64MIStr, new_strings, body.string_count)` with explicit byte-level `ptr_copy_nonoverlapping<u8>(body.strings as *const u8, new_strings as *mut u8, lir_mul_usize(body.string_count, size_of<X64MIStr>()))` so all `string_count * 24` bytes are copied when growing `body.strings` past 16 entries.
2. **`x64_mi_print_op` negative displacement-only `X64_OP_MEM` in `--interp` (`compiler/target/x64/isel.ax:814-882`)**:
   - Bound `op` fields (`let disp_i32: i32 = op.mem.disp;` etc.) to scalar locals before casting to `i64`, avoiding `axiom0` interpreter's projected-field cast zero-extension bug and formatting `"[-16]"` identically in `[interp]`, `[native]`, and `[native-O1]`.
3. **`push_u64_dec` / `push_i64_dec` `INT64_MIN` formatting in `[native]` / `[native-O1]` (`compiler/target/x64/isel.ax:751-784`)**:
   - Computed `half = v >> 1u64`, `r5 = (half % 5u64) as u8`, `odd = (v & 1u64) as u8`, `rem = r5 + r5 + odd`, and `v = half / 5u64` in `push_u64_dec` so bit 63 is cleared before signed `IDIV` and no 64-bit unsigned `MUL` is emitted.
4. **Synced `compiler/target/x64/isel.ax` into all 4 `tests/selfhost/isel/*.ax` test files**.

## Verification

Executed in `build-snap-T084c`:
- `python tools/archcheck.py --root .`: `188 files scanned, 0 violations`
- `ctest --test-dir build --output-on-failure`: `18/18 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/isel`: `12/12 PASS` (`[interp]`, `[native]`, `[native-O1]`)
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/encode`: `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/abi`: `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter mc/`: `9/9 PASS`
- `python tools/axtest.py --compiler build/axiom0.exe --filter encode/`: `10/10 PASS`

STATUS: COMPLETE round=1
