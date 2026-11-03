# SPEC-43 — Canonical SIMD Backend, LIR Vector Lowering & x86-64 SSE2/SSE4.1/AVX2/FMA Encoding Specification

Status: draft (T469, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0095 §15–43 (ASIMD-06..20)`; `specs/0162 §5–12, §30–40`; `specs/0179 §4–18`; `specs/0181 §2–14`; `tasks/0341 §100 (ANUM-24..28, 52..60, 92..100)`; `tasks/0344 §100 (ASIMD-23..27, 48..70, 98)`; `tasks/0347 §100 (ASIMD-23..27, 48..70, 98)`; `tasks/0403 §1–82 (ASIMD-20..80)`; `tasks/0407 §1–35 (AVEC-20..47)`; `tasks/0427 §100 (ANUM-53..57)`; `tasks/0472 §213.10–12 (AHW-29..32)`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-42-simd.md`.
Covers: `REQ-SIMD-019`, `REQ-SIMD-020`, `REQ-SIMD-021`, `REQ-SIMD-022`, `REQ-SIMD-023`, `REQ-SIMD-024`, `REQ-SIMD-025`, `REQ-SIMD-029`, `REQ-SIMD-030`, `REQ-SIMD-031`, `REQ-SIMD-032`, `REQ-SIMD-033`, `REQ-SIMD-034`, `REQ-SIMD-035`, `REQ-SIMD-036`, `REQ-SIMD-037`, `REQ-SIMD-038`, `REQ-SIMD-039`, `REQ-SIMD-042`, `REQ-SIMD-043`, `REQ-SIMD-046`, `REQ-SIMD-047`, `REQ-SIMD-048`, `REQ-SIMD-049`, `REQ-SIMD-050`.
Consumers: `compiler/lir/lir.ax`, `compiler/lir/builder.ax`, `compiler/abi/win64.ax`, `compiler/target/x64/encode.ax`, `compiler/target/x64/isel.ax`, `compiler/target/x64/frame.ax`, `std/arch/x86_64.ax`, `T470`–`T474`, `E12.5` (`SPEC-44`, `T475`–`T479`), `E15.5` (auto-vectorization).

## Tóm tắt

Tài liệu `SPEC-43` quy định chuẩn tắc tầng hạ mức vector LIR (`v128`, `v256`, `v512`), các lớp thanh ghi (`Vec128`, `Vec256`, `Vec512`, `Mask`), bộ hợp thức hóa vector (vector legalizer), quy ước gọi hàm vector trên Windows x64 (`Win64 ABI`), bộ mã hóa lệnh máy x86-64 (`0F 38`, `0F 3A`, tiền tố `VEX` 2-byte `C5` và 3-byte `C4`), và bảng chọn lệnh SSE2/SSE4.1/AVX2/FMA3 cùng gói intrinsic kiến trúc `std.arch.x86_64` cho phân hệ `E12.4` (Phase `P12`). Các quyết định kiến trúc cốt lõi gồm:
- **Mô hình vector LIR và cờ bộ nhớ hệ thống (`SPEC-04 AXS-EXT-050..051`, `ASIMD-68..70`)**: Mở rộng `compiler/lir/lir.ax` với các kiểu giá trị `LirType.V128`, `V256`, `V512` và lớp thanh ghi `RegClass.Vec128` (`XMM0`–`XMM15`), `RegClass.Vec256` (`YMM0`–`YMM15`), `RegClass.Vec512` (`ZMM`, dự trữ), `RegClass.Mask`, cờ bộ nhớ `LIR_MEM_FLAG_NONTEMPORAL` (`MOVNTDQ`/`MOVNTPS`/`MOVNTPD`) và lệnh gợi ý bộ nhớ đệm `LIR_INST_PREFETCH` (`PREFETCHT0`/`T1`/`T2`/`NTA`) không làm thay đổi ngữ nghĩa bộ nhớ thường của Axiom.
- **Bộ hợp thức hóa vector bảo toàn ngữ nghĩa từng làn (`ASIMD-23..24, 38..80`, `AVEC-20..47`)**: `compiler/lir/builder.ax` ánh xạ vector 128-bit trực tiếp vào `Vec128`, tách vector 256-bit/512-bit (hoặc vector 64 làn) thành các cặp/bộ bốn thanh ghi `Vec128` khi chưa bật `avx2` hoặc giữ nguyên trong `Vec256` (`YMM`) khi bật `avx2`, mở rộng vector hẹp hơn 128-bit (`i32x2`, `i16x4`, `u8x8`) vào phần thấp xác định của `Vec128`, và vô hướng hóa (scalarize) tất định các phép toán không có lệnh phần cứng trực tiếp (như `/`, `%` nguyên, bẫy tràn số học kiểm tra, `gather`/`scatter` trên SSE2) mà vẫn giữ nguyên kết quả từng bit so với `--interp` (`INV-ORACLE-002`).
- **Quy ước ABI vector Windows x64 và vệ sinh `VZEROUPPER` (`0181`, `ASIMD-33..34, 62..64`, `ANUM-92`)**: Tuân thủ chuẩn Microsoft x64 ABI (truyền tham số vector `Vector<T, N>` qua con trỏ ẩn tới khe nhớ căn chỉnh 16/32-byte hoặc thanh ghi theo hợp đồng ABI, bảo toàn đầy đủ 128-bit thấp của `XMM6`–`XMM15` trong `FrameLayout`, căn chỉnh động `RSP` 32-byte khi hàm dùng khung ngăn xếp `YMM` 32-byte, và phát lệnh `VZEROUPPER` (`C5 F8 77`) trước mọi lời gọi hàm không-AVX hoặc `RET` khi đã chạm tới trạng thái `YMM`).
- **Bộ mã hóa `0F 38`/`0F 3A` & `VEX` và chọn lệnh phân tầng (`SPEC-04 AXS-EXT-053`)**: Bổ sung bảng thoát 3-byte `0F 38` và `0F 3A`, tiền tố `VEX` 2-byte (`C5`, tự động chọn khi `X=1, B=1, W=0, mmmm=01`) và 3-byte (`C4`), chọn lệnh cơ sở SSE2 cho mọi CPU `x86_64-windows` (`WEAK-NATIVE 0`), nâng cấp lên SSE4.1/AVX2/FMA3 khi mục tiêu bật cờ tương ứng, và đóng gói các intrinsic phần cứng tường minh trong `std.arch.x86_64`.

---

## 1. LIR Vector Types, Register Classes, Memory Flags & Vectorization Legality (`AXS-SBE-001`..`004`)

### AXS-SBE-001 — LIR Vector Value Types (`v128`, `v256`, `v512`) & Register Classes (`Vec128`, `Vec256`, `Vec512`, `Mask`) (`SPEC-04 AXS-EXT-050`, `0162 §5–7`, `0179 §4`, `T470`)

1. **LIR Vector Value Types**: In `compiler/lir/lir.ax`, the machine-oriented type representation adds three packed vector widths alongside scalar `i8..i64`, `i128` (lowered to GPR pairs per `SPEC-40`), `ptr`, and `f32`/`f64` (`SPEC-41`):
   - `LirType.V128` (`128` bits / `16` bytes): native 128-bit packed vector value carrying lane layout metadata `(elem_kind: LirElemKind, lanes: u8)` where `elem_kind` $\in \{\text{I8}, \text{U8}, \text{I16}, \text{U16}, \text{I32}, \text{U32}, \text{I64}, \text{U64}, \text{F32}, \text{F64}\}$ and $\text{lanes} \cdot \text{bits}(\text{elem\_kind}) \le 128$.
   - `LirType.V256` (`256` bits / `32` bytes): native 256-bit packed vector value when `avx2` is enabled on the compilation target (`lanes * bits(elem_kind) == 256`).
   - `LirType.V512` (`512` bits / `64` bytes): reserved 512-bit packed vector value (`SPEC-04 AXS-EXT-050`), legalized on `x86_64-windows` into two `V256` values (when `avx2` is enabled) or four `V128` values (on baseline SSE2).
2. **Register Classes (`SPEC-04 AXS-EXT-050`, `SPEC-77 AXS-RA-010`)**:
   - `RegClass.Vec128` (`REG_CLASS_VEC128 = 2u8`): 128-bit vector registers mapped on x86-64 to `XMM0`–`XMM15` (sharing physical register units `16..31` with scalar floating-point `RegClass.Xmm`).
   - `RegClass.Vec256` (`REG_CLASS_VEC256 = 3u8`): 256-bit vector registers mapped on x86-64 (when `avx`/`avx2` is active) to `YMM0`–`YMM15` (physical register encoding units `0..15` whose low 128 bits `[127:0]` alias `XMM0`–`XMM15`).
   - `RegClass.Vec512` (`REG_CLASS_VEC512 = 4u8`): reserved for 512-bit `ZMM0`–`ZMM31` registers (`AVX-512`).
   - `RegClass.Mask` (`REG_CLASS_MASK = 5u8`): semantic lane-mask register class. On SSE2/SSE4.1/AVX2 targets without hardware predicate registers, `RegClass.Mask` is legalized to wide lane masks in `RegClass.Vec128` (`XMM`) or `RegClass.Vec256` (`YMM`) where each lane is all-ones (`0xFF..FF`, `true`) or all-zeros (`0x00..00`, `false`). On predicate-register targets (`AVX-512` `k0`–`k7`, `SVE` `p0`–`p15`), `RegClass.Mask` maps to `RegClass.Pred` (`SPEC-04 AXS-EXT-050`).

### AXS-SBE-002 — LIR Vector Instruction Set & Operand Model (`compiler/lir/lir.ax`, `T470`)

`compiler/lir/lir.ax` represents legalized vector operations with dedicated target-neutral LIR instruction kinds carrying element type `ty: TypeId`, `bit_width: u32` (`128` or `256`), and lane count `index: u32`:
- **Memory & Cache Operations**: `LIR_INST_VLOAD` (aligned or unaligned vector load with `flags`), `LIR_INST_VSTORE` (aligned or unaligned vector store with `flags`), `LIR_INST_VLOAD_MASKED`, `LIR_INST_VSTORE_MASKED`, `LIR_INST_VGATHER`, `LIR_INST_VSCATTER`, `LIR_INST_PREFETCH`.
- **Lane Construction & Permutation**: `LIR_INST_VSPLAT` (scalar-to-vector broadcast), `LIR_INST_VEXTRACT` (extract lane `idx` to scalar vreg), `LIR_INST_VINSERT` (insert scalar vreg into lane `idx`), `LIR_INST_VSHUFFLE` (two-vector constant-index lane permutation).
- **Lane-Wise Arithmetic, Bitwise & Shift**: `LIR_INST_VADD`, `LIR_INST_VSUB`, `LIR_INST_VMUL`, `LIR_INST_VDIV` (floating-point; integer `/` and `%` are scalarized by the legalizer per `AXS-SBE-013`), `LIR_INST_VSAT_ADD`, `LIR_INST_VSAT_SUB`, `LIR_INST_VNEG`, `LIR_INST_VABS`, `LIR_INST_VMIN`, `LIR_INST_VMAX`, `LIR_INST_VSQRT`, `LIR_INST_VFMA` (`a * b + c` single-rounding), `LIR_INST_VROUND` (mode: `Floor | Ceil | Trunc | NearestEven`), `LIR_INST_VAND`, `LIR_INST_VOR`, `LIR_INST_VXOR`, `LIR_INST_VANDN`, `LIR_INST_VNOT`, `LIR_INST_VSHL`, `LIR_INST_VSHR` (logical), `LIR_INST_VSAR` (arithmetic).
- **Comparisons, Selection, Casts & Reductions**: `LIR_INST_VCMP` (`Eq | Ne | Lt | Le | Gt | Ge` producing all-ones/all-zeros lane mask), `LIR_INST_VSELECT` (`(mask & on_true) | (~mask & on_false)`), `LIR_INST_VBITMASK` (`PMOVMSKB`/`MOVMSKPS`/`MOVMSKPD` + mask reduction), `LIR_INST_VCAST` (lane-wise numeric conversion), `LIR_INST_VBITCAST` (register-class zero-cost reinterpretation), `LIR_INST_VREDUCE` (`Add | AddOrdered | Mul | MulOrdered | Min | Max | And | Or | Xor`).

### AXS-SBE-003 — Non-Temporal Memory Flag (`LIR_MEM_FLAG_NONTEMPORAL`), Alignment & Prefetch Semantics (`SPEC-04 AXS-EXT-051`, `ASIMD-68..70`, `REQ-SIMD-040`, `REQ-SIMD-214`..`216`, `T470`, `T471`, `T473`)

1. **Memory operation flags (`SPEC-04 AXS-EXT-051`)**: Every LIR `Load`, `Store`, `VLoad`, and `VStore` carries `align: u32`, `addr_space: u16` (`0` in host code), and `flags: u8`:
   - `LIR_MEM_FLAG_NONE = 0u8`: ordinary coherent cacheable memory access.
   - `LIR_MEM_FLAG_VOLATILE = 1u8` (`bit 0`, `SPEC-51 AXS-MEM-002`): non-elidable, non-reordering volatile access.
   - `LIR_MEM_FLAG_NONTEMPORAL = 2u8` (`bit 1`, `E12.4`): streaming cache-bypass hint (`MOVNTDQ`, `MOVNTPS`, `MOVNTPD`, `VMOVNTDQ`, `VMOVNTPS`, `VMOVNTPD`, `MOVNTDQA`).
   - `LIR_MEM_FLAG_ALIGNED = 4u8` (`bit 2`): access is proven or explicitly contracted to be aligned to the vector width (`16` bytes for `v128`, `32` bytes for `v256`), permitting `MOVDQA`/`MOVAPS`/`MOVAPD`; when clear, the backend MUST emit unaligned-safe instructions (`MOVDQU`/`MOVUPS`/`MOVUPD`, `REQ-SIMD-040`, `REQ-SIMD-123`, `REQ-SIMD-285`).
2. **Prefetch & cache-hint invariants (`ASIMD-68..69`, `REQ-SIMD-214..215`)**:
   - `LIR_INST_PREFETCH` (`locality: 0 = NTA, 1 = T2, 2 = T1, 3 = T0`) lowers to `PREFETCHNTA`, `PREFETCHT2`, `PREFETCHT1`, or `PREFETCHT0`.
   - Prefetch is strictly a hardware cache hint, **not** a semantic memory read: it returns `unit`, never traps on unmapped or out-of-bounds addresses on x86-64, and never alters observable Axiom memory values or capability lifetimes.
3. **Non-temporal store ordering contract (`ASIMD-70`, `REQ-SIMD-216`)**:
   - Non-temporal stores bypass the L1/L2 write-back hierarchy via write-combining buffers, require natural vector alignment (`16` bytes for 128-bit `store_nontemporal_*`, `32` bytes for 256-bit `store_nontemporal256_*`), and are surfaced exclusively through explicit `unsafe` intrinsics in `std.arch.x86_64` (`AXS-SBE-043`). Programs issuing non-temporal stores that must become visible to other threads or coherent readers must issue `std.arch.x86_64.sfence()` (`SFENCE`, `0F AE F8`).

### AXS-SBE-004 — Vectorization Legality, Semantic Preservation & Cost-Model Separation (`tasks/0403 §82 ASIMD-38..80`, `tasks/0407 §35 AVEC-20..47`, `REQ-SIMD-019`..`025`, `REQ-SIMD-029`..`038`, `REQ-SIMD-042`..`043`, `REQ-SIMD-046`..`050`, `REQ-SIMD-058`..`084`, `REQ-SIMD-118`..`123`, `REQ-SIMD-194`..`207`, `REQ-SIMD-280`..`285`, `REQ-SIMD-331`, `REQ-SIMD-334`)

Whether SIMD instructions originate from explicit `std.simd` types or compiler-generated loop/SLP vectorization (`REQ-SIMD-042`, `REQ-SIMD-077`, `REQ-SIMD-118`, `REQ-SIMD-200`, `REQ-SIMD-280`), the backend and vectorization pipeline obey the following non-negotiable invariants:
1. **Verified MIR authority & semantic equivalence (`ASIMD-66, 73, 79..80`, `AVEC-20..21`, `REQ-SIMD-043`, `REQ-SIMD-050`, `REQ-SIMD-058..059`, `REQ-SIMD-119`, `REQ-SIMD-281`)**: Vector lowering occurs strictly after semantic verification (`Verified MIR`). Compiler-generated or legalized SIMD must produce observable behavior identical to scalar reference execution (`INV-ORACLE-002`) and can never weaken `Verified MIR` guarantees.
2. **Dependency & alias legality (`ASIMD-38..42, 48..51, 55..56`, `AVEC-22..25, 35..36`, `REQ-SIMD-019..022`, `REQ-SIMD-032..033`, `REQ-SIMD-060..061`, `REQ-SIMD-072..073`, `REQ-SIMD-120..122`, `REQ-SIMD-194..197`, `REQ-SIMD-282..284`, `REQ-SIMD-331`, `REQ-SIMD-334`)**:
   - Loop vectorization must respect all loop-carried true/anti/output dependencies (`REQ-SIMD-019`, `REQ-SIMD-033`, `REQ-SIMD-061`), and SLP vectorization must respect DAG data/memory dependencies (`REQ-SIMD-032`).
   - Vectorization may consume compiler-proven capability disjointness (`mut_view<[T]>` vs `view<[T]>` yielding `NoAlias`, `REQ-SIMD-021`, `REQ-SIMD-072`, `REQ-SIMD-120`, `REQ-SIMD-194..195`, `REQ-SIMD-282`, `REQ-SIMD-331`), and generic specialization may expose contiguous layout/type facts (`REQ-SIMD-076`), but vectorization **never** fabricates ownership or capability proofs (`REQ-SIMD-022`, `REQ-SIMD-073`) and **never** treats `UnknownAlias` / `MayAlias` as `NoAlias` (`REQ-SIMD-020`, `REQ-SIMD-060`, `REQ-SIMD-121`, `REQ-SIMD-196`, `REQ-SIMD-283`, `REQ-SIMD-334`).
   - When static alias or alignment proof is unavailable, an optimization pass may emit a runtime disjointness/alignment guard **only** with a semantically identical scalar fallback loop (`REQ-SIMD-029`, `REQ-SIMD-063`, `REQ-SIMD-080`, `REQ-SIMD-122`, `REQ-SIMD-197`, `REQ-SIMD-284`); runtime optimization guards never replace compile-time safety or bounds verification (`REQ-SIMD-030`, `REQ-SIMD-062`).
3. **Preservation of Ownership, `Drop`, Synchronization, Atomics & Volatiles (`ASIMD-43..47, 56..61`, `AVEC-31..34`, `REQ-SIMD-023..025`, `REQ-SIMD-068..071`, `REQ-SIMD-202..207`)**:
   - Vectorization and LIR vector lowering preserve ownership transfer (`REQ-SIMD-023`, `REQ-SIMD-202`), capability validity (`REQ-SIMD-203`), deterministic `Drop` ordering (`REQ-SIMD-024`, `REQ-SIMD-071`), `Happens-Before` synchronization (`REQ-SIMD-025`, `REQ-SIMD-204`), foreign/I/O side effects (`REQ-SIMD-070`), `Atomic<T>` operations (`REQ-SIMD-068`, `REQ-SIMD-205`), and `Volatile<T>` / `Mmio*<T>` accesses (`REQ-SIMD-069`, `REQ-SIMD-206..207`).
4. **Tail/Remainder Handling & Representation Contracts (`ASIMD-54, 59..61`, `AVEC-37..38`, `REQ-SIMD-031`, `REQ-SIMD-036..038`, `REQ-SIMD-074..075`, `REQ-SIMD-201`)**:
   - Loop tails (`len % N != 0`) handled via scalar epilogue loops or masked operations must preserve exact bounds and trap semantics and must never introduce speculative out-of-bounds memory touches or division/overflow traps on inactive lanes (`REQ-SIMD-031`, `REQ-SIMD-074..075`, `REQ-SIMD-201`).
   - Optimization may change physical register packing (`v256` vs $2 \times \text{v128}$ vs scalar) because throughput is not language semantics (`REQ-SIMD-036..037`, `REQ-SIMD-244`), except where an explicit `@repr(C)` / FFI / intrinsics representation contract forbids invalid layout changes (`REQ-SIMD-038`).
5. **Separation of Legality from Profitability, Determinism & Provenance (`ASIMD-57..58, 69..72`, `AVEC-26..29, 44..47`, `REQ-SIMD-034..035`, `REQ-SIMD-046..049`, `REQ-SIMD-064..067`, `REQ-SIMD-081..084`, `REQ-SIMD-198..199`)**:
   - Legality analysis is strictly separate from `CostModel` profitability (which accounts for target vector width, setup/reduction/epilogue overhead, and register pressure, while PGO weights affect profitability only, never legality). Unproven or unprofitable vectorization fails closed by keeping scalar code without emitting a user error, preserves source-to-LIR `Span` provenance, and remains 100% deterministic across runs.

---

## 2. Vector Legalizer: Multi-Register Splitting, Sub-128-Bit Promotion & Scalarization (`AXS-SBE-010`..`013`)

### AXS-SBE-010 — Target-Feature-Aware Legalization Matrix (`compiler/lir/builder.ax`, `REQ-SIMD-064`..`067`, `REQ-SIMD-169`..`170`, `REQ-SIMD-244`, `T470`)

During MIR-to-LIR lowering (`compiler/lir/builder.ax`), every semantic `Vector<T, N>` (total bit width $W = N \cdot \text{bits}(T) \in [16, 4096]$) and `Mask<N>` ($N \in \{2, 4, 8, 16, 32, 64\}$) is legalized according to the active target feature set of the enclosing function (`baseline = sse2` on `x86_64-windows`, optionally extended with `sse4.1`, `avx2`, `fma`):

| Semantic VectorBit Width $W = N \cdot \text{bits}(T)$ | Baseline Target (`sse2` / `sse4.1`, `avx2` disabled) | `avx2`-Enabled Target (`@target_feature("avx2")` or `-C target-feature=+avx2`) |
|---|---|---|
| $W < 128$ ($16, 32, 64$ bits, e.g., `u8x2`, `i16x4`, `i32x2`, `f32x2`) | Promoted into the low $W$ bits of a single `LirType.V128` (`RegClass.Vec128`, `XMM`) with upper bits zero-initialized on load/construction (`AXS-SBE-012`). | Same (`1` $\times$ `LirType.V128` in `XMM`; no 256-bit widening needed). |
| $W = 128$ (`16` bytes, e.g., `f32x4`, `f64x2`, `i32x4`, `u8x16`) | Native `1` $\times$ `LirType.V128` (`RegClass.Vec128` in `XMM0`–`XMM15`). | Native `1` $\times$ `LirType.V128` (`RegClass.Vec128` in `XMM0`–`XMM15`, VEX-128 encoded). |
| $W = 256$ (`32` bytes, e.g., `f32x8`, `f64x4`, `i32x8`, `u8x32`) | Split into `2` $\times$ `LirType.V128` (`lo: Vec128`, `hi: Vec128`) holding lanes $[0..N/2)$ and $[N/2..N)$ (`AXS-SBE-011`). | Native `1` $\times$ `LirType.V256` (`RegClass.Vec256` in `YMM0`–`YMM15`, VEX-256 encoded). |
| $W = 512$ (`64` bytes, e.g., `f32x16`, `f64x8`, `i32x16`, `u8x64`) | Split into `4` $\times$ `LirType.V128` (`v0..v3: Vec128`), each holding $N/4$ lanes. | Split into `2` $\times$ `LirType.V256` (`lo: Vec256`, `hi: Vec256`), each holding $N/2$ lanes. |
| $W \in \{1024, 2048, 4096\}$ (e.g., `i32x64`, `f64x64`) | Split into $K = W / 128 \in \{8, 16, 32\}$ `LirType.V128` chunks operated on in ascending lane chunk order $c = 0 .. K - 1$. | Split into $K = W / 256 \in \{4, 8, 16\}$ `LirType.V256` chunks operated on in ascending chunk order $c = 0 .. K - 1$. |

### AXS-SBE-011 — Splitting Wide Vectors (`v256`, `v512`, and `>512`-Bit Vectors) into Native Register Tuples (`ASIMD-23`, `REQ-SIMD-169`, `T470`)

When a semantic vector `Vector<T, N>` (or `Mask<N>`) of width $W > W_{\text{native}}$ ($W_{\text{native}} = 128$ without `avx2`, $256$ with `avx2`) is split into $K = W / W_{\text{native}}$ native chunks $(c_0, c_1, \dots, c_{K-1})$ of $M = N / K$ lanes each:
1. **Lane-wise unary/binary/ternary ops (`VAdd`, `VSub`, `VMul`, `VDiv`, `VSatAdd`, `VSatSub`, `VAnd`, `VOr`, `VXor`, `VShift`, `VCmp`, `VSelect`)**: Lower to $K$ independent native vector instructions `op(c_k)` for $k = 0, \dots, K - 1$ in ascending chunk order.
2. **Contiguous loads and stores (`VLoad`, `VStore`)**: Lower to $K$ native loads/stores at byte offsets $\text{base} + k \cdot (W_{\text{native}} / 8)$ for $k = 0, \dots, K - 1$.
3. **Broadcast (`VSplat`)**: Broadcasts the scalar into $c_0$ and copies $c_k = c_0$ for $k = 1, \dots, K - 1$.
4. **Extract and Insert (`VExtract`, `VInsert`)**: A constant lane index $\text{idx} \in [0, N)$ maps directly to chunk $q = \text{idx} / M$ and intra-chunk lane $r = \text{idx} \bmod M$. Dynamic lane indices spill/reload through an aligned stack slot of `Vector<T, N>` after the bounds check `idx < N`.
5. **Cross-chunk Shuffle (`VShuffle`) and Reductions (`VReduce`)**:
   - Each output chunk of a `shuffle` selects lanes from the $2K$ input chunks; when all selectors of output chunk $q$ fall within a single input chunk pair, native intra-register shuffles are emitted, otherwise lane extraction/insertion or stack-slot table lookup is emitted.
   - Pairwise tree reductions (`reduce_add`, `reduce_mul`, `reduce_min`, `reduce_max`, `reduce_and`, `reduce_or`, `reduce_xor`) fold upper chunk halves into lower chunk halves ($c_j \gets c_j \oplus c_{j + K/2}$ for $j = 0 .. K/2 - 1$) recursively down to a single `V128` register before executing the 128-bit horizontal reduction (`SPEC-42 AXS-SIMD-032` halving tree). Strictly ordered `reduce_add_ordered` / `reduce_mul_ordered` fold lanes $0, 1, \dots, N - 1$ sequentially from $c_0$ through $c_{K-1}$.

### AXS-SBE-012 — Promoting Sub-128-Bit Semantic Vectors (`16..64` Bits) into `Vec128` (`T470`)

For narrow vectors with $W = N \cdot \text{bits}(T) \in \{16, 32, 64\}$ (such as `Vector<u8, 2>`, `Vector<i16, 2>`, `Vector<i16, 4>`, `Vector<i32, 2>`, `Vector<f32, 2>`):
1. The value is held in the low $W$ bits (`[W-1:0]`) of a `RegClass.Vec128` (`XMM`) register.
2. Memory loads and stores transfer **only** the exact $W / 8 \in \{2, 4, 8\}$ bytes (`MOVZX` + `MOVD` for 16-bit, `MOVD`/`MOVSS` for 32-bit, `MOVQ`/`MOVSD` for 64-bit) — never reading or writing 16 bytes past the end of an allocation!
3. Before any operation sensitive to upper-lane values (such as `PMOVMSKB` bitmask extraction or horizontal reduction), bits `[127:W]` are masked or ignored so only the $N$ active low lanes participate.

### AXS-SBE-013 — Deterministic Scalarization of Non-Native Vector Operations (`ANUM-26`, `ASIMD-24`, `REQ-SIMD-170`, `T470`)

Whenever the active target ISA lacks a direct hardware instruction for a vector operation, the legalizer (`compiler/lir/builder.ax` or `compiler/target/x64/isel.ax`) lowers the operation to a deterministic lane-by-lane sequence in ascending lane order $i = 0, 1, \dots, N - 1$:
1. **Integer vector division and remainder (`/`, `%`, `checked_div`)**: x86-64 SSE2/AVX2 has no packed integer `IDIV`/`DIV` instruction. The legalizer extracts each lane $i = 0 .. N - 1$, performs the `SPEC-40` division-by-zero (`b[i] == 0`) and signed `T.MIN / -1` overflow checks in ascending lane order (guaranteeing the lowest-index failing lane traps first per `SPEC-42 AXS-SIMD-021`), executes scalar `IDIV`/`DIV`, and packs the results back into the destination vector.
2. **Default checked integer vector `+`, `-`, `*`, `-` traps**: Either evaluated via packed wrapping arithmetic + overflow predicate detection (`Jo`/signed comparison mask -> `PMOVMSKB` $\ne 0$ branching to cold overflow panic) or unrolled lane-wise `LIR_INST_SADD_OVERFLOW`/`UADD_OVERFLOW` checks in ascending lane index order.
3. **Saturating `FloatToInt` vector casts (`v.cast<I>()`)**: Lowers each lane with the saturating `NaN -> 0`, clamped `[I.MIN, I.MAX]` contract of `SPEC-41 AXS-FLT-044` so hardware `0x80000000` indefinite sentinels never leak.
4. **Masked `load_masked`, `store_masked`, `gather`, and `scatter` on baseline SSE2**: Lower to per-lane conditional branches over active mask bits (`(bitmask >> i) & 1 != 0`) in ascending lane order $i = 0 .. N - 1$, verifying bounds **only** on active lanes before any memory access (`SPEC-42 AXS-SIMD-041..042`).

---

## 3. Windows x64 Vector ABI, Stack Alignment & `VZEROUPPER` Hygiene (`AXS-SBE-020`..`022`)

### AXS-SBE-020 — Windows x64 Vector & Mask Argument/Return Classification (`0181 §2–4`, `SPEC-04 AXS-EXT-052`, `ASIMD-33..34, 62..64`, `ANUM-92`, `REQ-SIMD-014`..`015`, `REQ-SIMD-039`..`040`, `REQ-SIMD-157`, `REQ-SIMD-208`..`210`, `REQ-SIMD-319`, `T470`)

Vector ABI classification is a target-specific property of `compiler/abi/win64.ax`, strictly distinct from semantic `Vector<T, N>` type identity (`REQ-SIMD-014..015`, `REQ-SIMD-157`, `REQ-SIMD-208..209`, `REQ-SIMD-319`):
1. **By-reference indirect passing for `Vector<T, N>` and `Mask<N>` parameters (`0181`, Microsoft x64 ABI for `__m128`/`__m256`/aggregates)**:
   - Under the standard Microsoft x64 calling convention (`CallConv.Win64`, `extern "C"`), `Vector<T, N>` and `Mask<N>` values of size $> 8$ bytes (including 16-byte `v128` / `__m128`, 32-byte `v256` / `__m256`, and 64-byte `v512`) are passed **indirectly by hidden pointer** (`ABI_LOC_INDIRECT`): the caller allocates a temporary copy in its stack frame aligned to `align_of<Vector<T, N>>()` (`16` bytes for 128-bit vectors, `32` bytes for $\ge 256$-bit vectors) and passes the 64-bit pointer in the corresponding positional GPR (`RCX`, `RDX`, `R8`, `R9` for slots `0..3`, or `[RSP + 8 * k]` for slot $k \ge 4$).
   - Sub-128-bit vectors (`size_of<Vector<T, N>>() in {2, 4, 8}`) and `Mask<N>` (`size_of<Mask<N>>() in {2, 4, 8}`) whose byte size is $2, 4,$ or $8$ bytes are passed by value in the positional GPR (`RCX`/`RDX`/`R8`/`R9` or stack slot) or by hidden pointer if size $> 8$ bytes (`Mask<16>`, `Mask<32>`, `Mask<64>`), matching `compiler/abi/win64.ax` power-of-two classification (`SPEC-50 AXS-UNS-035`).
2. **Return value passing**:
   - Return values of size $2, 4,$ or $8$ bytes return directly in `RAX`.
   - `Vector<T, N>` and `Mask<N>` return values of size $> 8$ bytes (`16, 32, 64, ...` bytes) use hidden `sret` pointer passing (`ABI_LOC_INDIRECT` in `RCX` at slot `0`, shifting explicit arguments to slots `1..`, with `RAX` returning the `sret` pointer), guaranteeing alignment-safe returns across both SSE2 and AVX2 functions without requiring `__vectorcall`.
3. **FFI vector boundary contract (`REQ-SIMD-039`, `REQ-SIMD-210`)**: Crossing an `extern "C"` FFI boundary with a SIMD vector uses the exact Microsoft x64 by-reference `__m128`/`__m256` pointer convention above (or an explicit `@repr(C)` struct/array wrapper).

### AXS-SBE-021 — Stack Frame Alignment (`16`-Byte / `32`-Byte) & `XMM6`–`XMM15` Callee-Saved Preservation (`SPEC-04 AXS-EXT-054`, `T470`, `T472`)

1. **Stack Slot Alignment**: Every `LirStackSlot` holding a `Vector<T, N>` (including ABI indirect copy slots and register allocator spill slots) is aligned in `compiler/target/x64/frame.ax` to `align_of<Vector<T, N>>()` (`16` bytes for 128-bit vectors; `32` bytes for $\ge 256$-bit vectors). When a function allocates any 32-byte-aligned stack slot (`align == 32`), the prologue dynamically aligns the frame base (`AND rsp, -32` after saving `RBP`) so 32-byte aligned loads/stores (`VMOVDQA`/`VMOVAPS`) never fault.
2. **`XMM6`–`XMM15` Low 128-Bit Preservation vs Volatile Upper `YMM` Halves**:
   - Under the Windows x64 ABI, the low 128 bits (`XMM6`–`XMM15`) are **non-volatile (callee-saved)**, whereas `XMM0`–`XMM5` and the upper 128 bits (`[255:128]`) of **all** sixteen `YMM0`–`YMM15` registers (`YMM0_H`–`YMM15_H`) are **volatile (caller-saved)**.
   - Any function that writes to `XMM6`–`XMM15` (or `YMM6`–`YMM15`) MUST save the low 128 bits of each modified `XMM6`–`XMM15` register to 16-byte-aligned slots in `FrameLayout` in the prologue and restore them in the epilogue (`SPEC-41 AXS-FLT-041`). Any live 256-bit `Vec256` (`YMM`) value spanning a `CALL` instruction MUST be spilled to a 32-byte stack slot across the call.

### AXS-SBE-022 — `VZEROUPPER` Hygiene Across ABI Transitions (`C5 F8 77`, `T471`, `T473`)

On x86-64 microarchitectures, executing legacy non-VEX SSE instructions while the upper 128 bits `[255:128]` of any `YMM0`–`YMM15` register are dirty incurs a severe hardware SSE-AVX state transition penalty. Therefore, whenever a function compiled with `avx` / `avx2` / `fma` allocates or clobbers any 256-bit `RegClass.Vec256` (`YMM`) register:
1. The backend (`compiler/target/x64/isel.ax` / `frame.ax`) MUST emit `VZEROUPPER` (`C5 F8 77`) immediately before every `RET` instruction; and
2. The backend MUST emit `VZEROUPPER` immediately before every `CALL` to any function that is not statically known to be an AVX-enabled internal callee (after spilling any live 256-bit `YMM` registers).

---

## 4. x86-64 `0F 38`, `0F 3A` & 2/3-Byte `VEX` Machine Encoding (`AXS-SBE-030`..`032`)

### AXS-SBE-030 — Legacy `0F`, `0F 38`, and `0F 3A` SIMD Opcode Maps & Mandatory Prefixes (`SPEC-04 AXS-EXT-053`, `T471`)

`compiler/target/x64/encode.ax` encodes legacy SSE2/SSSE3/SSE4.1 instructions using four opcode map identifiers:
1. **Opcode Maps**:
   - `X64_MAP_LEGACY = 0u8` (1-byte primary opcode)
   - `X64_MAP_0F = 1u8` (2-byte escape `0F <op>`)
   - `X64_MAP_0F38 = 2u8` (3-byte escape `0F 38 <op>`, SSSE3/SSE4.1 3-byte opcodes without `imm8`)
   - `X64_MAP_0F3A = 3u8` (3-byte escape `0F 3A <op> ... <imm8>`, SSSE3/SSE4.1 3-byte opcodes with trailing `imm8`)
2. **Mandatory SIMD Prefix & REX Byte Ordering**:
   - Legacy SIMD instructions emit bytes in the strict architectural order:
     $$\text{[Mandatory Prefix: } \texttt{66} \mid \texttt{F3} \mid \texttt{F2}\text{]} \;\to\; \text{[REX: } \texttt{40..4F}\text{]} \;\to\; \text{[Escape: } \texttt{0F} \mid \texttt{0F 38} \mid \texttt{0F 3A}\text{]} \;\to\; \text{Opcode} \;\to\; \text{ModRM} \;\to\; \text{[SIB]} \;\to\; \text{[Disp]} \;\to\; \text{[Imm8]}$$
   - For `XMM0`–`XMM15` (and `YMM0`–`YMM15`), `x64_reg_unit(reg) = reg & 15`: bit `3` (`unit >= 8`, i.e., `XMM8`–`XMM15`) supplies `REX.R` (in `ModRM.reg`), `REX.X` (in `SIB.index`), or `REX.B` (in `ModRM.rm` / `SIB.base`), while `low3 = unit & 7` populates the 3-bit `ModRM`/`SIB` field. `REX.W = 1` (`0x48`) is set for 64-bit GPR-to-XMM transfers (`MOVQ`, `PINSRQ`, `PEXTRQ`, `CVTSI2SS`/`SD` r64).

### AXS-SBE-031 — 2-Byte (`C5`) and 3-Byte (`C4`) `VEX` Prefix Bit Layout & Shortest-Form Selection (`SPEC-04 AXS-EXT-053`, `T471`)

For AVX, AVX2, and FMA3 instructions, `compiler/target/x64/encode.ax` replaces the legacy mandatory prefix (`66`/`F3`/`F2`), `REX` byte, and `0F`/`0F 38`/`0F 3A` escape bytes with a 2-byte (`0xC5`) or 3-byte (`0xC4`) `VEX` prefix:
1. **Field Definitions**:
   - `~R`, `~X`, `~B` (`1` bit each): bitwise **inverted** (`1` when `reg < 8`, `0` when `reg >= 8`) extensions of `ModRM.reg`, `SIB.index`, and `ModRM.rm`/`SIB.base`.When no `SIB` index register is present, `~X = 1`.
   - `~vvvv` (`4` bits): bitwise **inverted** 4-bit register index (`(~nds_unit) & 0xF`) of the first non-destructive source register (`src1`). For 2-operand VEX instructions (`VMOVAPS`, `VSQRTPS`, `VZEROUPPER`, `VPBROADCAST*`), `vvvv = 0b1111` (`~0`).
   - `L` (`1` bit): vector length (`0` = 128-bit `XMM` / scalar, `1` = 256-bit `YMM`).
   - `pp` (`2` bits): implied mandatory prefix (`00` = none, `01` = `66`, `10` = `F3`, `11` = `F2`).
   - `mmmm` (`5` bits, 3-byte VEX only): implied escape map (`00001` = `0F`, `00010` = `0F 38`, `00011` = `0F 3A`).
   - `W` (`1` bit, 3-byte VEX only): `REX.W` / opcode extension (`0` or `1`).
2. **Bit Packing**:
   - **2-Byte `VEX` (`C5`)**: `Byte 0 = 0xC5`; `Byte 1 = ((~R) << 7) | ((~vvvv & 0xF) << 3) | (L << 2) | (pp & 3)`.
   - **3-Byte `VEX` (`C4`)**: `Byte 0 = 0xC4`; `Byte 1 = ((~R) << 7) | ((~X) << 6) | ((~B) << 5) | (mmmm & 0x1F)`; `Byte 2 = (W << 7) | ((~vvvv & 0xF) << 3) | (L << 2) | (pp & 3)`.
3. **Deterministic Shortest-Form Selection Rule**: `x64_emit_vex(...)` MUST emit the 2-byte `C5` prefix if and only if `mmmm == 1` (`0F`), `W == 0`, `~X == 1` (no `R8`–`R15`/`XMM8`–`XMM15` index), and `~B == 1` (rm/base register is `0..7`); otherwise it MUST emit the 3-byte `C4` prefix.
4. **4-Operand `is4` Immediate Encoding (`VBLENDVPS`, `VBLENDVPD`, `VPBLENDVB`)**: The third source mask register (`src3`) is encoded in bits `[7:4]` of the trailing immediate byte (`imm8 = (mask_unit << 4)`).

### AXS-SBE-032 — Canonical Opcode & Byte-Encoding Reference Table (`T471`)

| Instruction Family | Mnemonic(s) | Map / Prefix | Opcode & Operands | Byte Example (`xmm0/ymm0, xmm1/ymm1, xmm2/ymm2`) |
|---|---|---|---|---|
| SSE2 Move (Aligned/Unaligned) | `MOVAPS` / `MOVUPS`, `MOVAPD` / `MOVUPD`, `MOVDQA` / `MOVDQU` | `0F` (`NP`/`66`/`F3`) | `28`/`29` (`APS`/`APD`), `10`/`11` (`UPS`/`UPD`), `6F`/`7F` (`DQA`/`DQU`) | `movdqu xmm0, [rcx]` $\to$ `F3 0F 6F 01`; `movdqa [rcx], xmm0` $\to$ `66 0F 7F 01` |
| SSE2 Packed Int Add/Sub/Mul | `PADDB/W/D/Q`, `PSUBB/W/D/Q`, `PMULLW`, `PMULUDQ` | `66 0F` | `FC`/`FD`/`FE`/`D4` (add), `F8`/`F9`/`FA`/`FB` (sub), `D5` (`pmullw`), `F4` (`pmuludq`) | `paddd xmm0, xmm1` $\to$ `66 0F FE C1`; `psubq xmm0, xmm1` $\to$ `66 0F FB C1` |
| SSE2 Saturating Int Add/Sub | `PADDSB/W`, `PADDUSB/W`, `PSUBSB/W`, `PSUBUSB/W` | `66 0F` | `EC`/`ED` (`paddsb/w`), `DC`/`DD` (`paddusb/w`), `E8`/`E9` (`psubsb/w`), `D8`/`D9` (`psubusb/w`) | `paddusb xmm0, xmm1` $\to$ `66 0F DC C1`; `psubsw xmm0, xmm1` $\to$ `66 0F E9 C1` |
| SSE2 Packed Float Ops | `ADDPS/PD`, `SUBPS/PD`, `MULPS/PD`, `DIVPS/PD`, `SQRTPS/PD`, `MINPS/PD`, `MAXPS/PD`, `CMPPS/PD` | `0F` (`NP` / `66`) | `58` (add), `5C` (sub), `59` (mul), `5E` (div), `51` (sqrt), `5D` (min), `5F` (max), `C2 ib` (cmp) | `addps xmm0, xmm1` $\to$ `0F 58 C1`; `cmppd xmm0, xmm1, 0` $\to$ `66 0F C2 C1 00` |
| SSE2 Bitwise, Shift, Cmp, Shuffle | `PAND`, `POR`, `PXOR`, `PANDN`, `PSLLW/D/Q`, `PSRLW/D/Q`, `PSRAW/D`, `PCMPEQB/W/D`, `PCMPGTB/W/D`, `PSHUFD`, `SHUFPS/PD`, `PMOVMSKB` | `66 0F` (`NP 0F` for `SHUFPS`) | `DB`/`EB`/`EF`/`DF` (bit), `71..73 /6,/2,/4 ib` (shift imm), `74..76` (cmpeq), `64..66` (cmpgt), `70 ib` (`pshufd`), `C6 ib` (`shufps/pd`), `D7` (`pmovmskb`) | `pxor xmm0, xmm1` $\to$ `66 0F EF C1`; `pshufd xmm0, xmm1, 0x1B` $\to$ `66 0F 70 C1 1B`; `pmovmskb eax, xmm0` $\to$ `66 0F D7 C0` |
| SSSE3 / SSE4.1 `0F 38` Map | `PSHUFB`, `PMULLD`, `PCMPEQQ`, `PMINSD/UD`, `PMAXSD/UD`, `PBLENDVB`, `BLENDVPS/PD`, `PMOVSX*`, `PMOVZX*`, `PTEST` | `66 0F 38` | `00` (`pshufb`), `40` (`pmulld`), `29` (`pcmpeqq`), `38..3F` (min/max), `10`/`14`/`15` (blendv `<xmm0>`), `20..35` (pmovsx/zx), `17` (`ptest`) | `pmulld xmm0, xmm1` $\to$ `66 0F 38 40 C1`; `pblendvb xmm0, xmm1` $\to$ `66 0F 38 10 C1` |
| SSE4.1 `0F 3A` Map (`imm8`) | `ROUNDPS`, `ROUNDPD`, `PBLENDW`, `BLENDPS/PD`, `PINSRB/D/Q`, `PEXTRB/D/Q`, `INSERTPS` | `66 0F 3A` | `08 ib` (`roundps`), `09 ib` (`roundpd`), `0E ib` (`pblendw`), `20`/`22 ib` (`pinsrb/d/q`), `14`/`16 ib` (`pextrb/d/q`) | `roundps xmm0, xmm1, 9` $\to$ `66 0F 3A 08 C1 09`; `pinsrd xmm0, ecx, 2` $\to$ `66 0F 3A 22 C1 02` |
| AVX/AVX2 VEX-128 & VEX-256 | `VMOVDQA/U`, `VADDPS/PD`, `VPADDD/Q`, `VPMULLD`, `VPSHUFB`, `VPERMD`, `VPERMQ`, `VPBLENDVB`, `VPSLLVD/Q`, `VPSRLVD/Q`, `VGATHERDPS/PD`, `VZEROUPPER` | `VEX.128` / `VEX.256` (`C5` / `C4`) | Same primary opcodes in `0F`/`0F38`/`0F3A` plus `VPERMD` (`0F38 36`), `VPERMQ` (`0F3A 00 ib`), `VPSLLVD/Q` (`0F38 47`), `VGATHERDPS` (`0F38 92`), `VZEROUPPER` (`0F 77`) | `vpaddd ymm0, ymm1, ymm2` $\to$ `C5 F5 FE C2`; `vpmulld ymm0, ymm1, ymm2` $\to$ `C4 E2 75 40 C2`; `vzeroupper` $\to$ `C5 F8 77` |
| FMA3 (`VEX.DDS`) | `VFMADD213PS`, `VFMADD213PD`, `VFMADD213SS`, `VFMADD213SD` | `VEX` `0F 38` `66` (`W=0` `f32`, `W=1` `f64`) | `A8` (`dst = src1 * dst + src2`), `98` (`132`), `B8` (`231`) | `vfmadd213ps ymm0, ymm1, ymm2` $\to$ `C4 E2 75 A8 C2`; `vfmadd213pd ymm0, ymm1, ymm2` $\to$ `C4 E2 F5 A8 C2` |
| Non-Temporal & Prefetch | `MOVNTDQ`, `MOVNTPS`, `MOVNTPD`, `VMOVNTDQ/PS/PD`, `SFENCE`, `PREFETCHT0/T1/T2/NTA` | `0F` / `66 0F` / `VEX` | `E7` (`movntdq`), `2B` (`movntps/pd`), `0F AE F8` (`sfence`), `0F 18 /1,/2,/3,/0` (`prefetch*`) | `movntdq [rcx], xmm0` $\to$ `66 0F E7 01`; `sfence` $\to$ `0F AE F8`; `prefetcht0 [rcx]` $\to$ `0F 18 09` |

---

## 5. SSE2 Baseline, SSE4.1, AVX2 & FMA3 Instruction Selection & `std.arch.x86_64` (`AXS-SBE-040`..`043`)

### AXS-SBE-040 — Baseline SSE2 128-Bit Vector Instruction Selection (`compiler/target/x64/isel.ax`, `T472`)

Every `x86_64-windows` CPU guarantees baseline SSE2. Without requiring any extra target flag, `compiler/target/x64/isel.ax` lowers all 128-bit `LirType.V128` operations natively (`WEAK-NATIVE 0`):
1. **Loads & Stores**: Unaligned `MOVDQU` (int), `MOVUPS` (`f32x4`), `MOVUPD` (`f64x2`); aligned `MOVDQA`, `MOVAPS`, `MOVAPD` when `LIR_MEM_FLAG_ALIGNED` is set; non-temporal `MOVNTDQ`, `MOVNTPS`, `MOVNTPD` when `LIR_MEM_FLAG_NONTEMPORAL` is set.
2. **Wrapping & Saturating Integer Arithmetic**: `PADDB`/`PADDW`/`PADDD`/`PADDQ`, `PSUBB`/`PSUBW`/`PSUBD`/`PSUBQ` for `wrapping_add`/`wrapping_sub`; `PADDSB`/`PADDSW`, `PADDUSB`/`PADDUSW`, `PSUBSB`/`PSUBSW`, `PSUBUSB`/`PSUBUSW` for 8/16-bit saturating add/sub; compare-blend clamping for 32/64-bit saturating add/sub.
3. **Strict IEEE-754 Float Arithmetic**: `ADDPS`/`ADDPD`, `SUBPS`/`SUBPD`, `MULPS`/`MULPD`, `DIVPS`/`DIVPD`, `SQRTPS`/`SQRTPD`, sign-bit XOR `XORPS`/`XORPD` for unary `-`, sign-bit clear `ANDPS`/`ANDPD` for `abs`, and NaN/signed-zero-preserving `MINPS`/`MINPD` + `MAXPS`/`MAXPD` sequence (`AXS-SIMD-024`).

### AXS-SBE-041 — SSE2 Synthesized Sequences for Non-Trivial 128-Bit Operations (`REQ-SIMD-213`, `T472`)

On baseline SSE2 (when `sse4.1` is not enabled), `isel.ax` synthesizes exact multi-instruction sequences:
1. **Packed `i32x4` / `u32x4` Multiplication (`wrapping_mul`)**: Uses two `PMULUDQ` operations (`even = PMULUDQ(a, b)`, `odd = PMULUDQ(PSRLDQ(a, 4), PSRLDQ(b, 4))`) interleaved from low 32-bit products via `PSHUFD` + `PUNPCKLDQ`. Packed `i64x2` / `u64x2` multiplication decomposes $a \cdot b = a_{\text{lo}} b_{\text{lo}} + ((a_{\text{lo}} b_{\text{hi}} + a_{\text{hi}} b_{\text{lo}}) \ll 32)$ using `PMULUDQ`, `PSRLQ`, `PSLLQ`, and `PADDQ`.
2. **Unsigned & 64-Bit Integer Lane Comparisons**:
   - Unsigned `u8x16`, `u16x8`, `u32x4` relational `<`/`>` flip the sign bit of both operands (`PXOR` with `0x80`/`0x8000`/`0x8000_0000` bias constant) before `PCMPGTB`/`PCMPGTW`/`PCMPGTD`.
   - 64-bit `i64x2` / `u64x2` equality and relational comparisons compare high and low 32-bit halves with `PCMPEQD` / `PCMPGTD` and combine via `PSHUFD` + `PAND`/`POR`.
3. **Mask `select` (`LIR_INST_VSELECT`)**: Lowers to `PAND(mask, on_true) | PANDN(mask, on_false)` (`3` instructions on SSE2; upgraded to `PBLENDVB` / `BLENDVPS` / `BLENDVPD` when `sse4.1` is active).
4. **Horizontal Reductions (`LIR_INST_VREDUCE`)**:
   - Pairwise tree `reduce_add` on `f32x4` lowers to `MOVHLPS tmp, v` (`[v2, v3]`), `ADDPS v, tmp` (`[v0+v2, v1+v3]`), `PSHUFD tmp, v, 1` (`[v1+v3]`), `ADDSS v, tmp` (`(v0+v2)+(v1+v3)`), matching `SPEC-42 AXS-SIMD-032` bit-for-bit!
   - Strictly ordered `reduce_add_ordered` extracts lanes $0, 1, \dots, N-1$ via `PSHUFD`/`UNPCKHPD` and accumulates sequentially with `ADDSS`/`ADDSD`.

### AXS-SBE-042 — Target-Feature-Gated SSE4.1, AVX2 (`256`-Bit `YMM`) & FMA3 Selection (`T473`)

1. **When `sse4.1` is enabled**: `isel.ax` upgrades `i32x4` multiply to `PMULLD`, 64-bit equality to `PCMPEQQ`, mask `select` to `PBLENDVB`/`BLENDVPS`/`BLENDVPD`, lane extract/insert to `PEXTRB/D/Q` and `PINSRB/D/Q`, 32-bit min/max to `PMINSD`/`PMINUD`/`PMAXSD`/`PMAXUD`, widening casts to `PMOVSX*`/`PMOVZX*`, `all`/`none` mask tests to `PTEST`, and float rounding (`floor`/`ceil`/`trunc`/`round_ties_even`) to single-instruction `ROUNDPS`/`ROUNDPD` (`imm8 = 0x09, 0x0A, 0x0B, 0x08`).
2. **When `avx2` is enabled**: 256-bit `LirType.V256` operations lower directly to 256-bit VEX `YMM0`–`YMM15` instructions (`VMOVDQA`/`VMOVDQU`, `VMOVAPS`/`VMOVUPS`, `VPADDB/W/D/Q`, `VPSUBB/W/D/Q`, `VPMULLW/D`, `VADDPS/PD`, `VSUBPS/PD`, `VMULPS/PD`, `VDIVPS/PD`, `VSQRTPS/PD`, `VPAND`/`VPOR`/`VPXOR`/`VPANDN`, per-lane variable shifts `VPSLLVD/Q`, `VPSRLVD/Q`, `VPSRAVD`, cross-lane `VPERMD`/`VPERMQ`/`VPERM2I128`/`VEXTRACTI128`/`VINSERTI128`, `VPBLENDVB`/`VBLENDVPS`/`VBLENDVPD`, and hardware `VGATHERDPS`/`VGATHERDPD` after bounds checking active lanes).
3. **When `fma` is enabled**: Explicit `v.fma(b, c)` (`LIR_INST_VFMA`) lowers to single-instruction `VFMADD213PS` / `VFMADD213PD` (128-bit or 256-bit). Uncontracted `a * b + c` remains `VMULPS` + `VADDPS` (`SPEC-41 AXS-FLT-014`).

### AXS-SBE-043 — Explicit Architecture Intrinsics in `std.arch.x86_64` (`ANUM-28, 52`, `ASIMD-26..29`, `REQ-SIMD-009`..`010`, `REQ-SIMD-093`, `REQ-SIMD-117`, `REQ-SIMD-172`..`173`, `REQ-SIMD-255`, `REQ-SIMD-279`, `T473`)

1. **System/Architecture Layer Boundary (`REQ-SIMD-009`, `REQ-SIMD-093`, `REQ-SIMD-172`, `REQ-SIMD-255`)**: Target-specific x86-64 SIMD and cache intrinsics live exclusively in `std/arch/x86_64.ax` (`module std.arch.x86_64`), never in the language Core or `std.simd`.
2. **Explicit `unsafe` Preconditions & Oracle Parity (`REQ-SIMD-010`, `REQ-SIMD-117`, `REQ-SIMD-173`, `REQ-SIMD-279`)**:
   - Intrinsics that take raw pointers, require alignment preconditions, or expose non-temporal memory ordering (`prefetch_t0`, `prefetch_t1`, `prefetch_t2`, `prefetch_nta`, `store_nontemporal_i128`, `store_nontemporal_f32x4`, `store_nontemporal_f64x2`, `store_nontemporal256_i256`, `store_nontemporal256_f32x8`, `load_nontemporal_i128`) are declared `pub unsafe fn` (requiring an `unsafe` block, `AX_UNSAFE_REQUIRED`) and preserve Axiom provenance/alignment checks in `--interp` (`AX_UNSAFE_INTERP_UB`, exit `125` on misaligned or out-of-bounds non-temporal stores).
   - Pure value-to-value SIMD intrinsics in `std.arch.x86_64` (such as `paddb_128`, `pmaddwd_128`, `pshufb_128`, `vpaddd_256`, `vfmadd213_ps256`, plus fence/hint intrinsics `sfence()`, `lfence()`, `mfence()`, `pause()`) execute identically in `--interp` and native x86-64 (`INV-ORACLE-002`).

---

## 6. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-SBE-050`..`052`)

### AXS-SBE-050 — Backend Verifier & Diagnostic Contract

In accordance with `spec/diagnostics.md` (`AXD-042`), LIR vector legalization (`T470`), x86-64 VEX/opcode-map encoding (`T471`), and SSE2/AVX2 instruction selection (`T472`–`T473`) enforce the following diagnostic rules:
- Unproven optimization preconditions (e.g., `MayAlias` / `UnknownAlias`, unproven alignment, loop-carried dependency, or negative profitability in `CostModel`) fail closed by retaining the unvectorized scalar loop or unaligned load/store (`MOVDQU`/`MOVUPS`) and **never** emit a user error (`REQ-SIMD-049`, `REQ-SIMD-084`).
- Calling an `unsafe fn` intrinsic in `std.arch.x86_64` outside an `unsafe { ... }` block emits `AX_UNSAFE_REQUIRED` (`SPEC-50 AXS-UNS-002`).
- Passing a misaligned pointer (`addr % 16 != 0` for 128-bit or `addr % 32 != 0` for 256-bit) or out-of-bounds pointer to `store_nontemporal_*` under `--interp` traps deterministically with `AX_UNSAFE_INTERP_UB` (exit code `125`).
- Any internal violation of register class constraints (`RegClass.Vec128` vs `RegClass.Vec256` vs `RegClass.Gpr`), illegal VEX prefix state, or unlowered vector pseudo-instruction detected by `x64_verify_checked` reports `AX_ICE_INTERNAL` (`data.stage = "x64_verify"` or `"lir_lower"`, exit code `3`) and writes no artifact.
- Calling a `@target_feature("avx2")` function from a caller lacking `avx2` is diagnosed by the `E12.5` target-feature verifier (`SPEC-44`, `T475`–`T476`) with `AX_SIMD_TARGET_FEATURE_MISMATCH`.

### AXS-SBE-051 — Canonical Positive & Negative Examples

```axiom
use std.simd.f32x4
use std.simd.f32x8
use std.simd.i32x8
use std.arch.x86_64

// 1. Portable 256-bit vector (`f32x8`): splits into 2x `Vec128` (`XMM`) on baseline SSE2,
//    or lowers to a single `Vec256` (`YMM`) VEX instruction + `VZEROUPPER` when `avx2` is enabled (AXS-SBE-010..011, 022).
pub fn portable_f32x8_fma(a: f32x8, b: f32x8, c: f32x8) -> f32x8 {
    let prod = a.fma(b, c)
    prod
}

// 2. Explicit architecture-specific prefetch, non-temporal streaming store, and sfence (AXS-SBE-003, 043)
pub fn stream_store_128(src: f32x4, aligned_dst: *mut f32) {
    unsafe {
        x86_64.prefetch_t0(aligned_dst as *const u8)
        x86_64.store_nontemporal_f32x4(aligned_dst, src)
        x86_64.sfence()
    }
}

fn rejected_arch_intrinsic_outside_unsafe(src: f32x4, dst: *mut f32) {
    // ERROR [AX_UNSAFE_REQUIRED]: `store_nontemporal_f32x4` has a 16-byte alignment & raw-pointer contract (AXS-SBE-043)
    x86_64.store_nontemporal_f32x4(dst, src)
}
```

### AXS-SBE-052 — Requirement & Task Traceability Matrix

| Requirement ID | Corpus Source & Summary | Normative Rules in `SPEC-43` | Delivering / Verifying Tasks |
|---|---|---|---|
| `REQ-SIMD-019`..`025` | `tasks/0403 §82 ASIMD-38..47`: Vectorization requires dependency and alias legality; proven capability disjointness enables vectorization without fabricating ownership/capability proofs; preserves ownership, `Drop`, and synchronization. | `AXS-SBE-004` | `T469` (spec), `T472`, `T474` |
| `REQ-SIMD-029`..`039` | `tasks/0403 §82 ASIMD-51..62`: Runtime guards require scalar fallback; proof-based BCE; tail handling safety; SLP & loop dependence legality; cost-model separation & profitability rejection; physical representation flexibility vs explicit FFI/ABI contracts. | `AXS-SBE-004`, `AXS-SBE-010`..`013`, `AXS-SBE-020` | `T469` (spec), `T470`, `T472`, `T474` |
| `REQ-SIMD-042`..`043` | `tasks/0403 §82 ASIMD-65..66`: Compiler-generated SIMD from scalar source remains semantically equivalent to scalar execution. | `AXS-SBE-004`, `AXS-SBE-010`..`013` | `T469` (spec), `T472`, `T474` |
| `REQ-SIMD-046`..`050` | `tasks/0403 §82 ASIMD-69..73`: SIMD transformations preserve source provenance, are deterministic/incremental/parallelizable, explainable to tooling, fail closed without user errors, and never weaken `Verified MIR`. | `AXS-SBE-004`, `AXS-SBE-050` | `T469` (spec), `T470`–`T474` |
| `REQ-SIMD-014`..`015`, `040`, `157`, `169`..`170`, `208`..`210`, `244`, `319` | `tasks/0403 §82`, `tasks/0341 §100`, `tasks/0344 §100`: LIR `v128`/`v256`/`v512`, multi-register splitting, scalarization fallback, alignment contracts, and target-dependent Win64 vector ABI. | `AXS-SBE-001`..`003`, `AXS-SBE-010`..`013`, `AXS-SBE-020`..`021` | `T470` |
| `REQ-SIMD-064`..`067`, `213`..`216` | `tasks/0407 §35`, `tasks/0344 §100 ASIMD-67..70`: Target-dependent vector widths, `0F 38`/`0F 3A` & 2/3-byte `VEX` encoding, target shuffle lowering, prefetch hints, and non-temporal store semantics. | `AXS-SBE-003`, `AXS-SBE-022`, `AXS-SBE-030`..`032` | `T471` |
| `REQ-SIMD-058`..`063`, `068`..`077`, `080`..`084` | `tasks/0407 §35 AVEC-20..47`: Baseline SSE2 128-bit instruction selection preserving observable, atomic, volatile, ownership, capability, `Drop`, and remainder semantics. | `AXS-SBE-004`, `AXS-SBE-040`..`041` | `T472` |
| `REQ-SIMD-009`..`010`, `093`, `117`, `172`..`173`, `255`, `279` | `tasks/0403 §82`, `tasks/0341 §100`, `tasks/0344 §100`: Target-feature-gated SSE4.1/AVX2/FMA instruction selection, `VZEROUPPER`, and `std.arch.x86_64` explicit `unsafe` architecture intrinsics. | `AXS-SBE-022`, `AXS-SBE-042`..`043` | `T473` |
| `REQ-SIMD-118`..`123`, `194`..`207`, `280`..`285`, `331`, `334` | Differential (`--interp` vs native SSE2 and AVX2/FMA) conformance across 64/128/256/512-bit vectors, Win64 ABI `XMM6`–`XMM15` preservation, and `NoAlias`/alignment safety. | `AXS-SBE-001`..`051` | `T474` |

## Sources

- `docs/base/specs/0095 - Axiom — SIMD, Vectorization & Data-Oriented Computing v0.1.md` (`§15–43, ASIMD-06..20`)
- `docs/base/specs/0162 - AXIOM LIR v0.1.md` (`§5–12, §30–40`)
- `docs/base/specs/0179 - XLV — LIR-001 Axiom Low-Level IR v0.1.md` (`§4–18`)
- `docs/base/specs/0181 - XLVII-B — X86-001 Revision Windows x86-64 PE64.md` (`§2–14`)
- `docs/base/tasks/0341 - BOOTSTRAP-082 — Axiom SIMD, Vector, Tensor & Numeric Computing Model.md` (`§100, ANUM-24..28, 52..60, 92..100`)
- `docs/base/tasks/0344 - BOOTSTRAP-085 — Axiom SIMD, Vector, Matrix, Numeric Computing & Hardware Acceleration Model.md` (`§100, ASIMD-23..27, 48..70, 98`)
- `docs/base/tasks/0347 - BOOTSTRAP-088 — Axiom SIMD, Vector Types, Auto-Vectorization & Portable Vector Semantics.md` (`§100, ASIMD-23..27, 48..70, 98`)
- `docs/base/tasks/0403 - BOOTSTRAP-144 — SIMD, Vector Types & Auto-Vectorization Engine.md` (`§1–82, ASIMD-20..80`)
- `docs/base/tasks/0407 - BOOTSTRAP-148 — Vectorization, SIMD & Auto-Vectorization Engine.md` (`§1–35, AVEC-20..47`)
- `docs/base/tasks/0427 - BOOTSTRAP-168 — Numeric System, SIMD Types, Math Semantics & Fast Numerical Computing.md` (`§100, ANUM-53..57`)
- `docs/base/tasks/0472 - BOOTSTRAP-213 — Hardware ISA, CPU Features, Vector ISA, Intrinsics & Machine-Level Programming.md` (`§213.10–12, AHW-29..32`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050`..`054`)
- `spec/SPEC-40-integers.md` (`AXS-INT-001`..`054`)
- `spec/SPEC-41-floating-point.md` (`AXS-FLT-001`..`044`)
- `spec/SPEC-42-simd.md` (`AXS-SIMD-001`..`063`)
- `spec/requirements/CATALOG.md` (`REQ-SIMD-009`..`334`)
