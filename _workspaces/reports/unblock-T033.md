## Tóm tắt
Tác vụ T033 bị chặn do thiếu đường dẫn `bootstrap/axiom0/src/driver` trong mảng `paths`, dẫn đến không thể sửa các lỗi về native linker (duplicate symbol, PE emission). Tôi đã thêm trực tiếp đường dẫn này vào cấu hình `paths` của tác vụ và gỡ phong tỏa (unblock) để kỹ sư có thể tiếp tục. Các bước kiểm tra hợp lệ đều đã hoàn tất thành công.

## Files changed
- _workspaces/tasks/todo/T033-native-catch-up-cfg-calls-windows-abi-completeness.md
