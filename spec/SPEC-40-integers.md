# SPEC-40 — Canonical Integer Model, 128-Bit Arithmetic & Conversions

Status: draft (T450, 2026-11-03)
Owner: axiom-architect
Consolidates: `tasks/0327 §84.1, §84.3, §84.10–11, §84.14–16`; `tasks/0334 §91.1–12`; `tasks/0341 §98.1–12`; `tasks/0431 §172.1–14`; `specs/0157`; `specs/0175`; `specs/0245`.
Covers: `REQ-OWNER-007`, `REQ-SIMD-085`, `REQ-SIMD-101`, `REQ-SIMD-102`, `REQ-SIMD-103`, `REQ-SIMD-104`, `REQ-SIMD-105`, `REQ-SIMD-106`, `REQ-SIMD-156`, `REQ-SIMD-086`, `REQ-SIMD-100`, `REQ-SIMD-118`, `REQ-SIMD-141`, `REQ-SIMD-142`, `REQ-SIMD-143`, `REQ-SIMD-144`, `REQ-SIMD-211`.
Consumers: `compiler/lexer/`, `compiler/ast/`, `compiler/hir/`, `compiler/types/types.ax`, `compiler/types/layout.ax`, `compiler/types/typeck.ax`, `compiler/mir/mir.ax`, `compiler/mir/builder.ax`, `compiler/mir/interp.ax`, `compiler/verify/verifier.ax`, `compiler/lir/lir.ax`, `compiler/lir/lower.ax`, `compiler/abi/win64.ax`, `compiler/backend/x64/`, `std/core/num.ax`, `std/core/convert.ax`, `std/text/fmt/int.ax`.

## Tóm tắt

Tài liệu `SPEC-40` quy định mô hình số nguyên chuẩn tắc (canonical integer model) hoàn chỉnh của ngôn ngữ Axiom cho phân hệ `E12.1` (Phase `P12`), mở rộng nền tảng `VS0` trong `SPEC-03` lên toàn bộ 12 kiểu số nguyên vô hướng (`i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize`). Đặc tả này định nghĩa biểu diễn bù hai 16 byte của `i128`/`u128`, quy ước hạ cấp cặp thanh ghi 64-bit `(lo, hi)` ở tầng LIR và hợp đồng ABI Windows x64 (`T453`), cùng 5 họ phép toán số học tường minh: mặc định kiểm tra tràn (`+`, `-`, `*`, `/`, `%`, `-`, `<<`, `>>`), `wrapping_*`, `saturating_*` (hạ cấp trực tiếp xuống `MirBinOp.SatAdd`/`SatSub`/`SatMul`), `checked_*` trả về `Option<Self>`, và `overflowing_*` trả về `(Self, bool)`. Tài liệu cũng quy định bộ thao tác bit và chuyển đổi thứ tự byte (`to_le_bytes`, `from_be_bytes`, `swap_bytes`, `reverse_bits`, `leading_zeros`, v.v.), phân loại 4 lớp chuyển đổi kiểu (`COERCION`, `CAST`, `TRY_CAST`, `BITCAST`), và dàn thăng cấp số nguyên đa độ rộng tất định (`REQ-OWNER-007` integer sub-lattice) hạ cấp thành các lệnh `MIR_RVALUE_CAST` (`IntToInt`) tường minh trước khi qua bộ kiểm chứng MIR.

---

## 1. Complete Scalar Integer Model & 128-Bit Representation

### AXS-INT-001 — Twelve Fundamental Scalar Integer Types (`ANUM-20`, `REQ-SIMD-085`)

Scalar integer types are fundamental first-class value types in Axiom (`ANUM-20`), not single-lane SIMD degenerates or library wrapper structs. The complete scalar integer universe comprises twelve primitive types partitioned into six signed two's-complement types and six unsigned binary integer types:

| Type | Signedness | Bit width $N$ | Size (bytes) | Align (bytes) | Minimum value (`Self.MIN`) | Maximum value (`Self.MAX`) | `TypeKind` (`SPEC-04`) |
|---|---|---|---|---|---|---|---|
| `i8` | signed | $8$ | $1$ | $1$ | $-128$ ($-2^7$) | $127$ ($2^7 - 1$) | `Int(I8)` (`TY_I8 = 2`) |
| `i16` | signed | $16$ | $2$ | $2$ | $-32\,768$ ($-2^{15}$) | $32\,767$ ($2^{15} - 1$) | `Int(I16)` (`TY_I16 = 3`) |
| `i32` | signed | $32$ | $4$ | $4$ | $-2\,147\,483\,648$ ($-2^{31}$) | $2\,147\,483\,647$ ($2^{31} - 1$) | `Int(I32)` (`TY_I32 = 4`) |
| `i64` | signed | $64$ | $8$ | $8$ | $-9\,223\,372\,036\,854\,775\,808$ ($-2^{63}$) | $9\,223\,372\,036\,854\,775\,807$ ($2^{63} - 1$) | `Int(I64)` (`TY_I64 = 5`) |
| `i128` | signed | $128$ | $16$ | $16$ | $-170\,141\,183\,460\,469\,231\,731\,687\,303\,715\,884\,105\,728$ ($-2^{127}$) | $170\,141\,183\,460\,469\,231\,687\,303\,715\,884\,105\,727$ ($2^{127} - 1$) | `Int128(true)` (`TY_I128 = 14`) |
| `isize` | signed | $64$ (Win64) | $8$ | $8$ | $-2^{63}$ | $2^{63} - 1$ | `Int(Isize)` (`TY_ISIZE = 6`) |
| `u8` | unsigned | $8$ | $1$ | $1$ | $0$ | $255$ ($2^8 - 1$) | `Int(U8)` (`TY_U8 = 7`) |
| `u16` | unsigned | $16$ | $2$ | $2$ | $0$ | $65\,535$ ($2^{16} - 1$) | `Int(U16)` (`TY_U16 = 8`) |
| `u32` | unsigned | $32$ | $4$ | $4$ | $0$ | $4\,294\,967\,295$ ($2^{32} - 1$) | `Int(U32)` (`TY_U32 = 9`) |
| `u64` | unsigned | $64$ | $8$ | $8$ | $0$ | $18\,446\,744\,073\,709\,551\,615$ ($2^{64} - 1$) | `Int(U64)` (`TY_U64 = 10`) |
| `u128` | unsigned | $128$ | $16$ | $16$ | $0$ | $340\,282\,366\,920\,938\,463\,463\,374\,607\,431\,768\,211\,455$ ($2^{128} - 1$) | `Int128(false)` (`TY_U128 = 15`) |
| `usize` | unsigned | $64$ (Win64) | $8$ | $8$ | $0$ | $2^{64} - 1$ | `Int(Usize)` (`TY_USIZE = 11`) |

`isize` and `usize` have target pointer width ($64$ bits on `x86_64-pc-windows-msvc`), remain distinct nominal primitive types from `i64` and `u64` at API boundaries, and participate in the integer promotion sub-lattice defined in `§6`.

### AXS-INT-002 — Two's-Complement 128-Bit Representation & Memory Layout

1. Every signed integer type `iN` ($N \in \{8, 16, 32, 64, 128\}$ and `isize`) uses exact $N$-bit two's-complement representation with no padding bits, no trap representations, and no negative zero.
2. Every unsigned integer type `uN` ($N \in \{8, 16, 32, 64, 128\}$ and `usize`) uses exact $N$-bit pure binary positional representation in $[0, 2^N - 1]$ with no padding bits or trap representations.
3. On `x86_64-pc-windows-msvc` (little-endian), `i128` and `u128` occupy 16 contiguous bytes with `size_of == 16` (`SIZE_16 = 16`) and `align_of == 16` (`ALIGN_16 = 16` in `compiler/types/layout.ax`).
4. In memory at byte address $p$ (`p % 16 == 0`), a 128-bit integer consists of two adjacent little-endian 64-bit limbs:
   - `lo: u64` stored at byte offset `0..8` ($p + 0$), holding bits $0..63$.
   - `hi: u64` stored at byte offset `8..16` ($p + 8$), holding bits $64..127$.
5. The mathematical value of a `u128` with limb pair `(lo, hi)` is:
   $$u = \text{lo} + \text{hi} \cdot 2^{64} \in [0, 2^{128} - 1]$$
   The mathematical value of an `i128` with limb pair `(lo, hi)` is:
   $$s = \begin{cases} u & \text{if } \text{hi} < 2^{63} \text{ (bit 63 of } \text{hi} = 0\text{)} \\ u - 2^{128} & \text{if } \text{hi} \ge 2^{63} \text{ (bit 63 of } \text{hi} = 1\text{)} \end{cases}$$

### AXS-INT-003 — Associated Constants (`MIN`, `MAX`, `BITS`)

Every primitive integer type `T` in `{i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize}` exposes three compile-time associated constants accessed via dot syntax (`T.MIN`, `T.MAX`, `T.BITS`):

- `T.MIN: T` — the minimum representable value of `T` ($0$ for unsigned types; $-2^{N-1}$ for signed types).
- `T.MAX: T` — the maximum representable value of `T` ($2^N - 1$ for unsigned types; $2^{N-1} - 1$ for signed types).
- `T.BITS: u32` — the bit width $N$ of `T` as a `u32` constant (`8u32`, `16u32`, `32u32`, `64u32`, or `128u32`; `64u32` for `isize` and `usize` on 64-bit targets).

For 128-bit types specifically:
- `u128.MIN` has limb pair `(lo = 0u64, hi = 0u64)` ($0$).
- `u128.MAX` has limb pair `(lo = 0xFFFF_FFFF_FFFF_FFFFu64, hi = 0xFFFF_FFFF_FFFF_FFFFu64)` ($2^{128} - 1$).
- `i128.MIN` has limb pair `(lo = 0u64, hi = 0x8000_0000_0000_0000u64)` ($-2^{127}$).
- `i128.MAX` has limb pair `(lo = 0xFFFF_FFFF_FFFF_FFFFu64, hi = 0x7FFF_FFFF_FFFF_FFFFu64)` ($2^{127} - 1$).
- `i128.BITS == 128u32` and `u128.BITS == 128u32`.

### AXS-INT-004 — 128-Bit Integer Literals, Suffixes & Range Diagnostics

1. **Lexical suffixes (`SPEC-01 AXS-LEX-020`)**: Integer literals in decimal, hexadecimal (`0x`/`0X`), octal (`0o`/`0O`), or binary (`0b`/`0B`) base may carry any of the twelve integer type suffixes: `i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize`.
2. **128-bit magnitude parsing (`T451`)**: In `axiomc`, the lexer and AST/HIR literal parser accumulate integer literal magnitudes in full 128-bit unsigned precision `(lo: u64, hi: u64)` via base multiplication (`base` $\in \{2, 8, 10, 16\}$) and limb addition with carry.
   - `AX_LEX_INT_OVERFLOW` (`1004`) is emitted if and only if the raw unsigned magnitude exceeds $2^{128} - 1$ (`u128.MAX = 340282366920938463463374607431768211455`).
   - Note: The frozen bootstrap compiler (`axiom0`) remains bounded at 64-bit literal magnitudes (`SPEC-01 AXS-LEX-020`); full 128-bit literal parsing applies to `axiomc` (`T451`).
3. **Type-directed literal bounds & unary negation folding (`SPEC-03 AXS-SEM-021`)**:
   - Once the target integer type `T` of a literal is resolved (either from an explicit suffix or via `IntVar` type inference / fallback to `i32`), `typeck` verifies that the literal value fits in `[T.MIN, T.MAX]`. If it does not, `typeck` emits `AX_TYPE_LITERAL_OUT_OF_RANGE` (`2017`).
   - Unary negation `-lit` applied directly to an unsuffixed or signed-suffixed integer literal is folded prior to range checking so that minimum two's-complement bounds (`-128i8`, `-32768i16`, `-2147483648i32`, `-9223372036854775808i64`, `-170141183460469231731687303715884105728i128`) are valid in both runtime and `const` contexts, whereas positive `170141183460469231731687303715884105728i128` without unary `-` is rejected with `AX_TYPE_LITERAL_OUT_OF_RANGE`.
   - Unsuffixed integer literals whose magnitude exceeds `i32.MAX` ($2^{31} - 1$) cannot default to `i32` without a contextual wider integer type (`i64`, `u64`, `i128`, `u128`, `isize`, `usize`); if unconstrained, `IntVar` defaults to `i32` and `typeck` emits `AX_TYPE_LITERAL_OUT_OF_RANGE`.

### AXS-INT-005 — `ConstValue.Int128` & MIR Constant Representation (`SPEC-04 AXS-EXT-024`)

In `compiler/mir/mir.ax` and the compile-time evaluator (`compiler/mir/interp.ax`), 128-bit integer constants are represented by `ConstValue.Int128 { signed: bool, lo: u64, hi: u64 }` (`MIR_CONST_INT128`).
- Every compile-time constant expression of type `i128` or `u128` is evaluated with exact 128-bit semantics identical to runtime execution (`INV-SEM-002`).
- Compile-time overflow in default checked operators on `i128`/`u128` emits `AX_CONST_OVERFLOW` (`3103`), compile-time division or remainder by zero emits `AX_CONST_DIV_ZERO` (`3102`), and compile-time out-of-range shift emits `AX_CONST_SHIFT_RANGE` (`3104`).

### AXS-INT-006 — Built-in Trait Implementations for Integer Types

All twelve scalar integer types (`i8..i128`, `u8..u128`, `isize`, `usize`) automatically implement the following built-in lang-item and core traits:

1. `Copy` and `Clone` (`x.clone() == x` by bitwise value copy).
2. `PartialEq` and `Eq` (structural value equality: for `i128`/`u128`, `a == b` holds iff `a.lo == b.lo && a.hi == b.hi`).
3. `PartialOrd` and `Ord` (total mathematical order: for `u128`, lexicographic unsigned comparison of `(hi, lo)`; for `i128`, signed comparison of `hi as i64` first, then unsigned comparison of `lo` when `a.hi == b.hi`).
4. `Hash` (deterministic feeding of little-endian bytes `to_le_bytes()` into the hasher).
5. `Send` and `Share` (`SPEC-30 AXS-CON-010`: all primitive integer types are thread-safe value types with no interior mutability).
6. `Default` (`0` of type `Self`, limb pair `(0, 0)` for `i128`/`u128`).

---

## 2. LIR Register-Pair Lowering, Windows x64 ABI & x86-64 Codegen Contract

### AXS-INT-010 — LIR Register-Pair Representation (`SPEC-04 AXS-EXT-050`, `T453`)

Because `x86_64` general-purpose registers (`Gpr`) are 64 bits wide, 128-bit scalar integers (`i128` and `u128`) are lowered in `compiler/lir/lower.ax` from single MIR locals (`MirType` with `TY_I128` / `TY_U128`) to an explicit pair of 64-bit virtual/physical general-purpose registers `(lo: Gpr, hi: Gpr)`:

- `lo` holds bits `0..63` (`u64`), and `hi` holds bits `64..127` (`u64` for unsigned operations; sign bit in bit 63 of `hi` for signed `i128` operations).
- Stack spills and reloads of a 128-bit value allocate a single 16-byte-aligned stack slot (`size = 16, align = 16`) and issue two 64-bit `MOV` instructions at `[slot + 0]` (`lo`) and `[slot + 8]` (`hi`).
- All register-pair splitting is confined to LIR lowering and x86-64 backend emission (`compiler/lir/`, `compiler/abi/win64.ax`, `compiler/backend/x64/`). MIR locals, MIR rvalues, and MIR verifier checks treat `i128` and `u128` as atomic scalar types.

### AXS-INT-011 — Windows x64 Calling Convention Contract for `i128` / `u128` (`T453`)

On `x86_64-pc-windows-msvc` (`CallConv = Win64`), values of size 16 bytes are not passed in a pair of GPR argument registers. `compiler/abi/win64.ax` enforces the following deterministic ABI classification for `i128` and `u128`:

1. **Parameters (`ABI_LOC_INDIRECT`)**: Any function parameter of type `i128` or `u128` (size 16 bytes, alignment 16 bytes) is passed by reference: the caller copies the 16-byte value (`lo` at `+0`, `hi` at `+8`) into a 16-byte-aligned temporary slot in the caller frame and passes the 64-bit address of that temporary in the corresponding parameter slot (`RCX`, `RDX`, `R8`, `R9`, or stack shadow/overflow slot).
2. **Return values**:
   - In internal Axiom functions and lowered LIR register-pair return paths where the backend returns `(lo, hi)` in GPRs, `RAX` carries `lo` (bits `0..63`) and `RDX` carries `hi` (bits `64..127`), or when classified via hidden return pointer (`sret` / indirect 16-byte return slot in `win64.ax`), the caller passes a hidden pointer in `RCX` to a 16-byte-aligned buffer where the callee writes `lo` at `[rcx + 0]` and `hi` at `[rcx + 8]` and returns that address in `RAX`.
   - `compiler/abi/win64.ax` and `compiler/lir/lower.ax` must use a single self-consistent convention across all caller/callee lowers and `extern "C"` boundaries, verified by `tests/run/numeric/i128_abi_call.ax`.
3. **Struct aggregates containing `i128` / `u128`**: Any `struct` or tuple containing an `i128` or `u128` field inherits alignment $\ge 16$ and size $> 8$, and is therefore classified as `ABI_LOC_INDIRECT` for both arguments and sret return under standard Win64 aggregate rules.

### AXS-INT-012 — x86-64 Instruction Selection for 128-Bit Operations (`T453`)

The x86-64 backend (`compiler/backend/x64/`) lowers 128-bit register-pair `(lo, hi)` operations to the following canonical instruction sequences:

| Operation | x86-64 Instruction Sequence (`(a_lo, a_hi)` op `(b_lo, b_hi)` $\to$ `(r_lo, r_hi)`) | Overflow Flag / Panic Condition |
|---|---|---|
| Addition (`+`, `wrapping_add`, `overflowing_add`, `checked_add`) | `mov r_lo, a_lo; add r_lo, b_lo; mov r_hi, a_hi; adc r_hi, b_hi` | `u128`: `CF == 1` after `adc`; `i128`: `OF == 1` after `adc`. |
| Subtraction (`-`, `wrapping_sub`, `overflowing_sub`, `checked_sub`) | `mov r_lo, a_lo; sub r_lo, b_lo; mov r_hi, a_hi; sbb r_hi, b_hi` | `u128`: `CF == 1` after `sbb`; `i128`: `OF == 1` after `sbb`. |
| Unary negation (`-x`, `wrapping_neg`, `overflowing_neg`) | `xor r_lo, r_lo; xor r_hi, r_hi; sub r_lo, a_lo; sbb r_hi, a_hi` | `i128`: overflows iff `a_lo == 0 && a_hi == 0x8000_0000_0000_0000` (`OF == 1`). |
| Wrapping multiplication (`wrapping_mul`) | `mov rax, a_lo; mul b_lo` ($\to$ `rdx:rax`); `mov r_lo, rax; mov r_hi, rdx; imul t1, a_lo, b_hi; imul t2, a_hi, b_lo; add r_hi, t1; add r_hi, t2` | None (low 128 bits retained modulo $2^{128}$). |
| Checked / overflowing multiplication (`*`, `checked_mul`, `overflowing_mul`) | Full 256-bit or high-limb check: for `u128`, overflow iff `a_hi != 0 && b_hi != 0`, or `a_lo * b_hi` overflows 64 bits, or `a_hi * b_lo` overflows 64 bits, or adding cross products into `rdx` produces carry (`CF == 1`); for `i128`, signed 128$\times$128$\to$256 check verifying upper 128 bits equal sign-extension of bit 127 (`sar r_hi, 63`). | Panics / sets overflow flag when product $\notin [\text{MIN}, \text{MAX}]$. |
| Division & remainder (`/`, `%`, `wrapping_div`, `wrapping_rem`, `checked_div`, `checked_rem`, `overflowing_div`, `overflowing_rem`) | Software helper / runtime routine `udiv128(a_lo, a_hi, b_lo, b_hi) -> (q_lo, q_hi, r_lo, r_hi)` (fast path via 64-bit `div` when `a_hi == 0 && b_hi == 0`, binary long division / Knuth D when `b_hi != 0` or `a_hi != 0`); `sdiv128` takes absolute values via two's-complement negation, runs `udiv128`, and applies quotient sign $s_a \oplus s_b$ and dividend remainder sign $s_a$. | Panics on `b_lo == 0 && b_hi == 0` (`division by zero`), and for `i128` `/` or `%` on `a == i128.MIN && b == -1` (`arithmetic overflow`). |
| Left shift (`<<`, `wrapping_shl`) by $n = c \bmod 128$ | If $n == 0$: `(a_lo, a_hi)`; if $0 < n < 64$: `mov r_hi, a_hi; shld r_hi, a_lo, cl; mov r_lo, a_lo; shl r_lo, cl`; if $64 \le n < 128$: `mov r_hi, a_lo; shl r_hi, (cl - 64); xor r_lo, r_lo`. Branchless select via `test cl, 64` + `cmovnz`. | Default `<<` checks `shift_amt < 0 \|\| shift_amt >= 128` before masking (`shift amount out of range`). |
| Logical right shift (`u128 >>`, `u128.wrapping_shr`) by $n = c \bmod 128$ | If $0 < n < 64$: `mov r_lo, a_lo; shrd r_lo, a_hi, cl; mov r_hi, a_hi; shr r_hi, cl`; if $64 \le n < 128$: `mov r_lo, a_hi; shr r_lo, (cl - 64); xor r_hi, r_hi`. | Default `>>` checks `shift_amt < 0 \|\| shift_amt >= 128`. |
| Arithmetic right shift (`i128 >>`, `i128.wrapping_shr`) by $n = c \bmod 128$ | If $0 < n < 64$: `mov r_lo, a_lo; shrd r_lo, a_hi, cl; mov r_hi, a_hi; sar r_hi, cl`; if $64 \le n < 128$: `mov r_lo, a_hi; sar r_lo, (cl - 64); mov r_hi, a_hi; sar r_hi, 63`. | Default `>>` checks `shift_amt < 0 \|\| shift_amt >= 128`. |
| Rotates (`rotate_left`, `rotate_right`) | Double-precision `shld` / `shrd` across `(lo, hi)` with `test cl, 64` limb swap when bit 6 of shift count is 1. | Total for all `u32` counts (masked by `n & 127`). |
| Byte swap (`swap_bytes`) | `mov r_lo, a_hi; bswap r_lo; mov r_hi, a_lo; bswap r_hi` (swaps limbs and `bswap`s each 64-bit limb). | Infallible. |
| Bit counting (`leading_zeros`, `trailing_zeros`, `count_ones`) | `leading_zeros`: if `a_hi != 0` then `lzcnt(a_hi)` else `64 + lzcnt(a_lo)`; `trailing_zeros`: if `a_lo != 0` then `tzcnt(a_lo)` else `64 + tzcnt(a_hi)`; `count_ones`: `popcnt(a_lo) + popcnt(a_hi)`. | Infallible; returns `u32` in `0..=128`. |

### AXS-INT-013 — SIMD Lane Overflow Coherence (`ANUM-35`, `ANUM-36`, `REQ-SIMD-101`)

Vectorizing scalar integer loops into SIMD operations (`SPEC-42`, `E12.3`) or using integer SIMD vector types (`i32x4`, `u64x2`, etc.) **must never** silently alter integer overflow semantics (`ANUM-36`, `REQ-SIMD-101`):
- Scalar `+`, `-`, `*`, `/`, `%`, `-`, `<<`, `>>` remain checked in all builds (`AXS-SEM-030`). Auto-vectorization of checked scalar loops is legal only when the optimizer proves no lane can overflow or preserves exact trap-on-overflow semantics.
- SIMD lane-wise wrapping, saturating, and widening operations require explicit SIMD APIs or explicit scalar `wrapping_*` / `saturating_*` forms (`ANUM-35..38`).

---

## 3. Complete Integer Arithmetic Families

### AXS-INT-020 — Taxonomy of Five Integer Arithmetic Families (`ANUM-35..39`, `REQ-SIMD-101..104`)

Every primitive integer type `T` in `{i8, i16, i32, i64, i128, isize, u8, u16, u32, u64, u128, usize}` provides five orthogonal arithmetic families so that overflow behavior is always unambiguous in source code and IR:

1. **Default Checked Operators (`+`, `-`, `*`, `/`, `%`, unary `-`, `<<`, `>>`)**: Trap with a deterministic panic on overflow, division/remainder by zero, or shift count out of `[0, T.BITS - 1]` in **every** build profile (`debug`, `release`, `verify`) per `SPEC-03 AXS-SEM-030..034` and `INV-SEM-001`.
2. **Wrapping Family (`wrapping_*`, `ANUM-38`, `REQ-SIMD-103`)**: Explicit modular two's-complement arithmetic modulo $2^N$, never panicking on addition, subtraction, multiplication, negation, or shift count.
3. **Saturating Family (`saturating_*`, `ANUM-37`, `REQ-SIMD-102`)**: Explicit clamping arithmetic where mathematical results $< \text{T.MIN}$ clamp to `T.MIN` and results $> \text{T.MAX}$ clamp to `T.MAX`.
4. **Checked Family (`checked_*`, `ANUM-39`, `REQ-SIMD-104`)**: Explicit fallible arithmetic returning `Option<Self>` (`Option.Some(result)` when representable, `Option.None` on overflow, division by zero, or shift count $\ge \text{T.BITS}$).
5. **Overflowing Family (`overflowing_*`)**: Explicit two-output arithmetic returning `(Self, bool)` where `.0` is the wrapped modular result and `.1` is `true` iff mathematical overflow occurred.

### AXS-INT-021 — Default Checked Operators Across All Twelve Widths

For all twelve integer types `T` (including `i128` and `u128`):
- `a + b`, `a - b`, `a * b`: evaluate exact mathematical sum, difference, or product; if the result is outside `[T.MIN, T.MAX]`, panic with `"arithmetic overflow"`.
- `a / b`, `a % b`:
  - If `b == 0`, panic with `"division by zero"` (checked before overflow).
  - For signed `T`, if `a == T.MIN && b == -1`, panic with `"arithmetic overflow"` (both `T.MIN / -1` and `T.MIN % -1` trap per `SPEC-03 AXS-SEM-032`).
  - Integer division truncates toward zero ($q = \text{trunc}(a / b)$), and remainder satisfies $(a / b) \cdot b + (a \% b) == a$ with $\text{sgn}(a \% b) \in \{0, \text{sgn}(a)\}$.
- Unary `-a`:
  - Only valid on signed integer types (`i8`, `i16`, `i32`, `i64`, `i128`, `isize`). Applying unary `-` to an unsigned integer type emits `AX_TYPE_UNARY_OP` (`2012`).
  - If `a == T.MIN`, panics with `"arithmetic overflow"`.
- `a << b`, `a >> b`:
  - If `b < 0` (when `b` is signed) or `b >= T.BITS`, panics with `"shift amount out of range"`.
  - For `a >> b`, unsigned `T` performs logical right shift (zero-fill), and signed `T` performs arithmetic right shift (sign-fill).

### AXS-INT-022 — Wrapping Arithmetic Family (`ANUM-38`, `REQ-SIMD-103`)

Every integer type `T` of bit width $N = \text{T.BITS}$ provides the following associated methods in `std.core.num`:

| Method Signature | Mathematical Semantics | Corner Cases |
|---|---|---|
| `fn wrapping_add(self, rhs: Self) -> Self` | $(self + rhs) \bmod 2^N$ interpreted as `Self`. | Infallible. |
| `fn wrapping_sub(self, rhs: Self) -> Self` | $(self - rhs) \bmod 2^N$ interpreted as `Self`. | Infallible. |
| `fn wrapping_mul(self, rhs: Self) -> Self` | $(self \cdot rhs) \bmod 2^N$ interpreted as `Self`. | Infallible. |
| `fn wrapping_div(self, rhs: Self) -> Self` | Signed `T.MIN.wrapping_div(-1) == T.MIN`; otherwise $self / rhs$. | **Panics** with `"division by zero"` if `rhs == 0`. |
| `fn wrapping_rem(self, rhs: Self) -> Self` | Signed `T.MIN.wrapping_rem(-1) == 0`; otherwise $self \% rhs$. | **Panics** with `"division by zero"` if `rhs == 0`. |
| `fn wrapping_neg(self) -> Self` | $(0 - self) \bmod 2^N$ ($\sim self + 1$). | Infallible (`T.MIN.wrapping_neg() == T.MIN` for signed; `1u8.wrapping_neg() == 255u8` for unsigned). |
| `fn wrapping_shl(self, rhs: u32) -> Self` | `self << (rhs & (T.BITS - 1u32))` | Infallible for all `u32`. |
| `fn wrapping_shr(self, rhs: u32) -> Self` | `self >> (rhs & (T.BITS - 1u32))` | Infallible for all `u32`. |
| `fn wrapping_abs(self) -> Self` *(signed only)* | `if self < 0 { self.wrapping_neg() } else { self }` | `T.MIN.wrapping_abs() == T.MIN`. |
| `fn wrapping_pow(self, exp: u32) -> Self` | Exponentiation by squaring using `wrapping_mul`, $self^0 = 1$. | Infallible (`0.wrapping_pow(0) == 1`). |

### AXS-INT-023 — Saturating Arithmetic Family & MIR Lowering (`ANUM-37`, `REQ-SIMD-102`, `SPEC-04 AXS-EXT-042`)

1. **Method surface**: Every integer type `T` provides:
   - `fn saturating_add(self, rhs: Self) -> Self`: returns $\min(\text{T.MAX}, \max(\text{T.MIN}, self + rhs))$.
   - `fn saturating_sub(self, rhs: Self) -> Self`: returns $\min(\text{T.MAX}, \max(\text{T.MIN}, self - rhs))$.
   - `fn saturating_mul(self, rhs: Self) -> Self`: returns $\min(\text{T.MAX}, \max(\text{T.MIN}, self \cdot rhs))$.
   - `fn saturating_div(self, rhs: Self) -> Self`: panics on `rhs == 0`; for signed `T`, `T.MIN.saturating_div(-1) == T.MAX`; otherwise `self / rhs`.
   - `fn saturating_neg(self) -> Self` *(signed only)*: `T.MIN.saturating_neg() == T.MAX`; otherwise `-self`.
   - `fn saturating_abs(self) -> Self` *(signed only)*: `T.MIN.saturating_abs() == T.MAX`; otherwise `abs(self)`.
   - `fn saturating_pow(self, exp: u32) -> Self`: exponentiation by squaring using `saturating_mul`, clamping to `[T.MIN, T.MAX]`.
2. **Canonical MIR lowering (`SPEC-04 AXS-EXT-042`, `T452`)**:
   - Calls to `saturating_add`, `saturating_sub`, and `saturating_mul` (and intrinsics `intrinsic_saturating_add`, `intrinsic_saturating_sub`, `intrinsic_saturating_mul`) lower directly to `MIR_RVALUE_BINARY_OP` with `MirBinOp`:
     - `MIR_BINOP_SAT_ADD = 18` (`SatAdd`)
     - `MIR_BINOP_SAT_SUB = 19` (`SatSub`)
     - `MIR_BINOP_SAT_MUL = 20` (`SatMul`)
   - Unlike default `+`, `-`, `*`, the MIR builder (`compiler/mir/builder.ax`) does **not** emit a companion `MIR_RVALUE_OVERFLOWS_BINARY_OP` + `Assert` terminator before `SatAdd`/`SatSub`/`SatMul`; saturating binary ops are total and infallible.
3. **x86-64 codegen for `SatAdd` / `SatSub` / `SatMul` (`T452`, `T453`)**:
   - Unsigned `SatAdd`: `add dst, rhs; mov tmp, -1; cmovc dst, tmp` (clamps to `uN.MAX` on carry `CF = 1`).
   - Unsigned `SatSub`: `sub dst, rhs; mov tmp, 0; cmovc dst, tmp` (clamps to `0` on borrow `CF = 1`).
   - Signed `SatAdd` / `SatSub`: compute result setting `OF`, compute sign-derived saturation bound `(r >> (N - 1)) ^ T.MAX` (i.e., `T.MAX` when wrapped result is negative, `T.MIN` when wrapped result is non-negative), and select via `cmovo dst, bound`.
   - `SatMul`: perform widening multiplication (`mul` / `imul`), test `CF`/`OF`, and select `uN.MAX` (unsigned) or `(sign_a ^ sign_b) ? T.MIN : T.MAX` (signed) via `cmovo`.

### AXS-INT-024 — Checked Arithmetic Family (`ANUM-39`, `REQ-SIMD-104`)

Every integer type `T` provides the following fallible methods returning `Option<Self>`:

| Method Signature | Returns `Option.None` When | Returns `Option.Some(v)` When |
|---|---|---|
| `fn checked_add(self, rhs: Self) -> Option<Self>` | $self + rhs \notin [\text{T.MIN}, \text{T.MAX}]$ | $v = self + rhs$ fits in `Self`. |
| `fn checked_sub(self, rhs: Self) -> Option<Self>` | $self - rhs \notin [\text{T.MIN}, \text{T.MAX}]$ | $v = self - rhs$ fits in `Self`. |
| `fn checked_mul(self, rhs: Self) -> Option<Self>` | $self \cdot rhs \notin [\text{T.MIN}, \text{T.MAX}]$ | $v = self \cdot rhs$ fits in `Self`. |
| `fn checked_div(self, rhs: Self) -> Option<Self>` | `rhs == 0` or (signed `self == T.MIN && rhs == -1`) | $v = \text{trunc}(self / rhs)$. |
| `fn checked_rem(self, rhs: Self) -> Option<Self>` | `rhs == 0` or (signed `self == T.MIN && rhs == -1`) | $v = self \% rhs$. |
| `fn checked_neg(self) -> Option<Self>` | Signed `self == T.MIN`, or unsigned `self != 0` | $v = -self$ (or `0` for unsigned `0`). |
| `fn checked_shl(self, rhs: u32) -> Option<Self>` | `rhs >= T.BITS` | $v = self \ll rhs$. |
| `fn checked_shr(self, rhs: u32) -> Option<Self>` | `rhs >= T.BITS` | $v = self \gg rhs$. |
| `fn checked_abs(self) -> Option<Self>` *(signed)* | `self == T.MIN` | $v = |self|$. |
| `fn checked_pow(self, exp: u32) -> Option<Self>` | Any intermediate or final power $\notin [\text{T.MIN}, \text{T.MAX}]$ | $v = self^{exp}$ ($0^0 = 1$). |

Checked methods **never panic** for any input values, including `rhs == 0` in `checked_div` / `checked_rem` and `rhs >= T.BITS` in `checked_shl` / `checked_shr`.

### AXS-INT-025 — Overflowing Arithmetic Family

Every integer type `T` provides the following methods returning a 2-tuple `(Self, bool)`:

- `fn overflowing_add(self, rhs: Self) -> (Self, bool)`: returns `(self.wrapping_add(rhs), did_overflow)` where `did_overflow` is emitted via `MIR_RVALUE_OVERFLOWS_BINARY_OP(Add)`.
- `fn overflowing_sub(self, rhs: Self) -> (Self, bool)`: returns `(self.wrapping_sub(rhs), did_overflow)` via `MIR_RVALUE_OVERFLOWS_BINARY_OP(Sub)`.
- `fn overflowing_mul(self, rhs: Self) -> (Self, bool)`: returns `(self.wrapping_mul(rhs), did_overflow)` via `MIR_RVALUE_OVERFLOWS_BINARY_OP(Mul)`.
- `fn overflowing_div(self, rhs: Self) -> (Self, bool)`: **panics** on `rhs == 0`; for signed `self == T.MIN && rhs == -1`, returns `(T.MIN, true)`; otherwise returns `(self / rhs, false)`.
- `fn overflowing_rem(self, rhs: Self) -> (Self, bool)`: **panics** on `rhs == 0`; for signed `self == T.MIN && rhs == -1`, returns `(0, true)`; otherwise returns `(self % rhs, false)`.
- `fn overflowing_neg(self) -> (Self, bool)`: returns `(self.wrapping_neg(), did_overflow)` where `did_overflow` is `self == T.MIN` for signed `T` and `self != 0` for unsigned `T`.
- `fn overflowing_shl(self, rhs: u32) -> (Self, bool)`: returns `(self.wrapping_shl(rhs), rhs >= T.BITS)`.
- `fn overflowing_shr(self, rhs: u32) -> (Self, bool)`: returns `(self.wrapping_shr(rhs), rhs >= T.BITS)`.
- `fn overflowing_abs(self) -> (Self, bool)` *(signed)*: returns `(self.wrapping_abs(), self == T.MIN)`.
- `fn overflowing_pow(self, exp: u32) -> (Self, bool)`: returns `(self.wrapping_pow(exp), did_overflow)`.

### AXS-INT-026 — Signed Magnitude & Sign Inspection Helpers

1. Every signed integer type `T` in `{i8, i16, i32, i64, i128, isize}` provides:
   - `fn abs(self) -> Self`: returns $|self|$; panics with `"arithmetic overflow"` if `self == T.MIN`.
   - `fn unsigned_abs(self) -> UT`: infallible conversion returning $|self|$ in the corresponding unsigned type `UT` (`u8`, `u16`, `u32`, `u64`, `u128`, `usize`), mapping `T.MIN` to $2^{N-1}$ (`(T.MAX as UT) + 1`).
   - `fn signum(self) -> Self`: returns `-1` if `self < 0`, `0` if `self == 0`, and `1` if `self > 0`.
   - `fn is_positive(self) -> bool`: returns `self > 0`.
   - `fn is_negative(self) -> bool`: returns `self < 0`.
2. Every integer type `T` (signed and unsigned) provides:
   - `fn abs_diff(self, other: Self) -> UT`: infallible absolute difference $|self - other|$ returned in the corresponding unsigned type `UT` (`u8..u128`, `usize`).
   - `fn pow(self, exp: u32) -> Self`: checked exponentiation; panics with `"arithmetic overflow"` if $self^{exp} \notin [\text{T.MIN}, \text{T.MAX}]$.
   - `fn min(self, other: Self) -> Self` and `fn max(self, other: Self) -> Self` and `fn clamp(self, min_val: Self, max_val: Self) -> Self` (panics if `min_val > max_val`).

---

## 4. Bit Manipulation & Endian Byte Conversion Suite

### AXS-INT-030 — Bitwise Operators (`ANUM-40`, `REQ-SIMD-105`)

1. All twelve integer types support bitwise AND (`&`), bitwise OR (`|`), bitwise XOR (`^`), and unary bitwise NOT (`~`) (`SPEC-03 AXS-SEM-034`).
2. Bitwise operations operate purely on the $N$-bit two's-complement / binary bit pattern of their operands, never overflow, never trap, and preserve identical bit-level semantics between scalar integers and SIMD integer lanes (`ANUM-40`, `REQ-SIMD-105`).
3. Note: Unary logical negation `!` is restricted to `bool`; bitwise complement on integers uses `~x` (`AX_TYPE_BITNOT_ON_BOOL` if `~` is applied to `bool`).

### AXS-INT-031 — Bit Manipulation Intrinsics & Methods (`REQ-SIMD-211`, `T454`)

Every primitive integer type `T` of bit width $N = \text{T.BITS}$ implements the following bit manipulation methods in `std.core.num`:

| Method Signature | Semantics | Return Domain / Notes |
|---|---|---|
| `fn count_ones(self) -> u32` | Population count (Hamming weight): number of `1` bits in $N$-bit representation. | `0u32 ..= T.BITS` |
| `fn count_zeros(self) -> u32` | Number of `0` bits: `T.BITS - self.count_ones()`. | `0u32 ..= T.BITS` |
| `fn leading_zeros(self) -> u32` | Number of contiguous `0` bits starting from the most significant bit (bit $N - 1$). | `0u32 ..= T.BITS` (`self == 0` returns `T.BITS`). |
| `fn trailing_zeros(self) -> u32` | Number of contiguous `0` bits starting from the least significant bit (bit $0$). | `0u32 ..= T.BITS` (`self == 0` returns `T.BITS`). |
| `fn leading_ones(self) -> u32` | Number of contiguous `1` bits from bit $N - 1$: `(~self).leading_zeros()`. | `0u32 ..= T.BITS` |
| `fn trailing_ones(self) -> u32` | Number of contiguous `1` bits from bit $0$: `(~self).trailing_zeros()`. | `0u32 ..= T.BITS` |
| `fn rotate_left(self, n: u32) -> Self` | Circular left bit shift by $k = n \bmod N$: `(self << k) \| (self unsigned_shr (N - k))`. | Infallible for all `n: u32`. |
| `fn rotate_right(self, n: u32) -> Self` | Circular right bit shift by $k = n \bmod N$: `(self unsigned_shr k) \| (self << (N - k))`. | Infallible for all `n: u32` (uses logical shift even on signed `T`). |
| `fn swap_bytes(self) -> Self` | Reverses the byte order of the $N/8$ bytes comprising `self` (`self` unchanged for `i8`/`u8`). | Infallible (`x.swap_bytes().swap_bytes() == x`). |
| `fn reverse_bits(self) -> Self` | Reverses the bit order of all $N$ bits so bit $i$ moves to bit $N - 1 - i$. | Infallible (`x.reverse_bits().reverse_bits() == x`). |

Additionally, every **unsigned** integer type `UT` in `{u8, u16, u32, u64, u128, usize}` implements power-of-two queries and rounding:
- `fn is_power_of_two(self) -> bool`: returns `self != 0 && (self & (self - 1)) == 0` (equivalently `self.count_ones() == 1u32`).
- `fn checked_next_power_of_two(self) -> Option<Self>`: returns `Option.Some(1)` for `self <= 1`, `Option.Some(2^k)` for the smallest $2^k \ge self$ when $2^k \le \text{UT.MAX}$, and `Option.None` when $self > 2^{N-1}$.
- `fn next_power_of_two(self) -> Self`: returns the smallest power of two $\ge self$, panicking with `"arithmetic overflow"` if $self > 2^{N-1}$.

### AXS-INT-032 — Endian Byte Array Conversions (`to_*_bytes` / `from_*_bytes`, `T454`)

Every primitive integer type `T` with byte width $B = \text{T.BITS} / 8 \in \{1, 2, 4, 8, 16\}$ (`B = 8` for `isize`/`usize` on 64-bit targets) provides exact fixed-size byte-array conversions between `Self` and `[B]u8`:

1. `fn to_le_bytes(self) -> [B]u8`: returns the $B$-byte little-endian representation where byte $k \in [0, B-1]$ equals `((self as UT) >> (8 * k)) as u8`.
2. `fn from_le_bytes(bytes: [B]u8) -> Self`: reconstructs `Self` from its $B$-byte little-endian representation (`T.from_le_bytes(x.to_le_bytes()) == x`).
3. `fn to_be_bytes(self) -> [B]u8`: returns the $B$-byte big-endian (network byte order) representation where byte $0$ is the most significant byte (`self.swap_bytes().to_le_bytes()`).
4. `fn from_be_bytes(bytes: [B]u8) -> Self`: reconstructs `Self` from its $B$-byte big-endian representation (`T.from_le_bytes(bytes).swap_bytes()`).
5. `fn to_ne_bytes(self) -> [B]u8` and `fn from_ne_bytes(bytes: [B]u8) -> Self`: native-endian conversions. On `x86_64-pc-windows-msvc` (little-endian), `to_ne_bytes` is identical to `to_le_bytes` and `from_ne_bytes` is identical to `from_le_bytes`.

### AXS-INT-033 — 128-Bit Formatting & Parsing (`std.text.fmt.int`, `T451`)

`std.text.fmt.int` supports lossless formatting and parsing for all twelve integer types including `i128` and `u128`:
- Decimal, hexadecimal (`0x` / lower / upper hex), binary, and octal formatting of `u128` and `i128` (handling `i128.MIN = -170141183460469231731687303715884105728` via `unsigned_abs()` without negation overflow).
- Checked string-to-integer parsing returning `Option<T>` or `Result<T, ParseIntError>` that rejects strings whose value falls outside `[T.MIN, T.MAX]` using `checked_mul` and `checked_add` / `checked_sub`.

---

## 5. Four Conversion Classes: `COERCION`, `CAST`, `TRY_CAST` & `BITCAST`

### AXS-INT-040 — Canonical Conversion Taxonomy (`tasks/0431 §172.1–14`, `ANUM-41`, `ANUM-91`, `REQ-SIMD-106`, `REQ-SIMD-156`)

Axiom partitions all numeric and bit-level value transformations into four mutually exclusive conversion classes (`ACONV-20..75`, `ANUM-41`, `ANUM-91`):

| Conversion Class | Surface Syntax / API | Information Loss Policy | Runtime Failure Mode | Canonical Lowering |
|---|---|---|---|---|
| **`COERCION`** | Implicit in multi-width numeric expressions (`§6`, `REQ-OWNER-007`), `IntVar` literal specialization, and array-index expression normalization. | **Strictly lossless** value-preserving widening along the numeric promotion lattice. Never truncates or wraps. | Infallible (except array-index bounds check at index projection). | `typeck` synthesizes an explicit `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`) in `compiler/mir/builder.ax`. |
| **`CAST`** | Explicit `expr as TargetType` operator (`SPEC-03 AXS-SEM-061`). | **May lose information** (truncation, sign reinterpretation, or float-to-int saturation in `SPEC-41`); lossy conversions must be explicit (`ANUM-91`, `REQ-SIMD-156`). | Infallible at runtime; never panics and never invokes user traits (`From`/`TryFrom`). | `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`, `MIR_CAST_INT_TO_FLOAT`, `MIR_CAST_FLOAT_TO_INT`). |
| **`TRY_CAST`** | Trait methods `From.from(x)` / `x.into()` (infallible lossless) and `TryFrom.try_from(x)` / `x.try_into()` (fallible range-checked) in `std.core.convert`. | **Never loses information silently**: `From` only exists for compile-time lossless pairs; `TryFrom` checks dynamic bounds and returns `Result.Err(TryFromIntError)` if out of range. | Returns `Result<Target, TryFromIntError>` (`Option`/`Result` value path, no panic). | Normal trait method call in HIR/MIR (`std.core.convert`). |
| **`BITCAST`** | Explicit bit-pattern reinterpretation APIs (`to_ne_bytes`/`from_ne_bytes`, `to_le_bytes`/`from_le_bytes`, `f32.to_bits`/`f32.from_bits`, `f64.to_bits`/`f64.from_bits`, SIMD lane bitcast). | **Preserves exact bit representation** across equal-size types; does not preserve numeric value (`ANUM-41`, `REQ-SIMD-106`). | Infallible (compile-time size equality required). | Dedicated intrinsic / byte-reinterpretation rvalue. |

### AXS-INT-041 — Explicit Primitive `as` Cast (`CAST`, `MIR_CAST_INT_TO_INT`)

An explicit `x as Target` expression between any source integer type `Src` of bit width $M$ and any target integer type `Dst` of bit width $N$ (`Src, Dst` $\in \{i8..i128, u8..u128, isize, usize\}$) is always well-typed and lowers to `MIR_RVALUE_CAST` with `MIR_CAST_INT_TO_INT`:

1. **Same width ($M == N$, e.g. `i64 as u64`, `i128 as u128`, `isize as usize`, `i64 as isize`)**: No-op bit reinterpretation of the $N$-bit two's-complement pattern (value changes modulo $2^N$ when signedness differs).
2. **Narrowing ($M > N$, e.g. `u64 as u32`, `i64 as i16`, `i128 as i64`, `u128 as u8`)**: Retains the low $N$ bits (`x & ((1 << N) - 1)`), discarding the upper $M - N$ bits (modular reduction $\bmod 2^N$).
3. **Widening from unsigned ($M < N$, `Src` unsigned, `Dst` signed or unsigned, e.g. `u8 as u64`, `u32 as i64`, `u64 as i128`, `u64 as u128`)**: Zero-extends the $M$-bit unsigned value to $N$ bits (`hi = 0` when widening `u64` to `i128`/`u128`). Preserves exact mathematical value.
4. **Widening from signed ($M < N$, `Src` signed, `Dst` signed or unsigned, e.g. `i8 as i64`, `i8 as u64`, `i64 as i128`, `i64 as u128`)**: Sign-extends the $M$-bit two's-complement value to $N$ bits (`hi = (lo as i64 >> 63) as u64` when widening `i64` to `i128`/`u128`), then interprets the resulting $N$-bit pattern as `Dst`. In particular, `(-1i8) as u64 == 0xFFFF_FFFF_FFFF_FFFFu64` and `(-1i64) as u128 == u128.MAX`.
5. **`bool` and `char` integer casts (`SPEC-03 AXS-SEM-061`)**:
   - `bool as Dst` is valid for any integer type `Dst`, producing `0` for `false` and `1` for `true` (`MIR_CAST_BOOL_TO_INT`). Integer-to-`bool` `as` casts are rejected (`AX_TYPE_INVALID_CAST`); write `x != 0`.
   - `char as u32` (and widening to `u64`/`u128`/`usize`) produces the Unicode scalar value; `u8 as char` is the only valid integer-to-`char` `as` cast.

### AXS-INT-042 — Lossless `From<T>` / `Into<T>` Conversion Matrix (`TRY_CAST` Infallible Subset, `T454`)

In `std.core.convert`, `From<Src> for Dst` (and blanket `Into<Dst> for Src`) is implemented for primitive integers **if and only if** every mathematical value of `Src` is representable in `Dst` (`[Src.MIN, Src.MAX]` $\subseteq$ `[Dst.MIN, Dst.MAX]`):

1. **Reflexive**: `From<T> for T` for all 12 integer types.
2. **Unsigned-to-unsigned widening**:
   - `u8` $\to$ `u16`, `u32`, `u64`, `u128`, `usize`
   - `u16` $\to$ `u32`, `u64`, `u128`, `usize`
   - `u32` $\to$ `u64`, `u128`, `usize` *(on 64-bit targets)*
   - `u64` $\to$ `u128`
   - `usize` $\to$ `u128`
3. **Signed-to-signed widening**:
   - `i8` $\to$ `i16`, `i32`, `i64`, `i128`, `isize`
   - `i16` $\to$ `i32`, `i64`, `i128`, `isize`
   - `i32` $\to$ `i64`, `i128`, `isize` *(on 64-bit targets)*
   - `i64` $\to$ `i128`
   - `isize` $\to$ `i128`
4. **Unsigned-to-strictly-wider-signed**:
   - `u8` $\to$ `i16`, `i32`, `i64`, `i128`, `isize`
   - `u16` $\to$ `i32`, `i64`, `i128`, `isize`
   - `u32` $\to$ `i64`, `i128`, `isize` *(on 64-bit targets)*
   - `u64` $\to$ `i128`
   - `usize` $\to$ `i128`
5. **`bool` to integer**: `From<bool> for Dst` for all 12 integer types (`false` $\mapsto 0$, `true` $\mapsto 1$).

Signed-to-unsigned conversions (`i8` $\to$ `u16`, etc.) and same-width `i64` $\leftrightarrow$ `isize` / `u64` $\leftrightarrow$ `usize` are **not** in `From` (the former can be negative; the latter use explicit `as` or `TryFrom`/`From` target-width helpers as specified in `std.core.convert`).

### AXS-INT-043 — Fallible `TryFrom<T>` / `TryInto<T>` & `TryFromIntError` (`TRY_CAST`, `ANUM-91`, `REQ-SIMD-156`, `T454`)

1. **`TryFromIntError`**: `std.core.convert` defines:
   ```axiom
   pub struct TryFromIntError {}
   ```
   implementing `Copy`, `Clone`, `Eq`, `PartialEq`, `Debug`, and `Display`.
2. **Blanket and fallible implementations**:
   - Every pair `(Src, Dst)` implementing `From<Src> for Dst` also satisfies `TryFrom<Src> for Dst` returning `Result.Ok(Dst.from(x))`.
   - Every remaining integer pair `(Src, Dst)` across the 12 integer types implements `TryFrom<Src> for Dst` with `type Error = TryFromIntError`:
     - **Narrowing same-signedness (`Src` wider than `Dst`)**: returns `Result.Ok(x as Dst)` iff `x >= (Dst.MIN as Src) && x <= (Dst.MAX as Src)`, else `Result.Err(TryFromIntError {})`.
     - **Signed `Src` to unsigned `Dst`**:
       - If $\text{Dst.BITS} \ge \text{Src.BITS}$ (e.g., `i32` $\to$ `u32` or `i32` $\to$ `u64`): returns `Result.Ok(x as Dst)` iff `x >= 0`, else `Result.Err(TryFromIntError {})`.
       - If $\text{Dst.BITS} < \text{Src.BITS}$ (e.g., `i64` $\to$ `u16`): returns `Result.Ok(x as Dst)` iff `x >= 0 && x <= (Dst.MAX as Src)`, else `Result.Err(TryFromIntError {})`.
     - **Unsigned `Src` to signed `Dst` with $\text{Dst.BITS} \le \text{Src.BITS}$** (e.g., `u32` $\to$ `i32`, `u64` $\to$ `i32`, `u128` $\to$ `i128`): returns `Result.Ok(x as Dst)` iff `x <= (Dst.MAX as Src)`, else `Result.Err(TryFromIntError {})`.

### AXS-INT-044 — Strict Separation of Numeric Conversion and `BITCAST` (`ANUM-41`, `REQ-SIMD-106`)

1. Numeric conversion (`COERCION`, `CAST`, `TRY_CAST`) maps a **mathematical number** from one numeric domain to another (`42i32 as f32 == 42.0f32`, `256u16 as u8 == 0u8`).
2. `BITCAST` reinterprets the **underlying bit pattern** of an $N$-bit value as another $N$-bit type without altering any bits (`0x3F80_0000u32` bitcast to `f32` is `1.0f32`; `(-1i8).to_ne_bytes()` is `[0xFFu8]`).
3. `as` **never** performs a float-to-int or int-to-float bitcast (`ANUM-41`, `REQ-SIMD-106`). Reinterpreting integer bits as floating-point or byte arrays requires explicit bitcast methods (`f32.from_bits`, `f32.to_bits`, `f64.from_bits`, `f64.to_bits` in `SPEC-41`, or `to_ne_bytes`/`from_ne_bytes` in `AXS-INT-032`).

---

## 6. Multi-Width Integer Expression Promotion Lattice (`REQ-OWNER-007` Integer Sub-Lattice)

### AXS-INT-050 — Scope & Design Principles of Multi-Width Integer Promotion (`REQ-OWNER-007`, `T455`)

To support ergonomic mathematical and scientific formulas that combine multiple integer widths in a single expression (`REQ-OWNER-007` Pattern D) while preserving Axiom's strict type safety at declaration and call boundaries (`SPEC-03 AXS-SEM-022`), `axiomc` defines a deterministic **Multi-Width Integer Expression Promotion Sub-Lattice** in `compiler/types/typeck.ax` and `compiler/mir/builder.ax`:

1. **Where implicit widening applies**: Inside binary arithmetic (`+`, `-`, `*`, `/`, `%`), bitwise (`&`, `|`, `^`), and comparison (`==`, `!=`, `<`, `<=`, `>`, `>=`) expressions whose operands have **different integer widths** (or where narrow integer operands combine with unsuffixed integer literals inside a wider integer expression tree), and inside array/slice index expressions `base[idx_expr]`.
2. **Where implicit widening does NOT apply (preserving `SPEC-03 AXS-SEM-022` and existing UI diagnostics)**:
   - **Standalone variable binding, assignment, return, or function argument**: `let b: i64 = a` (where `a: i32`), `x = a`, `takes_i64(a)`, `return a`, or `let f: i32 = ~x` (where `x: u8` is a unary expression not participating in a multi-width binary promotion) **must not** implicitly widen `a` or `~x`; `typeck` emits `AX_TYPE_MISMATCH` (`2001`).
   - **Same-width signed/unsigned mixing without a wider enclosing arithmetic context**: A standalone binary operation between same-width signed and unsigned integers (`i8 + u8`, `i16 + u16`, `i32 + u32`, `i64 + u64`, `i128 + u128`) has no lossless common type at that width and emits `AX_TYPE_MISMATCH` (`2001`).
   - **Single-width narrow integer + unsuffixed literal in isolation**: When an expression such as `let x: u8 = 255; let y = x + 1` or `let a: u16 = 65535; let b = a - 65535` has no wider integer operand and no wider expected integer type annotation, the unsuffixed literal (`IntVar`) unifies directly with the narrow operand's type (`u8` or `u16`), preserving narrow overflow checking (`tests/conformance/vs0/arith_u8_overflow.ax`).

### AXS-INT-051 — Deterministic Pure-Integer Promotion Join $\text{join}_{\text{int}}(T_1, T_2)$

Given two concrete primitive integer types $T_1 \ne T_2$ of bit widths $W(T_1)$ and $W(T_2)$ (where $W(\text{isize}) = W(\text{usize}) = 64$ on 64-bit targets) appearing as operands of a binary arithmetic, bitwise, or comparison operator, the common promoted integer type $T_{\text{common}} = \text{join}_{\text{int}}(T_1, T_2)$ is defined deterministically as follows:

1. **Same signedness, different widths ($W(T_1) \ne W(T_2)$)**:
   - Both signed (`i8`, `i16`, `i32`, `i64`, `isize`, `i128`): $T_{\text{common}}$ is the wider signed type ($\max_W(T_1, T_2)$).
     - Chain: `i8` $\prec$ `i16` $\prec$ `i32` $\prec$ `i64` / `isize` $\prec$ `i128`.
   - Both unsigned (`u8`, `u16`, `u32`, `u64`, `usize`, `u128`): $T_{\text{common}}$ is the wider unsigned type ($\max_W(T_1, T_2)$).
     - Chain: `u8` $\prec$ `u16` $\prec$ `u32` $\prec$ `u64` / `usize` $\prec$ `u128`.
2. **Same signedness, pointer-sized vs 64-bit fixed (`i64` with `isize`, or `u64` with `usize`)**:
   - $\text{join}_{\text{int}}(\text{i64}, \text{isize}) = \text{i64}$ (or `isize` when the enclosing expected type is `isize`).
   - $\text{join}_{\text{int}}(\text{u64}, \text{usize}) = \text{u64}$ (or `usize` when inside an index expression or when the enclosing expected type is `usize`).
3. **Different signedness, narrower unsigned $U_N$ + wider signed $I_M$ ($N < M$)**:
   - Because every value of $U_N$ ($[0, 2^N - 1]$) is strictly representable in $I_M$ ($[-2^{M-1}, 2^{M-1} - 1]$ for $N < M$), $U_N$ promotes losslessly to $I_M$:
     $$\text{join}_{\text{int}}(U_N, I_M) = I_M \quad (N < M)$$
     Specifically:
     - `u8` + `i16` $\to$ `i16`; `u8` + `i32` $\to$ `i32`; `u8` + `i64` $\to$ `i64`; `u8` + `i128` $\to$ `i128`.
     - `u16` + `i32` $\to$ `i32`; `u16` + `i64` $\to$ `i64`; `u16` + `i128` $\to$ `i128`.
     - `u32` + `i64` $\to$ `i64`; `u32` + `i128` $\to$ `i128`.
     - `u64` / `usize` + `i128` $\to$ `i128`.
4. **Different signedness, narrower signed $I_N$ + wider unsigned $U_M$ ($N < M$, e.g. `u16 + i8`)**:
   - Neither $I_N$ nor $U_M$ contains the other's full domain, so both promote to the **smallest signed integer type $I_K$ with $K > M$** that losslessly encompasses both $[-2^{N-1}, 2^{N-1}-1]$ and $[0, 2^M - 1]$ (or to the enclosing wider signed target type if one is active):
     - $M = 16$ (`u16` with `i8`): $\text{join}_{\text{int}}(\text{u16}, \text{i8}) = \text{i32}$ (or `i64` when evaluated under an `i64` expected context).
     - $M = 32$ (`u32` with `i8` or `i16`): $\text{join}_{\text{int}}(\text{u32}, I_N) = \text{i64}$.
     - $M = 64$ (`u64` / `usize` with `i8`, `i16`, `i32`): $\text{join}_{\text{int}}(U_{64}, I_N) = \text{i128}$ (or `i64` if explicitly under an `i64` arithmetic chain where $U_{64}$ is not present).
     - $M = 128$ (`u128` with any signed $I_N$): **no lossless signed super-type exists**; rejected with `AX_TYPE_MISMATCH` (`2001`).
5. **Different signedness, equal width ($N == M$, e.g. `i32 + u32`, `i8 + u8`)**:
   - If the binary expression is evaluated under an active wider signed expected context $I_K$ ($K > N$, e.g. inside an `i64` arithmetic tree), both operands promote to $I_K$.
   - Otherwise (standalone `let e = a_i32 + d_u32` with no wider enclosing arithmetic type), $\text{join}_{\text{int}}$ is **undefined** and `typeck` emits `AX_TYPE_MISMATCH` (`2001`).
6. **Interaction with floating-point promotion (`SPEC-41`, `T456`, `T457`)**:
   - When an expression mixes integer types with `f32` or `f64` (`REQ-OWNER-007` Patterns A, B, C), the pure-integer sub-lattice in `SPEC-40` embeds directly into the full numeric promotion lattice in `SPEC-41`: integer sub-expressions promote along `AXS-INT-051..053` and widen to `f32`/`f64` at mixed int-float operator nodes via `MIR_CAST_INT_TO_FLOAT`.

### AXS-INT-052 — Contextual Propagation & `IntVar` Resolution in Compound Integer Trees (`REQ-OWNER-007` Pattern D)

In compound multi-operand arithmetic trees such as `REQ-OWNER-007` Pattern D:

```axiom
let s64: i64 = 100000
let s32: i32 = -2000
let u16v: u16 = 500
let b8: u8 = 200
let s8: i8 = -50
let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8)
```

evaluating narrow sub-expressions such as `b8 * 2` (`200u8 * 2 = 400`, which would overflow `u8.MAX = 255`) or `4 - s8` in narrow `u8`/`i8` width before widening would produce spurious narrow overflow or sub-tree width mismatches. Therefore, `typeck` applies two-pass (or contextual top-down + bottom-up) integer tree typing:

1. **Multi-width arithmetic tree detection**: An arithmetic expression tree $E$ (built from binary `+`, `-`, `*`, `/`, `%`, `&`, `|`, `^`, unary `-`, `~`, and parenthesized sub-expressions) is a **widening arithmetic context** of target type $T_{\text{ctx}}$ whenever:
   - $E$ has an explicit wider expected integer type $T_{\text{expected}}$ from its enclosing declaration/expression (e.g., `let total: i64 = E`) **and** $E$ contains at least two distinct concrete integer types or a concrete integer type narrower than $T_{\text{expected}}$ combined inside a binary arithmetic chain; **or**
   - $E$ itself combines concrete integer operands of at least two different widths whose join under `AXS-INT-051` is $T_{\text{ctx}}$.
2. **Propagation into sub-expressions with narrow integers and `IntVar` literals**:
   - Inside a widening arithmetic context of signed/unsigned target type $T_{\text{ctx}}$ (such as `i64` in Pattern D), any arithmetic sub-expression combining a narrower integer operand $x : T_{\text{narrow}}$ ($W(T_{\text{narrow}}) < W(T_{\text{ctx}})$) with an unsuffixed integer literal (`IntVar`, such as `b8 * 2`, `s32 * 3`, `4 - s8`, or `... - 7`) promotes $x$ and unifies the `IntVar` literal to the enclosing arithmetic type $T_{\text{ctx}}$ (or the sub-tree's promoted width $\ge \text{i32}$) **before** performing the binary operation.
   - Consequently, in Pattern D:
     - `s32 * 3`: `s32` (`i32`) widens to `i64` (or evaluates in `i64` with `3i64`), yielding `-6000i64`; `s64 + s32 * 3 == 94000i64`.
     - `b8 * 2`: `b8` (`200u8`) widens to `i64` (or `i32` then `i64`) before multiplying by `2`, yielding `400` without overflowing `u8`!
     - `u16v + b8 * 2 + s8 - 7`: `500 + 400 + (-50) - 7 == 843i64`.
     - `4 - s8`: `s8` (`-50i8`) widens to `i64` before subtracting from `4`, yielding `54i64`.
     - `(u16v + b8 * 2 + s8 - 7) / (4 - s8)`: `843i64 / 54i64 == 15i64` (truncating integer division).
     - `total`: `94000i64 - 15i64 == 93985i64`.
3. **Standalone single-width preservation**: When an expression tree contains only a single concrete narrow integer type $T$ and unsuffixed literals (`IntVar`) and has **no** wider integer operand and **no** wider expected type (or its expected type is $T$ itself, e.g. `let x: u8 = 255; let y = x + 1` or `let y: u8 = x + 1`), $T_{\text{ctx}} = T$ (`u8`), so `1` unifies with `u8` and `x + 1` checks overflow at `u8` width as required by `SPEC-03 AXS-SEM-021`.

### AXS-INT-053 — Array and Slice Index Expression Promotion to `usize` (`REQ-OWNER-007` Pattern C, `T455`)

In an array or slice indexing expression `base[idx_expr]` (`SPEC-03 AXS-SEM-042`):
1. If `idx_expr` is a composite integer expression (e.g. `coeff[idx + off]`, `coeff[idx - 1]`) or has any concrete integer type $T_{\text{idx}} \in \{i8..i128, u8..u128, isize, usize\}$ after evaluating `idx_expr` under the integer promotion rules (`AXS-INT-051..052`):
   - Unsuffixed literals inside `idx_expr` (such as `1` in `idx - 1` where `idx: i32`) unify with the operand type (`i32`) so `idx + off` and `idx - 1` evaluate naturally in `i32`.
   - If the resulting type $T_{\text{idx}}$ of `idx_expr` is not already `usize`, `compiler/mir/builder.ax` emits an explicit `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`) converting the index temporary from $T_{\text{idx}}$ to `usize` before emitting `MIR_PROJ_INDEX` and the bounds check `idx_usize < len`.
   - Non-integer index expressions (e.g. `bool`, `f32`, `f64`, structs) remain rejected with `AX_TYPE_INDEX_NOT_INT` (`2014`).

### AXS-INT-054 — Homogeneous MIR Invariant & Explicit `MIR_RVALUE_CAST` Lowering (`INV-INT-003`, `T455`)

1. **Single-stage promotion lowering**: All implicit integer promotions (`AXS-INT-051..053`) are resolved in `compiler/types/typeck.ax` and materialized during HIR-to-MIR lowering (`compiler/mir/builder.ax`) by inserting an explicit temporary local of the promoted type $T_{\text{common}}$ assigned via:
   ```text
   _promoted = Cast(IntToInt, _narrow_operand, T_common)
   ```
   immediately prior to the `MIR_RVALUE_OVERFLOWS_BINARY_OP`, `MIR_RVALUE_BINARY_OP`, or `MIR_PROJ_INDEX` instruction.
2. **Verifier enforcement**: `compiler/verify/verifier.ax` (`INV-INT-003`) requires that for every `MIR_RVALUE_BINARY_OP` and `MIR_RVALUE_OVERFLOWS_BINARY_OP` (except shift operators `Shl`/`Shr`, where the shift count operand may be any integer type or `u32`), the left-hand and right-hand MIR operands have **identical** `MirType`, and for arithmetic/bitwise operators the destination local also has that identical `MirType`.
3. **Downstream stage simplicity**: Because `compiler/mir/builder.ax` emits explicit `MIR_RVALUE_CAST` instructions for all promotions, the MIR interpreter (`compiler/mir/interp.ax`), MIR optimization passes (`compiler/opt/`), LIR lowering (`compiler/lir/lower.ax`), and the x86-64 backend (`compiler/backend/x64/`) never encounter mixed-width binary operations.

---

## 7. Diagnostics, Canonical Examples & Requirement Traceability

### AXS-INT-060 — Integer & Conversion Diagnostic Codes

| Code | Numeric ID | Symbolic Name | Trigger Condition in `SPEC-40` |
|---|---|---|---|
| `1004` | `1004` | `AX_LEX_INT_OVERFLOW` | Integer literal magnitude exceeds `u128.MAX` ($2^{128} - 1$) during lexing (`AXS-INT-004`). |
| `2001` | `2001` | `AX_TYPE_MISMATCH` | Direct standalone variable binding, assignment, return, or call argument between distinct integer types (`let x: i64 = y_i32`), or standalone same-width signed/unsigned binary operation (`i32 + u32`), or `u128` mixed with signed integer (`AXS-INT-050..051`). |
| `2011` | `2011` | `AX_TYPE_BINARY_OP` | Binary arithmetic or bitwise operator applied to non-numeric / incompatible types (`AXS-INT-021`). |
| `2012` | `2012` | `AX_TYPE_UNARY_OP` | Unary negation `-` applied to an unsigned integer type (`u8..u128`, `usize`) (`AXS-INT-021`). |
| `2014` | `2014` | `AX_TYPE_INDEX_NOT_INT` | Array/slice index expression is not an integer type (`AXS-INT-053`). |
| `2016` | `2016` | `AX_TYPE_INVALID_CAST` | Invalid `as` cast, such as casting an integer to `bool` (`x as bool`) or casting non-`u8` integer to `char` (`AXS-INT-041`). |
| `2017` | `2017` | `AX_TYPE_LITERAL_OUT_OF_RANGE` | Integer literal (after folding unary `-`) falls outside `[T.MIN, T.MAX]` of its resolved target integer type `T` (`AXS-INT-004`). |
| `2021` | `2021` | `AX_TYPE_SHIFT_COUNT` | Shift count operand is not an integer type or is known at compile time to be outside `[0, T.BITS - 1]` (`AXS-INT-021`). |
| `3102` | `3102` | `AX_CONST_DIV_ZERO` | Compile-time constant evaluation divides or takes remainder by zero (`AXS-INT-005`). |
| `3103` | `3103` | `AX_CONST_OVERFLOW` | Compile-time constant evaluation overflows target integer range `[T.MIN, T.MAX]` in a checked operator (`AXS-INT-005`). |
| `3104` | `3104` | `AX_CONST_SHIFT_RANGE` | Compile-time constant shift count $< 0$ or $\ge \text{T.BITS}$ (`AXS-INT-005`). |

### AXS-INT-061 — Canonical Positive Examples

#### Example 1 — 128-Bit Arithmetic, Bit Intrinsics & Endian Conversions

```axiom
module example.integers_128

pub fn demo_i128_and_families() -> i128 {
    let hi_val: i128 = 170141183460469231731687303715884105720i128
    let saturated: i128 = hi_val.saturating_add(100i128)
    assert(saturated == i128.MAX)

    let wrapped: u128 = u128.MAX.wrapping_add(1u128)
    assert(wrapped == 0u128)

    let checked: Option<i128> = i128.MAX.checked_add(1i128)
    assert(checked.is_none())

    let ovf: (u128, bool) = u128.MAX.overflowing_add(2u128)
    assert(ovf.0 == 1u128)
    assert(ovf.1)

    let mask: u128 = (1u128 << 100u32) | 0xFFu128
    assert(mask.count_ones() == 9u32)
    assert(mask.leading_zeros() == 27u32)
    assert(mask.trailing_zeros() == 0u32)

    let le: [16]u8 = hi_val.to_le_bytes()
    let roundtrip: i128 = i128.from_le_bytes(le)
    assert(roundtrip == hi_val)

    return roundtrip
}
```

#### Example 2 — `From` / `TryFrom` Conversions & Multi-Width Integer Expression (`REQ-OWNER-007` Pattern D)

```axiom
module example.integer_promotions

use std.core.convert.From
use std.core.convert.TryFrom
use std.core.convert.TryFromIntError

pub fn compute_pattern_d() -> i64 {
    let s64: i64 = 100000
    let s32: i32 = -2000
    let u16v: u16 = 500
    let b8: u8 = 200
    let s8: i8 = -50

    // REQ-OWNER-007 Pattern D: multi-width integer expression promotion
    // (100000 + (-6000)) - (500 + 400 - 50 - 7) / (4 - (-50))
    // = 94000 - 843 / 54 = 94000 - 15 = 93985
    let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8)
    assert(total == 93985)

    // Lossless widening via From
    let widened: i128 = i128.from(total)
    assert(widened == 93985i128)

    // Fallible narrowing via TryFrom
    let ok_u16: Result<u16, TryFromIntError> = u16.try_from(500i64)
    assert(ok_u16.is_ok())
    let err_u16: Result<u16, TryFromIntError> = u16.try_from(total)
    assert(err_u16.is_err())

    return total
}
```

### AXS-INT-062 — Canonical Negative Examples (Compile-Time Rejections)

1. **Direct standalone variable binding between distinct integer widths (`AX_TYPE_MISMATCH`)**:
   - Writing `let a: i32 = 10` followed by `let b: i64 = a` is rejected with `AX_TYPE_MISMATCH` (`2001`). Implicit integer promotion applies only inside multi-width expressions (`§6`), never across standalone bindings, assignments, return statements, or function call arguments; write `let b: i64 = i64.from(a)` or `let b: i64 = a as i64`.
2. **Standalone same-width signed and unsigned binary operation (`AX_TYPE_MISMATCH`)**:
   - Writing `let a: i32 = 1` and `let d: u32 = 2` followed by `let e = a + d` is rejected with `AX_TYPE_MISMATCH` (`2001`) because no 32-bit type can losslessly represent both `i32` and `u32`.
3. **Literal out of range for target type (`AX_TYPE_LITERAL_OUT_OF_RANGE`)**:
   - Writing `let x: u8 = 256` or `let y: i128 = 170141183460469231731687303715884105728i128` (without unary `-`) is rejected with `AX_TYPE_LITERAL_OUT_OF_RANGE` (`2017`).
4. **Literal exceeding 128-bit unsigned maximum (`AX_LEX_INT_OVERFLOW`)**:
   - Writing `let z: u128 = 340282366920938463463374607431768211456u128` ($2^{128}$) is rejected by the lexer with `AX_LEX_INT_OVERFLOW` (`1004`).
5. **Unary negation on unsigned integer (`AX_TYPE_UNARY_OP`)**:
   - Writing `let u: u64 = 5` followed by `let n = -u` is rejected with `AX_TYPE_UNARY_OP` (`2012`); use `u.wrapping_neg()` or `u.checked_neg()`.

### AXS-INT-063 — Requirement Traceability Matrix

| Requirement ID | Legacy / Catalog ID | Title / Summary | Normative Section(s) in `SPEC-40` | Downstream Implementation Task(s) |
|---|---|---|---|---|
| `REQ-OWNER-007` | `REQ-OWNER-007` | Complex Mixed-Type Expression Matrix (pure-integer sub-lattice, Pattern D, and index expression promotion; float lattice in `SPEC-41`) | `§5 AXS-INT-040`, `§6 AXS-INT-050..054`, `§7 AXS-INT-061` | `T455` (integer sub-lattice), `T456` (`SPEC-41`), `T457` (float+int lattice) |
| `REQ-SIMD-085` | `ANUM-20` | Scalar numeric types are fundamental Axiom values | `§1 AXS-INT-001..006` | `T451` |
| `REQ-SIMD-101` | `ANUM-36` | SIMD arithmetic does not silently change overflow semantics | `§2 AXS-INT-013`, `§3 AXS-INT-020..021` | `T452`, `T463` |
| `REQ-SIMD-102` | `ANUM-37` | Saturating arithmetic is explicit (`saturating_*`, `MirBinOp.SatAdd`/`SatSub`/`SatMul`) | `§3 AXS-INT-020, AXS-INT-023` | `T452`, `T453` |
| `REQ-SIMD-103` | `ANUM-38` | Wrapping arithmetic is explicit (`wrapping_*`) | `§3 AXS-INT-020, AXS-INT-022` | `T452`, `T453` |
| `REQ-SIMD-104` | `ANUM-39` | Checked arithmetic is explicit (`checked_*` returning `Option<Self>`) | `§3 AXS-INT-020, AXS-INT-024..025` | `T452`, `T453` |
| `REQ-SIMD-105` | `ANUM-40` | SIMD bitwise operations preserve bit-level semantics | `§4 AXS-INT-030..031` | `T454`, `T463` |
| `REQ-SIMD-106` | `ANUM-41` | Numeric conversion is distinct from bitcast | `§5 AXS-INT-040, AXS-INT-044` | `T454`, `T456` |
| `REQ-SIMD-156` | `ANUM-91` / `ACONV-30` | Numeric conversions that may lose information are explicit (`as` vs `From`/`TryFrom`) | `§5 AXS-INT-040..043` | `T454`, `T455` |
| `REQ-SIMD-086` | `ANUM-21` | Fixed-width integer semantics across all widths (`i8..i128`, `u8..u128`, `isize`, `usize`) | `§1 AXS-INT-001..006`, `§2 AXS-INT-010..012` | `T451`, `T453` |
| `REQ-SIMD-100` | `ANUM-35` | Explicit integer overflow modes (checked default, wrapping, saturating, checked, overflowing) | `§3 AXS-INT-020..026` | `T452`, `T453` |
| `REQ-SIMD-118` | `ANUM-53` | 128-bit integer ABI and register-pair lowering | `§2 AXS-INT-010..012` | `T453` |
| `REQ-SIMD-141` | `ANUM-76` | Lossless integer widening conversions (`From`/`Into`) | `§5 AXS-INT-040, AXS-INT-042` | `T454` |
| `REQ-SIMD-142` | `ANUM-77` | Fallible integer conversions (`TryFrom`/`TryInto`, `TryFromIntError`) | `§5 AXS-INT-040, AXS-INT-043` | `T454` |
| `REQ-SIMD-143` | `ANUM-78` | Primitive `as` cast truncation/sign-extension rules | `§5 AXS-INT-041` | `T453`, `T454` |
| `REQ-SIMD-144` | `ANUM-79` | Endian byte conversions (`to_le_bytes`, `from_le_bytes`, `to_be_bytes`, `from_be_bytes`, `to_ne_bytes`, `from_ne_bytes`) | `§4 AXS-INT-032` | `T454` |
| `REQ-SIMD-211` | `ANUM-146` | Bit manipulation suite (`swap_bytes`, `reverse_bits`, `leading_zeros`, `trailing_zeros`, `count_ones`, `rotate_left`, `rotate_right`, `is_power_of_two`, `next_power_of_two`) | `§4 AXS-INT-031` | `T454` |

---

## Sources

- `docs/base/tasks/0327_phase6_3_numerical_computing_float_complex_simd_tens.md` (`§84.1, §84.3, §84.10–11, §84.14–16`)
- `docs/base/tasks/0334_phase6_4_floating_point_semantics_ieee754_rounding_n.md` (`§91.1–12`)
- `docs/base/tasks/0341_phase6_5_simd_vector_model_portable_simd_width_abstr.md` (`§98.1–12`)
- `docs/base/tasks/0431_phase9_11_numeric_conversion_casting_semantics_coerc.md` (`§172.1–14`)
- `docs/base/specs/0157_type_system_v2.md`
- `docs/base/specs/0175_core_types_primitives_v2.md`
- `docs/base/specs/0245_stdlib_core_v2.md`
- `spec/SPEC-01-lexical.md` (`AXS-LEX-020`)
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-010`, `AXS-SEM-021..022`, `AXS-SEM-030..034`, `AXS-SEM-042`, `AXS-SEM-061`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-020`, `AXS-EXT-024`, `AXS-EXT-042`, `AXS-EXT-050`)
- `spec/requirements/OWNER.md` (`REQ-OWNER-007`)
- `spec/requirements/CATALOG.md` (`REQ-SIMD-085..086`, `REQ-SIMD-100..106`, `REQ-SIMD-118`, `REQ-SIMD-141..144`, `REQ-SIMD-156`, `REQ-SIMD-211`)
