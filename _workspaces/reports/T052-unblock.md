# T052 Unblock Analysis

## Tóm tắt
T052 (P6 gate) bị chặn do các script kiểm tra (`gatecheck.py`, `reqcov.py`, `harness_check.py`) báo lỗi ở những file nằm ngoài phạm vi `paths` ban đầu của task. Lỗi chủ yếu do metadata bị cũ: các task T046, T049 đã được thay thế (superseded) nhưng vẫn còn tham chiếu trong `spec/invariants.md` và `spec/requirements/CATALOG.md`; các tag `xfail` của T130 và T126 vẫn còn trong test dù task đã xong; và T052a thiếu trường `gate_model`.
Thay vì tạo một task mới, phạm vi `paths` của T052 đã được mở rộng để có thể tự dọn dẹp các metadata này, vì một gate task cần có khả năng dọn dẹp board hygiene để hoàn thành các script kiểm tra. Kế hoạch triển khai của T052 cũng đã được cập nhật chi tiết các bước sửa lỗi metadata.

## Decision
- **Option 1**: Create a prerequisite board hygiene task (`T134`) and have T052 depend on it.
- **Option 2**: Expand T052's `paths` to include `tests`, `spec`, and `_workspaces/tasks/done` so it can fix the metadata itself, as a gate task is expected to ensure system-wide cleanliness.
- **Decision**: Option 2. T052 is a gate task and its acceptance criteria explicitly require `gatecheck.py`, `reqcov.py`, and `harness_check.py` to pass. Restricting its paths to only the new adversarial tests prevented it from achieving its acceptance criteria. We have expanded its `paths` and updated its `Implementation Plan` with the exact metadata updates needed.

## Files changed
- _workspaces/tasks/doing/T052-p6-gate-adversarial-semantic-suite.md

STATUS: UNBLOCKED
