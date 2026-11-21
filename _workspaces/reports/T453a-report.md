# T453a report — native `print_int` of u64/usize >= 2^63

## Summary
`print_int(x)` with an unsigned 64-bit operand (`u64`, `usize`) was lowered to a call of the hand-written signed 64-bit stub
`__ax_host_print_int` (`compiler/link/import.ax`), so values >= 2^63 printed as negative numbers natively (interp was correct).
Fix in `compiler/lir/builder.ax` (`TY_BUILTIN_PRINT_INT` call lowering): an operand whose type kind is `TY_U64` or `TY_USIZE` is
now routed through the existing `lower_print_int128_call` with `is_signed = false` and target type `u128`, so
`lower_operand_128` zero-extends it (`LIR_INST_I128_ZEXT`, or an `emit_const128` for constants, which also covers `-O1`
constant-folded arguments) and the unsigned decimal loop formats it. Signed types and narrow unsigned types (u8/u16/u32, which are
already held zero-extended) keep the host routine unchanged, so no new code size for them and the stub is untouched.

## Design decisions
- Reused the 128-bit unsigned formatting path rather than adding a new host routine: no new hand-written machine code (ADR-0002
  spirit), no change to `compiler/link/import.ax` (listed in `paths:` but not needed).
- Only `u64`/`usize` are routed: narrow unsigned operands print correctly today (tests `narrow_and_signed.ax` pin that, including
  computed/wrapped narrow values in `computed.ax`).

## Tests (`tests/run/print_int_unsigned/`, default modes interp + native + native-O1, exact `// stdout:`)
- `u64_edges.ax`: u64 / usize at 0, 2^63-1, 2^63, 2^63+1, 2^64-2, 2^64-1, a mid value.
- `narrow_and_signed.ax`: u8/u16/u32 max and sign-bit values; signed `-1i64`, `i64.MIN`, `i64.MAX`, i8/i16/i32 MIN, `-1isize`.
- `computed.ax`: non-constant values: `wrapping_sub`, shifts, `as` casts from `-1i64`, struct fields, calls, narrow wrapping results,
  a loop-derived value.
- Note: `print_int` writes no newline, so each test prints `"\n"` between values.
- Mutation evidence: with the pre-fix compilers from `_workspaces/artifacts/compiler-cache` (`axiomc2_O1_27c02f54...`,
  `axiomc2_O1_6c6ca8c9...`, `--no-cache`), `u64_edges.ax` and `computed.ax` FAIL `[native]` and `[native-O1]` ("interp/native
  disagree", stdout differs at byte 22 / byte 0); with the fixed `axiomc2` all 9 results PASS, WEAK-NATIVE 0.

## Results (in `build-snap-T453a`, Release stage-0 clang)
- `tools/build_axiomc.py --out build`: BUILD-AXIOMC OK, stage-2/stage-3 (O1) fixed point holds (sha256 87f4350e38bda937...), STAGE0-GUARD OK
  (log `_workspaces/T453a_build.log`).
- `axtest --filter print_int_unsigned`: TOTAL 9 PASS 9, WEAK-NATIVE 0.
- `axtest --filter run/numeric/`: TOTAL 832 PASS 832. `axtest --filter conformance/p12`: TOTAL 472 PASS 472.
- Task gate: `python tools/taskgate.py --task T453a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
  (log `_workspaces/T453a_taskgate.log`, JSON `_workspaces/artifacts/taskgate-T453a.json`): exit 0, `TOTAL 201 PASS 190 FAIL 0 SKIP 11 XFAIL 0`,
  failing ids none, baseline OK, archcheck clean (232 files), WEAK-NATIVE 3 in the run, 0 in the task's own/changed tests. The affected
  set included the selfhost lir/abi/backend/driver/obj_link_driver groups (all pass).
- `grep -rn "native-after: T453a" tests` prints nothing.

## Follow-ups
- None. (`print_int` of a pointer-typed value is not routed; typeck does not accept it as an integer argument.)

## Files changed
- compiler/lir/builder.ax
- tests/run/print_int_unsigned/u64_edges.ax
- tests/run/print_int_unsigned/narrow_and_signed.ax
- tests/run/print_int_unsigned/computed.ax

STATUS: COMPLETE round=0
