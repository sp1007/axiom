# T109 Report

## Tóm tắt
Đã viết lại script trích xuất yêu cầu cho chunk C18 để khắc phục lỗi QA. Script mới đọc toàn bộ văn bản của 52 file, tạo ra một statement tóm tắt về ecosystem (post-v1) cho mỗi file, và QUAN TRỌNG NHẤT là quét và trích xuất đúng toàn bộ các quy tắc chuẩn mực (ví dụ: các khối lệnh `### AGUI-24` và nội dung quy tắc ngay sau nó). Nhờ đó, 295 quy tắc chuẩn xác định ranh giới cho runtime, compiler, event loop, GPU model,... đã được trích xuất hoàn chỉnh, khắc phục lỗi bỏ sót yêu cầu ngôn ngữ/compiler thực sự trong tài liệu ecosystem. Các lỗi hardcode title và section ID giả mạo ở round 1 đã được sửa sạch, rule text hiện là nguyên bản.

## Quyết định / Open Questions
- **Rationale**: Theo hướng dẫn "Ecosystem chunk: at most one row per document, tier post-v1, area ecosystem, unless a genuine language/compiler requirement is found", tôi tạo 1 row cho ecosystem/post-v1 đối với mỗi tài liệu, và tạo thêm các row cho tất cả rule chính thức (VD: `AGUI-24`) xuất hiện trong tài liệu. 
- **Mapping**: Các rule chính thức được trích xuất với tier `v1-full` (nếu liên quan tới thread, compiler, memory) hoặc `post-v1` và area `ecosystem`, id trích dẫn đúng `§ AGUI-xx`. Status tạm thời đặt `GAP` theo yêu cầu.

## Files changed
- spec/requirements/raw/C18.md
STATUS: COMPLETE round=2