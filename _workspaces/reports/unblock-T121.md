# Unblock T121: Move dataflow analysis

## Tóm tắt
Task T121 gặp vấn đề không thể thêm chẩn đoán (diagnostics) với vị trí và nhãn (location & labels) do MIR hiện tại không theo dõi vị trí cho statements/operands. Để giải quyết, tôi đã tạo mới task T122 nhằm thêm tính năng theo dõi vị trí vào MIR (AxLocation) như một prerequisite cho T121. T121 đã được unblock (về trạng thái chờ T122 hoàn thành) và tài liệu cũng được cập nhật tương ứng.

## Files changed
* _workspaces/tasks/todo/T121-move-dataflow-analysis.md
* _workspaces/tasks/todo/T122-mir-location-tracking.md
* spec/decisions/ADR-0021-mir-location-tracking.md
* spec/ROADMAP.md
