# ADR-0008 — Statement termination: newline or `;`, decided by the parser with one fixed rule

## Tóm tắt
Tài liệu gốc mâu thuẫn về dấu kết thúc câu lệnh: 0243 bắt buộc `;`; 0154/0155 nói `;` tuỳ chọn nhưng
"newline không có nghĩa, parser tự suy ra"; bản đóng băng v1.0 (tasks/0476 §3) nói câu lệnh kết thúc ở
cuối dòng khi không mơ hồ, `;` là tuỳ chọn. Quyết định: theo bản đóng băng, và viết thành **một quy
tắc chính xác** để mọi parser cho cùng kết quả: câu lệnh/khai báo kết thúc bằng `;`, bằng xuống dòng,
trước `}` hoặc ở cuối file. Lexer không chèn `;` và không sinh token xuống dòng — nó chỉ gắn cờ
`NL_BEFORE` lên token đứng sau dấu xuống dòng; parser chỉ xét cờ này ở hai loại vị trí: chỗ một câu
lệnh có thể kết thúc, và chỗ một biểu thức đã đầy đủ có thể được nối dài. Dòng kết thúc bằng toán tử,
`,`, `(`, `[`, `{`, `.` hay `=` thì đương nhiên nối tiếp (parser đang cần toán hạng); dòng **bắt đầu**
bằng `.` nối tiếp chuỗi gọi phương thức. Toán tử chỉ có thể là hai ngôi/hậu tố (`+`, `&&`, `==`, `=`,
`?`, `as` …) đứng đầu dòng là lỗi có hướng dẫn sửa; còn `-`, `*`, `!`, `~`, `|`, `||`, `(`, `[`, `{` ở
đầu dòng **bắt đầu một câu lệnh mới, không báo lỗi** (`a` xuống dòng `- b` là hai câu lệnh). Trong
`( )` và `[ ]` xuống dòng không có nghĩa. Biểu thức cuối khối không có `;` là giá trị của khối.
Revisit: không.

Status: **Accepted** (architect, T001). Date: 2026-10-01. Revisit: no.

## Context

| Source | Position |
|---|---|
| 0243 §1, §6, APARSE-27 | `;` required after simple statements; "no automatic semicolon insertion" |
| 0154 §33-35, ALEX-38 | `;` optional; newline is not a token; "no ASI"; the parser finds boundaries from the grammar |
| 0155 §50, APARSE-26 | `;` optional; `foo` newline `(bar)` must not be guessed; parser "may access newline information" |
| tasks/0323 §5-6, ASYNTAX-55..57 | `;` optional; newline does not end an expression where continuation is valid |
| tasks/0324 §5-7, ALEX-29..32 | lexer keeps newline information; "automatic statement termination is parser-defined" |
| tasks/0476 §3, §107-108, ASYNTAX-22 (frozen v1.0) | newline-sensitive termination where unambiguous; `;` optional; leading-dot method chains allowed; termination "shall be deterministic" |
| `axiom-syntax` Rule 3 (binding) | newline ends a statement; trailing operator / `,` / opener / `.` / `=` continues; a leading `.` continues |

A purely grammar-driven rule ("ignore newlines, let the grammar decide", 0154) is not deterministic for
Axiom: `a` newline `(b)`, `a` newline `[1]`, `a` newline `-b`, `return` newline `x` each have two valid
parses. The later documents all move to newline-aware termination, and the frozen one requires a
deterministic rule without giving it.

## Options

A. Mandatory `;` (0243). Deterministic, but contradicts every later document, the frozen surface and
   the canonical style.
B. Lexer-level semicolon insertion (Go style: insert `;` after a line whose last token can end a
   statement). Simple, but it forbids leading-dot method chains (required by tasks/0476 §108), and
   pushes syntax knowledge into the lexer (against ALEX-32, 0154 §35).
C. **Parser-level rule with a newline flag** (Swift/Kotlin style, restricted). The lexer marks tokens
   that follow a line break; the parser consults the mark only at termination points and continuation
   points, with a fixed list of exceptions. **Chosen.**
D. Like C, but any token that cannot start a statement continues the previous line (`&&`, `==`, `+`
   at line start). Rejected: `||`, `-`, `*`, `|`, `(`, `[` can start a statement, so `&&` would
   continue while `||` would not — an irregular rule that silently changes meaning.

## Decision

1. **Lexer.** No newline token and no inserted `;`. Every token carries the flag `NL_BEFORE`: at
   least one line feed lies between the previous token and this one (including line feeds inside or
   after comments). SPEC-01 AXS-LEX-013.
2. **Terminator.** A statement, a top-level item and a member of a trait / impl / extern block end
   with `Term = ";" | NL | lookahead "}" | lookahead EOF`, where `NL` is the zero-width condition
   "the next token has `NL_BEFORE`". Two statements share a line only when separated by `;`.
   SPEC-02 AXS-GRM-011.
3. **Where the flag is consulted.** Only at (a) *termination points* (a `Term` or a list separator is
   expected) and (b) *continuation points*: after a complete operand, when the next token could
   extend the expression — a binary operator, `as`, `..`, `..=`, a postfix `(`, `[`, `?`, `.`, `->`,
   the `<` of generic arguments, the `{` of a struct literal. Everywhere else line breaks are
   ignored: before a construct the grammar requires, and before an optional part of a declaration
   that is recognised by its first token (`->`, `where`, a body `{`, `=` or `else` of a `let`) —
   none of these tokens can start a statement or an item. Consequently a line that ends with a binary
   operator, `,`, `(`, `[`, `{`, `.`, `=`, `=>`, `->` or a keyword that needs an operand continues on
   the next line, and `if c` newline `{` or a `where` clause on its own lines are valid.
   SPEC-02 AXS-GRM-012, AXS-GRM-017.
4. **Continuation at line start.** At a continuation point a token with `NL_BEFORE` does **not**
   continue the expression, with exactly two exceptions: a leading `.` (member access, method chain,
   `.await`) and the keyword `else` after the block of an `if` or after the initialiser of a
   `let … else`. SPEC-02 AXS-GRM-013, AXS-GRM-014.
5. **Leading operators are diagnosed, never reinterpreted.** A statement that begins with a token
   that can only be a binary/postfix operator (`&&`, `==`, `+`, `/`, `=`, `?`, `as`, …) reports
   `AX_PARSE_LEADING_OPERATOR` ("move the operator to the end of the previous line"). Tokens that can
   legally start a statement (`-`, `*`, `!`, `~`, `(`, `[`, `{`, `|`, `||`) start a new statement.
   SPEC-02 AXS-GRM-019.
6. **Jump labels and operands.** `break` and `continue` take a label, and `return` and `break` take
   an operand, only when it starts on the same line as the keyword (a label can begin a statement:
   `'a: loop { }`). SPEC-02 AXS-GRM-015.
7. **Inside `( )` and `[ ]`** line breaks are never significant (the flag is ignored at continuation
   points); a `{` nested inside them makes line breaks significant again for its own contents.
   SPEC-02 AXS-GRM-010.
8. **Lists in braces** (struct fields, enum variants, match arms, struct-literal fields, struct-pattern
   fields, `use` groups) separate elements with `,` or a line break; lists in `( )`, `[ ]`, `< >`
   use `,` only. SPEC-02 AXS-GRM-016.
9. **Block value.** If the last statement of a block is an expression statement not followed by an
   explicit `;`, it is the block's tail expression (its value); otherwise the block has value `()`.
   An explicit `;` after the last expression discards the value (0243 §6 kept for this one purpose).
   SPEC-02 AXS-GRM-040.
10. `;` alone is an empty statement; the formatter (E19.2) removes redundant `;`.

## Consequences

- One rule for all implementations (axiom0 in C, axiomc in Axiom, the formatter, the LSP), testable
  with the continuation matrix in SPEC-02 §3.
- "No ASI" (0154, 0243, 0155) holds in the sense those documents meant it: the lexer inserts nothing
  and no program changes meaning through an inserted token; statements are delimited by a parser rule.
- `return` newline `value` returns unit and leaves `value` as an unreachable statement — reported by
  the unreachable-code warning (T031), not silently accepted.
- `a` newline `- b` (also `*`, `!`, `~`, `|`, `||`, `(`, `[`, `{` at line start) is two statements
  with no parser diagnostic. This is the one case where a line break changes meaning silently; it is
  to be caught by an unused-value / suspicious-leading-operator lint (follow-up for T031 or E19.4),
  and the skill tells authors to end the previous line with the operator.
- T010 implements the flag (not newline tokens); T011 implements `Term`, the NL-mode stack and the
  recovery rule "sync at newline".

## Sources
0154 §33-35 (ALEX-37, ALEX-38); 0155 §50 (APARSE-26); 0243 §1, §5-6 (APARSE-27, APARSE-28); tasks/0323
§5-6 (ASYNTAX-55..58); tasks/0324 §4-7 (ALEX-27..32); tasks/0476 §3-4, §107-108 (ASYNTAX-22, ASYNTAX-23);
`.claude/skills/axiom-syntax/SKILL.md` Rule 3.
