# ADR-0009 — Lexical decisions for Axiom v0.1 (identifiers, keywords, literals, operators)

## Tóm tắt
Các tài liệu về lexer (0154, 0173, 0243, tasks/0324, tasks/0476) trái nhau ở nhiều điểm nhỏ. ADR này
chốt từng điểm cho `spec/SPEC-01-lexical.md`:
(1) **Định danh chỉ dùng ASCII ở v0.1** — chuỗi, ký tự và chú thích vẫn là UTF-8 đầy đủ (in được
"Xin chào thế giới"); định danh Unicode cần bảng XID lớn, viết bằng C rồi phải viết lại bằng Axiom
(trái R7), nên dời sau self-host và hiện báo lỗi rõ ràng — **đánh dấu Revisit** vì chủ dự án có thể
muốn đặt tên biến tiếng Việt sớm hơn. (2) Bộ từ khoá cố định gồm 37 từ, thêm `view`, `mut_view`,
`self`, `Self`; `var`, `import`, `mod` không phải từ khoá; `move`, `union`, `yield` được giữ chỗ.
(3) Số có hậu tố kiểu (`42u32`), dấu `_` chỉ nằm giữa hai chữ số; số thực phải có chữ số hai bên dấu
chấm (`1.0`), nên `1..2` và `p.0.1` không bao giờ bị hiểu nhầm. (4) Có ký tự `'a'`, byte `b'a'`,
chuỗi thô `r"…"`, nhãn vòng lặp `'outer`; **không có nội suy chuỗi** — `{` trong chuỗi là ký tự
thường. (5) Có phép gán kép (`+=` …) và `~`; không có `+%`, `+|`, `++`, `#`. (6) Chỉ `///` là chú
thích tài liệu.

Status: **Accepted** (architect, T001). Date: 2026-10-01.
Revisit: **yes — item 1 (ASCII-only identifiers) and item 9 (no string interpolation)**; others no.

## Context, options and decision (per item)

Each item lists the conflicting sources, the options, and the decision. Rule ids refer to
`spec/SPEC-01-lexical.md`.

### 1. Identifiers: ASCII only in v0.1 (AXS-LEX-030, AXS-LEX-031) — Revisit: yes
- Sources: Unicode XID identifiers in 0154 §4-5, 0173 §7, 0243 §3, tasks/0324 §3; "ASCII canonical,
  Unicode may be supported" in tasks/0476 §103 and tasks/0323 §10. Normalisation: none (0154 §6, 0173
  §7), reject non-NFC (0243 §3), normalise to NFC (tasks/0324 §3) — three different rules.
- Options: (A) XID + a normalisation rule now; (B) ASCII now, Unicode later; (C) "any non-ASCII
  scalar is an identifier character" (cheap but admits spaces, punctuation and look-alikes that XID
  excludes, and could not be narrowed later without breaking code).
- Decision: **B**. An identifier is `[A-Za-z_][A-Za-z0-9_]*`. A non-ASCII character outside comments
  and string/char literals reports `AX_LEX_NON_ASCII_IDENT`. Rationale: XID_Start/XID_Continue and NFC
  tables are large generated data that would be written in C and again in Axiom (ROADMAP R7); the
  self-host compiler and std use ASCII names; because every non-ASCII identifier is an error today,
  adding Unicode identifiers later is purely additive. When added (needs the Unicode property tables
  of E21.2; scheduled by the P21 planning task; to be settled before the spec freeze E23.2), the rule
  will be: XID_Start/XID_Continue, identity = scalar sequence, source must already be NFC (error
  otherwise, never silent normalisation — 0243 §3).
- Not affected: string literals, char literals and comments are full UTF-8 (owner rule: samples print
  `Xin chào thế giới`).

### 2. Keywords (AXS-LEX-040..043)
- Sources give six different lists (0154 §7, 0173 §3, 0243 §8, tasks/0323 §12, tasks/0324 §10,
  tasks/0476 §104); they differ on `var`, `import`, `use`, `mod`/`module`, `mut`, `move`, `dyn`,
  `loop`, `static`, `where`, `self`/`Self`.
- Decision — 37 reserved keywords: `as async await break comptime const continue dyn else enum extern
  false fn for if impl in let loop match module mut mut_view pub return self Self static struct trait
  true type unsafe use view where while`.
  - `view` and `mut_view` are keywords: `view(x)` operates on a *place* (it creates a capability, it
    does not move or copy `x`), so it is a syntactic form, not a call of a library function
    (tasks/0476 §55, tasks/0324 §94 called it "function-like"; the frozen semantics need the place).
  - `self` and `Self` are keywords (0243 §8; 0154 §7 had `self` as a special identifier).
  - Reserved for future use, rejected by the parser with `AX_PARSE_RESERVED_KEYWORD`: `move`
    (closure capture is inferred, tasks/0476 §37-38; explicit move capture may return with E11.1),
    `union` (E13.2), `yield` (E14.3).
  - Not keywords: `var`, `import`, `mod` (ADR-0007: targeted parser diagnostics instead); primitive
    type names (`i32`, `bool`, `char`, `never`, `Str`, …) and prelude names (0243 §9); attribute
    names; `package` (contextual, only inside `pub(package)`); `null` (0154 §11).

### 3. `_` (AXS-LEX-032)
- 0154 §42: `_` is an identifier that the pattern parser reinterprets. Decision: a lone `_` is its
  own token `Underscore` (wildcard / placeholder); `_x` and `__` are identifiers. A separate token
  keeps "is `_` a name?" out of the resolver.

### 4. Numeric literals (AXS-LEX-050..058)
- Type suffixes: rejected in 0154 §19; present in 0243 §13, tasks/0476 §91, 0152 §12 and `axiom-syntax`.
  Decision: **suffixes exist** — `i8 i16 i32 i64 isize u8 u16 u32 u64 usize` on integers, `f32 f64`
  on floats. `i128`/`u128` arrive with E12.1.
- Digit separators: `_` only between two digits (0154 §16 wants `1__000` rejected). `0x_ff`, `1_`,
  `1_u32` are errors. A numeric literal reports each diagnostic code at most once; a prefix with no
  digit at all (`0x`, `0x_`) reports only `AX_LEX_MISSING_DIGITS` (AXS-LEX-101).
- Base prefixes are lower-case only (`0x`, `0o`, `0b`); a leading-zero decimal is decimal (0154 §14).
- Float: digits on both sides of the point, or an exponent. `1.` is **not** a float (0154 §17 allowed
  it; `axiom-syntax` Rule 3 forbids it) and `.5` is not a float. This makes `1..2`, `1.max(2)` and
  `p.0.1` unambiguous with one character of lookahead plus the rule "after a `.` token a number is a
  plain decimal index" (AXS-LEX-057).
- A literal followed directly by identifier characters that are not a valid suffix is one erroneous
  token (`AX_LEX_INVALID_SUFFIX`), not an integer followed by an identifier (0154 §5 said two tokens).
- The lexer decodes integer values (T010); v0.1 limit 2^64 − 1 (`AX_LEX_INT_OVERFLOW`). Whether the
  value fits its *type* is a type-checker question (0154 §57).
- Floats lex and parse in axiom0 but are not typed there (owner decision 2026-09-30, E12.2).

### 5. Character, byte and label tokens (AXS-LEX-065..067)
- 0154 §21 and 0243 §16 postponed `char`; tasks/0324 §17 and tasks/0476 §93 have it; the owner
  decision of 2026-09-30 puts `char` before self-hosting. Decision: `'a'` is a `char` literal (one
  Unicode scalar value).
- Byte literal `b'a'` (tasks/0324 §18, 0243 §16): decision — it is lexical sugar for an integer
  literal with suffix `u8` (token kind `Int`), so it costs nothing after the lexer and works in
  patterns and ranges (`b'a'..=b'z'`).
- Loop labels are spelled `'name` (tasks/0323 §97, tasks/0324 §96). `'a'` is a char, `'a` not followed
  by `'` is a label (the well-known rule for this spelling). 0243 §7 ("no lifetime token") is kept in
  substance: the token is a label, Axiom has no lifetime syntax.

### 6. Strings (AXS-LEX-060..064, AXS-LEX-069)
- Escapes: `\n \r \t \\ \" \' \0 \xNN \u{…}` (union of 0154 §24, 0243 §15, tasks/0324 §19,
  tasks/0476 §96). `\xNN` is limited to 00–7F in strings and chars (strings stay valid UTF-8) and
  00–FF in byte strings.
- A string literal does not span lines (0173 §20 recovery rule made normative).
- Raw strings: absent in 0154 §49, simple form in 0243 §15, present in tasks/0476 §94 (frozen).
  Decision: `r"…"` (no escapes, no `"` inside); the `r#"…"#` family is deferred.
- Multi-line `"""…"""` (tasks/0324 §21-22): deferred; adding it later is safe because two adjacent
  string literals are never valid Axiom.

### 7. Operators and punctuation (AXS-LEX-080..086)
- Compound assignment: absent in 0154 §36 / 0155 §38, present in 0243 §11 and tasks/0476 §82
  (frozen) and used by tasks T030. Decision: present.
- Wrapping/saturating operators `+% -% *% +| -| *|` (0154 §37, 0173 §4): **not tokens**. The frozen
  operator list (tasks/0476 §82) omits them and ADR-0004 §1 provides wrapping arithmetic as
  intrinsics/methods.
- `~` is bitwise NOT (tasks/0324 §26, 0243 §11); `!` is logical NOT only.
- `->` is one token used for return types and for the unsafe pointer-member sugar (tasks/0476 §60).
- `#`, `$`, backtick and a bare `\` are invalid characters (0154 §48). A run of three or more dots is
  an error (0154 §47).
- `::` and `:=` are recognised only to diagnose them (ADR-0007).

### 8. Whitespace, line ends, BOM, comments (AXS-LEX-002, AXS-LEX-010..023)
- Whitespace is exactly space, tab, CR, LF (0154 §32); other Unicode spaces are invalid characters.
  LF is the line terminator; CR is plain whitespace, so CRLF files work and spans stay byte-exact.
- A UTF-8 BOM is accepted only at offset 0 (0243 §2).
- `///` is the only documentation comment in v0.1; `/** */` and `//!` (tasks/0324 §9) are ordinary
  comments until the documentation generator (E19.5) defines them. Block comments nest (all sources).

### 9. No string interpolation in v0.1 (AXS-LEX-069) — Revisit: yes
- 0154 §26-28, 0173 §16 and 0109 §90 specify `"Hello, {name}"` with a lexer mode switch; the frozen
  surface (tasks/0476) does not mention it and the self-host subset does not need it.
- Decision: `{` and `}` are ordinary characters in every string literal, permanently. If
  interpolation is added, it will use a distinct literal prefix (a new token kind), so that no existing
  string changes meaning (tasks/0476 ASYNTAX-65). Formatting uses the std formatting API (T071).

## Consequences

- SPEC-01 is implementable by T010 with one character class table and no Unicode property data.
- The lexer has exactly one context dependency (previous token is `.`, AXS-LEX-057) and no modes.
- Deferred items and the milestones that need them are listed in SPEC-01 §12.
- `axiom-syntax` is updated (chars enabled, suffixes, raw strings, labels, keyword list).

## Sources
0152 §12; 0154 (whole); 0173 §3-16; 0243 §2-16, §48; 0109 §88-90; tasks/0323 §8-12, §97; tasks/0324
§2-27; tasks/0476 §91-97, §103-105, §140; ADR-0004 §1; ROADMAP R7, E12.1, E12.2, E13.2, E14.3, E19.5,
E21.2; CLAUDE.md change log 2026-09-30 (`char`, floats in P12).
