# Architect unblock report for T047

## Tóm tắt
T047 bị chặn do thiếu quyền truy xuất vào các file `own.c`, `typeck.c` và `verify.c` để thực hiện tích hợp phân tích khởi tạo và gỡ bỏ các đoạn kiểm tra cũ. Tôi đã quyết định thêm các file này vào danh sách `locks` của T047 thay vì chia nhỏ task, giúp cho toàn bộ chu trình (logic phân tích + tích hợp) được thực hiện trong một task duy nhất. Quyết định được lưu trong ADR-0023.

## Decision and Rationale
Task T047 was blocked due to missing paths to `own.c`, `typeck.c`, and `verify.c` required to wire up the analysis and remove legacy checks. I chose to rescope the task by adding the required files to the `locks:` array (Option 2), which enables the task to fully integrate its analysis and prove it works via the existing test suite, satisfying R1 (Spec goes wide, implementation goes vertical). The alternative of splitting the integration into a new task (Option 1) was rejected because it would leave the analysis un-exercised in the initial task.

The decision has been recorded in `spec/decisions/ADR-0023-t047-locks.md` and appended to the change log in `spec/ROADMAP.md`. T047 has been unblocked via `taskctl.py unblock T047`.

## Files changed
- _workspaces/tasks/todo/T047-initialization-analysis-definite-init-reinit-after.md
- spec/decisions/ADR-0023-t047-locks.md
- spec/ROADMAP.md
