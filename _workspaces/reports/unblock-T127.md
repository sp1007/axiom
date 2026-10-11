# Unblock T127

## Tóm tắt
Chuỗi kiểm thử MIR trong `cdriver_mir_drop.c` đã bị lỗi cú pháp (`fn main` thay vì `mir_body`), dẫn đến ICE và làm cho task T127 bị QA block. Lỗi này đã được khắc phục bằng cách sửa đổi chuỗi trực tiếp trong bài kiểm thử cho đúng với định dạng mà `parse.c` yêu cầu, cùng với các từ khóa cần thiết như `type#` và `bbX: {`. Bài kiểm thử đã chạy qua thành công (HARNESS OK) và task T127 đã được unblock.

## Files changed
- tests/ui/drop/cdriver_mir_drop.c
- spec/decisions/ADR-0028-t127-fix-test-syntax.md
