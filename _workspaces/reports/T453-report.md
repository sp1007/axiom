# T453 report
## Summary
E12.1 native 128-bit integers: i128/u128 values are lowered in LIR as a pair of registers, follow the Win64 16-byte ABI, and compile to x86-64 code that has been checked byte by byte against GNU as (SPEC-40 AXS-INT-010..012, SPEC-04 AXS-EXT-050). A previous agent had left partial work. I kept it, checked it and finished it:

- LIR (compiler/lir/lir.ax, builder.ax, mod.ax): adds a 16-byte const_hi and the register-pair instruction set: const128, pair_*, i128.{add,sub,mul,sdiv,srem,udiv,urem,and,or,xor,shl,shr,sar,neg,bitnot,icmp.*}, the {s,u}{add,sub,mul}_overflow and sdiv/srem_overflow checks, {s,u}sat_{add,sub,mul}, and sext/zext/trunc. Lowering covers binary, unary, cast, overflow-check, saturating, aggregate-field and print_int operations; print_int(i128/u128) uses an inline decimal loop that calls __ax_host_print.
- ABI (compiler/abi/win64.ax): i128 and u128 parameters are 16 bytes and passed ABI_LOC_INDIRECT, i.e. by reference. 16-byte returns go through the hidden sret pointer in RCX. Both are uniform across caller and callee (AXS-INT-011, rules 1-3). I fixed an axiom0 parse error (a struct literal inside an if condition) and a TypeId move error that had broken Stage 1.
- isel (compiler/target/x64/isel.ax):
  - ADD+ADC and SUB+SBB. Compares are SUB/SBB followed by SETcc. The checked forms use the OF or CF flag of the high limb.
  - Wrapping MUL is a one-operand MUL plus IMUL cross terms. Checked and saturating MUL use an exact 256-bit product (with a signed correction) and test the high limbs.
  - Shifts are SHLD/SHRD/SHL/SHR/SAR by CL, then `test rcx, 64` with CMOVNE to select the limb.
  - Saturation is branch-free with CMOVB, CMOVO or CMOVNE.
  - sdiv128 takes absolute values, runs udiv128, then fixes the sign.
- Machine IR and encoding (compiler/target/x64/encode.ax, frame.ax):
  - New opcodes ADC, SBB, SHLD, SHRD, DIV, IMUL1, NEG, NOT, BSWAP, BSR, BSF, LZCNT, TZCNT and POPCNT, plus the pseudo-op UDIV128, are now encoded. Before this the encoder silently dropped them, so the native build produced no ADC at all. I also added the encoding for TEST r, imm.
  - UDIV128 expands as follows. When the divisor fits in 64 bits it emits two chained DIVs. Otherwise it runs a 128-step restoring loop built from ADD/ADC/SUB/SBB with rel8 jumps that are patched in place.
  - frame.ax now knows these opcodes everywhere it needs to:
    - LIR liveness for all i128 kinds.
    - Physical register def/use masks for the regalloc and the peephole pass (UDIV128 clobbers RAX, RCX, RDX and R8-R11).
    - EFLAGS effects: ADC and SBB read flags, SHLD/SHRD by CL may leave them unchanged, NOT and BSWAP preserve them.
    - The peephole store-forwarding scan stops at UDIV128, DIV and IMUL1 and respects the defs of the new opcodes.
    - Callee-saved register detection.
  - Without this, -O1 and the peephole pass would corrupt the instruction sequences.
- Tests:
  - Removed `native-after: T453` from all 28 files in tests/run/int128_interp. `grep -rn "native-after: T453" tests` now prints nothing. tests/opt/int128 had no such directive.
  - tests/run/int128_native: arithmetic matrices, every shift and rotate count from 0 to 127, a seeded udiv/sdiv stress test that exercises both udiv128 paths, casts in both directions, and Win64 call-boundary checks (stack arguments, sret, structs holding 128-bit fields, recursion). The expected output is computed with exact integers by regen_expected.py.
  - 128-bit rows in tests/run/saturating_native (i128 and u128).
  - LIR and MI emission checks in tests/lir/int128.
  - tests/encode/int128: 75 GNU-as-verified vectors run against the live encode.ax in interp, -O0 and -O1. When as and objdump are on PATH the table is also re-assembled with GNU as to catch drift. I confirmed by mutation that both checks fail on a wrong byte.
  - The verbatim encode.ax copy inside tests/encode/axiom/gnu_as_vectors.ax is refreshed. `tools/gen_encode_tests.py check` reports OK and encode_tests.inc is unchanged.
  - The three T481a ICE expectations in tests/ui/backend_ice expected T453 to be missing. With the coordinator's approval I turned them into positive checks and renamed the .mir input to sat_u128_lowered.mir.

## Decisions (for the architect)
1. **Bit intrinsics.** count_ones, leading/trailing_zeros, swap_bytes, reverse_bits and the rotates reach the backend already expanded by MIR (T452). So isel does not choose LZCNT, TZCNT, POPCNT or BSWAP for them. Those MI opcodes and encoders do exist and are byte-verified. LZCNT, TZCNT and POPCNT need ABM/BMI1, which baseline x86-64 does not guarantee, so selecting them belongs with CPU-feature dispatch (E12.5).
2. **MULX.** Not used, because it needs BMI2. The one-operand MUL/IMUL forms give the same results on baseline x86-64.
3. **16-byte returns.** These use the sret pointer rather than RAX:RDX. AXS-INT-011 §2 allows either form as long as it is used consistently.
4. **udiv128.** This is an MI pseudo-op expanded at encode time, with the DIV fast path and a restoring loop. I did not implement Knuth D. Correctness is shown by divrem_stress.ax.
5. **Narrow saturation (T481).** I left the existing correct expansion unchanged. All of saturating_native is green.
6. **Spec file names.** SPEC-40 names compiler/lir/lower.ax and compiler/backend/x64. The real modules are compiler/lir/builder.ax and compiler/target/x64.

## Files changed
- compiler/abi/mod.ax
- compiler/abi/win64.ax
- compiler/lir/builder.ax
- compiler/lir/lir.ax
- compiler/lir/mod.ax
- compiler/target/x64/encode.ax
- compiler/target/x64/frame.ax
- compiler/target/x64/isel.ax
- compiler/target/x64/mod.ax
- tests/encode/axiom/gnu_as_vectors.ax
- tests/run/int128_interp/arith_basic.ax
- tests/run/int128_interp/bit_intrinsics.ax
- tests/run/int128_interp/neg_carry.ax
- tests/run/int128_interp/panics_div_zero.ax
- tests/run/int128_interp/panics_overflow_add.ax
- tests/run/int128_interp/panics_overflow_div.ax
- tests/run/int128_interp/panics_shift.ax
- tests/run/int128_interp/pattern_d.ax
- tests/run/int128_interp/qa_matrix_i128.ax
- tests/run/int128_interp/qa_matrix_i128_fold.ax
- tests/run/int128_interp/qa_matrix_u128.ax
- tests/run/int128_interp/qa_matrix_u128_fold.ax
- tests/run/int128_interp/qa_neg_lowword.ax
- tests/run/int128_interp/qa_no_panic_at_limits.ax
- tests/run/int128_interp/qa_panic_i128_mul_2p64_2p63.ax
- tests/run/int128_interp/qa_panic_i128_mul_min_m1.ax
- tests/run/int128_interp/qa_panic_i128_neg_min.ax
- tests/run/int128_interp/qa_panic_i128_rem_min_m1.ax
- tests/run/int128_interp/qa_panic_i128_rem_zero.ax
- tests/run/int128_interp/qa_panic_i128_shr_neg_amount.ax
- tests/run/int128_interp/qa_panic_i128_sub_underflow.ax
- tests/run/int128_interp/qa_panic_u128_add_max.ax
- tests/run/int128_interp/qa_panic_u128_div_zero.ax
- tests/run/int128_interp/qa_panic_u128_mul_2p64_2p64.ax
- tests/run/int128_interp/qa_panic_u128_shl_128.ax
- tests/run/int128_interp/qa_panic_u128_shr_200.ax
- tests/run/int128_interp/qa_panic_u128_sub_borrow_word.ax
- tests/run/int128_interp/saturating.ax
- tests/ui/backend_ice/sat_u128_emit_lir.test
- tests/ui/backend_ice/sat_u128_emit_mc.test
- tests/ui/backend_ice/sat_u128_emit_mi.test
- tests/ui/backend_ice/sat_u128_unsupported.mir
- tests/encode/int128/coff_stub.ax.in
- tests/encode/int128/encode_int128.py
- tests/encode/int128/encode_int128.test
- tests/lir/int128/int128_ops_lir.ax
- tests/lir/int128/int128_ops_lir.test
- tests/lir/int128/int128_ops_mi.test
- tests/run/int128_native/abi_calls.ax
- tests/run/int128_native/arith_matrix_i128.ax
- tests/run/int128_native/arith_matrix_u128.ax
- tests/run/int128_native/casts.ax
- tests/run/int128_native/divrem_stress.ax
- tests/run/int128_native/regen_expected.py
- tests/run/int128_native/shifts_i128.ax
- tests/run/int128_native/shifts_u128.ax
- tests/run/saturating_native/i128_saturating.ax
- tests/run/saturating_native/u128_saturating.ax
- tests/ui/backend_ice/sat_u128_lowered.mir
## Tests
- Build: `python build-snap-T453/tools/build_axiomc.py --out build-snap-T453/build`. Result: BUILD-AXIOMC OK, fixed point O1 OK, STAGE0-GUARD OK.
- Full suite: `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --gate -j 2`, run in the snapshot. Result: TOTAL 4627, PASS 4600, FAIL 0, SKIP 27. The global WEAK-NATIVE count of 143 is the pre-existing baseline; none of those are T453 tests.
- Targeted run with --no-cache over ui/backend_ice, run/int128*, run/saturating_native, lir/int128, encode/int128, encode/axiom and opt/int128: TOTAL 163, PASS 163, WEAK-NATIVE 0.
- `bundles_current` filter: 34 of 34 PASS. `archcheck.py`: 229 files, 0 violations. `tools/gen_encode_tests.py check`: OK (10211 vectors).
## Spec deviations
None beyond the decisions above, all of which are allowed by SPEC-40 AXS-INT-011/012.
## Follow-ups
- Pre-existing, not caused by T453: native `print_int` of a u64 value of 2^63 or more prints a negative number. The interpreter prints it correctly. For example, `print_int(18446744073709551615u64)` prints -1 natively. Suggested task: lower print_int for unsigned 64-bit arguments with unsigned formatting.
- The legacy `--emit=mc` path (x64_encode_mi_inst_mc, which mirrors axiom0's emit_mc.c) does not encode SETcc, CMOVcc, TEST and several other ALU forms, for any width. Real builds use the object path, which does encode them.

STATUS: COMPLETE round=0
