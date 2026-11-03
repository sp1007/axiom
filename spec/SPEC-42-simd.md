# SPEC-42 — Canonical Portable SIMD, Mask Semantics & Data-Oriented Tensor/Matrix View Specification

Status: draft (T463, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0095 §1–43 (ASIMD-01..20)`; `tasks/0337 §1–100 (ASIMD-20..100)`; `tasks/0341 §1–100 (ANUM-20..100)`; `tasks/0344 §1–100 (ASIMD-20..100)`; `tasks/0347 §1–100 (ASIMD-20..100)`; `tasks/0403 §1–82 (ASIMD-20..80)`; `tasks/0426 §1–85 (AITER-20..75)`; `tasks/0427 §27–100 (ANUM-42..52)`; `tasks/0472 §213.8–12, §213.99 (AHW-27..32)`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`.
Covers: `REQ-SIMD-001`, `REQ-SIMD-002`, `REQ-SIMD-003`, `REQ-SIMD-004`, `REQ-SIMD-005`, `REQ-SIMD-006`, `REQ-SIMD-007`, `REQ-SIMD-008`, `REQ-SIMD-086`, `REQ-SIMD-087`, `REQ-SIMD-088`, `REQ-SIMD-089`, `REQ-SIMD-090`, `REQ-SIMD-091`, `REQ-SIMD-092`, `REQ-SIMD-096`, `REQ-SIMD-097`, `REQ-SIMD-166`, `REQ-SIMD-167`, `REQ-SIMD-168`, `REQ-SIMD-171`, `REQ-SIMD-333`.
Consumers: `compiler/types/types.ax`, `compiler/types/layout.ax`, `compiler/types/typeck.ax`, `compiler/hir/`, `compiler/mir/mir.ax`, `compiler/mir/builder.ax`, `compiler/verify/verifier.ax`, `compiler/interp/`, `compiler/opt/const_fold.ax`, `std/simd/mod.ax`, `std/simd/tensor.ax`, `std/simd/matrix.ax`, `T464`–`T468`, `E12.4` (`SPEC-43`, `T469`–`T474`), `E12.5` (`SPEC-44`, `T475`–`T479`).

## Tóm tắt

Tài liệu `SPEC-42` quy định chuẩn tắc mô hình vector SIMD khả chuyển (`Vector<T, N>` và `Mask<N>`), ngữ nghĩa phép toán theo làn (lane-wise operations), phép thu gọn ngang (horizontal reductions), truy cập bộ nhớ có mặt nạ và thu/phát (`load_masked`, `store_masked`, `gather`, `scatter`), cùng các cấu trúc dữ liệu hướng mảng/tensor (`TensorView<T, R>`, `TensorMutView<T, R>`, `MatrixView<T>`, `Vec2..4<T>`, `Mat2..4<T>`) cho phân hệ `E12.3` (Phase `P12`). Các quyết định kiến trúc cốt lõi gồm:
- **Mô hình vector ngữ nghĩa độc lập phần cứng (`ANUM-21..27`, `ASIMD-20..25`, `REQ-SIMD-001..008`, `REQ-SIMD-333`)**: `Vector<T, N>` và `Mask<N>` (`SPEC-04 AXS-EXT-020`) là các kiểu giá trị (`Copy`, phân biệt hoàn toàn với mảng cố định `[N]T`) với kiểu phần tử vô hướng `T` (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`) và số làn ngữ nghĩa `N` là lũy thừa của 2 trong `{2, 4, 8, 16, 32, 64}`. Core không gắn cứng thanh ghi vật lý (`__m128`/`__m256`) vào ngôn ngữ và giữ thiết kế mở cho các kiến trúc vector khả mở (`SVE`/`RVV`); mọi vector chưa khớp độ rộng phần cứng đều được bộ hợp thức hóa (legalizer) tách thành nhiều thanh ghi hoặc vô hướng hóa (scalarize) mà không đổi ngữ nghĩa chương trình và không cần runtime điều phối ngầm.
- **Bảo toàn ngữ nghĩa số học vô hướng trên từng làn và thu gọn tất định (`ANUM-31..45`, `ASIMD-28..43`)**: Số học nguyên trên `Vector<T, N>` kế thừa nguyên vẹn 3 họ phép toán của `SPEC-40`: mặc định kiểm tra tràn (`+`, `-`, `*`, `/`, `%`, `<<`, `>>`), `wrapping_*`, và `saturating_*`; số học dấu phẩy động tuân thủ IEEE-754 nghiêm ngặt (`SPEC-41`) trên từng làn. So sánh vector tạo `Mask<N>` (không trả về `[N]bool`); ép kiểu giá trị (`cast`) tách biệt hoàn toàn với tái diễn giải bit kiểm tra kích thước (`bitcast`). Phép thu gọn dấu phẩy động phân biệt tường minh giữa thu gọn có thứ tự trái-sang-phải tất định (`reduce_add_ordered`: `(((v[0] + v[1]) + v[2]) + ...)`) và thu gọn cây kết hợp (`reduce_add`).
- **Truy cập bộ nhớ an toàn dựa trên capability và mặt nạ (`ASIMD-34..36, 40..47`)**: Các phép nạp/lưu qua `view<[T]>`/`mut_view<[T]>` (`from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_masked`, `store_masked`, `gather`, `scatter`) kiểm tra biên đầy đủ; các làn bị tắt mặt nạ (`mask[i] == false`) **không thực hiện truy cập bộ nhớ ngữ nghĩa** (không bao giờ gây lỗi đọc/ghi ngoài biên ở làn không hoạt động), và `scatter` quy định thứ tự ghi làn tăng dần tất định khi trùng chỉ số đích.
- **Thư viện `TensorView`/`TensorMutView`/`MatrixView` không chi phí ẩn (`ANUM-64..95`, `ASIMD-83..96`)**: Tensor và ma trận là trừu tượng thư viện trong `std.simd` xây dựng trên một capability phẳng duy nhất (`data: view<[T]>` hoặc `mut_view<[T]>`) kết hợp siêu dữ liệu `shape: [R]usize` và `strides: [R]isize` (không dùng view lồng nhau, không cấp phát heap ngầm, không phụ thuộc BLAS/runtime ngoài), bảo đảm tính độc quyền `mut_view` và cấm `broadcast` tạo vùng ghi chồng lấn.

---

## 1. Portable SIMD Type Model: `Vector<T, N>` and `Mask<N>` (`AXS-SIMD-001`..`008`)

### AXS-SIMD-001 — Target-Independent Semantic Vector & Mask Model (`REQ-SIMD-001`..`008`, `REQ-SIMD-086`..`092`, `REQ-SIMD-166`..`171`, `REQ-SIMD-333`, `SPEC-04 AXS-EXT-020`)

1. **Semantic abstraction, not hardware registers**: `Vector<T, N>` (`TypeKind.Vector`) and `Mask<N>` (`TypeKind.Mask`) represent target-independent semantic $N$-lane data-parallel values. Core language semantics never expose ISA-specific register types (such as x86 `__m128`/`__m256`/`__m512`, ARM `float32x4_t`, or predicate register types `__mmask8`/`__mmask16`); architecture-specific intrinsics and register aliases belong exclusively to `std.arch.*` (`E12.4`/`E12.5`, `ANUM-28`, `ASIMD-26`).
2. **Independence of semantic lane count and physical register width (`ANUM-23..26`, `ASIMD-20..24`)**: The lane count $N$ of `Vector<T, N>` and `Mask<N>` is a semantic property of the type, not a guarantee that the value resides in a single hardware vector register of bit width $N \cdot \text{bits}(T)$:
   - A backend may keep `Vector<T, N>` in a single native vector register (e.g., `Vector<f32, 4>` in `XMM` on SSE2, `Vector<f32, 8>` in `YMM` on AVX2), split a wider vector across multiple registers (e.g., `Vector<f32, 8>` into two `XMM` registers on baseline SSE2, or `Vector<i64, 64>` into multiple vector chunks), pack narrower vectors, or scalarize any vector operation into a deterministic scalar sequence when the target lacks a direct instruction (`SPEC-43`).
   - Every legal target lowering must produce observable results identical to the lane-by-lane reference semantics defined in this specification (`INV-ORACLE-002`).
3. **Zero mandatory runtime or dispatch (`ANUM-27, 61, 63, 95`, `ASIMD-75..78, 99`)**: Using `Vector<T, N>` or `Mask<N>` never introduces heap allocation, object headers, reference counting, dynamic trait dispatch, runtime type descriptors, or implicit runtime CPU feature probing. Portable SIMD compiles directly to target instructions for the active target feature set; function multiversioning (`@multiversion`) and runtime feature detection (`std.arch.is_x86_feature_detected`) are explicit facilities specified in `SPEC-44` (`E12.5`).
4. **Bootstrap boundary (`SPEC-04 AXS-EXT-010, 020`)**: In the frozen C Stage-0 bootstrap compiler (`bootstrap/axiom0`), `TypeKind.Vector` and `TypeKind.Mask` are reserved enum variants rejected with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`data.construct = "Vector" | "Mask"`, `data.epic = "E12.3"`). In self-hosted `axiomc` (`T464`+), `TypeKind.Vector` and `TypeKind.Mask` are first-class compiler-known types surfaced through `std.simd`.
[0095 §1–5, §42 ASIMD-01..05; tasks/0337 §100 ASIMD-20..28; tasks/0341 §100 ANUM-21..27; tasks/0344 §100 ASIMD-20..25; tasks/0347 §100 ASIMD-20..29; tasks/0403 §82 ASIMD-20..27, 75..78; tasks/0472 §213.8–9, §213.99 AHW-20, AHW-27..28; SPEC-04 AXS-EXT-020]

### AXS-SIMD-002 — Supported Scalar Element Types `T` (`SimdElement`) & Semantic Lane Counts `N` (`T464`)

1. **Closed set of portable vector element types (`SimdElement`)**: A fixed-width portable vector `Vector<T, N>` requires its element type `T` to implement the sealed compiler-known marker trait `std.simd.SimdElement`. Exactly twelve primitive scalar numeric types satisfy `SimdElement`:
   - Signed two's-complement integers (`SPEC-40`): `i8`, `i16`, `i32`, `i64`, `isize`.
   - Unsigned binary integers (`SPEC-40`): `u8`, `u16`, `u32`, `u64`, `usize`.
   - IEEE-754 binary floating-point types (`SPEC-41`): `f32`, `f64`.
   - Note: `bool` is **not** a valid `Vector<T, N>` element type (boolean lane predicates are represented by `Mask<N>`, `AXS-SIMD-003`); `i128`, `u128`, `char`, `Str`, tuples, arrays, structs, enums, `view`/`mut_view`, and raw pointers are not valid `SimdElement` types in `v1`. Instantiating `Vector<T, N>` with any non-`SimdElement` concrete type `T` is rejected at compile time by `compiler/types/typeck.ax` with `AX_SIMD_INVALID_ELEMENT` (`data.elem = "<T>"`).
2. **Supported semantic lane counts $N$**: Both `Vector<T, N>` and `Mask<N>` require the lane count $N$ to be a compile-time constant power of two in the closed set:
   $$N \in \{2, 4, 8, 16, 32, 64\}$$
   - Single-lane $N = 1$ is rejected (scalar types `T` and `bool` are used directly, `ANUM-20`), $N = 0$ is rejected, non-powers of two (such as $3, 5, 6, 7, 12$) are rejected, and $N > 64$ is rejected.
   - Any instantiation of `Vector<T, N>` or `Mask<N>` whose resolved lane count $N \notin \{2, 4, 8, 16, 32, 64\}$ is rejected at compile time with `AX_SIMD_INVALID_LANES` (`data.lanes = N`).
3. **Type identity (`INV-KERN-004`)**: In `compiler/types/types.ax`, `TypeKind.Vector { elem: TypeId, lanes: u32 }` and `TypeKind.Mask { lanes: u32 }` are hash-consed in `TypeInterner`. Two vector types are equal if and only if they have the exact same `elem` `TypeId` (`i64` and `isize` remain distinct nominal types, as do `u64` and `usize`, per `SPEC-40 AXS-INT-001`) and the same `lanes` count $N$. Two mask types `Mask<N>` and `Mask<M>` are equal if and only if $N = M$.
[tasks/0337 §99–100 ASIMD-22..24; tasks/0341 §100 ANUM-20..23; tasks/0347 §100 ASIMD-22, 27; tasks/0403 §8, §82 ASIMD-23]

### AXS-SIMD-003 — Value Semantics, Traits & Distinction from Fixed Arrays `[N]T` (`ANUM-21..22`, `ASIMD-20..26`, `REQ-SIMD-003`..`006`, `REQ-SIMD-086`..`087`, `REQ-SIMD-166`..`167`)

1. **Pure value semantics**: Every `Vector<T, N>` and `Mask<N>` is a first-class value type that automatically implements:
   - `Copy` and `Clone` (bitwise value copy, no custom `Drop` implementation permitted);
   - `PartialEq` (`a == b` and `a != b` return a scalar `bool` indicating whether all $N$ lanes are equal; for `Vector<f32, N>` and `Vector<f64, N>`, `a == b` is `a.simd_eq(b).all()`, so any `NaN` lane yields `a == b == false` and `a != b == true`, matching scalar IEEE-754 `PartialEq` in `SPEC-41 AXS-FLT-020`);
   - `Eq` and `Hash` for integer `Vector<T, N>` and for `Mask<N>` (floating-point vectors implement `PartialEq` but not `Eq`, matching `f32`/`f64`);
   - `Default` (`Vector<T, N>.default()` is `Vector.splat(T.default())` = all-zero lanes; `Mask<N>.default()` is `Mask.splat(false)` = all-false lanes);
   - `Send` and `Share` (`SPEC-30 AXS-CONC-010`: pure value types with no interior mutability or thread-local state).
2. **Strict distinction from fixed arrays `[N]T` and `[N]bool` (`ANUM-22`, `ASIMD-21, 25, 35`)**:
   - `Vector<T, N>` is a distinct type from `[N]T`; neither coerces implicitly to the other (`let a: [4]f32 = v_f32x4` is rejected with `AX_TYPE_MISMATCH`). Explicit lossless conversions are provided via `Vector.from_array(arr: [N]T) -> Vector<T, N>` and `v.to_array() -> [N]T`.
   - `Mask<N>` is a distinct semantic predicate type from `[N]bool`, from `Vector<u8, N>`, and from scalar `bool` (`ASIMD-33, 35`). A `Mask<N>` cannot be used directly as the condition of an `if` or `while` statement (`if m { ... }` where `m: Mask<4>` is rejected with `AX_TYPE_MISMATCH`; the programmer must write `if m.all() { ... }` or `if m.any() { ... }`).
   - Unlike `[N]T`, individual lanes of a `Vector<T, N>` or `Mask<N>` are **not** addressable memory places: taking a capability view or raw pointer to a single lane (`view(v[0])`, `mut_view(v[i])`, or `address_of(v[i])`) is rejected because vector lanes may reside in packed SIMD or predicate registers without per-lane byte addresses (`ASIMD-24, 36`). Reading or updating a lane uses value-returning `v.extract(idx)` and `v.insert(idx, val)` (`AXS-SIMD-011`).
[tasks/0337 §100 ASIMD-22..23, 32..33; tasks/0341 §33, §100 ANUM-21..22, 31..32; tasks/0344 §16, §100 ASIMD-20..21, 32..33; tasks/0347 §100 ASIMD-21, 25..26, 34..36]

### AXS-SIMD-004 — Size, Alignment & In-Memory Lane Layout (`ASIMD-44..45, 65`, `T464`)

When a `Vector<T, N>` or `Mask<N>` is materialized in memory (inside a stack slot, `struct`, `enum`, array, or constant pool), `compiler/types/layout.ax` assigns the following deterministic layout:

1. **`Vector<T, N>` size and alignment**:
   - `size_of<Vector<T, N>>() == N * size_of<T>()` (ranging from $2 \times 1 = 2$ bytes for `Vector<u8, 2>` up to $64 \times 8 = 512$ bytes for `Vector<f64, 64>`).
   - `align_of<Vector<T, N>>() == min(N * size_of<T>(), 32)` on `x86_64-pc-windows-msvc` (i.e., natural power-of-two byte size capped at 32 bytes so 128-bit vectors have 16-byte alignment, 256-bit and wider vectors have 32-byte alignment compatible with AVX2 `VMOVDQA`/`VMOVAPS` and Win64 stack frame alignment, while smaller vectors such as `Vector<u8, 2>`, `Vector<i16, 2>`, `Vector<f32, 2>` have alignments 2, 4, 8 respectively). An explicit `@align(64)` attribute on an enclosing struct can raise storage alignment further (`ASIMD-45`).
2. **In-memory lane order (`ASIMD-65`)**:
   - When stored to or loaded from contiguous memory, lane $i \in [0, N - 1]$ of `Vector<T, N>` occupies byte offset $[i \cdot \text{size\_of}(T),\; (i + 1) \cdot \text{size\_of}(T))$ in little-endian element byte order, matching the element layout of `[N]T`.
   - Consequently, `v.to_array()[i] == v.extract(i)` and `Vector.from_array(arr).extract(i) == arr[i]` for all $0 \le i < N$.
3. **`Mask<N>` size, alignment, and canonical memory representation (`REQ-SIMD-006`, `ASIMD-36`)**:
   - While in registers, `Mask<N>` may be represented by the backend as a wide lane mask (`XMM`/`YMM` all-ones `0xFF..FF` vs all-zeros `0x00..00` per lane on SSE2/AVX2) or a compact hardware predicate register (`k0`–`k7` bitmask on AVX-512).
   - When materialized in memory or inspected via `size_of<Mask<N>>()` / `align_of<Mask<N>>()`, `Mask<N>` has canonical layout equivalent to `[N]bool`: `size_of<Mask<N>>() == N` bytes and `align_of<Mask<N>>() == min(N, 16)` bytes, where byte $i \in [0, N - 1]$ is `1u8` (`true`) or `0u8` (`false`).
   - `Mask<N>` is not legal in `simd_bitcast` (`AXS-SIMD-025`) because its in-register hardware representation is target-dependent (`ASIMD-33, 36`); converting a mask to integer bits uses `m.bitmask() -> u64` (`AXS-SIMD-031`) or `m.to_int_mask<I>() -> Vector<I, N>`.
[tasks/0337 §29, §100 ASIMD-33, 60; tasks/0341 §22, §100 ANUM-58; tasks/0344 §31–32, §100 ASIMD-44..45, 65; tasks/0347 §100 ASIMD-36, 41..42]

### AXS-SIMD-005 — Standard Fixed-Width `std.simd` Type Aliases (`T466`)

`std.simd` (`std/simd/mod.ax`) defines the canonical fixed-width vector and mask type aliases over `Vector<T, N>` and `Mask<N>`:

| Category | 128-bit / Standard Aliases | 256-bit / Wide Aliases |
|---|---|---|
| Signed integer vectors | `pub type i8x16 = Vector<i8, 16>`, `pub type i16x8 = Vector<i16, 8>`, `pub type i32x4 = Vector<i32, 4>`, `pub type i64x2 = Vector<i64, 2>` | `pub type i8x32 = Vector<i8, 32>`, `pub type i16x16 = Vector<i16, 16>`, `pub type i32x8 = Vector<i32, 8>`, `pub type i64x4 = Vector<i64, 4>` |
| Unsigned integer vectors | `pub type u8x16 = Vector<u8, 16>`, `pub type u16x8 = Vector<u16, 8>`, `pub type u32x4 = Vector<u32, 4>`, `pub type u64x2 = Vector<u64, 2>` | `pub type u8x32 = Vector<u8, 32>`, `pub type u16x16 = Vector<u16, 16>`, `pub type u32x8 = Vector<u32, 8>`, `pub type u64x4 = Vector<u64, 4>` |
| Floating-point vectors | `pub type f32x4 = Vector<f32, 4>`, `pub type f64x2 = Vector<f64, 2>` | `pub type f32x8 = Vector<f32, 8>`, `pub type f64x4 = Vector<f64, 4>` |
| Lane masks | `pub type mask8x16 = Mask<16>`, `pub type mask16x8 = Mask<8>`, `pub type mask32x4 = Mask<4>`, `pub type mask64x2 = Mask<2>` | `pub type mask8x32 = Mask<32>`, `pub type mask16x16 = Mask<16>`, `pub type mask32x8 = Mask<8>`, `pub type mask64x4 = Mask<4>` |

All aliases above are pure type aliases (`TypeAlias`) for `Vector<T, N>` and `Mask<N>`, not distinct nominal types (`tasks/0427 §27–28`).

### AXS-SIMD-006 — Scalable Vector Model Reservation (`REQ-SIMD-005`, `REQ-SIMD-333`, `AHW-27..28`)

1. **No fixed register width baked into Core**: Core language rules and MIR vector rvalues (`VectorOp`, `Splat`, `Reduce`) parameterize vector operations by semantic lane structure rather than assuming fixed 128-bit or 256-bit hardware registers (`REQ-SIMD-001..005`, `REQ-SIMD-333`).
2. **Scalable vector extensibility (`tasks/0403 §10, ASIMD-24`, `tasks/0472 §213.8–9, AHW-27..28`)**: For target architectures with hardware-variable vector length (`vscale`, such as ARM64 SVE/SVE2 and RISC-V RVV in `Phase 16`), the type model reserves `ScalableVector<T, MIN_LANES>` and `ScalableMask<MIN_LANES>` whose runtime lane count is $vscale \times \text{MIN\_LANES}$ queried via `std.simd.vscale()` and processed through strip-mined loop predication (`while_lt(idx, len) -> ScalableMask<MIN_LANES>`) without changing any Core syntax or fixed-width `Vector<T, N>` semantics. On fixed-width targets (`x86_64-windows`), `vscale() == 1`.
[tasks/0403 §9–11, §82 ASIMD-23..24; tasks/0472 §213.8–9, §213.99 AHW-27..28]

### AXS-SIMD-007 — `ConstValue.Vector` & Compile-Time SIMD Evaluation (`SPEC-04 AXS-EXT-024`, `T464`, `T465`)

1. **`ConstValue.Vector` representation**: In `compiler/types/types.ax` and `compiler/mir/mir.ax`, compile-time constant vectors and masks are represented by `CONST_VECTOR` / `MIR_CONST_VECTOR` (`SPEC-04 AXS-EXT-024`) storing the resolved `ty: TypeId` (`TypeKind.Vector` or `TypeKind.Mask`), lane count `lanes: u32`, and the packed lane array of `N` scalar constant values (`u64` bit patterns per lane).
2. **Compile-time evaluation parity (`T465`)**: Every pure operation on `Vector<T, N>` and `Mask<N>` (`splat`, `from_array`, `to_array`, `extract`, `insert`, `shuffle`, lane-wise arithmetic, bitwise/shift ops, comparisons, `select`, `cast`, `bitcast`, and horizontal reductions) is evaluable in `const` items and folded by `compiler/opt/const_fold.ax` at `-O1`+ using the exact same lane-by-lane evaluator as `--interp`:
   - Compile-time integer overflow in default checked vector operators (`+`, `-`, `*`, `/`, `%`, unary `-`) emits `AX_CONST_OVERFLOW` (`96u32`).
   - Compile-time integer division or remainder by zero in any lane emits `AX_CONST_DIV_ZERO` (`97u32`).
   - Compile-time out-of-range shift in any lane emits `AX_CONST_SHIFT_RANGE` (`SPEC-40 AXS-INT-005`).

### AXS-SIMD-008 — Non-Synchronizing, Non-Atomic Ordinary Memory Semantics (`ANUM-46..50`, `ASIMD-48..50, 58..61`)

1. **No implicit atomicity or synchronization**: Executing a SIMD load, store, arithmetic operation, or reduction does **not** imply memory atomicity, inter-thread synchronization, or a `Happens-Before` edge, even when a target lowers a 128-bit or 256-bit load/store to a single machine instruction (`ANUM-47..48`, `ASIMD-48`).
2. **Concurrency verifier participation**: `Vector<T, N>` and `Mask<N>` places and slice views (`view<[T]>`, `mut_view<[T]>`) participate in the `SPEC-30` compile-time data-race verifier under the ordinary rules: concurrent unsynchronized `READ`/`WRITE` or `WRITE`/`WRITE` across threads is rejected with `AX_CONC_SHARED_MUT`.
3. **Preservation of `Atomic<T>` and `Volatile<T>` (`ASIMD-59..61`)**: Neither portable SIMD nor auto-vectorization may coalesce, widen, reorder, or convert `Atomic<T>` (`SPEC-31`) or `Volatile<T>` / `Mmio<T>` (`SPEC-50`) accesses into ordinary SIMD memory operations.

---

## 2. Lane Construction, Extraction, Insertion & Permutation (`AXS-SIMD-010`..`013`)

### AXS-SIMD-010 — Explicit Broadcast (`splat`) & Array Conversions (`from_array`, `to_array`) (`ANUM-33`, `REQ-SIMD-098`)

1. **No implicit scalar-to-vector broadcast (`ANUM-33`, `REQ-SIMD-098`)**: A scalar value `s: T` never coerces or promotes implicitly to `Vector<T, N>` in binary expressions, bindings, or calls (`v + 1` or `v + 1.0f32` where `v: Vector<f32, 4>` is rejected with `AX_TYPE_MISMATCH` / `AX_TYPE_OPERATOR`). Broadcasting a scalar across all $N$ lanes is always explicit via `Vector.splat(value: T) -> Vector<T, N>` (or `Mask.splat(value: bool) -> Mask<N>`):
   $$\text{splat}(x)[i] = x \quad \text{for all } 0 \le i < N$$
2. **Array conversions**:
   - `Vector<T, N>.from_array(arr: [N]T) -> Vector<T, N>`: constructs a vector where lane $i$ equals `arr[i]`.
   - `v.to_array(self: Vector<T, N>) -> [N]T`: returns a fixed array `[N]T` where element $i$ equals lane $i$ of `v`.
   - `Mask<N>.from_array(arr: [N]bool) -> Mask<N>` and `m.to_array(self: Mask<N>) -> [N]bool`: convert losslessly between `Mask<N>` and `[N]bool`.
   - `Vector<T, N>.lanes() -> usize` and `Mask<N>.lanes() -> usize`: return the compile-time lane count $N$.

### AXS-SIMD-011 — Explicit Lane Extraction (`extract`) & Lane Insertion (`insert`) (`ANUM-34`, `REQ-SIMD-099`)

1. **Extraction (`extract`)**:
   - `v.extract(self: Vector<T, N>, idx: usize) -> T` (and `@intrinsic fn simd_extract<T, N>(v: Vector<T, N>, idx: usize) -> T`) returns the scalar value of lane `idx`.
   - `m.test(self: Mask<N>, idx: usize) -> bool` (alias `m.extract(idx)`) returns the boolean predicate of lane `idx`.
2. **Insertion (`insert` / `replace`)**:
   - `v.insert(self: Vector<T, N>, idx: usize, val: T) -> Vector<T, N>` (and `@intrinsic fn simd_insert<T, N>(v: Vector<T, N>, idx: usize, val: T) -> Vector<T, N>`) returns a new `Vector<T, N>` equal to `v` at every lane $j \ne \text{idx}$ and equal to `val` at lane `idx`.
   - `m.set(self: Mask<N>, idx: usize, val: bool) -> Mask<N>` (alias `m.insert(idx, val)`) returns a new `Mask<N>` with lane `idx` updated to `val`.
3. **Bounds verification on lane indices (`T464`, `T465`, `ASIMD-54..55`)**:
   - When `idx` is a compile-time constant expression (or literal) in `simd_extract`/`simd_insert`/`extract`/`insert` and `idx >= N`, `compiler/types/typeck.ax` and `compiler/verify/verifier.ax` reject the program at compile time with `AX_SIMD_LANE_OUT_OF_RANGE` (`data.index = idx`, `data.lanes = N`).
   - When `idx` is a dynamic runtime `usize` value, if `idx >= N` at runtime, execution traps deterministically with a bounds-check panic (`SPEC-03 AXS-SEM-041`, exit code `101`, message `"index out of bounds"`), identical in `--interp` and native codegen.

### AXS-SIMD-012 — Two-Vector Compile-Time Permutation (`shuffle`, `interleave_lo`, `interleave_hi`, `reverse`, `rotate_lanes_left`, `rotate_lanes_right`) (`ASIMD-53..55, 66..67`, `T464`, `T466`)

1. **General two-vector shuffle (`simd_shuffle` / `Vector.shuffle`)**:
   - Signature: `pub fn shuffle<T, N, M>(a: Vector<T, N>, b: Vector<T, N>, indices: [M]u32) -> Vector<T, M>` (backed by `@intrinsic fn simd_shuffle<T, N, M>(a: Vector<T, N>, b: Vector<T, N>, indices: [M]u32) -> Vector<T, M>`), where $N, M \in \{2, 4, 8, 16, 32, 64\}$.
   - Semantics: Concatenates the $N$ lanes of `a` (indexed $0 .. N - 1$) and the $N$ lanes of `b` (indexed $N .. 2N - 1$) into a $2N$-lane conceptual sequence $C$:
     $$C[k] = \begin{cases} a[k] & \text{if } 0 \le k < N \\ b[k - N] & \text{if } N \le k < 2N \end{cases}$$
     and produces a result `out: Vector<T, M>` where:
     $$\text{out}[j] = C[\text{indices}[j]] \quad \text{for all } 0 \le j < M$$
   - Compile-time index obligation: `indices` must be a compile-time constant array (`[M]u32`) in `simd_shuffle`, and every selector `indices[j]` must satisfy $0 \le \text{indices}[j] < 2N$. If `indices` is not a compile-time constant or any `indices[j] >= 2 * N`, `typeck` and `verifier` emit `AX_SIMD_SHUFFLE_OUT_OF_RANGE` (`data.index = indices[j]`, `data.max_index = 2 * N - 1`).
2. **Single-vector swizzle (`swizzle`)**:
   - `v.swizzle<M>(self: Vector<T, N>, indices: [M]u32) -> Vector<T, M>` is defined as `Vector.shuffle(self, self, indices)` where every selector satisfies $0 \le \text{indices}[j] < N$ (otherwise `AX_SIMD_SHUFFLE_OUT_OF_RANGE`).
3. **Standard structured permutations (`std.simd`, `T466`)**:
   - `v.interleave_lo(self: Vector<T, N>, other: Vector<T, N>) -> Vector<T, N>`: interleaves the lower $N/2$ lanes of `self` and `other`: $[a_0, b_0, a_1, b_1, \dots, a_{N/2-1}, b_{N/2-1}]$.
   - `v.interleave_hi(self: Vector<T, N>, other: Vector<T, N>) -> Vector<T, N>`: interleaves the upper $N/2$ lanes of `self` and `other`: $[a_{N/2}, b_{N/2}, \dots, a_{N-1}, b_{N-1}]$.
   - `v.deinterleave(self: Vector<T, N>, other: Vector<T, N>) -> (Vector<T, N>, Vector<T, N>)`: returns `(even_lanes, odd_lanes)` across `(self, other)`: `even_lanes` $= [a_0, a_2, \dots, b_0, b_2, \dots]$ and `odd_lanes` $= [a_1, a_3, \dots, b_1, b_3, \dots]$.
   - `v.reverse(self: Vector<T, N>) -> Vector<T, N>`: reverses lane order $[a_{N-1}, a_{N-2}, \dots, a_0]$.
   - `v.rotate_lanes_left<const K: u32>(self: Vector<T, N>) -> Vector<T, N>` and `v.rotate_lanes_right<const K: u32>(self: Vector<T, N>) -> Vector<T, N>`: cyclically shifts lanes by $K \bmod N$.

### AXS-SIMD-013 — Contiguous Slice Chunk Iteration (`simd_chunks`, `REQ-SIMD-328`)

`std.simd` provides zero-allocation chunking helpers over `view<[T]>` and `mut_view<[T]>` (`tasks/0403 §11`, `tasks/0426 §85 AITER-47..48, 60`):
- `pub fn as_simd_chunks<T, N>(slice: view<[T]>) -> (usize, view<[T]>, view<[T]>)`: partitions `slice` of length $L$ into $Q = L / N$ full $N$-lane chunks `head = slice[0 .. Q * N]` and a scalar remainder `tail = slice[Q * N .. L]` of length $L \bmod N < N$.
- Because `view<[T]>` and `mut_view<[T]>` expose contiguous unit-stride layout (`stride == 1`) and proven capability disjointness (`SPEC-71 AXS-ALIAS-002`), loops over `0..Q` loading `Vector<T, N>.from_slice(head[c * N .. (c + 1) * N])` allow `SPEC-72` Bounds-Check Elimination (`BCE`) to discharge inner slice bounds checks statically.

---

## 3. Lane-Wise Arithmetic, Bitwise, Shift & Math Operations (`AXS-SIMD-020`..`025`)

### AXS-SIMD-020 — Lane-Wise Execution Principle & Homogeneous Vector Operands (`ANUM-35`, `ASIMD-28..30`, `REQ-SIMD-007`)

1. **Semantic equivalence to lane-wise scalar evaluation (`REQ-SIMD-007`, `ANUM-35`, `ASIMD-29..30`)**: For every unary operator $\Diamond$ and binary operator $\oplus$ defined on `Vector<T, N>`, applying the operator to vectors `a, b: Vector<T, N>` is semantically defined as applying the corresponding scalar operator (`SPEC-40` for integers, `SPEC-41` for floats) independently to each lane $i \in [0, N - 1]$:
   $$(\Diamond a)[i] = \Diamond(a[i]), \qquad (a \oplus b)[i] = a[i] \oplus b[i]$$
2. **Homogeneous vector operands (no implicit cross-lane or cross-element promotion)**: Binary operators on `Vector<T, N>` require both operands to have the exact same type `Vector<T, N>` (same `T` and same `N`). Unlike scalar mixed-type expressions (`REQ-OWNER-007` in `SPEC-41 §4`), `Vector<i16, 8> + Vector<i32, 8>`, `Vector<f32, 4> + Vector<f64, 4>`, `Vector<f32, 4> + Vector<i32, 4>`, and `Vector<f32, 4> + 1.0f32` are rejected with `AX_TYPE_MISMATCH` (`AX_TYPE_OPERATOR`): vector element widening/conversion is always explicit via `.cast<U>()` (`AXS-SIMD-025`) and scalar broadcast is always explicit via `Vector.splat(...)` (`AXS-SIMD-010`) so register width changes and lane splits are never hidden (`ANUM-33, 91`, `tasks/0344 §26`).

### AXS-SIMD-021 — Integer Vector Overflow Families: Checked Default, `wrapping_*`, `saturating_*`, `checked_*`, `overflowing_*` (`ANUM-36..39`, `ASIMD-30..33`)

For every integer element type `T` $\in \{\text{i8}, \text{i16}, \text{i32}, \text{i64}, \text{isize}, \text{u8}, \text{u16}, \text{u32}, \text{u64}, \text{usize}\}$, `Vector<T, N>` preserves Axiom's five explicit integer overflow families (`SPEC-40 AXS-INT-020..025`, `ANUM-36..39`):

1. **Default checked operators (`+`, `-`, `*`, `/`, `%`, unary `-`, `<<`, `>>`)**:
   - In `a + b`, `a - b`, `a * b`, and `-a` (for signed `T`), if **any** lane $i \in [0, N - 1]$ overflows `[T.MIN, T.MAX]`, execution panics deterministically with an integer overflow trap (`SPEC-03 AXS-SEM-030`, exit code `101`, message `"integer overflow"`).
   - In `a / b` and `a % b`, if **any** lane $i$ has `b[i] == 0`, execution panics with `"division by zero"` (exit code `101`); if `T` is signed and any lane has `a[i] == T.MIN && b[i] == -1`, execution panics with `"integer overflow"` (exit code `101`).
   - **Deterministic lane trap precedence (`T465`, `SPEC-43`)**: When a single checked vector operation encounters both division-by-zero and signed `T.MIN / -1` overflow across different lanes, lanes are checked in ascending lane index order $i = 0, 1, \dots, N - 1$, and the trap kind of the lowest-index failing lane is reported.
2. **Wrapping arithmetic (`wrapping_add`, `wrapping_sub`, `wrapping_mul`, `wrapping_neg`, `wrapping_abs`)**:
   - `a.wrapping_add(b)`, `a.wrapping_sub(b)`, `a.wrapping_mul(b)`, `a.wrapping_neg()`, `a.wrapping_abs()` compute two's-complement modulo $2^{\text{BITS}}$ results in every lane $i \in [0, N - 1]$ without trapping (`PADDB`/`PADDW`/`PADDD`/`PADDQ`, `PSUB*`, `PMULL*` on x86-64).
3. **Saturating arithmetic (`saturating_add`, `saturating_sub`, `saturating_mul`, `saturating_abs`)**:
   - `a.saturating_add(b)`, `a.saturating_sub(b)`, `a.saturating_mul(b)`, `a.saturating_abs()` clamp the exact mathematical result of each lane $i$ into $[T.\text{MIN}, T.\text{MAX}]$:
     $$\text{sat\_op}(a, b)[i] = \min(\max(\text{exact\_op}(a[i], b[i]),\, T.\text{MIN}),\, T.\text{MAX})$$
   - On x86-64 (`SPEC-43`), `i8`/`u8`/`i16`/`u16` saturating add/sub lower directly to hardware `PADDSB`/`PADDSW`/`PADDUSB`/`PADDUSW`/`PSUBSB`/`PSUBSW`/`PSUBUSB`/`PSUBUSW`, while `i32`/`u32`/`i64`/`u64` lower to branchless compare-blend or min/max sequences.
4. **Overflow-reporting methods (`overflowing_*` and `checked_*`)**:
   - `a.overflowing_add(b) -> (Vector<T, N>, Mask<N>)`, `a.overflowing_sub(b) -> (Vector<T, N>, Mask<N>)`, `a.overflowing_mul(b) -> (Vector<T, N>, Mask<N>)`: return the wrapped vector together with a `Mask<N>` whose lane $i$ is `true` if and only if lane $i$ overflowed (`tasks/0341 §32`).
   - `a.checked_add(b) -> Option<Vector<T, N>>`, `a.checked_sub(b) -> Option<Vector<T, N>>`, `a.checked_mul(b) -> Option<Vector<T, N>>`, `a.checked_div(b) -> Option<Vector<T, N>>`: return `Option.Some(res)` if and only if all $N$ lanes succeeded without overflow or zero divisor (`!ovf_mask.any()`), and `Option.None` if any lane overflowed or divided by zero.

### AXS-SIMD-022 — IEEE-754 Strict Lane-Wise Floating-Point Arithmetic & Explicit `fma` (`ANUM-43..45`, `ASIMD-41..43, 64..67`, `REQ-SIMD-108`..`110`)

For `T` $\in \{\text{f32}, \text{f64}\}$, `Vector<T, N>` follows the strict IEEE-754 binary32/binary64 contract of `SPEC-41` (`AXS-FLT-010..016`) on every lane $i \in [0, N - 1]$:

1. **Arithmetic operators (`+`, `-`, `*`, `/`, `%`, unary `-`)**:
   - `a + b`, `a - b`, `a * b`, `a / b` evaluate each lane with `roundTiesToEven`, preserving `-0.0` (`-0.0 + -0.0 == -0.0`, `x + -0.0 == x` for $x \ne -0.0$), `±inf`, gradual underflow (subnormals never flushed to zero in default strict mode), and quiet `NaN` propagation (`ADDPS`/`ADDPD`, `SUBPS`/`SUBPD`, `MULPS`/`MULPD`, `DIVPS`/`DIVPD`).
   - `a % b` computes lane-wise IEEE-754 truncated remainder `a[i] - trunc(a[i] / b[i]) * b[i]` (`SPEC-41 AXS-FLT-011`).
   - Unary `-a` flips the sign bit of every lane $i$ (`a[i] ^ SIGN_MASK`), so `-Vector.splat(0.0f32)` has `-0.0f32` in every lane.
2. **No silent FMA contraction or reassociation (`ANUM-43..45`, `ASIMD-40..43`)**:
   - Under default strict semantics, `a * b + c` on `Vector<f32, N>` or `Vector<f64, N>` performs two roundings (lane-wise multiply rounded to `T`, then lane-wise add rounded to `T`) and is **never** silently contracted into a single-rounding hardware FMA instruction.
   - Single-rounding fused multiply-add is invoked explicitly via `a.fma(b, c) -> Vector<T, N>` (or `std.simd.fma(a, b, c)`), which computes $\text{rn}(a[i] \cdot b[i] + c[i])$ with a single IEEE-754 `roundTiesToEven` rounding per lane (`SPEC-41 AXS-FLT-016, 062`).

### AXS-SIMD-023 — Bitwise & Per-Lane Shift Semantics (`&`, `|`, `^`, `~`, `<<`, `>>`, `wrapping_shl`, `wrapping_shr`) (`ANUM-40`)

For integer element types `T` $\in \{\text{i8..i64}, \text{u8..u64}, \text{isize}, \text{usize}\}$:
1. **Bitwise operators**:
   - `a & b`, `a | b`, `a ^ b`, and unary `~a` (or `!a`) operate bit-by-bit across all $N$ integer lanes (`PAND`, `POR`, `PXOR`).
   - Applying `&`, `|`, `^`, `~`, `<<`, or `>>` to `Vector<f32, N>` or `Vector<f64, N>` is rejected at compile time with `AX_TYPE_OPERATOR` (`SPEC-41 AXS-FLT-033`).
2. **Per-lane shifts (`<<`, `>>`, `wrapping_shl`, `wrapping_shr`)**:
   - `a << b` and `a >> b` take `a: Vector<T, N>` and `b: Vector<T, N>` (or scalar shift count via `a.shl_scalar(s: u32)` / `a.shr_scalar(s: u32)`):
     - `<<` performs logical left shift in each lane $i$: `a[i] << b[i]`.
     - `>>` performs arithmetic right shift for signed `T` and logical right shift for unsigned `T` in each lane $i$: `a[i] >> b[i]`.
   - **Checked shift bounds (`SPEC-03 AXS-SEM-034`, `SPEC-40 AXS-INT-021`)**: In default `a << b` and `a >> b`, if any lane $i$ has $b[i] < 0$ (for signed `T`) or $b[i] \ge T.\text{BITS}$, execution panics deterministically with a shift-range trap (`"shift count out of range"`, exit code `101`).
   - **Wrapping shifts**: `a.wrapping_shl(b: Vector<u32, N>)` and `a.wrapping_shr(b: Vector<u32, N>)` mask each lane's shift count by `b[i] & (T.BITS - 1)` without trapping.
3. **Per-lane bit manipulation helpers (`std.simd`, `T466`)**:
   - `v.rotate_left(n: Vector<u32, N>)`, `v.rotate_right(n: Vector<u32, N>)`, `v.count_ones() -> Vector<u32, N>`, `v.leading_zeros() -> Vector<u32, N>`, `v.trailing_zeros() -> Vector<u32, N>`, `v.swap_bytes() -> Vector<T, N>` apply the corresponding `SPEC-40` bit operation to each lane $i$.

### AXS-SIMD-024 — Lane-Wise `abs`, `min`, `max`, `clamp` & Pure-Axiom Vector Elementary Functions (`T466`)

1. **Integer vector `abs`, `min`, `max`, `clamp`**:
   - `v.min(other: Vector<T, N>) -> Vector<T, N>` and `v.max(other: Vector<T, N>) -> Vector<T, N>`: return lane-wise minimum and maximum (`\min(v[i], \text{other}[i])`, `\max(v[i], \text{other}[i])`).
   - `v.clamp(lo: Vector<T, N>, hi: Vector<T, N>) -> Vector<T, N>`: panics if any lane has `lo[i] > hi[i]`, otherwise returns `v.max(lo).min(hi)`.
   - For signed integer `T`: `v.abs() -> Vector<T, N>` traps on overflow if any lane is `T.MIN` (`v.wrapping_abs()` and `v.saturating_abs()` provide non-trapping variants).
2. **Floating-point vector `abs`, `copysign`, `min`, `max`, `clamp`, `sqrt`, `floor`, `ceil`, `round`, `trunc` (`SPEC-41 AXS-FLT-015, 062`)**:
   - `v.abs() -> Vector<T, N>`: clears the sign bit of every lane (`v[i] & ~SIGN_MASK`, mapping `-0.0 -> +0.0`, `-inf -> +inf`).
   - `v.copysign(sign: Vector<T, N>) -> Vector<T, N>`: copies the sign bit of `sign[i]` onto `v[i]` in every lane.
   - `v.min(other: Vector<T, N>)` and `v.max(other: Vector<T, N>)`: follow IEEE-754 `minimumNumber` / `maximumNumber` semantics (`SPEC-41 AXS-FLT-015`: if exactly one of `v[i]`, `other[i]` is `NaN`, returns the non-`NaN` operand; orders `-0.0 < +0.0`).
   - `v.sqrt()`, `v.floor()`, `v.ceil()`, `v.trunc()`, `v.round()`, `v.round_ties_even()`: apply the exact ($\le 0.5\text{ ULP}$) `SPEC-41 AXS-FLT-062` operation to each lane $i \in [0, N - 1]$.

### AXS-SIMD-025 — Numeric Lane Conversion (`cast`) vs Representation-Checked `bitcast` (`ANUM-41..42`, `ASIMD-37..38, 51..52`, `T464`)

Axiom strictly separates value-converting lane casts from bit-preserving vector reinterpretation (`ANUM-41..42`, `ASIMD-37..38`):

1. **Lane-wise numeric value conversion (`v.cast<U>()` / `simd_cast`)**:
   - Signature: `pub fn cast<U: SimdElement>(self: Vector<T, N>) -> Vector<U, N>` (backed by `@intrinsic fn simd_cast<T, U, N>(v: Vector<T, N>) -> Vector<U, N>`), requiring the **same lane count $N$** in source and target vectors.
   - Semantics: Converts each lane $i \in [0, N - 1]$ using the exact scalar `as` cast semantics of `SPEC-40 AXS-INT-041` and `SPEC-41 AXS-FLT-022..024`:
     $$\text{v.cast<U>()}[i] = (v[i] \text{ as } U)$$
     - `Int -> Int`: sign-extends or zero-extends when widening, truncates low bits when narrowing (`MIR_CAST_INT_TO_INT`).
     - `Int -> Float`: converts exact integer value to `f32`/`f64` using `roundTiesToEven` (`MIR_CAST_INT_TO_FLOAT`).
     - `Float -> Int`: truncates toward zero with **saturating** clamp (`NaN -> 0`, `>= U.MAX -> U.MAX`, `<= U.MIN -> U.MIN`, never UB or hardware `0x80000000` indefinite sentinel, `SPEC-41 AXS-FLT-022`).
     - `f32 -> f64` and `f64 -> f32`: exact widening or `roundTiesToEven` narrowing (`MIR_CAST_FLOAT_CONVERT`).
   - Attempting to call `simd_cast` between vectors of different lane counts $N \ne M$ is rejected with `AX_TYPE_MISMATCH`.
2. **Bit-preserving vector reinterpretation (`v.bitcast<U, M>()` / `simd_bitcast`)**:
   - Signature: `pub fn bitcast<U: SimdElement, const M: usize>(self: Vector<T, N>) -> Vector<U, M>` (backed by `@intrinsic fn simd_bitcast<T, N, U, M>(v: Vector<T, N>) -> Vector<U, M>`).
   - Compile-time representation invariant (`ANUM-42`, `ASIMD-38, 52`): Both source and target types must be valid `Vector` types (`SimdElement` elements, valid power-of-two lane counts $N, M \in \{2, 4, 8, 16, 32, 64\}$) with **identical total byte size**:
     $$N \cdot \text{size\_of}(T) == M \cdot \text{size\_of}(U)$$
   - If $N \cdot \text{size\_of}(T) \ne M \cdot \text{size\_of}(U)$ (for example, attempting to bitcast `Vector<f32, 4>` (16 bytes) to `Vector<f64, 4>` (32 bytes)), or if either operand is a `Mask<N>` (whose register representation is target-dependent, `AXS-SIMD-004`), `compiler/types/typeck.ax` and `compiler/verify/verifier.ax` reject the call at compile time with `AX_SIMD_BITCAST_SIZE_MISMATCH` (`data.src_size = N * size_of(T)`, `data.dst_size = M * size_of(U)`).
   - Semantics: Reinterprets the $N \cdot \text{size\_of}(T)$ little-endian bytes of `self` in memory order (`AXS-SIMD-004`) as the $M \cdot \text{size\_of}(U)$ bytes of `Vector<U, M>` with zero runtime instructions when kept in the same vector register class.

---

## 4. Lane Comparisons, Mask Algebra & Horizontal Reductions (`AXS-SIMD-030`..`033`)

### AXS-SIMD-030 — Lane-Wise Comparisons Returning `Mask<N>` (`ANUM-31..32`, `ASIMD-32..37`, `REQ-SIMD-096`..`097`)

1. **Lane-wise comparison methods (`simd_eq`, `simd_ne`, `simd_lt`, `simd_le`, `simd_gt`, `simd_ge`)**:
   - Every `Vector<T, N>` provides lane-wise comparison methods taking `(self: Vector<T, N>, other: Vector<T, N>) -> Mask<N>` (backed by `@intrinsic fn simd_eq/ne/lt/le/gt/ge<T, N>(a: Vector<T, N>, b: Vector<T, N>) -> Mask<N>`):
     - `a.simd_eq(b)[i] = (a[i] == b[i])`
     - `a.simd_ne(b)[i] = (a[i] != b[i])`
     - `a.simd_lt(b)[i] = (a[i] <  b[i])`
     - `a.simd_le(b)[i] = (a[i] <= b[i])`
     - `a.simd_gt(b)[i] = (a[i] >  b[i])`
     - `a.simd_ge(b)[i] = (a[i] >= b[i])`
2. **Distinction between `==`/`!=` (whole-vector `PartialEq`) and `simd_eq`/`simd_ne` (lane-wise `Mask<N>`)**:
   - Standard equality operators `a == b` and `a != b` implement `PartialEq` (`AXS-SIMD-003`) and return a scalar `bool` (`a.simd_eq(b).all()` and `!a.simd_eq(b).all()`) so vectors compose with generic algorithms, `assert(a == b)`, and collections.
   - Lane-wise predicate generation uses `a.simd_eq(b)`, `a.simd_ne(b)`, `a.simd_lt(b)`, `a.simd_le(b)`, `a.simd_gt(b)`, `a.simd_ge(b)` returning `Mask<N>`.
3. **IEEE-754 floating-point lane comparison semantics (`SPEC-41 AXS-FLT-020`, `REQ-SIMD-110`)**:
   - On `Vector<f32, N>` and `Vector<f64, N>`, if `a[i]` or `b[i]` is `NaN`, then `simd_eq`, `simd_lt`, `simd_le`, `simd_gt`, and `simd_ge` produce `false` in lane $i$, while `simd_ne` produces `true` in lane $i$ (`CMPPS`/`CMPPD` unordered-aware predicates).
   - `-0.0` and `+0.0` compare equal (`simd_eq` is `true`, `simd_lt`/`simd_gt` are `false`).
   - Floating-point vectors also provide lane-wise classification predicates returning `Mask<N>`: `v.is_nan() -> Mask<N>`, `v.is_infinite() -> Mask<N>`, `v.is_finite() -> Mask<N>`, `v.is_normal() -> Mask<N>`, `v.is_sign_negative() -> Mask<N>`.

### AXS-SIMD-031 — Mask Logical Algebra, Predicate Reductions & Lane Selection (`select`) (`ASIMD-35..39`, `REQ-SIMD-016`, `REQ-SIMD-330`)

`Mask<N>` supports the following lane-preserving logical operators, reductions, and conditional lane selection (`T464`–`T466`):

1. **Logical algebra on `Mask<N>`**:
   - Bitwise/logical AND `m1 & m2`: `(m1 & m2)[i] = m1[i] && m2[i]`.
   - Bitwise/logical OR `m1 | m2`: `(m1 | m2)[i] = m1[i] || m2[i]`.
   - Bitwise/logical XOR `m1 ^ m2`: `(m1 ^ m2)[i] = (m1[i] != m2[i])`.
   - Logical NOT `!m` (and `~m`): `(!m)[i] = !m[i]`.
   - Short-circuit operators `&&` and `||` are not overloaded on `Mask<N>` (`AX_TYPE_OPERATOR`); eager lane-wise `&` and `|` are used instead.
2. **Mask predicate reductions**:
   - `m.all(self: Mask<N>) -> bool`: returns `true` iff `m[i] == true` for all $0 \le i < N$.
   - `m.any(self: Mask<N>) -> bool`: returns `true` iff there exists $0 \le i < N$ with `m[i] == true`.
   - `m.none(self: Mask<N>) -> bool`: returns `!m.any()` (`true` iff `m[i] == false` for all $0 \le i < N$).
   - `m.count_ones(self: Mask<N>) -> u32`: returns the number of active (`true`) lanes $\sum_{i=0}^{N-1} [m[i] == \text{true}] \in [0, N]$.
   - `m.bitmask(self: Mask<N>) -> u64`: packs the $N$ boolean lanes into the low $N$ bits of a `u64`:
     $$\text{m.bitmask()} = \sum_{i=0}^{N-1} \left([m[i] == \text{true}] \ll i\right)$$
     where bits $[N .. 63]$ are guaranteed to be `0` (for $N = 64$, all 64 bits are populated).
   - `Mask<N>.from_bitmask(bits: u64) -> Mask<N>`: inverse of `bitmask()`, setting lane $i \in [0, N - 1]$ to `((bits >> i) & 1u64) != 0u64`.
3. **Branchless lane-wise conditional selection (`select` / `simd_select`)**:
   - Signature: `pub fn select<T: SimdElement>(self: Mask<N>, on_true: Vector<T, N>, on_false: Vector<T, N>) -> Vector<T, N>` (also callable as `std.simd.select(mask, on_true, on_false)` and backed by `@intrinsic fn simd_select<T, N>(mask: Mask<N>, on_true: Vector<T, N>, on_false: Vector<T, N>) -> Vector<T, N>`).
   - Semantics (`ASIMD-38..39`, `REQ-SIMD-330`): Both `on_true` and `on_false` are already-evaluated `Vector<T, N>` values; `select` chooses lane $i$ from `on_true` when `mask[i]` is `true` and from `on_false` when `mask[i]` is `false`:
     $$\text{select}(\text{mask}, a, b)[i] = \begin{cases} a[i] & \text{if } \text{mask}[i] = \text{true} \\ b[i] & \text{if } \text{mask}[i] = \text{false} \end{cases}$$
   - `select` preserves exact bit patterns of selected lanes (including `-0.0` and quiet/signaling `NaN` payloads on floating-point vectors).

### AXS-SIMD-032 — Horizontal Reductions & Explicit Floating-Point Reduction Ordering (`ASIMD-39..40`, `REQ-SIMD-028`, `REQ-SIMD-330`)

Horizontal reductions collapse a `Vector<T, N>` across its $N$ lanes into a single scalar `T`:

1. **Integer horizontal reductions (`T` $\in \{\text{i8..i64}, \text{u8..u64}, \text{isize}, \text{usize}\}$)**:
   - `v.reduce_add() -> T`: computes the wrapping two's-complement sum $\sum_{i=0}^{N-1} v[i] \pmod{2^{\text{BITS}}}$ (associative and commutative; tree reduction via `PHADDD` / `PSHUFD` + `PADDD` is always bit-exact).
   - `v.reduce_add_checked() -> T`: computes the checked left-to-right sum $(((v[0] + v[1]) + v[2]) + \dots + v[N-1])$, trapping on integer overflow if any intermediate accumulator overflows `[T.MIN, T.MAX]`.
   - `v.reduce_mul() -> T`: computes the wrapping product $\prod_{i=0}^{N-1} v[i] \pmod{2^{\text{BITS}}}$.
   - `v.reduce_min() -> T` and `v.reduce_max() -> T`: return $\min_{0 \le i < N} v[i]$ and $\max_{0 \le i < N} v[i]$.
   - `v.reduce_and() -> T`, `v.reduce_or() -> T`, `v.reduce_xor() -> T`: compute the bitwise `&`, `|`, and `^` across all $N$ lanes.
2. **Floating-point horizontal reductions (`T` $\in \{\text{f32}, \text{f64}\}$, `ASIMD-39..40, 68..70`, `REQ-SIMD-330`)**:
   - Because IEEE-754 floating-point addition and multiplication are **not** associative (`(a + b) + c != a + (b + c)`), Axiom separates strictly ordered left-to-right reductions from pairwise tree reductions (`tasks/0344 §20–21`, `tasks/0347 §37–40`):
   - **Strictly ordered left-to-right reduction (`reduce_add_ordered`, `reduce_mul_ordered`)**:
     - `v.reduce_add_ordered(self: Vector<T, N>) -> T` (and `v.reduce_add_ordered_with(init: T) -> T`) evaluates strictly left-to-right in lane index order $i = 0, 1, \dots, N - 1$:
       $$\text{reduce\_add\_ordered}(v) = (\cdots((v[0] \oplus_{\text{fp}} v[1]) \oplus_{\text{fp}} v[2]) \cdots \oplus_{\text{fp}} v[N - 1])$$
       $$\text{reduce\_add\_ordered\_with}(v, \text{init}) = (\cdots((\text{init} \oplus_{\text{fp}} v[0]) \oplus_{\text{fp}} v[1]) \cdots \oplus_{\text{fp}} v[N - 1])$$
     - The compiler and backend are **forbidden** from reassociating `reduce_add_ordered` into a tree reduction unless an explicit `@fast_math` contract is active (`ASIMD-40..41, 69`).
   - **Pairwise binary-tree reduction (`reduce_add`, `reduce_mul`)**:
     - `v.reduce_add(self: Vector<T, N>) -> T` and `v.reduce_mul(self: Vector<T, N>) -> T` are explicitly defined with **canonical pairwise binary-tree parenthesization** so that even tree reductions are 100% deterministic across `--interp`, `-O0..O2`, SSE2, and AVX2:
       - Base case ($N = 2$): $\text{tree\_add}([v_0, v_1]) = v_0 \oplus_{\text{fp}} v_1$.
       - Recursive step ($N = 2K \ge 4$): splits `v` into lower half $L = v[0 .. K]$ and upper half $H = v[K .. 2K]$, adds lane-wise $S[j] = L[j] \oplus_{\text{fp}} H[j]$ for $0 \le j < K$, and recursively evaluates $\text{tree\_add}(S)$.
       - For $N = 4$: $(v[0] + v[2]) + (v[1] + v[3])$.
       - For $N = 8$: $((v[0] + v[4]) + (v[2] + v[6])) + ((v[1] + v[5]) + (v[3] + v[7]))$.
     - Defining `reduce_add` with this exact halving tree parenthesization maps directly to hardware `VEXTRACTF128` + `VADDPS` + `MOVHLPS` + `ADDPS` + `SHUFPS` + `ADDSS` while preserving byte-for-bit oracle vs native agreement (`INV-ORACLE-002`)!
   - **Floating-point `reduce_min` and `reduce_max`**:
     - `v.reduce_min() -> T` and `v.reduce_max() -> T` fold lanes using IEEE-754 `minimumNumber` / `maximumNumber` (`AXS-SIMD-024`: ignoring `NaN` unless all $N$ lanes are `NaN`, in which case canonical `T.NAN` is returned; ordering `-0.0 < +0.0`).

### AXS-SIMD-033 — MIR Lowering & Verifier Invariants for `Vector<T, N>` and `Mask<N>` (`SPEC-04 AXS-EXT-042`, `T464`, `T465`)

In `compiler/mir/mir.ax`, `compiler/mir/builder.ax`, and `compiler/verify/verifier.ax` (`SPEC-04 AXS-EXT-042`):

1. **Reserved MIR rvalue kinds activated in `T464`**:
   - `MIR_RVALUE_VECTOR_OP { op: MirVecOp, lanes: u32, lhs: MirOperand, rhs: MirOperand, third: MirOperand }` covering lane-wise binary/unary/ternary operations (`Add`, `Sub`, `Mul`, `Div`, `Rem`, `WrappingAdd`, `WrappingSub`, `WrappingMul`, `SatAdd`, `SatSub`, `SatMul`, `BitAnd`, `BitOr`, `BitXor`, `BitNot`, `Shl`, `Shr`, `WrappingShl`, `WrappingShr`, `Neg`, `Abs`, `Min`, `Max`, `Sqrt`, `Fma`, `Floor`, `Ceil`, `Round`, `Trunc`, `Eq`, `Ne`, `Lt`, `Le`, `Gt`, `Ge`, `Select`, `Cast`, `Bitcast`, `LoadMasked`, `Gather`).
   - `MIR_RVALUE_SPLAT { lanes: u32, src: MirOperand }`: broadcasts scalar `src: T` (or `bool`) to `Vector<T, N>` (or `Mask<N>`).
   - `MIR_RVALUE_EXTRACT { lanes: u32, vec: MirOperand, idx: MirOperand }`: extracts scalar `T` (or `bool`) from lane `idx`.
   - `MIR_RVALUE_INSERT { lanes: u32, vec: MirOperand, idx: MirOperand, val: MirOperand }`: returns updated `Vector<T, N>` (or `Mask<N>`).
   - `MIR_RVALUE_SHUFFLE { lanes_in: u32, lanes_out: u32, lhs: MirOperand, rhs: MirOperand, indices: *mut u32 }`: permutes two `Vector<T, N>` operands into `Vector<T, M>`.
   - `MIR_RVALUE_REDUCE { op: MirReduceOp, lanes: u32, src: MirOperand, init: MirOperand }`: horizontal reduction (`Add`, `AddOrdered`, `AddChecked`, `Mul`, `MulOrdered`, `Min`, `Max`, `And`, `Or`, `Xor`, `MaskAll`, `MaskAny`, `MaskNone`, `MaskBitmask`) yielding scalar result.
   - Statements / calls for side-effecting masked and indexed stores (`simd_store_masked`, `simd_scatter`).
2. **MIR Verifier rules (`compiler/verify/verifier.ax`, `T464`, `REQ-SIMD-056..057`)**:
   - Every `Vector<T, N>` and `Mask<N>` local and rvalue must have `T: SimdElement` and $N \in \{2, 4, 8, 16, 32, 64\}$ (`AX_VERIFY_TYPE_MISMATCH`).
   - Binary/ternary lane-wise `VectorOp` operands must have identical vector/mask types and matching lane count $N$; comparison `VectorOp` (`Eq..Ge`) takes two `Vector<T, N>` operands and assigns to a `Mask<N>` destination; `Select` takes `(Mask<N>, Vector<T, N>, Vector<T, N>)` and assigns to `Vector<T, N>`.
   - `Splat` source type must equal destination element type `T` (or `bool` for `Mask<N>`).
   - `Extract` destination type and `Insert` value type must equal the vector's element type `T` (or `bool` for `Mask<N>`), and any constant lane index must satisfy `idx < N`.
   - `Shuffle` operands `lhs` and `rhs` must have the same `Vector<T, N>` type, destination must have type `Vector<T, M>` with the same element type `T`, and all $M$ indices must satisfy `indices[j] < 2 * N`.
   - `Bitcast` source `Vector<T, N>` and destination `Vector<U, M>` must satisfy `N * size_of(T) == M * size_of(U)`.
   - `Reduce` source must be `Vector<T, N>` (or `Mask<N>` for mask reductions) and destination must be `T` (or `bool` / `u64` for mask reductions).

---

## 5. Capability-Safe SIMD Memory Access, Masked Loads/Stores & Gather/Scatter (`AXS-SIMD-040`..`043`)

### AXS-SIMD-040 — Capability-Based Contiguous Slice Loads & Stores (`from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_aligned`, `store_aligned`) (`ANUM-51, 58..59`, `ASIMD-40..46`, `REQ-SIMD-041`)

Ordinary portable SIMD memory operations operate directly on safe Axiom slice capabilities (`view<[T]>` for reads, `mut_view<[T]>` for writes) without requiring raw pointers or `unsafe` blocks (`REQ-SIMD-041`, `ANUM-51`, `ASIMD-64`):

1. **Contiguous slice loads (`from_slice`, `load_unaligned`)**:
   - `Vector<T, N>.from_slice(slice: view<[T]>) -> Vector<T, N>`: requires `slice.len() >= N`; loads lanes $0 .. N - 1$ from `slice[0 .. N]`. If `slice.len() < N`, panics deterministically with `"index out of bounds"` (exit code `101`).
   - `Vector<T, N>.load_unaligned(slice: view<[T]>, offset: usize) -> Vector<T, N>`: requires `offset <= slice.len()` and ` slice.len() - offset >= N` (checked without overflow); loads lane $i \in [0, N - 1]$ from `slice[offset + i]`. If `offset + N > slice.len()`, panics with `"index out of bounds"` (exit code `101`).
   - **Unaligned validity (`ANUM-58..59`, `ASIMD-41..43, 46`)**: `from_slice` and `load_unaligned` do **not** require `slice` to be aligned to `align_of<Vector<T, N>>()` (16 or 32 bytes); they require only natural element alignment `align_of<T>()` guaranteed by `view<[T]>`. On x86-64 (`SPEC-43`), they lower to unaligned vector loads (`MOVUPS`/`MOVUPD`/`MOVDQU`/`VMOVUPS`/`VMOVUPD`/`VMOVDQU`) unless alignment analysis proves 16/32-byte alignment.
2. **Contiguous slice stores (`copy_to_slice`, `store_unaligned`)**:
   - `v.copy_to_slice(self: Vector<T, N>, dst: mut_view<[T]>)`: requires `dst.len() >= N`; writes lane $i \in [0, N - 1]$ to `dst[i]`. Panics if `dst.len() < N`.
   - `v.store_unaligned(self: Vector<T, N>, dst: mut_view<[T]>, offset: usize)`: requires `offset <= dst.len()` and `dst.len() - offset >= N`; writes lane $i \in [0, N - 1]$ to `dst[offset + i]`. Panics if `offset + N > dst.len()`.
3. **Explicitly aligned slice loads and stores (`load_aligned`, `store_aligned`, `ANUM-58`, `ASIMD-42, 45`)**:
   - `Vector<T, N>.load_aligned(slice: view<[T]>, offset: usize) -> Vector<T, N>` and `v.store_aligned(self: Vector<T, N>, dst: mut_view<[T]>, offset: usize)` verify both `offset + N <= slice.len()` and that the runtime byte address of `slice[offset]` is aligned to `align_of<Vector<T, N>>()`, panicking with `"misaligned SIMD access"` (exit code `101`) if misaligned, and lowering to aligned instructions (`MOVAPS`/`MOVAPD`/`MOVDQA`).
[tasks/0337 §29–30, §100 ASIMD-40..42, 60; tasks/0341 §21–23, §100 ANUM-51, 58..59; tasks/0344 §30–32, §100 ASIMD-44..46; tasks/0347 §19–22, §100 ASIMD-40..45; tasks/0403 §82 ASIMD-63..64]

### AXS-SIMD-041 — Masked Contiguous Memory Operations & Inactive-Lane Memory Safety (`load_masked`, `store_masked`) (`ASIMD-34, 36`, `REQ-SIMD-017`, `REQ-SIMD-330`)

Masked memory operations enable safe vectorized loop tails (`len % N != 0`) and predicated algorithms without out-of-bounds faults on inactive lanes:

1. **Masked contiguous load (`load_masked` / `simd_load_masked`)**:
   - Signature: `pub fn load_masked(slice: view<[T]>, offset: usize, mask: Mask<N>, passthrough: Vector<T, N>) -> Vector<T, N>` (backed by `@intrinsic fn simd_load_masked<T, N>(slice: view<[T]>, offset: usize, mask: Mask<N>, passthrough: Vector<T, N>) -> Vector<T, N>`).
   - **Inactive-lane non-access invariant (`ASIMD-34`, `REQ-SIMD-017`, `REQ-SIMD-330`)**: For each lane $i \in [0, N - 1]$:
     - If `mask.test(i) == false`: **no semantic memory read occurs** for lane $i$, no bounds check is required for `offset + i`, and the result lane is `passthrough.extract(i)`. Even if `offset + i >= slice.len()` (or `slice` is empty when `mask.none() == true`), an inactive lane **never** traps or reads out-of-bounds memory.
     - If `mask.test(i) == true`: `offset + i` must satisfy `offset + i < slice.len()`. If `offset + i >= slice.len()` for any active lane, execution panics deterministically with `"index out of bounds"` (exit code `101`); otherwise result lane $i$ is `slice[offset + i]`.
     $$\text{load\_masked}(\text{slice}, \text{off}, m, p)[i] = \begin{cases} \text{slice}[\text{off} + i] & \text{if } m[i] = \text{true } (\text{checked: } \text{off} + i < \text{slice.len()}) \\ p[i] & \text{if } m[i] = \text{false } (\text{no memory access}) \end{cases}$$
2. **Masked contiguous store (`store_masked` / `simd_store_masked`)**:
   - Signature: `pub fn store_masked(self: Vector<T, N>, dst: mut_view<[T]>, offset: usize, mask: Mask<N>)` (backed by `@intrinsic fn simd_store_masked<T, N>(v: Vector<T, N>, dst: mut_view<[T]>, offset: usize, mask: Mask<N>)`).
   - **Inactive-lane non-write invariant (`ASIMD-34`, `REQ-SIMD-017`)**: For each lane $i \in [0, N - 1]$:
     - If `mask.test(i) == false`: **no semantic memory write occurs** at `offset + i` (existing elements of `dst` are untouched, and `offset + i >= dst.len()` is permitted without trapping).
     - If `mask.test(i) == true`: `offset + i` must satisfy `offset + i < dst.len()` (panicking with `"index out of bounds"`, exit code `101` if any active lane is out of bounds), and `dst[offset + i]` is overwritten with `self.extract(i)`.
   - All active-lane bounds checks in `load_masked` and `store_masked` are validated **before** any lane modifies `dst`, so a failing `store_masked` panics cleanly without partial writes.
[tasks/0337 §96, §100 ASIMD-34, 41..42; tasks/0344 §30, §100 ASIMD-34; tasks/0403 §82 ASIMD-35..36]

### AXS-SIMD-042 — Indexed `gather` & `scatter` Semantics, Bounds Checking & Duplicate-Index Determinism (`ANUM-60`, `ASIMD-34..36, 46..47`, `REQ-SIMD-018`)

1. **Unmasked and masked `gather` (`gather`, `gather_masked` / `simd_gather`)**:
   - Signatures:
     - `pub fn gather(slice: view<[T]>, indices: Vector<usize, N>) -> Vector<T, N>` (equivalent to `gather_masked(slice, indices, Mask.splat(true), Vector.default())`).
     - `pub fn gather_masked(slice: view<[T]>, indices: Vector<usize, N>, mask: Mask<N>, passthrough: Vector<T, N>) -> Vector<T, N>` (backed by `@intrinsic fn simd_gather<T, N>(slice: view<[T]>, indices: Vector<usize, N>, mask: Mask<N>, passthrough: Vector<T, N>) -> Vector<T, N>`).
   - Semantics: For each lane $i \in [0, N - 1]$:
     - If `mask.test(i) == false`: no memory access is performed for lane $i$ (even if `indices.extract(i) >= slice.len()`), and result lane $i$ is `passthrough.extract(i)`.
     - If `mask.test(i) == true`: checks `indices.extract(i) < slice.len()` (panicking with `"index out of bounds"`, exit code `101` if out of bounds) and reads `slice[indices.extract(i)]` into result lane $i$. Duplicate indices across active lanes in `gather` are always valid and read the same element.
2. **Unmasked and masked `scatter` (`scatter`, `scatter_masked` / `simd_scatter`)**:
   - Signatures:
     - `pub fn scatter(self: Vector<T, N>, dst: mut_view<[T]>, indices: Vector<usize, N>)` (equivalent to `self.scatter_masked(dst, indices, Mask.splat(true))`).
     - `pub fn scatter_masked(self: Vector<T, N>, dst: mut_view<[T]>, indices: Vector<usize, N>, mask: Mask<N>)` (backed by `@intrinsic fn simd_scatter<T, N>(v: Vector<T, N>, dst: mut_view<[T]>, indices: Vector<usize, N>, mask: Mask<N>)`).
   - **Bounds and inactive-lane rule**: First, for every active lane $i \in [0, N - 1]$ with `mask.test(i) == true`, checks `indices.extract(i) < dst.len()`; if any active lane index is out of bounds, panics with `"index out of bounds"` (exit code `101`) prior to modifying `dst`. Inactive lanes (`mask.test(i) == false`) are not accessed and their indices are not required to be in bounds.
   - **Deterministic duplicate-index write order (`ASIMD-36` in `0344`, `ASIMD-47` in `0347`)**: `scatter` does **not** assume active lane indices are pairwise distinct. Active lanes are committed in strictly ascending lane order $i = 0, 1, \dots, N - 1$: if two active lanes $i < j$ have `indices[i] == indices[j] == k`, both writes are legal and the final value at `dst[k]` after `scatter` is deterministically `self.extract(j)` (the highest active lane index targeting `k`).
[tasks/0337 §100 ASIMD-35..37; tasks/0341 §24, §100 ANUM-60; tasks/0344 §28–29, §100 ASIMD-35..36; tasks/0347 §30–34, §100 ASIMD-46..47; tasks/0403 §82 ASIMD-37]

### AXS-SIMD-043 — Capability Exclusivity, Aliasing & Unsafe Unchecked SIMD Escape Hatches (`ANUM-51..57`, `ASIMD-47..51, 90..93`)

1. **Capability exclusivity preserved (`INV-SEM-002`, `ANUM-51`, `ASIMD-90`)**:
   - Every safe SIMD store (`copy_to_slice`, `store_unaligned`, `store_aligned`, `store_masked`, `scatter`, ` scatter_masked`) requires an exclusive `mut_view<[T]>`. Passing an immutable `view<[T]>` to a store function is rejected with `AX_TYPE_MISMATCH`, and creating overlapping `view<[T]>` and `mut_view<[T]>` over the same backing storage is rejected by the capability checker with `AX_CAP_CONFLICT_MUT` (`91u32`).
2. **Compiler `NoAlias` consumption vs conservative `UnknownAlias` (`ANUM-55..57`, `ASIMD-48..51`, `REQ-SIMD-334`)**:
   - When a function receives `a: view<[T]>`, `b: view<[T]>`, and `out: mut_view<[T]>`, capability verification guarantees `NoAlias(a, out)` and `NoAlias(b, out)` (`SPEC-71 AXS-ALIAS-002`), enabling SIMD loop vectorization without C-style `restrict` annotations (`0095 §10–11`).
   - Conversely, when aliasing is `MayAlias` or `UnknownAlias` (e.g., raw pointers `*mut T` inside `unsafe`), the compiler **never** treats `UnknownAlias` as `NoAlias`; auto-vectorization must either emit a runtime range-disjointness guard with a scalar fallback loop or keep the scalar loop (`ASIMD-50..51`, `tasks/0472 AHW-30..32`).
3. **Explicit `unsafe` raw-pointer SIMD operations (`ANUM-52`, `ASIMD-47, 92..93`)**:
   - `unsafe fn load_ptr_unaligned<T, N>(ptr: *const T) -> Vector<T, N>` and `unsafe fn store_ptr_unaligned<T, N>(v: Vector<T, N>, ptr: *mut T)` require an `unsafe` block (`AX_UNSAFE_REQUIRED` outside `unsafe`) and are verified by the `--interp` UB detector (`SPEC-50 AXS-UNS-015`: reading or writing outside a live allocation provenance traps with `AX_UNSAFE_INTERP_UB`, exit code `125`).

---

## 6. Data-Oriented `TensorView<T, R>`, `TensorMutView<T, R>`, `MatrixView<T>` & SoA Abstractions (`AXS-SIMD-050`..`056`)

### AXS-SIMD-050 — Library-First Tensor & Matrix Architecture Without Mandatory Runtime (`ANUM-64..65, 75..78, 95`, `ASIMD-83..84`, `REQ-SIMD-045`)

1. **No Core tensor or matrix keywords (`ANUM-64..65`, `ASIMD-71..73` in `0337`, `ASIMD-83..84` in `0344`, `REQ-SIMD-045`)**: Axiom does not place `tensor` or `matrix` into the minimal language Core (`TypeKind` has no `Tensor` or `Matrix` variant). Multi-dimensional arrays, matrices, and Structure-of-Arrays (`SoA`) views are zero-overhead standard library abstractions in `std.simd.tensor` (`std/simd/tensor.ax`) and `std.simd.matrix` (`std/simd/matrix.ax`) composed from:
   - Core slice capabilities (`view<[T]>`, `mut_view<[T]>`),
   - fixed-rank shape and stride arrays (`[R]usize`, `[R]isize`), and
   - portable `Vector<T, N>` SIMD kernels.
2. **Zero external runtime or BLAS dependency (`ANUM-77..78, 87, 95`)**: `std.simd.tensor` and `std.simd.matrix` are implemented in 100% pure Axiom with zero mandatory heap allocation, no dynamic dispatch, no hidden thread pool, and no external C BLAS/LAPACK/ML runtime dependency. External accelerator or BLAS libraries may be bound explicitly via `SPEC-50` FFI wrappers (`AXS-SIMD-056`).
[0095 §24–28; tasks/0337 §31–36, §100 ASIMD-71..75; tasks/0341 §38–40, §100 ANUM-64..65, 75..78, 87, 95; tasks/0344 §100 ASIMD-83..86]

### AXS-SIMD-051 — `TensorView<T, R>` and `TensorMutView<T, R>` Representation Over Single Flat Capability (`ANUM-66..70`, `ASIMD-85..90`, `T467`)

1. **Flat capability + metadata representation (no nested views, `ANUM-66..68`, `ASIMD-85..86`)**:
   - A rank-$R$ tensor view ($R \ge 1$) is represented in `std.simd.tensor` as a flat descriptor over a single contiguous backing slice capability — **never** as nested views `view<[view<[T]>]>` (which would introduce pointer indirection, fragmented allocations, and non-vectorizable gather chains):
   ```axiom
   @derive(Copy, Clone)
   pub struct TensorView<T, const R: usize> {
       pub data: view<[T]>,
       pub offset: usize,
       pub shape: [R]usize,
       pub strides: [R]isize,
   }

   pub struct TensorMutView<T, const R: usize> {
       pub data: mut_view<[T]>,
       pub offset: usize,
       pub shape: [R]usize,
       pub strides: [R]isize,
   }
   ```
   *(Note: Until const-generic array lengths `[R]usize` are specialized in a module, `std.simd.tensor` also provides concrete rank specializations `TensorView1D<T>`..`TensorView4D<T>` and `TensorMutView1D<T>`..`TensorMutView4D<T>` alongside generic helpers so all rank-1..4 workloads compile cleanly within the self-host type system.)*
2. **Ownership, copying, and capability provenance (`ANUM-68..70, 88..90`, `ASIMD-76..79, 89..90`)**:
   - Neither `TensorView` nor `TensorMutView` owns its underlying element buffer (`ANUM-68`). Their lifetime and provenance are tracked by the compiler's stored-view capability rules (`SPEC-11`, `ADR-0004 §3`) directly through their `data: view<[T]>` or `data: mut_view<[T]>` field (`ANUM-69`).
   - `TensorView<T, R>` is `Copy` (`CAP_VIEW`): duplicating a `TensorView` duplicates only the `(data, offset, shape, strides)` metadata without copying elements or creating ownership (`ANUM-90`).
   - `TensorMutView<T, R>` is **move-only** (`!Copy`, `CAP_MUT_VIEW`): mutating tensor elements requires exclusive mutable capability (`ANUM-70`). A `TensorMutView<T, R>` can be reborrowed as a read-only `TensorView<T, R>` via `t.as_view()`, during which the `TensorMutView` cannot be mutated (`INV-SEM-002`).

### AXS-SIMD-052 — Shape, Stride, Offset Validation & Contiguous vs Strided Layout Classification (`ANUM-73..74`, `ASIMD-87..88`)

1. **Multi-index address formula**:
   - Given a multi-index $\mathbf{i} = (i_0, i_1, \dots, i_{R-1})$ with $0 \le i_d < \text{shape}[d]$ for every axis $d \in [0, R - 1]$, the linear element index in `data` is:
     $$\text{linear\_idx}(\mathbf{i}) = \text{isize}(\text{offset}) + \sum_{d=0}^{R-1} \text{isize}(i_d) \cdot \text{strides}[d]$$
2. **Construction-time bounds validation (`from_slice`, `from_strided`)**:
   - `TensorView.from_slice(data: view<[T]>, shape: [R]usize) -> Option<TensorView<T, R>>` (and `unwrap` variant `new_contiguous(data, shape)`): computes canonical row-major (C-contiguous) strides where:
     $$\text{strides}[R - 1] = 1, \qquad \text{strides}[d] = \prod_{k = d + 1}^{R - 1} \text{shape}[k]$$
     and verifies with checked multiplication that $\prod_{d=0}^{R-1} \text{shape}[d] \le \text{data.len()}$, returning `Option.None` (or panicking in `new_contiguous`) on overflow or insufficient slice length.
   - `TensorView.from_strided(data: view<[T]>, offset: usize, shape: [R]usize, strides: [R]isize) -> Option<TensorView<T, R>>`: verifies that either the tensor is empty ($\exists d:\, \text{shape}[d] == 0$) or both the minimum reachable linear index $\text{min\_idx} = \text{offset} + \sum_{d:\, \text{strides}[d] < 0} (\text{shape}[d] - 1) \cdot \text{strides}[d]$ and maximum reachable linear index $\text{max\_idx} = \text{offset} + \sum_{d:\, \text{strides}[d] > 0} (\text{shape}[d] - 1) \cdot \text{strides}[d]$ satisfy:
     $$0 \le \text{min\_idx} \le \text{max\_idx} < \text{data.len()}$$
3. **Contiguous vs strided classification (`ASIMD-87..88`)**:
   - A tensor view is **Never assumed contiguous without proof** (`ASIMD-88`).
   - `t.is_row_major_contiguous() -> bool` returns `true` iff every axis $d$ satisfies $\text{strides}[d] == \prod_{k=d+1}^{R-1} \text{shape}[k]$ (or $\text{shape}[d] == 1$).
   - `t.is_col_major_contiguous() -> bool` returns `true` iff $\text{strides}[0] == 1$ and $\text{strides}[d] == \prod_{k=0}^{d-1} \text{shape}[k]$.
   - `t.is_inner_contiguous() -> bool` returns `true` iff the innermost axis $R - 1$ has unit stride `strides[R - 1] == 1`, permitting contiguous `Vector<T, N>` loads/stores along each row even when outer rows have padding (`lda > cols`).

### AXS-SIMD-053 — Tensor Indexing, `subview`, `transpose`, `reshape_contiguous` & Read-Only `broadcast` Safety (`ANUM-70..72`, `ASIMD-78..84`, `T467`)

1. **Bounds-checked element access (`get`, `set`)**:
   - `t.get(indices: [R]usize) -> T` (on `TensorView` and `TensorMutView`) and `t.set(indices: [R]usize, val: T)` (on `TensorMutView` only): verify $i_d < \text{shape}[d]$ for every axis $d \in [0, R - 1]$ (panicking with `"tensor index out of bounds"`, exit code `101` if any $i_d \ge \text{shape}[d]$) and read/write `data[linear_idx(indices)]`.
2. **Metadata-only transformations (`subview`, `transpose`, `permute_axes`, `reshape_contiguous`)**:
   - `t.subview(starts: [R]usize, lengths: [R]usize)`: verifies `starts[d] + lengths[d] <= shape[d]` for all $d$, advances `offset` to `linear_idx(starts)`, sets `shape = lengths`, and preserves `strides` in $O(1)$ time with zero data copying.
   - `t.transpose(axis_a: usize, axis_b: usize)`: swaps `shape[axis_a] <-> shape[axis_b]` and `strides[axis_a] <-> strides[axis_b]` in $O(1)$ time with zero data copying.
   - `t.reshape_contiguous<const R2: usize>(new_shape: [R2]usize) -> Option<TensorView<T, R2>>`: succeeds if and only if `t.is_row_major_contiguous()` is `true` and $\prod \text{new\_shape} == \prod \text{t.shape}$ (`ASIMD-87`).
3. **Disjoint mutable partition (`split_axis_mut`)**:
   - `t_mut.split_axis_mut(axis: usize, mid: usize) -> (TensorMutView<T, R>, TensorMutView<T, R>)`: requires positive stride along `axis` and non-overlapping positive strides, splitting the underlying `mut_view<[T]>` at the axis boundary so two disjoint `TensorMutView` halves can be mutated in parallel (`SPEC-30 AXS-CONC-032`).
4. **Broadcast safety invariant (`ANUM-71..72`, `ASIMD-83..84`)**:
   - **Read-only broadcast (`TensorView.broadcast_to`)**: A `TensorView<T, R>` may set `strides[d] = 0` along any singleton axis ($\text{shape}[d] == 1$) and expand $\text{shape}[d] \gets M > 1$ so multiple logical coordinates read the same physical element (`ASIMD-83`).
   - **Prohibition of mutable broadcast aliasing (`ANUM-72`, `ASIMD-84`)**: `TensorMutView<T, R>` **forbids** `strides[d] == 0` when $\text{shape}[d] > 1$ and forbids any stride combination where two distinct valid multi-indices $\mathbf{i} \ne \mathbf{j}$ map to the same linear index $\text{linear\_idx}(\mathbf{i}) == \text{linear\_idx}(\mathbf{j})$. `TensorMutView.from_strided` rejects zero or self-overlapping strides (`Option.None`), and `broadcast_to` is defined exclusively on read-only `TensorView<T, R>`.

### AXS-SIMD-054 — Value-Semantic Small Vectors/Matrices (`Vec2..4<T>`, `Mat2..4<T>`) & `MatrixView<T>` (`ANUM-75..76`, `T467`)

`std.simd.matrix` (`std/simd/matrix.ax`) defines two complementary matrix abstractions (`ANUM-75`):

1. **Fixed small value-semantic vectors and matrices (`Vec2<T>`, `Vec3<T>`, `Vec4<T>`, `Mat2<T>`, `Mat3<T>`, `Mat4<T>`)**:
   - `@derive(Copy, Clone, PartialEq)` value structs for graphics, geometry, physics, and scientific kernels (`T` $\in \{\text{f32}, \text{f64}, \text{i32}, \text{i64}\}$):
     - `Vec2<T> { pub x: T, pub y: T }`, `Vec3<T> { pub x: T, pub y: T, pub z: T }`, `Vec4<T> { pub x: T, pub y: T, pub z: T, pub w: T }` (with `Vec4<T>.to_simd() -> Vector<T, 4>` and `Vec4<T>.from_simd(v: Vector<T, 4>) -> Vec4<T>`).
     - `Mat2<T> { pub cols: [2]Vec2<T> }`, `Mat3<T> { pub cols: [3]Vec3<T> }`, `Mat4<T> { pub cols: [4]Vec4<T> }` stored in column-major order (`cols[c]` is column $c$), providing `identity()`, `zero()`, `from_rows(...)`, `from_cols(...)`, `transpose()`, `determinant()`, `mul_vec(v)`, and `mul_mat(m)` accelerated via `Vector<T, 4>` lane operations.
2. **Dynamic capability-backed 2D matrix views (`MatrixView<T>`, `MatrixMutView<T>`)**:
   - Rank-2 specializations of `TensorView<T, 2>` and `TensorMutView<T, 2>`:
     ```axiom
     @derive(Copy, Clone)
     pub struct MatrixView<T> {
         pub data: view<[T]>,
         pub offset: usize,
         pub rows: usize,
         pub cols: usize,
         pub row_stride: isize,
         pub col_stride: isize,
     }

     pub struct MatrixMutView<T> {
         pub data: mut_view<[T]>,
         pub offset: usize,
         pub rows: usize,
         pub cols: usize,
         pub row_stride: isize,
         pub col_stride: isize,
     }
     ```
   - Supporting `from_row_major(data, rows, cols)`, `from_col_major(data, rows, cols)`, `get(r, c)`, `set(r, c, val)`, `row(r) -> Option<view<[T]>>` (when `col_stride == 1`), `submatrix(r0, c0, nr, nc)`, and `transpose()` (swapping `rows <-> cols` and `row_stride <-> col_stride` in $O(1)$).

### AXS-SIMD-055 — Pure-Axiom SIMD Kernels (`dot`, `axpy`, `gemv`, Tiled `matmul`) & Data-Oriented `SoA` Helpers (`0095 §24–27`, `ANUM-76..78`, `T467`)

`std.simd.matrix` and `std.simd.tensor` provide deterministic SIMD-accelerated numerical kernels in pure Axiom:

1. **1D Vector Kernels (`dot`, `dot_ordered`, `axpy`)**:
   - `pub fn dot_f32(a: view<[f32]>, b: view<[f32]>) -> f32` and `pub fn dot_f64(a: view<[f64]>, b: view<[f64]>) -> f64`: require `a.len() == b.len()` (panicking on length mismatch); accumulate 4-lane (`f64x4`) or 8-lane (`f32x8`) vector products over `0 .. (n / N) * N`, reduce the vector accumulator with canonical `reduce_add()`, and add the scalar tail `(n / N) * N .. n` left-to-right.
   - `pub fn dot_ordered_f32(a: view<[f32]>, b: view<[f32]>) -> f32` and `pub fn dot_ordered_f64(a: view<[f64]>, b: view<[f64]>) -> f64`: strictly left-to-right sequential accumulation `acc = acc + (a[i] * b[i])` for $i = 0 .. n - 1$.
   - `pub fn axpy_f32(alpha: f32, x: view<[f32]>, y: mut_view<[f32]>)` and `pub fn axpy_f64(alpha: f64, x: view<[f64]>, y: mut_view<[f64]>)`: compute `y[i] = alpha * x[i] + y[i]` using `Vector.splat(alpha)` across $N$-lane chunks plus scalar tail.
2. **2D Matrix Kernels (`gemv`, Tiled `matmul`, `ANUM-76..77`)**:
   - `pub fn gemv_f32(a: MatrixView<f32>, x: view<[f32]>, y: mut_view<[f32]>)` (`y = A * x` where `a.cols == x.len()` and `a.rows == y.len()`).
   - `pub fn matmul_f32(a: MatrixView<f32>, b: MatrixView<f32>, out: MatrixMutView<f32>)` and `pub fn matmul_f64(a: MatrixView<f64>, b: MatrixView<f64>, out: MatrixMutView<f64>)`:
     - Verify `a.cols == b.rows`, `out.rows == a.rows`, and `out.cols == b.cols` (panicking with `"matrix dimension mismatch"`, exit code `101` otherwise).
     - Capability exclusivity (`out: MatrixMutView<T>`) statically guarantees `out` does not alias `a` or `b` (`AX_CAP_CONFLICT_MUT` if the caller attempts to pass overlapping views of the same slice).
     - Uses cache-friendly register-tiled accumulation (`4x8` micro-kernel over `f32x8` or `4x4` over `f32x4`/`f64x4` with deterministic $k = 0 .. K - 1$ inner-product order `c_row += Vector.splat(a[i, k]) * b_row_k`) so every element `out[i, j]` accumulates across $k = 0, 1, \dots, K - 1$ in the exact same floating-point addition order as the reference triple loop!
3. **Data-Oriented `SoA` / `AoSoA` Slice Bundle Helpers (`0095 §24–27`, `T467`)**:
   - Rather than adding a `soa struct` keyword to Core (`0095 §24, 26`), `std.simd.tensor` provides `Soa2<A, B>`, `Soa3<A, B, C>`, and `Soa4<A, B, C, D>` view/mut-view bundles (e.g., `Soa3MutView<f32, f32, f32> { pub x: mut_view<[f32]>, pub y: mut_view<[f32]>, pub z: mut_view<[f32]>, pub len: usize }`) that validate equal slice lengths on construction and iterate in lockstep $N$-lane `Vector<T, N>` chunks across separate contiguous field arrays.

### AXS-SIMD-056 — Execution Domains, Concurrency (`Send`/`Share`), and FFI Tensor/Vector Boundary Contracts (`ANUM-79..94`, `ASIMD-62..64, 83..95`, `REQ-SIMD-044`, `REQ-SIMD-078`)

1. **CPU SIMD vs GPU execution domains (`REQ-SIMD-044`, `REQ-SIMD-078`, `ANUM-79..85`, `ASIMD-85..87, 91..94`)**:
   - CPU SIMD (`Vector<T, N>` lane execution within a single CPU thread) and GPU execution (`@domain(gpu)` kernels, warps/wavefronts, and device address spaces in `Phase 22`) are distinct execution mechanisms (`REQ-SIMD-044`, `REQ-SIMD-078`).
   - Host `TensorView<T, R>` wraps host memory (`view<[T]>`); device tensor buffers live in explicit device storage domains and require explicit host-to-device / device-to-host transfers (`ANUM-79..81`).
2. **Parallel tensor/SIMD execution (`ANUM-97`, `ASIMD-94..95`, `REQ-SIMD-324`)**:
   - Because `Vector<T, N>`, `Mask<N>`, and `TensorView<T, R>` (for `T: Share`) implement `Send` and `Share` (`SPEC-30`), and `TensorMutView.split_axis_mut` produces provably disjoint mutable subviews, parallel executors (`SPEC-34`) can process disjoint tensor tiles concurrently while preserving full compile-time data-race freedom (`INV-CONC-003`).
3. **FFI contracts for `Vector<T, N>` and `TensorView<T, R>` (`ANUM-92..94`, `ASIMD-62..64, 82..84`)**:
   - `TensorView<T, R>` and `TensorMutView<T, R>` are **not** `extern "C"` FFI-safe by default (`ANUM-93`, rejected in `extern "C"` signatures with `AX_FFI_BAD_TYPE`). Crossing a C FFI boundary uses the explicit `@repr(C)` descriptor `TensorFfiDesc<T>` (`data: *mut T`, `offset: usize`, `rank: usize`, `shape: *const usize`, `strides: *const isize`, `ANUM-94`).
   - Passing `Vector<T, N>` across internal Axiom calls uses the target's register calling convention (`SPEC-43` for Windows x64); passing vectors across `extern "C"` requires a target-supported fixed vector width or an explicit `@repr(C)` array/struct wrapper (`ASIMD-62..64`).

---

## 7. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-SIMD-060`..`063`)

### AXS-SIMD-060 — Portable SIMD & Tensor View Diagnostic Codes

In accordance with `spec/diagnostics.md` (`AXD-010`, `AXD-021`), `SPEC-42` defines the following diagnostic codes in self-hosted `axiomc` (`compiler/diag/code.ax`, `T464`):

| Code | Severity | Emit Condition |
|---|---|---|
| `AX_SIMD_INVALID_ELEMENT` | `error` | `Vector<T, N>` instantiated with an element type `T` outside the twelve `SimdElement` scalar types (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`), such as `Vector<bool, 4>`, `Vector<i128, 2>`, `Vector<Str, 4>`, or a struct/pointer (`AXS-SIMD-002`; `data.elem`). |
| `AX_SIMD_INVALID_LANES` | `error` | `Vector<T, N>` or `Mask<N>` instantiated with a lane count $N \notin \{2, 4, 8, 16, 32, 64\}$ (e.g., `N = 0`, `N = 1`, `N = 3`, `N = 6`, `N = 128`) (`AXS-SIMD-002`; `data.lanes`). |
| `AX_SIMD_LANE_OUT_OF_RANGE` | `error` | Compile-time constant lane index `idx` in `extract`/`insert`/`simd_extract`/`simd_insert` satisfies `idx >= N` (`AXS-SIMD-011`; `data.index`, `data.lanes`). |
| `AX_SIMD_SHUFFLE_OUT_OF_RANGE` | `error` | Non-constant selector array or compile-time selector `indices[j] >= 2 * N` in `shuffle`/`simd_shuffle` (or `>= N` in single-vector `swizzle`) (`AXS-SIMD-012`; `data.index`, `data.max_index`). |
| `AX_SIMD_BITCAST_SIZE_MISMATCH` | `error` | `bitcast` / `simd_bitcast` between `Vector<T, N>` and `Vector<U, M>` where $N \cdot \text{size\_of}(T) \ne M \cdot \text{size\_of}(U)$, or involving `Mask<N>` or a non-vector type (`AXS-SIMD-025`; `data.src_size`, `data.dst_size`). |
| `AX_TYPE_MISMATCH` | `error` | Mixing vectors of different element types or lane counts in a binary operation (`Vector<f32, 4> + Vector<f64, 4>`), implicit scalar-to-vector broadcast (`v + 1.0f32`), implicit array-to-vector coercion (`let a: [4]f32 = v`), using `Mask<N>` as a scalar `bool` condition (`if m { }`), or `simd_cast` between different lane counts (`AXS-SIMD-003, 010, 020, 025`). |
| `AX_TYPE_OPERATOR` | `error` | Applying bitwise or shift operators (`&`, `\|`, `^`, `~`, `<<`, `>>`) to floating-point vectors `Vector<f32, N>` or `Vector<f64, N>`, or `&&`/`\|\|` to `Mask<N>` (`AXS-SIMD-023, 031`). |
| `AX_CAP_CONFLICT_MUT` | `error` | Creating a `mut_view<[T]>` or `TensorMutView<T, R>` that overlaps an active `view<[T]>`, `mut_view<[T]>`, `TensorView<T, R>`, or `TensorMutView<T, R>` (`AXS-SIMD-043, 051, 055`). |
| `AX_VERIFY_TYPE_MISMATCH` | `error` | MIR verifier (`compiler/verify/verifier.ax`) detects mismatched lane counts, element types, out-of-range shuffle/extract indices, or mismatched bitcast byte sizes on a `MIR_RVALUE_VECTOR_OP`, `Splat`, `Extract`, `Insert`, `Shuffle`, or `Reduce` rvalue (`AXS-SIMD-033`). |
| `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | `error` | Using `Vector<T, N>` or `Mask<N>` in the frozen C Stage-0 bootstrap compiler `axiom0` (`AXS-SIMD-001`, `SPEC-04 AXS-EXT-010, 020`). |

### AXS-SIMD-061 — Canonical Positive Examples

```axiom
use std.simd.Vector
use std.simd.Mask
use std.simd.f32x4
use std.simd.i32x4
use std.simd.u8x16
use std.simd.u32x4
use std.simd.tensor.TensorView
use std.simd.matrix.MatrixView
use std.simd.matrix.MatrixMutView
use std.simd.matrix.matmul_f32

pub fn simd_portable_demo(src: view<[f32]>, dst: mut_view<[f32]>) -> f32 {
    // 1. Explicit splat, from_array, and lane-wise IEEE-754 arithmetic (AXS-SIMD-010, 020, 022)
    let scale = f32x4.splat(2.5f32)
    let bias = f32x4.from_array([1.0f32, 2.0f32, 3.0f32, 4.0f32])
    let x = f32x4.from_slice(src[0..4])
    let y = x * scale + bias

    // 2. Lane comparison yielding Mask<4>, mask algebra, and branchless select (AXS-SIMD-030, 031)
    let zero = f32x4.splat(0.0f32)
    let positive_mask: Mask<4> = y.simd_gt(zero)
    let clamped = positive_mask.select(y, zero)
    assert(positive_mask.any())

    // 3. Compile-time shuffle and lane extract/insert (AXS-SIMD-011, 012)
    let rev = Vector.shuffle(clamped, clamped, [3u32, 2u32, 1u32, 0u32])
    let updated = rev.insert(0usize, 10.0f32)

    // 4. Value cast vs same-size bitcast (AXS-SIMD-025)
    let as_ints: i32x4 = updated.cast<i32>()
    let raw_bits: u32x4 = updated.bitcast<u32, 4>()
    assert(raw_bits.extract(0usize) == 10.0f32.to_bits())

    // 5. Masked tail load/store where inactive lanes do not touch out-of-bounds memory (AXS-SIMD-041)
    let tail_mask = Mask<4>.from_array([true, true, false, false])
    let tail_vec = f32x4.load_masked(src, src.len() - 2usize, tail_mask, zero)
    tail_vec.store_masked(dst, dst.len() - 2usize, tail_mask)

    // 6. Strictly ordered left-to-right FP reduction vs pairwise tree reduction (AXS-SIMD-032)
    let ordered_sum = updated.reduce_add_ordered()
    let tree_sum = updated.reduce_add() + (as_ints.reduce_add() as f32)
    ordered_sum + tree_sum
}

pub fn simd_integer_overflow_families(a: u8x16, b: u8x16) -> u8x16 {
    // Explicit wrapping and saturating integer SIMD arithmetic (AXS-SIMD-021)
    let sat = a.saturating_add(b)
    let wrap = a.wrapping_sub(b)
    sat ^ wrap
}

pub fn tensor_and_matrix_view_demo(
    a_buf: view<[f32]>,
    b_buf: view<[f32]>,
    c_buf: mut_view<[f32]>
) -> f32 {
    // Flat capability + shape/stride metadata without nested views (AXS-SIMD-051..055)
    let a = MatrixView.from_row_major(a_buf, 4usize, 4usize).unwrap()
    let b = MatrixView.from_row_major(b_buf, 4usize, 4usize).unwrap()
    let b_t = b.transpose()
    let mut c = MatrixMutView.from_row_major(c_buf, 4usize, 4usize).unwrap()

    matmul_f32(a, b_t, mut_view(c))
    c.get(0usize, 0usize)
}
```

### AXS-SIMD-062 — Canonical Negative Examples

```axiom
use std.simd.Vector
use std.simd.Mask
use std.simd.f32x4
use std.simd.f64x4
use std.simd.tensor.TensorMutView

fn rejected_simd_cases(v: f32x4, m: Mask<4>, buf: mut_view<[f32]>) {
    // ERROR [AX_SIMD_INVALID_ELEMENT]: `bool` is not a valid `Vector<T, N>` element; use `Mask<4>` (AXS-SIMD-002)
    let bad_elem: Vector<bool, 4> = Vector.splat(true)

    // ERROR [AX_SIMD_INVALID_LANES]: lane count `3` is not a power of two in `2..=64` (AXS-SIMD-002)
    let bad_lanes: Vector<f32, 3> = Vector.splat(0.0f32)

    // ERROR [AX_TYPE_MISMATCH]: no implicit scalar-to-vector broadcast; write `v + f32x4.splat(1.0f32)` (AXS-SIMD-010)
    let bad_splat = v + 1.0f32

    // ERROR [AX_TYPE_MISMATCH]: `Mask<4>` is not a scalar `bool`; write `if m.all()` or `if m.any()` (AXS-SIMD-003)
    if m {
    }

    // ERROR [AX_SIMD_LANE_OUT_OF_RANGE]: constant lane index `4` is out of range for `Vector<f32, 4>` (`0..4`) (AXS-SIMD-011)
    let bad_extract = v.extract(4usize)

    // ERROR [AX_SIMD_SHUFFLE_OUT_OF_RANGE]: shuffle selector `9` exceeds `2 * N - 1 = 7` (AXS-SIMD-012)
    let bad_shuf = Vector.shuffle(v, v, [0u32, 1u32, 2u32, 9u32])

    // ERROR [AX_SIMD_BITCAST_SIZE_MISMATCH]: `Vector<f32, 4>` (16 bytes) cannot bitcast to `Vector<f64, 4>` (32 bytes) (AXS-SIMD-025)
    let bad_bitcast: f64x4 = v.bitcast<f64, 4>()

    // ERROR [AX_CAP_CONFLICT_MUT]: second `TensorMutView` over `buf` conflicts with live mutable capability `t1` (AXS-SIMD-051)
    let t1 = TensorMutView.new_contiguous(mut_view(buf), [2usize, 2usize])
    let t2 = TensorMutView.new_contiguous(mut_view(buf), [2usize, 2usize])
    t1.set([0usize, 0usize], 1.0f32)
    t2.set([0usize, 0usize], 2.0f32)
}
```

### AXS-SIMD-063 — Requirement & Task Traceability Matrix

| Requirement ID | Corpus Source & Summary | Normative Rules in `SPEC-42` | Delivering / Verifying Tasks |
|---|---|---|---|
| `REQ-SIMD-001` | `tasks/0403 §82 ASIMD-20`: Vector semantics are independent of target ISA. | `AXS-SIMD-001`, `AXS-SIMD-006` | `T463` (spec), `T464`–`T468` |
| `REQ-SIMD-002` | `tasks/0403 §82 ASIMD-21`: Core does not expose ISA-specific vector register types. | `AXS-SIMD-001`, `AXS-SIMD-002` | `T463` (spec), `T464` |
| `REQ-SIMD-003` | `tasks/0403 §82 ASIMD-22`: Vector semantic types are distinct from physical register representations. | `AXS-SIMD-001`, `AXS-SIMD-003`, `AXS-SIMD-004` | `T463` (spec), `T464`, `T470` |
| `REQ-SIMD-004` | `tasks/0403 §82 ASIMD-23`: Fixed-width vectors have semantic lane counts. | `AXS-SIMD-001`, `AXS-SIMD-002`, `AXS-SIMD-005` | `T463` (spec), `T464`, `T466` |
| `REQ-SIMD-005` | `tasks/0403 §82 ASIMD-24`: Scalable vectors represent target-scalable lane execution. | `AXS-SIMD-006` | `T463` (spec) |
| `REQ-SIMD-006` | `tasks/0403 §82 ASIMD-25`: Mask semantics are independent of physical mask representation. | `AXS-SIMD-001`, `AXS-SIMD-003`, `AXS-SIMD-004`, `AXS-SIMD-030`, `AXS-SIMD-031` | `T463` (spec), `T464`–`T466` |
| `REQ-SIMD-007` | `tasks/0403 §82 ASIMD-26`: Vector operations preserve scalar semantic meaning. | `AXS-SIMD-020`..`AXS-SIMD-025` | `T463` (spec), `T464`–`T468` |
| `REQ-SIMD-008` | `tasks/0403 §82 ASIMD-27`: Explicit SIMD does not inherently imply a particular ISA. | `AXS-SIMD-001`, `AXS-SIMD-006` | `T463` (spec), `T464`–`T468` |
| `REQ-SIMD-086` | `tasks/0341 §100 ANUM-21`: SIMD vectors are value-semantic types. | `AXS-SIMD-001`, `AXS-SIMD-003` | `T463` (spec), `T464`, `T466` |
| `REQ-SIMD-087` | `tasks/0341 §100 ANUM-22`: SIMD vector semantics are distinct from array semantics. | `AXS-SIMD-003`, `AXS-SIMD-010` | `T463` (spec), `T464`, `T466` |
| `REQ-SIMD-088` | `tasks/0341 §100 ANUM-23`: SIMD vector width is a semantic lane count. | `AXS-SIMD-001`, `AXS-SIMD-002` | `T463` (spec), `T464` |
| `REQ-SIMD-089` | `tasks/0341 §100 ANUM-24`: Physical register width is an implementation property. | `AXS-SIMD-001`, `AXS-SIMD-004` | `T463` (spec), `T470` |
| `REQ-SIMD-090` | `tasks/0341 §100 ANUM-25`: A SIMD vector does not require a native SIMD instruction set. | `AXS-SIMD-001`, `AXS-SIMD-006` | `T463` (spec), `T465`, `T470` |
| `REQ-SIMD-091` | `tasks/0341 §100 ANUM-26`: Unsupported SIMD operations may be lowered to scalar or alternative target sequences. | `AXS-SIMD-001`, `AXS-SIMD-021`..`025` | `T463` (spec), `T465`, `T470` |
| `REQ-SIMD-092` | `tasks/0341 §100 ANUM-27`: Portable SIMD does not require runtime dispatch. | `AXS-SIMD-001` | `T463` (spec), `T466`, `T472` |
| `REQ-SIMD-096` | `tasks/0341 §100 ANUM-31`: SIMD masks are semantic predicate values. | `AXS-SIMD-003`, `AXS-SIMD-030`, `AXS-SIMD-031` | `T463` (spec), `T464`–`T466` |
| `REQ-SIMD-097` | `tasks/0341 §100 ANUM-32`: SIMD comparison produces mask semantics. | `AXS-SIMD-030`, `AXS-SIMD-031` | `T463` (spec), `T464`–`T466` |
| `REQ-SIMD-166` | `tasks/0344 §100 ASIMD-20`: Vector types have explicit semantic lane structure. | `AXS-SIMD-001`, `AXS-SIMD-002`, `AXS-SIMD-010`..`012` | `T463` (spec), `T464`–`T466` |
| `REQ-SIMD-167` | `tasks/0344 §100 ASIMD-21`: Vector types are distinct from arrays. | `AXS-SIMD-003`, `AXS-SIMD-010` | `T463` (spec), `T464`, `T466` |
| `REQ-SIMD-168` | `tasks/0344 §100 ASIMD-22`: Vector width does not imply a particular physical register width. | `AXS-SIMD-001`, `AXS-SIMD-004` | `T463` (spec), `T464`, `T470` |
| `REQ-SIMD-171` | `tasks/0344 §100 ASIMD-25`: Portable SIMD is the primary programmer-facing SIMD abstraction. | `AXS-SIMD-001`, `AXS-SIMD-005`, `AXS-SIMD-040` | `T463` (spec), `T466` |
| `REQ-SIMD-333` | `tasks/0472 §213.8–9, AHW-27..28`: Vector semantics remain distinct from physical register width; scalable vector ISAs (SVE, RVV) representable without hard-coding fixed vector lengths into Core. | `AXS-SIMD-001`, `AXS-SIMD-006` | `T463` (spec) |
| `REQ-SIMD-098`..`099`, `107`, `111`..`116`, `178`..`179`, `183`..`184`, `248`..`254`, `329` | Explicit `splat`/`extract`/`insert`/`shuffle`, lane-wise arithmetic/overflow, `cast` vs `bitcast`, MIR lowering & verifier rules. | `AXS-SIMD-010`..`012`, `AXS-SIMD-020`..`025`, `AXS-SIMD-033`, `AXS-SIMD-060` | `T464` |
| `REQ-SIMD-016`..`018`, `028`, `124`..`125`, `180`..`182`, `185`, `258`..`261`, `269`, `273`..`278`, `330` | Mask operations, masked load/store inactive-lane safety, gather/scatter bounds & duplicate-index rules, ordered vs associative reductions, oracle & const-eval. | `AXS-SIMD-007`, `AXS-SIMD-030`..`032`, `AXS-SIMD-040`..`042` | `T465` |
| `REQ-SIMD-041`, `052`..`053`, `126`..`128`, `190`..`193`, `212`, `225`..`228`, `286`..`290`, `328` | `std.simd` portable vector/mask aliases, operators, reductions, capability-safe slice access, and contiguous chunk iteration. | `AXS-SIMD-005`, `AXS-SIMD-010`..`013`, `AXS-SIMD-020`..`032`, `AXS-SIMD-040`..`043` | `T466` |
| `REQ-SIMD-129`..`159`, `229`..`240`, `291`..`321` | `TensorView<T, R>`, `TensorMutView<T, R>`, `MatrixView<T>`, `Vec2..4`/`Mat2..4`, broadcast safety, tiled `matmul`, and `SoA` helpers. | `AXS-SIMD-050`..`AXS-SIMD-056` | `T467` |
| `REQ-SIMD-044`..`045`, `078`, `161`..`162`, `245`..`246`, `323`..`324` | End-to-end `E12.3` portable SIMD, mask, gather/scatter, and tensor/matrix view conformance. | `AXS-SIMD-001`..`AXS-SIMD-062` | `T468` |

## Sources

- `docs/base/specs/0095 - Axiom — SIMD, Vectorization & Data-Oriented Computing v0.1.md` (`§1–43, ASIMD-01..20`)
- `docs/base/tasks/0337 - BOOTSTRAP-078 — Axiom SIMD  Vector  Matrix  Tensor Execution Model.md` (`§1–100, ASIMD-20..100`)
- `docs/base/tasks/0341 - BOOTSTRAP-082 — Axiom SIMD, Vector, Tensor & Numeric Computing Model.md` (`§1–100, ANUM-20..100`)
- `docs/base/tasks/0344 - BOOTSTRAP-085 — Axiom SIMD, Vector, Matrix, Numeric Computing & Hardware Acceleration Model.md` (`§1–100, ASIMD-20..100`)
- `docs/base/tasks/0347 - BOOTSTRAP-088 — Axiom SIMD, Vector Types, Auto-Vectorization & Portable Vector Semantics.md` (`§1–100, ASIMD-20..100`)
- `docs/base/tasks/0403 - BOOTSTRAP-144 — SIMD, Vector Types & Auto-Vectorization Engine.md` (`§1–82, ASIMD-20..80`)
- `docs/base/tasks/0426 - BOOTSTRAP-167 — Iterator, Range, Algorithms & Zero-Cost Generic Programming.md` (`§1–85, AITER-20..75`)
- `docs/base/tasks/0427 - BOOTSTRAP-168 — Numeric System, SIMD Types, Math Semantics & Fast Numerical Computing.md` (`§27–100, ANUM-42..52`)
- `docs/base/tasks/0472 - BOOTSTRAP-213 — Hardware ISA, CPU Features, Vector ISA, Intrinsics & Machine-Level Programming.md` (`§213.8–12, §213.99, AHW-27..32`)
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-010`, `AXS-SEM-030`..`034`, `AXS-SEM-041`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-010`, `AXS-EXT-020`, `AXS-EXT-024`, `AXS-EXT-042`, `AXS-EXT-050`)
- `spec/SPEC-40-integers.md` (`AXS-INT-001`..`054`)
- `spec/SPEC-41-floating-point.md` (`AXS-FLT-001`..`073`)
- `spec/requirements/CATALOG.md` (`REQ-SIMD-001`..`333`)
