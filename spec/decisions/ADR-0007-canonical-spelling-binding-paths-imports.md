# ADR-0007 — Canonical spelling: `=` for binding/assignment, `.` for every path, `use`, `module`

## Tóm tắt
Bộ tài liệu gốc viết cùng một khái niệm bằng nhiều cách: `x := 1` / `var x = 1` / `let mut x = 1`;
`a::b` / `a.b`; `import` / `use`; `mod` / `module`. Chủ dự án đã chốt (REQ-OWNER-001, REQ-OWNER-002):
gán và khai báo **chỉ dùng `=`**, phân tách đường dẫn **chỉ dùng `.`**. ADR này ghi lại bốn quyết định
chính tả đó và phần hệ quả kỹ thuật: (1) `let` / `let mut` là dạng khai báo duy nhất, `var` và `:=`
không phải cú pháp Axiom và có chẩn đoán kèm fix-it; (2) `::` không phải token, mọi đường dẫn dùng `.`
và **resolver** (không phải parser) phân biệt giá trị / module / kiểu; (3) `use` là từ khoá import duy
nhất, `import` bị từ chối kèm fix-it; (4) `module a.b` khai báo module của file, `mod` bị từ chối.
Vì không còn `::` nên không có "turbofish": tham số generic trong biểu thức viết `f<T>(x)` và parser
dùng quy tắc cam kết (commit) cố định. Ngữ nghĩa không đổi, chỉ đổi chính tả. Revisit: không (quyết
định của chủ dự án).

Status: **Accepted** (owner decisions REQ-OWNER-001/002 + architect consolidation, T001).
Date: 2026-10-01. Revisit: no.

## Context

The corpus disagrees with itself on four spellings:

| Topic | Variants in `docs/base` | Where |
|---|---|---|
| Mutable binding | `var x = 1` | 0154 §7, 0155 §46, 0243 §31, tasks/0323 §30-31, tasks/0324 §76 |
| | `let mut x = 1` | tasks/0476 §9 (frozen v1.0), 0243 §8 (`mut` keyword) |
| | `x := 1` | scattered examples (and EBNF meta-notation that looks like it) |
| Path separator | `a::b`, `Result::Ok(v)`, `Self::Item`, `foo::<T>()` | 0154 §45, 0243 §10/§34/§39, tasks/0476 §25/§46/§79 |
| | `a.b`, `Color.Red`, `std.fs.File` | 0155 §59, tasks/0323 §49-51, tasks/0324 §27 |
| Import keyword | `import a.b` | 0154 §8 ("no `use`"), 0155 §7, tasks/0323 §52, tasks/0324 §57 |
| | `use a::b` | 0243 §34, tasks/0476 §79-80 |
| Module keyword | `module a.b` (file-level declaration) | 0154 §7, 0155 §6, tasks/0323 §86, tasks/0476 §79 |
| | `mod x;` / `mod x { … }` (Rust style, inline modules) | 0243 §34, tasks/0324 §10 |

The project owner fixed the first two on 2026-09-29 (`spec/requirements/OWNER.md`): `=` is the only
binding/assignment spelling; `.` is the only namespace/library/path separator. The other two follow the
frozen v1.0 surface (tasks/0476) and the binding skill `axiom-syntax`.

## Options

A. Keep several spellings as aliases (accept both `var` and `let mut`, both `::` and `.`).
   Rejected: violates ASYNTAX-20 ("one canonical surface syntax", tasks/0476 §140) and the owner's
   requirement; every tool and every AI-generated program would have to choose.
B. One spelling per concept, everything else is a syntax error with a targeted fix-it. **Chosen.**

## Decision

1. **Binding and assignment use `=` only.** `let x = e` (immutable), `let mut x = e` (mutable),
   `let x: T` (deferred initialisation), `x = e` and the compound forms `+= -= *= /= %= &= |= ^= <<=
   >>=`. `:=` is not a token: the lexer reports `AX_LEX_COLON_EQ` with a fix-it replacing it by `=`
   and continues as if `=` had been written (SPEC-01 AXS-LEX-083). `var` is **not a keyword**: a
   statement that starts with the identifier `var` followed on the same line by another identifier
   reports `AX_PARSE_VAR` with the fix-it `let mut`, and parsing continues as a `let mut` statement
   (SPEC-02 AXS-GRM-045).
2. **`.` is the only path separator**: module paths, imports, enum variants, associated items,
   qualified trait calls, package-qualified names (`std.io.print`, `Result.Ok(v)`, `Self.Item`,
   `Vec.new()`, `Display.display(p)`). `::` is not a token: the lexer reports `AX_LEX_COLON_COLON`
   with a fix-it replacing it by `.` and continues with a `.` token (SPEC-01 AXS-LEX-082).
   The parser never decides what a dotted name means: it builds a `DottedChain` and the resolver
   classifies each segment with the frozen lookup order (SPEC-02 AXS-GRM-055; resolver rules in T014).
3. **Generic arguments in expressions have no turbofish.** `f<T>(x)`, `Vec<i32>.new()`,
   `Point<f32> { … }`: the parser parses `<…>` tentatively after a name segment and commits only when
   the closing `>` is immediately followed by `(`, `.` or (where struct literals are allowed) `{`
   (SPEC-02 AXS-GRM-056). Comparison operators are non-associative, so no valid comparison is lost
   except the documented corner `f(a < b, c > (d))`, which must be parenthesised.
4. **`use` is the only import keyword.** `use a.b.C`, `use a.b.C as D`, `use a.b.{C, D as E}`,
   `pub use …` for re-export. `import` is not a keyword: an item that starts with the identifier
   `import` followed on the same line by an identifier reports `AX_PARSE_IMPORT` with the fix-it `use`
   and is parsed as a `use` declaration (SPEC-02 AXS-GRM-038).
5. **`module a.b` is the only module spelling** — one optional declaration at the top of a file
   (ADR-0006 §7 maps `src/a/b.ax` to module `a.b`). `mod` is not a keyword; `mod x` at item position
   reports `AX_PARSE_MOD`. Inline modules (`mod x { … }`) are not Axiom v0.1 syntax.
6. **Qualified forms that relied on `::`** are written with `.`: a trait method call is
   `Trait.method(x)`; an associated type is `T.Item` / `Self.Item`. The fully qualified form
   `<T as Trait>::name` (0155 §60, already postponed there) has no v0.1 spelling; if trait resolution
   (T055/T056) proves it necessary, a new ADR defines one.
7. **EBNF in `spec/` is ISO style** (`rule = a , b ;`), never `:=` / `::=`, so grammar notation is
   never mistaken for Axiom code.

## Consequences

- `spec/SPEC-01-lexical.md` and `spec/SPEC-02-grammar.md` (T001) apply these rules; every Axiom
  example in `spec/`, tests and std uses them. Examples copied from `docs/base` are translated with the
  table in `axiom-syntax`.
- Lexer: two recovery diagnostics (`AX_LEX_COLON_COLON`, `AX_LEX_COLON_EQ`), T010. Parser: three
  (`AX_PARSE_VAR`, `AX_PARSE_IMPORT`, `AX_PARSE_MOD`), T011.
- `var`, `import`, `mod` stay usable as ordinary identifiers (`let var = 1` is legal); the diagnostics
  fire only in the statement/item-start shapes above, which are never valid Axiom.
- The resolver carries the disambiguation work and the warning `AX_NAME_SHADOW_MODULE` (T014).
- Requirements covered: REQ-OWNER-001, REQ-OWNER-002.

## Sources
`spec/requirements/OWNER.md` (REQ-OWNER-001, REQ-OWNER-002); `.claude/skills/axiom-syntax/SKILL.md`
Rules 1-2; 0154 §7-8, §45; 0155 §6-7, §46, §59-60; 0243 §8, §31, §34, §39; tasks/0323 §30-31, §49-53;
tasks/0324 §10, §27, §57, §76; tasks/0476 §9, §25, §79-80, §104, §140 (ASYNTAX-20).
