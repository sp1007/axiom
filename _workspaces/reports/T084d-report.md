# T084d Report — Port x64 Machine Code Encoder to Axiom

## Summary

Ported the Stage-0 C x86-64 machine code binary encoder (`bootstrap/axiom0/src/target/x64/encode/{encode.h,encode.c}`), relocation record emitters and basic-block branch fixup/rodata helpers (`bootstrap/axiom0/src/driver/{emit_obj.c,emit_mc.c,build_native/build.c}`), and standard Windows x64 frame prologue/epilogue + 4KB page stack probe emitters (`bootstrap/axiom0/src/target/x64/frame/frame.c`) to pure Axiom in `compiler/target/x64/encode.ax` (`module compiler.target.x64.encode`).

## Implementation Details

1. **Registers, Condition Codes, and Machine IR Opcodes (`compiler/target/x64/encode.ax`)**:
   - Defined all 16 general-purpose x86-64 register constants (`REG_RAX`..`REG_R15`, `REG_NONE = 255`) and Stage-0 C-compatible aliases (`AX_REG_RAX`..`AX_REG_R15`, `AX_REG_NONE = 255`), plus register predicates (`x64_reg_is_none`, `x64_reg_is_valid`, `x64_reg_is_extended`, `x64_reg_needs_byte_rex`, `x64_reg_low3`) and mnemonic formatters (`x64_reg_name`, `x64_reg_name_sz`).
   - Defined all 16 x86-64 condition codes (`CC_O`..`CC_G`, mnemonic aliases `CC_C`..`CC_NLE`, and `AX_CC_*` aliases) with `x64_cc_invert` and `x64_cc_name`.
   - Defined Machine IR operand kinds (`X64_OP_*`) and opcodes (`X64_MI_*` / `AX_X64_MI_*`) with `x64_mi_opcode_name`.

2. **Addressing Modes & Binary Encoding Primitives**:
   - Implemented `@derive(Copy) pub struct X64Mem` and constructors `x64_mem_base`, `x64_mem_base_disp`, `x64_mem_index`, `x64_mem_index_disp`, `x64_mem_rip`, `x64_mem_frame_rbp`, and `x64_mem_stack_rsp` (with `ax_x64_mem_*` aliases).
   - Implemented little-endian emitters (`x64_emit8`, `x64_emit16`, `x64_emit_i16`, `x64_emit32`, `x64_emit_i32`, `x64_emit64`, `x64_emit_i64`), 16-bit operand size prefix (`x64_emit_sz_prefix`), REX prefix calculation and emission (`x64_rex_rr_byte`, `x64_rex_rm_byte`, `x64_emit_rex_rr`, `x64_emit_rex_rm`), ModR/M and SIB byte encoding (`x64_modrm_byte`, `x64_sib_byte`, `x64_emit_modrm_sib_disp` with `RSP`/`R12` forced SIB and `RBP`/`R13` forced disp8=0 rules), and generic `r/m` and `mem` opcode emitters.

3. **Full x86-64 Instruction Set**:
   - **Data Movement**: `x64_mov_rr`, `x64_mov_rm`, `x64_mov_mr`, `x64_mov_ri` (8/16/32/64-bit `movabs`), `x64_mov_mi`, `x64_movzx_rr`, `x64_movzx_rm`, `x64_movsx_rr`, `x64_movsx_rm`, `x64_lea`.
   - **ALU Operations**: `add`, `or`, `and`, `sub`, `xor`, `cmp` across `_rr`, `_mr`, `_rm`, and `_ri` (including `AL`/`AX`/`EAX`/`RAX` accumulator short forms, `0x83` sign-extended `imm8` compression, and `0x81` `imm16`/`imm32` forms), plus `x64_test_rr`, `x64_test_rm`, `x64_test_ri`.
   - **Multiply, Divide & Unary**: `x64_imul_rr`, `x64_imul_rm`, `x64_mul_r`, `x64_mul_m`, `x64_cqo`, `x64_cdq`, `x64_idiv_r`, `x64_idiv_m`, `x64_div_r`, `x64_div_m`, `x64_neg_r`, `x64_neg_m`, `x64_not_r`, `x64_not_m`.
   - **Bitwise Shifts**: `x64_shl_rcl`, `x64_shl_ri`, `x64_shr_rcl`, `x64_shr_ri`, `x64_sar_rcl`, `x64_sar_ri` (including `0xD0`/`0xD1` `imm == 1` short encodings and `0xC0`/`0xC1` `imm8` encodings).
   - **Branches, Calls, Stack & System**: `x64_setcc_r`, `x64_setcc_m`, `x64_jcc`, `x64_jmp`, `x64_jcc8`, `x64_jmp8`, `x64_call`, `x64_call_r`, `x64_call_m`, `x64_ret`, `x64_push_r`, `x64_push_m`, `x64_pop_r`, `x64_pop_m`, `x64_int3`, `x64_nop`, `x64_align_code`.

4. **Relocations, Branch Fixups, Rodata & Frame Helpers**:
   - **Symbol Relocations (`AX_RELOC_X86_64_PC32`, addend `-4` or `disp - 4`)**: `x64_call_sym`, `x64_lea_sym`, `x64_lea_sym_disp`, `x64_mov_rm_sym`, `x64_mov_rm_sym_disp`, `x64_mov_mr_sym`, `x64_mov_mr_sym_disp`, `x64_jcc_sym`, `x64_jmp_sym`, plus external symbol lookup/deduplication helpers (`x64_find_or_add_extern_sym`, `x64_find_or_add_extern_sym_str`, `x64_call_extern`, `x64_call_extern_str`, `x64_lea_extern`, `x64_lea_extern_str`).
   - **Basic-Block Branch Fixups**: `@derive(Copy) pub struct X64BranchFixup`, `x64_emit_jmp_placeholder`, `x64_emit_jcc_placeholder`, `x64_patch_rel32`, `x64_patch_branch_fixups`, and `x64_compute_rel8`.
   - **Rodata & Panic Sequence**: `x64_emit_rodata_bytes`, `x64_emit_rodata_slice`, and `x64_emit_panic_sequence`.
   - **Windows x64 Frame Prologue/Epilogue**: `x64_emit_prologue_size` (including the `frame_size > 4096` inline 4KB page probe loop) and `x64_emit_epilogue_size`.

## Verification

- Built isolated snapshot `build-snap-T084d` via `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T084d`.
- Ran `python build-snap-T084d/tools/axtest.py --compiler build-snap-T084d/build/axiom0.exe --root build-snap-T084d --filter selfhost/encode --verbose`:
  - `PASS selfhost/encode/qa_encode_instructions.ax [interp]` (142 instruction & addressing-mode fixtures + helper checks)
  - `PASS selfhost/encode/qa_encode_instructions.ax [native]`
  - `PASS selfhost/encode/qa_encode_instructions.ax [native-O1]`
  - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [interp]` (symbol relocations, branch fixup patching, frame prologues/epilogues, stack probe loop, and byte-exact differential `.obj` checks against `relocs.obj` and `ret42.obj`)
  - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [native]`
  - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [native-O1]`
- Ran `python tools/archcheck.py --root build-snap-T084d` and `python tools/archcheck.py --root .`: `188 files scanned, 0 violations`.
- Ran broader suites (`--filter encode`, `--filter mc`, `--filter obj`): all passed with 0 failures.

## Files changed

- `compiler/target/x64/encode.ax`
- `tests/selfhost/encode/qa_encode_instructions.ax`
- `tests/selfhost/encode/qa_encode_relocs_and_frames.ax`

STATUS: COMPLETE round=0
