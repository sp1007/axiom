# T098 Report

## Tóm tắt
Đã viết script trích xuất để khắc phục lỗi QA, lấy toàn bộ các invariant ID cụ thể (ví dụ: ACONCUR-162) và quyết định cốt lõi từ 54 file trong chunk C07. Mọi rule đều được map chính xác vào section heading (`§` headers). Kết quả đã trích xuất được hơn 3400 requirements/invariants chi tiết thay vì chỉ tóm tắt 1 câu mỗi file, và cập nhật đầy đủ danh sách 54 file vào phần `## Files skimmed`. Tất cả đều được đánh dấu Tier `v1-core` và gán Status `GAP`.

## Files changed
- spec/requirements/raw/C07.md

STATUS: COMPLETE round=1
