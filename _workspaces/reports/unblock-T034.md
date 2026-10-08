## Tóm tắt
Tác vụ T034 bị chặn vì thiếu quyền chỉnh sửa `bootstrap/axiom0/src/resolve` để thêm `isize` vào các kiểu dữ liệu cơ bản (prelude types). Vì việc thêm `isize` là một phần trực tiếp của việc triển khai các kiểu số nguyên, việc bổ sung đường dẫn này vào cấu hình của T034 là giải pháp tốt nhất. Đã cập nhật mảng `paths` và bỏ chặn T034 để nó có thể tiếp tục hoàn thành.

## Quyết định và Phương án (Decision and Rationale)
**Vấn đề (Issue):** T034 needs to add `isize` to the prelude types in `resolve.c` but lacked the required path `bootstrap/axiom0/src/resolve`.
**Các phương án (Options considered):**
1. *Create a new prerequisite task*: Too much overhead for adding a single primitive type to the prelude.
2. *Split T034*: Unnecessary since the change is minimal and conceptually belongs to the scope of implementing numeric types.
3. *Add the path to T034*: Allows the task to accomplish its goal directly without complicated task board management.
**Quyết định (Decision):** Option 3. Added `bootstrap/axiom0/src/resolve` to T034's `paths` and unblocked the task using `taskctl.py`.

## Files changed
- _workspaces/tasks/todo/T034-numeric-types-casts-checked-arithmetic-panic-abort.md
