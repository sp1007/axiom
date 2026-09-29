# Axiom — ngôn ngữ và compiler mới

Tài liệu thiết kế gốc: `docs/base/specs`, `docs/base/tasks` (rất lớn, có mâu thuẫn — tra cứu qua skill
`axiom-spec-index`). `specs/`, `tasks/`, `others/` là kết luận đã phản biện (có giá trị quy chuẩn);
`discussions/` chỉ là bàn bạc, không lấy làm yêu cầu. Spec chuẩn hoá do agent kiến trúc sư viết nằm ở `spec/` và được ưu tiên hơn `docs/base`.

**Quy ước cú pháp bắt buộc:** gán/khai báo chỉ dùng `=` (không có `:=`, không có `var`); phân giải
namespace/thư viện chỉ dùng `.` (không có `::`). Chi tiết: skill `axiom-syntax`.

## Harness: Axiom compiler

**Mục tiêu:** Xây compiler Axiom từ spec → Stage-0 `axiom0` (C11, Windows x64 PE trước) → self-hosting
`axiomc`, bằng đội agent (architect, frontend, semantics, backend, stdlib, qa) với QA gate và auto-commit
sau mỗi task.

**Trigger:** Mọi yêu cầu xây/tiếp tục/sửa/kiểm thử compiler Axiom → dùng skill `axiom-compiler`.
Chạy tự động liên tục → `/tu-dong` (dừng: `/tu-dong dừng`, trạng thái: `/tu-dong trạng thái`); nhịp
giám sát 5 phút → `/axiom-tick`. Quản lý task → `axiom-tasks` (board ở `_workspaces/tasks/{todo,doing,done}`).
Câu hỏi đơn giản có thể trả lời trực tiếp.

**Lịch sử thay đổi:**
| Ngày | Thay đổi | Đối tượng | Lý do |
|------|----------|-----------|-------|
| 2026-09-29 | Khởi tạo harness: 6 agent, 9 skill, 91 task (P0–P11) | toàn bộ | Yêu cầu dựng đội agent xây compiler |
| 2026-09-29 | Thêm truy vết yêu cầu: T092–T109 rút yêu cầu theo 18 khối, T110 catalog, T111 mở rộng backlog; `reqcov.py`; thu hẹp bộ lọc ngoài phạm vi | skills/axiom-spec-index, axiom-tasks, agents/axiom-architect, board | Board chưa phủ hết mục tiêu trong specs và tasks |
| 2026-09-29 | Roadmap cố định P0–P24 (`spec/ROADMAP.md`): 14 task lập kế hoạch T211–T224 (T224 deferred), 13 gate T311–T323; axiom0 đóng băng sau T087; T088–T091 chuyển vào P11/P23; trạng thái `deferred`, `EPIC(...)` trong reqcov | spec/ROADMAP.md, board, agents, skills | Tránh tự sinh task không nhất quán sau khi xong core |
| 2026-09-29 | R7 C tối thiểu: dời T058/T063/T064/T066/T067/T068 ra sau self-host, thu gọn T061, thêm T003a (hợp đồng mở rộng core + tập self-host chính xác), QA kiểm phạm vi C | spec/ROADMAP.md, board, axiom-c-stage0, axiom-qa | Core nhanh, tổng quát, tránh viết C rồi viết lại |
| 2026-09-29 | Yêu cầu chủ dự án: khai báo biến/mảng/struct/hàm tại địa chỉ cố định (`@at`) — ADR-0001, epic E13.6, `spec/requirements/OWNER.md`; T001/T003a/T010/T110 cập nhật | spec, board, axiom-syntax | Specs chỉ có MMIO qua con trỏ/`map_mmio`, chưa có khai báo tại địa chỉ |
| 2026-09-29 | Yêu cầu chủ dự án: ràng buộc hàm/dữ liệu theo base module + offset (phân giải lúc nạp) và xuất PE DLL — REQ-OWNER-005, ADR-0001 §5-6, epic E13.7 | spec, axiom-syntax | Gọi hàm của tiến trình host từ DLL (ASLR) |
| 2026-09-29 | Bổ sung xuất file đa nền tảng/đa chip và thư viện: E16.10 (ma trận exe/lib tĩnh/lib động), E16.11 universal binary, E16.12 Windows ARM64, E12.5 multiversioning CPU, E20.7 plugin/hot-reload/ABI Axiom | spec/ROADMAP.md | Specs có (0453, 0563, 0584…) nhưng roadmap chưa gom đủ |
| 2026-09-29 | Windows x64 xuất/dùng đủ artifact: .obj/.exe ở core; .lib, .dll + import lib ngay sau self-host (E18.7: T750, T751); T003a chừa sẵn loại artifact; REQ-OWNER-006; E13.7 chỉ còn binding theo module | board, spec | Yêu cầu chủ dự án |
| 2026-09-29 | Rà soát harness: sửa thứ tự tầng (objmodel là tầng thấp), commit kèm test do QA thêm, T024/T026 phụ thuộc T003a, .gitattributes (LF, binary), đánh số ADR tiếp theo | axiom-c-stage0, taskctl.py, board, architect | Lỗi phát hiện khi rà soát |
