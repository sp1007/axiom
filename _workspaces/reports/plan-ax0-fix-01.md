# plan-ax0-fix-01 — native intrinsics, assert, panic

## Tóm tắt
- Lỗi đã xác nhận (2026-10-19): các intrinsic wrapping/bit (`wrapping_*`, `rotate_*`, `leading_zeros`,
  `trailing_zeros`, `count_ones`), `assert` và `panic` chỉ được interp xử lý theo tên; backend native
  biên dịch thân giả `{ 0 }` / `{}`. Hậu quả: mọi `assert` ở chân native là vô nghĩa, `panic` không
  dừng chương trình, hàm băm kernel/std native trả hằng số — axiomc build native (T085–T087) sẽ sai.
- Quyết định: tạo task sửa T134 "AX0-FIX-01", ưu tiên 0 (chạy một mình), phase P10-selfhost,
  owner axiom-backend, model sonnet (ngữ nghĩa đã đặc tả đầy đủ, kiểm chứng bằng đối chứng
  interp/native), gate opus.
- Hướng sửa theo ADR-0004 §1 / SPEC-03: MIR builder hạ các intrinsic thành phép toán MIR và
  terminator Assert/abort (mã thoát 101) cho cả hai bộ thực thi; một bảng intrinsic duy nhất; intrinsic
  không có trong bảng là lỗi biên dịch `AX_TYPE_UNKNOWN_INTRINSIC`; quét lại toàn bộ test native để
  tìm test "qua vô nghĩa"; đối chứng hash native với hằng tham chiếu của `kernel/hash.c`.
- T086 nay phụ thuộc T134. Không có ADR mới (đây là phần thực thi còn thiếu của ADR-0004 §1);
  ghi vào nhật ký thay đổi ROADMAP.

## Decision
Classification: TYPE A defect with a TYPE B clarification (single intrinsic table + compile-error
guard), covered by existing ADR-0004 §1 and SPEC-03; no new ADR needed.

Options considered:
1. Patch native only (special-case names in lir/lower like the host intrinsics) — rejected: keeps two
   divergent implementations and repeats the by-name pattern that caused the bug.
2. Lower in the MIR builder so both executors run the same MIR (chosen; ADR-0004 §1 spec'd route),
   plus a table-driven guard so an unhandled `@intrinsic` can never again compile silently.
3. Implement in std as plain Axiom (shifts/loops) — rejected: `assert`/`panic` need the abort
   terminator anyway, and per-call loops would slow the hash path of axiomc.

Owner axiom-backend because most new work is LIR/x64 isel/encoder; MIR builder, interp, verifier and
opt are in `paths`, typeck.c and TYPE.def as `locks`. Paths include `tests/selfhost`, which overlaps
running T085, so T134 starts right after T085 is accepted. Real bugs found in ported `compiler/` or
`std/` code are not fixed in T134; they are reported as follow-ups and marked `native-after: T086`
until the architect files fix tasks.

Checks: `taskctl.py lint` OK, `taskctl.py validate` OK (217 tasks), `harness_check.py` OK,
`reqcov.py --strict` COVERAGE OK.

Risk: the vacuous-test sweep may reveal several real bugs in the ported modules, which would add
fix tasks before T086.

## Files changed
- _workspaces/tasks/todo/T134-ax0-fix-01-native-intrinsics-assert-panic.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- spec/ROADMAP.md
- _workspaces/reports/plan-ax0-fix-01.md
