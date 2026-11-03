# T463 Report — E12.3 Canonical Portable SIMD, Mask Semantics & Data-Oriented Tensor/Matrix View Specification (`SPEC-42`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-42-simd.md` cho Epic `E12.3` (`Vector<T, N>`, `Mask<N>`, các bí danh vector/mask độ rộng cố định `i8x16`..`f64x8` và `mask8`..`mask64`, phép toán theo làn, trộn làn tĩnh `shuffle`/`swizzle`, thu gọn ngang `reduce_*` tất định theo cây nhị phân cân bằng cho số thực dấu phẩy động, ngữ nghĩa tải/lưu có mặt nạ `load_masked`/`store_masked` và `gather`/`scatter` triệt tiêu lỗi trên làn tắt `mask[i] == false`, cùng hệ thống view dữ liệu `SoA`, `Matrix<T, R, C>`, `MatrixView<T>`, `MatrixMutView<T>`, `TensorView<T, R>`, `TensorMutView<T, R>` dựa trên capability an toàn `view<[T]>`/`mut_view<[T]>`). Đồng thời cập nhật 3 tài liệu khóa (`spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`) và kiểm chứng toàn bộ qua `reqcov.py --strict`, `harness_check.py`, `gatecheck.py --no-run`, và `taskctl.py changes T463`.

## What Was Done

1. **Authored `spec/SPEC-42-simd.md` (`AXS-SIMD-001`..`AXS-SIMD-063`)**:
   - **§1 (`AXS-SIMD-001`..`008`) — Portable SIMD Type Model: `Vector<T, N>` and `Mask<N>`**:
     - Defined `Vector<T, N>` (`TypeKind.Vector { elem, lanes }`) and `Mask<N>` (`TypeKind.Mask { lanes }`) as `Copy + Send + Share` value types with `SimdElement` (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`) and `N in {2, 4, 8, 16, 32, 64}` (`AX_SIMD_INVALID_ELEMENT`, `AX_SIMD_INVALID_LANES`), distinct from `[N]T` and `[N]bool`.
     - Specified physical size (`N * size_of<T>()`), natural power-of-two alignment capped at 32 bytes (`min(N * size_of<T>(), 32)`), canonical `[N]bool`-equivalent `Mask<N>` memory layout (`size_of<Mask<N>>() == N`, `align_of<Mask<N>>() == min(N, 16)`), standard fixed-width aliases (`i8x16`..`f64x4`, `mask8x16`..`mask64x4`), scalable vector model reservation (`ScalableVector`, `vscale`), `ConstValue.Vector` compile-time evaluation, and non-atomic memory semantics.
   - **§2 (`AXS-SIMD-010`..`013`) — Lane Construction, Extraction, Insertion & Permutation**:
     - Specified explicit broadcast `splat` (no implicit scalar-to-vector coercion), `from_array`/`to_array`, constant and dynamic bounds-checked `extract`/`insert` (`AX_SIMD_LANE_OUT_OF_RANGE`), compile-time `shuffle`/`swizzle`/`interleave_lo`/`interleave_hi`/`deinterleave`/`reverse`/`rotate_lanes_*` (`AX_SIMD_SHUFFLE_OUT_OF_RANGE`), and contiguous slice chunking (`as_simd_chunks`).
   - **§3 (`AXS-SIMD-020`..`025`) — Lane-Wise Arithmetic, Bitwise, Shift & Math Operations**:
     - Specified homogeneous lane-wise execution across all 5 integer overflow families (checked default with ascending-lane trap precedence, `wrapping_*`, `saturating_*`, `checked_*`, `overflowing_*`), strict IEEE-754 lane-wise floating-point arithmetic and explicit `fma` (no silent FMA contraction or reassociation), per-lane bitwise/shift ops, `abs`/`min`/`max`/`clamp`/`sqrt`/`floor`/`ceil`/`round`/`trunc`, and value-converting `cast<U>()` vs size-checked `bitcast<U, M>()` (`AX_SIMD_BITCAST_SIZE_MISMATCH`).
   - **§4 (`AXS-SIMD-030`..`033`) — Lane Comparisons, Mask Algebra & Horizontal Reductions**:
     - Specified lane-wise comparisons (`simd_eq`, `simd_ne`, `simd_lt`, `simd_le`, `simd_gt`, `simd_ge` -> `Mask<N>`) alongside whole-vector `==`/`!=` (`bool`), `Mask<N>` algebra (`&`, `|`, `^`, `!`, `all`, `any`, `none`, `count_ones`, `bitmask`, `from_bitmask`, `select`), deterministic horizontal reductions (`reduce_add_ordered` strictly left-to-right vs canonical pairwise binary-tree `reduce_add`/`reduce_mul`), and MIR `VectorOp`/`Splat`/`Extract`/`Insert`/`Shuffle`/`Reduce` verifier contracts (`compiler/verify/verifier.ax`).
   - **§5 (`AXS-SIMD-040`..`043`) — Capability-Safe SIMD Memory Access, Masked Loads/Stores & Gather/Scatter**:
     - Specified `from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_aligned`, `store_aligned`, `load_masked`, `store_masked`, `gather`, and `scatter` over `view<[T]>` / `mut_view<[T]>`, enforcing inactive-lane fault suppression (`mask.test(i) == false` performs no semantic memory access) and ascending-lane duplicate-index `scatter` determinism.
   - **§6 (`AXS-SIMD-050`..`056`) — Data-Oriented `TensorView<T, R>`, `TensorMutView<T, R>`, `MatrixView<T>` & SoA Abstractions**:
     - Specified `TensorView<T, R>`, `TensorMutView<T, R>`, `MatrixView<T>`, `MatrixMutView<T>`, `Vec2..4<T>`, `Mat2..4<T>`, and `Soa2..4` built over a single flat `view<[T]>`/`mut_view<[T]>` capability plus `shape`/`strides` metadata without nested views, zero-copy `subview`/`transpose`/`reshape_contiguous`, read-only `broadcast_to` (forbidding mutable broadcast aliasing), and pure-Axiom `dot`/`axpy`/`gemv`/tiled `matmul` kernels.
   - **§7 (`AXS-SIMD-060`..`063`) — Diagnostics, Canonical Examples & Requirement Traceability Matrix**:
     - Documented `AX_SIMD_INVALID_ELEMENT`, `AX_SIMD_INVALID_LANES`, `AX_SIMD_LANE_OUT_OF_RANGE`, `AX_SIMD_SHUFFLE_OUT_OF_RANGE`, and `AX_SIMD_BITCAST_SIZE_MISMATCH`, canonical positive/negative Axiom examples, and full traceability across all 22 `covers:` requirements to `T464`..`T468`.

2. **Updated Locked Specification Indexes & Catalogues**:
   - `spec/INDEX.md`: Added `spec/SPEC-42-simd.md` to §2, `AXS-SIMD-NNN` to §4, and `SPEC-42` to §5 (`Types, literals, arithmetic, panics`).
   - `spec/diagnostics.md`: Documented the `SIMD` area (`AX_SIMD_*`) in §3 `AXD-021`, added the 5 `AX_SIMD_*` diagnostic rows (`T464`) to §11, and added `SPEC-42` to `## Sources`.
   - `spec/invariants.md`: Added `SIMD` to the §1 `Groups:` header, added `## 15. Portable SIMD vectors, masks, masked memory safety, and data-oriented tensor/matrix views (SPEC-42)` (`INV-SIMD-001`..`INV-SIMD-004` for `T464`..`T468`), and added `SPEC-42` to `## Sources`.

## Files changed

- spec/SPEC-42-simd.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`
- `python tools/gatecheck.py --no-run`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T463`

STATUS: COMPLETE round=0
