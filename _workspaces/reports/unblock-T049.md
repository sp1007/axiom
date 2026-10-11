## Tóm tắt
Nhiệm vụ T049 đã được chia nhỏ thành 4 nhiệm vụ con (T127, T128, T129, T130) để giảm phạm vi công việc do các lỗi logic và vi phạm cấu trúc (layer violations) khi biên dịch bằng GCC. Một ADR (ADR-0027) đã được tạo để ghi lại quyết định này. Các nhiệm vụ mới đã được thiết lập để thực hiện từng bước các chức năng drop.

## Files changed
- _workspaces/tasks/done/T049-drop-elaboration-cleanup-on-every-edge.md
- _workspaces/tasks/todo/T127-mir-infrastructure-for-drop.md
- _workspaces/tasks/todo/T128-basic-drop-elaboration.md
- _workspaces/tasks/todo/T129-advanced-control-flow-cleanup.md
- _workspaces/tasks/todo/T130-aggregates-and-conditional-moves.md
- spec/decisions/ADR-0027-drop-elaboration-split.md
