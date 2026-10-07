## Tóm tắt
Đã thêm `bootstrap/axiom0/src/target/x64/mir/frame.c` và `bootstrap/axiom0/src/target/x64/isel/isel.c` vào mảng `locks:` trong tệp tác vụ của T028 và gỡ block (unblock) cho task. Điều này cho phép agent có quyền sửa các lỗi memory corruption và con trỏ SIB bị thiếu sót từ T025, để T028 có thể hoàn thành việc biên dịch end-to-end. Lựa chọn này là đơn giản nhất và giữ nguyên tính liên kết của việc fix bugs cho T028.

## Rationale
- **Options considered**:
  1. Add missing paths to `locks:` in T028 to grant editing access.
  2. Split the task into a bug-fix task first and then T028.
- **Decision**: Option 1 was selected. It is much simpler and faster to allow the current task to correct these bugs since the problem directly blocks the current end-to-end build effort.

## Files changed
- _workspaces/tasks/todo/T028-axiom0-build-end-to-end-first-native-axiom-program.md
