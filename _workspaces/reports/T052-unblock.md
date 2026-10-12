## Tóm tắt
Cổng P6 (T052) bị block vì hai lỗi implementation: `archcheck_selftest` bị sai thứ tự layer (own < mir thay vì mir < own), và tính năng slice của T126 chưa hoàn thiện khiến các test bị lỗi khi gỡ bỏ `xfail: T126`. Quyết định: tạo task T052b để sửa archcheck và T126a để sửa slice, đồng thời thêm chúng vào dependency của T052 để các lỗi này được giải quyết trước khi đóng cổng.

## Analysis
The T052 QA report (Round 3) shows two issues blocking the gate:
1. `archcheck_selftest` fails because `test_archcheck.py` expects the layer order `own < mir`, which contradicts the actual C code and `tools/archcheck_rules.txt` (`mir < own`).
2. Slice features introduced in T126 are incomplete. The instruction to remove `xfail: T126` exposed bugs in `qa_slice_bounds_panic.ax`, `qa_slice_inverted_panic.ax`, `qa_slice_open_ranges.ax`, and `sub_range.ax`. 

According to the architect rules (0264 §20), a gate blocked by implementation bugs gets fix tasks for the owning areas, on which the gate then depends.

## Actions Taken
- Created `_workspaces/tasks/todo/T052b-fix-archcheck.md` to fix the `test_archcheck.py` layer order.
- Created `_workspaces/tasks/todo/T126a-fix-slice.md` to fix the incomplete slice implementations.
- Updated `_workspaces/tasks/doing/T052-p6-gate-adversarial-semantic-suite.md`:
  - Added `T052b` and `T126a` to the `depends` list.
  - Removed the flawed instruction to remove `xfail: T126` from slice tests in this task (T126a will handle it).

## Files changed
- _workspaces/tasks/todo/T052b-fix-archcheck.md
- _workspaces/tasks/todo/T126a-fix-slice.md
- _workspaces/tasks/doing/T052-p6-gate-adversarial-semantic-suite.md

STATUS: UNBLOCKED
