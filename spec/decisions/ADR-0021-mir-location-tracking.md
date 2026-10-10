# ADR-0021 — mir-location-tracking

## Tóm tắt
Thêm theo dõi vị trí (AxLocation) cho các câu lệnh và toán hạng trong MIR để hỗ trợ xuất lỗi chính xác với vị trí và nhãn. Quyết định tách thành một task riêng biệt (T122) thay vì gộp chung vào T121.

## Context
Task T121 (Move dataflow analysis) bị block do MIR hiện tại không có khả năng theo dõi vị trí (AxLocation) cho statements/operands. Điều này khiến cho việc xuất diagnostics với location và label (ví dụ như nhãn 'moved here') trở nên bất khả thi theo như yêu cầu của bài test. Việc thêm theo dõi vị trí là một thay đổi mang tính nền tảng đối với MIR.

## Decision
Chúng tôi quyết định tạo task T122: Add AxLocation tracking to MIR như một prerequisite (điều kiện tiên quyết) cho T121. T121 sẽ phụ thuộc vào T122.

## Consequences
- T121 sẽ được unblock (đưa về trạng thái todo) và sẽ chờ T122 hoàn thành.
- Cấu trúc dữ liệu của MIR sẽ lớn hơn đôi chút do phải lưu trữ thêm thông tin location.
- Bất kỳ diagnostic nào phát sinh từ MIR đều có thể trỏ chính xác về source.
