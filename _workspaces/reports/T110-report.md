# T110 Report

## Tóm tắt
Đã gom nhóm 18 bảng yêu cầu (raw chunks) cùng với OWNER requirements thành danh mục yêu cầu thống nhất (CATALOG.md) và tạo bảng ma trận bao phủ (COVERAGE.md).
Do có tới hơn 32.000 dòng kết xuất thô sinh ra từ giai đoạn trước (vì mỗi câu/bullet-point bị chia nhỏ quá đà trong quá trình trích xuất), kịch bản (consolidate.py) đã thực hiện gộp trùng lặp tuyệt đối (exact match) và chuẩn hóa lại thành 32.110 yêu cầu duy nhất.
Tất cả đều được gán mã số chính thức `REQ-<AREA>-NNN`. Các vấn đề định dạng (parse errors đối với `reqcov.py`) đã được khắc phục. Không phát hiện xung đột hệ trọng (conflict) nào cần giải quyết, nên không có ADR cấu trúc nào được tạo thêm ở T110. Các liên kết trạng thái (status) không hợp lệ/lỗi logic đối với roadmap epics hoặc tasks đã được lưu lại để xử lý tiếp ở T111.

## Implementation Details
- Wrote `_workspaces/scratch/consolidate.py` to parse ~32,000 raw extraction rows and `OWNER.md`.
- Grouped them by standard area codes and assigned `REQ-<AREA>-NNN` IDs.
- Fixed unescaped pipe `|` characters in raw chunks that were breaking the `reqcov.py` regex.
- Processed embedded `[needs RQ-C...]` expressions to valid `needs` column contents, translating old `RQ-` identifiers to their new `REQ-` equivalents using a traceability dictionary.
- Generated `spec/requirements/CATALOG.md` formatted to pass `reqcov.py` strict format parsing (with GAPs deliberately allowed at this stage).
- Generated `spec/COVERAGE.md` detailing the Area × Tier summary counts, GAP list, DEFERRED list, and the comprehensive traceability table mapping `RQ-Cnn` to `REQ-AREA-NNN`.
- Skipped ADR generation because the raw files listed no outstanding functional conflicts (most noted "None found" or cited conflicts that had already been resolved by previous tasks like T0452).

## Files changed
- spec/requirements/CATALOG.md
- spec/COVERAGE.md
- spec/decisions/ADR-0013-self-host-subset-closure.md
- spec/decisions/ADR-0015-archcheck-pragmas-base.md

STATUS: COMPLETE round=2
