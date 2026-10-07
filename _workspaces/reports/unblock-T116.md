# Unblock T116 Report

## Tóm tắt
Nhiệm vụ T116 đã bị chặn do liên tục thất bại QA ở phần xử lý `parse.c` và kiểm tra tràn số nguyên 32-bit trong `interp.c`. Quyết định giải quyết (như đã ghi nhận trong `ADR-0018-split-t116-checked-arithmetic.md`) là chia nhỏ nhiệm vụ này để giảm thiểu rủi ro:
- Cập nhật lại phạm vi của `T116` để chỉ tập trung vào builder `~`, exhaustive ICE (M1, M3), và thêm cấu trúc/terminator `Assert` vào verifier và print. Các phần text parser và interpreter semantics chi tiết sẽ được đưa ra ngoài phạm vi nhiệm vụ này.
- Tạo nhiệm vụ mới `T119` (phụ thuộc vào `T116`) kế thừa các công việc còn lại: hỗ trợ text parser cho `~` và `overflows(...)` trong `parse.c`, cũng như việc sử dụng chính xác `__builtin_*_overflow` trong `interp.c` để xử lý tràn số.
Nhiệm vụ T116 giờ đây đã được chia nhỏ và rõ ràng hơn, giúp dễ dàng vượt qua QA. T116 sẽ được unblock.

## Files changed
- spec/decisions/ADR-0018-split-t116-checked-arithmetic.md
- _workspaces/tasks/todo/T116-vs0-fix-mir-builder-bitnot-asserts.md
- _workspaces/tasks/todo/T119-vs0-fix-mir-parser-interp-asserts.md
