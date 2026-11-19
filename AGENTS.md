Xem CLAUDE.md

## Quy tắc chọn model khi chạy trong Antigravity

1. **Carbon (`Gemini 4 Carbon (High)` / `gemini-4-carbon-high`):** Dùng để chốt đặc tả ngữ pháp (Grammar/EBNF), thiết kế cấu trúc cây cú pháp (AST), hệ thống kiểu (Type System) và bộ sinh mã (Code Generator / LLVM IR / native backend), cũng như thiết kế kiến trúc tổng thể.
2. **Neon (`Gemini 4 Neon (Medium)` / `gemini-4-neon-medium`):** Chuyển sang để triển khai chi tiết từng module nhỏ, viết các ca kiểm thử biên (edge cases / QA adversarial tests) và tối ưu tốc độ phản hồi khi debug từng lỗi nhỏ.

### Cách áp dụng trong công cụ Antigravity
- Khi khởi tạo hoặc đổi model cho worker qua `swarm` (`action: "add"` hoặc `action: "model"`), truyền trực tiếp mã model:
  - Đặc tả ngữ pháp / AST / Type System / Code Generator: `model: "gemini-4-carbon-high"`
  - Triển khai chi tiết module nhỏ / Kiểm thử biên (edge cases) / Debug lỗi nhỏ: `model: "gemini-4-neon-medium"`
- Khi gọi `invoke_subagent` (`Model: "inherit"`), subagent kế thừa model đang chọn của phiên điều phối tại thời điểm khởi tạo; nếu cần ghim riêng `gemini-4-carbon-high` hoặc `gemini-4-neon-medium` cho từng vai trò độc lập thì dùng `swarm` hoặc chuyển model bằng `swarm(action="model", ...)`.

## Quy tắc đặt tên subagent / swarm worker theo Task đang chạy

1. **Tên worker / subagent bắt buộc mang mã Task và giai đoạn (`impl` / `qa` / `fix`):**
   - Với `swarm(action="add")`: đặt `name` đúng theo mã task viết thường kèm giai đoạn, ví dụ `t436-impl`, `t436-qa`, `t441-impl`, `t441-qa` (không đặt tên chung chung như `impl-neon` hay `qa-gate`). Khi task/giai đoạn đó kết thúc, dọn worker cũ (`action: "kill"`) để danh sách luôn chỉ hiển thị đúng các task đang chạy.
   - Với `swarm(action="title")`: cập nhật tiêu đề swarm mỗi khi chuyển task/giai đoạn theo mẫu `<TaskID> (<stage>) — <mô tả ngắn>` (ví dụ: `T436 (impl) — Selfhost driver & stage-1 parity`).
   - Với `invoke_subagent`: đặt `Role` bắt đầu bằng mã task, ví dụ `T436-impl: Selfhost driver & stage-1 parity` hoặc `T436-qa: QA Gate T436`.
