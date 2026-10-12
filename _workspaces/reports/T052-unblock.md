# T052 Unblock Report

## Tóm tắt
Đã giải quyết các blocker cho cổng P6 (T052) bằng cách chia nhỏ các lỗi thành các task mới để sửa chữa triệt để thay vì hạ thấp tiêu chuẩn:
- Tạo T126b để sửa lỗi implement của slice (crashes và open ranges).
- Tạo T052c để sửa lỗi compiler với `drop()` (use-after-move không bị phát hiện).
- Tạo T052d để khắc phục lỗi thiếu thư mục `tests/run/native_abi` trong `gatecheck.py`.
- Tạo T052e để sửa kịch bản kiểm tra `test_archcheck.py`.
- Viết ADR-0007 để thống nhất và khẳng định thứ tự tầng kiến trúc chuẩn xác là `mir < own`.

## Analysis
T052 is a gate task and must not have relaxed acceptance criteria. Therefore, implementation bugs found during the gate execution must be fixed in appropriate fix tasks before the gate can pass.

- **Slice Bugs**: T126 slice implementation was incomplete. Split to `T126b`.
- **Drop Bug**: Explicit `drop(b)` allows use-after-move without triggering `AX_MOVE_USE_AFTER_MOVE`. Split to `T052c`.
- **Native ABI Directory**: The `gatecheck.py` script fails on missing `tests/run/native_abi`. Split to `T052d`.
- **Archcheck Layer Order**: QA observed that `test_archcheck.py` incorrectly hardcodes `own < mir` while the codebase legitimately uses `mir < own`. Codified this architectural decision in `docs/adr/ADR-0007-layer-order.md` and created `T052e` to fix the test script.

## Files changed
- docs/adr/ADR-0007-layer-order.md
- _workspaces/tasks/todo/T052-p6-gate-adversarial-semantic-suite.md
- _workspaces/tasks/todo/T126b-fix-slice-crashes.md
- _workspaces/tasks/todo/T052c-fix-drop-uam.md
- _workspaces/tasks/todo/T052d-fix-native-abi-missing.md
- _workspaces/tasks/todo/T052e-fix-archcheck-test.md

STATUS: UNBLOCKED
