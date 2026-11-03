# T456 Report — E12.2 Canonical IEEE-754 Floating-Point, Mixed-Type Promotion Lattice & Math Specification (`SPEC-41`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-41-floating-point.md` cho Epic `E12.2` (`f32`/`f64`, suy diễn literal `FloatVar`, số học IEEE-754 chuẩn, `NaN`/`-0.0`/`±inf`, ép kiểu bão hòa `FloatToInt`, dàn nâng kiểu biểu thức hỗn hợp 12 kiểu nguyên thủy theo `REQ-OWNER-007` với 4 mẫu chuẩn Pattern A/B/C/D, hạ tầng LIR `Xmm` và ABI Windows x64 SSE2, định dạng/phân tích chuỗi `std.text.fmt.float` tất định, và thư viện toán học `std.math` thuần Axiom). Đồng thời cập nhật 4 tài liệu khóa liên quan (`spec/INDEX.md`, `spec/SPEC-03-core-semantics.md`, `spec/diagnostics.md`, `spec/invariants.md`) và kiểm chứng toàn bộ bằng `reqcov.py --strict`, `harness_check.py`, `gatecheck.py --no-run`, và `taskctl.py changes T456`.

## What Was Done

1. **Authored `spec/SPEC-41-floating-point.md` (`AXS-FLT-001`..`AXS-FLT-073`)**:
   - **§1 (`AXS-FLT-001`..`006`) — Floating-Point Type Model, Bit Encoding & Literals**:
     - Defined `f32` (IEEE-754 `binary32`, size 4, align 4) and `f64` (IEEE-754 `binary64`, size 8, align 8), `FpCategory`, canonical quiet `NaN` bit patterns (`0x7FC0_0000u32` and `0x7FF8_0000_0000_0000u64`), `FloatVar` literal inference (`f64` fallback), exact `roundTiesToEven` decimal conversion (`AX_TYPE_LITERAL_OUT_OF_RANGE` on finite literal overflow), associated constants (`INFINITY`, `NEG_INFINITY`, `NAN`, `EPSILON`, `MIN`, `MIN_POSITIVE`, `MAX`, `RADIX`, `MANTISSA_DIGITS`, `DIGITS`, `MIN_EXP`, `MAX_EXP`, `MIN_10_EXP`, `MAX_10_EXP`), classification methods, built-in traits (`PartialEq`/`PartialOrd`, not `Eq`/`Ord`/`Hash`), and float literal pattern rules.
   - **§2 (`AXS-FLT-010`..`016`) — IEEE-754 Arithmetic, Rounding, `NaN` & Signed Zero Semantics**:
     - Specified strict IEEE-754 `roundTiesToEven` arithmetic (`+`, `-`, `*`, `/`, `%`, unary `-`), non-panicking float overflow (`±inf`) and division by zero (`±inf`/`NaN`), truncating `%` (`fmod`), subnormal support (`FTZ=0, DAZ=0`), quiet `NaN` propagation, signed zero (`+0.0` vs `-0.0`) rules, prohibition of implicit `-ffast-math` reassociation and silent FMA contraction (`REQ-SIMD-108`..`110`, `REQ-SIMD-163`, `REQ-SIMD-186`..`189`), directed rounding (`floor`, `ceil`, `trunc`, `round`, `round_ties_even`, `fract`, `next_up`, `next_down`), and `NaN`-propagating `min`/`max`/`clamp`.
   - **§3 (`AXS-FLT-020`..`025`) — Comparisons & Conversions (`as`, `From`/`TryFrom`, Bitcasts)**:
     - Specified IEEE-754 partial comparisons and the `UCOMISS`/`UCOMISD` `ZF`/`PF`/`CF` truth table, IEEE-754 `totalOrder` via `total_cmp`, saturating `FloatToInt` `as` casts (`MIR_CAST_FLOAT_TO_INT`: `NaN -> 0`, clamped to `[T.MIN, T.MAX]`), `IntToFloat` (`MIR_CAST_INT_TO_FLOAT`) + lossless `From` subset (`i8`/`u8`/`i16`/`u16 -> f32`, `i8..i32`/`u8..u32 -> f64`), `FloatConvert` (`MIR_CAST_FLOAT_CONVERT`), and `to_bits`/`from_bits`/endian byte conversions.
   - **§4 (`AXS-FLT-030`..`037`) — `REQ-OWNER-007` Complete Mixed-Type Promotion Lattice**:
     - Defined the complete `join_num(A, B)` table across `i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`, `IntVar`, and `FloatVar` (where `join_num(F, Int) = F` promotes concrete integer operands and `IntVar` literals via `MIR_CAST_INT_TO_FLOAT`); sub-expression propagation across arithmetic, bitwise, shift, unary, index, and comparison operators; explicit `MIR_RVALUE_CAST` lowering and homogeneous MIR verifier rules; forbidden implicit conversion boundaries (`AX_TYPE_MISMATCH` on standalone bindings/narrowing and same-width signed/unsigned integer operations); and normative specifications + MIR cast sequences for `REQ-OWNER-007` Patterns A, B, C, and D.
   - **§5 (`AXS-FLT-040`..`044`) — LIR, Windows x64 ABI & SSE2 Scalar Lowering**:
     - Specified `LirType.F32`/`F64`, `RegClass.Xmm` (`XMM0`–`XMM15`), `.rdata` constant deduplication by exact bit pattern (`+0.0` vs `-0.0`), Windows x64 ABI positional parameter passing (`XMM0`–`XMM3`, stack slots $\ge 4$, GPR mirroring on variadic `extern "C"`, `XMM0` return, `XMM6`–`XMM15` 128-bit callee-saved preservation in `FrameLayout`), SSE2 scalar instruction selection, `UCOMISS`/`UCOMISD` unordered `PF` handling (`SETE+SETNP+AND` for `==`, `SETNE+SETP+OR` for `!=`), two-path unsigned `u64 -> f32/f64`, and saturating `CVTTSS2SI`/`CVTTSD2SI` lowering.
   - **§6 (`AXS-FLT-050`..`052`) — Deterministic Formatting & Parsing (`std.text.fmt.float`)**:
     - Specified `"NaN"`, `"inf"`, `"-inf"`, `"-0.0"` formatting, shortest round-trip guarantee (`parse(format(x)).unwrap().to_bits() == x.to_bits()`), fixed-precision (`format_f64_fixed`) and scientific (`format_f64_exp`) formatting, and exact `roundTiesToEven` decimal parsing (`parse_f32(s: Str) -> Result<f32, ParseFloatError>`, `parse_f64(s: Str) -> Result<f64, ParseFloatError>`).
   - **§7 (`AXS-FLT-060`..`064`) — Pure-Axiom Standard Mathematical Library (`std.math`)**:
     - Specified 100% pure-Axiom `std.math` (`T461`) constants (`PI`, `TAU`, `E`, `LN_2`, `SQRT_2`, etc. with exact hex bit patterns), exact ($\le 0.5\text{ ULP}$) elementary operations (`sqrt`, `fma`, `floor`, `ceil`, `trunc`, `round`, `round_ties_even`, `fract`, `modf`, `frexp`, `ldexp`, `scalbn`, `div_euclid`, `rem_euclid`), bounded ($\le 1.0\text{ ULP}$ / $\le 1.5\text{ ULP}$) minimax + Cody-Waite/Payne-Hanek transcendental functions, and the IEEE-754 special-value table.
   - **§8 (`AXS-FLT-070`..`073`) — Diagnostics, Canonical Examples & Traceability Matrix**:
     - Documented registered diagnostic codes, canonical positive/negative Axiom examples, and the traceability matrix mapping `REQ-OWNER-007`, `REQ-SIMD-108`..`110`, `REQ-SIMD-163`, and `REQ-SIMD-186`..`189` to `SPEC-41` clauses and `T457`..`T462`.

2. **Updated Locked Specification Indexes & Catalogues**:
   - `spec/INDEX.md`: Registered `spec/SPEC-41-floating-point.md` in §2, `AXS-FLT-NNN` in §4, and `SPEC-41` in §5.
   - `spec/SPEC-03-core-semantics.md`: Linked `SPEC-41` in `AXS-SEM-010`, `AXS-SEM-022`, `AXS-SEM-035`, and `AXS-SEM-060`.
   - `spec/diagnostics.md`: Referenced `SPEC-41` in `AX_TYPE_MISMATCH`, `AX_TYPE_OPERATOR`, `AX_TYPE_LITERAL_OUT_OF_RANGE`, `AX_TYPE_INVALID_CAST`, `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, and `## Sources`.
   - `spec/invariants.md`: Added `FLT` group to §1 and catalogued `INV-FLT-001`..`INV-FLT-004` in §13.

## Files changed

- `spec/SPEC-41-floating-point.md` (created)
- `spec/INDEX.md` (modified)
- `spec/SPEC-03-core-semantics.md` (modified)
- `spec/diagnostics.md` (modified)
- `spec/invariants.md` (modified)

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python tools/gatecheck.py --no-run` -> `invariant catalogue OK`, `GATE PASS`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T456` -> all modified files within `paths:` + `locks:` of `T456`

STATUS: COMPLETE round=2
