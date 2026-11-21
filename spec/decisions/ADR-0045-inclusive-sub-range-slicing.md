# ADR-0045 — Inclusive sub-ranges `s[a..=b]` and `s[..=b]`

Status: accepted (2026-11-21, architect; owner-delegated decision). Type B (architecture clarification).

## Tóm tắt
- QA của T496 phát hiện `s[0..=2]` cho độ dài 2 thay vì 3 (cả interp lẫn native): compiler chấp nhận cú pháp
  nhưng bỏ qua dấu `=`, tức là cắt sai âm thầm.
- SPEC-02 AXS-GRM-052 đã định nghĩa `a..=b` là range có chứa đầu mút, nhưng AXS-GRM-070 chỉ liệt kê `s[a..b]`,
  `s[a..]`, `s[..b]`, nên không rõ dạng bao gồm có được dùng trong chỉ số hay không.
- Quyết định: `s[a..=b]` và `s[..=b]` là hợp lệ và có nghĩa đúng như `[a, b]` (b được tính), độ dài `b - a + 1`.
  Kiểm tra biên làm trong độ rộng của kiểu chỉ số (đúng quy tắc ADR-0044 §1): `b < len` (không phải `b + 1 <= len`
  tính trong kiểu có thể tràn), nên `s[0..=u128.MAX]` và `s[0..=usize.MAX]` phải bẫy `index out of bounds`, không bị
  quấn số. `a..=` (thiếu đầu mút phải) vẫn là lỗi cú pháp.
- Task sửa: T496a (semantics). Revisit: không.

## Context
- `_workspaces/reports/T496-qa.md` Follow-up 1: `let t = s[0..=2]; len(t)` prints 2, interp and native, also with
  `usize` bounds and for `s[..=hi]`; reproduces with the compiler before T496.
- SPEC-02 AXS-GRM-052 (`a..=b` end included) and AXS-GRM-070 (open forms only inside index brackets);
  SPEC-03 AXS-SEM-047 and the panic table (`index or sub-range out of bounds`); SPEC-40 AXS-INT-053/054 and
  ADR-0044 §1 (bounds of an index wider than 64 bits are checked in the index's own width before the cast to `usize`).

## Options
1. Reject `..=` inside index brackets with a diagnostic.
2. Accept it with the inclusive meaning, checked as `b < len` in the bound's own (unsigned-reinterpreted) width.
3. Accept it and lower as `s[a..b+1]` with a plain `+ 1`.

## Decision
Option 2. Inside index brackets, `s[a..=b]` denotes the elements `a..b` *including* `b`, and `s[..=b]` is `s[0..=b]`.
The sub-range is valid iff `a <= b + 1` mathematically and `b < len` (so the empty inclusive range is `s[k..=k-1]` only
when `k >= 1`; `s[0..=x]` is never empty). Lowering: check `b < len` (for a bound type wider than `usize`, in that width,
per ADR-0044 §1), then compute the exclusive end `b + 1` in `usize`, which cannot overflow because `b < len <= usize.MAX`;
then apply the usual `a <= end` check. Out-of-bounds panics with `index out of bounds` (SPEC-03 panic table).
Option 1 would remove a form the grammar already gives a meaning to; option 3 overflows for `b = MAX` (wraps to an empty
or huge slice instead of trapping).

## Consequences
- SPEC-02 AXS-GRM-070 lists the inclusive forms. No new diagnostic.
- Fix task T496a (owner axiom-semantics): MIR builder range lowering (reuse `mb_emit_range_bounds_check`), interpreter and
  native parity tests with exact `// stdout:`, trap tests for `b == len` and `b == MAX` of `usize`, `u64`, `u128`, `i128`.

## Sources
- `spec/SPEC-02-grammar.md` AXS-GRM-052, AXS-GRM-070; `spec/SPEC-03-core-semantics.md` AXS-SEM-047, §panic messages;
  `spec/SPEC-40-integers.md` AXS-INT-053/054; `spec/decisions/ADR-0044-t455-integer-model-gaps.md` §1;
  `_workspaces/reports/T496-qa.md`; tasks/0476 §86-87.
