# Task T084b Report: Port Windows x64 ABI Lowering to Axiom (`compiler/abi/`)

## Summary of Changes

Ported the Windows x64 ABI classification and LIR ABI lowering subsystem (`bootstrap/axiom0/src/abi/{abi.h,win64.c,lower.c}`) to Axiom under `compiler/abi/`:

1. **`compiler/abi/win64.ax` (`module compiler.abi.win64`)**:
   - **Location Kinds & Target ABI Identifiers**: Defined `ABI_LOC_REG` (`0`), `ABI_LOC_STACK` (`1`), `ABI_LOC_INDIRECT` (`2`) (along with `AX_ABI_LOC_*` aliases) and `ABI_KIND_WIN64` (`0`).
   - **Windows x64 Register & Frame Constants**: Defined general-purpose register constants (`WIN64_REG_RAX = 0` .. `WIN64_REG_R15 = 15`, `WIN64_REG_NONE = 0xFFFFFFFF`), `WIN64_SHADOW_SPACE = 32`, `WIN64_STACK_ALIGN = 16`, `WIN64_STACK_SLOT_SIZE = 8`, `WIN64_MAX_REG_ARGS = 4`, `WIN64_RET_REG = 0`, `WIN64_CALLEE_SAVED_COUNT = 7`, `WIN64_CALLEE_SAVED_BYTES = 56`, and register tables `WIN64_ARG_REGS` (`[RCX=1, RDX=2, R8=8, R9=9]`), `WIN64_CALLER_SAVED_REGS` (`[RAX, RCX, RDX, R8, R9, R10, R11]`), and `WIN64_CALLEE_SAVED_REGS` (`[RBX, RSI, RDI, R12, R13, R14, R15]`).
   - **ABI Data Model (`AbiLoc`, `AbiArg`, `AbiSig`, `Abi`)**: Ported `AxAbiLoc`, `AxAbiArg`, `AxAbiSig`, and `AxAbi`. To preserve 100% compatibility with the C `union { uint32_t reg; uint32_t offset; }` in `AxAbiLoc` (used by `lower.c` and `isel.c` when inspecting indirect stack arguments at offset `>= 32`), all `AbiLoc` constructors (`abi_loc_reg`, `abi_loc_stack`, `abi_loc_indirect_reg`, `abi_loc_indirect_stack`) populate both `.reg` and `.offset` with the 32-bit location payload.
   - **Classification & Layout Helpers**: Implemented `win64_arg_reg`, `win64_is_caller_saved`, `win64_is_nonvolatile_gp`, `win64_is_callee_saved`, `win64_needs_indirect` (direct by-value for sizes `0, 1, 2, 4, 8`; indirect by pointer for `3, 5, 6, 7, >8`), `win64_align_stack`, `win64_outgoing_args_size`, `abi_loc_reg_or_offset`, `abi_loc_is_indirect_in_reg`, and `abi_loc_is_indirect_on_stack`.
   - **Signature Classification (`win64_classify`, `abi_classify`)**: Ported `win64_classify` from `bootstrap/axiom0/src/abi/win64.c`, handling `TY_FN`, `TY_CLOSURE` (unwrapping `fn_type`), `TY_BUILTIN_PRINT` (`str` parameter, 16 bytes -> `ABI_LOC_INDIRECT` in `RCX`), and `TY_BUILTIN_PRINT_INT` (`i64` parameter, 8 bytes -> `ABI_LOC_REG` in `RCX`), hidden return pointer (`sret`) allocation in `RCX` (`arg_idx = 0`) shifting subsequent parameters to `RDX`, `R8`, `R9`, and 8-byte stack slots starting at offset `32` (`WIN64_SHADOW_SPACE`), and computing `shadow_space = 32` and `stack_args_size`.
   - **LIR ABI Lowering Pass (`lir_lower_abi_in_arena`, `lir_lower_abi`, `ax_lir_lower_abi`, `lir_lower_win64_abi`)**: Ported `ax_lir_lower_abi` from `bootstrap/axiom0/src/abi/lower.c`, lowering incoming and outgoing `LIR_INST_ABI_ARG` and `LIR_INST_ABI_RESULT` instructions, scanning forward/backward for the associated `LIR_INST_CALL` instruction, and updating `body.frame_req.max_outgoing_args_bytes` and `body.frame_req.requires_16_byte_alignment`.
2. **`compiler/abi/mod.ax` (`module compiler.abi`)**:
   - Re-exported the complete public API of `compiler.abi.win64`.
3. **Selfhost Unit Tests (`tests/selfhost/abi/`)**:
   - `tests/selfhost/abi/qa_abi_win64_classify.ax`: Tests all register/caller-saved/callee-saved/alignment/indirect-size rules, ports all test cases from `tests/mc/isel/cdriver_abi.c`, `cdriver_abi_edge.c`, `cdriver_abi_qa.c`, and `cdriver_abi_qa2.c`, and tests `TY_BUILTIN_PRINT`, `TY_BUILTIN_PRINT_INT`, `TY_CLOSURE`, and null/non-function guards.
   - `tests/selfhost/abi/qa_abi_lir_lower.ax`: Tests end-to-end MIR -> LIR -> `lir_lower_win64_abi` lowering of incoming parameters, outgoing call arguments (including `sret` register shifting and indirect stack arguments), call `ABI_RESULT` and standalone return `ABI_RESULT` fallback, `max_outgoing_args_bytes` tracking across multiple calls, and `TY_BUILTIN_PRINT` / `TY_BUILTIN_PRINT_INT` lowering.

## Files changed

- `compiler/abi/mod.ax`
- `compiler/abi/win64.ax`
- `tests/selfhost/abi/qa_abi_lir_lower.ax`
- `tests/selfhost/abi/qa_abi_win64_classify.ax`

## Test Verdict

- `python tools/archcheck.py --root .` (in `build-snap-T084b`): `archcheck: 188 files scanned, 0 violations`
- `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build` (in `build-snap-T084b`): Built cleanly with 0 warnings.
- `ctest --test-dir build --output-on-failure` (in `build-snap-T084b`): `18/18` passed (including `ct_mc_isel_cdriver_abi`, `ct_mc_isel_cdriver_abi_edge`, `ct_mc_isel_cdriver_abi_qa`, `ct_mc_isel_cdriver_abi_qa2`).
- `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/abi --verbose` (in `build-snap-T084b`):
  - `PASS selfhost/abi/qa_abi_lir_lower.ax [interp]`
  - `PASS selfhost/abi/qa_abi_lir_lower.ax [native]`
  - `PASS selfhost/abi/qa_abi_lir_lower.ax [native-O1]`
  - `PASS selfhost/abi/qa_abi_win64_classify.ax [interp]`
  - `PASS selfhost/abi/qa_abi_win64_classify.ax [native]`
  - `PASS selfhost/abi/qa_abi_win64_classify.ax [native-O1]`
  - `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/axtest.py --compiler build/axiom0.exe -j 16 --filter mc/` (in `build-snap-T084b`): `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0`

STATUS: COMPLETE round=0
