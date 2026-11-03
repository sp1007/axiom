# T760 Report — E18.3: Canonical parallel compilation & deterministic DAG scheduling specification (SPEC-23)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-23-parallel-compilation.md` cho E18.3 (Biên dịch song song, ảnh chụp cơ sở dữ liệu ngữ nghĩa an toàn luồng `DatabaseSnapshot`, cấp phát định danh độc lập với thứ tự lập lịch, và bộ lập lịch DAG đánh cắp việc trong `compiler/`):
- Định nghĩa bất biến tương đương tuyệt đối giữa biên dịch tuần tự và song song (`--jobs 1` == `--jobs N`): song song hóa chỉ thay đổi thứ tự thực thi vật lý giữa các luồng worker, tuyệt đối không làm đổi ngữ nghĩa, định danh nội bộ (`DefId`, `HirId`, `TypeId`, `SymbolId`), danh sách/thứ tự chẩn đoán (`AXD-060`), hay từng byte của tệp `.obj`/`.lib`/`.dll`/`.exe` (`APAR-20..24`, `ACOMPILER-30`, `ACOMPARCH-20..60`, `AQUERY-50..80`) (`AXS-PAR-001`..`005`).
- Quy định chia sẻ `DatabaseSnapshot` bất biến, vùng nhớ arena cục bộ theo luồng/truy vấn, cấp phát định danh 2 tầng `(ModuleId, LocalIndex)` (cấm bộ đếm nguyên tử toàn cục tuần tự), và bảng intern chuỗi/kiểu phân mảnh (sharded interner) định địa chỉ theo nội dung (`AXS-PAR-003`..`005`).
- Quy định cơ chế khử trùng lặp truy vấn đang chạy (`SingleFlightLatch`), đồ thị chờ xuyên worker (`WaitForGraph`) phát hiện chu trình tức thời không khóa chết (`AQUERY-51`) kèm xoay chuẩn hóa theo `SemanticKey`, và bộ lập lịch DAG đánh cắp việc (`--jobs N`) điều phối theo đường găng (critical path), ngân sách token tài nguyên (`cpu_cost`, `memory_cost`, `REQ-CORE-3125`, `REQ-CORE-3126`), thực thi suy đoán có kiểm chứng (speculative execution), hủy bỏ ưu tiên cho IDE/LSP, và cô lập hành động kín (hermetic action identity) (`AXS-PAR-010`..`015`).
- Quy định phân hoạch `CodegenUnit` (`CGU`) tất định, hạ bậc LIR / phân bổ thanh ghi / sinh mã `.obj` song song kết hợp bộ nhớ đệm tăng dần `.axiom-cache`, hợp nhất bộ đệm chẩn đoán theo thứ tự chuẩn `AXD-060`, và ghép nối `.obj` vào trình liên kết theo đúng thứ tự chỉ mục `CGU` chuẩn (`AXS-PAR-020`..`024`, `AXS-PAR-050`..`053`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (§29 `INV-PAR-001`..`003`).

## Specification & Index Updates

1. **`spec/SPEC-23-parallel-compilation.md`**:
   - **§1 (`AXS-PAR-001`..`005`)**: Fundamental parallel determinism invariant (`--jobs 1` == `--jobs N`), acyclic compiler architecture & semantic vs representation authority (`ACOMPARCH-20..60`, `AQUERY-51..80`), immutable `DatabaseSnapshot` sharing & per-worker arena isolation, module-scoped `(ModuleId, LocalIndex)` IDs, and sharded deterministic string/type interning.
   - **§2 (`AXS-PAR-010`..`015`)**: In-flight query deduplication & `SingleFlightLatch` state machine, cross-worker `WaitForGraph` deadlock-free cycle detection & canonical rotation, action/query DAG state machine & critical-path work-stealing queue hierarchy, resource-token admission control & memory-pressure governance (`REQ-CORE-3125`, `REQ-CORE-3126`), validated speculative execution & interactive preemption, and hermetic action identity / fault recovery.
   - **§3 (`AXS-PAR-020`..`024`)**: Deterministic `CGU` partitioning & canonical indexing, isolated per-worker LIR lowering / register allocation / COFF `.obj` emission, hybrid incremental cache + parallel codegen execution, deterministic post-join `AXD-060` diagnostic merging, and canonical linker input ordering & finalization barriers.
   - **§4 (`AXS-PAR-050`..`053`)**: Parallel CLI flags (`--jobs`, `--schedule-mode`, `inspect --emit=parallel-trace`), positive and negative canonical Axiom examples (`=` and `.` syntax only), E18.3 verification matrix (`T761`–`T763`), and corpus source citations.
2. **`spec/INDEX.md`**:
   - Added `spec/SPEC-23-parallel-compilation.md` to §2 Canonical documents table.
   - Added `AXS-PAR-NNN` to §4 Identifier namespaces table.
   - Updated §5 Topic -> canonical source table (`Kernel` / parallel compilation row).
3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` (§3) and `## Sources` for E18.3 (`SPEC-23`: cross-worker `WaitForGraph` cycle detection using `SPEC-21` cycle codes and post-join `AXD-060` diagnostic merging).
4. **`spec/invariants.md`**:
   - Added group `PAR` to §1 Groups list.
   - Added §29 (`INV-PAR-001` `since: T761`, `INV-PAR-002` `since: T762`, `INV-PAR-003` `since: T763`) covering `0153 APAR-20..24` and `SPEC-23`, and updated `## Sources`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`requirements: 32308`, `gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T760` → `4 STAGE`, `0 REFUSED`

## Files changed

- `spec/SPEC-23-parallel-compilation.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE round=0
