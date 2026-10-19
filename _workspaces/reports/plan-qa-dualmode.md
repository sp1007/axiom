# plan-qa-dualmode — Standing QA rule: native PASS must check something

## Tóm tắt
- T134 phát hiện backend native của axiom0 biên dịch thân giả của các hàm `@intrinsic` (wrapping/bit trả 0, `assert`/`panic` không làm gì), nên mọi chân test native chỉ dựa vào `assert()` đã qua "nhầm" nhiều tuần.
- Quy tắc thường trực (chủ dự án duyệt 2026-10-19): "interp đúng không có nghĩa native đúng; PASS native phải chứng minh được là có kiểm tra".
- Gate QA có bước mới 4a: mỗi test chạy native mà task thêm/sửa phải chốt một kết quả quan sát được (exit khác 0, `stdout:` chính xác, `stdout-contains:`, hoặc `test: diff`). Chỉ exit 0 thì không phải bằng chứng.
- Test chỉ dựa vào `assert()` bị tính FAIL cho đến khi T134 xong (sau đó `assert(false)` native thoát 101).
- Các canary của T134 (assert_false, panic_abort, unknown_intrinsic) chạy trong mọi bộ test đầy đủ; nếu chúng bị SKIP hoặc lỗi thì gate FAIL. QA phải đột biến thử một kỳ vọng trong snapshot để thấy chân native FAIL.
- Skill axiom-testing ghi quy tắc cho người viết test.
- Tạo task T139 (axiom-qa, khoá `tools/axtest.py`): runner tự so mã thoát và stdout giữa interp và native cho test `run`, kèm báo cáo `WEAK-NATIVE`. T139 phụ thuộc T134. T086 phụ thuộc T139, vì Stage-1 là gate đầu tiên mà file chạy native (axiomc1) là bằng chứng chính.

## Decision
Type B (process/architecture clarification), owner-approved.

Options considered for the runner gap:
1. Do nothing in the runner; rely on QA manual checks only. Rejected: manual checks are what failed
   for weeks.
2. Add a new directive that marks tests as "differential". Rejected: needs every test edited, and
   new directives multiply exemptions.
3. **Chosen:** the runner compares interp and native observations (exit code and stdout bytes) for
   every `run` test that executes in two or more modes, using the same comparison `test: diff` already
   uses. It also reports `WEAK-NATIVE` for native legs whose only expectation is exit 0. This
   changes no test files and catches output the test prints but does not declare.

Ordering: T139 depends on T134, because the comparison must run on a suite that T134 has already
swept and where `assert` actually works. T086 now depends on T139. The task is small (sonnet), and
without it Stage-1 would treat "axiomc passes the full suite" as evidence even though the runner
never compares undeclared output between modes. Before T139 lands, Gate protocol 4a tells QA to
check that agreement by hand.

`tools/axtest.py` is a shared file owned by T005 (done). T139 lists it under `locks:`, following
ADR-0005 §2. The axiom-testing ownership sentence now mentions this. T139 does not touch any path
owned by T085 or T134.

## Checks
- `taskctl.py lint` on T139: OK
- `taskctl.py validate`: OK (218 tasks)
- `harness_check.py`: HARNESS OK (only the known optional guard-hook WARN)
- `reqcov.py --strict`: COVERAGE OK, gaps 0

## Files changed
- .claude/agents/axiom-qa.md
- .claude/skills/axiom-testing/SKILL.md
- _workspaces/tasks/todo/T139-axtest-cross-mode-agreement-native-evidence.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- spec/ROADMAP.md
- CLAUDE.md
- _workspaces/reports/plan-qa-dualmode.md
