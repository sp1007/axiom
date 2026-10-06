## Tóm tắt
Thêm `bootstrap/axiom0/src/driver/driver.h` và `bootstrap/axiom0/src/driver/cmd_check.c` vào danh sách `paths` của T017 để giải quyết blocker.

## Decision
- Option A: Add the files to `paths` to allow the engineer to modify them.
- Rationale: The engineer needs these files to implement the typeck driver interface correctly. Adding them to `paths` is straightforward and unblocks the task.

## Files changed
- _workspaces/tasks/todo/T017-type-interner-typeck-for-the-bootstrap-subset-type.md
- _workspaces/reports/T017-unblock.md
