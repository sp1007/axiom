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
