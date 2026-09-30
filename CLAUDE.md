# Axiom — ngôn ngữ và compiler mới

Tài liệu thiết kế gốc: `docs/base/specs`, `docs/base/tasks` (rất lớn, có mâu thuẫn — tra cứu qua skill
`axiom-spec-index`). `specs/`, `tasks/`, `others/` là kết luận đã phản biện (có giá trị quy chuẩn);
`discussions/` chỉ là bàn bạc, không lấy làm yêu cầu. Spec chuẩn hoá do agent kiến trúc sư viết nằm ở `spec/` và được ưu tiên hơn `docs/base`.

**Quy ước cú pháp bắt buộc:** gán/khai báo chỉ dùng `=` (không có `:=`, không có `var`); phân giải
namespace/thư viện chỉ dùng `.` (không có `::`). Chi tiết: skill `axiom-syntax`.

## Harness: Axiom compiler

**Mục tiêu:** Xây compiler Axiom từ spec → Stage-0 `axiom0` (C11, Windows x64 PE trước) → self-hosting
`axiomc`, bằng đội agent (architect, frontend, semantics, backend, stdlib, qa) với QA gate và auto-commit
sau mỗi task.

**Ngôn ngữ:** spec/code/test/báo cáo giữa agent bằng tiếng Anh; mỗi spec chuẩn, ADR, bản rà soát phase có `## Tóm tắt` tiếng Việt; autopilot báo cáo bằng tiếng Việt.

**Trigger:** Mọi yêu cầu xây/tiếp tục/sửa/kiểm thử compiler Axiom → dùng skill `axiom-compiler`.
Chạy tự động liên tục → `/tu-dong` (dừng: `/tu-dong dừng`, trạng thái: `/tu-dong trạng thái`); nhịp
giám sát 5 phút → `/axiom-tick`. Quản lý task → `axiom-tasks` (board ở `_workspaces/tasks/{todo,doing,done}`).
Câu hỏi đơn giản có thể trả lời trực tiếp.

**Lịch sử thay đổi:**
| Ngày | Thay đổi | Đối tượng | Lý do |
|------|----------|-----------|-------|
| 2026-09-29 | Khởi tạo harness: 6 agent, 9 skill, 91 task (P0–P11) | toàn bộ | Yêu cầu dựng đội agent xây compiler |
| 2026-09-29 | Thêm truy vết yêu cầu: T092–T109 rút yêu cầu theo 18 khối, T110 catalog, T111 mở rộng backlog; `reqcov.py`; thu hẹp bộ lọc ngoài phạm vi | skills/axiom-spec-index, axiom-tasks, agents/axiom-architect, board | Board chưa phủ hết mục tiêu trong specs và tasks |
| 2026-09-29 | Roadmap cố định P0–P24 (`spec/ROADMAP.md`): 14 task lập kế hoạch T211–T224 (T224 deferred), 13 gate T311–T323; axiom0 đóng băng sau T087; T088–T091 chuyển vào P11/P23; trạng thái `deferred`, `EPIC(...)` trong reqcov | spec/ROADMAP.md, board, agents, skills | Tránh tự sinh task không nhất quán sau khi xong core |
| 2026-09-29 | R7 C tối thiểu: dời T058/T063/T064/T066/T067/T068 ra sau self-host, thu gọn T061, thêm T003a (hợp đồng mở rộng core + tập self-host chính xác), QA kiểm phạm vi C | spec/ROADMAP.md, board, axiom-c-stage0, axiom-qa | Core nhanh, tổng quát, tránh viết C rồi viết lại |
| 2026-09-29 | Yêu cầu chủ dự án: khai báo biến/mảng/struct/hàm tại địa chỉ cố định (`@at`) — ADR-0001, epic E13.6, `spec/requirements/OWNER.md`; T001/T003a/T010/T110 cập nhật | spec, board, axiom-syntax | Specs chỉ có MMIO qua con trỏ/`map_mmio`, chưa có khai báo tại địa chỉ |
| 2026-09-29 | Yêu cầu chủ dự án: ràng buộc hàm/dữ liệu theo base module + offset (phân giải lúc nạp) và xuất PE DLL — REQ-OWNER-005, ADR-0001 §5-6, epic E13.7 | spec, axiom-syntax | Gọi hàm của tiến trình host từ DLL (ASLR) |
| 2026-09-29 | Bổ sung xuất file đa nền tảng/đa chip và thư viện: E16.10 (ma trận exe/lib tĩnh/lib động), E16.11 universal binary, E16.12 Windows ARM64, E12.5 multiversioning CPU, E20.7 plugin/hot-reload/ABI Axiom | spec/ROADMAP.md | Specs có (0453, 0563, 0584…) nhưng roadmap chưa gom đủ |
| 2026-09-29 | Windows x64 xuất/dùng đủ artifact: .obj/.exe ở core; .lib, .dll + import lib ngay sau self-host (E18.7: T750, T751); T003a chừa sẵn loại artifact; REQ-OWNER-006; E13.7 chỉ còn binding theo module | board, spec | Yêu cầu chủ dự án |
| 2026-09-29 | Rà soát harness: sửa thứ tự tầng (objmodel là tầng thấp), commit kèm test do QA thêm, T024/T026 phụ thuộc T003a, .gitattributes (LF, binary), đánh số ADR tiếp theo | axiom-c-stage0, taskctl.py, board, architect | Lỗi phát hiện khi rà soát |
| 2026-09-29 | Autopilot lấp chỗ trống ngay khi một task xong (tối đa 3 song song, không chồng thư mục; task critical chạy một mình); tóm tắt tiếng Việt cho spec/ADR/rà soát phase | axiom-tick, axiom-compiler, tu-dong, taskctl.py, architect | Quyết định của chủ dự án |
| 2026-09-29 | Mẫu thử in "Xin chào thế giới" thay cho "hello world" để kiểm UTF-8 (byte chính xác qua pipe, hiển thị đúng trên console Windows); tiêu chí thêm vào T010, T041, T042, T071, T074 | axiom-testing, board | Yêu cầu chủ dự án |
| 2026-09-29 | Sửa sự cố: gỡ docs/base khỏi commit chuẩn hoá LF (tài liệu của chủ dự án giữ nguyên byte, `docs/base/** -text`); sửa taskctl ghi LF | .gitattributes, taskctl.py | Lỗi của harness |
| 2026-09-29 | Rà soát lần 2: harness_check.py; commit sau gỡ chặn chỉ stage file được liệt kê; task của QA do architect duyệt; QA gate cho task chỉ viết spec; chuẩn hoá LF toàn bộ harness | axiom-compiler, axiom-qa, axiom-tasks, board | Lỗi logic phát hiện khi rà soát |
| 2026-09-30 | Phân model: Opus cho architect/semantics/gate cuối phase/gate spec quan trọng; Sonnet cho frontend/backend/stdlib/QA thường/rút yêu cầu; vòng sửa QA thứ 2 tự nâng Opus; trường `model`/`gate_model` trên mọi task | agents, axiom-compiler, axiom-tasks, board, ROADMAP | Tiết kiệm quota, giữ chất lượng chỗ quan trọng |
| 2026-09-30 | Bổ sung std cần cho self-host: T073a arena + bảng ID có kiểu (kéo từ E21.9), sort, StringBuilder/format/parse/ByteBuf, file nhị phân/path/liệt kê thư mục/đồng hồ; T003a định nghĩa tập std self-host từ sớm | board, ROADMAP | Compiler viết bằng Axiom cần các thư viện này |
| 2026-09-30 | R8: std viết bằng Axiom ngay khi đủ tính năng (không bao giờ viết std bằng C, không phải port); nới phụ thuộc T065, T069, T073, T075 theo tính năng cần | ROADMAP, board, axiom-stdlib | Nhận xét của chủ dự án |
| 2026-09-30 | Rà soát lần 3 trước khi chạy thật: task critical không bị bỏ đói (drain); requeue quá 3 lần thì chặn; `start` kiểm tra phụ thuộc; commit bỏ qua `docs/` và file gitignore; `.claude/settings.json` (cấm sửa `docs/`, cấm `git push`); QA build riêng `build-qa-<ID>`; I/O nhị phân chống CRLF (T004/T005); rút yêu cầu ghi dần; dùng Write/Edit thay heredoc; nạp tool deferred; harness_check bắt CR/escape vỡ | taskctl.py, harness_check.py, skills, axiom-qa, board | Lỗi phát hiện khi mô phỏng và thử toolchain |
| 2026-09-30 | Kiểm tra cuối: 17 task tham chiếu tài liệu trong `docs/base/tasks` thiếu tiền tố `tasks/`; harness_check kiểm mọi tham chiếu spec | board, harness_check.py | Agent sẽ tìm sai thư mục |
| 2026-09-30 | Giữ PE writer tối giản trước self-host (T027); thêm phép đối chứng: .obj của axiom0 được gcc/ld link và phải chạy giống PE tự ghi (T026 fixture, T028 mọi chương trình run/basic); chỉ là test, không dùng trong đường sản xuất | T026, T028, axiom-testing | Tách lỗi COFF writer khỏi lỗi linker; chứng minh .obj dùng được với toolchain khác |
