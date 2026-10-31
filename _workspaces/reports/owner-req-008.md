# Architecture Report — Record Owner Requirement REQ-OWNER-008 (Taking Addresses of Functions and Variables for `@at`)

## Tóm tắt
- Ghi nhận yêu cầu mới của chủ dự án **`REQ-OWNER-008`** vào `spec/requirements/OWNER.md` và `spec/requirements/CATALOG.md` (gắn vào `EPIC(E13.6)` trong Phase `P13`).
- Cập nhật `spec/decisions/ADR-0001-fixed-address-declarations.md` (§7) và `spec/ROADMAP.md` (`E13.6` + nhật ký thay đổi): trong mã cấp thấp/`unsafe`, lập trình viên có thể lấy địa chỉ bộ nhớ của bất kỳ hàm (`fn`, `extern fn`, hàm `@at`) hoặc biến/đối tượng tĩnh (`static`, `static mut`, mục `@at`, biến cục bộ, trường/phần tử) dưới dạng con trỏ thô hoặc địa chỉ `usize` thông qua `address_of` / `address_of_mut` / `addr_of` và ép kiểu `as usize`, phục vụ trực tiếp việc kiểm tra, truyền và liên kết với các khai báo `@at(...)`.

## Files changed
- spec/requirements/OWNER.md
- spec/requirements/CATALOG.md
- spec/decisions/ADR-0001-fixed-address-declarations.md
- spec/ROADMAP.md
