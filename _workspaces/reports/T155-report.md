# T155 Report: Native `axiomc` Lexer 20-Digit (`u64::MAX`) Integer Literal Parity

## Summary
- Verified natively built `axiomc.exe` (compiled by `build-snap-T155/build/axiom0.exe` with `--stack-reserve=67108864`) against `axiom0.exe` across 19 boundary and overflow integer literal cases (`18446744073709551615u64`, unsuffixed `18446744073709551615`, `_`-separated decimal, `0xFFFF_FFFF_FFFF_FFFFu64`, `0o1_777_777_777_777_777_777_777u64`, 64-bit `0b1111...u64`, `9223372036854775808u64`, `18446744073709551614u64`, and `> u64::MAX` overflow cases in all four bases): **0 mismatches** in exit codes, rendered token streams (`inspect --emit=tokens`), or rendered diagnostics.
- Verified `compiler/lex/scanner.ax`, `compiler/lex/token.ax`, and `compiler/lexer/session.ax` line-by-line against `bootstrap/axiom0/src/lex/lex.c` and `bootstrap/axiom0/src/driver/emit_tokens.c`; no changes to `compiler/lex` or `compiler/lexer` were needed because `compiler/lex/scanner.ax` already uses exact unsigned `u64` accumulation (`val = val * base + d` guarded by `max_q`/`max_r`) and `compiler/lex/token.ax` already formats `u64` without overflow (`(v >> 1u32) / 5u64`).
- Added parity run test `tests/run/parity/lexer/u64_max_literal.ax` (`modes: interp native`), printing hand-derived values `18446744073709551615`, `true` (`0xFFFF_FFFF_FFFF_FFFFu64 == 18446744073709551615u64`), and `4611686018427387904` (`9223372036854775808u64 / 2u64`), verified across `[interp]`, `[native]`, `[native-O1]` and `EQUAL` under `tests/selfhost/obj_link_driver/axiomc_e2e.test`.
- Added selfhost lexer test `tests/selfhost/lex/u64_max_literal.ax.in` (and generated `tests/selfhost/lex/u64_max_literal.ax` from real `compiler/lex` + `compiler/lexer` sources via `tests/selfhost/lex/gen_lex_tests.py`), running in `[interp]`, `[native]`, and `[native-O1]` to verify `18446744073709551615u64` (plus unsuffixed/hex/oct/bin `u64::MAX` forms) lexes into a single `TOK_INT` with `int_val == 0xFFFFFFFFFFFFFFFFu64` (`SUFFIX_U64`, `0` errors) and `18446744073709551616` (plus suffixed/21-digit/hex/oct/bin `> u64::MAX` forms) reports `AX_LEX_INT_OVERFLOW` (`15u32`) with `TOK_FLAG_ERROR`, `int_val == 0u64`, and exact `axiom0` token/diagnostic output.

## Root Cause
The 2026-10-20 `exit 101` (`panic: arithmetic overflow`) on 20-digit literals in natively built `axiomc` had a two-part root cause, resolved by `T140` (`bda91be`) and `T144` (`34e364c`):

1. **Stale `REFERENCE_BUNDLE` signed-`i64` multiplication workaround (`T144`, commit `34e364c`)**:
   - On disk, `compiler/lex/scanner.ax` (lines 873–880, since `T078a` / `73f9f4d`) already used unsigned `u64` accumulation `val = val * base + d;` guarded by exact `u64` quotient/remainder bounds (`max_q = 1844674407370955161u64`, `max_r = 5u64` for base 10; `0x0FFFFFFFFFFFFFFFu64`/`15`, `0x1FFFFFFFFFFFFFFFu64`/`7`, `0x7FFFFFFFFFFFFFFFu64`/`1` for bases 16/8/2). That is why `compiler/lex/scanner.ax` passed in the interpreter and why compiling `1844674407370955161u64 * 10u64 + 5u64` standalone with `axiom0` did not trap.
   - However, prior to `T144`, `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (`axiomc_bundle_text()`) spliced `compiler.lex.scanner` not from `compiler/lex/scanner.ax`, but from `"ref"` (`REFERENCE_BUNDLE = "tests/selfhost/lir/qa_lir_from_ax_a.ax"`), where line 879 had been rewritten to a signed `i64` cast workaround:
     `val = (((val as i64) * (base as i64)) as u64) + d;`
   - That explains every symptom observed in the 2026-10-20 probe:
     - For `9223372036854775808u64` (`i64::MAX + 1`): before the final digit `8`, `val = 922337203685477580`; signed `922337203685477580i64 * 10i64 = 9223372036854775800 <= i64::MAX (9223372036854775807)` did not overflow signed `i64`, and `+ 8u64` was unsigned `u64`, so `9223372036854775808u64` succeeded.
     - For `18446744073709551615u64`: before the final digit `5`, `val = 1844674407370955161`; signed `1844674407370955161i64 * 10i64 = 18446744073709551610 > i64::MAX`, so checked signed 64-bit multiplication (`AX_LIR_INST_SMUL_OVERFLOW` → `imul` + `jo`) trapped with exit 101 `panic: arithmetic overflow` on every `axiomc` command (`inspect --emit=tokens` through `build`).
   - `T144` (`34e364c`) eliminated `REFERENCE_BUNDLE` so `axiomc` and all selfhost bundles assemble `compiler.lex.scanner` verbatim from `compiler/lex/scanner.ax` (`val = val * base + d;`).

2. **Unsigned 64-bit `UDIV`/`UREM` and 64-bit `UMUL_OVERFLOW` in native x64 codegen (`T140`, commit `bda91be`, `AX0-FIX-02`)**:
   - Prior to `T140`, native x64 codegen in `bootstrap/axiom0/src/target/x64/isel/isel.c` and `compiler/target/x64/isel.ax` lowered `/` and `%` on `u64`/`usize` to signed `sar rdx, 63` + `idiv` (sign-extending values with bit 63 set such as `u64::MAX` to `-1`) and treated `size == 8` in `UMUL_OVERFLOW` as a no-op. `T140` implemented unsigned `UDIV`/`UREM` (`xor edx, edx` + `div`) and 64-bit `UMUL_OVERFLOW` (`mul` + `jc`) in lockstep across `axiom0` and `compiler/`, ensuring checked `u64` multiplication in `scanner.ax` and runtime `u64` division/formatting work identically in native builds.

## Registry Changes (`tests/selfhost/obj_link_driver/known_divergent.txt`)
All 8 `tokens`-stage entries cited in `T155` were already resolved and removed before `T155` landed, leaving **0** `tokens`-stage entries in `tests/selfhost/obj_link_driver/known_divergent.txt` (and **0** entries added or modified by `T155`):
- Removed as `EQUAL` in `T144` (`34e364c`):
  - `tests/run/numeric/boundary.ax`
  - `tests/run/numeric/qa_boundary_missing.ax`
  - `tests/run/numeric/qa_overflow_u64.ax`
  - `tests/run/numeric/qa_overflow_usize.ax`
- Moved past `tokens` (`tokens` → `thir`) in `T144` (`34e364c`), then removed as `EQUAL` in `T150` (`318b837`):
  - `tests/run/host/fs/dir.ax`
  - `tests/run/host/fs/file_io.ax`
  - `tests/run/host/fs/metadata.ax`
  - `tests/run/numeric/intrinsic_ops.ax`

## Files changed
- tests/run/parity/lexer/u64_max_literal.ax
- tests/selfhost/lex/gen_lex_tests.py
- tests/selfhost/lex/u64_max_literal.ax
- tests/selfhost/lex/u64_max_literal.ax.in

## Tests
- Targeted `axtest.py` (`-j 1`) in `build-snap-T155` on `parity/lexer` and `selfhost/lex` (`selfhost/lexer` included): `TOTAL 29 PASS 29 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `selfhost/obj_link_driver/{axiomc_e2e,bundles_current,qa_registry_format}.test` (`-j 1`): `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`tests/run/parity/lexer/u64_max_literal.ax` verified `EQUAL` across `-O0`/`-O1` `.obj`/`.exe` and runtime execution).
- `python tools/archcheck.py`: `192 files scanned, 0 violations`.
- Full suite (`python tools/axtest.py --compiler build/axiom0.exe -j 1` in `build-snap-T155`): `TOTAL 2832 PASS 2832 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 165`, `0` weak-native in the new `T155` tests).

## Spec deviations
None.

## Follow-ups
None.

STATUS: COMPLETE round=0
