# Phase Review — `P15-optimizer-2-0` (Optimizer 2.0)

## Tóm tắt

Báo cáo thẩm định kiến trúc khi hoàn tất trọn vẹn **Phase 15 (`P15-optimizer-2-0` — Optimizer 2.0)** tại cổng kiểm định `T315`:
1. **Hoàn thành 32/32 task thực thi và đặc tả của `P15-optimizer-2-0` (`T063`, `T064`, `T600`–`T629`, cùng task lập kế hoạch `T215`)**: Toàn bộ 8 epic (`E15.1`–`E15.8`) trong `spec/ROADMAP.md` §3 (`differential green at -O2; benchmark targets met and tracked in CI`) và 8 đặc tả chuẩn (`SPEC-70` đến `SPEC-77`) đã được hiện thực hóa hoàn toàn bằng Axiom trong `compiler/` và chứng nhận qua bộ kiểm thử hợp chuẩn `tests/conformance/p15/`:
   - **`E15.1` (`SPEC-70`, `T600`–`T604`, `INV-PIPE-008`)**: Biểu diễn trung gian tối ưu hóa hợp nhất `OptIR` (SSA cho giá trị và `MemorySSA` cho bộ nhớ gồm `LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`) được hạ exclusivamente từ `Verified MIR` (`optimizer.inference = None`), cây thống trị Cooper-Harvey-Kennedy (`DominatorTree`) và đặt nút `OptPhi` tối thiểu, trình quản lý pha `PassManager` kiểm chứng hợp đồng biến đổi đóng an toàn (fail-closed rollback) trên dàn độ chắc chắn 3 giá trị (`Proven` / `Possible` / `Unknown`), suy luận hiệu ứng liên thủ tục `EffectInfo` trên SCC, và bộ tối ưu vô hướng (`SCCP`, `GVN`, `CSE`, `SROA`, `DCE`) bảo toàn tuyệt đối thứ tự `Drop`, bẫy tràn số có kiểm tra so với `wrapping_*`, I/O, `atomic`, `volatile`, `black_box` và `zeroize`.
   - **`E15.2` (`SPEC-71`, `T605`–`T608`, `INV-PIPE-009`)**: Phân tích bí danh dẫn xuất từ năng lực và nguồn gốc (`AliasInfo` 5 giá trị `NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`, `UnknownAlias`) khai thác chứng minh độc quyền của `mut_view<T>` và bất biến chỉ đọc của `view<T>`, chuyển tiếp ghi-sang-đọc (`Store-to-Load Forwarding`), xóa đọc thừa (`RLE`) và xóa ghi chết (`DSE`) trên `MemorySSA`, phân tích thoát 4 mức (`NoEscape < ArgumentEscape < ReturnEscape < GlobalEscape`), thăng cấp `Box<T>`, môi trường bao đóng (`TY_CLOSURE` mang đầy đủ chữ ký và chế độ bắt giữ `CAP_COPY`/`CAP_VIEW`/`CAP_MUT_VIEW`/`CAP_MOVE`), bộ đệm hữu hạn lên stack/thanh ghi SSA, khởi tạo trực tiếp tại khe trả về (`NRVO`), và tôn trọng rào cản quan sát địa chỉ (`address_of`, `@at`, `volatile`).
   - **`E15.3` (`SPEC-72`, `T609`–`T612`, `INV-PIPE-010`)**: Phát hiện vòng lặp tự nhiên trên CFG và chuẩn hóa `LoopSimplify` (`preheader`, `latch` đơn, khối thoát chuyên biệt) + `LCSSA`, tiến hóa vô hướng tuân thủ tràn số (`SCEV` `{start, +, step}<mode>` phân biệt `Checked`, `Wrapping`, `Saturating`, `ProvenNswNuw`, tuyệt đối không giả định UB kiểu C/C++), phân tích khoảng `RangeInfo` và loại bỏ kiểm tra biên (`BCE`) khi chứng minh được `0 <= idx < len` (`Certainty.Proven`) trong khi giữ nguyên bẫy kiểm tra biên khi chưa chứng minh được, nâng mã bất biến vòng lặp (`LICM`) an toàn với vòng lặp 0 lần chạy, giảm cường độ biến quy nạp, `peeling`, `unswitching`, `unrolling`, `versioning` có nhánh dự phòng, và hợp nhất chuỗi bộ lặp lười (`Iterator Pipeline Fusion`).
   - **`E15.4` (`SPEC-73`, `T613`, `T064`, `T614`, `T615`, `INV-PIPE-011`)**: Phân tích đồ thị lời gọi `CallGraph` theo thành phần liên thông mạnh Tarjan `SCC` (`Result<T, E>` không bị nhầm là `MayPanic`), truyền bản sao/di chuyển bảo toàn cờ hủy, phân rã vô hướng đệ quy các kiểu tổng hợp (`SROA`) và `RVO`/`NRVO`, nội tuyến hàm/bao đóng tách biệt tính hợp lệ (`InlineLegality`) khỏi mô hình chi phí (`CostModel`) (`@inline`, `@inline(always)`, `@inline(never)`), chuyên biệt hóa điểm gọi/hằng/bao đóng (`SpecializationKey`) có kiểm soát ngân sách và bảo toàn định danh con trỏ hàm (`address_taken_fn`), khử ảo hóa 3 tầng (`Exact`, `Guarded`, `RetainedDynamic`), và hạ đệ quy đuôi xuống vòng lặp ngăn xếp $O(1)$ (`@tailcall`).
   - **`E15.5` (`SPEC-74`, `T616`–`T619`, `INV-VEC-001..003`)**: Tự động vector hóa vòng lặp (`opt_loop_vec`) và khối lệnh thẳng (`opt_slp_vec` — `SLP`) trên `OptIR` trước khi hạ xuống LIR mà không cần chú thích mã nguồn, chứng minh độc lập phụ thuộc bộ nhớ từ tính tách biệt năng lực (`mut_view<[T]>` so với `view<[T]>`) và khoảng `SCEV`, bảo toàn thứ tự dấu phẩy động IEEE-754 nghiêm ngặt mặc định bên cạnh thu gọn kết hợp (`wrapping_*`, bitwise, `min`/`max`), sinh vòng lặp vô hướng phần dư (`N % VF`) cho mọi độ dài mảng, mô hình chi phí `VectorCostModel` (`SSE2` 128-bit / `AVX2` 256-bit) hạ xuống `LIR` `Vec128`/`Vec256` kèm `VZEROUPPER`, và truy vết `Source → MIR → OptIR → LIR → Machine` (`--emit=vectorize`, `--emit=vector-cost`).
   - **`E15.6` (`SPEC-75`, `T620`–`T623`, `INV-PIPE-012`)**: Tối ưu hóa thời điểm liên kết đa chế độ (`--lto=off|thin|full`) dùng tóm tắt `.axmeta`, phân tích khả đạt thế giới đóng từ tập gốc tường minh (`@entry`, `@export`, FFI, phản xạ, `@at` MMIO), nội tuyến/chuyên biệt hóa/khử ảo hóa RTA xuyên mô-đun, khử trùng lặp thực thể tổng quát (`generic instances`), thu gom rác mức section (`COMDAT` GC) kèm gộp mã đồng nhất an toàn định danh (`Safe ICF` dùng thunk nhảy 5-byte `0xE9 jmp rel32` khi địa chỉ hàm được lấy), và đường ống `--pgo-gen` / `--pgo-use` tất định trong đó hồ sơ thực nghiệm (`Observed`) chỉ dẫn đường cho mô hình chi phí mà không bao giờ thay thế chứng minh ngữ nghĩa (`Certainty.Proven`).
   - **`E15.7` (`SPEC-76`, `T624`–`T626`, `INV-PIPE-013`)**: Hợp đồng hiệu năng thực thi bảo toàn ngữ nghĩa đồng nhất xuyên mọi cấu hình (`--interp`, `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, `--pgo-use`) không có UB an toàn và không phụ thuộc runtime nguyên khối, mô hình kích thước nhị phân 3 chiều (`FileSize`, `MappedSize`, `WorkingSet`) kèm bố cục phân cụm nhiệt độ `.text` (`StartupEntrySet -> HotCluster -> WarmNormal -> ColdSplit`), đo đếm `--time-passes` và `--size-report` trực giao với tính tất định nhị phân, cùng 7 bộ benchmark chuẩn (`tools/bench`) và 9 ngân sách hồi quy CI (`BUDGET-CTIME-001`..`BUDGET-SELF-002`) được kiểm định tự động qua `tools/perf.py --check-budgets`.
   - **`E15.8` (`SPEC-77`, `T627`, `T063`, `T628`, `T629`, `INV-PIPE-006..007`)**: Chạy đầu tiên trong P15 để tăng tốc chính `axiomc`: phân tích độ sống ngược RPO và khoảng sống có trọng số độ sâu vòng lặp $10^d$, cấp phát thanh ghi quét tuyến tính (`Linear-Scan Register Allocation`) tôn trọng ràng buộc thanh ghi cố định (`rcx` cho dịch bit, `rax`/`rdx` cho nhân/chia) và clobber qua lời gọi hàm Win64, hợp nhất `mov` (`Copy Coalescing`), tô màu khe tràn và bảo toàn thanh ghi callee-saved trong `FrameLayout`, lựa chọn lệnh địa chỉ phức hợp `lea` và nhân/chia hằng số bằng số ma thuật, chuyển đổi nhánh kim cương không rẽ nhánh (`cmovcc`/`setcc`) không đầu cơ lệnh gây bẫy, tối ưu peephole hậu cấp phát an toàn cờ `EFLAGS`, và giữ Machine IR hậu cấp phát (`--emit=mi`) có thể kiểm tra độc lập trước khi mã hóa byte (`--emit=mc`).
2. **Độ phủ yêu cầu, hiệu năng và kiểm chứng toàn cục**: Toàn bộ **411 yêu cầu** ánh xạ vào `P15-optimizer-2-0` đều đạt trạng thái `done`; `reqcov.py --strict` báo cáo `gaps: 0` (`COVERAGE OK`); `archcheck.py` quét 197 tệp nguồn với `0 violations`; `harness_check.py` đạt `HARNESS OK`; `tools/perf.py --compiler build/axiomc2.exe --check-budgets` vượt qua toàn bộ 7 benchmark và 9 ngân sách CI (exit `0`); toàn bộ 11 bất biến của P15 (`INV-PIPE-006`..`INV-PIPE-013`, `INV-VEC-001`..`INV-VEC-003`) và 8 bộ kiểm thử `conformance/p15` vượt qua 100% (`TOTAL 193 PASS 193 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`).

---

## 1. Phase 15 (`P15-optimizer-2-0`) Completion Summary

- **Phase Tasks**: All `32 / 32` implementation, specification, and epic conformance tasks (`T063`, `T064`, `T600`–`T629`) plus planning task `T215` are `done` and verified via QA gates.
- **Canonical Specifications Delivered (`SPEC-70`–`SPEC-77`)**:
  - `spec/SPEC-70-optir-ssa-memoryssa.md` (`T600`): `AXS-OPT-001..047` (`INV-PIPE-008`).
  - `spec/SPEC-71-alias-escape-promotion.md` (`T605`): `AXS-ALIAS-001..006`, `AXS-ESC-001..017` (`INV-PIPE-009`).
  - `spec/SPEC-72-loops-scev-bce.md` (`T609`): `AXS-LOOP-001..018`, `AXS-BCE-001..006` (`INV-PIPE-010`).
  - `spec/SPEC-73-inlining-specialization-devirt.md` (`T613`): `AXS-INL-001..035` (`INV-PIPE-011`).
  - `spec/SPEC-74-auto-vectorization.md` (`T616`): `AXS-VEC-001..053` (`INV-VEC-001..003`).
  - `spec/SPEC-75-lto-wpo-section-gc-pgo.md` (`T620`): `AXS-LTO-001..030`, `AXS-PGO-001..016` (`INV-PIPE-012`).
  - `spec/SPEC-76-performance-contract.md` (`T624`): `AXS-PERF-001..044` (`INV-PIPE-013`).
  - `spec/SPEC-77-regalloc-machine-opt.md` (`T627`): `AXS-RA-010..027`, `AXS-MCOPT-001..026` (`INV-PIPE-006`, `INV-PIPE-007`).

---

## 2. Epic Exit-Criterion Verification (`E15.1`–`E15.8`)

### 2.1 `E15.1` — `OptIR`: SSA, `MemorySSA`, Pass-Contract Verifier & Scalar Optimization (`SPEC-70`, `T600`–`T604`)
- **Subsystems**: `compiler/opt/optir/mod.ax`, `compiler/opt/effects/mod.ax`, `compiler/opt/passmgr/mod.ax`, `compiler/opt/scalar/mod.ax`.
- **Exit Criteria Certified**:
  - `OptIR` is lowered exclusively from `Verified MIR` (`optimizer.inference = None`), computing Cooper-Harvey-Kennedy `DominatorTree`, dominance frontiers, minimal `OptPhi` nodes, and `MemorySSA` (`LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi`) with round-trip verification (`INV-PIPE-008`).
  - `PassManager` enforces declarative `TransformationContract` preconditions, postconditions, analysis invalidation, and fail-closed rollback whenever a candidate proof is `Certainty.Possible` or `Certainty.Unknown`.
  - Unified scalar optimization (`SCCP`, dominator-scoped `GVN`, commutative `CSE`, `SROA`, `DCE`, and `InstCombine`) preserves checked-arithmetic overflow/division-by-zero traps (distinguishing them from modular `wrapping_*`), `NaN`/`-0.0` floating-point hazards, deterministic LIFO `Drop` order, explicit `Clone` calls, ordered UTF-8 I/O, `atomic`, `volatile`, `black_box`, and unread secret `zeroize` barriers across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
- **Verification Suite**: `tests/run/optir_ssa`, `tests/run/opt_passmgr`, `tests/run/opt_scalar`, `tests/conformance/p15/e15_1_optir_ssa` (`PASS`, `0 WEAK-NATIVE`).

### 2.2 `E15.2` — Capability-Driven Alias Analysis, Escape Analysis & Allocation Promotion (`SPEC-71`, `T605`–`T608`)
- **Subsystems**: `compiler/opt/alias/mod.ax`, `compiler/opt/memopt/mod.ax`, `compiler/opt/escape/mod.ax`, `compiler/own/cap.ax`.
- **Exit Criteria Certified**:
  - `AliasInfo` derives `NoAlias` and `MustAlias` from verified `mut_view<T>` exclusivity, `view<T>` read-only immutability, distinct `AllocationIdentity` roots, and disjoint field/slice projections while keeping raw-pointer and FFI aliasing conservative (`MayAlias`/`UnknownAlias`) (`INV-PIPE-009`).
  - Unified `MemorySSA` memory optimizations perform store-to-load forwarding, redundant load elimination (`RLE`), dead store elimination (`DSE`), and overlap-safe `memcpy`/`memmove` lowering while respecting `volatile`, `atomic`, `zeroize`, `black_box`, and `@at` MMIO barriers.
  - Interprocedural Tarjan SCC `EscapeInfo` (`NoEscape < ArgumentEscape < ReturnEscape < GlobalEscape`) promotes non-escaping `Box<T>` allocations, closure environments (`TY_CLOSURE` preserving parameter/return types and `CAP_COPY`/`CAP_VIEW`/`CAP_MUT_VIEW`/`CAP_MOVE` capability checks), bounded buffers, and caller-allocated return slots (`NRVO`) to stack frames or SSA registers while honoring `address_of`/`address_of_mut` stable-address barriers and LIFO `Drop` ordering.
- **Verification Suite**: `tests/run/opt_alias`, `tests/run/opt_escape`, `tests/conformance/p15/e15_2_alias_escape` (`PASS`, `0 WEAK-NATIVE`).

### 2.3 `E15.3` — Canonical Loop Analysis, Overflow-Faithful `SCEV`, `BCE` & Loop Transformations (`SPEC-72`, `T609`–`T612`)
- **Subsystems**: `compiler/opt/loops/mod.ax`, `compiler/opt/bce/mod.ax`, `compiler/opt/loop_xform/mod.ax`.
- **Exit Criteria Certified**:
  - CFG backedge natural loop discovery, `LoopSimplify` (`preheader`, single `latch`, dedicated exits), and `LCSSA` boundary `phi` placement preserve ownership, capability, `Drop`, `await`, and FFI invariants (`INV-PIPE-010`).
  - Overflow-faithful `SCEV` (`{start, +, step}<mode>`) and `RangeInfo` eliminate bounds checks (`BCE_PROVEN_SAFE`) on fixed arrays, slices, multi-slice zip loops, `Vec<T>`, descending loops, and adjacent half-open subslices `[0..mid)` / `[mid..len)` when `0 <= idx < len` is `Certainty.Proven`, and strictly retain runtime bounds traps (`exit: 101`) when unproven or when `Vec.len` shrinks in-loop.
  - `LICM` (blocking trap hoisting out of potentially zero-trip or guarded paths), overflow-gated induction variable strength reduction, loop peeling, unswitching, bounded unrolling, loop versioning with a verified scalar fallback, loop fusion, and lazy iterator pipeline fusion preserve exact observable behavior across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
- **Verification Suite**: `tests/run/opt_bce`, `tests/run/opt_loops`, `tests/conformance/p15/e15_3_loops_bce` (`PASS`, `0 WEAK-NATIVE`).

### 2.4 `E15.4` — Inlining, `SROA`, Call-Site Specialization, Devirtualization & Tail-Call Optimization (`SPEC-73`, `T613`, `T064`, `T614`, `T615`)
- **Subsystems**: `compiler/opt/sroa/mod.ax`, `compiler/opt/inline/mod.ax`, `compiler/opt/ipa/mod.ax`, `compiler/opt/devirt/mod.ax`.
- **Exit Criteria Certified**:
  - Tarjan `SCC` call-graph construction and bottom-up summary propagation (`EffectSummary`, `EscapeSummary`, `AliasSummary`) distinguish `Result<T, E>` normal return values from `MayPanic` and bound recursive `SCC` expansion (`INV-PIPE-011`).
  - Ownership-aware copy/move propagation, deep recursive `SROA`, caller `RVO`/`NRVO`, and 2-stage `InlineLegality` vs `CostModel` inlining (`@inline`, `@inline(always)`, `@inline(never)`) erase unobservable wrapper/closure/iterator boundaries while preserving left-to-right argument evaluation and inner LIFO `Drop` order on panic.
  - Canonical `SpecializationKey` constant/closure specialization respects `SpecializationBudget` and `address_taken_fn` function-pointer identity; 3-tier devirtualization lowers proven single-target `dyn Trait`/fn-ptr calls to direct inlinable calls (`DEVIRT_TIER_EXACT`), finite target sets to guarded switch dispatch (`DEVIRT_TIER_GUARDED`), and open-world/exported calls to retained dynamic dispatch (`DEVIRT_TIER_RETAINED_DYNAMIC`); tail-call optimization (`@tailcall`) lowers self-tail-recursion to $O(1)$-stack loops when no live post-call `Drop` or stack-borrowed `view` escapes.
- **Verification Suite**: `tests/opt2`, `tests/run/opt_ipa_devirt`, `tests/conformance/p15/e15_4_inline_specialize_devirt` (`PASS`, `0 WEAK-NATIVE`).

### 2.5 `E15.5` — Loop & `SLP` Auto-Vectorization (`SPEC-74`, `T616`–`T619`)
- **Subsystems**: `compiler/opt/vectorize/mod.ax`, `compiler/opt/slp/mod.ax`, `compiler/lir/vec_lower/mod.ax`.
- **Exit Criteria Certified**:
  - Annotation-free loop auto-vectorization (`opt_loop_vec`) and straight-line basic-block `SLP` pack-tree vectorization (`opt_slp_vec`) run on `OptIR` before LIR lowering, using `AliasInfo` capability disjointness (`mut_view<[T]>` vs `view<[T]>`) and `SCEV` distance proofs while failing closed to scalar code on `MayAlias`/`UnknownAlias`, `atomic`, or `volatile` barriers (`INV-VEC-001`, `INV-VEC-002`).
  - Preserves strict IEEE-754 floating-point ordering by default while vectorizing associative reductions (`wrapping_*`, bitwise, `min`/`max`, proven `NoOverflow`), generates scalar remainder epilogue loops (`N % VF`) for zero, unit, prime, aligned, and unaligned trip counts, lowers through `TargetDesc`-driven `VectorCostModel` to `LIR` `Vec128`/`Vec256` (`SSE2`/`AVX2`) with `VZEROUPPER` hygiene, and emits deterministic `Source → MIR → OptIR → LIR → Machine` vectorization remarks (`--emit=vectorize`, `--emit=vector-cost`) (`INV-VEC-003`).
- **Verification Suite**: `tests/run/opt_loop_vec`, `tests/run/opt_slp_vec`, `tests/conformance/p15/e15_5_autovec` (`PASS`, `0 WEAK-NATIVE`).

### 2.6 `E15.6` — Whole-Program `LTO`, Section GC / `ICF` & `PGO` (`SPEC-75`, `T620`–`T623`)
- **Subsystems**: `compiler/opt/lto/mod.ax`, `compiler/link/gc_icf/mod.ax`, `compiler/opt/pgo/mod.ax`.
- **Exit Criteria Certified**:
  - Supports `--lto=off|thin|full` with `.axmeta` summary serialization and `ThinLTO` partition rebuild detection, computing closed-world reachability from explicit roots (`@entry`, `@export`, FFI callbacks, reflection, `@at` MMIO) to internalize non-exported symbols, inline/specialize/devirtualize across modules, and deduplicate representation-equivalent generic instantiations while preserving observable function-pointer addresses (`INV-PIPE-012`).
  - Linker section GC (`COMDAT` dead stripping with `.pdata` unwind reclamation) and `Safe ICF` (emitting 5-byte `0xE9 jmp rel32` identity thunks when `address_taken == true`) reduce 3D binary size (`FileSize`, `MappedSize`, `WorkingSet`) without re-inferring source ownership.
  - Deterministic AOT `--pgo-gen` → `pgo_merge_profiles` → `--pgo-use` pipeline treats profile counts strictly as `Observed` profitability weights (`CostModel`), gracefully degrades on stale profiles (`PGO_COMPAT_STALE`), and never upgrades `Possible`/`Unknown` safety, bounds, or alias obligations to `Proven`.
- **Verification Suite**: `tests/run/opt_lto`, `tests/run/opt_pgo_gc`, `tests/conformance/p15/e15_6_lto_pgo_gc` (`PASS`, `0 WEAK-NATIVE`).

### 2.7 `E15.7` — Performance Contract, 3D Binary Footprint, Telemetry & CI Regression Budgets (`SPEC-76`, `T624`–`T626`)
- **Subsystems**: `compiler/driver/perf_telemetry/mod.ax`, `tools/perf.py`, `tools/bench/`.
- **Exit Criteria Certified**:
  - Certifies identical observable semantics across `--interp`, `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, and `--pgo-use` with zero safe UB and zero monolithic runtime dependency (`INV-PIPE-013`).
  - Exposes deterministic `--time-passes` and `--size-report` JSON telemetry (`FileSize`, `MappedSize`, `StartupWorkingSet`, `PeakWorkingSet`, `.bss` zero-file-bytes, thermal `.text` clustering) that never alters emitted binary bytes (`det_a == det_b`).
  - `tools/perf.py --compiler build/axiomc2.exe --check-budgets` validates output correctness before accepting timings and enforces all 7 canonical benchmarks (`BENCH-STARTUP-001`..`BENCH-COMPILE-001`) and all 9 quantitative budgets (`BUDGET-CTIME-001`..`BUDGET-SELF-002`).
- **Verification Suite**: `tests/run/perf_contract`, `tests/conformance/p15/e15_7_perf_contract`, `tools/perf.py` (`PASS`, `0 WEAK-NATIVE`).

### 2.8 `E15.8` — Linear-Scan Register Allocation, Instruction Selection & Post-RA Machine Optimization (`SPEC-77`, `T627`, `T063`, `T628`, `T629`)
- **Subsystems**: `compiler/backend/regalloc/mod.ax`, `compiler/target/x64/{isel,frame,verify,print,encode}.ax`, `compiler/backend/peephole/mod.ax`.
- **Exit Criteria Certified**:
  - RPO liveness analysis and loop-depth-weighted (`10^d`) linear-scan register allocation eliminate virtual registers, satisfy pre-colored fixed-register constraints (`rcx` variable shifts, `rax`/`rdx` `div`/`idiv`/`mul`) and Win64 call clobbers, coalesce non-interfering moves, color disjoint spill slots, and save/restore modified callee-saved registers in 16-byte-aligned `FrameLayout` (`INV-PIPE-006`).
  - Pattern-matching instruction selection (`lea` `base + index * scale + disp` addressing while excluding checked `+`/`*` so overflow traps are preserved per `AXS-MCOPT-016`, plus magic-multiply constant division/remainder), non-speculating branchless `cmovcc`/`setcc` diamond if-conversion, and `EFLAGS`-liveness-gated post-RA peepholes (`mov r, r`, `mov r, 0 -> xor r, r`, `cmp r, 0 -> test r, r`, store-reload forwarding with alias/call barriers) pass `x64_verify_checked` and remain inspectable via `axiomc inspect --emit=mi` prior to byte encoding (`--emit=mc`) (`INV-PIPE-007`).
- **Verification Suite**: `tests/mc/regalloc`, `tests/mc/isel_peephole`, `tests/conformance/p15/e15_8_regalloc_isel` (`PASS`, `0 WEAK-NATIVE`).

---

## 3. Governance, Traceability & Quality Gate Evidence

1. **Phase 15 Conformance Suite (`axtest.py -j 1`)**:
   - Command:
     ```bash
     python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p15
     ```
   - Result: `WEAK-NATIVE 0`, `TOTAL 193 PASS 193 FAIL 0 SKIP 0 XFAIL 0` (exit `0`).
2. **Performance Contract & CI Regression Budgets (`perf.py --check-budgets`)**:
   - Command:
     ```bash
     python tools/perf.py --compiler build/axiomc2.exe --check-budgets
     ```
   - Result (exit `0`):
     - `BENCH-STARTUP-001` (`bench_minimal_startup.ax`): `insts=11->8 us=28->21 size=2048->2048 (-Oz=2048) [PASS]`
     - `BENCH-SCALAR-001` (`bench_scalar_loops_bce.ax`): `insts=2033->1001 us=4069->1658 size=10752->6656 (-Oz=6656) [PASS]`
     - `BENCH-MEM-001` (`bench_escape_sroa_alloc.ax`): `insts=2519->1295 us=5038->2141 size=12288->8192 (-Oz=8192) [PASS]`
     - `BENCH-IPA-001` (`bench_iter_inline_devirt.ax`): `insts=1713->805 us=3426->1329 size=8704->5120 (-Oz=5120) [PASS]`
     - `BENCH-SIMD-001` (`bench_simd_autovec_kernel.ax`): `insts=2613->1240 us=5230->2049 size=12800->8192 (-Oz=8192) [PASS]`
     - `BENCH-ALGO-001` (`bench_sort_hash_parse.ax`): `insts=4454->2303 us=8910->3800 size=19968->12288 (-Oz=12288) [PASS]`
     - `BENCH-COMPILE-001` (`bench_compile_throughput.ax`): `insts=2120->1280 us=4241->2114 size=10240->6656 (-Oz=6656) [PASS]`
     - All 9 CI budgets (`BUDGET-CTIME-001`, `BUDGET-SPEED-001`, `BUDGET-IR-001`, `BUDGET-SIZE-001`, `BUDGET-SIZE-002`, `BUDGET-START-001`, `BUDGET-DET-001`, `BUDGET-SELF-001`, `BUDGET-SELF-002`): `PASS`.
3. **Requirements Coverage (`reqcov.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P15-optimizer-2-0`
   - Result: All `411` requirement mappings in `P15-optimizer-2-0` across `T063`, `T064`, and `T600`–`T629` are `done` (`0` planned/todo remaining in P15).
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
   - Result:
     - `requirements: 32308`
     - `v1-core: implemented=5864`
     - `v1-full: implemented=6600 planned=2231`
     - `post-v1: epic=17535 planned=78`
     - `gaps: 0` — **`COVERAGE OK`** (exit `0`).
4. **Architecture Layer Check (`archcheck.py`)**:
   - Command: `python tools/archcheck.py`
   - Result: `archcheck: 197 files scanned, 0 violations` (exit `0`).
5. **Harness & Freeze Integrity Check (`harness_check.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/harness_check.py`
   - Result: `HARNESS OK` (exit `0`; `bootstrap/axiom0` remains untouched since `axiom0-frozen`).

---

## 4. Spec Drift, Shortcuts to Retire & Follow-Ups for `axiom-architect`

- **Phase 15 Spec Drift**: None. All eight canonical specifications (`SPEC-70` through `SPEC-77`) and all 11 Phase 15 invariants (`INV-PIPE-006`..`INV-PIPE-013`, `INV-VEC-001`..`INV-VEC-003`) match their implemented subsystems and conformance oracles with `0` `xfail` entries and `0` shortcuts remaining in P15.
- **Shortcuts Retired in P15**:
  - Retired the Stage-0/Stage-1 stack-spill-everything register allocation and naive instruction selection in `compiler/` (`T063`, `T628`, `T629`): replaced with RPO linear-scan register allocation, move coalescing, spill-slot coloring, `lea` scaled addressing, magic-multiply division, branchless `cmovcc`/`setcc` if-conversion, and `EFLAGS`-safe post-RA peepholes (`SPEC-77`).
  - Retired the Stage-1 local-only `-O1` peephole/const-fold ceiling (`T064`, `T601`–`T626`): `compiler/opt/` now provides the full `OptIR` SSA + `MemorySSA` pipeline, `PassManager` fail-closed proof contracts, capability-driven `AliasInfo` & `EscapeInfo` allocation promotion, overflow-faithful `SCEV` & `BCE`, interprocedural `SCC` inlining/specialization/devirtualization/tail-call lowering, loop & `SLP` SIMD auto-vectorization, `--lto=thin|full` + `COMDAT` section GC/`Safe ICF` + `--pgo-gen`/`--pgo-use`, and CI-enforced performance budgets (`tools/perf.py --check-budgets`).
- **Follow-Ups for `axiom-architect`**:
  - None for P15 (`0` spec deviations, `0` remaining P15 shortcuts).

## Files changed
- tests/conformance/p15/README.md
- ./_workspaces/reports/phase-P15-review.md
