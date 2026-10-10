# Unblock Report

## Tóm tắt
Đã giải cứu (unpark) task T121. Rescope paths của T121, bao gồm `archcheck_rules.txt`, `tests/run/pattern/enum_struct_if_let.ax` và file ADR mới. Tạo file ADR `spec/decisions/ADR-0022-allow-own-depend-on-mir.md` để cho phép `own` phụ thuộc vào `mir`. Cuối cùng, gọi lệnh validate board thành công.

## Files changed
* _workspaces/tasks/todo/T121-move-dataflow-analysis.md
* spec/decisions/ADR-0022-allow-own-depend-on-mir.md
