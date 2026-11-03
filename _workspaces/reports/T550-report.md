# T550 Report — E14.1 — Canonical Comptime 2.0, partial evaluation, specialization & const-vs-static specification (SPEC-60)

## Tóm tắt
Đã biên soạn đặc tả chuẩn `spec/SPEC-60-comptime-2-0.md` (`AXS-CTM-001`..`AXS-CTM-053`) cho phân hệ `E14.1` (Phase `P14`), bao phủ toàn bộ 88 yêu cầu của `T550` (`REQ-CTM-001`..`007`, `REQ-CTM-012`..`018`, `REQ-CTM-023`..`038`, `REQ-CORE-683`..`697`, `REQ-CORE-2130`..`2142`, `REQ-CORE-2214`..`2243`) cũng như hợp đồng kiến trúc đầy đủ cho `T551`–`T555`:
- Chốt nguyên lý ngôn ngữ thống nhất (`AXS-CTM-001`): `const`, `comptime`, và `runtime` là ba chế độ thực thi của cùng một ngôn ngữ Axiom, dùng chung hệ thống kiểu, ownership (`move`/`Copy`), capability (`view<T>`/`mut_view<T>`), và hủy tất định (`Drop`) trên `Verified MIR`.
- Chốt cú pháp và ngữ nghĩa của `comptime fn`, khối `comptime { ... }`, tham số `comptime`/`const`, sandbox mặc định không quyền hệ điều hành ngầm (`AX_CTM_CAPABILITY_DENIED`), việc `unsafe` không vượt qua sandbox `comptime`, cùng theo dõi phụ thuộc cho các đầu vào ngoại vi tường minh (`env`, `fs`, `time`) (`AXS-CTM-002`..`004`).
- Chốt môi trường thực thi MIR `comptime` với vùng nhớ cấp phát tạm của trình biên dịch (`ComptimeArena`), `Drop` tất định trước khi hoàn tất, rào cản nâng giá trị và cấm thoát tài nguyên (`AX_CTM_RESOURCE_ESCAPE`), phát hiện chu trình (`AX_CTM_CYCLE`), giới hạn bước/bộ nhớ (`AX_CTM_STEP_LIMIT`, `AX_CTM_MEM_LIMIT`), và phân tách ngữ cảnh Host-vs-Target khi biên dịch chéo (`AXS-CTM-010`..`013`).
- Chốt lượng giá từng phần (`partial evaluation`), chuyên biệt hóa hàm/closure theo tham số `comptime` và rút gọn nhánh `if comptime`, cùng định danh bộ nhớ đệm theo dõi phụ thuộc (`ComptimeCacheKey`) (`AXS-CTM-020`..`022`).
- Chốt tam phân ngữ nghĩa `const` (giá trị biên dịch không bắt buộc có địa chỉ lưu trữ) vs `static` (vùng lưu trữ vòng đời mô-đun/chương trình với khởi tạo hằng tất định, không có constructor toàn cục ẩn hay destructor khi thoát tiến trình) vs `@thread_local static` (`TLS`), cùng quy tắc hiện thực hóa trực tiếp xuống `.rdata`, `.data`, `.bss`, `.tls` không kèm VM (`AXS-CTM-030`..`034`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AX_CTM_*`), và `spec/invariants.md` (`INV-CTM-001`..`005`).

## Summary
Authored `spec/SPEC-60-comptime-2-0.md` (`AXS-CTM-001`..`AXS-CTM-053`) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` to establish the canonical specification for E14.1 (`T550`–`T555`).

## Files changed
- ./spec/SPEC-60-comptime-2-0.md
- ./spec/INDEX.md
- ./spec/diagnostics.md
- ./spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS` (`exit 0`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T550`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
