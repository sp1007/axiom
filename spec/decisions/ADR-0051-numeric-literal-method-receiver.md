# ADR-0051 — A method call on an unsuffixed numeric literal defaults the receiver first

Status: accepted (2026-11-26, architect; owner-delegated decision). Type B (clarification of SPEC-03 literal
defaulting / SPEC-41 AXS-FLT-003 item 2 for method receivers). Implementation: T461b.

## Tóm tắt
- QA của T461 (N5) thấy `1.0.exp()` bị từ chối với `AX_TYPE_UNKNOWN_FIELD`, trong khi `let x = 1.0; x.exp()` chạy được.
  Lexer đúng spec (AXS-LEX-056: `1.0` `.` `exp`); lỗi nằm ở typeck: kiểu của literal chưa hậu tố còn là biến
  `FloatVar`/`IntVar` khi tra phương thức, nên không tìm được phương thức nào.
- Quyết định: khi bộ nhận của lời gọi phương thức (hoặc truy cập trường/hằng liên kết qua `.`) là biến kiểu số còn tự do,
  typeck áp dụng ngay giá trị mặc định đã có (`FloatVar` → `f64`, `IntVar` → `i32`) rồi mới tra phương thức. Không có
  quy tắc mới về kiểu mặc định; chỉ là áp dụng sớm hơn tại đúng một chỗ cần kiểu cụ thể.
- Hệ quả: `1.0.exp()`, `2.0.sqrt()`, `1.max(2)` (đã có trong bảng AXS-LEX-056) chạy được; `1.max(2i64)` báo lỗi lệch kiểu
  (viết `1i64.max(2i64)`). Bộ nhận đã bị ràng buộc trước đó (vd. `let y: f32 = ..; (1.0 + y).sqrt()`) không bị ảnh hưởng.
- Phương án bị loại: từ chối như Rust (E0689) — kém tiện, trái tinh thần REQ-OWNER-007; hoãn tra phương thức tới cuối
  thân hàm — phức tạp, khó xác định. Revisit: không.

## Context
- SPEC-01 AXS-LEX-056 already tokenises `1.0.exp()` as `Float` `Dot` `Ident` `LParen` `RParen` and lists
  `1.max(2)` as a valid method call on an integer literal.
- SPEC-03 (literal typing, `IntVar`) and SPEC-41 AXS-FLT-003 item 2 default an unconstrained `IntVar` to `i32`
  and an unconstrained `FloatVar` to `f64` *at the end of the body*. Method lookup needs a concrete receiver type
  earlier, so an unsuffixed literal receiver currently fails with `AX_TYPE_UNKNOWN_FIELD` (T461-qa.md N5).

## Options
1. Default the receiver variable at the point of method/field/associated-item lookup (chosen).
2. Reject with a dedicated diagnostic and a fix-it (`1.0f64.exp()`), as Rust E0689.
3. Defer method resolution of such receivers to the end of the body and re-check.

## Decision
When the receiver of `recv.name(..)` or `recv.name` has a type that is still an unconstrained `IntVar` or `FloatVar`
at lookup time, typeck unifies it with the default type (`i32` / `f64`) before the lookup. Literal range checks
(SPEC-40 overflow rule, AXS-FLT-003 item 3) apply to the defaulted type as usual. Recorded as the bullet "Literal method receivers" of SPEC-41
AXS-FLT-003 item 2; it applies equally to integer literals.

## Consequences
- T461b implements it in `compiler/types/typeck.ax` with tests; SPEC-41 AXS-FLT-003 item 2 records the rule.
- No change to the lexer, the parser, the defaulting types or REQ-OWNER-007 promotion.
- A receiver literal never adopts a type from the method's argument types (no backward inference through methods).

## Sources
T461-qa.md N5; SPEC-01 AXS-LEX-056; SPEC-03 integer-literal defaulting; SPEC-41 AXS-FLT-003; SPEC-40 literal rules.
