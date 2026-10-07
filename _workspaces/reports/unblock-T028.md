## Tóm tắt
Tác vụ T028 bị block do `typeck.c` gặp lỗi crash (lỗi `TypeInterner: invalid id 0`) khi hàm `main` trong `build_ok.test` không có kiểu trả về. Agent cần quyền lock file này để sửa lỗi. Tôi đã thêm `bootstrap/axiom0/src/typeck/typeck.c` vào danh sách `locks` của T028 và unblock tác vụ. Đây là cách giải quyết đơn giản nhất để agent có thể tiếp tục thực hiện và sửa lỗi type checking fallback.

## Options and Rationale
- **Option A:** Add `bootstrap/axiom0/src/typeck/typeck.c` to T028's `locks` array. This is the simplest and most direct way to unblock the agent, allowing it to quickly fix the missing return type fallback in `typeck.c` for `build_ok.test`.
- **Option B:** Split the task to fix the type checking bug separately. This adds unnecessary overhead for a minor fallback bug that blocks the current progress.

Decision: Option A. The lock was added to T028 and the task was unblocked via `taskctl.py unblock T028`.

## Files changed
- _workspaces/tasks/todo/T028-axiom0-build-end-to-end-first-native-axiom-program.md
