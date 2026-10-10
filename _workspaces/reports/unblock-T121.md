# Unblock T121

## Tóm tắt
Thêm `bootstrap/axiom0/src/driver/pipeline.c` vào danh sách `paths` của task T121 và tạo ADR-0020 để ghi nhận quyết định này. Đã unblock T121 và cập nhật ROADMAP.md.

## Quyết định
- **Vấn đề**: T121 cần sửa đổi `bootstrap/axiom0/src/driver/pipeline.c` nhưng file này không nằm trong `paths`.
- **Giải pháp**: Cập nhật trực tiếp `paths` của T121 thay vì chia nhỏ (split) task, vì việc đăng ký pipeline chỉ là một thay đổi nhỏ đi kèm với dataflow analysis.

## Files changed
- spec/decisions/ADR-0020-rescope-t121-paths.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T121-move-dataflow-analysis.md
