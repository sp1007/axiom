# Unblock T036

## Tóm tắt
- T036 bị chặn do `resolve.c` báo lỗi `AX_NAME_UNRESOLVED` cho hàm built-in `len()`, và pipeline dừng lại không cho `typeck` chạy.
- Kỹ sư cho rằng cần sửa `pipeline.c` để cho `typeck` tiếp tục chạy ngay cả khi có lỗi resolution, nhưng cách tiếp cận này là sai.
- Theo ADR-0006 §3, `len(a)` phải được thêm vào như một built-in function ở pha resolution (`resolve.c`), khi đó sẽ không còn lỗi `AX_NAME_UNRESOLVED`.
- Tôi đã viết lại phạm vi của task T036 (thêm `bootstrap/axiom0/src/resolve` vào `paths`) để chỉ rõ `len()` cần được khai báo trong `resolve.c`, sau đó unblock task này.

## Quyết định (Decision)
Tôi chọn phương án (d): rewrite the task's scope.
Cách tiếp cận cũ (bypass lỗi ở typeck và sửa pipeline.c) là sai. Cách tiếp cận đúng là khai báo `len()` như một built-in ở pha resolution (trong `resolve.c`) theo đúng tinh thần của ADR-0006 §3. Tôi đã thêm `bootstrap/axiom0/src/resolve` vào danh sách `paths` của T036 và làm rõ scope.

## Files changed
- _workspaces/tasks/doing/T036-fixed-arrays-indexing-bounds-checks.md
