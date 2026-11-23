# T484 report

## Summary
Implemented `-O1` constant folding of all 8 bit intrinsics (`rotate_left`, `rotate_right`, `leading_zeros`, `trailing_zeros`, `count_ones`, `swap_bytes`, `reverse_bits`, `wrapping_neg`) across all 12 scalar integer types (`i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize`, widths `8..128`) per `spec/SPEC-40-integers.md` (`AXS-INT-022`, `AXS-INT-031`, `AXS-INT-041`) and `ADR-0042` §4.

### Design choice: Option (b) — local constant propagation + folding in `compiler/opt/` over intrinsic MIR expansions
We evaluated Option (a) (new MIR intrinsic rvalue folded by `-O1` and expanded by LIR/interp) against Option (b) (local constant propagation + folding in `compiler/opt/`):
- **Why Option (b) was chosen**:
  1. **Module & lock boundaries**: Option (a) would require adding a new `MirRvalue` kind across modules outside T484's `locks:` (`compiler/verify/verifier.ax` including mixed `(T, u32) -> T` / `(T) -> u32` typechecking and `verify_parse_mir` text parsing, `compiler/mir/mod.ax`, `compiler/own/{cap,init}.ax`, `compiler/mir/{drop,async_lower}.ax`) and would change `-O0` MIR dumps asserted by existing golden tests (`tests/mir/intrinsics/rotate_u8.mir`, `tests/mir/intrinsics/qa_mixed_materialize_and_signed_rotate.mir`).
  2. **Single semantic source of truth**: `mb_build_intrinsic_mir_op` in `compiler/mir/builder.ax` already lowers every bit intrinsic (`8..128` bits, both method syntax and `@intrinsic fn` calls) into canonical shift/mask/bitwise/cast/wrapping-sub MIR operations shared by `interp` and the native backend (`LIR`/`isel`).
  3. **Exact `-O1` collapse to one constant with zero perturbation to non-intrinsic MIR**:
     - Added `MIR_RVALUE_FLAG_INTRINSIC` (`compiler/mir/mir.ax`) and tagged rvalues synthesized by `mb_build_intrinsic_mir_op` (`compiler/mir/builder.ax`).
     - Extended `compiler/opt/const_fold.ax` (`compiler/opt/mod.ax`) with:
       - `do_const_fold_cast`: folds `MIR_CAST_INT_TO_INT` across all 12 scalar integer types (`8..128` bits, narrowing, zero-extension, sign-extension to 64/128 bits, and same-width reinterpretation per `AXS-INT-041`).
       - `opt_extract_shift_amount` & mixed-width shift support in `do_const_fold_binop`: folds `MIR_BINOP_SHL` / `MIR_BINOP_SHR` when the shift amount has a distinct integer type (e.g. `u128 << u32`), while leaving negative or `>= BITS` shift counts unfolded so runtime traps remain intact.
       - `opt_const_fold_in_arena`: records single-definition unborrowed/unprojected scalar constants with CFG dominance checks (`opt_known_dominates_stmt`) and substitutes them into `MIR_RVALUE_FLAG_INTRINSIC` rvalues and `MIR_LOCAL_TEMP` locals derived from them, normalizing `<64`-bit integer constants to their width mask.
     - Iterative `opt_dce` then removes all dead intermediate temporaries, leaving `bb0: { _0 = const <val>; return; }` (1 constant) for every constant-operand bit intrinsic across widths `8..128`, while keeping all non-intrinsic `-O1` MIR dumps byte-identical and preserving `AX_INIT_USE_UNINIT` diagnostics on non-dominating control-flow paths.

## Files changed
- compiler/mir/mir.ax
- compiler/mir/builder.ax
- compiler/opt/const_fold.ax
- compiler/opt/mod.ax
- tests/opt/bit_intrinsics_fold/check_mir_opt_fold.py
- tests/opt/bit_intrinsics_fold/mir_opt_all_widths.ax
- tests/opt/bit_intrinsics_fold/mir_opt_all_widths.test
- tests/opt/bit_intrinsics_fold/mir_opt_direct.test
- tests/opt/bit_intrinsics_fold/run_chains_and_soundness.ax
- tests/opt/bit_intrinsics_fold/run_interp_o1_signed.ax
- tests/opt/bit_intrinsics_fold/run_interp_o1_unsigned.ax
- tests/opt/bit_intrinsics_fold/run_panic_preserved.ax
- tests/opt/bit_intrinsics_fold/run_panic_preserved_o1.ax
- tests/opt/bit_intrinsics_fold/run_signed_all_widths.ax
- tests/opt/bit_intrinsics_fold/run_unsigned_all_widths.ax
- tests/opt/bit_intrinsics_fold/ui_uninit_branch_o1.ax

## Tests
All builds and tests executed inside isolated snapshot `build-snap-T484/` (on `HEAD d89e8b2a48d8`):
- Stage-2/3 bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 4fafb63c8206cbdaae750ffca0fbd37264acd87f0da4d674d0e9870409d5c177` (8,415,744 bytes).
  - `STAGE0-GUARD OK`: `axiomc1` and seeded stage produced byte-identical `.exe` on 6 smoke programs (`-O1`, incl. `Xin chào thế giới`).
- New suite `tests/opt/bit_intrinsics_fold` (`--no-cache -j 2`): `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`):
  - `mir_opt_all_widths.test` + `mir_opt_direct.test`: verified `inspect --emit=mir-opt -O1` collapses all 8 bit intrinsics across all 12 integer types (`8..128` bits, 96 canonical width×intrinsic functions + 45 boundary/const/let/`@intrinsic`/chained functions = 141 single-block functions + 3 unary-negation expression functions) to `_0 = const <val>;` matching an independent Python big-int oracle, while keeping runtime-operand controls unfolded.
  - `run_unsigned_all_widths.ax`, `run_interp_o1_unsigned.ax`, `run_signed_all_widths.ax`, `run_interp_o1_signed.ax`, `run_chains_and_soundness.ax`, `run_panic_preserved.ax`, `run_panic_preserved_o1.ax`: bit-for-bit identical stdout/exit/panic results across `interp O0`, `interp -O1`, `native O0`, and `native -O1` (`WEAK-NATIVE: 0`).
  - `ui_uninit_branch_o1.ax`: verified maybe-uninitialized variable across branch still reports `AX_INIT_USE_UNINIT` under `-O1`.
  - Mutation liveness proof (in `build-snap-T484/` only, then restored byte-identical): mutating `// stdout: 165\n` -> `// stdout: 166\n` in `run_unsigned_all_widths.ax` failed `[interp]`, `[native]`, and `[native-O1]` (`TOTAL 3 PASS 0 FAIL 3`); restoring passed `3/3`.
- Targeted suites (`--no-cache -j 2 --filter opt --filter run/intrinsics --filter run/int128_interp --filter mir/intrinsics`): `TOTAL 426 PASS 426 FAIL 0 SKIP 0 XFAIL 0`.
- Full per-task gate (`python tools/taskgate.py --task T484 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TOTAL 810 PASS 808 FAIL 0 SKIP 2 XFAIL 0` (`TASKGATE T484 exit=0`).
  - `WEAK-NATIVE: 0` in T484's own/changed tests; `BASELINE OK`; `archcheck`: 0 violations (232 files); `smoke-check`: OK.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0