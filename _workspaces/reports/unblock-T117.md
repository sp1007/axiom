# Unblock T117

## Tóm tắt
Task T117 bị chặn (blocked) do lỗi phân giải giá trị boolean literal (`true`/`false` bị dịch nhầm thành `0`). Lỗi này nằm ở `builder.c` và `parse.c`, nhưng các file này chưa được cấp quyền `locks:` cho T117. Giải pháp đơn giản nhất được chọn là thêm `bootstrap/axiom0/src/mir/parse.c` và `bootstrap/axiom0/src/mir/build/builder.c` vào mảng `locks:` của T117 để cấp quyền cho implementation agent tự sửa lỗi này trong cùng một task, tránh việc tách thêm task phụ gây phức tạp không cần thiết.

## Files changed
- _workspaces/tasks/todo/T117-vs0-fix-interp-width-bitwise-panic.md
