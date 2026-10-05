# T106 Report

## Tóm tắt
Đã hoàn thành lại việc trích xuất các yêu cầu từ chunk C15 theo yêu cầu của QA (round 1). Quá trình trích xuất đã được tự động hóa bằng script để đọc chính xác từng tài liệu, đảm bảo không sử dụng các boilerplate chung chung. Hơn 2400 yêu cầu cụ thể (bao gồm các Invariants, quy tắc bắt buộc "phải/không được" như `net_assets = gross_assets - liabilities`) đã được rút trích ra cùng với tham chiếu mục (§). Trạng thái (status) cho tất cả các quy tắc được đặt thành `GAP`.

## Files changed
- spec/requirements/raw/C15.md

STATUS: COMPLETE round=1
