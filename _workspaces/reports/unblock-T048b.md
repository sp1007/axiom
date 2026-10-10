# Unblock T048b

## Tóm tắt
Task T048b đã bị chặn (blocked) do tính năng sub-range (`s[a..b]`) và việc chia rẽ (disjoint split) yêu cầu phải bổ sung loại MIR projection mới và hỗ trợ suy luận logic (symbolic reasoning) cho vùng rời rạc trong trình phân tích vùng, điều này quá lớn để hoàn thành trong một step.
Vì vậy, T048b đã được thu hẹp (rescope) chỉ còn bao gồm dynamic-length views cơ bản, built-in `len`, bounded indexing và `Str`. Các tính năng liên quan đến sub-range và disjoint split đã được chuyển sang một task mới là T126 (sẽ thực hiện sau T048b). Các thay đổi đã được ghi nhận qua ADR-0026 và cập nhật vào lộ trình (ROADMAP.md).

## Files changed
- `_workspaces/tasks/todo/T048b-slices-dynamic-length-views.md`
- `_workspaces/tasks/todo/T126-slices-sub-ranges.md`
- `spec/ROADMAP.md`
- `spec/decisions/ADR-0026-rescoped-t048b.md`
