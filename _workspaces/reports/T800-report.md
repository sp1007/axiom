# T800 Report — E19.1 Canonical LSP Server, IDE Semantic Engine, `AXEDITOR`/`AXCODEEDITOR` & VS Code Extension Specification (`SPEC-100`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-100-lsp-server-ide-engine.md` (`AXS-LSP-001..004`, `AXS-LSP-010..012`, `AXS-LSP-020..022`, `AXS-LSP-030..032`, `AXS-LSP-040..043`, `AXS-LSP-050..052`, `AXS-LSP-060..063` — tổng cộng 23 quy tắc chuẩn hóa) cho máy chủ ngôn ngữ chuẩn `axiomc lsp`, bộ máy ngữ nghĩa IDE chia sẻ trực tiếp `CompilerDB` (`SPEC-21`/`SPEC-22`), bộ đệm văn bản file lớn hỗ trợ Unicode đầy đủ `std.editor` (`AXEDITOR`), hệ thống tô sáng ngữ nghĩa / hiển thị inlay sở hữu–di chuyển–bất đồng bộ / gợi ý hoàn thành mã nguồn (`AXCODEEDITOR`), và kiến trúc tiện ích mở rộng VS Code mỏng (`tools/vscode-axiom`). Đồng bộ hóa đăng ký vào `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-021`, `AXD-040`, `## Sources`), và `spec/invariants.md` (nhóm `LSP`, mục §46 với `INV-LSP-001`..`INV-LSP-003`, và `## Sources`).

## Key Architectural Decisions & Specification Rules (`SPEC-100`)
1. **Single Semantic Authority & Generational Entity IDs (`AXS-LSP-001`..`004`, `REQ-TOOL-183`, `REQ-TOOL-184`, `REQ-TOOL-185`, `REQ-TOOL-191`, `REQ-TOOL-297`, `REQ-TOOL-298`)**:
   - `CompilerDB` (`SPEC-21` / `SPEC-22`) là nguồn chân lý ngữ nghĩa duy nhất cho CLI (`axiomc check`/`build`), máy chủ LSP (`axiomc lsp`), bộ máy IDE, và các trình soạn thảo (`AXEDITOR`/`AXCODEEDITOR`). Nghiêm cấm tạo bộ phân tích cú pháp hay bộ suy luận kiểu riêng cho IDE.
   - Mọi thực thể ngữ nghĩa đều được định danh bằng ID thế hệ có kiểu mạnh (`SymbolId`, `TypeId`, `FunctionId`, `LocalId`, `PlaceId`) với phạm vi mô-đun `(ModuleId, LocalIndex)` (`SPEC-23 AXS-PAR-003`), giữ nguyên định danh qua các lần sửa thân hàm cục bộ khi chữ ký mục không đổi (`InterfaceFingerprint` không đổi).
   - Mọi truy vấn IDE tương tác chỉ thực thi đến tầng `CheckItem`/`CheckBody` và phân tích dòng chảy MIR cục bộ trên `DatabaseSnapshot`; tuyệt đối không kích hoạt `OptIR`, `LIR`, `ObjectEmit`, hay `Linker` (`0` lệnh gọi sinh mã).
2. **JSON-RPC 2.0 Transport, `VfsOverlay` & Multi-Encoding `LineIndex` (`AXS-LSP-010`..`012`)**:
   - Giao thức dây JSON-RPC 2.0 đóng khung `Content-Length: <N>\r\n\r\n`, quản lý vòng đời `initialize` -> `initialized` -> `shutdown` -> `exit`, và hủy bỏ hợp tác `$/cancelRequest` (`-32800` `RequestCancelled`).
   - `VfsOverlay` ưu tiên tuyệt đối bộ đệm đang mở trong bộ nhớ (`didOpen`/`didChange`/`didClose`/`didSave`) và ánh xạ trực tiếp vào `CompilerDB.SourceText(FileId)` để kích hoạt lan truyền bẩn–xanh (`try_mark_green`).
   - `LineIndex` chuyển đổi hai chiều không mất mát trong $O(\log L)$ giữa độ lệch byte UTF-8, đơn vị mã UTF-16 (mặc định của LSP 3.17), và giá trị vô hướng Unicode UTF-32 (`SPEC-01 §1`).
3. **`std.editor` (`AXEDITOR`) Large-File Unicode Text Buffer (`AXS-LSP-020`..`022`, `tasks/1053`, `REQ-TOOL-299`)**:
   - Cấu trúc bảng mảnh cây B (`PieceTree`) bất biến chia sẻ cấu trúc qua chụp nhanh CoW (`PieceTreeSnapshot`), đạt $O(\log P)$ cho chèn/xóa/tách dòng, độ trễ sửa đổi tăng dần `< 2` ms p99 trên tệp `>= 10` MiB, bảo toàn ranh giới cụm ký tự hiển thị Unicode (`grapheme cluster`) và chuỗi tiếng Việt có dấu (`"Xin chào thế giới"`), hỗ trợ đa con trỏ (`SelectionSet`), giao dịch hoàn tác/làm lại nguyên tử (`EditTransaction`), và chỉ mục tìm kiếm gia tăng (`SearchIndex`).
4. **Partial-Program Syntax & Semantic Recovery (`AXS-LSP-030`..`032`, `REQ-TOOL-188`)**:
   - Phục hồi cú pháp không hoảng loạn (`panic-free`) cho biểu thức truy cập thành viên bỏ dở (`buf.`), danh sách đối số chưa đóng (`process(buf, `), khối lệnh thiếu `}`, và nhánh `match` chưa hoàn chỉnh.
   - Cô lập nhiễm độc cục bộ (`ExprKind.Error`, `PatKind.Error`, `TypeId.ERROR` theo `AXD-044`) giúp bảo toàn 100% chữ ký các mục anh em trong mô-đun và môi trường biến cục bộ hợp lệ trước điểm con trỏ.
5. **Constraint-Aware Semantic IDE Queries (`AXS-LSP-040`..`043`, `0101 §6-13`, `0146 §31-37`, `tasks/0450`, `REQ-TOOL-189`)**:
   - Hoàn thành mã nguồn (`textDocument/completion`) lọc chính xác theo phạm vi hiển thị mô-đun (`pub`), trạng thái sống của sở hữu/di chuyển (loại bỏ biến `!Copy` đã bị `move`), quyền năng của đối tượng nhận (`view<T>` chỉ cho phép phương thức nhận `view<T>` / bất biến, loại bỏ phương thức nhận `mut self` hoặc tiêu thụ `self`; `mut_view<T>` cho phép phương thức nhận `view<T>` và `mut_view<T>`, loại bỏ phương thức tiêu thụ `self`), và ràng buộc trait/associated items.
   - Định nghĩa chuẩn xác cho `hover`, `goto_definition`, `find_references`, và `prepareRename`/`rename` có kiểm tra vệ sinh từ vựng, xung đột bóng tên (`shadowing`), và bảo toàn ngữ nghĩa toàn không gian làm việc.
6. **`AXCODEEDITOR` & Thin VS Code Extension (`AXS-LSP-050`..`052`, `0101 §38-41`, `tasks/1054`, `REQ-TOOL-300`)**:
   - `AXCODEEDITOR` xuất luồng token ngữ nghĩa mã hóa delta (`semanticTokens/full`, `semanticTokens/range`) với các bổ từ chuyên biệt của Axiom (`mutable`, `consumed`, `viewCap`, `mutViewCap`, `asyncBound`, `comptimeEval`, `unsafeOp`) và hệ thống gợi ý inlay (`inlayHint`) hiển thị kiểu suy luận, tên tham số, điểm chuyển giao sở hữu (`move`), mượn ngầm định (`view`/`mut_view`), điểm tạm dừng `.await`, và giá trị hằng `comptime`, kết nối trực tiếp với các bản vá `AXD-055` qua `textDocument/codeAction`.
   - Tiện ích mở rộng VS Code (`tools/vscode-axiom`) đóng vai trò trình khách mỏng thuần túy, ủy quyền 100% phân tích ngữ nghĩa cho `axiomc lsp`.
7. **Diagnostics, Invariants & E19.1 Verification Matrix (`AXS-LSP-060`..`063`, `INV-LSP-001`..`003`)**:
   - Tái sử dụng 100% mã chẩn đoán chuẩn `AX_<AREA>_<NAME>` và thứ tự `AXD-060` qua `textDocument/publishDiagnostics`, ánh xạ tường minh các mã ví dụ trong kho tư liệu (`AX_METHOD_0001`, `AX_VIEW_0001..0007`, `AX_MOVE_0003`, `AX_TRAIT_0012`, `ATYPE-204`, `ACAP-204`) sang mã chuẩn hiện hành, và đăng ký `INV-LSP-001` (`since: T801`), `INV-LSP-002` (`since: T802`), `INV-LSP-003` (`since: T803`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`requirements: 32308`, `gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T800`: khớp chính xác 4 tệp trong `paths:` và `locks:`.

## Files changed
- ./spec/SPEC-100-lsp-server-ide-engine.md
- ./spec/INDEX.md
- ./spec/diagnostics.md
- ./spec/invariants.md

STATUS: COMPLETE round=0
