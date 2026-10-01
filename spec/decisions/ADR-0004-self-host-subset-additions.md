# ADR-0004 — Self-host subset additions found by the 2026-09-30 audit

## Tóm tắt
Khi viết thử axiomc theo từng module, đợt thẩm định phát hiện vài tính năng compiler viết bằng Axiom
chắc chắn cần nhưng chưa có task nào làm. Quyết định đưa vào tập self-host (vẫn tối thiểu theo R7):
phép toán **wrapping/bit** không bẫy tràn (cho hàm băm, mangling); **bảng hằng** dạng `const`
aggregate đặt một lần trong `.rdata` (bảng opcode, từ khoá, mã chẩn đoán) — không thêm `static`;
**view lưu trong struct** (iterator, context của compiler); **HashMap duyệt theo thứ tự chèn**, dùng
đúng hàm băm của axiom0 để đối chứng từng byte; **drop glue cho kiểu generic**; `@derive(Hash, Eq,
Ord)`; vòng lặp có nhãn, pattern ký tự/khoảng/hoặc, ép `enum as uN`; hằng được tính qua một giao diện
evaluator để `types` không phụ thuộc ngược vào `interp`. Không có tính năng nào trong số này bị chủ
dự án xếp sau self-host; phần còn lại (saturating, i128, `static`, `static mut`) vẫn ở P12/P13.
Revisit: không.

Status: **Accepted** (architect, audit 2026-09-30: A1-06, A1-07, A1-08, A1-09, A1-10, A1-12, A1-13,
A3-13, A1 cross-lens note on const evaluation layering).
Date: 2026-09-30. Revisit: no.

## Context

T003a defines the exact self-host subset (ROADMAP R7). A module-by-module sketch of axiomc (audit A1)
found features the compiler needs that no P0–P9 task delivered, or delivered only in interp mode.
Each one below is small; each missing one would cause either a blocked port task or throw-away C.

## Decision

1. **Wrapping and bit intrinsics** — `wrapping_add/sub/mul/neg`, `rotate_left/right`,
   `leading_zeros`, `trailing_zeros`, `count_ones` for every integer width, as MIR ops without an
   overflow assert (interp in T034, native in T037; std methods wrap them in T069). SPEC-03 defines
   them. Saturating ops, i128/u128 stay in E12.1.
2. **Constant tables** — `const` items of aggregate type (arrays of structs with integer, bool,
   `char`, `Str` fields) that are used as places are materialised **once** (interp: one allocation;
   native: `.rdata` with relocations for `Str` pointers) and indexed in place, never copied per use.
   Oracle side T061, native side new task T061d. `static` / `static mut` items stay outside the
   subset (E13.3 / ADR-0001): axiom0 reports `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` for them.
3. **Stored views** — a view held in a struct field (0541 §96, tasks/0270 ACAP-43): owner-outlives
   check, no self-reference. Rule in SPEC-11 (T045), implementation in T048.
4. **HashMap contract** — std `HashMap`/`HashSet` iterate in insertion order (index-map layout) and
   use the documented 64-bit hash algorithm of axiom0 `kernel/` (T007), so ported code produces
   byte-identical output to axiom0 (T073).
5. **Generic drop glue** — drop elaboration per monomorphized instance and generic `Drop` impls
   (T054b); intrinsics `drop_in_place<T>` and `needs_drop<T>` (T061a).
6. **Derive and tuple impls** — `@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)` (T056; the
   ownership analysis T046 already recognises `@derive(Copy)` as a built-in marker, ADR-0006 §3);
   `Eq`/`Ord`/`Hash` for tuples up to arity 4 in std core (T069).
7. **Control/pattern forms** — labelled `break`/`continue`, literal / char-range (`'a'..='z'`) /
   or-patterns, `enum as uN` for fieldless enums (SPEC-02 in T001, typing in T031/T038/T038b).
8. **Const evaluation layering** — `types` declares a const-evaluator interface; the driver wires the
   interpreter into it. No `types → interp` include (archcheck rule, T006).
9. **MIR text parser** — test infrastructure in C only (verifier/interp tests); not in the subset,
   not ported to axiomc (T003a).

## Consequences

Scope/acceptance lines added to T001, T003, T003a, T006, T007, T031, T034, T037, T038, T038b, T045,
T048, T054b, T056, T061, T061a, T069, T073; new task T061d. `spec/selfhost-subset.tsv` (T003a)
lists each item with its delivering and first consuming task.

## Sources
tasks/0260 §3-4, §39-40; 0263 §42; 0541 §96; tasks/0270 ACAP-43; 0172 AKERNEL-24; ROADMAP R7;
audit A1-06, A1-07, A1-08, A1-09, A1-10, A1-12, A1-13, A3-13.
