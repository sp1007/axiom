# ADR-0010 — Grammar forms for Axiom v0.1 (types, precedence, statements, items, patterns)

## Tóm tắt
ADR này chốt các điểm ngữ pháp mà tài liệu gốc viết khác nhau, để `spec/SPEC-02-grammar.md` chỉ có
một dạng cho mỗi cấu trúc:
(1) Kiểu mảng cố định là `[N]T` (không phải `[T; N]`), kiểu dãy độ dài động là `[T]` dùng sau view:
`view<[T]>`. (2) Bảng ưu tiên toán tử: toán tử bit (`& ^ |`) **chặt hơn** so sánh — để
`status & MASK == 0` có nghĩa đúng như ví dụ trong ADR-0001; mọi phép so sánh nằm chung một mức và
không kết hợp (`a < b < c` là lỗi); `as` nằm ngay dưới toán tử một ngôi. (3) **Phép gán là câu lệnh**,
không phải biểu thức — `if x = 5` là lỗi cú pháp và `f(x = 1)` để dành cho tương lai. (4) `return`,
`break`, `continue` là biểu thức kiểu `never` nên dùng được ở nhánh `match`. (5) Tham số `self` luôn
ghi kiểu (`self: view<Self>`), không có dạng viết tắt. (6) Closure không có `move`. (7) Trong điều
kiện `if`/`while`/`match`/`for`, `Tên {` không phải struct literal. (8) Cấu trúc chưa cần cho self-host
(`async`, `.await`, `comptime`) có ngữ pháp trong spec nhưng axiom0 chỉ báo "chưa hỗ trợ". Các dạng
khác chưa cần được liệt kê là hoãn kèm mốc. Revisit: không, trừ mục 3 nếu sau này thêm tham số có tên.

Status: **Accepted** (architect, T001). Date: 2026-10-01. Revisit: no (item 3 only together with a
named-argument proposal).

## Context, options and decision (per item)

Rule ids refer to `spec/SPEC-02-grammar.md`.

### 1. Array and slice types (AXS-GRM-082, AXS-GRM-083, AXS-GRM-062)
- Sources: `[T; N]` in 0243 §17 and tasks/0324 §48; `[N]T` decided in tasks/0476 §17 (frozen) and
  `axiom-syntax`. Dynamic-length sequences: `view<[T]>` throughout the corpus (more than 70 occurrences)
  and in tasks T048/T048b; tasks/0476 §17 mentions `[]T` once.
- Decision: fixed array type **`[N]T`** (`N` a constant expression); unsized sequence type **`[T]`**,
  used behind a view or pointer (`view<[u8]>`). The two are told apart after the `]`: an element type
  on the same line means array. Array literals `[a, b, c]` and the repeat form `[value; count]`
  (tasks/0324 §87, 0155 §26) are unchanged. The old type spelling `[T; N]` reports
  `AX_PARSE_ARRAY_TYPE_ORDER` with a fix-it.

### 2. Operator precedence (AXS-GRM-050..054)
- Sources: the C order — `|`, `^`, `&` looser than `== !=` and `< <= > >=`, with equality and
  relational operators on two separate levels — is given by 0243 §35, 0155 §35, 0173 §30,
  tasks/0324 §28 and the "conceptual" list of tasks/0476 §136. The opposite order — `&`, `^`, `|`
  tighter than a single comparison level `== != < <= > >=`, with `as` "near unary/postfix" — is
  given by **0109 §92** only. Position of `as`: tighter than unary in 0243 §35, looser than unary
  in 0155 §35 and 0173 §30. Range: below the logical operators in tasks/0324 §38 and 0109 §92.
- Decision (tightest first): postfix; unary `- ! ~ *`; `as`; `* / %`; `+ -`; `<< >>`; `&`; `^`; `|`;
  comparison `== != < <= > >=` (one level, **non-associative**); `&&`; `||`; range `.. ..=`
  (non-associative). This is the order of 0109 §92, chosen **against** the five documents that give
  the C order. Rationale: Axiom has no implicit truthiness (tasks/0323 ASYNTAX-59), so with the C
  order `flags & MASK == 0` would always be a type error and the C order has no valid use for the
  looser bitwise levels; ADR-0001 §2 already writes `UART0.status & TX_READY == 0` with the intended
  meaning. tasks/0476 §136 calls its list "conceptual" and tasks/0476 §137 only requires that the
  table be fixed — it is fixed here. One non-associative comparison level (0109 §92; made
  non-associative by `axiom-syntax` Rule 2) is what makes the generic-argument rule of ADR-0007 §3
  sound. `as` is placed just below the prefix operators (0155 §35, 0173 §30, compatible with
  0109 §92).
- No unary `+` (tasks/0324 §30, 0155 §35 had it): it has no use and one fewer prefix form.
- `&x` and `&mut x` report `AX_PARSE_REFERENCE_OPERATOR` (use `view(x)` / `mut_view(x)`).

### 3. Assignment is a statement (AXS-GRM-043) — Revisit with named arguments
- Sources: assignment expression of type unit in 0155 §38; right-associative assignment expression in
  tasks/0324 §39.
- Decision: `place = expr` and the compound forms are **statements**. `if x = 5 { }` and `f(x = 1)`
  are syntax errors (`AX_PARSE_ASSIGN_IN_EXPR`, hint `==`); `a = b = c` does not exist. A match arm or
  closure that assigns uses a block: `Some(v) => { total += v }`. This also keeps `name = value`
  inside call parentheses free for a future named-argument feature (tasks/0323 §65 excludes it from
  v1 but tasks/0476 ASYNTAX-65 forbids changing the meaning of existing syntax later).

### 4. Jump expressions; `break` carries values and labels (AXS-GRM-065, AXS-GRM-066)
- Sources: `return` is a statement in 0155 §47; `break` has no value in 0155 §48; `break value` in
  0243 §25, tasks/0323 §95, tasks/0476 §34; labels in tasks/0323 §97, tasks/0324 §78-79, ADR-0004 §7.
- Decision: `return [e]`, `break ['label] [e]`, `continue ['label]` are expressions of type `never`
  at the lowest precedence level, so `Err(e) => return Err(e)` needs no block. The label and the
  operand are taken only from the same line (ADR-0008 §6). Loops take an optional
  label `'name:` before `loop` / `while` / `for`. Labelled blocks are not part of v0.1.

### 5. Functions, receivers, methods (AXS-GRM-025, AXS-GRM-026, AXS-GRM-032)
- Receiver shorthand: `self` / `mut self` by value in 0243 §19; `self` meaning an inferred view in
  tasks/0323 §24; a `Receiver` production in tasks/0324 §67; always `self: Type` in tasks/0476
  §39-43 and `axiom-syntax`. Decision: **no shorthand** — the receiver is the first parameter, named
  `self`, with an explicit type (`self: Self`, `self: view<Self>`, `self: mut_view<Self>`); a bare
  `self` reports `AX_PARSE_SELF_NEEDS_TYPE`.
- Methods are functions whose first parameter is `self` (tasks/0476 ASYNTAX-29). The grammar admits them both as
  free functions (tasks/0476 §39) and inside `impl Type { … }` (tasks/0323 §21); resolution order is
  tasks/0476 §88 (T053).
- Qualifier order is fixed: `[async | comptime] [unsafe] [extern "abi"] fn` (0243 §21 allowed any
  order). The ABI string is mandatory after `extern` (tasks/0476 ASYNTAX-49).
- A function without a body is written by ending the signature with a terminator; it is valid in
  traits, in `extern` blocks, and as an `extern` function item (foreign import, or `@at` overlay per
  ADR-0001). Elsewhere `AX_PARSE_FN_BODY_REQUIRED`.
- Return-type inference for functions (tasks/0323 §35) is not part of the grammar question: an
  omitted `-> T` means unit (tasks/0476 §7).

### 6. Closures (AXS-GRM-067)
- `move |x| …` in 0243 §30, 0155 §42, tasks/0324 §90; capture always inferred, "programmer does not
  write `move`" in tasks/0476 §37-38 (frozen). Decision: no `move` closures in v0.1; `move` stays a
  reserved word (ADR-0009 §2).

### 7. Struct literals and conditions (AXS-GRM-058, AXS-GRM-059)
- No source resolves `if x == Point { … } { … }`. Decision: in the condition of `if` / `while`, the
  scrutinee of `match` and `if let` / `while let`, and the iterable of `for`, a `{` after a path
  starts the block, not a struct literal; parentheses lift the restriction.
- Fields are separated by `,` or a line break (tasks/0476 §13); the shorthand `Point { x, y }`
  (tasks/0323 §18) is accepted. The update form `..base` (tasks/0476 §15 "may support") is deferred.

### 8. `view` / `mut_view` (AXS-GRM-069, AXS-GRM-084)
- Types `view<T>`, `mut_view<T>`; expressions `view(place)`, `mut_view(place)` as dedicated forms
  (ADR-0009 §2). No `&`, `&mut`, no safe `*x` (tasks/0476 §58).

### 9. Items (AXS-GRM-021..037)
- `static`: `@static var` in tasks/0323 §88; `static NAME: T = e` / `static mut` in 0109 §80, 0154
  §7; `unsafe static` in ADR-0001. Decision: `[unsafe] static [mut] NAME: Type [= expr]`. axiom0
  parses it and reports `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (ADR-0004 §2).
- Visibility: tasks/0476 §78 lists `pub`, `pub(package)`, `pub(module)` and `private`; 0155 §9 has
  `internal`. Decision: `pub`, `pub(package)`, `pub(module)`; private is the default and has no
  keyword (tasks/0323 §87); `private` and `internal` are not Axiom.
- Enum variants and struct fields are separated by `,` or a line break (0155 §15 used commas,
  tasks/0476 §24 line breaks; both accepted, ADR-0008 §8). Explicit discriminant values are deferred.
- `extern "abi" { … }` blocks and `extern "abi" fn` items (0243 §40, tasks/0323 §83-85, tasks/0476
  §126); `@link("name")` is an ordinary attribute on the block.
- Attributes: `@name` or `@name(args)` with expression arguments and optional `key = value` pairs;
  on items, impl/trait/extern members, fields and variants. `@at(<const expr>)` is admitted on
  `static`, `static mut`, `fn` and `extern fn` items by the general rule (REQ-OWNER-003, ADR-0001).
- No items inside blocks (local functions, consts, types) in v0.1; no glob imports (tasks/0476 §80).

### 10. Patterns (AXS-GRM-090..099)
- Set for v0.1: wildcard, binding (`mut`), literal (integer, `char`, bool), range (`a..=b`, `a..b`
  with literal bounds), path (`Option.None`), tuple-variant, struct (with `..`), tuple, or-patterns,
  guards; `let … else`, `if let`, `while let` (tasks/0476 §113-119, ADR-0004 §7, T038b).
- A single identifier in a pattern is classified by the resolver: an existing unit variant, unit
  struct or constant in scope makes it a constant pattern, otherwise it is a new binding. Dotted
  paths never bind.
- Deferred: binding-at (`name @ pat`), slice patterns, string/float literal patterns, `..` inside
  tuple patterns, generic arguments in pattern paths.

### 11. Staging (AXS-GRM-003)
- axiom0 parses the whole grammar (T011, T012) except the **S1** forms, whose keywords are reserved
  and whose grammar is fixed now but which the axiom0 parser rejects with
  `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP`: `async fn`, `.await` (E11.4), `comptime fn`, `comptime { }`
  (E14.1). This follows ROADMAP R7 (no out-of-subset code in C) and "final syntax from the first
  task" (ADR-0006). Constructs that axiom0 parses but does not type (floats, `static`, `dyn`, `@at`)
  are diagnosed by the later phase that owns them.

## Consequences

- SPEC-02 has one production per construct and a fixed precedence table; T011/T012 implement it
  without consulting `docs/base`.
- `axiom-syntax` is updated: slice type, precedence note, assignment statement, receiver rule,
  keyword list, labels.
- Deferred forms with their milestones are listed in SPEC-02 §12 and in the T001 report.

## Sources
0109 §80, §92; 0154 §7; 0155 §9, §15, §26, §35, §38, §42, §47-48, §60; 0173 §30; 0243 §17, §19, §21, §25,
§30, §35, §40; tasks/0323 §18, §21-24, §35, §65, §83-88, §95-97, §100 (ASYNTAX-59); tasks/0324 §28-39, §48, §67, §78-79,
§87, §90; tasks/0476 §7, §13-17, §24, §34, §37-43, §58, §78, §80, §88, §113-119, §126, §136-137, §140;
ADR-0001 §1-2; ADR-0004 §2, §7; ADR-0006; ROADMAP R7.
