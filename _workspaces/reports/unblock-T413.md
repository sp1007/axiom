# Unblock T413 — E11.3: @thread_local statics, COFF/PE .tls emission & thread-local storage

## Tóm tắt
- Task `T413` (`owner: axiom-backend`) bị chặn do thiếu locks để hoàn thiện phát thải COFF/PE `.tls` và tra cứu TLS x86-64 trên Windows: `compiler/link/linker.ax`, `compiler/target/x64/encode.ax`, `compiler/target/x64/frame.ax`, `compiler/driver/pipeline.ax`, `compiler/diag/code.ax`.
- Kiến trúc sư đã tiến hành rà soát toàn bộ chu trình xử lý (pipeline seam audit) từ HIR -> Typeck -> Own (`!Share` / non-escaping borrow check) -> MIR -> Verifier -> Interp/Oracle -> LIR -> x64 -> ObjModel/COFF -> PE Linker -> Driver.
- Rà soát xác định ngoài 5 tệp kỹ sư yêu cầu, cần bổ sung đồng bộ các tệp định nghĩa và kiểm tra liên quan (`compiler/hir/hir.ax`, `compiler/own/unsafe.ax`, `compiler/mir/mir.ax`, `compiler/verify/verifier.ax`, `compiler/interp/oracle.ax`, `compiler/lir/lir.ax`, `compiler/target/x64/mod.ax`, `compiler/backend/session.ax`, `compiler/obj/writer.ax`, `compiler/link/mod.ax`) vào danh sách `locks:` của `T413` để đảm bảo kỹ sư hiện thực trọn vẹn hạ tầng `@thread_local` mà không gặp bất kỳ xung đột lock nào nữa.
- Quyết định phân loại: **TYPE A** (mở rộng danh sách locks hiện thực theo đúng đặc tả `spec/SPEC-32-threads-sync.md` và `spec/SPEC-04-core-extensibility.md`, không thay đổi cú pháp hay ngữ nghĩa ngôn ngữ).
- Cập nhật danh sách 25 locks đồng bộ trong task card `_workspaces/tasks/todo/T413-e11-3-thread-local-storage-coff-pe-tls.md` và thực thi `taskctl.py unblock T413`.
- Đã xác thực thành công qua `taskctl.py lint`, `taskctl.py validate` (599 tasks OK, 0 blocked), `reqcov.py --strict` (COVERAGE OK, 0 gaps), và `harness_check.py` (HARNESS OK). Task `T413` đã trở về trạng thái `todo` và sẵn sàng chạy (`ready: T413`).

## Decision & Pipeline Seam Audit

Classification: **TYPE A** (implementation lock set extension for planned feature; no syntax or semantic model change, no ADR required).

### Seam Audit Details
Để đảm bảo quy trình phát thải `@thread_local` hoạt động xuyên suốt từ đầu đến cuối không bị gián đoạn do thiếu lock, danh sách lock được mở rộng đồng bộ qua các tầng:

1. **HIR / Diagnostics / Typeck / Own (`!Share` & Borrow Check)**:
   - `compiler/diag/code.ax`: Định nghĩa mã chẩn đoán 166 (`AX_CONC_TLS_ESCAPE`) và 167 (`AX_TYPE_INVALID_TLS_DECL`).
   - `compiler/hir/hir.ax`: Khai báo cờ và cấu trúc thuộc tính `HirItem` cho `@thread_local`.
   - `compiler/hir/lower.ax`: Hạ giải thuộc tính `@thread_local` từ AST sang HIR (đã có trong lock).
   - `compiler/types/typeck.ax`: Kiểm tra tính hợp lệ của khai báo static `@thread_local` (đã có trong lock).
   - `compiler/own/unsafe.ax`: Kiểm tra miễn trừ `Share` cho TLS static và kiểm tra nghiêm ngặt không cho phép `view<T>` mượn từ TLS static thoát ra khỏi phạm vi tiểu trình hiện tại (`AX_CONC_TLS_ESCAPE`, `0136 §53`).

2. **MIR / Verifier / Interp Oracle**:
   - `compiler/mir/mir.ax`: Định nghĩa cấu trúc place / const / operand cho TLS trong MIR.
   - `compiler/mir/builder.ax`: Hạ giải biểu thức truy cập static place sang MIR (đã có trong lock).
   - `compiler/verify/verifier.ax`: Kiểm tra tính hợp lệ của place, kiểu dữ liệu và ràng buộc capability mượn trên MIR.
   - `compiler/interp/interp.ax`: Quản lý bộ nhớ TLS cách ly theo từng tiểu trình trong trình thông dịch MIR (đã có trong lock).
   - `compiler/interp/oracle.ax`: Theo dõi vòng đời tiểu trình máy chủ và vector clocks cho phân tích data race.

3. **LIR (Low-level IR)**:
   - `compiler/lir/lir.ax`: Định nghĩa tập lệnh hạ tầng (`LIR_INST_TLS_ADDR`), cấu trúc dữ liệu LIR và text printer.
   - `compiler/lir/builder.ax`: Hạ giải từ MIR sang LIR với toán tử địa chỉ TLS (đã có trong lock).

4. **Target x86-64 Backend**:
   - `compiler/target/x64/encode.ax`: Tiền tố phân đoạn GS (`0x65`) và mã hóa chỉ thị x64.
   - `compiler/target/x64/frame.ax`: Mã hóa chỉ thị máy `x64_encode_mi_inst_obj`, phát chuỗi 4 lệnh tra cứu TLS qua `gs:[0x58]` (`mov r_tmp, gs:[0x58]`, `mov r_idx, [rip + _tls_index]`, `mov r_base, [r_tmp + r_idx*8]`, `lea r_dst, [r_base + sym@SECREL32]`) cùng relocations `IMAGE_REL_AMD64_REL32` và `IMAGE_REL_AMD64_SECREL`.
   - `compiler/target/x64/isel.ax`: Lựa chọn chỉ thị x64 cho địa chỉ TLS (đã có trong lock).
   - `compiler/target/x64/mod.ax`: Tái xuất các hằng số và hàm mã hóa máy x64 ra toàn bộ compiler.

5. **COFF Object Model & Serialization**:
   - `compiler/obj/coff.ax`: Khai báo section `SEC_TLS` (`.tls$`), kiểu relocation `AX_RELOC_X86_64_TLSREL` / `IMAGE_REL_AMD64_SECREL` (đã có trong lock).
   - `compiler/obj/writer.ax`: Xuất định dạng nhị phân COFF (.obj), hỗ trợ ghi nhận section characteristics và relocation addends cho TLS.
   - `compiler/backend/session.ax`: Quản lý phiên phát thải `ObjModel` từ HIR/MIR/LIR và bảng hằng số.
   - `compiler/driver/pipeline.ax`: Trình điều khiển biên dịch phát thải dữ liệu `@thread_local static` vào section `.tls$` trong `ObjModel`.

6. **PE Linker**:
   - `compiler/link/pe.ax`: Cấu trúc PE header và TLS directory `IMAGE_DIRECTORY_ENTRY_TLS` (đã có trong lock).
   - `compiler/link/linker.ax`: Hợp nhất các section `.tls$`, tổng hợp `_tls_index` (4-byte trong `.data`), `_tls_callbacks` (8-byte trong `.rdata`), và phát bản ghi 40-byte `IMAGE_TLS_DIRECTORY64` (`_tls_used`) để điền Data Directory 9 (`PE_DIR_TLS`).
   - `compiler/link/mod.ax`: Tái xuất API PE Linker.

7. **Standard Library & Tests**:
   - `std/thread/mod.ax`: Tái xuất `LocalKey` và móc hàm dọn dẹp `thread_local_cleanup` khi tiểu trình kết thúc (đã có trong lock).
   - `tests/selfhost`: Bộ kiểm thử tự lưu trữ (đã có trong lock).

## Board changes
- Cập nhật trường `locks:` trong `_workspaces/tasks/todo/T413-e11-3-thread-local-storage-coff-pe-tls.md`:
  `locks: [compiler/diag/code.ax, compiler/hir/hir.ax, compiler/hir/lower.ax, compiler/types/typeck.ax, compiler/own/unsafe.ax, compiler/mir/mir.ax, compiler/mir/builder.ax, compiler/verify/verifier.ax, compiler/interp/interp.ax, compiler/interp/oracle.ax, compiler/lir/lir.ax, compiler/lir/builder.ax, compiler/target/x64/encode.ax, compiler/target/x64/frame.ax, compiler/target/x64/isel.ax, compiler/target/x64/mod.ax, compiler/backend/session.ax, compiler/driver/pipeline.ax, compiler/obj/coff.ax, compiler/obj/writer.ax, compiler/link/pe.ax, compiler/link/linker.ax, compiler/link/mod.ax, std/thread/mod.ax, tests/selfhost]`
- Chạy `python .claude/skills/axiom-tasks/scripts/taskctl.py unblock T413`.
- Trạng thái bàn làm việc: `T413` chuyển từ `blocked` sang `todo`, số lần thử được reset về 0 (`attempts: 0`, `unblocks: 1`), sẵn sàng được nhận lệnh chạy (`ready: T413`).
- Kiểm thử kiểm định:
  - `taskctl.py lint _workspaces/tasks/todo/T413-e11-3-thread-local-storage-coff-pe-tls.md` -> OK
  - `taskctl.py validate` -> OK (599 tasks)
  - `reqcov.py --strict` -> COVERAGE OK (0 gaps)
  - `harness_check.py` -> HARNESS OK

## Safety & Isolation Checks
- Giữ nguyên toàn bộ tiến trình công việc của `T413` trên cây làm việc (`compiler/obj/coff.ax`, `std/thread/local.ax`, `std/thread/mod.ax`), không hoàn tác hay can thiệp.
- Tuyệt đối không chạm vào hay liệt kê các tệp của `T412` đang chạy song song (`std/sync/channel`, `tests/std/channel`, `std/sync/mod.ax`).
- Không chỉnh sửa `docs/` hay `bootstrap/axiom0/`.
- Giữ nguyên trạng thái `deferred` của `T224`.
- Không thực hiện git commit hoặc git push thủ công (bộ điều phối orchestrator sẽ chạy `taskctl.py commit-report`).

## Files changed
- _workspaces/tasks/todo/T413-e11-3-thread-local-storage-coff-pe-tls.md
