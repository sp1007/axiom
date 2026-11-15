Xem CLAUDE.md

## Quy tắc chọn model khi chạy trong Antigravity

1. **Carbon (`Gemini 4 Carbon (High)` / `gemini-4-carbon-high`):** Dùng để chốt đặc tả ngữ pháp (Grammar/EBNF), thiết kế cấu trúc cây cú pháp (AST), hệ thống kiểu (Type System) và bộ sinh mã (Code Generator / LLVM IR / native backend), cũng như thiết kế kiến trúc tổng thể.
2. **Argon (`Gemini 4 Argon (Medium)` / `gemini-4-argon-medium`):** Chuyển sang để triển khai chi tiết từng module nhỏ, viết các ca kiểm thử biên (edge cases / QA adversarial tests) và tối ưu tốc độ phản hồi khi debug từng lỗi nhỏ.

### Cách áp dụng trong công cụ Antigravity
- Khi khởi tạo hoặc đổi model cho worker qua `swarm` (`action: "add"` hoặc `action: "model"`), truyền trực tiếp mã model:
  - Đặc tả ngữ pháp / AST / Type System / Code Generator: `model: "gemini-4-carbon-high"`
  - Triển khai chi tiết module nhỏ / Kiểm thử biên (edge cases) / Debug lỗi nhỏ: `model: "gemini-4-argon-medium"`
- Khi gọi `invoke_subagent` (`Model: "inherit"`), subagent kế thừa model đang chọn của phiên điều phối tại thời điểm khởi tạo; nếu cần ghim riêng `gemini-4-carbon-high` hoặc `gemini-4-argon-medium` cho từng vai trò độc lập thì dùng `swarm` hoặc chuyển model bằng `swarm(action="model", ...)`.
