# T616 — E15.5 — Canonical loop & SLP auto-vectorization specification (SPEC-74)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-74-auto-vectorization.md` (`AXS-VEC-001`..`AXS-VEC-053`) cho phân hệ tự động vector hóa vòng lặp (`Loop Auto-Vectorization` — `opt_loop_vec`) và vector hóa khối lệnh thẳng (`Superword-Level Parallelism` — `SLP` / `opt_slp_vec`) thuộc Epic `E15.5` (Phase 15 `P15-optimizer-2-0`):
- Chuẩn hóa vị trí của tự động vector hóa trên `OptIR` trước khi hạ xuống LIR mà không đòi hỏi chú thích mã nguồn bắt buộc (`@vectorize`, `restrict`, hay `unsafe` — `0162 §31`, `REQ-OPT-013`), đồng thời bảo toàn tương đương ngữ nghĩa vô hướng tuyệt đối (`REQ-OPT-191`, `INV-ORACLE-002`) và quyền uy tối hậu của `Verified MIR` (`REQ-OPT-216`, `REQ-OPT-217`).
- Quy định điều kiện hợp lệ phụ thuộc bộ nhớ (`REQ-OPT-148..150`, `AXS-VEC-010..018`): tận dụng chứng minh tách rời năng lực (`mut_view<[T]>` độc quyền so với `view<[T]>`) từ `AliasInfo` và khoảng `SCEV` tách rời để chứng minh không có phụ thuộc mang qua vòng lặp (`DEP_NONE`, `Certainty.Proven`) mà không cần kiểm tra chồng lấn lúc chạy; cấm tuyệt đối giả định bí danh `Unknown`/`MayAlias` là `NoAlias` (`REQ-OPT-150`, `REQ-OPT-215`), và quy định cơ chế đa phiên bản hóa lúc chạy (`runtime alias/trip-count guard`) luôn kèm nhánh dự phòng vô hướng tương đương ngữ nghĩa.
- Quy định rào cản cứng đối với `Atomic<T>` (`REQ-OPT-151`, `AXS-VEC-019`) và `Volatile<T>` / `@at` MMIO (`REQ-OPT-152`, `AXS-VEC-020`), bảo toàn thứ tự phép toán dấu phẩy động IEEE-754 nghiêm ngặt theo mặc định (`REQ-OPT-153`, `REQ-OPT-206`, `AXS-VEC-021`), quy tắc hợp lệ khi tái kết hợp phép thu gọn (`wrapping_*`, phép toán bit, `min`/`max`, số học có kiểm tra đã chứng minh `NoOverflow`, hoặc thu gọn kết hợp tường minh — `REQ-OPT-154`, `AXS-VEC-022..023`), và bảo toàn bẫy số học có kiểm tra trên từng làn (`AXS-VEC-024..025`).
- Quy định biến đổi vòng lặp có vòng lặp phần dư vô hướng (`scalar remainder epilogue` cho `N % VF != 0`, `AXS-VEC-028..035`), xây dựng cây đóng gói đẳng cấu `SLP` trong khối cơ bản (`AXS-VEC-036..043`), mô hình chi phí chọn độ rộng vector theo tập tính năng đích (`SSE2` 128-bit mặc định so với `AVX2` 256-bit dưới `@target_feature` / `--target-feature` — `REQ-OPT-209..214`, `AXS-VEC-044..047`), hạ xuống thanh ghi `Vec128`/`Vec256` kèm vệ sinh `VZEROUPPER` trong `compiler/lir/vec_lower` (`AXS-VEC-048`), và truy vết giải thích `Source → MIR → OptIR → LIR → Machine` (`inspect --emit=vectorize` / `--emit=vector-cost`, `REQ-OPT-219..222`, `AXS-VEC-051`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-VEC-001`..`INV-VEC-003`).

## What was decided / produced
1. **`spec/SPEC-74-auto-vectorization.md` (`AXS-VEC-001`..`AXS-VEC-053`)**:
   - **Section 1 (`AXS-VEC-001`..`AXS-VEC-009`)**: Pre-LIR optimizer pipeline placement (`REQ-OPT-013`), scalar-to-vector semantic equivalence (`REQ-OPT-191`), `Verified MIR` authority (`REQ-OPT-216..217`), typed `OptIR` vector operations, strict separation of legality (`Certainty.Proven`) from `VectorCostModel` profitability (`REQ-OPT-212`, `REQ-OPT-220`), isolation of target profiles from Core semantics (`REQ-OPT-213..214, 219`), fail-closed scalar fallback, ownership/`Drop` preservation, and CPU SIMD vs GPU SIMT separation.
   - **Section 2 (`AXS-VEC-010`..`AXS-VEC-018`)**: Memory-dependence legality gate (`REQ-OPT-148`), capability-driven disjointness proofs (`mut_view<[T]>` vs `view<[T]>`, `REQ-OPT-149`), disjoint `SCEV` strides and sub-slice partitions, prohibition on treating `UnknownAlias`/`MayAlias` as `NoAlias` (`REQ-OPT-150`, `REQ-OPT-215`), loop-carried distance $d$ vs $VF$ legality ($0 < d < VF$ rejected), runtime alias/trip-count versioning guards with mandatory scalar fallback, alignment classification (`KnownAligned` vs unaligned-safe default), unit-stride vs gather/scatter rules, and inlining/specialization integration.
   - **Section 3 (`AXS-VEC-019`..`AXS-VEC-027`)**: Hard barriers for `Atomic<T>` (`REQ-OPT-151`) and `Volatile<T>` / `Mmio*<T>` (`REQ-OPT-152`), strict IEEE-754 floating-point ordering by default (`REQ-OPT-153`, `REQ-OPT-206`), reduction operator recognition and reassociation legality (`REQ-OPT-154`), wrapping/bitwise/`min`/`max` vs proven `NoOverflow` checked integer reductions, checked-arithmetic trap preservation across vector lanes, predicated `VSelect` non-speculative fault rules, `VSplat`/`VStep` widening, and multi-accumulator interleaving (`UF in {1, 2, 4}`).
   - **Section 4 (`AXS-VEC-028`..`AXS-VEC-035`)**: Canonical loop preconditions, $N_{\text{vec}} = N \mathbin{\&} \sim(VF \cdot UF - 1)$ and $N_{\text{rem}} = N \bmod (VF \cdot UF)$ trip-count partitioning, scalar remainder epilogue loop generation, short-trip bypass guard (`N < VF * UF`), alignment peeling, masked tail alternative, horizontal reduction epilogue merge (`OPT_INST_VREDUCE`), and `LCSSA`/`DominatorTree`/`MemorySSA` reconstruction.
   - **Section 5 (`AXS-VEC-036`..`AXS-VEC-043`)**: Basic-block `SLP` seed discovery (adjacent struct fields, array elements, associative reduction trees), isomorphic `SlpTree` construction (`SLP_NODE_VECTORIZABLE`, `SLP_NODE_BROADCAST`, `SLP_NODE_GATHER_PACK`), DAG acyclicity and `MemorySSA` independence (`REQ-OPT-215..217`), pack width selection (`L in {2, 4, 8}`), `SLP` profitability formula, `VExtract` for external scalar uses, post-unroll `SLP` cooperation, and `SLP` semantic barriers.
   - **Section 6 (`AXS-VEC-044`..`AXS-VEC-052`)**: Target ISA width selection (`128`-bit `SSE2` baseline vs `256`-bit `AVX2` under `@target_feature` / `--target-feature`, `REQ-OPT-209..211, 214`), register-pressure/spill modeling (`16` `XMM`/`YMM` budget), confidence-tagged `VectorCostModel` formula (`REQ-OPT-220`), `-O0`..`-Oz` and PGO policy, `compiler/lir/vec_lower` (`Vec128`/`Vec256` + `VZEROUPPER` hygiene), `PassManager` contracts and transactional rollback, diagnostic contract (zero new user errors; `AX_ICE_MIR_VERIFY`/`AX_ICE_INTERNAL` on broken IR), end-to-end `Source → MIR → OptIR → LIR → Machine` provenance and `inspect --emit=vectorize` / `--emit=vector-cost` (`REQ-OPT-221..222`), and determinism/parallel/incremental caching rules.
   - **Section 7 (`AXS-VEC-053`)**: Canonical positive and negative Axiom examples (`=` and `.` syntax), requirement traceability matrix, and corpus sources.
2. **Index, Diagnostics, and Invariants Updates**:
   - Registered `spec/SPEC-74-auto-vectorization.md` and `AXS-VEC-NNN` in `spec/INDEX.md` (§2, §4, §5).
   - Added `SPEC-74` to `spec/diagnostics.md` Sources.
   - Added §33 (`INV-VEC-001`..`INV-VEC-003`) to `spec/invariants.md`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS (exit 0)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS (exit 0)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T616`: PASS (exit 0, 0 REFUSED files)

## Files changed
- spec/SPEC-74-auto-vectorization.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
