# T457 Report — E12.2: Frontend, typeck & MIR lowering for f32/f64 and the REQ-OWNER-007 mixed-type matrix

## Summary
- **Lexer (`compiler/lex/token.ax`, `scanner.ax`)**: float literals are now converted exactly. The lexer converts the decimal text directly to binary64 (`Token.int_val`) and to binary32 (`Token.char_val`) with roundTiesToEven, so neither result is double-rounded. Overflow flags go in `Token.str_len` (`FLOAT_LIT_F64_OVERFLOW | FLOAT_LIT_F32_OVERFLOW`). The conversion uses only integers (axiom0 has no floating point): base-2^32 big integers, exact long division, and a sticky remainder. It keeps 800 significant digits plus a sticky digit, and decides magnitudes outside 10^-330..10^311 without big-integer arithmetic. `float_bits_from_u128` rounds integer literals to a float type the same way.
  - The code lives in `token.ax`, not in a new `float_lit.ax` module. The reason: the selfhost bundle generators (`tests/selfhost/bundle_common.py` `FULL_MODULE_ORDER`, and the driver and interp_opt `FULL_MODULES`) hard-code the module list. A new module would need generator edits outside this task's paths.
- **Types (`types.ax`, `layout.ax`)**:
  - New kinds: `TY_F32 = 51`, `TY_F64 = 52`, `TY_FLOAT_VAR = 53`. `CONST_FLOAT = 6`.
  - f32 and f64 use sentinel TypeIds `TYPEID_F32 = 0x3FFF0F32` (`type#1073680178`) and `TYPEID_F64 = 0x3FFF0F64` (`type#1073680228`), following the i128 precedent from T451. All interned TypeIds and existing `type#N` goldens are unchanged. The interner scratch block grows from 3 to 5 slots.
  - Float variables: `TypeVarEntry.is_float` and `type_vars_new_float_var`. A float variable unifies only with f32, f64 or another float variable, and defaults to f64.
  - `type_is_float` added. f32, f64 and float variables are Copy. Layout: f32 is 4/4, f64 is 8/8.
- **Typeck (`typeck.ax`)**:
  - `f32`/`f64` type names, suffixed and unsuffixed float literals, float literal patterns (`AXS-FLT-006`), unary `-` on floats, and comparisons are accepted. `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` is no longer reported for floats.
  - Casts: `as` allows IntToFloat, FloatToInt and FloatConvert; `float as bool` stays `AX_TYPE_INVALID_CAST`.
  - Range check: a float literal that rounds to infinity is `AX_TYPE_LITERAL_OUT_OF_RANGE`. This also applies to an integer literal fixed to f32 near 2^128.
  - Index operand of float type: `AX_TYPE_INDEX_NOT_INT` with the word "float".
  - THIR dump prints `f32`, `f64` and `{float}`.
  - **REQ-OWNER-007 matrix** (`check_binary_float`, `AXS-FLT-031..033`):
    - When one operand of an arithmetic or comparison node is floating-point, the node's type is the float join: f32 ⊔ f64 = f64, and a float variable takes its peer's or the context's float type.
    - Unsuffixed integer literal operands (including `-3`) are typed directly as that float type (`AXS-EXT-035`).
    - Other integer sub-expressions keep their integer type and integer arithmetic (the existing T451 integer lattice), and are promoted at the node where they meet a float.
    - An enclosing expected f64 widens an f32 root operation.
    - `&`, `|`, `^`, `<<`, `>>` and `~` on floats are `AX_TYPE_OPERATOR`.
    - Assignment, binding, argument and narrowing boundaries stay `AX_TYPE_MISMATCH` (`AXS-FLT-035`).
- **MIR (`mir.ax`, `builder.ax`)**:
  - New constant `MIR_CONST_FLOAT = 6`, printed `const f64#3ff8000000000000` / `const f32#3fc00000`.
  - New cast kinds `MIR_CAST_FLOAT_TO_INT = 4`, `MIR_CAST_INT_TO_FLOAT = 5`, `MIR_CAST_FLOAT_CONVERT = 6`, printed as `as type#N (IntToFloat)` etc. IntToInt and the pointer casts print exactly as before, so existing dumps are byte-identical.
  - The MIR text parser reads all of these forms.
  - The builder emits an explicit cast temporary before every mixed binary, comparison or unary instruction (`mb_cast_int_if_needed` now covers IntToInt, IntToFloat and FloatConvert; `mb_join_float_ty` handles comparisons).
  - Float arithmetic and float negation have no overflow or divide-by-zero assert (`AXS-FLT-010`). `-lit` becomes one constant with the sign bit flipped.
  - Float literal patterns lower to IEEE `scrutinee == const`, and `as` casts get the right float kind.
- **Verifier (`verifier.ax`)**, INV-FLT-002:
  - A binary op that mentions a float operand must have identical float operand types and must not be bitwise, shift, offset, wrapping or saturating. Its result type must match.
  - `overflows(...)` on floats is rejected. Unary on a float must be `Neg`.
  - The cast kind must agree with the source and target classes (IntToInt never touches a float).
  - All violations are `AX_VERIFY_TYPE_MISMATCH`.
  - Operands whose type the verifier does not record (projected places) are treated as unknown, matching the existing `verify_types_compatible` policy.
  - The `.mir` parser reads float constants and the new cast kinds. The minimal THIR has 5 scratch slots.
  - The parser-local `VERIFY_CAST_UNSIZE` moved from 4 to 7, because 4 is now `MIR_CAST_FLOAT_TO_INT` (SPEC-41 fixes 4/5/6).
- **Parser (`parse.ax`)**: `1.5` and `-1.5` start a literal pattern.

## Decisions (made under the owner's delegation, for the architect)
1. **Integer literals beside a float are retyped as the float.** SPEC-41 AXS-FLT-032 rule 2 allows either "type the literal as F" or "type it i32/i64 plus an IntToFloat cast". I chose the first. A literal `i32` default would wrongly reject large literals (`x * 3000000000`), and the MIR is simpler. Non-literal integer operands, including `IntVar`-typed variables, are cast.
2. **Context widening for floats.** `let y: f64 = w_f32 + 0.5` evaluates in f64, which mirrors the existing integer rule (`let x: i64 = a_i32 + b_i8`). Children of a float node get no expected type, so nested sub-trees follow the normative Pattern A steps (`w + 0.5` is computed in f32, then FloatConvert).
3. **Pattern B joins `u32 + isize` to `i64`, not the spec's `isize`.** This comes from the existing T451 `join_int` order dependence, not from T457. Both types are 64-bit and the value is identical. I left it unchanged because it is outside the float work; it is flagged here for the architect and T462.
4. **Float `const` items are not enabled.** `is_valid_const_type` is unchanged, because constant evaluation of floats belongs to T458 (oracle/comptime).
5. **Message text.** `AX_TYPE_LITERAL_OUT_OF_RANGE` keeps its registry message ("integer literal does not fit its type") for float literals. Only the code is normative.

**REQ-OWNER-007 status (corrected in round 1):** Patterns A-D type-check and lower with explicit casts. Round 0 said decision 3 was the only deviation from the spec text. That was too strong. The known deviations are decision 3 and the "Open items" below.

## Open items for the architect (not fixed here)
1. **`1.5u8` is silently accepted as `f64` (caused by T457).** HEAD rejected every float literal; T457 ignores a non-float suffix. `1e-5u8` behaves the same. SPEC-01 AXS-LEX-058 and SPEC-41 AXS-FLT-070 require `AX_LEX_INVALID_SUFFIX`. Found in round 1 and left unfixed because the round's scope forbids changing suffix behaviour. The fix is one check in `scan_number`.
2. **`1f32` is silently an `i32` with value 1** (already so on HEAD and in axiom0). The same spec rows require `AX_LEX_INVALID_SUFFIX`. It matters more now that `f32` exists: `2f32 + 1.5` type-checks as f64.
3. **Verifier index check not implemented.** SPEC-41 AXS-FLT-034 rule 3 asks for `MIR_PROJ_INDEX` locals to be `usize`; the verifier only checks that the local exists. The builder does emit the cast.
4. **Verifier operand gap.** An operand that is a projected place (`(_8)[_16]`, a field) has no recorded type, so homogeneity is not checked on that side.
5. QA findings F2 (Pattern B `isize`), F3 (float programs reach interpreter/native and produce wrong code until T458/T459) and F4 (`!x` code) are unchanged, as instructed.

## Obsolete bootstrap-rejection tests (resolved after the unblock)
The coordinator added these three tests to `paths:`. Each one asserted the `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` float rejection that this task removes. I applied the coordinator's decision as follows:
- `tests/ui/numeric/float_bootstrap.ax`: about the frozen axiom0 behaviour. Added `// requires: axiom0-internal`; the test id is kept.
- `tests/conformance/vs0/float_unsupported.ax`: same treatment. The file's CRLF line endings are preserved.
- `tests/ui/typeck/bug_float_unsupported.ax`: about axiomc typing, so it is now a positive axiomc test.
  - `fn half(x: f64)` and `let a = 1.5` are accepted.
  - `let b: f32 = 2` expects `AX_TYPE_MISMATCH`, the spec'd SPEC-41 AXS-FLT-035 rule 1 diagnostic.

`tests/ui/index_not_int/float_literal.ax` passes unchanged.

## Files changed
- compiler/lex/scanner.ax
- compiler/lex/token.ax
- compiler/syntax/parse.ax
- compiler/types/types.ax
- compiler/types/layout.ax
- compiler/types/typeck.ax
- compiler/mir/mir.ax
- compiler/mir/builder.ax
- compiler/verify/verifier.ax
- tests/typeck/float/float_typing_pos.ax
- tests/typeck/float/float_typing_pos.test
- tests/typeck/float/mixed_patterns_pos.ax
- tests/typeck/float/mixed_patterns_pos.test
- tests/typeck/float/float_neg.ax
- tests/mir/float_mixed/patterns_abcd.ax
- tests/mir/float_mixed/patterns_abcd.test
- tests/mir/float_mixed/patterns_abcd_verify.test
- tests/mir/float_mixed/float_ops.ax
- tests/mir/float_mixed/float_ops.test
- tests/mir/float_mixed/float_ops_verify.test
- tests/mir/float_mixed/literal_rounding.ax
- tests/mir/float_mixed/literal_rounding.test
- tests/mir/float_mixed/verify_float_ok.mir
- tests/mir/float_mixed/verify_float_ok.test
- tests/mir/float_mixed/verify_float_ok_emit.test
- tests/mir/float_mixed/verify_mixed_binop_neg.mir
- tests/mir/float_mixed/verify_mixed_binop_neg.test
- tests/mir/float_mixed/verify_float_bitand_neg.mir
- tests/mir/float_mixed/verify_float_bitand_neg.test
- tests/mir/float_mixed/verify_bad_cast_kind_neg.mir
- tests/mir/float_mixed/verify_bad_cast_kind_neg.test
- tests/mir/float_mixed/lex_exponent_pos.ax
- tests/mir/float_mixed/lex_exponent_pos.test
- tests/mir/float_mixed/lex_exponent_neg.ax
- tests/mir/float_mixed/lex_exponent_neg.test
- tests/ui/numeric/float_bootstrap.ax
- tests/ui/typeck/bug_float_unsupported.ax
- tests/conformance/vs0/float_unsupported.ax

No other task's files were touched. `verifier.ax` and `typeck.ax` had no foreign uncommitted hunks in the main tree when I edited them.

## Verification, round 0 (snapshot `build-snap-T457`)
- **Build:** `python tools/build_axiomc.py --out build --stage 3` succeeded: STAGE1 OK, then seeded STAGE2/STAGE3 with `FIXED-POINT (O1) OK`, `sha256=41577925caf1cc90…`, and STAGE0-GUARD OK.
- **Own tests:** `axtest -j 2 typeck/float mir/float_mixed`: `TOTAL 13 PASS 13`.
  - Pattern A–D MIR matches SPEC-41 AXS-FLT-036/037: every implicit promotion is an explicit `(IntToFloat)` / `(FloatConvert)` / IntToInt cast, and indices are cast to usize.
  - Literal bit patterns match exact roundTiesToEven. Examples: `16777217.0f32` → `4b800000`; `1.0000000596046448f32` → `3f800001` (a double-rounding trap); `4.9e-324` → `1`; `2.2250738585072011e-308` → `000fffffffffffff`; `2^53+1` fixed to f64 → `4340000000000000`.
  - Each negative `.mir` test reports exactly one `AX_VERIFY_TYPE_MISMATCH`.
- **Taskgate (after the unblock, fresh snapshot):** `taskgate --task T457 -j 2`: `TOTAL 592 PASS 588 FAIL 0 SKIP 4`, BASELINE OK, `TASKGATE T457 exit=0`. `archcheck`: clean, 232 files, 0 violations. Smoke check OK. WEAK-NATIVE 0 in the task's own and changed tests.
- **The three updated tests:** `axtest -j 2 ui/numeric/float_bootstrap.ax ui/typeck/bug_float_unsupported.ax conformance/vs0/float_unsupported.ax`: `TOTAL 3 PASS 1 SKIP 2` (the two `requires: axiom0-internal` tests are skipped for axiomc).
- **Related suites:** `axtest -j 2 ui/numeric conformance/vs0 ui/index_not_int ui/typeck lex parse typeck mir`: `TOTAL 582 PASS 578 FAIL 3 SKIP 1`. This run was made before the unblock; its 3 failures were exactly the three tests above, which have since been fixed.
- **Selfhost:** `axtest bundles_current.test`: 34/34 PASS. `selfhost/lex selfhost/lexer selfhost/verify`: 18/18 PASS.
- **Out of scope:** floats in the MIR interpreter (T458) and native x86-64 code generation (T459).

## Round 1 (QA finding F1)
**Fix** (`compiler/lex/scanner.ax`, `scan_number` plus helper `exponent_digits_pos`): `e`/`E` straight after the integer digits now goes through the same exponent branch as the fraction form, so `1e-5`, `2E+10`, `1_0e-3f64`, `1e-5f32` are one Float token.

**Behaviour change beyond F1 (please review):** the exponent branch now follows SPEC-01 AXS-LEX-056 / SPEC-41 AXS-FLT-070: one exponent, and only with digits. Before, `1.5e` and `1.5e-` were accepted as 1.5 and `1.5e3e4`, `1e3e4` as 1.5e3 / 1e3, dropping the tail silently; the two-line fix alone would have added `1e-3e4` to that group. They are now `AX_LEX_INVALID_SUFFIX`. axiom0 (frozen) still accepts them; its tokens were identical to axiomc's on all 34 probe inputs before this round.

**Unchanged (compared before/after on 34 inputs):** `1e`, `1E`, `1e-`, `1e+`, `1e-x`, `1e--5`, `1e-_5` (`AX_LEX_INVALID_SUFFIX` on `e`, Int token with ERROR flag), `0x1e-5`, `0x1E+5`, `0b1e-5`, `0o1e-5`, `x.1e-5`, `x.0.1e-5`, `1u8-5`, `5-3`, `1e5`, `1.0e-5`.

**Tests:** `lex_exponent_pos.test` and `lex_exponent_neg.test` (exact token dumps; all 10 negative lines reported at their positions). They are in `tests/mir/float_mixed` because `tests/lex` is outside `paths:`. QA's 18 files are untouched.

**Verification (snapshot refreshed, Stage-0 clang Release, `--stage 3`):**
- Build: FIXED-POINT (O1) OK, `sha256=236ac8bf20fd1de7...`, STAGE0-GUARD OK.
- `axtest -j 2 --no-cache mir/float_mixed typeck/float`: `TOTAL 25 PASS 25`, including `qa_exp_sign.test`.
- `axtest -j 2 mir/float_mixed typeck/float lex ui/lex selfhost/lex selfhost/lexer bundles_current.test` plus the 3 old float tests (before the two new lexer tests existed): `TOTAL 120 PASS 118 FAIL 0 SKIP 2`.
- 300 random literals of the form `<digits>e<sign><digits>` against Python `float`: 0 mismatches.
- Taskgate (`-j 2`, task and QA files): `TOTAL 683 PASS 679 FAIL 0 SKIP 4`, BASELINE OK, `TASKGATE T457 exit=0`; archcheck 232 files, 0 violations; WEAK-NATIVE 0 in own/changed tests.
- The full suite was not run in either round; taskgate defers the large selfhost bundles to the periodic full run.

STATUS: COMPLETE round=1
