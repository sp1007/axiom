# Unblock T048 Report

## Tóm tắt
Nhiệm vụ T048 bị chặn vì thiếu cơ sở hạ tầng theo dõi capability cơ bản trong `ax_mir_cap_tracker`, `own.c`, và `syntax/typeck`. Để giải quyết, tôi đã áp dụng quyết định kiến trúc ADR-0025, tách T048 thành hai nhiệm vụ nhỏ hơn:
- T124: Cơ sở hạ tầng capability tracking và syntax cho views.
- T125: Phần còn lại của T048 (view/mut_view, regions, conflicts, escapes) phụ thuộc vào T124.
Nhiệm vụ T048 cũ đã bị thay thế (supersede) bởi T124.

## Files changed
- spec/decisions/ADR-0025-split-t048-view-tracking.md
- _workspaces/tasks/todo/T124-basic-capability-tracking.md
- _workspaces/tasks/todo/T125-views-capabilities-view-mut-view-regions-conflicts.md
- _workspaces/tasks/done/T048-views-capabilities-view-mut-view-regions-conflicts.md
