# SPEC-41 — Canonical IEEE-754 Floating-Point, Mixed-Type Promotion Lattice & Math Specification

Status: draft (T456, 2026-11-03)
Owner: axiom-architect
Consolidates: `tasks/0327 §84.2, §84.4–84.9`; `tasks/0331 §17–30, §59–70, §100 (ANUM-41..57, 81..100)`; `tasks/0334 §91.1–12`; `tasks/0338 §15–36, §93–100 (ANUM-37..65, 80..100)`; `tasks/0345 §17–36, §98–100 (ANUM-22, 35..62, 78..100)`; `tasks/0427 §15–26`; `tasks/0431 §172.1–14`; `tasks/0469 §210.1–210.80 (AMATH-20..70)`; `specs/0157`; `specs/0162`; `specs/0175`; `specs/0179`; `specs/0181`; `specs/0245`; `spec/SPEC-01-lexical.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-40-integers.md`; `spec/requirements/OWNER.md` (`REQ-OWNER-007`).
Covers: `REQ-OWNER-007`, `REQ-SIMD-108`, `REQ-SIMD-109`, `REQ-SIMD-110`, `REQ-SIMD-163`, `REQ-SIMD-186`, `REQ-SIMD-187`, `REQ-SIMD-188`, `REQ-SIMD-189`.
Consumers: `compiler/lex/`, `compiler/syntax/`, `compiler/hir/`, `compiler/types/types.ax`, `compiler/types/layout.ax`, `compiler/types/typeck.ax`, `compiler/mir/mir.ax`, `compiler/mir/builder.ax`, `compiler/verify/verifier.ax`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/abi/win64.ax`, `compiler/target/x64/`, `std/core/float.ax`, `std/text/fmt/float.ax`, `std/math/mod.ax`, `T457`–`T462`.

## Tóm tắt

Tài liệu `SPEC-41` quy định chuẩn tắc toàn bộ ngữ nghĩa dấu phẩy động IEEE-754 (`f32` binary32 và `f64` binary64), ma trận thăng cấp biểu thức hỗn hợp đa kiểu phức tạp (`REQ-OWNER-007` Complex Mixed-Type Expression Matrix), quy ước gọi hàm thanh ghi `XMM` trên Windows x64, định dạng/phân tích chuỗi số thực chính xác, và hợp đồng độ chính xác ULP của thư viện toán học `std.math` cho phân hệ `E12.2` (Phase `P12`). Các quyết định kiến trúc cốt lõi gồm:
- **Mô hình IEEE-754 nghiêm ngặt mặc định (`Strict FP`)**: `f32` (4 byte, căn chỉnh 4) và `f64` (8 byte, căn chỉnh 8) tuân thủ chuẩn IEEE-754-2019 với chế độ làm tròn mặc định `roundTiesToEven`, bảo toàn số không có dấu (`+0.0` và `-0.0`), vô cực (`±inf`), `NaN` tĩnh (`qNaN`), và giảm cấp tiệm tiến (subnormals). Nghiêm cấm mọi biến đổi `fast-math` ngầm định như kết hợp lại phép cộng/nhân (`reassociation`), bỏ qua `NaN`/`-0.0`, hoặc gộp `a * b + c` thành `FMA` khi không được phép (`ANUM-43..45, 98`, `ASIMD-40..43`).
- **So sánh và chuyển đổi kiểu an toàn**: Các toán tử `==`, `!=`, `<`, `<=`, `>`, `>=` thực hiện so sánh từng phần IEEE-754 (trả về `false` nếu có toán hạng `NaN`, trừ `!=` trả về `true`), trong khi `total_cmp` cung cấp thứ tự toàn phần tất định. Phép ép kiểu `float as Int` (`MIR_CAST_FLOAT_TO_INT`) thực hiện cắt phần thập phân về 0 và **bão hòa (saturating)**: `NaN -> 0`, giá trị vượt biên bị kẹp vào `[T.MIN, T.MAX]`, tuyệt đối không bao giờ gây UB hoặc lỗi phần cứng `#IA`.
- **Ma trận biểu thức hỗn hợp `REQ-OWNER-007` và bất biến MIR đồng nhất**: Trong các biểu thức toán học phức tạp kết hợp hằng số không hậu tố (`IntVar`, `FloatVar`) và biến thuộc nhiều kiểu số (`i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`) qua các nhánh số học, dịch bit/bitwise, chỉ số mảng (`coeff[idx + off]`), lời gọi hàm và so sánh (Patterns A, B, C, D), `typeck` suy diễn kiểu hằng số và thăng cấp biến hẹp hơn theo dàn thứ tự tất định, đồng thời `compiler/mir/builder.ax` phát sinh tường minh các lệnh `MIR_RVALUE_CAST` (`IntToInt`, `IntToFloat`, `FloatConvert`) trước mỗi phép toán để `compiler/verify/verifier.ax`, trình thông dịch oracle, bộ tối ưu hóa, LIR và backend x86-64 luôn nhận 100% toán hạng đồng nhất kiểu.
- **ABI Windows x64, định dạng chuỗi và `std.math` thuần Axiom**: Tham số thực truyền qua `XMM0`–`XMM3`, trả về qua `XMM0`, bảo toàn đủ 128 bit của `XMM6`–`XMM15`; định dạng thập phân ngắn nhất bảo đảm khứ hồi từng bit (`parse(format(x)) == x`); và `std.math` cài đặt hoàn toàn bằng Axiom (không phụ thuộc CRT/libm) với sai số tối đa $\le 0.5\text{ ULP}$ cho hàm cơ sở và $\le 1.0\text{ ULP}$ (hoặc $\le 1.5\text{ ULP}$ cho hàm siêu việt phức hợp) đồng nhất giữa `--interp` và mã máy x86-64.

---

## 1. IEEE-754 Scalar Floating-Point Model (`f32`, `f64`)

### AXS-FLT-001 — Primitive Floating-Point Types & Representation (`ANUM-22`, `SPEC-04 AXS-EXT-020`)

Axiom defines two fundamental scalar binary floating-point primitive types in the language core (`TypeKind.Float`):

| Type | IEEE-754 Format | Bit Width | Sign Bits | Exponent Bits ($w$) | Exponent Bias | Significand Precision ($p$, incl. hidden bit) | Stored Trailing Significand Bits ($t = p - 1$) | Size (bytes) | Align (bytes) |
|---|---|---|---|---|---|---|---|---|---|
| `f32` | `binary32` (single) | $32$ | $1$ (bit 31) | $8$ (bits $30..23$) | $127$ | $24$ bits | $23$ (bits $22..0$) | $4$ | $4$ |
| `f64` | `binary64` (double) | $64$ | $1$ (bit 63) | $11$ (bits $62..52$) | $1023$ | $53$ bits | $52$ (bits $51..0$) | $8$ | $8$ |

1. **Compiler type representation**: In `compiler/types/types.ax` (`T457`), `f32` and `f64` are represented as distinct primitive `TypeKind.Float` entries (`TY_F32` and `TY_F64`), and unsuffixed floating-point literals are represented during type inference by a floating-point inference variable `TY_FLOAT_VAR` (`Infer.FloatVar`).
2. **Bootstrap boundary**: In the frozen C Stage-0 bootstrap compiler (`bootstrap/axiom0`), `f32`, `f64`, and floating-point literals are rejected during type checking with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct = "f32" | "f64" | "float literal"`, `data.epic = "E12.2"` per `SPEC-03 AXS-SEM-010` and `SPEC-04 AXS-EXT-010`). In self-hosted `axiomc` (`T457`+), `f32` and `f64` are fully enabled.
3. **Reserved half-precision widths (`SPEC-04 AXS-EXT-020`, `ANUM-86..88`)**: The 16-bit floating-point widths `f16` (IEEE-754 `binary16`) and `bf16` (bfloat16) remain reserved in `TypeKind.Float` so future AI/accelerator extensions can add them without changing the core type model; they are not implicit aliases of `f32`. There are no C-style `float` or `double` keyword aliases in Axiom (`tasks/0345 §21`).
4. **Byte order**: In memory on `x86_64-pc-windows-msvc`, `f32` and `f64` are stored in little-endian byte order matching the IEEE-754 bit layout of `u32` and `u64` respectively.
[tasks/0331 §1, §17, ANUM-41; tasks/0338 §17, ANUM-37; tasks/0345 §1, §21, ANUM-22; SPEC-03 AXS-SEM-010; SPEC-04 AXS-EXT-020]

### AXS-FLT-002 — Bit-Level Encoding, Categories & Canonical Quiet `NaN` (`ANUM-42..44`)

For a floating-point format with bit width $N \in \{32, 64\}$, exponent width $w \in \{8, 11\}$, bias $B = 2^{w-1} - 1 \in \{127, 1023\}$, and trailing significand width $t \in \{23, 52\}$, an $N$-bit unsigned integer bit pattern $b$ decomposes into:
- sign bit $s = (b \gg (N - 1)) \mathbin{\&} 1 \in \{0, 1\}$,
- biased exponent field $E = (b \gg t) \mathbin{\&} ((1 \ll w) - 1) \in [0, 2^w - 1]$,
- trailing significand field $M = b \mathbin{\&} ((1 \ll t) - 1) \in [0, 2^t - 1]$.

Every bit pattern $b$ belongs to exactly one of the five `FpCategory` states:

1. **Zero (`FpCategory.Zero`, $E = 0 \land M = 0$)**:
   - `+0.0` has $s = 0$ (`0x0000_0000u32` for `f32`, `0x0000_0000_0000_0000u64` for `f64`).
   - `-0.0` has $s = 1$ (`0x8000_0000u32` for `f32`, `0x8000_0000_0000_0000u64` for `f64`).
2. **Subnormal (`FpCategory.Subnormal`, $E = 0 \land M \ne 0$)**:
   - Exact mathematical value: $(-1)^s \cdot 2^{1 - B} \cdot (M \cdot 2^{-t})$.
   - Subnormals provide gradual underflow down to `f32.MIN_POSITIVE_SUBNORMAL` ($2^{-149}$, bit pattern `0x0000_0001u32`) and `f64.MIN_POSITIVE_SUBNORMAL` ($2^{-1074}$, bit pattern `0x0000_0000_0000_0001u64`).
3. **Normal (`FpCategory.Normal`, $1 \le E \le 2^w - 2$)**:
   - Exact mathematical value: $(-1)^s \cdot 2^{E - B} \cdot (1 + M \cdot 2^{-t})$.
4. **Infinite (`FpCategory.Infinite`, $E = 2^w - 1 \land M = 0$)**:
   - `+inf` (`f32.INFINITY = 0x7F80_0000u32`, `f64.INFINITY = 0x7FF0_0000_0000_0000u64`) for $s = 0$.
   - `-inf` (`f32.NEG_INFINITY = 0xFF80_0000u32`, `f64.NEG_INFINITY = 0xFFF0_0000_0000_0000u64`) for $s = 1$.
5. **Not-a-Number (`FpCategory.Nan`, $E = 2^w - 1 \land M \ne 0$)**:
   - Bit $t - 1$ of $M$ is the `is_quiet` bit: when bit $t - 1$ is $1$, the value is a **quiet `NaN` (`qNaN`)**; when bit $t - 1$ is $0$ (and $M \ne 0$), the bit pattern is a signaling `NaN` (`sNaN`, constructible only via `from_bits` or raw memory).
   - **Canonical Quiet `NaN`**: Whenever an arithmetic operation, intrinsic, or `std.math` function produces a fresh `NaN` from non-`NaN` inputs (e.g., `0.0 / 0.0`, `inf - inf`, `0.0 * inf`, `sqrt(-1.0)`), or when evaluating `f32.NAN` / `f64.NAN`, both the MIR interpreter oracle (`--interp`) and constant folding produce the canonical positive quiet `NaN` bit pattern:
     - `f32.NAN` bits: `0x7FC0_0000u32` ($s = 0, E = 255, M = 2^{22}$).
     - `f64.NAN` bits: `0x7FF8_0000_0000_0000u64` ($s = 0, E = 2047, M = 2^{51}$).
   - Note on hardware `NaN` sign bit in x86-64 SSE2 (`tasks/0331 §21`): x86-64 SSE2 instructions (`DIVSD 0.0/0.0`, `SQRTSD -1.0`) produce the architectural quiet `NaN` indefinite value (`0xFFC0_0000u32` / `0xFFF8_0000_0000_0000u64`, with quiet bit $t - 1 = 1$). Core arithmetic semantics guarantee that any `NaN` result satisfies `x.is_nan() == true` and has its quiet bit set; arbitrary `NaN` payload or sign bits of arithmetic-generated `NaN`s are not part of observable numeric semantics unless inspected via `to_bits()` on a value produced by `from_bits()`/`copysign()`, and formatting (`§6`) always prints any `NaN` (regardless of sign or payload bits) as `"NaN"`.
[tasks/0331 §17–21, ANUM-42..47; tasks/0338 §18–21, ANUM-38..41; tasks/0345 §22–26, ANUM-45..49]

### AXS-FLT-003 — Floating-Point Literals, `FloatVar` Inference & Decimal-to-Binary Conversion (`SPEC-01 AXS-LEX-055`, `ANUM-44`, `ANUM-58`)

1. **Lexical forms (`SPEC-01 AXS-LEX-055..058`)**:
   - A floating-point literal consists of decimal digits with a fractional part (`1.5`, `0.0`, `3.141_592_65`), an exponent (`1e-5`, `2E+10`), or both (`1.5e3`), optionally followed by suffix `f32` or `f64` (`2.5f32`, `3.0f64`).
   - Digit separators `_` are ignored when computing the mathematical value.
   - Unary negation `-lit` applied to a floating-point literal negates the sign bit $s \gets s \oplus 1$ (`-0.0` has bit pattern `0x8000_0000_0000_0000u64` for `f64` and `0x8000_0000u32` for `f32`).
2. **Type resolution (`FloatVar`)**:
   - A suffixed literal (`2.5f32`, `3.0f64`) has concrete type `f32` or `f64` immediately.
   - An unsuffixed floating-point literal (`1.5`, `0.5`, `6.0`, `1e-5`) receives a fresh floating-point inference variable `TY_FLOAT_VAR` (`Infer.FloatVar`).
   - `FloatVar` unifies with `f32` or `f64` from its surrounding typing context (type annotation, parameter type, return type, struct/array/tuple element type, or peer operand in a numeric expression per `§4`).
   - Any `FloatVar` remaining unconstrained at the end of the enclosing item/function body defaults deterministically to **`f64`** (`tasks/0331 §63`, `tasks/0427 §24`).
   - Unifying a `FloatVar` with a non-floating-point type (outside the `REQ-OWNER-007` promotion rules where the peer is promoted *to* the float type, `§4`) emits `AX_TYPE_MISMATCH`.
3. **Exact round-to-nearest-even decimal-to-binary conversion (`SPEC-01 §11`, `ANUM-44`)**:
   - Once the target type (`f32` or `f64`) of a float literal is known, the compiler converts the exact decimal rational value $d = m \cdot 10^k$ to the target IEEE-754 binary format using **roundTiesToEven** (Clinger / Eisel–Lemire algorithm with exact multiprecision fallback).
   - Crucially, an `f32` literal (whether suffixed `1.0000001f32` or an unsuffixed literal unified with `f32`) is rounded **directly** from the exact decimal value to `f32` — never rounded to `f64` first and then rounded a second time to `f32` (preventing double-rounding errors at midpoint boundaries).
   - If the decimal magnitude of a literal exceeds `T.MAX` (i.e. $\ge (2 - 2^{-24}) \cdot 2^{128}$ for `f32` or $\ge (2 - 2^{-53}) \cdot 2^{1024}$ for `f64`), `typeck` emits `AX_TYPE_LITERAL_OUT_OF_RANGE` (`63u32`); programmers writing infinity must use `f32.INFINITY` / `f64.INFINITY` (or `1.0 / 0.0`). Non-zero literals smaller than half the minimum subnormal underflow to signed zero (`+0.0` or `-0.0`).
4. **Compile-time constant representation (`SPEC-04 AXS-EXT-024`)**:
   - In `compiler/types/types.ax` and `compiler/mir/mir.ax`, floating-point constants use `CONST_FLOAT` / `MIR_CONST_FLOAT` storing the exact IEEE-754 bit pattern in `u64` (`bits: u64`, where `f32` occupies the low 32 bits `bits & 0xFFFF_FFFFu64` and `f64` occupies all 64 bits) together with `ty: TypeId` (`TY_F32` or `TY_F64`).

### AXS-FLT-004 — Associated Constants & Classification API (`std.core.float`, `T460`)

Both `f32` and `f64` expose the following compile-time associated constants (`f32.<NAME>`, `f64.<NAME>`) and classification methods in `std.core.float`:

| Associated Constant | Type | `f32` Value / Bit Pattern | `f64` Value / Bit Pattern |
|---|---|---|---|
| `RADIX` | `u32` | `2u32` | `2u32` |
| `MANTISSA_DIGITS` | `u32` | `24u32` | `53u32` |
| `DIGITS` | `u32` | `6u32` | `15u32` |
| `EPSILON` | `Self` | $2^{-23} \approx 1.1920929\times 10^{-7}$ (`0x3400_0000u32`) | $2^{-52} \approx 2.220446049250313\times 10^{-16}$ (`0x3CB0_0000_0000_0000u64`) |
| `MIN` | `Self` | $-3.40282347\times 10^{38}$ (`0xFF7F_FFFFu32`) | $-1.7976931348623157\times 10^{308}$ (`0xFFEF_FFFF_FFFF_FFFFu64`) |
| `MAX` | `Self` | $3.40282347\times 10^{38}$ (`0x7F7F_FFFFu32`) | $1.7976931348623157\times 10^{308}$ (`0x7FEF_FFFF_FFFF_FFFFu64`) |
| `MIN_POSITIVE` | `Self` | $2^{-126} \approx 1.17549435\times 10^{-38}$ (`0x0080_0000u32`) | $2^{-1022} \approx 2.2250738585072014\times 10^{-308}$ (`0x0010_0000_0000_0000u64`) |
| `MIN_EXP` | `i32` | `-125` | `-1021` |
| `MAX_EXP` | `i32` | `128` | `1024` |
| `MIN_10_EXP` | `i32` | `-37` | `-307` |
| `MAX_10_EXP` | `i32` | `38` | `308` |
| `INFINITY` | `Self` | $+\infty$ (`0x7F80_0000u32`) | $+\infty$ (`0x7FF0_0000_0000_0000u64`) |
| `NEG_INFINITY` | `Self` | $-\infty$ (`0xFF80_0000u32`) | $-\infty$ (`0xFFF0_0000_0000_0000u64`) |
| `NAN` | `Self` | canonical `qNaN` (`0x7FC0_0000u32`) | canonical `qNaN` (`0x7FF8_0000_0000_0000u64`) |

`std.core.float` defines the classification enum and predicates on `f32` (`self: f32`) and `f64` (`self: f64`):
```axiom
@derive(Copy, Clone, Eq, PartialEq)
pub enum FpCategory {
    Nan,
    Infinite,
    Zero,
    Subnormal,
    Normal,
}
```
- `pub fn classify(self: f32) -> FpCategory` / `pub fn classify(self: f64) -> FpCategory`: returns the category per `AXS-FLT-002`.
- `pub fn is_nan(self: f32) -> bool` / `pub fn is_nan(self: f64) -> bool`: `self != self` (equivalently `(bits & EXP_MASK) == EXP_MASK && (bits & MANT_MASK) != 0`).
- `pub fn is_infinite(self: f32) -> bool` / `pub fn is_infinite(self: f64) -> bool`: `(bits & ~SIGN_MASK) == INF_BITS`.
- `pub fn is_finite(self: f32) -> bool` / `pub fn is_finite(self: f64) -> bool`: `(bits & EXP_MASK) != EXP_MASK` (true for `Zero`, `Subnormal`, and `Normal`).
- `pub fn is_normal(self: f32) -> bool` / `pub fn is_normal(self: f64) -> bool`: `let e = bits & EXP_MASK; e != 0 && e != EXP_MASK`.
- `pub fn is_subnormal(self: f32) -> bool` / `pub fn is_subnormal(self: f64) -> bool`: `(bits & EXP_MASK) == 0 && (bits & MANT_MASK) != 0`.
- `pub fn is_sign_positive(self: f32) -> bool` / `pub fn is_sign_positive(self: f64) -> bool`: `(bits >> (BITS - 1)) == 0` (note: true for `+0.0`, `+inf`, and any `NaN` with sign bit `0`).
- `pub fn is_sign_negative(self: f32) -> bool` / `pub fn is_sign_negative(self: f64) -> bool`: `(bits >> (BITS - 1)) == 1` (note: true for `-0.0`, `-inf`, and any `NaN` with sign bit `1`).

### AXS-FLT-005 — Built-in Trait Implementations & Absence of `Eq`/`Ord` (`ANUM-45..51`, `tasks/0427 §20`)

1. Both `f32` and `f64` implement:
   - `Copy` and `Clone` (bitwise copy of the 32-bit or 64-bit IEEE-754 representation).
   - `PartialEq` (`==`, `!=` following IEEE-754 unordered partial equality, `AXS-FLT-020`).
   - `PartialOrd` (`partial_cmp` returning `Option<Ordering>`: `Option.None` when either operand is `NaN`, `Option.Some(Ordering.Equal)` for `-0.0` vs `+0.0`, and `Option.Some(Less | Greater | Equal)` for ordered pairs).
   - `Default` (`0.0f32` and `0.0f64`, positive zero).
   - `Send` and `Share` (`SPEC-30 AXS-CONC-010`: primitive value types with no interior mutability).
2. Neither `f32` nor `f64` implements `Eq` or `Ord` directly because `NaN != NaN` violates reflexivity (`tasks/0427 §20`, `ANUM-48`). Sorting, binary search, and total comparisons use `x.total_cmp(y) -> Ordering` (`AXS-FLT-021`).
3. If a floating-point value is hashed via canonical float key helpers (`ANUM-51`), `-0.0` and `+0.0` must normalize to the same canonical zero bit pattern (`0`) so `a == b ==> hash(a) == hash(b)` holds for all non-`NaN` values, and all `NaN` bit patterns normalize to canonical `NAN` bits.

### AXS-FLT-006 — Floating-Point Literal Patterns (`SPEC-04 AXS-EXT-034`, `T457`)

In `match` and `let` pattern matching (`SPEC-04 AXS-EXT-034`), a literal pattern may be a positive or negated finite floating-point literal (`0.0`, `-1.5`, `3.14f32`):
- Matching a scrutinee `s` against a float literal pattern `pat_lit` lowers to the IEEE-754 equality comparison `s == pat_lit` (`MIR_BINOP_EQ`), so `-0.0` matches `0.0`.
- Because `f32` and `f64` have an infinite domain (for exhaustiveness purposes) and include `NaN`, a `match` on `f32` or `f64` always requires a wildcard `_` or binding catch-all arm (`AX_PAT_NON_EXHAUSTIVE` if omitted).

---

## 2. Strict IEEE-754 Arithmetic, Rounding, Special Values & Optimization Contract

### AXS-FLT-010 — Default Strict IEEE-754 Arithmetic & `roundTiesToEven` (`ANUM-41..55`)

1. **Default profile is `Strict FP`**: In all compilation profiles (`--interp`, `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, `--pgo-use`), floating-point operations on `f32` and `f64` obey **strict IEEE-754-2019 semantics** under the default rounding mode **roundTiesToEven** (round to nearest representable value, ties round to the neighbor with an even least-significant significand bit $0$).
2. **Core operators**:
   - `a + b` (`MIR_BINOP_ADD`), `a - b` (`MIR_BINOP_SUB`), `a * b` (`MIR_BINOP_MUL`), `a / b` (`MIR_BINOP_DIV`): compute the infinitely precise mathematical result and round once to the target precision (`24` bits for `f32`, `53` bits for `f64`) using `roundTiesToEven`.
   - Unary `-a` (`MIR_UNOP_NEG`): flips the IEEE-754 sign bit (`bits ^ SIGN_MASK`), transforming `+0.0` $\leftrightarrow$ `-0.0`, `+inf` $\leftrightarrow$ `-inf`, and flipping the sign bit of finite values and `NaN`s without altering exponent or significand bits.
   - Compound assignments (`+=`, `-=`, `*=`, `/=`, `%=`) evaluate according to `SPEC-03 AXS-SEM-044` using the corresponding strict floating-point binary operator.
3. **No overflow panic on floats (`tasks/0345 §20, §25–26`)**: Unlike integer `+`, `-`, `*`, `/`, `%`, floating-point arithmetic **never panics** on overflow, underflow, division by zero, or invalid domain:
   - In `compiler/mir/builder.ax` (`T457`), lowering `a + b`, `a - b`, `a * b`, `a / b`, `a % b`, or `-a` when the operand type is `TY_F32` or `TY_F64` emits a single `MIR_RVALUE_BINARY_OP` / `MIR_RVALUE_UNARY_OP` instruction with **no** `MIR_RVALUE_OVERFLOWS_BINARY_OP` and **no** `MIR_TERM_ASSERT` overflow/divzero check.
   - Likewise, constant evaluation (`const` items) of floating-point expressions producing `±inf` or `NaN` succeeds and produces the corresponding IEEE-754 `ConstValue.Float` without emitting `AX_CONST_OVERFLOW` or `AX_CONST_DIV_ZERO`.

### AXS-FLT-011 — Division by Zero, Truncating Remainder (`%`), `±inf` & Gradual Underflow

1. **Floating-point division (`a / b`)**:
   - Finite non-zero `a / ±0.0` produces signed infinity: $\text{sgn}(a) \oplus \text{sgn}(b)$ (`1.0 / +0.0 == +inf`, `1.0 / -0.0 == -inf`, `-1.0 / -0.0 == +inf`).
   - `±0.0 / ±0.0` and `±inf / ±inf` produce quiet `NaN` (`AXS-FLT-002`).
   - Finite `a / ±inf` produces signed zero with sign $\text{sgn}(a) \oplus \text{sgn}(b)$.
   - `±inf / finite` produces signed infinity with sign $\text{sgn}(a) \oplus \text{sgn}(b)$.
2. **Floating-point remainder (`a % b`, `MIR_BINOP_REM`)**:
   - `a % b` is the exact truncating floating-point remainder (`fmod`), defined for finite `a` and non-zero finite `b` as $r = a - \text{trunc}(a / b) \cdot b$, where $\text{trunc}(a / b)$ is the mathematical quotient truncated toward zero to an exact integer (possibly exceeding 64-bit integer range, computed via exact exponent-aligned significand reduction).
   - If $r == 0$, the sign bit of $r$ equals the sign bit of the dividend `a` (`-4.0 % 2.0` has bit pattern `-0.0`).
   - Special cases for `a % b`:
     - If `a.is_nan()` or `b.is_nan()` or `a.is_infinite()` or `b == 0.0`, the result is quiet `NaN` (never a panic!).
     - If `a` is finite and `b.is_infinite()`, the result is `a` (preserving the exact bit pattern and sign of `a`, including `-0.0`).
3. **Gradual underflow (subnormals)**:
   - Both the MIR interpreter oracle (`--interp`) and native x86-64 SSE2 execution (`MXCSR` bits `FTZ = 0` and `DAZ = 0`) preserve full IEEE-754 gradual underflow for subnormal inputs and outputs.

### AXS-FLT-012 — Quiet `NaN` Propagation & Indeterminate Forms (`ANUM-42`, `ANUM-45`)

1. Any arithmetic operation (`+`, `-`, `*`, `/`, `%`, unary `-`, `sqrt`, `fma`) where at least one input is `NaN` returns a quiet `NaN`.
2. The following indeterminate operations on non-`NaN` inputs produce a quiet `NaN` (`AXS-FLT-002`):
   - `(+inf) + (-inf)` and `(-inf) + (+inf)`
   - `(+inf) - (+inf)` and `(-inf) - (-inf)`
   - `±0.0 * ±inf` and `±inf * ±0.0`
   - `±0.0 / ±0.0` and `±inf / ±inf`
   - `x % ±0.0` and `±inf % y`
   - `sqrt(x)` for $x < 0.0$ (note: `sqrt(-0.0) == -0.0` per IEEE-754).

### AXS-FLT-013 — Signed Zero (`+0.0` vs `-0.0`) Semantics (`ANUM-43`, `ANUM-46`)

Axiom preserves the IEEE-754 distinction between `+0.0` ($s = 0$) and `-0.0` ($s = 1$) across all operations:
1. **Equality**: `-0.0 == +0.0` is `true`, and `-0.0 != +0.0` is `false`; `<`, `>`, `<=`, `>=` treat `-0.0` and `+0.0` as equal (`-0.0 < +0.0 == false`, `-0.0 <= +0.0 == true`).
2. **Addition and subtraction**:
   - Under `roundTiesToEven`, `(+0.0) + (+0.0) == +0.0`, `(-0.0) + (-0.0) == -0.0`, and `(+0.0) + (-0.0) == (-0.0) + (+0.0) == +0.0`.
   - For any finite $x$, $x - x == (+0.0)$ under `roundTiesToEven`, whereas `(-0.0) - (+0.0) == -0.0`.
   - Crucially, for $x = -0.0$, `x + 0.0` evaluates to `+0.0` whereas `x - 0.0` (and `x + (-0.0)`) evaluates to `-0.0`.
3. **Multiplication and division**: The sign of a product or quotient zero is the XOR of the operand sign bits ($s_a \oplus s_b$), so `(-0.0) * 5.0 == -0.0`, `(-0.0) * (-5.0) == +0.0`, and `(-0.0) / 2.0 == -0.0`.
4. **Square root**: `sqrt(+0.0) == +0.0` and `sqrt(-0.0) == -0.0`.
5. **Observability**: The sign of zero is directly observable via `1.0 / z` (`+inf` vs `-inf`), `z.is_sign_negative()`, `z.copysign(1.0)`, `z.to_bits()`, `z.total_cmp(0.0)`, and string formatting (`format(-0.0) == "-0.0"`, `§6`).

### AXS-FLT-014 — Prohibition of Implicit Fast-Math & Uncontracted FMA (`ANUM-43..45, 98`, `ASIMD-40..43`, `REQ-SIMD-108..110`, `REQ-SIMD-163`, `REQ-SIMD-186..189`, `T458`)

In strict floating-point mode (the default across all optimization levels `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, `--pgo-use`), the MIR optimizer (`compiler/opt/const_fold.ax`, `compiler/opt/dce.ax`, OptIR passes in `P15`, and SIMD vectorizers in `E12.3`/`E12.4`) **must never** apply algebraic identities or transformations that violate IEEE-754 `NaN`, signed-zero, infinity, or single-rounding behavior:

1. **Forbidden algebraic rewrites on variables (`T458`)**:
   - **Never fold `x + 0.0 -> x`** (when $x = -0.0$, `x + 0.0` is `+0.0`, not `-0.0`; when $x$ is a signaling `NaN`, addition quietens it). Note: `x - 0.0` or `x + (-0.0)` preserves `-0.0` on finite/zero $x$ only if $x$ is proven not to be `sNaN`, so `const_fold` only folds when both operands are known constants!
   - **Never fold `x * 0.0 -> 0.0` or `0.0 / x -> 0.0`** (when $x$ is `NaN` or `±inf`, `x * 0.0` is `NaN`; when $x < 0$ or $x = -0.0$, `x * 0.0` is `-0.0`).
   - **Never fold `x * 1.0 -> x` or `x / 1.0 -> x`** unless `x` is a known compile-time constant (or proven non-`sNaN`).
   - **Never fold `x - x -> 0.0` or `x / x -> 1.0`** (when $x$ is `±inf` or `NaN`, `x - x` is `NaN`; when $x$ is `0.0`, `±inf`, or `NaN`, `x / x` is `NaN`).
   - **Never fold `x == x -> true`, `x <= x -> true`, `x >= x -> true`, or `x != x -> false`** (when $x$ is `NaN`, `x == x`, `x <= x`, `x >= x` are `false` and `x != x` is `true`).
   - **Never invert `!(a < b) -> a >= b`** (when either operand is `NaN`, `a < b` is `false` so `!(a < b)` is `true`, whereas `a >= b` is `false`).
2. **No implicit floating-point reassociation (`REQ-SIMD-108`, `REQ-SIMD-186`, `REQ-SIMD-270`)**:
   - The compiler must never rewrite `(a + b) + c` into `a + (b + c)`, `(a * b) * c` into `a * (b * c)`, or reorder a sequential floating-point reduction loop without an explicit relaxed numeric contract (`ANUM-43`, `ASIMD-40`).
3. **No implicit FMA contraction (`REQ-SIMD-110`, `REQ-SIMD-188`, `REQ-SIMD-272`, `REQ-SIMD-332`)**:
   - Separate expression `a * b + c` computes `t = round(a * b)` first and then `round(t + c)` (two roundings).
   - Fused multiply-add `fma(a, b, c)` / `a.mul_add(b, c)` computes $\text{round}(a \cdot b + c)$ with a **single** rounding from the exact infinite-precision product $a \cdot b$.
   - Under default strict semantics, the compiler **must never** silently contract `a * b + c` into `FMA`, nor expand `fma(a, b, c)` into separate `MULSD` + `ADDSD` (`ANUM-45`, `ASIMD-42`, `AMATH-60`).
4. **Explicit fast-math / reproducibility contracts (`REQ-SIMD-109`, `REQ-SIMD-163`, `REQ-SIMD-187`, `REQ-SIMD-189`, `REQ-SIMD-271`, `REQ-SIMD-325`)**:
   - Any fast-math relaxation (`reassoc`, `no_nan`, `no_inf`, `no_signed_zeros`, `contract_fma`, `approx_recp`) requires an explicit semantic contract (reserved attribute `@fast_math(...)` in post-v1 profiles) and is never enabled implicitly by `-O1`/`-O2`/`-O3` or target CPU feature flags (`ANUM-44`, `ANUM-98`, `ASIMD-41`, `ASIMD-43`).

### AXS-FLT-015 — Directed Rounding & Neighbor Operations (`std.core.float`, `T458`, `T460`)

Every floating-point type `T` in `{f32, f64}` (`self: f32` in `impl f32`, `self: f64` in `impl f64`) provides the following deterministic rounding and neighbor methods (preserving the sign of `±0.0` and propagating `±inf` and `NaN` unchanged):

1. `pub fn floor(self: f32) -> f32` / `pub fn floor(self: f64) -> f64`: largest integral floating-point value $\le self$ (`roundTowardNegative`). For $x \in (-1.0, -0.0]$, `(-0.5).floor() == -1.0` and `(-0.0).floor() == -0.0`.
2. `pub fn ceil(self: f32) -> f32` / `pub fn ceil(self: f64) -> f64`: smallest integral floating-point value $\ge self$ (`roundTowardPositive`). Crucially, for $x \in (-1.0, 0.0)$, `(-0.5).ceil() == -0.0` (with negative sign bit $s = 1$).
3. `pub fn trunc(self: f32) -> f32` / `pub fn trunc(self: f64) -> f64`: integral floating-point value nearest to $self$ whose magnitude is $\le |self|$ (`roundTowardZero`). For $x \in (-1.0, 0.0)$, `(-0.5).trunc() == -0.0`.
4. `pub fn round(self: f32) -> f32` / `pub fn round(self: f64) -> f64`: integral floating-point value nearest to $self$, rounding half-way cases **away from zero** (`roundTiesToAway`: `2.5.round() == 3.0`, `(-2.5).round() == -3.0`, `(-0.4).round() == -0.0`).
5. `pub fn round_ties_even(self: f32) -> f32` / `pub fn round_ties_even(self: f64) -> f64`: integral floating-point value nearest to $self$, rounding half-way cases to the **even** integer (`roundTiesToEven`: `2.5.round_ties_even() == 2.0`, `3.5.round_ties_even() == 4.0`, `(-2.5).round_ties_even() == -2.0`).
6. `pub fn fract(self: f32) -> f32` / `pub fn fract(self: f64) -> f64`: fractional part `self - self.trunc()` (`NaN` for `±inf` and `NaN`, `+0.0` for `+0.0`, `-0.0` for `-0.0` in `self - self.trunc()` or sign-preserving zero).
7. `pub fn next_up(self: f32) -> f32` / `pub fn next_up(self: f64) -> f64` and `pub fn next_down(self: f32) -> f32` / `pub fn next_down(self: f64) -> f64` (IEEE-754 `nextUp` / `nextDown`):
   - `next_up`: smallest representable value strictly greater than `self` (`(-0.0).next_up() == (+0.0).next_up() == MIN_POSITIVE_SUBNORMAL`, `(-inf).next_up() == MIN`, `MAX.next_up() == +inf`, `(+inf).next_up() == +inf`, `NaN.next_up() == NaN`).
   - `next_down`: largest representable value strictly less than `self` (`(+0.0).next_down() == (-0.0).next_down() == -MIN_POSITIVE_SUBNORMAL`, `(+inf).next_down() == MAX`, `MIN.next_down() == -inf`, `(-inf).next_down() == -inf`, `NaN.next_down() == NaN`).

### AXS-FLT-016 — Minimum, Maximum & Clamping (`min`, `max`, `clamp`, `T458`, `T460`)

1. `pub fn min(self: f32, other: f32) -> f32` / `pub fn min(self: f64, other: f64) -> f64` (IEEE-754-2008 `minNum`):
   - If exactly one of `self` or `other` is `NaN`, returns the **non-`NaN`** operand (`(1.0).min(f64.NAN) == 1.0`, `(f64.NAN).min(1.0) == 1.0`).
   - If both are `NaN`, returns quiet `NaN`.
   - Between `-0.0` and `+0.0`, returns `-0.0` (`(-0.0).min(0.0)` and `(0.0).min(-0.0)` both have bit pattern `-0.0`).
2. `pub fn max(self: f32, other: f32) -> f32` / `pub fn max(self: f64, other: f64) -> f64` (IEEE-754-2008 `maxNum`):
   - If exactly one of `self` or `other` is `NaN`, returns the **non-`NaN`** operand.
   - If both are `NaN`, returns quiet `NaN`.
   - Between `-0.0` and `+0.0`, returns `+0.0` (`(-0.0).max(0.0)` and `(0.0).max(-0.0)` both have bit pattern `+0.0`).
3. `pub fn clamp(self: f32, min_val: f32, max_val: f32) -> f32` / `pub fn clamp(self: f64, min_val: f64, max_val: f64) -> f64`:
   - **Panics** with `"assertion failed"` (or `"min > max in clamp"`) if `min_val > max_val`, `min_val.is_nan()`, or `max_val.is_nan()`.
   - If `self.is_nan()`, returns quiet `NaN`.
   - If `self < min_val`, returns `min_val`; if `self > max_val`, returns `max_val`; otherwise returns `self` (note: clamping `-0.0` with `min_val = +0.0` or `+0.0` with `max_val = -0.0` follows `if self < min_val { min_val } else if self > max_val { max_val } else { self }`).

---

## 3. Comparisons, Ordering & Numeric/Bit Conversions

### AXS-FLT-020 — IEEE-754 Partial Comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`) & x86-64 `UCOMISS`/`UCOMISD` Truth Table (`ANUM-45..46`, `T458`, `T459`)

1. **Four-valued relation**: Any pair of floating-point values $(a, b) \in T \times T$ satisfies exactly one of four mutually exclusive IEEE-754 relations: **Less** ($a < b$), **Equal** ($a = b$, including $(-0.0, +0.0)$ and $(+0.0, -0.0)$), **Greater** ($a > b$), or **Unordered** ($a$ is `NaN` or $b$ is `NaN`).
2. **Operator truth table**:

| Operator | MIR `MirBinOp` | Less ($a < b$) | Equal ($a = b$) | Greater ($a > b$) | Unordered (`a.is_nan() \|\| b.is_nan()`) | x86-64 `UCOMISS a, b` / `UCOMISD a, b` Condition (`ZF, PF, CF`) |
|---|---|---|---|---|---|---|
| `a == b` | `MIR_BINOP_EQ` | `false` | `true` | `false` | **`false`** | `ZF == 1 && PF == 0` (`sete al` + `setnp cl` + `and al, cl`) |
| `a != b` | `MIR_BINOP_NE` | `true` | `false` | `true` | **`true`** | `ZF == 0 \|\| PF == 1` (`setne al` + `setp cl` + `or al, cl`) |
| `a < b` | `MIR_BINOP_LT` | `true` | `false` | `false` | **`false`** | `UCOMIS* b, a` with `JA` / `seta al` (`CF == 0 && ZF == 0`, which implies `PF == 0`) |
| `a <= b` | `MIR_BINOP_LE` | `true` | `true` | `false` | **`false`** | `UCOMIS* b, a` with `JAE` / `setae al` (`CF == 0`, which implies `PF == 0`) |
| `a > b` | `MIR_BINOP_GT` | `false` | `false` | `true` | **`false`** | `UCOMIS* a, b` with `JA` / `seta al` (`CF == 0 && ZF == 0`, which implies `PF == 0`) |
| `a >= b` | `MIR_BINOP_GE` | `false` | `true` | `true` | **`false`** | `UCOMIS* a, b` with `JAE` / `setae al` (`CF == 0`, which implies `PF == 0`) |

3. **Hardware `UCOMISS` / `UCOMISD` pitfall mandate (`T459`)**:
   - On x86-64, `UCOMISS`/`UCOMISD` sets `ZF = 1, PF = 1, CF = 1` when either operand is `NaN`.
   - Consequently, plain `JE` (`ZF == 1`) is **wrong** for `a == b` (it would return `true` on `NaN`!), plain `JNE` (`ZF == 0`) is **wrong** for `a != b` (it would return `false` on `NaN`!), and plain `JB`/`JBE` (`CF == 1` / `CF == 1 || ZF == 1`) is **wrong** for `a < b` / `a <= b` (it would return `true` on `NaN`!).
   - `compiler/target/x64/isel.ax` (`T459`) **must**:
     - For `a == b`: combine `sete` and `setnp` via bitwise `and` (`ZF == 1 && PF == 0`).
     - For `a != b`: combine `setne` and `setp` via bitwise `or` (`ZF == 0 || PF == 1`).
     - For `a > b` and `a >= b`: run `ucomiss/ucomisd lhs, rhs` and test `seta` (`CF == 0 && ZF == 0`) / `setae` (`CF == 0`), because `PF == 1` always sets `CF = 1` and `ZF = 1` simultaneously.
     - For `a < b` and `a <= b`: swap the operands (`ucomiss/ucomisd rhs, lhs`) and test `seta` / `setae` so `PF == 1` (`CF = 1, ZF = 1`) automatically evaluates to `false` in a single condition code!

### AXS-FLT-021 — IEEE-754 Total Ordering (`total_cmp`, `ANUM-46`, `ANUM-50`, `T460`)

Both `f32` and `f64` implement `pub fn total_cmp(self: f32, other: f32) -> Ordering` and `pub fn total_cmp(self: f64, other: f64) -> Ordering` (in `std.core.float`) conforming to the IEEE-754-2019 `totalOrder` predicate:

$$-\text{qNaN} < -\text{sNaN} < -\infty < \text{negative normals} < \text{negative subnormals} < -0.0 < +0.0 < \text{positive subnormals} < \text{positive normals} < +\infty < +\text{sNaN} < +\text{qNaN}$$

1. **Bitwise canonical algorithm**:
   - For `f32`: let ` mut left = self.to_bits() as i32; let mut right = other.to_bits() as i32; left = left ^ (((left >> 31) as u32 >> 1) as i32); right = right ^ (((right >> 31) as u32 >> 1) as i32);` and return the standard signed `i32` `Ord` comparison of `left` and `right`.
   - For `f64`: let `mut left = self.to_bits() as i64; let mut right = other.to_bits() as i64; left = left ^ (((left >> 63) as u64 >> 1) as i64); right = right ^ (((right >> 63) as u64 >> 1) as i64);` and return the standard signed `i64` `Ord` comparison of `left` and `right`.
2. **Properties**: `total_cmp` is a strict total order (reflexive, antisymmetric on bit patterns, transitive) over all $2^{32}$ `f32` and $2^{64}$ `f64` bit patterns, distinguishing `-0.0 < +0.0` and ordering `NaN` payloads deterministically.

### AXS-FLT-022 — Saturating `FloatToInt` Casts (`as`, `MIR_CAST_FLOAT_TO_INT`, `ANUM-52`, `T457`–`T459`)

An explicit cast `x as Dst` where `x` has type `Src` $\in \{\text{f32}, \text{f64}\}$ and `Dst` is any of the twelve integer types $\{i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize\}$ lowers to `MIR_RVALUE_CAST` with `MIR_CAST_FLOAT_TO_INT` (`4u8` in `compiler/mir/mir.ax`) and executes **saturating truncation toward zero**:

1. **NaN maps to `0`**: If `x.is_nan()`, `x as Dst == 0`.
2. **Truncate toward zero**: Let $v = \text{trunc}(x)$ be the mathematical integer part of $x$ truncated toward zero (for `±inf`, $v = \pm\infty$).
3. **Saturate to `[Dst.MIN, Dst.MAX]`**:
   - If $v \le \text{Dst.MIN}$ (including $x = -\infty$, or $x < 0$ when `Dst` is unsigned), `x as Dst == Dst.MIN` (`0` for unsigned `Dst`).
   - If $v \ge \text{Dst.MAX}$ (including $x = +\infty$, or $x \ge 2^{31}$ for `i32`, $x \ge 2^{63}$ for `i64`, $x \ge 2^{64}$ for `u64`), `x as Dst == Dst.MAX`.
   - Otherwise, `x as Dst` is the exact integer $v$ represented in `Dst`.
4. **No UB and no hardware `#IA` exception**:
   - On x86-64, `CVTTSS2SI` and `CVTTSD2SI` return the "integer indefinite" value `0x8000_0000` (`i32.MIN`) or `0x8000_0000_0000_0000` (`i64.MIN`) whenever the input is `NaN`, `+inf`, `-inf`, or outside `[MIN, MAX]`.
   - Therefore, raw `CVTTSS2SI`/`CVTTSD2SI` alone is **not sufficient**; both the MIR interpreter (`T458`) and the x86-64 backend (`T459`, `§5 AXS-FLT-044`) must check for `NaN` (`-> 0`) and upper/lower saturation bounds so `NaN as i32 == 0`, `1e20f64 as i32 == 2147483647`, and `(-1e20f64) as u32 == 0u32` agree bit-for-bit across `--interp` and native x86-64!

### AXS-FLT-023 — `IntToFloat` Casts (`as`, `MIR_CAST_INT_TO_FLOAT`) & Lossless `From` Subset (`ANUM-53`, `T457`–`T459`)

1. **Primitive `as` cast (`MIR_CAST_INT_TO_FLOAT`, `5u8` in `compiler/mir/mir.ax`)**:
   - For any source integer type `Src` $\in \{i8..i128, u8..u128, isize, usize\}$ and target float type `Dst` $\in \{\text{f32}, \text{f64}\}$, `x as Dst` converts the exact mathematical integer $x$ to `Dst` using **roundTiesToEven**:
     - If $|x|$ is representable with $\le 24$ significand bits (`f32`) or $\le 53$ significand bits (`f64`), the conversion is exact.
     - Otherwise, $x$ is rounded to the nearest representable floating-point value in `Dst`, breaking ties to even significand bit $0$.
     - Specifically for `u128 as f32`: values $\ge (2 - 2^{-24}) \cdot 2^{128} = 340\,282\,356\,779\,733\,661\,637\,539\,395\,458\,142\,568\,448$ overflow to `+inf` (`f32.INFINITY`) under `roundTiesToEven` (`u128.MAX as f32 == f32.INFINITY`), whereas `i128.MIN as f32 == -1.7014118e38f32` and all `i128`/`u128 as f64` values are finite (since $2^{128} \ll 2^{1024}$).
2. **Lossless `From<Int> for Float` implementations (`std.core.convert`, `TRY_CAST` infallible subset)**:
   - `From<Src> for f32` is implemented **only** for `i8`, `u8`, `i16`, `u16` (widths $\le 16 < 24$, where every integer is $100\%$ exact in `f32`; `i32`/`u32` can lose precision above $2^{24} = 16\,777\,216$ and therefore are **not** in `From<...> for f32` per `tasks/0331 §29`).
   - `From<Src> for f64` is implemented **only** for `i8`, `u8`, `i16`, `u16`, `i32`, `u32` (widths $\le 32 < 53$, where every integer is $100\%$ exact in `f64`; `i64`/`u64`/`isize`/`usize`/`i128`/`u128` can lose precision above $2^{53}$ and are **not** in `From<...> for f64`).

### AXS-FLT-024 — `FloatConvert` Casts (`f32 <-> f64`, `MIR_CAST_FLOAT_CONVERT`, `ANUM-87`)

1. **Widening `f32 as f64` (`MIR_CAST_FLOAT_CONVERT`, `6u8` in `compiler/mir/mir.ax`, and `From<f32> for f64`)**:
   - Every finite, zero, subnormal, or infinite `f32` value is converted **losslessly and exactly** to `f64` (`CVTSS2SD`), preserving sign bit $s$.
   - If the `f32` input is `NaN`, the result is a quiet `NaN` in `f64` (preserving the sign bit and quietness).
   - `std.core.convert` implements `From<f32> for f64` (and `Into<f64> for f32`).
2. **Narrowing `f64 as f32` (`MIR_CAST_FLOAT_CONVERT`)**:
   - Narrowing `f64` to `f32` is **never implicit** (`AX_TYPE_MISMATCH` if written without `as`); it requires an explicit `x as f32` cast.
   - `x as f32` rounds the `f64` value to `f32` using `roundTiesToEven` (`CVTSD2SS`), overflowing to `±f32.INFINITY` if $|x| \ge (2 - 2^{-24}) \cdot 2^{128}$, underflowing to subnormal or `±0.0f32` for tiny magnitudes, preserving `-0.0f64 as f32 == -0.0f32`, and mapping any `NaN` to a quiet `f32` `NaN`.

### AXS-FLT-025 — Bitcasts (`to_bits` / `from_bits`) & Endian Byte Conversions (`ANUM-38`, `REQ-SIMD-106`, `T458`, `T460`)

Per `SPEC-40 AXS-INT-040, AXS-INT-044`, bit reinterpretation (`BITCAST`) is strictly distinct from numeric conversion (`as`):
1. **`f32` bitcasts and byte conversions**:
   - `f32.to_bits(self: f32) -> u32`: returns the exact 32-bit IEEE-754 bit pattern of `self` without altering any `NaN` payload or sign bit (`MOVD eax, xmm0`).
   - `f32.from_bits(v: u32) -> f32`: reinterprets the 32-bit unsigned integer `v` as an `f32` bit-for-bit (`f32.from_bits(x.to_bits())` has identical bits to `x` for all $2^{32}$ bit patterns).
   - `f32.to_le_bytes(self: f32) -> [4]u8`, `f32.from_le_bytes(b: [4]u8) -> f32`, `f32.to_be_bytes(self: f32) -> [4]u8`, `f32.from_be_bytes(b: [4]u8) -> f32`, `f32.to_ne_bytes(self: f32) -> [4]u8`, `f32.from_ne_bytes(b: [4]u8) -> f32`: exact delegation to `self.to_bits().to_*_bytes()` and `f32.from_bits(u32.from_*_bytes(b))`.
2. **`f64` bitcasts and byte conversions**:
   - `f64.to_bits(self: f64) -> u64` and `f64.from_bits(v: u64) -> f64` (`MOVQ rax, xmm0` / `MOVQ xmm0, rax`): exact 64-bit bit-pattern reinterpretation.
   - `f64.to_le_bytes(self: f64) -> [8]u8`, `f64.from_le_bytes(b: [8]u8) -> f64`, `f64.to_be_bytes(self: f64) -> [8]u8`, `f64.from_be_bytes(b: [8]u8) -> f64`, `f64.to_ne_bytes(self: f64) -> [8]u8`, `f64.from_ne_bytes(b: [8]u8) -> f64`: exact delegation to `u64` endian byte conversions.

---

## 4. Complex Mixed-Type Expression Promotion Lattice & Homogeneous MIR Lowering (`REQ-OWNER-007`)

### AXS-FLT-030 — Architectural Mandate of the `REQ-OWNER-007` Mixed-Type Expression Matrix (`OWNER.md REQ-OWNER-007`, `T456`, `T457`, `T462`)

`REQ-OWNER-007` is a binding project-owner requirement:
> In complex mathematical expressions mixing unsuffixed numeric literals (`1`, `-3`, `0x3F`, `0.5`, `6.0`) and variables of different numeric types (`i8..usize`, `f32`, `f64`) across nested arithmetic, bitwise/shift, unary, array-index, call, and comparison sub-expressions, the compiler automatically infers literal types and promotes narrower integer/float variables along a deterministic numeric lattice lowered to explicit MIR casts so no suffixes or manual `as` casts are required.

To satisfy `REQ-OWNER-007` without introducing C-style silent narrowing UB or backend register-class chaos, Axiom enforces a **two-part architectural contract**:
1. **Frontend / `typeck` deterministic promotion lattice**: Inside compound numeric expressions, unsuffixed literals (`IntVar`, `FloatVar`) and narrower integer/floating-point operands automatically unify and widen along a single, cycle-free promotion lattice (`AXS-FLT-031..033`).
2. **Homogeneous MIR lowering via explicit `MIR_RVALUE_CAST` (`AXS-FLT-034`)**: All numeric promotions are resolved **exclusively** in `compiler/types/typeck.ax` and HIR-to-MIR lowering (`compiler/mir/builder.ax`), which materializes an explicit `MIR_RVALUE_CAST` (`IntToInt`, `IntToFloat`, or `FloatConvert`) temporary local **before** every binary arithmetic, bitwise, comparison, or array-index instruction. Consequently, Verified MIR, the MIR interpreter (`compiler/interp/`), the MIR optimizer (`compiler/opt/`), LIR (`compiler/lir/`), and the x86-64 backend (`compiler/target/x64/`) see **100% homogeneous operand types** on every instruction and never mix GPR and XMM registers or narrow and wide widths inside a single binary instruction.

### AXS-FLT-031 — Complete Numeric Promotion Lattice & Binary Join $\text{join}_{\text{num}}(T_1, T_2)$ (`REQ-OWNER-007`, `T457`)

The complete scalar numeric universe consists of:
- Inference literal variables: `IntVar` (`TY_INT_VAR`, unsuffixed integer literal) and `FloatVar` (`TY_FLOAT_VAR`, unsuffixed float literal).
- Concrete integer types $\mathcal{I} = \{\text{i8}, \text{i16}, \text{i32}, \text{i64}, \text{isize}, \text{i128}, \text{u8}, \text{u16}, \text{u32}, \text{u64}, \text{usize}, \text{u128}\}$.
- Concrete floating-point types $\mathcal{F} = \{\text{f32}, \text{f64}\}$ with strict promotion order $\text{f32} \prec \text{f64}$.

The global promotion partial order embeds the pure-integer sub-lattice of `SPEC-40 AXS-INT-051` below the floating-point chain:

```text
   u8  ──►  u16  ──►  u32  ──►  u64 / usize  ──►  u128 ─┐
    │        │         │             │                  │
    ▼        ▼         ▼             ▼                  ▼
   i8  ──►  i16  ──►  i32  ──►  i64 / isize  ──►  i128 ─┼──►  f32  ──►  f64
                                                        ▲      ▲
                                                   IntVar      FloatVar
```

For any two numeric operand types $T_1, T_2$ in a binary arithmetic (`+`, `-`, `*`, `/`, `%`) or relational comparison (`==`, `!=`, `<`, `<=`, `>`, `>=`) expression, the deterministic common promoted type $T_{\text{common}} = \text{join}_{\text{num}}(T_1, T_2)$ is defined by five exhaustive rules:

1. **Identity ($T_1 == T_2$)**:
   - If $T_1 = T_2$, then $\text{join}_{\text{num}}(T_1, T_2) = T_1$ (no cast emitted).
2. **Both floating-point ($T_1, T_2 \in \{\text{f32}, \text{f64}, \text{FloatVar}\}$)**:
   - $\text{join}_{\text{num}}(\text{f64}, \text{f32}) = \text{join}_{\text{num}}(\text{f32}, \text{f64}) = \text{f64}$ (the `f32` operand is promoted via `MIR_CAST_FLOAT_CONVERT` to `f64`).
   - $\text{join}_{\text{num}}(\text{f32}, \text{FloatVar}) = \text{f32}$ (the `FloatVar` literal unifies directly to `f32`, unless an enclosing wider `f64` arithmetic context promotes the sub-tree to `f64`).
   - $\text{join}_{\text{num}}(\text{f64}, \text{FloatVar}) = \text{f64}$ (the `FloatVar` literal unifies to `f64`).
   - $\text{join}_{\text{num}}(\text{FloatVar}, \text{FloatVar}) = \text{FloatVar}$ (resolving to the enclosing float context or defaulting to `f64`).
3. **One floating-point and one integer ($T_1 \in \{\text{f32}, \text{f64}, \text{FloatVar}\}$ and $T_2 \in \mathcal{I} \cup \{\text{IntVar}\}$, or symmetrically)**:
   - Let $F \in \{\text{f32}, \text{f64}\}$ be the floating-point type (if $T_1 = \text{FloatVar}$, $F$ resolves to the enclosing expected float type if `f32`, else `f64`).
   - Then $\text{join}_{\text{num}}(F, T_2) = \text{join}_{\text{num}}(T_2, F) = F$!
   - If the integer operand is an unsuffixed `IntVar` literal (`1`, `-3`, `2`, `4`), it is fixed to $F$ (`IntToFloat` literal fixing `SPEC-04 AXS-EXT-035` / `MIR_CAST_INT_TO_FLOAT`).
   - If the integer operand has a concrete integer type $I \in \mathcal{I}$ (`i8..i128`, `u8..u128`, `isize`, `usize`), it is promoted to $F$ via an explicit `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_FLOAT`).
4. **Both integer ($T_1, T_2 \in \mathcal{I} \cup \{\text{IntVar}\}$)**:
   - If one operand is `IntVar` and the other is a concrete integer type $I \in \mathcal{I}$, $\text{join}_{\text{num}}(I, \text{IntVar}) = I$ (or the enclosing wider integer context $T_{\text{ctx}}$ per `SPEC-40 AXS-INT-052`).
   - If both operands are concrete integer types $T_1, T_2 \in \mathcal{I}$, $\text{join}_{\text{num}}(T_1, T_2) = \text{join}_{\text{int}}(T_1, T_2)$ as defined in `SPEC-40 AXS-INT-051`:
     - Same signedness, different widths: wider type (`i8 -> i16 -> i32 -> i64/isize -> i128`; `u8 -> u16 -> u32 -> u64/usize -> u128`).
     - Narrower unsigned $U_N$ + wider signed $I_M$ ($N < M$, e.g. `u16 + i64`, `u32 + isize`, `u8 + isize`): wider signed type $I_M$.
     - Narrower signed $I_N$ + wider unsigned $U_M$ ($N < M$, e.g. `i8 + u16`): smallest signed type $I_K$ ($K > M$) containing both (`i32` for $M=16$, `i64` for $M=32$, `i128` for $M=64$; or the active wider signed context $T_{\text{ctx}}$).
     - Same-width signed + unsigned (`i32 + u32`, `i8 + u8`): promotes to the enclosing wider signed/float context if inside a wider arithmetic tree; otherwise rejected with `AX_TYPE_MISMATCH`.
   - Every integer operand narrower than $T_{\text{common}}$ is promoted via `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`).

### AXS-FLT-032 — Contextual Literal Unification (`IntVar`, `FloatVar` & `IntToFloat` Fixing, `SPEC-04 AXS-EXT-035`)

1. **`IntVar` in integer contexts**: An unsuffixed integer literal (`1`, `2`, `3`, `4`, `5`, `7`, `10`, `0x3F`) in a binary operation with an integer operand $e : I$ unifies its `IntVar` with $I$ (or with the promoted integer type of the enclosing multi-width integer sub-tree per `SPEC-40 AXS-INT-052`).
2. **`IntVar` in floating-point contexts (`IntToFloat` literal fixing, `SPEC-04 AXS-EXT-035`)**:
   - When an unsuffixed integer literal (`1` in `a + i * k - 1`, `2` in `a * a / 6.0 - k + 2`, `3` in `x - 3`, `4` in `coeff[idx - 1] * 4`) appears as an operand of `+`, `-`, `*`, `/`, `%`, or comparison alongside a floating-point operand of type $F \in \{\text{f32}, \text{f64}\}$, `typeck` fixes the literal to $F$ (either by typing the literal directly as $F$ or typing it as `i32`/`i64` and emitting `MIR_CAST_INT_TO_FLOAT` to $F$).
   - Note: Standalone binding of an integer literal to a float variable without a decimal point (`let x: f64 = 1`) remains `AX_TYPE_MISMATCH` (`SPEC-03 AXS-SEM-020`); `IntToFloat` fixing applies only to unsuffixed integer literals participating in numeric operator expressions where the peer operand (or enclosing arithmetic operator) is floating-point!
3. **`FloatVar` in mixed expressions**:
   - An unsuffixed float literal (`0.5`, `6.0`, `1.25`) combined with an `f32` operand (`w + 0.5` where `w: f32`) unifies its `FloatVar` to `f32` (`0.5f32`), so `w + 0.5` has type `f32`. If that `f32` sub-expression then combines with an `f64` operand (`((...) / (...)) * (w + 0.5)`), the `f32` result is promoted to `f64` via `MIR_CAST_FLOAT_CONVERT`.
   - An unsuffixed float literal combined with an integer operand (`i * 0.5` where `i: i32`, or `(base / 10 - u) + 1.25` where `base / 10 - u: i64`) resolves its `FloatVar` to the enclosing float context (`f32` if the enclosing expression expects `f32`, otherwise default `f64`), and promotes the integer operand to that float type via `MIR_CAST_INT_TO_FLOAT`.

### AXS-FLT-033 — Sub-Expression Propagation Across Operator Kinds (`REQ-OWNER-007`)

Inside a complex expression tree, each operator category preserves its exact domain semantics while feeding its result into the parent node's promotion join:

1. **Pure-integer arithmetic sub-trees inside a larger float expression**:
   - When both operands of `+`, `-`, `*`, `/`, or `%` are integer sub-expressions (e.g., `i * k`, `2 * n + u - 3`, `base - u * 4 + i` in Pattern A; `((mask >> sh) & 0x3F) + delta * step - 5` and `(1 << sh) + 3` in Pattern B; `idx * 2 + 1` and `base / 10 - u` in Pattern C; all of Pattern D), the sub-expression is evaluated using **integer arithmetic** at the promoted integer width $\text{join}_{\text{int}}$ (`SPEC-40 AXS-INT-051..052`).
   - In particular, `base / 10` (where `base: i64` and `10: IntVar`) performs **integer division** `i64 / i64 -> i64` before subtracting `u: u16` (widened to `i64`) and finally promoting `(base / 10 - u): i64` to `f64` when adding `1.25`!
   - A sub-expression switches from integer arithmetic to floating-point arithmetic **at the exact AST/HIR binary operator node** where one child has floating-point type (`f32`, `f64`, `FloatVar`).
2. **Bitwise (`&`, `|`, `^`, `~`) and shift (`<<`, `>>`) sub-trees**:
   - Bitwise and shift operators require integer operands (`AX_TYPE_OPERATOR` if applied to `f32`/`f64`).
   - In `x << sh` and `x >> sh`, `x` is any integer type (if `x` is an unsuffixed `IntVar` as in `1 << sh`, `1` defaults/resolves to `i32` unless constrained by a wider pure-integer bitwise context), `sh` is any integer type (`u8`, `u32`, `usize`, etc.), and the shift result has the type of `x`.
   - In `lhs & rhs`, `lhs | rhs`, `lhs ^ rhs`, both integer operands promote to $\text{join}_{\text{int}}(T_{\text{lhs}}, T_{\text{rhs}})$ (`(mask >> sh) & 0x3F` has `mask >> sh: u32` and `0x3F: IntVar -> u32`, yielding `u32`), which can then feed directly into an enclosing integer or floating-point arithmetic expression (`(((mask >> sh) & 0x3F) + delta * step - 5)`).
3. **Unary negation (`-e`) and bitwise NOT (`~e`)**:
   - Unary `-e` preserves the type of `e` (promoting narrow unsigned only if inside a wider signed arithmetic context after folding literal negation; for any signed integer or float `e`, `-e` has the same type as `e`).
4. **Array and slice indexing (`base[idx_expr]`, `SPEC-40 AXS-INT-053`)**:
   - Inside `base[idx_expr]` (such as `coeff[idx + off]` with `idx: u8, off: isize` and `coeff[idx - 1]` with `idx: u8`), `idx_expr` is first typed using the integer promotion rules (`idx + off` promotes `idx: u8` to `isize` via `MIR_CAST_INT_TO_INT`, yielding `isize`; `idx - 1` unifies `1` with `u8`, yielding `u8`).
   - Then `compiler/mir/builder.ax` emits an explicit `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`) converting the index result from `T_idx` (`isize` or `u8`) to `usize` before `MIR_PROJ_INDEX` and the array bounds check.
   - The resulting element value `coeff[...]` has the array element type (`f32` in Pattern C), which then participates in the enclosing arithmetic promotion (`coeff[idx + off] * (x - 3)` promotes `f32 -> f64` via `MIR_CAST_FLOAT_CONVERT`).
5. **Relational and equality comparisons (`<`, `<=`, `>`, `>=`, `==`, `!=`)**:
   - In `lhs cmp rhs` (such as `(p + i * 0.5) > (base / 10 - u + 1.25)` in Pattern C, or `int_expr < float_expr`), `lhs` and `rhs` are first typed independently, and if both are numeric ($T_{\text{lhs}}, T_{\text{rhs}} \in \mathcal{I} \cup \mathcal{F} \cup \{\text{IntVar}, \text{FloatVar}\}$), both promote to $T_{\text{common}} = \text{join}_{\text{num}}(T_{\text{lhs}}, T_{\text{rhs}})$ via explicit `MIR_RVALUE_CAST` temporaries before the homogeneous comparison `MIR_RVALUE_BINARY_OP(Eq|Ne|Lt|Le|Gt|Ge)` produces `bool`.

### AXS-FLT-034 — Explicit `MIR_RVALUE_CAST` Lowering & Homogeneous MIR Verifier Invariant (`INV-FLT-002`, `T457`)

1. **MIR Cast Kinds (`compiler/mir/mir.ax`, `SPEC-04 AXS-EXT-042`)**:
   Every numeric promotion synthesized by `typeck` / `compiler/mir/builder.ax` uses `MIR_RVALUE_CAST` with one of the three numeric cast kinds:
   - `MIR_CAST_INT_TO_INT = 0u8`: integer width or signedness conversion (`T_src in Int -> T_dst in Int`).
   - `MIR_CAST_FLOAT_TO_INT = 4u8`: explicit `as` saturating float-to-integer conversion (`f32/f64 -> Int`; never emitted implicitly!).
   - `MIR_CAST_INT_TO_FLOAT = 5u8`: integer-to-float conversion (`T_src in Int -> f32/f64`).
   - `MIR_CAST_FLOAT_CONVERT = 6u8`: float-to-float conversion (`f32 -> f64` in implicit promotion or explicit `as`; `f64 -> f32` in explicit `as` only).
2. **Lowering invariant in `compiler/mir/builder.ax` (`T457`)**:
   Whenever a binary operator `lhs op rhs` has operands whose lowered MIR locals `_lhs: T_lhs` and `_rhs: T_rhs` differ from the resolved operator type $T_{\text{common}}$:
   - If $T_{\text{lhs}} \ne T_{\text{common}}$, the builder allocates a fresh temporary `_lhs_cast: T_common` and emits `_lhs_cast = Cast(kind, _lhs, T_common)` before the binary instruction.
   - If $T_{\text{rhs}} \ne T_{\text{common}}$ (and `op` is not `Shl`/`Shr`), the builder allocates a fresh temporary `_rhs_cast: T_common` and emits `_rhs_cast = Cast(kind, _rhs, T_common)` before the binary instruction.
   - Whenever an index expression `base[idx]` lowers to `_idx: T_idx` with $T_{\text{idx}} \ne \text{usize}$, the builder allocates `_idx_usize: usize` and emits `_idx_usize = Cast(IntToInt, _idx, usize)` before `MIR_PROJ_INDEX(_idx_usize)`.
3. **Strict MIR Verifier enforcement (`compiler/verify/verifier.ax`, `INV-FLT-002`)**:
   - For every `MIR_RVALUE_BINARY_OP` and `MIR_RVALUE_OVERFLOWS_BINARY_OP` (except `MIR_BINOP_SHL`, `MIR_BINOP_SHR`, and `MIR_BINOP_OFFSET`), `verifier.ax` verifies that `ty(lhs) == ty(rhs)`; for arithmetic/bitwise ops (`Add`, `Sub`, `Mul`, `Div`, `Rem`, `BitAnd`, `BitOr`, `BitXor`, `WrappingAdd`, `WrappingSub`, `WrappingMul`, `SatAdd`, `SatSub`, `SatMul`), `verifier.ax` also verifies `ty(dest) == ty(lhs)`, and for comparison ops (`Eq`, `Ne`, `Lt`, `Le`, `Gt`, `Ge`), `verifier.ax` verifies `ty(dest) == TY_BOOL`.
   - For `MIR_RVALUE_BINARY_OP` with `BitAnd`, `BitOr`, `BitXor`, `Shl`, `Shr`, or `MIR_RVALUE_OVERFLOWS_BINARY_OP`, `verifier.ax` rejects `f32`/`f64` operands with `AX_VERIFY_TYPE_MISMATCH`.
   - For `MIR_PROJ_INDEX(index_local)`, `verifier.ax` verifies that `ty(index_local) == TY_USIZE` (or integer index normalized to `usize`).
   - Any violation in compiler-built MIR triggers `AX_ICE_MIR_VERIFY` (`AXD-042`).

### AXS-FLT-035 — Boundaries Where Implicit Promotion Is Forbidden (`ANUM-35..37`, `SPEC-03 AXS-SEM-022`)

To preserve Axiom's explicit type safety at declaration and API boundaries, implicit promotion **never** occurs in the following contexts (each emits `AX_TYPE_MISMATCH`):
1. **Standalone variable binding, assignment, or return statement**:
   - `let x: f64 = a_f32` (standalone variable of type `f32` assigned to `f64` without a mixed binary operator) -> `AX_TYPE_MISMATCH`; write `a_f32 as f64` or `f64.from(a_f32)`.
   - `let x: f64 = n_i32` or `let x: f64 = 1` (integer variable or integer literal without decimal point assigned to `f64`) -> `AX_TYPE_MISMATCH`; write `n_i32 as f64` or `1.0`.
   - `let x: i64 = n_i32` -> `AX_TYPE_MISMATCH` (`SPEC-40 AXS-INT-050`).
2. **Any narrowing conversion (`f64 -> f32`, `Float -> Int`, wider `Int ->` narrower `Int`)**:
   - `let w: f32 = a_f64 + 1.0f32` (expression has promoted type `f64`, assigned to `f32`) -> `AX_TYPE_MISMATCH`; write `(a_f64 + 1.0) as f32`.
   - `let n: i32 = a_f64 + 1.0` -> `AX_TYPE_MISMATCH`; write `(a_f64 + 1.0) as i32`.
3. **Standalone function/method call arguments**:
   - Passing `x: i32` or `w: f32` directly to a parameter `p: f64` (`foo(x)` or `foo(w)`) without an explicit `as f64` or `f64.from(...)` emits `AX_TYPE_MISMATCH`. (However, a compound mixed expression passed as a call argument, such as `foo((a_f64 + i_i32) * 0.5)`, promotes internally to `f64` and matches `p: f64`!).
4. **Standalone same-width signed/unsigned integer binary operation**:
   - `let e = a_i32 + u_u32` (with no enclosing wider signed or float arithmetic context) emits `AX_TYPE_MISMATCH` (`SPEC-40 AXS-INT-051`).

### AXS-FLT-036 — Normative `REQ-OWNER-007` Pattern A & Pattern B Specification (`T457`, `T462`)

#### Pattern A — Deeply Nested Mixed Float/Integer Rational Expression
```axiom
let a: f64 = 6.0
let w: f32 = 1.5f32
let i: i32 = 4
let k: i16 = 3i16
let u: u16 = 5u16
let n: usize = 3usize
let base: i64 = 36i64
let y: f64 = ((a + i * k - 1) / (2 * n + u - 3)) * (w + 0.5) + (base - u * 4 + i) / (a * a / 6.0 - k + 2)
```
**Normative typing & `MIR_RVALUE_CAST` lowering for Pattern A**:
1. `i * k`: `k: i16` $\xrightarrow{\text{Cast(IntToInt, i32)}}$ `_t1: i32`; `_t2: i32 = i * _t1` (`4 * 3 = 12i32`).
2. `a + i * k`: `_t2: i32` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t3: f64`; `_t4: f64 = a + _t3` (`6.0 + 12.0 = 18.0f64`).
3. `(a + i * k) - 1`: literal `1` fixed to `1.0f64` (or `Cast(IntToFloat, 1i32 -> f64)`); `_t5: f64 = _t4 - 1.0f64` (`17.0f64`).
4. `2 * n + u - 3`: `2` unifies with `usize`; `_t6: usize = 2usize * n` (`6usize`); `u: u16` $\xrightarrow{\text{Cast(IntToInt, usize)}}$ `_t7: usize`; `_t8: usize = _t6 + _t7` (`11usize`); `3` unifies with `usize`; `_t9: usize = _t8 - 3usize` (`8usize`). *(Equivalently promoted in `i64` if signed context is used; both yield exact `8`.)*
5. `((a + i * k - 1) / (2 * n + u - 3))`: `_t9: usize` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t10: f64` (`8.0f64`); `_t11: f64 = _t5 / _t10` (`17.0 / 8.0 = 2.125f64`).
6. `w + 0.5`: `0.5` (`FloatVar`) unifies with `w: f32` (`0.5f32`), `_t12: f32 = w + 0.5f32` (`2.0f32`), then `_t12` $\xrightarrow{\text{Cast(FloatConvert, f64)}}$ `_t13: f64` (`2.0f64`); `_t14: f64 = _t11 * _t13` (`4.25f64`).
7. `base - u * 4 + i`: inside the `i64` integer sub-tree (`SPEC-40 AXS-INT-052`), `u: u16` widens via `Cast(IntToInt, i64)` to `_t15: i64`, `_t16: i64 = _t15 * 4i64` (`20i64`), `_t17: i64 = base - _t16` (`16i64`), `i: i32` $\xrightarrow{\text{Cast(IntToInt, i64)}}$ `_t18: i64`, `_t19: i64 = _t17 + _t18` (`20i64`).
8. `a * a / 6.0 - k + 2`: `_t20: f64 = a * a` (`36.0f64`); `6.0` unifies with `f64`, `_t21: f64 = _t20 / 6.0f64` (`6.0f64`); `k: i16` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t22: f64` (`3.0f64`), `_t23: f64 = _t21 - _t22` (`3.0f64`); `2` fixed to `2.0f64`, `_t24: f64 = _t23 + 2.0f64` (`5.0f64`).
9. `(base - u * 4 + i) / (a * a / 6.0 - k + 2)`: `_t19: i64` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t25: f64` (`20.0f64`); `_t26: f64 = _t25 / _t24` (`4.0f64`).
10. `y`: `_t27: f64 = _t14 + _t26` (`4.25 + 4.0 = 8.25f64`).

#### Pattern B — Bitwise/Shift Sub-Trees Feeding Mixed Signed/Unsigned & Float Arithmetic
```axiom
let mask: u32 = 0xABu32
let sh: u8 = 2u8
let delta: i8 = -3i8
let step: isize = 5isize
let scale: f64 = 3.5
let z: f64 = (((mask >> sh) & 0x3F) + delta * step - 5) * scale / ((1 << sh) + 3)
```
**Normative typing & `MIR_RVALUE_CAST` lowering for Pattern B**:
1. `mask >> sh`: `mask: u32`, `sh: u8` $\to$ `_t1: u32 = mask >> sh` (`0xABu32 >> 2u8 = 42u32`).
2. `(mask >> sh) & 0x3F`: `0x3F` (`IntVar`) unifies with `u32` (`0x3Fu32`); `_t2: u32 = _t1 & 0x3Fu32` (`42u32`).
3. `delta * step`: `delta: i8` $\xrightarrow{\text{Cast(IntToInt, isize)}}$ `_t3: isize`; `_t4: isize = _t3 * step` (`-15isize`).
4. `((mask >> sh) & 0x3F) + delta * step`: `join_int(u32, isize) = isize` (32-bit unsigned into 64-bit signed); `_t2: u32` $\xrightarrow{\text{Cast(IntToInt, isize)}}$ `_t5: isize` (`42isize`); `_t6: isize = _t5 + _t4` (`27isize`).
5. `(...) - 5`: `5` (`IntVar`) unifies with `isize` (`5isize`); `_t7: isize = _t6 - 5isize` (`22isize`).
6. `(...) * scale`: `_t7: isize` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t8: f64` (`22.0f64`); `_t9: f64 = _t8 * scale` (`77.0f64`).
7. `(1 << sh) + 3`: `1` (`IntVar`) resolves to `1i32`, `_t10: i32 = 1i32 << sh` (`4i32`); `3` unifies with `i32`, `_t11: i32 = _t10 + 3i32` (`7i32`).
8. `z`: `_t11: i32` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t12: f64` (`7.0f64`); `z: f64 = _t9 / _t12` (`77.0 / 7.0 = 11.0f64`).

### AXS-FLT-037 — Normative `REQ-OWNER-007` Pattern C & Pattern D Specification (`T457`, `T462`)

#### Pattern C — Array-Index Promotion, Mixed `f32`/`f64`/Integer Arithmetic & Relational Comparison
```axiom
let coeff: [4]f32 = [1.0f32, 2.5f32, 4.0f32, 0.5f32]
let idx: u8 = 1u8
let off: isize = 1isize
let x: f64 = 6.0
let i: i32 = 2
let base: i64 = 100i64
let u: u16 = 3u16
let p: f64 = coeff[idx + off] * (x - 3) / (idx * 2 + 1) + coeff[idx - 1] * 4
let ok: bool = (p + i * 0.5) > (base / 10 - u + 1.25)
```
**Normative typing & `MIR_RVALUE_CAST` lowering for Pattern C**:
1. `coeff[idx + off]`: `idx: u8` $\xrightarrow{\text{Cast(IntToInt, isize)}}$ `_t1: isize`; `_t2: isize = _t1 + off` (`2isize`); `_t2: isize` $\xrightarrow{\text{Cast(IntToInt, usize)}}$ `_idx1: usize` (`2usize`); `_elem1: f32 = coeff[_idx1]` (`4.0f32`).
2. `coeff[idx + off] * (x - 3)`: `3` fixed to `3.0f64`, `_t3: f64 = x - 3.0f64` (`3.0f64`); `_elem1: f32` $\xrightarrow{\text{Cast(FloatConvert, f64)}}$ `_t4: f64` (`4.0f64`); `_t5: f64 = _t4 * _t3` (`12.0f64`).
3. `(...) / (idx * 2 + 1)`: `idx * 2 + 1` evaluates in integer (`3u8` or `3i32`) and promotes via `Cast(IntToFloat, f64)` to `_t6: f64` (`3.0f64`); `_t7: f64 = _t5 / _t6` (`4.0f64`).
4. `coeff[idx - 1] * 4`: `idx - 1` evaluates to `0u8` (or `0i32`), promotes via `Cast(IntToInt, usize)` to `_idx2: usize` (`0usize`); `_elem2: f32 = coeff[_idx2]` (`1.0f32`); `4` fixed to `4.0f32`, `_t8: f32 = _elem2 * 4.0f32` (`4.0f32`), then `_t8` $\xrightarrow{\text{Cast(FloatConvert, f64)}}$ `_t9: f64` (`4.0f64`).
5. `p`: `p: f64 = _t7 + _t9` (`4.0 + 4.0 = 8.0f64`).
6. `ok`: `i: i32` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `_t10: f64` (`2.0f64`), `_lhs: f64 = p + _t10 * 0.5f64` (`9.0f64`); `base / 10` is `100i64 / 10i64 = 10i64`, `u: u16` $\xrightarrow{\text{Cast(IntToInt, i64)}}$ `3i64`, `10i64 - 3i64 = 7i64` $\xrightarrow{\text{Cast(IntToFloat, f64)}}$ `7.0f64`, `_rhs: f64 = 7.0f64 + 1.25f64` (`8.25f64`); `ok: bool = _lhs > _rhs` (`9.0 > 8.25 == true`).

#### Pattern D — Pure Multi-Width Signed/Unsigned Integer Promotion (`SPEC-40 AXS-INT-052`)
```axiom
let s64: i64 = 100000
let s32: i32 = -2000
let u16v: u16 = 500
let b8: u8 = 200
let s8: i8 = -50
let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8)
```
As specified in `SPEC-40 AXS-INT-052`, all narrower integer operands (`s32: i32`, `u16v: u16`, `b8: u8`, `s8: i8`) and unsuffixed `IntVar` literals (`3`, `2`, `7`, `4`) inside the `i64` multi-width tree widen via explicit `MIR_RVALUE_CAST(IntToInt -> i64)` temporaries prior to arithmetic (so `b8 * 2` evaluates as `200i64 * 2i64 = 400i64` without overflowing `u8`), yielding `total == 93985i64`.

---

## 5. LIR, Windows x64 ABI & SSE2 Scalar Lowering (`AXS-FLT-040`..`044`)

### AXS-FLT-040 — LIR Floating-Point Scalar Types & `Xmm` Register Class

In the Low-Level Intermediate Representation (`compiler/lir/lir.ax`), scalar floating-point values are first-class values distinct from GPR integer scalars:

1. **LIR Scalar Types**:
   - `LirType.F32` — 32-bit IEEE-754 binary32 scalar (occupies the low 32 bits `[31:0]` of an `XMM` register or a 4-byte aligned stack/memory slot).
   - `LirType.F64` — 64-bit IEEE-754 binary64 scalar (occupies the low 64 bits `[63:0]` of an `XMM` register or an 8-byte aligned stack/memory slot).
2. **`RegClass.Xmm` Physical Registers**:
   - `XMM0` through `XMM15` (16 architectural 128-bit SSE2 registers on x86-64).
   - Scalar `f32`/`f64` operations use the low lane (`[31:0]` for `f32`, `[63:0]` for `f64`) of `XMM0`–`XMM15`. The upper bits (`[127:32]` or `[127:64]`) of an `XMM` register holding a scalar `f32`/`f64` value are unspecified scratch bits and MUST NOT be relied upon by scalar operations.
3. **Floating-Point Immediate Materialization**:
   - x86-64 SSE2 instructions do not encode immediate `f32`/`f64` operands directly.
   - `+0.0f32` and `+0.0f64` MAY be materialized in-register via `XORPS xmm, xmm` / `XORPD xmm, xmm` (NOTE: `-0.0` MUST NOT be materialized via `XORPS`/`XORPD` because that loses the sign bit; `-0.0` MUST load its bit pattern `0x8000_0000u32` or `0x8000_0000_0000_0000u64`).
   - All other `MirConst.Float32(bits)` and `MirConst.Float64(bits)` constants are either emitted into the read-only `.rdata` section (aligned to 4 bytes for `f32` or 8 bytes for `f64`, deduplicated by exact bit pattern `bits`, so `+0.0` and `-0.0` occupy distinct `.rdata` entries) and loaded via RIP-relative `MOVSS xmm, [rip + .LC_f32_XXXXXXXX]` / `MOVSD xmm, [rip + .LC_f64_XXXXXXXXXXXXXXXX]`, or materialized into a scratch GPR via `MOV eax, imm32` / `MOV rax, imm64` followed by `MOVD xmm, eax` / `MOVQ xmm, rax`.

### AXS-FLT-041 — Windows x64 ABI Floating-Point Calling Convention

On `x86_64-pc-windows-msvc` (`SPEC-04 AXS-EXT-052`, `0181`, `T459`), scalar `f32` and `f64` parameters and return values obey the Microsoft x64 calling convention:

1. **Positional Parameter Slots (`0..3`)**:
   - The first four parameter positions (indices `0`, `1`, `2`, `3`) share a single positional index across integer/pointer arguments and floating-point arguments:
     - Slot 0: `RCX` (integer/pointer) or `XMM0` (`f32`/`f64`)
     - Slot 1: `RDX` (integer/pointer) or `XMM1` (`f32`/`f64`)
     - Slot 2: `R8` (integer/pointer) or `XMM2` (`f32`/`f64`)
     - Slot 3: `R9` (integer/pointer) or `XMM3` (`f32`/`f64`)
   - Example: `fn mix(a: i32, b: f64, c: i64, d: f32)` passes `a` in `ECX`, `b` in `XMM1` (not `XMM0`), `c` in `R8`, and `d` in `XMM3` (not `XMM1`).
2. **Stack Parameter Slots (`>= 4`) & 32-Byte Home Space**:
   - Every call frame allocates the mandatory 32-byte shadow space ("home space") for slots `0..3` at `[RSP + 0]`..`[RSP + 24]`.
   - Parameters at positional index `k >= 4` (including `f32` and `f64`) are stored in 8-byte stack slots at `[RSP + 8 * k]` prior to `CALL`. A 32-bit `f32` stack parameter is stored in the low 32 bits of its 8-byte stack slot via `MOVSS [RSP + 8 * k], xmm`.
3. **Variadic `extern "C"` Calls (GPR Mirroring)**:
   - When calling a variadic `extern "C"` function (e.g., `printf`), any `f32` argument is first promoted to `f64` (`CVTSS2SD`), and for any floating-point argument in positional slots `0..3`, its 64-bit IEEE-754 representation MUST be placed in **both** `XMMn` and the corresponding GPR `RCX`/`RDX`/`R8`/`R9` (`MOVQ rcx, xmm0`, etc.) so both XMM-reading and GPR-homing variadic callees observe the value.
4. **Return Value**:
   - Scalar `f32` and `f64` return values are returned in `XMM0` (`[31:0]` for `f32`, `[63:0]` for `f64`).
5. **Volatile vs Non-Volatile `XMM` Registers (`XMM6`–`XMM15` Callee-Saved)**:
   - `XMM0` through `XMM5` are **caller-saved (volatile)** across function calls.
   - `XMM6` through `XMM15` are **callee-saved (non-volatile)** under the Windows x64 ABI. Any Axiom function whose register allocation clobbers any of `XMM6`–`XMM15` MUST save the full 128-bit register (`MOVAPS` / `MOVUPS` to a 16-byte stack slot in `FrameLayout`) in the function prologue and restore it in the epilogue, with corresponding `.seh_savexmm` unwind metadata when SEH unwind tables are emitted.

### AXS-FLT-042 — SSE2 Scalar Arithmetic & Cast Instruction Selection

All scalar `f32`/`f64` operations lower to baseline x86-64 SSE2 instructions (always present on all 64-bit x86 processors) with default MXCSR control flags (Round-to-Nearest-Even `RC = 00`, `FTZ = 0`, `DAZ = 0`, all IEEE-754 exceptions masked):

| Operation | `f32` SSE2 Instruction Sequence | `f64` SSE2 Instruction Sequence |
|---|---|---|
| Register/memory move | `MOVSS` / `MOVAPS` | `MOVSD` / `MOVAPD` |
| Addition (`a + b`) | `ADDSS xmm_dst, xmm_rhs` | `ADDSD xmm_dst, xmm_rhs` |
| Subtraction (`a - b`) | `SUBSS xmm_dst, xmm_rhs` | `SUBSD xmm_dst, xmm_rhs` |
| Multiplication (`a * b`) | `MULSS xmm_dst, xmm_rhs` | `MULSD xmm_dst, xmm_rhs` |
| Division (`a / b`) | `DIVSS xmm_dst, xmm_rhs` | `DIVSD xmm_dst, xmm_rhs` |
| Remainder (`a % b`) | `__axiom_fmodf(a, b)` (`f32`) | `__axiom_fmod(a, b)` (`f64`) |
| Unary negation (`-a`) | `XORPS xmm_dst, [rip + .LC_sign_f32]` (`0x8000_0000u32`) | `XORPD xmm_dst, [rip + .LC_sign_f64]` (`0x8000_0000_0000_0000u64`) |
| Absolute value (`a.abs()`) | `ANDPS xmm_dst, [rip + .LC_abs_f32]` (`0x7FFF_FFFFu32`) | `ANDPD xmm_dst, [rip + .LC_abs_f64]` (`0x7FFF_FFFF_FFFF_FFFFu64`) |
| Square root (`a.sqrt()`) | `SQRTSS xmm_dst, xmm_src` | `SQRTSD xmm_dst, xmm_src` |
| `FloatConvert` (`f32 <-> f64`) | `CVTSS2SD xmm_dst, xmm_src` (`f32 -> f64`) | `CVTSD2SS xmm_dst, xmm_src` (`f64 -> f32`) |
| `to_bits` / `from_bits` | `MOVD eax, xmm_src` / `MOVD xmm_dst, eax` | `MOVQ rax, xmm_src` / `MOVQ xmm_dst, rax` |

### AXS-FLT-043 — SSE2 `UCOMISS` / `UCOMISD` Unordered Comparison Lowering

Because `UCOMISS` and `UCOMISD` set `ZF=1, PF=1, CF=1` when either operand is `NaN`:

1. **`a == b` (`MirBinOp.Eq`)**:
   - A single `SETE al` is **incorrect** because `SETE` tests `ZF == 1`, which is `true` on `NaN` (`ZF=1, PF=1`).
   - Canonical lowering:
     ```text
     UCOMISS/UCOMISD xmm_a, xmm_b
     SETE   al          ; al = (ZF == 1)
     SETNP  cl          ; cl = (PF == 0, i.e., ordered)
     AND    al, cl      ; true iff ZF == 1 && PF == 0
     ```
2. **`a != b` (`MirBinOp.Ne`)**:
   - A single `SETNE al` is **incorrect** because `SETNE` tests `ZF == 0`, which is `false` on `NaN` (`ZF=1, PF=1`), whereas `NaN != x` MUST be `true`.
   - Canonical lowering:
     ```text
     UCOMISS/UCOMISD xmm_a, xmm_b
     SETNE  al          ; al = (ZF == 0)
     SETP   cl          ; cl = (PF == 1, i.e., unordered/NaN)
     OR     al, cl      ; true iff ZF == 0 || PF == 1
     ```
3. **`a > b` (`MirBinOp.Gt`) and `a >= b` (`MirBinOp.Ge`)**:
   - `UCOMISS/UCOMISD xmm_a, xmm_b` followed by `SETA al` (`CF == 0 && ZF == 0`) for `>` or `SETAE al` (`CF == 0`) for `>=`. Since unordered sets `CF = 1, ZF = 1`, `SETA` and `SETAE` automatically yield `0` (`false`) when either operand is `NaN`.
4. **`a < b` (`MirBinOp.Lt`) and `a <= b` (`MirBinOp.Le`)**:
   - `SETB` (`CF == 1`) and `SETBE` (`CF == 1 || ZF == 1`) MUST NOT be used directly on `UCOMISD xmm_a, xmm_b` because unordered `NaN` sets `CF = 1, ZF = 1`.
   - Canonical lowering swaps the operands and uses `SETA` / `SETAE`:
     - `a < b` $\Longleftrightarrow$ `b > a`: `UCOMISS/UCOMISD xmm_b, xmm_a` followed by `SETA al`.
     - `a <= b` $\Longleftrightarrow$ `b >= a`: `UCOMISS/UCOMISD xmm_b, xmm_a` followed by `SETAE al`.

### AXS-FLT-044 — Integer-Float & Saturating Float-Integer Lowering Sequences

1. **Signed Integer `->` Float (`MIR_CAST_INT_TO_FLOAT`)**:
   - `i8`, `i16`, `i32` sign-extend to 32-bit `r32` (`MOVSX`) followed by `CVTSI2SS xmm_dst, r32` or `CVTSI2SD xmm_dst, r32`.
   - `i64`, `isize` convert directly via 64-bit `CVTSI2SS xmm_dst, r64` or `CVTSI2SD xmm_dst, r64`.
   - `i128` lowers via helper `__axiom_i128_to_f32` / `__axiom_i128_to_f64` using round-to-nearest-even.
2. **Unsigned Integer `->` Float (`MIR_CAST_INT_TO_FLOAT`)**:
   - `u8`, `u16` zero-extend to 32-bit `r32` (`MOVZX`) followed by `CVTSI2SS xmm_dst, r32` or `CVTSI2SD xmm_dst, r32`.
   - `u32` zero-extends to 64-bit `r64` (`MOV r32, r32`) followed by 64-bit `CVTSI2SS xmm_dst, r64` or `CVTSI2SD xmm_dst, r64` (exact for `f64`, single-rounding for `f32`).
   - `u64` / `usize` uses the two-path SSE2 sequence to avoid signed `i64` interpretation when bit 63 is set:
     - Fast path (`x >= 0` as signed `i64`, i.e., `TEST r64, r64; JS .high_bit`): `CVTSI2SD xmm_dst, r64`.
     - High-bit path (`bit 63 == 1`): `r_half = (x >> 1) | (x & 1)` (preserving sticky bit for exact round-to-nearest-even), `CVTSI2SD xmm_dst, r_half`, followed by `ADDSD xmm_dst, xmm_dst` (doubling the result).
   - `u128` lowers via helper `__axiom_u128_to_f32` / `__axiom_u128_to_f64` using round-to-nearest-even.
3. **Saturating Float `->` Integer (`MIR_CAST_FLOAT_TO_INT`)**:
   - Raw x86-64 `CVTTSS2SI` / `CVTTSD2SI` returns the hardware sentinel `0x8000_0000` (`i32.MIN`) or `0x8000_0000_0000_0000` (`i64.MIN`) on `NaN`, `+inf`, `-inf`, and out-of-range positive values. Raw `CVTT*2SI` without bounds/NaN checks is therefore **non-conforming**.
   - Every `MIR_CAST_FLOAT_TO_INT` MUST lower to the saturating sequence (`AXS-FLT-022`):
     1. Check unordered (`UCOMISS/UCOMISD xmm_src, xmm_src; JP .is_nan`) -> return `0`.
     2. Check lower bound (`<= T_min_bound`) -> return `T.MIN`.
     3. Check upper bound (`>= T_max_exclusive_bound`, e.g., `2147483648.0f64` for `i32`, `9223372036854775808.0f64` (`2.0^63`) for `i64`, `18446744073709551616.0f64` (`2.0^64`) for `u64`) -> return `T.MAX`.
     4. In-bounds finite value -> execute `CVTTSS2SI` / `CVTTSD2SI` (using two-range split at `2.0^63` for `u64`).

---

## 6. Deterministic Formatting & Parsing (`std.text.fmt.float`, `AXS-FLT-050`..`052`)

### AXS-FLT-050 — Special Floating-Point String Representations

All canonical formatting routines in `std.text.fmt.float` and `Display` / `Debug` implementations for `f32` and `f64` MUST format special IEEE-754 values identically across all platforms without calling C `snprintf`:

| Value | Formatted String | Notes |
|---|---|---|
| Any `NaN` (regardless of sign bit or payload) | `"NaN"` | Always canonical `"NaN"`, never `"-nan"`, `"nan(ind)"`, or `"1.#QNAN"` |
| `+inf` (`f32.INFINITY` / `f64.INFINITY`) | `"inf"` | Lowercase `"inf"` |
| `-inf` (`f32.NEG_INFINITY` / `f64.NEG_INFINITY`) | `"-inf"` | Lowercase `"-inf"` |
| `+0.0` (`bits == 0`) | `"0.0"` (shortest/Debug) or `"0"` / `"0.00..."` (fixed precision) | No leading `'+'` unless sign flag requested |
| `-0.0` (`sign == 1`, exponent == 0, mantissa == 0) | `"-0.0"` (shortest/Debug) or `"-0.00..."` (fixed precision) | Leading `'-'` sign bit of negative zero is preserved |

### AXS-FLT-051 — Shortest Round-Trip Formatting & Fixed/Scientific Modes

`std.text.fmt.float` provides pure-Axiom deterministic formatting functions:

- `pub fn format_f32(val: f32) -> String`
- `pub fn format_f64(val: f64) -> String`
- `pub fn format_f32_fixed(val: f32, precision: usize) -> String`
- `pub fn format_f64_fixed(val: f64, precision: usize) -> String`
- `pub fn format_f32_exp(val: f32, precision: usize) -> String`
- `pub fn format_f64_exp(val: f64, precision: usize) -> String`

Normative guarantees:

1. **Shortest Round-Trip Guarantee (`format_f32`, `format_f64`)**:
   - For every finite `x: f32`, `parse_f32(format_f32(x).as_str()).unwrap().to_bits() == x.to_bits()`.
   - For every finite `x: f64`, `parse_f64(format_f64(x).as_str()).unwrap().to_bits() == x.to_bits()`.
   - Among all decimal strings that round back to `x` under `roundTiesToEven`, `format_f32` / `format_f64` selects the shortest significand (using Ryu / Dragonbox / Grisu-exact interval refinement), breaking ties in favor of the even last digit.
   - Whole-number finite values in decimal notation include `.0` in `Debug` / canonical float mode (e.g., `1.0`, `-0.0`, `42.0`) so floating-point outputs remain visually distinct from integers.
2. **Fixed-Precision Mode (`format_f64_fixed(val, precision)`)**:
   - Rounds `val` to `precision` digits after the decimal point using IEEE-754 `roundTiesToEven` (halfway to even), not round-half-away-from-zero.
   - When `precision == 0`, no decimal point or fractional digits are emitted.
3. **Scientific Notation Mode (`format_f64_exp(val, precision)`)**:
   - Emits `[-]d.dddde±dd` with one non-zero leading decimal digit (or `0` when `val == ±0.0`), `precision` fractional digits, lowercase `'e'`, explicit `'+'` or `'-'` exponent sign, and at least two exponent digits (or minimum necessary digits without leading padding if specified by the format spec).

### AXS-FLT-052 — Exact Decimal-to-Binary Parsing (`parse_f32`, `parse_f64`)

`std.text.fmt.float` provides exact decimal-to-binary parsing functions:

- `pub fn parse_f32(s: Str) -> Result<f32, ParseFloatError>`
- `pub fn parse_f64(s: Str) -> Result<f64, ParseFloatError>`

```axiom
pub enum ParseFloatError {
    Empty,
    InvalidSyntax,
}
```

Normative parsing rules:

1. **Accepted Grammar**:
   - Optional leading sign `'+'` or `'-'`.
   - Case-insensitive special strings `"inf"`, `"infinity"`, and `"nan"` (returning `±INFINITY` or canonical quiet `NaN`; `"-nan"` returns canonical quiet `NaN` with sign bit or canonical `NaN`, and `.is_nan() == true`).
   - Finite decimal strings: `[0-9]+ ('.' [0-9]*)? ([eE] [+-]? [0-9]+)?` or `'.' [0-9]+ ([eE] [+-]? [0-9]+)?` (underscores `_` are **not** accepted by `parse_f32`/`parse_f64` runtime string parsers; underscores are lexical literal syntax only).
   - Leading or trailing whitespace is rejected with `Err(ParseFloatError.InvalidSyntax)` (callers must `.trim()` explicitly if desired).
2. **Exact `roundTiesToEven` Conversion**:
   - Every valid finite decimal string is converted to the single nearest `f32` or `f64` value under IEEE-754 `roundTiesToEven` (using Eisel-Lemire fast path + exact multiprecision fallback for ambiguous halfway cases), achieving $0.5\text{ ULP}$ (correctly rounded) accuracy across the entire decimal exponent range.
   - Magnitudes overflowing `MAX` return `Ok(f32.INFINITY)` / `Ok(f64.INFINITY)` (or `NEG_INFINITY` if negative).
   - Magnitudes underflowing below `MIN_POSITIVE_SUBNORMAL` return `Ok(+0.0)` (or `Ok(-0.0)` when the input has a leading `'-'`).

---

## 7. Standard Mathematical Library (`std.math`, `AXS-FLT-060`..`064`)

### AXS-FLT-060 — Pure-Axiom Deterministic `std.math` Architecture

The `std.math` module (`std/math/mod.ax`, `T461`) MUST be implemented in **100% pure Axiom** using IEEE-754 bit manipulation (`to_bits` / `from_bits`), hardware-lowered `sqrt`, and deterministic polynomial/rational approximations.

- `std.math` MUST NOT link against or call OS-provided `libm` / `msvcrt.dll` / `ucrtbase.dll` transcendental functions (`sin`, `cos`, `exp`, `log`, `pow`, etc.), because system `libm` implementations vary across Windows UCRT versions, Linux glibc/musl versions, and CPU microarchitectures.
- Consequently, every `std.math` function produces **bit-identical outputs across all target hosts and compiler stages** (`INV-FLT-004`).

### AXS-FLT-061 — Mathematical Constants (`std.math` & `f32` / `f64`)

`std.math.f64.consts` (re-exported at `std.math`) and `std.math.f32.consts` define the following IEEE-754 correctly rounded constants:

| Constant | Mathematical Value | `f64` Value & Exact Bit Pattern | `f32` Bit Pattern |
|---|---|---|---|
| `PI` | $\pi$ | `3.14159265358979323846` (`0x4009_21FB_5444_2D18u64`) | `0x4049_0FDBu32` |
| `TAU` | $2\pi$ | `6.28318530717958647692` (`0x4019_21FB_5444_2D18u64`) | `0x40C9_0FDBu32` |
| `FRAC_PI_2` | $\pi / 2$ | `1.57079632679489661923` (`0x3FF9_21FB_5444_2D18u64`) | `0x3FC9_0FDBu32` |
| `FRAC_PI_3` | $\pi / 3$ | `1.04719755119659774615` (`0x3FF0_C152_382D_7366u64`) | `0x3F86_0A92u32` |
| `FRAC_PI_4` | $\pi / 4$ | `0.78539816339744830962` (`0x3FE9_21FB_5444_2D18u64`) | `0x3F49_0FDBu32` |
| `FRAC_PI_6` | $\pi / 6$ | `0.52359877559829887308` (`0x3FE0_C152_382D_7366u64`) | `0x3F06_0A92u32` |
| `FRAC_PI_8` | $\pi / 8$ | `0.39269908169872415481` (`0x3FD9_21FB_5444_2D18u64`) | `0x3EC9_0FDBu32` |
| `FRAC_1_PI` | $1 / \pi$ | `0.31830988618379067154` (`0x3FD4_5F30_6DC9_C883u64`) | `0x3EA2_F983u32` |
| `FRAC_2_PI` | $2 / \pi$ | `0.63661977236758134308` (`0x3FE4_5F30_6DC9_C883u64`) | `0x3F22_F983u32` |
| `FRAC_2_SQRT_PI` | $2 / \sqrt{\pi}$ | `1.12837916709551257390` (`0x3FF2_0DD7_5042_9B6Du64`) | `0x3F90_6EBBu32` |
| `E` | $e$ | `2.71828182845904523536` (`0x4005_BF0A_8B14_5769u64`) | `0x402D_F854u32` |
| `LOG2_E` | $\log_2(e)$ | `1.44269504088896340736` (`0x3FF7_1547_652B_82FEu64`) | `0x3FB8_AA3Bu32` |
| `LOG10_E` | $\log_{10}(e)$ | `0.43429448190325182765` (`0x3FDB_CB7B_1526_E50Eu64`) | `0x3EDE_5BD9u32` |
| `LN_2` | $\ln(2)$ | `0.69314718055994530942` (`0x3FE6_2E42_FEFA_39EFu64`) | `0x3F31_7218u32` |
| `LN_10` | $\ln(10)$ | `2.30258509299404568402` (`0x4002_6BB1_BBB5_5516u64`) | `0x4013_5D8Eu32` |
| `SQRT_2` | $\sqrt{2}$ | `1.41421356237309504880` (`0x3FF6_A09E_667F_3BCDu64`) | `0x3FB5_04F3u32` |
| `FRAC_1_SQRT_2` | $1 / \sqrt{2}$ | `0.70710678118654752440` (`0x3FE6_A09E_667F_3BCDu64`) | `0x3F35_04F3u32` |

### AXS-FLT-062 — Exact ($0.5\text{ ULP}$) Elementary Operations & Bit Decompositions

The following operations MUST be exact ($\le 0.5\text{ ULP}$, correctly rounded according to IEEE-754):

1. **Square Root & Fused Multiply-Add**:
   - `sqrt(x)` — exact IEEE-754 square root (`SQRTSS` / `SQRTSD`); returns `-0.0` for `-0.0`, `+0.0` for `+0.0`, `+inf` for `+inf`, and `NaN` for `x < -0.0` or `NaN`.
   - `fma(a, b, c)` / `mul_add(a, b, c)` — computes $(a \times b) + c$ with a **single** final `roundTiesToEven` rounding step (implemented via hardware `VFMADD213SS`/`SD` when enabled by target profile or Dekker/TwoProduct + TwoSum exact software emulation on baseline SSE2).
2. **Sign, Rounding & Decomposition**:
   - `abs(x)`, `copysign(x, y)`, `signum(x)`
   - `floor(x)`, `ceil(x)`, `trunc(x)`, `round(x)`, `round_ties_even(x)`, `fract(x)`
   - `modf(x) -> (T, T)` — returns `(trunc(x), fract(x))` where both components carry the sign of `x`.
   - `frexp(x) -> (T, i32)` — decomposes finite non-zero `x` into `(m, exp)` where $|m| \in [0.5, 1.0)$ and $x = m \cdot 2^{\text{exp}}$; for `±0.0`, `±inf`, or `NaN`, returns `(x, 0)`.
   - `ldexp(x, exp: i32) -> T` / `scalbn(x, exp: i32) -> T` — computes $x \cdot 2^{\text{exp}}$ exactly (with IEEE-754 overflow to `±inf` and gradual subnormal underflow to `±0.0`).
   - `next_up(x) -> T`, `next_down(x) -> T` — adjacent IEEE-754 floating-point values (`AXS-FLT-015`).
3. **Euclidean Division & Remainder**:
   - `div_euclid(a, b) -> T` — returns integer quotient $q$ such that $a = q \cdot b + r$ with $0.0 \le r < |b|$.
   - `rem_euclid(a, b) -> T` — returns non-negative remainder $r \in [0.0, |b|)$ (returns `NaN` if `b == 0.0` or either input is `NaN`).
4. **Linear Interpolation & Radian/Degree Scaling**:
   - `lerp(a, b, t) -> T` — computes $a + t \cdot (b - a)$ (monotonic, exact at $t = 0.0 \implies a$, and special-cased or two-term blended so $t = 1.0 \implies b$ for finite `a, b`).
   - `to_radians(deg) -> T` (`deg * (PI / 180.0)`), `to_degrees(rad) -> T` (`rad * (180.0 / PI)`).

### AXS-FLT-063 — Transcendental Functions & Maximum ULP Error Bounds

`std.math` provides the following transcendental functions for `f64` and `f32` (with `f32` variants suffixed `_f32` or provided as inherent methods on `f32`/`f64`) with deterministic minimax polynomial approximations and range reduction:

| Category | Functions | Range Reduction / Algorithm | Max Error Bound |
|---|---|---|---|
| Cube root & Hypotenuse | `cbrt(x)`, `hypot(x, y)` | Exponent extraction + Newton-Raphson / Halley refinement in extended precision (`cbrt`); exponent-scaled $\sqrt{x^2 + y^2}$ avoiding intermediate overflow/underflow (`hypot`) | $\le 1.0\text{ ULP}$ |
| Exponential | `exp(x)`, `exp2(x)`, `expm1(x)` | $x = k \ln 2 + r$ with $\|r\| \le \frac{\ln 2}{2}$ (Cody-Waite high/low split of $\ln 2$) + degree-6/11 Remez minimax polynomial | $\le 1.0\text{ ULP}$ |
| Logarithmic | `ln(x)`, `log2(x)`, `log10(x)`, `ln_1p(x)`, `log(x, base)` | $x = 2^k \cdot m$ with $m \in [\frac{\sqrt{2}}{2}, \sqrt{2}]$, $s = \frac{m - 1}{m + 1}$ Padé / minimax odd polynomial in $s^2$ | $\le 1.0\text{ ULP}$ |
| Power | `powf(x, y)`, `powi(x, n: i32)` | `powi`: binary exponentiation; `powf`: high-precision $y \cdot \log_2(|x|)$ split into integer + fractional parts with IEEE-754 parity handling for negative $x$ | $\le 1.5\text{ ULP}$ (`powf`), $\le 1.0\text{ ULP}$ (`powi`) |
| Trigonometric | `sin(x)`, `cos(x)`, `tan(x)`, `sincos(x) -> (T, T)` | Cody-Waite 3-word $\frac{\pi}{2}$ reduction for $\|x\| < 2^{20}$ and Payne-Hanek multi-word $\frac{2}{\pi}$ reduction for large $\|x\|$, mapping to kernel polynomials on $[-\frac{\pi}{4}, \frac{\pi}{4}]$ | $\le 1.0\text{ ULP}$ (`sin`, `cos`), $\le 1.5\text{ ULP}$ (`tan`) |
| Inverse Trigonometric | `asin(x)`, `acos(x)`, `atan(x)`, `atan2(y, x)` | Argument folding ($\|x\| > 0.5 \implies \sqrt{\frac{1 - \|x\|}{2}}$ for `asin`/`acos`; 4-interval octant reduction for `atan`/`atan2`) + Remez rational/polynomial kernel | $\le 1.0\text{ ULP}$ |
| Hyperbolic | `sinh(x)`, `cosh(x)`, `tanh(x)`, `asinh(x)`, `acosh(x)`, `atanh(x)` | `expm1`-based evaluation for small $\|x\|$ to avoid catastrophic cancellation; `ln_1p`-based evaluation for inverse hyperbolics | $\le 1.5\text{ ULP}$ |
| Error Functions | `erf(x)`, `erfc(x)` | Piecewise rational Chebyshev approximations on $[0, 0.84375]$, $[0.84375, 1.25]$, and asymptotic $e^{-x^2}/x$ expansion for large $\|x\|$ | $\le 1.5\text{ ULP}$ |

### AXS-FLT-064 — IEEE-754 Special-Value Table for `std.math`

Every `std.math` function MUST satisfy the following IEEE-754-2019 §9.2 special-value identities without panicking:

| Function | Special Input(s) | Exact Required Output |
|---|---|---|
| `sqrt(x)` | `x == ±0.0` $\implies$ `±0.0`; `x == +inf` $\implies$ `+inf`; `x < 0.0` $\implies$ `NaN` | Preserves `-0.0` |
| `cbrt(x)` | `x == ±0.0` $\implies$ `±0.0`; `x == ±inf` $\implies$ `±inf` | Odd function: `cbrt(-x) == -cbrt(x)` |
| `hypot(x, y)` | Either `±inf` (even if the other is `NaN`) $\implies$ `+inf`; `(±0.0, ±0.0)` $\implies$ `+0.0` | Commutative, non-negative |
| `exp(x)` / `exp2(x)` | `±0.0` $\implies$ `1.0`; `+inf` $\implies$ `+inf`; `-inf` $\implies$ `+0.0` | Monotonic |
| `expm1(x)` | `±0.0` $\implies$ `±0.0`; `+inf` $\implies$ `+inf`; `-inf` $\implies$ `-1.0` | Preserves `-0.0` |
| `ln(x)` / `log2(x)` / `log10(x)` | `1.0` $\implies$ `+0.0`; `±0.0` $\implies$ `-inf`; `x < 0.0` $\implies$ `NaN`; `+inf` $\implies$ `+inf` | Exact at `1.0` |
| `ln_1p(x)` | `±0.0` $\implies$ `±0.0`; `-1.0` $\implies$ `-inf`; `x < -1.0` $\implies$ `NaN`; `+inf` $\implies$ `+inf` | Preserves `-0.0` |
| `powf(x, y)` | `powf(x, ±0.0)` $\implies$ `1.0` (even if `x` is `NaN` or `±inf`); `powf(1.0, y)` $\implies$ `1.0` (even if `y` is `NaN` or `±inf`); `powf(x < 0.0, non-integer y)` $\implies$ `NaN` | IEEE-754 `pow` special rules |
| `sin(x)` / `tan(x)` | `±0.0` $\implies$ `±0.0`; `±inf` $\implies$ `NaN` | Odd around `±0.0` |
| `cos(x)` | `±0.0` $\implies$ `1.0`; `±inf` $\implies$ `NaN` | Even function |
| `asin(x)` | `±0.0` $\implies$ `±0.0`; `\|x\| > 1.0` $\implies$ `NaN` | Range $[-\frac{\pi}{2}, \frac{\pi}{2}]$ |
| `acos(x)` | `1.0` $\implies$ `+0.0`; `\|x\| > 1.0` $\implies$ `NaN` | Range $[0, \pi]$ |
| `atan(x)` | `±0.0` $\implies$ `±0.0`; `±inf` $\implies$ `±FRAC_PI_2` | Range $[-\frac{\pi}{2}, \frac{\pi}{2}]$ |
| `atan2(y, x)` | `(±0.0, +0.0)` $\implies$ `±0.0`; `(±0.0, -0.0)` $\implies$ `±PI`; `(±0.0, x < 0)` $\implies$ `±PI`; `(y != 0, ±0.0)` $\implies$ `copysign(FRAC_PI_2, y)`; `(±inf, +inf)` $\implies$ `±FRAC_PI_4`; `(±inf, -inf)` $\implies$ `±3*FRAC_PI_4` | Full 4-quadrant signed zero awareness |
| `sinh(x)` / `tanh(x)` / `asinh(x)` / `erf(x)` | `±0.0` $\implies$ `±0.0`; `sinh(±inf)` $\implies$ `±inf`; `tanh(±inf)` $\implies$ `±1.0`; `erf(±inf)` $\implies$ `±1.0` | Odd functions preserving `-0.0` |
| `cosh(x)` | `±0.0` $\implies$ `1.0`; `±inf` $\implies$ `+inf` | Even function |

---

## 8. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-FLT-070`..`073`)

### AXS-FLT-070 — Floating-Point & Mixed-Promotion Diagnostic Codes

| Code | Severity | Emit Condition |
|---|---|---|
| `AX_LEX_INVALID_SUFFIX` | `error` | Invalid or mismatched suffix on a numeric literal (`1.5u8`, `1.5foo`), integer literal with a float suffix but no fraction or exponent (`1f32`, note `"write 1.0f32"`), or malformed float exponent without digits (`1.0e` scanned as suffix `e`) (`SPEC-01 AXS-LEX-056, AXS-LEX-058`). |
| `AX_LEX_BAD_DIGIT_SEPARATOR` | `error` | Misplaced `_` in a floating-point literal (`1._5`, `1.5_`, `1.5e_2`) (`SPEC-01 AXS-LEX-051`). |
| `AX_TYPE_LITERAL_OUT_OF_RANGE` | `error` | Floating-point literal magnitude overflows `f32.MAX` ($\ge (2 - 2^{-24}) \cdot 2^{128}$ for `f32`, e.g., `1e40f32`) or `f64.MAX` ($\ge (2 - 2^{-53}) \cdot 2^{1024}$ for `f64`, e.g., `1e309f64`) (`AXS-FLT-003`). |
| `AX_TYPE_MISMATCH` | `error` | Standalone variable binding, assignment, return, or function argument type mismatch without a mixed binary operator or explicit `as` / `From` conversion (e.g., `let x: f64 = n_i32`, `let x: f64 = w_f32`, `let x: f64 = 1`, `let n: i32 = x_f64`, `let w: f32 = x_f64`), standalone same-width signed/unsigned concrete integer mixing (`n_i32 + u_u32` without an enclosing wider signed or float arithmetic context), or floating-point array/slice index (`arr[x_f64]`) (`AXS-FLT-035`). |
| `AX_TYPE_OPERATOR` | `error` | Bitwise, shift, or logical-not operator (`&`, `\|`, `^`, `~`, `<<`, `>>`, `!`) applied to an `f32` or `f64` operand (`x & 1.0`, `x << 2`, `~x`, `!x`) (`AXS-FLT-033`, `spec/diagnostics.md` §10.4). |
| `AX_TYPE_INVALID_CAST` | `error` | Invalid `as` cast involving `f32`/`f64` (e.g., `x as bool`, `b as f64`, `ptr as f64`, `x as Str`, `x as char`) (`SPEC-03 AXS-SEM-060`, `AXS-FLT-022..024`). |
| `AX_PAT_NON_EXHAUSTIVE` | `error` | `match` on `f32` or `f64` missing a wildcard `_` or binding catch-all arm (`AXS-FLT-006`). |
| `AX_NAME_UNRESOLVED` / `AX_TYPE_UNKNOWN` | `error` | Calling an unresolved method name on `f32`/`f64`, or calling a method when a numeric type inference variable cannot be inferred (`spec/diagnostics.md` §10.3–10.4). |
| `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | `error` | Using `f32`, `f64`, or float literals in the frozen Stage-0 bootstrap compiler `axiom0` (`AXS-FLT-001`, `SPEC-03 AXS-SEM-010`). |

### AXS-FLT-071 — Canonical Positive Examples

```axiom
use std.math

pub fn demo_ieee754_and_mixed_promotion(i: i32, k: i16) -> f64 {
    // 1. Concrete integer and unsuffixed literals promote to float peer in binary expressions (AXS-FLT-031..032)
    let x: f64 = 1.5
    let y = x + i * k - 1               // `i * k` promotes i16 -> i32, then IntToFloat -> f64; `1` -> 1.0f64

    // 2. f32 -> f64 widening promotion in binary expression (AXS-FLT-031)
    let a: f32 = 0.5f32
    let z = (a + 0.5) + y               // `0.5` unifies with `f32`, then `(a + 0.5)` widens `f32 -> f64`

    // 3. Saturating FloatToInt cast (AXS-FLT-022)
    let sat_max: u8 = 999.9f64 as u8    // 255u8
    let sat_nan: i32 = f64.NAN as i32   // 0i32
    let sat_neg: u32 = (-42.0f64) as u32 // 0u32

    // 4. Signed zero and NaN behavior (AXS-FLT-012, AXS-FLT-013, AXS-FLT-020, AXS-FLT-021)
    let neg_zero = -0.0f64
    assert(neg_zero == 0.0f64)
    assert((1.0 / neg_zero) == f64.NEG_INFINITY)
    assert(f64.NAN != f64.NAN)
    assert(f64.NAN.total_cmp(1.0) == Ordering.Greater)

    // 5. Deterministic std.math (AXS-FLT-060..064)
    let angle = std.math.FRAC_PI_4
    let h = std.math.hypot(3.0, 4.0)    // 5.0f64
    let c = std.math.cos(angle) * std.math.SQRT_2 // 1.0f64

    z + (sat_max as f64) + (sat_nan as f64) + (sat_neg as f64) + h + c
}
```

### AXS-FLT-072 — Canonical Negative Examples

```axiom
fn rejected_float_and_mixed_cases(x: f64, w: f32, n: i32, u: u32) {
    // ERROR [AX_TYPE_MISMATCH]: standalone variable binding from `i32` to `f64` requires `n as f64` or `f64.from(n)` (AXS-FLT-035)
    let bad1: f64 = n

    // ERROR [AX_TYPE_MISMATCH]: standalone same-width signed `i32` and unsigned `u32` addition has no common integer supertype (AXS-FLT-031, AXS-FLT-035)
    let bad2 = n + u

    // ERROR [AX_TYPE_MISMATCH]: implicit narrowing from `f64` to `f32` or `f64` to `i32` is forbidden (AXS-FLT-035)
    let bad3: f32 = x
    let bad3_int: i32 = x + w

    // ERROR [AX_TYPE_LITERAL_OUT_OF_RANGE]: float literal `1e40f32` exceeds `f32.MAX` (AXS-FLT-003)
    let bad4: f32 = 1e40f32

    // ERROR [AX_TYPE_OPERATOR]: bitwise operator `&` is not defined for `f64` (AXS-FLT-033)
    let bad5 = x & 1.0

    // ERROR [AX_TYPE_INVALID_CAST]: cannot cast `f64` to `bool` or `Str` (AXS-SEM-060)
    let bad6 = x as bool
}
```

### AXS-FLT-073 — Requirement & Task Traceability Matrix

| Requirement / Epic ID | Title / Scope | Normative Clauses in `SPEC-41` | Downstream Implementation Tasks |
|---|---|---|---|
| `REQ-OWNER-007` | Complex Mixed-Type Expression Matrix (12 primitives, Patterns A/B/C/D, promotion lattice, explicit MIR casts) | `AXS-FLT-030`..`AXS-FLT-037` | `T457` (typechecker promotion lattice & explicit MIR casts), `T458` (oracle evaluation), `T459` (SSE2 lowering), `T462` (E12.2 verification matrix) |
| `REQ-SIMD-108` | Strict IEEE-754 floating-point semantics by default (no implicit `-ffast-math` or reassociation) | `AXS-FLT-010`, `AXS-FLT-011`, `AXS-FLT-012`, `AXS-FLT-013`, `AXS-FLT-014` | `T458`, `T459`, `T462` |
| `REQ-SIMD-109` | Explicit opt-in required for algebraic floating-point relaxation (`@fast_math` / `std.simd` reductions) | `AXS-FLT-014` | `T458`, `T459` |
| `REQ-SIMD-110` | Deterministic `NaN`, signed zero (`-0.0`), and infinity handling across scalar and SIMD lanes | `AXS-FLT-001`..`003`, `AXS-FLT-011`..`016`, `AXS-FLT-020`..`021` | `T458`, `T459`, `T461`, `T462` |
| `REQ-SIMD-163` | Deterministic floating-point evaluation order and absence of silent FMA contraction | `AXS-FLT-010`, `AXS-FLT-014`, `AXS-FLT-062` | `T458`, `T459`, `T461`, `T462` |
| `REQ-SIMD-186` | IEEE-754 quiet `NaN` propagation and canonical `NaN` bit representation | `AXS-FLT-002`, `AXS-FLT-003`, `AXS-FLT-012`, `AXS-FLT-020` | `T458`, `T459`, `T460`, `T461`, `T462` |
| `REQ-SIMD-187` | IEEE-754 signed zero (`+0.0` / `-0.0`) preservation across arithmetic, casts, and math functions | `AXS-FLT-013`, `AXS-FLT-015`, `AXS-FLT-016`, `AXS-FLT-040`, `AXS-FLT-050`, `AXS-FLT-064` | `T458`, `T459`, `T460`, `T461`, `T462` |
| `REQ-SIMD-188` | Saturating float-to-int `as` casts and deterministic int-to-float rounding | `AXS-FLT-022`, `AXS-FLT-023`, `AXS-FLT-024`, `AXS-FLT-044` | `T457`, `T458`, `T459`, `T462` |
| `REQ-SIMD-189` | Deterministic pure-Axiom formatting, parsing, and `std.math` library | `AXS-FLT-050`..`052`, `AXS-FLT-060`..`064` | `T460` (`std.text.fmt.float`), `T461` (`std.math`), `T462` (E12.2 conformance) |

## Sources

- `docs/base/tasks/0327 - BOOTSTRAP-068 — Axiom Numeric Model, Integer Semantics, Floating-Point & SIMD.md` (`§84.2, §84.4–84.9`)
- `docs/base/tasks/0331 - BOOTSTRAP-072 — Axiom Numeric Model, SIMD & Floating-Point Semantics.md` (`§17–30, §59–70, §100, ANUM-41..57, 81..100`)
- `docs/base/tasks/0334 - BOOTSTRAP-075 — Axiom Numeric Model, Integer, Floating-Point, SIMD & Math.md` (`§91.1–12`)
- `docs/base/tasks/0338 - BOOTSTRAP-079 — Axiom Numeric Model, Math, Floating Point, Precision & Numeric Semantics.md` (`§15–36, §93–100, ANUM-37..65, 80..100`)
- `docs/base/tasks/0345 - BOOTSTRAP-086 — Axiom Numeric Type, Floating-Point, Precision & Extended Arithmetic Model.md` (`§17–36, §98–100, ANUM-22, 35..62, 78..100`)
- `docs/base/tasks/0427 - BOOTSTRAP-168 — Numeric System, SIMD Types, Math Semantics & Fast Numerical Computing.md` (`§15–26`)
- `docs/base/tasks/0431 - BOOTSTRAP-172 — Conversions, Casting, Coercion & Type-Safe Interoperability.md` (`§172.1–14`)
- `docs/base/tasks/0469 - BOOTSTRAP-210 — Scientific Computing, Numerical Methods, Complex Numbers & High-Performance Math.md` (`§210.1–210.80, AMATH-20..70`)
- `docs/base/specs/0157 - AXIOM TYPE SYSTEM KERNEL v0.1.md`
- `docs/base/specs/0162 - AXIOM LIR v0.1.md`
- `docs/base/specs/0175 - XXXVIII — TYPE-001 Type Engine + Typed HIR.md`
- `docs/base/specs/0179 - XLV — LIR-001 Axiom Low-Level IR v0.1.md`
- `docs/base/specs/0181 - XLVII-B — X86-001 Revision Windows x86-64 PE64.md`
- `docs/base/specs/0245 - COMPILER-003 — TYPE SYSTEM.md`
- `spec/requirements/OWNER.md` (`REQ-OWNER-007`)
- `spec/requirements/CATALOG.md` (`REQ-SIMD-108`..`110`, `REQ-SIMD-163`, `REQ-SIMD-186`..`189`)
- `spec/SPEC-01-lexical.md` (`AXS-LEX-050`..`058`)
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-010`, `AXS-SEM-022`, `AXS-SEM-035`, `AXS-SEM-060`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-010`, `AXS-EXT-020`, `AXS-EXT-024`, `AXS-EXT-034`..`035`, `AXS-EXT-042`, `AXS-EXT-050`, `AXS-EXT-052`)
- `spec/SPEC-40-integers.md` (`AXS-INT-001`..`054`)
