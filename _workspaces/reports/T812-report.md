# T812 Report — E19.4 Canonical Diagnostics UX 2.0, Explain Registry, Machine-Applicable Fixes & AI-Agent Fact Protocol Specification (SPEC-103)

## Tóm tắt

Hoàn thành đặc tả chuẩn tắc `spec/SPEC-103-diagnostics-ux-ai-interface.md` cho E19.4 (`T812`), định nghĩa:
1. **Diagnostics UX 2.0 với chuỗi nhân-quả đa vị trí & triệt tiêu lỗi dây chuyền (`AXS-DIAG-001`..`AXS-DIAG-005` / `AXS-DUX-001`..`AXS-DUX-005`, `REQ-TOOL-298`)**: Mọi chẩn đoán được sinh từ `CompilerDB` kèm đồ thị nguyên nhân có hướng (`CausalProvenanceChain`: `Origin` → `Transfer`/`BorrowShared`/`BorrowMut`/`AliasOverlap`/`ContainerMutation`/`SuspensionPoint`/`ScopeExit`/`ObligationOrigin` → `Violation`), dấu vân tay tất định 128-bit (`DiagnosticFingerprint`) độc lập câu chữ hiển thị (`0146 §40`), và cơ chế lan truyền độc tố (`PoisonTaint`) triệt tiêu hoàn toàn các lỗi giả tạo dây chuyền.
2. **Sửa lỗi tự động phân cấp độ tin cậy & `axiomc fix` giao dịch (`AXS-DIAG-010`..`AXS-DIAG-014` / `AXS-DUX-010`..`AXS-DUX-014`, `REQ-TOOL-185`, `REQ-TOOL-186`)**: Phân loại 4 mức `Applicability` (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`, `Unspecified`), cấm phân loại các gợi ý đưa `unsafe` hoặc cú pháp phi chuẩn thành `MachineApplicable`, và quy định lệnh `axiomc fix` áp dụng giao dịch kèm cổng tái kiểm chứng `CompilerDB` bắt buộc.
3. **Từ điển bách khoa `axiomc explain <AX_CODE>` (`AXS-DIAG-020`..`AXS-DIAG-022` / `AXS-DUX-020`..`AXS-DUX-022`)**: Bao phủ toàn bộ 18+ vùng mã chẩn đoán với liên kết hai chiều tới quy tắc đặc tả (`AXS-*`, `AXD-*`), bất biến (`INV-*`), và ví dụ Axiom chuẩn chạy được (`=` và `.`).
4. **Giao thức sự kiện ngữ nghĩa AI (`axiomc query`), thanh tra bố cục (`axiomc inspect layout`), hợp đồng container `.axmeta` & hiệu ứng `std.meta_effects` (`AXS-AI-001`..`AXS-AI-021` / `AXS-DUX-030`..`AXS-DUX-051`, `REQ-TOOL-004`, `REQ-TOOL-180`..`182`, `REQ-TOOL-185`..`187`, `REQ-TOOL-190`)**: Xuất luồng sự kiện JSON/NDJSON có phiên bản (`AXCP v1`, `schema_version = 1`) không cần sinh mã máy (`codegen_invoked = false`), kiểm tra bố cục kiểu/ABI qua `axiomc inspect layout`, xuất `ContainerContract` và `ApiEffectSummary` vào `.axmeta` / `CompilerDB`, bắt buộc xác minh mọi bản vá AI qua compiler, và tách biệt hoàn toàn `.axmeta`/`.axdb`/debug khỏi tệp thực thi sản xuất.
5. Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-021`, `AXD-052`, `AXD-056`, `AXD-057`) và `spec/invariants.md` (mục §49 với `INV-DIAG-009` cho `T813`, `INV-DIAG-010` cho `T814`, và `INV-DIAG-011` cho `T815`).

## Files changed

- spec/SPEC-103-diagnostics-ux-ai-interface.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T812` → verified

STATUS: COMPLETE round=0
