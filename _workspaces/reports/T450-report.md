# T450 Report — Canonical Integer Model, 128-Bit Arithmetic & Conversion Specification (`SPEC-40`)

## Tóm tắt

Hoàn thành đặc tả chuẩn tắc `spec/SPEC-40-integers.md` cho phân hệ `E12.1` (Phase `P12`), quy định toàn bộ mô hình 12 kiểu số nguyên vô hướng (`i8`, `i16`, `i32`, `i64`, `i128`, `isize`, `u8`, `u16`, `u32`, `u64`, `u128`, `usize`). Tài liệu chốt biểu diễn bù hai 16 byte của `i128`/`u128` (`TypeKind.Int128`, `ConstValue.Int128`), quy ước hạ cấp cặp thanh ghi 64-bit `(lo: Gpr, hi: Gpr)` ở tầng LIR cùng hợp đồng ABI Windows x64 (`T453`), 5 họ phép toán số học tường minh (mặc định kiểm tra tràn, `wrapping_*`, `saturating_*` hạ cấp trực tiếp xuống `MirBinOp.SatAdd`/`SatSub`/`SatMul`, `checked_*` trả về `Option<Self>`, và `overflowing_*` trả về `(Self, bool)`), bộ thao tác bit và endian (`to_le_bytes`, `from_be_bytes`, `swap_bytes`, `reverse_bits`, v.v.), 4 lớp chuyển đổi (`COERCION`, `CAST`, `TRY_CAST` với `From`/`TryFrom`/`TryFromIntError`, `BITCAST`), và dàn thăng cấp số nguyên đa độ rộng tất định (`REQ-OWNER-007` integer sub-lattice, Pattern D) hạ cấp thành các lệnh `MIR_RVALUE_CAST` (`IntToInt`) tường minh trước khi qua bộ kiểm chứng MIR. Đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md` (`INV-INT-001..003`), và `spec/SPEC-03-core-semantics.md`.

---

## Summary of Architectural Decisions & Deliverables

1. **Complete 12-Type Scalar Integer Model & 128-Bit Representation (`SPEC-40 §1`, `AXS-INT-001..006`)**:
   - Specified all 12 scalar integer types (`i8..i128`, `u8..u128`, `isize`, `usize`) as first-class value types (`ANUM-20`, `REQ-SIMD-085`).
   - Defined `i128` (`TY_I128 = 14`) and `u128` (`TY_U128 = 15`) with `size = 16`, `align = 16`, little-endian two's-complement limb representation `(lo: u64, hi: u64)`, associated constants (`MIN`, `MAX`, `BITS = 128u32`), 128-bit literal scanning in `axiomc` (`AX_LEX_INT_OVERFLOW` above $2^{128}-1$, `AX_TYPE_LITERAL_OUT_OF_RANGE` after unary `-` folding), `ConstValue.Int128`, and built-in marker/value traits (`Copy`, `Clone`, `Eq`, `PartialEq`, `Ord`, `Hash`, `Send`, `Share`, `Default`).
2. **LIR Register-Pair Lowering, Win64 ABI & x86-64 Codegen Contract (`SPEC-40 §2`, `AXS-INT-010..013`)**:
   - Specified atomic MIR scalar representation lowered in `compiler/lir/lower.ax` to a 64-bit GPR pair `(lo: Gpr, hi: Gpr)` (`SPEC-04 AXS-EXT-050`) and 16-byte stack slots.
   - Specified the Windows x64 calling convention (`compiler/abi/win64.ax`, `T453`) for 16-byte integers and canonical x86-64 instruction sequences (`ADD`/`ADC`, `SUB`/`SBB`, `MUL`/`IMUL` with 128-bit overflow check, `udiv128`/`sdiv128`, `SHLD`/`SHRD` shifts and rotates, `BSWAP` limb swap, `LZCNT`/`TZCNT`/`POPCNT`, and branchless `CMOVcc` saturation).
   - Specified SIMD lane overflow coherence (`ANUM-36`, `REQ-SIMD-101`): SIMD never silently weakens scalar checked overflow semantics.
3. **Five Explicit Integer Arithmetic Families (`SPEC-40 §3`, `AXS-INT-020..026`)**:
   - Specified default checked operators (`+`, `-`, `*`, `/`, `%`, unary `-`, `<<`, `>>`), `wrapping_*` (`ANUM-38`, `REQ-SIMD-103`), `saturating_*` (`ANUM-37`, `REQ-SIMD-102`, lowering `saturating_add`/`sub`/`mul` directly to `MirBinOp.SatAdd`/`SatSub`/`SatMul`), `checked_*` returning `Option<Self>` (`ANUM-39`, `REQ-SIMD-104`), and `overflowing_*` returning `(Self, bool)`.
4. **Bit Manipulation & Endian Byte Array Conversions (`SPEC-40 §4`, `AXS-INT-030..033`)**:
   - Specified `&`, `|`, `^`, `~` (`ANUM-40`, `REQ-SIMD-105`), bit intrinsics/methods (`count_ones`, `count_zeros`, `leading_zeros`, `trailing_zeros`, `leading_ones`, `trailing_ones`, `rotate_left`, `rotate_right`, `swap_bytes`, `reverse_bits`, `is_power_of_two`, `next_power_of_two`, `checked_next_power_of_two`), fixed-size endian byte conversions (`to_le_bytes`, `from_le_bytes`, `to_be_bytes`, `from_be_bytes`, `to_ne_bytes`, `from_ne_bytes`), and `std.text.fmt.int` 128-bit formatting/parsing.
5. **Four Conversion Classes (`COERCION`, `CAST`, `TRY_CAST`, `BITCAST`) (`SPEC-40 §5`, `AXS-INT-040..044`)**:
   - Partitioned conversions into `COERCION`, `CAST` (`as` lowered to `MIR_CAST_INT_TO_INT`), `TRY_CAST` (`From`/`Into` lossless widening matrix and `TryFrom`/`TryInto` with `TryFromIntError` in `std.core.convert`), and `BITCAST` (`ANUM-41`, `ANUM-91`, `REQ-SIMD-106`, `REQ-SIMD-156`).
6. **`REQ-OWNER-007` Multi-Width Integer Expression Promotion Sub-Lattice (`SPEC-40 §6`, `AXS-INT-050..054`)**:
   - Defined the deterministic pure-integer promotion join $\text{join}_{\text{int}}(T_1, T_2)$, contextual propagation into narrow sub-expressions with `IntVar` literals (preventing premature `u8` overflow on `b8 * 2` in Pattern D `let total: i64 = (s64 + s32 * 3) - (u16v + b8 * 2 + s8 - 7) / (4 - s8) == 93985`), array-index expression promotion to `usize`, preservation of standalone `AX_TYPE_MISMATCH` on direct bindings/assignments/returns/arguments and same-width signed/unsigned mixing, and explicit `MIR_RVALUE_CAST` (`IntToInt`) materialization before `compiler/verify/verifier.ax`.
7. **Cross-Spec Integration (`INDEX.md`, `diagnostics.md`, `invariants.md`, `SPEC-03`)**:
   - Registered `SPEC-40` and `AXS-INT-NNN` in `spec/INDEX.md`.
   - Updated `spec/diagnostics.md` for 128-bit literal and constant evaluation diagnostics.
   - Added group `INT` and invariants `INV-INT-001`, `INV-INT-002`, `INV-INT-003` to `spec/invariants.md`.
   - Cross-referenced `spec/SPEC-40-integers.md` in `spec/SPEC-03-core-semantics.md` (`AXS-SEM-010`, `AXS-SEM-022`, `AXS-SEM-031`, `AXS-SEM-061`).

---

## Files changed

- `spec/SPEC-40-integers.md` (created)
- `spec/INDEX.md` (updated)
- `spec/diagnostics.md` (updated)
- `spec/invariants.md` (updated)
- `spec/SPEC-03-core-semantics.md` (updated)

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python tools/gatecheck.py --no-run` → `GATE PASS`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T450` → `0 REFUSED`

STATUS: COMPLETE
