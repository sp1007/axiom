# T808 Report — E19.3 Canonical Semantic Refactoring Engine & AST-Aware AXDIFF/AXMERGE/AXPATCH/AXHISTORY/AXVCS Specification (SPEC-102)

## Tóm tắt

Hoàn thành đặc tả chuẩn tắc `spec/SPEC-102-refactoring-engine-semantic-vcs.md` cho E19.3 (`T808`), định nghĩa:
1. **Bộ máy tái cấu trúc ngữ nghĩa dùng chung `CompilerDB` (`AXS-REF-001`..`AXS-REF-021`)**: Hợp nhất cơ sở hạ tầng phân tích chương trình cho IDE/CLI (`REQ-TOOL-183`), cổng kiểm chứng ngữ nghĩa hậu biến đổi bắt buộc áp dụng cho cả thao tác của lập trình viên lẫn đề xuất từ AI (`REQ-TOOL-186`), các phép biến đổi chuẩn tắc (`extract_function`, `extract_variable`/`introduce_variable`, `inline_variable`, `populate_match_arms`/`add_missing_match_arms`, `organize_imports`, `change_signature`, `move_item`, `convert_capability_view`) với chứng minh bảo toàn ownership/capability (`view<T>`, `mut_view<T>`, `ByCopy`, `ByMove`) và hiệu ứng lỗi (`! ErrorType`), cùng giao thức LSP `textDocument/codeAction` và `codeAction/resolve` (`SPEC-100` `AXS-LSP-052`).
2. **Hệ thống kiểm soát phiên bản & bản vá nhận thức AST/CST (`AXS-REF-030`..`AXS-REF-063`)**:
   - `AXDIFF` (`REQ-TOOL-301`, `DIFF-INV-01..40`): So khớp CST/AST và đồ thị ký hiệu `CompilerDB` với phân loại 9 trạng thái `DiffStatus` (`Unchanged`, `Added`, `Removed`, `Modified`, `Moved`, `Renamed`, `Refactored`, `Reordered`, `FormattingOnly`), mức bằng chứng `DiffEvidenceLevel` và kiểm tra tương thích API/ABI.
   - `AXMERGE` (`REQ-TOOL-302`, `MERGE-INV-01..40`): Hợp nhất ngữ nghĩa 3 nhánh (`BASE`, `LEFT`, `RIGHT`) theo 6 cấp định danh thực thể, tự động hợp nhất các thay đổi giao hoán và cô lập xung đột cấu trúc/ngữ nghĩa (`MergeConflictKind`, `ConflictId` tất định) kèm cổng kiểm chứng `CompilerDB` hậu hợp nhất.
   - `AXPATCH` (`REQ-TOOL-303`, `PATCH-INV-01..40`): Định dạng bản vá AST/ngữ nghĩa định danh theo nội dung (`PatchId`), định vị mục tiêu 6 cấp độ, kiểm tra tiền điều kiện/hậu điều kiện, giao dịch nguyên tử copy-on-write (`PatchTransaction`), cùng các phép toán `reverse`, `compose` và `rebase_patch`.
   - `AXHISTORY` (`REQ-TOOL-304`, `HISTORY-INV-01..40`): Đồ thị lịch sử DAG (`RevisionId`) và truy vết phả hệ ký hiệu (`SymbolHistoryEvent`: `Created`, `Modified`, `Renamed`, `Moved`, `ExtractedFrom`, `InlinedInto`, `SplitInto`, `MergedFrom`, `Removed`).
   - `AXVCS` (`REQ-TOOL-305`, `VCS-INV-01..40`): Kho lưu trữ đối tượng định danh nội dung (`ObjectId`: `Blob`, `Tree`, `Semantic`, `Patch`, `Revision`), giao dịch cập nhật nhánh nguyên tử, mô-đun thư viện chuẩn `std.vcs`, và các lệnh CLI `axiomc refactor`, `axiomc diff`, `axiomc merge`, `axiomc patch`.
3. Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-021`) và `spec/invariants.md` (nhóm `REF`, mục §48 với `INV-REF-001` cho `T809`, `INV-REF-002` cho `T810`, và `INV-REF-003` cho `T811`).

## Files changed

- `spec/SPEC-102-refactoring-engine-semantic-vcs.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T808` → verified

STATUS: COMPLETE round=0
