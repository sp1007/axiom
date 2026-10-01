# SPEC-01 — Axiom v0.1 lexical specification

## Tóm tắt
Tài liệu này là chuẩn duy nhất cho **lexer** của Axiom v0.1 (axiom0 viết bằng C và axiomc viết bằng
Axiom phải cho cùng dãy token). Nội dung chính:
- File nguồn là UTF-8; chuỗi, ký tự và chú thích dùng được tiếng Việt đầy đủ; **tên (định danh) tạm
  thời chỉ dùng ASCII** (ADR-0009, có đánh dấu xem lại).
- Lexer không sinh token xuống dòng và không tự chèn `;`. Mỗi token mang cờ `NL_BEFORE` ("trước nó
  có xuống dòng"); parser dùng cờ này để kết thúc câu lệnh (ADR-0008).
- 37 từ khoá cố định, 3 từ giữ chỗ (`move`, `union`, `yield`). `var`, `import`, `mod` **không** phải
  từ khoá — parser báo lỗi kèm gợi ý sửa.
- `::` và `:=` **không phải token của Axiom**: lexer nhận ra chúng chỉ để báo lỗi kèm fix-it (`.` và
  `=`) rồi đi tiếp (quyết định của chủ dự án, ADR-0007).
- Số: `42`, `1_000`, `0xff`, `0b1010`, `0o17`, hậu tố kiểu `42u32`; số thực `1.0`, `1e10`, `2.5f32`
  (phải có chữ số hai bên dấu chấm, nên `1..2` là khoảng và `p.0.1` là truy cập tuple).
- Chuỗi `"…"`, chuỗi byte `b"…"`, chuỗi thô `r"…"`, ký tự `'a'`, byte `b'a'`, nhãn vòng lặp `'outer`.
  Không có nội suy chuỗi.
- Mỗi quy tắc có mã `AXS-LEX-NNN` để test và code tham chiếu; mỗi lỗi có mã `AX_LEX_*` cố định.

Status: canonical (T001, 2026-10-01). Decisions: ADR-0007, ADR-0008, ADR-0009.
Consumers: T010 (lexer), T013 (fuzzing), T076+ (the lexer port). Grammar: `spec/SPEC-02-grammar.md`.

Conventions used in this document:
- Rule ids `AXS-LEX-NNN` are stable; numbers are never reused or renumbered (gaps are intentional).
- Source tags such as `[0154 §12]` name `docs/base/specs` files; `tasks/` prefixes
  `docs/base/tasks`; `ADR-NNNN` names `spec/decisions`.
- Grammar notation is ISO EBNF: `=` defines, `,` concatenates, `|` alternates, `[ ]` optional,
  `{ }` repetition, `"…"` terminal, `? … ?` a character class described in prose, `-` exception,
  `(* … *)` comment, `;` ends a rule.
- Invalid spellings are shown as inline code or in `text` blocks, never in `axiom` blocks. Every
  `axiom` block in this document is valid Axiom.

---

## 1. Lexer boundary

**AXS-LEX-001 — Encoding.** A source file is a sequence of bytes that must be valid UTF-8 (no
overlong forms, no surrogates, nothing above U+10FFFF). There is no fallback encoding. An invalid
sequence reports `AX_LEX_INVALID_UTF8` on the maximal run of bytes that cannot start or continue a
valid sequence; the run produces one `Error` token and lexing continues after it.
[0154 §2, 0243 §2, tasks/0324 §2]

**AXS-LEX-002 — Byte order mark.** A UTF-8 BOM (bytes EF BB BF) at offset 0 is skipped; it is not
a token and not trivia. U+FEFF anywhere else is an invalid character (AXS-LEX-085). [0243 §2]

**AXS-LEX-003 — Spans.** A token's span is the half-open byte range `[start, end)` in the original
file (the BOM counts in offsets). Spans never use character or column indices. [0154 §3, 0243 §42]

**AXS-LEX-004 — No semantics.** The lexer maps bytes to tokens. It does not resolve names, does not
know types, does not distinguish generic brackets from comparison operators and has no modes. Its
only context dependency is AXS-LEX-057 (the previous token). Output depends only on the input bytes
(deterministic, no host addresses, no hash-order effects) and is produced in time linear in the input
length. [0154 §1, §59; 0173 §1, §22; 0243 §44-45]

**AXS-LEX-005 — Totality.** For every byte sequence the lexer terminates, never crashes, and returns
a token sequence ending with exactly one `Eof` token whose span is empty at the end of the file.
Every byte of the input belongs to exactly one of: a token, a comment, whitespace, the BOM.
[0154 §55-56, 0173 §25]

## 2. Whitespace, lines, comments

**AXS-LEX-010 — Whitespace.** Whitespace is exactly U+0020 (space), U+0009 (tab), U+000D (CR) and
U+000A (LF). Any other Unicode space or control character outside comments and literals is an
invalid character (AXS-LEX-085). Whitespace separates tokens and has no other meaning.
[0154 §32; ADR-0009 §8]

**AXS-LEX-011 — Line terminator.** LF is the only line terminator. CR is ordinary whitespace, so
CRLF files behave like LF files. Line and column numbers shown to users are computed by the source
database from LF positions; they are not part of tokens. [0243 §5; ADR-0009 §8]

**AXS-LEX-012 — No indentation sensitivity.** Indentation and the amount of whitespace never change
the token sequence. [tasks/0324 §4, tasks/0323 §7]

**AXS-LEX-013 — Newline flag.** The lexer emits no newline token and never inserts `;`. Each token
(including `Eof`) carries the boolean flag `NL_BEFORE`: true iff at least one LF occurs between the
end of the previous token and the start of this token — in whitespace, as the end of a line comment,
or inside a block comment — or the token is the first token of the file. The parser uses the flag
as specified in SPEC-02 §3. [ADR-0008 §1; tasks/0324 §5, ALEX-29; 0155 §50]

**AXS-LEX-014 — Trivia.** Comments are not tokens. The lexer records each comment in a side list
(`kind`, `span`) with kinds `LineComment`, `DocComment`, `BlockComment`, in source order, for tooling
(formatter, documentation). Whitespace is not recorded (it is the gaps between spans).
[tasks/0476 §99, ASYNTAX-57]

**AXS-LEX-020 — Line comment.** `//` starts a comment that extends to, and does not include, the
next LF or the end of file. [0154 §29]

**AXS-LEX-021 — Documentation comment.** A line comment that starts with exactly three slashes
(`///` not followed by a fourth `/`) has kind `DocComment`. It is trivia like any comment: it may
appear anywhere and the grammar does not see it. `/** … */` and `//!` are ordinary comments in v0.1.
[tasks/0476 §97; ADR-0009 §8]

**AXS-LEX-022 — Block comment.** `/*` starts a block comment that ends at the matching `*/`. Block
comments nest: every `/*` inside increases the depth, every `*/` decreases it. Quotes inside a
comment have no meaning. [0154 §30, 0173 §6, 0243 §4, tasks/0324 §8]

**AXS-LEX-023 — Unterminated block comment.** If the file ends at depth > 0, the lexer reports
`AX_LEX_UNTERMINATED_COMMENT` with the span of the outermost unclosed `/*` to the end of the file;
the comment extends to the end of the file and `Eof` follows. [0154 §31]

```axiom
// a line comment
/// documentation for the item below
/* a block comment /* nested */ still inside the outer comment */
fn main() {}
```

## 3. Identifiers and keywords

```ebnf
ident_start    = ? one of the ASCII letters A-Z a-z ? | "_" ;
ident_continue = ident_start | dec_digit ;
dec_digit      = ? one of 0 1 2 3 4 5 6 7 8 9 ? ;
word           = ident_start , { ident_continue } ;
```

**AXS-LEX-030 — Identifier.** A `word` is scanned by maximal munch. If it is a keyword
(AXS-LEX-040, AXS-LEX-041) the token is that keyword; if it is exactly `_` the token is `Underscore`
(AXS-LEX-032); if it is `b` immediately followed by `"` or `'`, or `r` immediately followed by `"`,
it starts a prefixed literal (AXS-LEX-063, AXS-LEX-064, AXS-LEX-066); otherwise the token is `Ident`
(`r'x'` is the identifier `r` followed by a character literal; `br"…"` is the identifier `br`
followed by a string). Identifiers are
case-sensitive, have no length limit and are never normalised. [tasks/0476 §103; ADR-0009 §1]

**AXS-LEX-031 — Non-ASCII outside literals.** A character ≥ U+0080 outside comments and
string/char literals reports `AX_LEX_NON_ASCII_IDENT` ("identifiers are ASCII in Axiom v0.1"). The
maximal run of characters ≥ U+0080 and `ident_continue` characters starting there forms one `Error`
token. If the run directly follows an identifier or keyword with no whitespace between (as in a word
that begins with ASCII letters), the `Error` token starts at the first non-ASCII character.
[ADR-0009 §1, Revisit: yes]

**AXS-LEX-032 — Underscore.** A lone `_` is the token `Underscore`, not an identifier. `_x`, `x_`,
`__` are identifiers. [ADR-0009 §3]

**AXS-LEX-040 — Keywords.** The following 37 words are reserved; they are never identifiers:

```text
as        async     await     break     comptime  const     continue  dyn
else      enum      extern    false     fn        for       if        impl
in        let       loop      match     module    mut       mut_view  pub
return    self      Self      static    struct    trait     true      type
unsafe    use       view      where     while
```

Each keyword has its own token kind (§9). `true` and `false` are keyword tokens that the grammar
uses as literals. [tasks/0476 §104; 0243 §8; ADR-0009 §2]

**AXS-LEX-041 — Words reserved for future use.** `move`, `union`, `yield` are keyword tokens that
no v0.1 production uses; the parser reports `AX_PARSE_RESERVED_KEYWORD` where they appear.
[ADR-0009 §2; ROADMAP E11.1, E13.2, E14.3]

**AXS-LEX-042 — Words that are not keywords.** These are ordinary identifiers for the lexer:
`var`, `import`, `mod` (the parser diagnoses their old uses — SPEC-02 AXS-GRM-038, AXS-GRM-045);
all primitive type names (`bool`, `char`, `i8` … `u64`, `isize`, `usize`, `f32`, `f64`, `never`,
`Str`); prelude names (`Option`, `Some`, `print`, `drop`, `len`, `panic`, …); attribute names;
`package` (contextual in `pub(package)`); `null`. [0243 §9; 0154 §11; ADR-0007; ADR-0009 §2]

**AXS-LEX-043 — Keyword recognition is purely lexical.** A word is a keyword in every position,
including after `.` (`x.type` is not a field access; `.await` is the only keyword the grammar accepts
after a dot). [0154 §9, 0173 §8]

## 4. Integer and float literals

```ebnf
int_literal   = ( dec_digits | "0x" , hex_digits | "0o" , oct_digits | "0b" , bin_digits ) , [ suffix ] ;
float_literal = dec_digits , ( "." , dec_digits , [ exponent ] | exponent ) , [ suffix ] ;
exponent      = ( "e" | "E" ) , [ "+" | "-" ] , dec_digits ;
dec_digits    = dec_digit , { [ "_" ] , dec_digit } ;
hex_digits    = hex_digit , { [ "_" ] , hex_digit } ;
oct_digits    = oct_digit , { [ "_" ] , oct_digit } ;
bin_digits    = bin_digit , { [ "_" ] , bin_digit } ;
hex_digit     = dec_digit | ? one of a b c d e f A B C D E F ? ;
oct_digit     = ? one of 0 1 2 3 4 5 6 7 ? ;
bin_digit     = "0" | "1" ;
suffix        = word ;   (* must be one of the type suffixes of AXS-LEX-052 *)
```

**AXS-LEX-050 — Integer literal.** Decimal, hexadecimal (`0x`), octal (`0o`) and binary (`0b`)
forms. A leading-zero decimal such as `0123` is decimal 123; there is no C-style octal. Token kind
`Int`. There are no negative literals: `-1` is the unary operator applied to `1` (the type checker
folds a negated literal before its range check, SPEC-03). [0154 §12-15, tasks/0324 §13, 0243 §13]

**AXS-LEX-051 — Digit separators.** A single `_` may appear between two digits of the same digit
sequence. A maximal run of underscores inside, directly before (after a base prefix) or directly
after a digit sequence that is not exactly one underscore between two digits (`1__0`, `1_`, `0x_ff`,
`1_u32`) is a *bad run*: it is skipped and scanning of the literal continues. The first bad run of a
literal reports `AX_LEX_BAD_DIGIT_SEPARATOR` on that run; later bad runs in the same literal report
nothing, and no bad run is reported in a literal that reports `AX_LEX_MISSING_DIGITS` (AXS-LEX-053).
[0154 §16; ADR-0009 §4]

**AXS-LEX-052 — Suffixes.** A literal may be followed, with nothing in between, by a type suffix:
`i8 i16 i32 i64 isize u8 u16 u32 u64 usize` on `Int`; `f32 f64` on `Float`. The suffix is part of
the token. [0243 §13, tasks/0476 §91, 0152 §12; ADR-0009 §4]

**AXS-LEX-053 — Malformed integers.**
- A base prefix whose digit run contains no digit at all (`0x`, `0b`, `0o`, and also `0x_`,
  `0b__`) reports `AX_LEX_MISSING_DIGITS` on the whole literal and nothing else for its digits; the
  token is `Int` with value 0. (`0x_ff` has digits: it reports only `AX_LEX_BAD_DIGIT_SEPARATOR` and
  has value 255.) [0154 §16]
- An upper-case prefix (`0X`, `0O`, `0B`) reports `AX_LEX_BAD_BASE_PREFIX` with a fix-it to lower
  case and is then scanned as the lower-case prefix.
- In a binary or octal literal the digit run is the maximal run of decimal digits and separators; a
  digit that is not valid for the base reports `AX_LEX_INVALID_DIGIT` once per literal, at the first
  such digit.

**AXS-LEX-054 — Value.** The lexer computes the value of every `Int` (separators ignored). In v0.1
the value must be ≤ 2^64 − 1; otherwise `AX_LEX_INT_OVERFLOW` and the stored value is 0. Whether the
value fits the literal's type is decided by the type checker, not the lexer. [0154 §57; T010]

**AXS-LEX-055 — Float literal.** A decimal digit sequence followed by a fraction (`.` and at least
one digit), an exponent, or both. Token kind `Float`. The token keeps its spelling; conversion to a
binary value belongs to E12.2. axiom0 lexes and parses floats and rejects them in type checking
(T034). There are no hexadecimal floats. [0154 §17, tasks/0324 §16; ADR-0009 §4]

**AXS-LEX-056 — `.` after digits.** After a decimal digit sequence, a `.` belongs to the number
only if the character after the `.` is a decimal digit. Therefore:

| Input | Tokens |
|---|---|
| `1.5` | `Float` |
| `1..2` | `Int` `DotDot` `Int` |
| `1..=2` | `Int` `DotDotEq` `Int` |
| `1.max(2)` | `Int` `Dot` `Ident` `LParen` `Int` `RParen` |
| `1.` then end of line | `Int` `Dot` |
| `.5` | `Dot` `Int` (AXS-LEX-057) |

An exponent is recognised only if `e`/`E` is followed by a digit, or by a sign and a digit; otherwise
the letters are a suffix (and an invalid one). [0154 §17-18, §54; 0173 §12-13; `axiom-syntax` Rule 3]

**AXS-LEX-057 — Tuple-index mode.** If the previous token (ignoring whitespace and comments) is
`Dot` and the next character is a decimal digit, the token is an `Int` consisting of the maximal run
of decimal digits only: no base prefix, separator, fraction, exponent or suffix is recognised.
`p.0.1` is `Ident` `Dot` `Int` `Dot` `Int`. [0155 §29; `axiom-syntax` Rule 3]

**AXS-LEX-058 — Trailing word.** If a numeric literal (outside tuple-index mode) is directly
followed by an ASCII letter, the maximal `ident_continue` run is taken as the suffix. If it is not a
suffix allowed for that literal kind, the lexer reports `AX_LEX_INVALID_SUFFIX` on the run and the
whole text is one literal token with the `ERROR` flag (`2foo`, `1f32`, `1.5u8`, `0x1G`). `1f32` gets
the note "write `1.0f32`". [ADR-0009 §4]

```axiom
const A: u32 = 1_000_000
const B: u8 = 0xff
const C: u64 = 0b1010_0011u64
const D: i32 = 0o17
const E: f64 = 6.02e23
const F: f32 = 2.5f32
```

## 5. String, character and byte literals

```ebnf
string_literal      = '"' , { string_char | escape } , '"' ;
raw_string_literal  = "r" , '"' , { ? any character except '"', CR and LF ? } , '"' ;
byte_string_literal = "b" , '"' , { byte_char | byte_escape } , '"' ;
char_literal        = "'" , ( char_char | escape ) , "'" ;
byte_literal        = "b" , "'" , ( byte_quote_char | byte_escape ) , "'" ;
label               = "'" , word ;   (* only when the word is not followed by "'" *)

string_char     = ? any character except '"', "\", CR and LF ? ;
char_char       = ? any character except "'", "\", CR and LF ? ;
byte_char       = ? any ASCII character except '"', "\", CR and LF ? ;
byte_quote_char = ? any ASCII character except "'", "\", CR and LF ? ;
escape          = simple_escape | "\x" , oct_digit , hex_digit | "\u{" , hex_digit , { hex_digit } , "}" ;
byte_escape     = simple_escape | "\x" , hex_digit , hex_digit ;
simple_escape   = "\n" | "\r" | "\t" | "\\" | "\0" | '\"' | "\'" ;
```

**AXS-LEX-060 — String literal.** `"…"` on one line. The decoded value is a sequence of bytes that
is valid UTF-8; its type is `Str` (SPEC-03). Token kind `Str`. A string literal cannot contain a raw
line break. [0154 §22, tasks/0476 §94]

**AXS-LEX-061 — Escapes.** `\n` (U+000A), `\r` (U+000D), `\t` (U+0009), `\\`, `\"`, `\'`, `\0`
(U+0000), `\xNN` (exactly two hex digits) and `\u{H…}`. In `Str` and `Char` literals `\xNN` must be
≤ `\x7F`; in byte strings and byte literals it may be `\x00`–`\xFF`. A `\` directly followed by CR,
LF or the end of file is not an escape and reports nothing by itself: the literal is unterminated
(AXS-LEX-067, AXS-LEX-068) and the `\` is the last character of its span. Any other character after `\`,
a `\x` without two hex digits, or an out-of-range `\x` reports `AX_LEX_INVALID_ESCAPE` on the escape
(the backslash, the following character and, for `\x`, up to two hex digits); the escape contributes
nothing to the value and scanning of the literal continues. [0154 §24, 0243 §15, tasks/0476 §96]

**AXS-LEX-062 — Unicode escape.** `\u{H…}` has 1 to 6 hex digits and must denote a Unicode scalar
value (≤ 10FFFF, not D800–DFFF). It is valid in `Str` and `Char` literals only. A violation (no `{`,
no digit, more than 6 digits, a non-hex character, no `}`, a surrogate, a value above 10FFFF, or use
in a byte literal) reports `AX_LEX_INVALID_UNICODE_ESCAPE`. The span is `\u`, plus — when `{`
follows — everything up to and including the first `}` that occurs before the closing quote or the
end of the line; if there is no such `}` the span is `\u{`. [0154 §24; T010]

**AXS-LEX-063 — Byte string.** `b"…"`: ASCII characters and byte escapes; value is a byte
sequence; token kind `ByteStr`. A non-ASCII character inside reports
`AX_LEX_NON_ASCII_IN_BYTE_LITERAL` on that character. [0154 §23, §25]

**AXS-LEX-064 — Raw string.** `r"…"`: no escapes are processed; the value is the text between the
quotes; it cannot contain `"` or a line break. Token kind `Str` (flag `RAW`). [tasks/0476 §94;
ADR-0009 §6]

**AXS-LEX-065 — Character literal.** `'c'` holds exactly one character or one escape and denotes
one Unicode scalar value of type `char`. Token kind `Char`. Zero (`''`) or more than one element
(`'ab'`) reports `AX_LEX_BAD_CHAR_LITERAL` on the whole literal. [tasks/0324 §17, tasks/0476 §93;
ADR-0009 §5; owner decision 2026-09-30]

**AXS-LEX-066 — Byte literal.** `b'c'` holds one ASCII character or one byte escape. It is an
integer literal: token kind `Int`, value = the byte, suffix `u8`, flag `BYTE_FORM`. It is scanned
like case 2 of AXS-LEX-067 (never as a label): zero or several elements report
`AX_LEX_BAD_CHAR_LITERAL`, a missing closing quote `AX_LEX_UNTERMINATED_CHAR`, a non-ASCII character
`AX_LEX_NON_ASCII_IN_BYTE_LITERAL`. [tasks/0324 §18; ADR-0009 §5]

**AXS-LEX-067 — `'`: character or label.** After a `'`:
1. If the next character is `ident_start`, scan the maximal `word` W. If the character after W is
   `'`, the token is a character literal (valid when W is one character, otherwise
   `AX_LEX_BAD_CHAR_LITERAL`). Otherwise the token is `Label` with spelling `'W`; W may be any word,
   including a keyword spelling.
2. Otherwise scan literal elements up to the next `'`, CR, LF or end of file. If a `'` is found the
   token is a character literal (AXS-LEX-065). If not, `AX_LEX_UNTERMINATED_CHAR` and the `Error`
   token ends before the CR/LF or at the end of file.

`'a'` is a `Char`; `'outer` in `'outer: loop` is a `Label`; `'ế'` and `'\n'` follow case 2.
[tasks/0323 §97; ADR-0009 §5]

**AXS-LEX-068 — Unterminated string.** If a CR, LF or the end of file is reached before the closing
quote of a string, raw string or byte string, the lexer reports `AX_LEX_UNTERMINATED_STRING` (span:
opening quote, including the prefix, to the last character before the line break); the token gets
the `ERROR` flag, its value is the content scanned so far, and lexing resumes at the line break.
[0173 §20]

**AXS-LEX-069 — No interpolation.** `{` and `}` are ordinary characters in every string literal.
[ADR-0009 §9, Revisit: yes]

```axiom
const GREETING: Str = "Xin chào thế giới\n"
const E_ACUTE: Str = "\u{1EBF}"
const PATH: Str = r"C:\temp\file.txt"
const MAGIC: [4]u8 = [0x7f, b'E', b'L', b'F']
const BYTES: view<[u8]> = b"\x00\xff"
const QUOTE: char = '\''
const LETTER: char = 'ế'
```

## 6. Punctuation and operators

**AXS-LEX-080 — Token set.** These and only these punctuation and operator tokens exist:

```text
(  )  [  ]  {  }  ,  ;  :  .  ..  ..=  @  ?  ->  =>
+  -  *  /  %  &  |  ^  ~  !  <<  >>  &&  ||
==  !=  <  <=  >  >=
=  +=  -=  *=  /=  %=  &=  |=  ^=  <<=  >>=
```

[tasks/0476 §82; 0243 §10-11; tasks/0324 §25-27; ADR-0009 §7]

**AXS-LEX-081 — Maximal munch.** At each position the longest token of AXS-LEX-080 that matches
is produced (`<<=` before `<<` before `<`; `..=` before `..` before `.`), except where AXS-LEX-020,
AXS-LEX-022 (comments), AXS-LEX-082, AXS-LEX-083 or AXS-LEX-084 apply first. `===` is `==` `=`;
`a--b` is `a` `-` `-` `b`. [0154 §53]

**AXS-LEX-082 — `::` is not a token.** The character pair reports `AX_LEX_COLON_COLON` ("`::` is
not Axiom syntax; paths use `.`") with a fix-it replacing the pair by `.`, and the lexer produces one
`Dot` token (flag `ERROR`) covering both characters, so parsing continues as if `.` had been written.
[REQ-OWNER-002; ADR-0007 §2]

**AXS-LEX-083 — `:=` is not a token.** The character pair reports `AX_LEX_COLON_EQ` ("`:=` is not
Axiom syntax; write `let x = …` for a new binding or `x = …` to assign") with a fix-it replacing the
pair by `=`, and the lexer produces one `Eq` token (flag `ERROR`) covering both characters.
[REQ-OWNER-001; ADR-0007 §1]

**AXS-LEX-084 — Runs of dots.** Three or more consecutive `.` characters report
`AX_LEX_INVALID_OPERATOR` and form one `Error` token. [0154 §47]

**AXS-LEX-085 — Invalid character.** Any character that cannot start a token — `#`, `$`, a
backtick, a bare `\`, a control character, a non-whitespace Unicode space, U+FEFF — reports
`AX_LEX_INVALID_CHAR` and forms a one-character `Error` token. For `#` the diagnostic adds the note
"attributes are written `@name`". (Characters ≥ U+0080 that are not Unicode spaces or U+FEFF fall
under AXS-LEX-031.) [0154 §48]

**AXS-LEX-086 — No context splitting.** The lexer always produces `>>`, `>=` and `>>=` as single
tokens; splitting them when they close generic arguments is the parser's job (SPEC-02 AXS-GRM-057).
[0173 §32, tasks/0324 §44, ALEX-62]

Not tokens, by decision: `+%  -%  *%  +|  -|  *|` (wrapping and saturating arithmetic are
intrinsics/methods, ADR-0004 §1), `++`, `--`, `**`, `?.`, `??`, `|>`, `<-`, `#[`. Their characters
lex as the shorter tokens above and the parser rejects the sequence. [tasks/0476 §109-111; ADR-0009 §7]

## 7. Token model

**AXS-LEX-090 — Token.** A token is `(kind, span, flags)` plus a decoded payload for literals.
Flags: `NL_BEFORE` (AXS-LEX-013), `ERROR` (a diagnostic was reported inside this token), `RAW`
(AXS-LEX-064), `BYTE_FORM` (AXS-LEX-066). A token never owns a copy of its text; the spelling is
`source[span]`. [0154 §50, 0173 §2]

**AXS-LEX-091 — Payload.** `Int`: value (u64) and suffix (none or one of AXS-LEX-052). `Float`:
suffix; the digits are read from the span. `Str`, `ByteStr`: decoded bytes. `Char`: scalar value.
`Ident`, `Label`: interned name (for `Label`, without the quote). [T010]

**AXS-LEX-092 — Kind names.** The canonical kind names, used by `inspect --emit=tokens` and by
golden tests:

```text
Ident  Int  Float  Str  ByteStr  Char  Label  Underscore  Error  Eof

KwAs  KwAsync  KwAwait  KwBreak  KwComptime  KwConst  KwContinue  KwDyn  KwElse  KwEnum
KwExtern  KwFalse  KwFn  KwFor  KwIf  KwImpl  KwIn  KwLet  KwLoop  KwMatch  KwModule  KwMut
KwMutView  KwPub  KwReturn  KwSelfValue  KwSelfType  KwStatic  KwStruct  KwTrait  KwTrue
KwType  KwUnsafe  KwUse  KwView  KwWhere  KwWhile
KwMove  KwUnion  KwYield

LParen  RParen  LBracket  RBracket  LBrace  RBrace  Comma  Semi  Colon  Dot  DotDot  DotDotEq
At  Question  Arrow  FatArrow
Plus  Minus  Star  Slash  Percent  Amp  Pipe  Caret  Tilde  Bang  Shl  Shr  AmpAmp  PipePipe
EqEq  BangEq  Lt  LtEq  Gt  GtEq
Eq  PlusEq  MinusEq  StarEq  SlashEq  PercentEq  AmpEq  PipeEq  CaretEq  ShlEq  ShrEq
```

`KwSelfValue` is `self`, `KwSelfType` is `Self`. The textual dump format itself is defined by T010
(`tests/lex/README.md`).

## 8. Scanning order

**AXS-LEX-095 — Dispatch.** At a token start (after skipping whitespace and comments) the first
matching case applies:

1. End of input → `Eof`.
2. A byte that is not valid UTF-8 → AXS-LEX-001.
3. `ident_start` → AXS-LEX-030 (word, keyword, `Underscore`, or `b"`, `b'`, `r"` literal).
4. A decimal digit → tuple-index mode if the previous token is `Dot` (AXS-LEX-057), else a number
   (§4).
5. `"` → string (AXS-LEX-060). `'` → AXS-LEX-067.
6. `::` → AXS-LEX-082. `:=` → AXS-LEX-083. Three or more dots → AXS-LEX-084.
7. The longest punctuation/operator token (AXS-LEX-081).
8. A character ≥ U+0080 → AXS-LEX-031, except Unicode spaces and U+FEFF → AXS-LEX-085.
9. Anything else → AXS-LEX-085.

Comments are recognised before case 7: `//` and `/*` are never the `Slash` token.

## 9. Diagnostics

**AXS-LEX-100 — Codes.** The lexer reports exactly these codes (area `LEX`; registry file
`bootstrap/axiom0/src/diag/codes/LEX.def`, taxonomy in `spec/diagnostics.md` by T002). All are
errors. "Fix-it" means a machine-applicable replacement.

| Code | Condition | Rule | Fix-it |
|---|---|---|---|
| `AX_LEX_INVALID_UTF8` | invalid UTF-8 byte run | AXS-LEX-001 | — |
| `AX_LEX_INVALID_CHAR` | character that cannot start a token | AXS-LEX-085 | — |
| `AX_LEX_NON_ASCII_IDENT` | non-ASCII character outside literals and comments | AXS-LEX-031 | — |
| `AX_LEX_UNTERMINATED_COMMENT` | block comment open at end of file | AXS-LEX-023 | — |
| `AX_LEX_UNTERMINATED_STRING` | line break or end of file inside a string | AXS-LEX-068 | — |
| `AX_LEX_UNTERMINATED_CHAR` | `'` with no closing quote on the line | AXS-LEX-067 | — |
| `AX_LEX_BAD_CHAR_LITERAL` | empty or multi-character char/byte literal | AXS-LEX-065 | — |
| `AX_LEX_INVALID_ESCAPE` | unknown escape, bad `\x` | AXS-LEX-061 | — |
| `AX_LEX_INVALID_UNICODE_ESCAPE` | malformed or non-scalar `\u{…}` | AXS-LEX-062 | — |
| `AX_LEX_NON_ASCII_IN_BYTE_LITERAL` | non-ASCII character in `b"…"` or `b'…'` | AXS-LEX-063 | — |
| `AX_LEX_MISSING_DIGITS` | base prefix without digits | AXS-LEX-053 | — |
| `AX_LEX_BAD_BASE_PREFIX` | `0X`, `0O`, `0B` | AXS-LEX-053 | lower-case prefix |
| `AX_LEX_INVALID_DIGIT` | digit not valid for the base | AXS-LEX-053 | — |
| `AX_LEX_BAD_DIGIT_SEPARATOR` | misplaced `_` in a number | AXS-LEX-051 | remove the run |
| `AX_LEX_INVALID_SUFFIX` | unknown or mismatched literal suffix | AXS-LEX-058 | — |
| `AX_LEX_INT_OVERFLOW` | integer literal above 2^64 − 1 | AXS-LEX-054 | — |
| `AX_LEX_INVALID_OPERATOR` | three or more dots | AXS-LEX-084 | — |
| `AX_LEX_COLON_COLON` | `::` | AXS-LEX-082 | replace by `.` |
| `AX_LEX_COLON_EQ` | `:=` | AXS-LEX-083 | replace by `=` |

**AXS-LEX-101 — Recovery and diagnostic count.** The lexer always advances by at least one byte,
and the token that contains an error carries the `ERROR` flag (or has kind `Error`). The number of
diagnostics is exact:
- a numeric literal reports each code at most once, at the first place it applies
  (`AX_LEX_BAD_BASE_PREFIX`, `AX_LEX_MISSING_DIGITS`, `AX_LEX_INVALID_DIGIT`,
  `AX_LEX_BAD_DIGIT_SEPARATOR`, `AX_LEX_INVALID_SUFFIX`, `AX_LEX_INT_OVERFLOW`); different codes may
  be reported for the same literal (`0b12_` reports `AX_LEX_INVALID_DIGIT` and
  `AX_LEX_BAD_DIGIT_SEPARATOR`), except that `AX_LEX_MISSING_DIGITS` suppresses
  `AX_LEX_BAD_DIGIT_SEPARATOR` (AXS-LEX-053) and a literal with any other error is not checked for
  `AX_LEX_INT_OVERFLOW`;
- a string, byte-string, character or byte literal reports one diagnostic per erroneous escape and
  per non-ASCII character in a byte literal, plus at most one of `AX_LEX_UNTERMINATED_STRING`,
  `AX_LEX_UNTERMINATED_CHAR`, `AX_LEX_BAD_CHAR_LITERAL`;
- every other error (invalid UTF-8 run, invalid character, non-ASCII run, dot run, `::`, `:=`,
  unterminated comment) reports exactly one diagnostic for its token.

Diagnostics are emitted in source order of the start of their spans (ties: the order of the table
in AXS-LEX-100). The parser treats an `Error` token as an unexpected token without reporting it again
(SPEC-02 AXS-GRM-100). [0154 §55-56, 0173 §20-21]

## 10. Conformance examples

These pairs are normative; T010 turns them into golden tests (`tests/lex`) and ui tests
(`tests/ui/lex`). `·` marks a token with `NL_BEFORE`.

| # | Input (one line unless noted) | Tokens |
|---|---|---|
| L01 | `let x = 1..=10` | ·`KwLet` `Ident` `Eq` `Int` `DotDotEq` `Int` `Eof` |
| L02 | `p.0.1` | ·`Ident` `Dot` `Int` `Dot` `Int` `Eof` |
| L03 | `1.5e3f32` | ·`Float`(suffix f32) `Eof` |
| L04 | `a<<=b>>c` | ·`Ident` `ShlEq` `Ident` `Shr` `Ident` `Eof` |
| L05 | `Vec<Vec<i32>>` | ·`Ident` `Lt` `Ident` `Lt` `Ident` `Shr` `Eof` |
| L06 | `'a'..='z'` | ·`Char` `DotDotEq` `Char` `Eof` |
| L07 | `'outer: loop` | ·`Label` `Colon` `KwLoop` `Eof` |
| L08 | `b'A'` | ·`Int`(65, u8, BYTE_FORM) `Eof` |
| L09 | `x` LF `.f()` | ·`Ident` ·`Dot` `Ident` `LParen` `RParen` `Eof` |
| L10 | `@at(0x4000_1000)` | ·`At` `Ident` `LParen` `Int`(0x40001000) `RParen` `Eof` |
| L11 | `a /* x */ b // y` | ·`Ident` `Ident` `Eof` (two comments in the trivia list) |
| L12 | `"Xin chào thế giới"` | ·`Str` (22 bytes, span length 24) `Eof` |
| L13 | `_ _x` | ·`Underscore` `Ident` `Eof` |
| L14 | `self.view` | ·`KwSelfValue` `Dot` `KwView` `Eof` |

Error cases (each reports exactly the listed codes, each once, in the listed order):

| # | Input | Tokens | Diagnostic |
|---|---|---|---|
| E01 | `a::b` | `Ident` `Dot`(ERROR) `Ident` | `AX_LEX_COLON_COLON` |
| E02 | `x := 1` | `Ident` `Eq`(ERROR) `Int` | `AX_LEX_COLON_EQ` |
| E03 | `0x` | `Int`(ERROR) | `AX_LEX_MISSING_DIGITS` |
| E04 | `1__000` | `Int`(ERROR, 1000) | `AX_LEX_BAD_DIGIT_SEPARATOR` |
| E05 | `2foo` | `Int`(ERROR) | `AX_LEX_INVALID_SUFFIX` |
| E06 | `'ab'` | `Char`(ERROR) | `AX_LEX_BAD_CHAR_LITERAL` |
| E07 | `''` | `Char`(ERROR) | `AX_LEX_BAD_CHAR_LITERAL` |
| E08 | `"\u{D800}"` | `Str`(ERROR) | `AX_LEX_INVALID_UNICODE_ESCAPE` |
| E09 | `"\u{110000}"` | `Str`(ERROR) | `AX_LEX_INVALID_UNICODE_ESCAPE` |
| E10 | `"abc` then LF | `Str`(ERROR) | `AX_LEX_UNTERMINATED_STRING` |
| E11 | `/* /* */` then end of file | — | `AX_LEX_UNTERMINATED_COMMENT` |
| E12 | `#[x]` | `Error` `LBracket` `Ident` `RBracket` | `AX_LEX_INVALID_CHAR` |
| E13 | `a...b` | `Ident` `Error` `Ident` | `AX_LEX_INVALID_OPERATOR` |
| E14 | `let tên = 1` | `KwLet` `Ident`(`t`) `Error`(`ên`) `Eq` `Int` | `AX_LEX_NON_ASCII_IDENT` |
| E15 | `0b102` | `Int`(ERROR) | `AX_LEX_INVALID_DIGIT` |
| E16 | `18446744073709551616` | `Int`(ERROR) | `AX_LEX_INT_OVERFLOW` |
| E17 | `0x_` | `Int`(ERROR, 0) | `AX_LEX_MISSING_DIGITS` |
| E18 | `0x_ff` | `Int`(ERROR, 255) | `AX_LEX_BAD_DIGIT_SEPARATOR` |
| E19 | `0b12_` | `Int`(ERROR) | `AX_LEX_INVALID_DIGIT`, `AX_LEX_BAD_DIGIT_SEPARATOR` |
| E20 | `1__0__0` | `Int`(ERROR, 100) | `AX_LEX_BAD_DIGIT_SEPARATOR` (first run only) |
| E21 | `"abc\` then LF | `Str`(ERROR), span includes the `\` | `AX_LEX_UNTERMINATED_STRING` |
| E22 | `"a\qb\zc"` | `Str`(ERROR) | `AX_LEX_INVALID_ESCAPE`, `AX_LEX_INVALID_ESCAPE` |
| E23 | `'\` then end of file | `Error` | `AX_LEX_UNTERMINATED_CHAR` |

## 11. Invariants

- **AXS-LEX-110** — Concatenating, in order, the BOM (if any), whitespace gaps, comment spans and
  token spans reproduces the input exactly (lossless).
- **AXS-LEX-111** — Lexing the same bytes twice gives identical tokens, payloads, trivia and
  diagnostics (determinism; checked by T013 and the determinism gate T029).
- **AXS-LEX-112** — No diagnostic is reported for a file made only of valid tokens, whitespace and
  comments; conversely an `Error` token or `ERROR` flag never appears without a diagnostic.

## 12. Deliberately deferred

| Item | Why deferred | Milestone that needs it |
|---|---|---|
| Unicode identifiers (XID + NFC-required rule) | large Unicode tables in C would be rewritten (R7) | E21.2 provides the tables; decide before spec freeze E23.2 (T091) — ADR-0009 §1 |
| String interpolation (prefixed literal) | not in the frozen surface, needs lexer modes | language-completion planning T214; decide before E23.2 |
| Multi-line strings `"""…"""`, raw strings with `#` delimiters, `br"…"` | not needed for self-hosting | T214; decide before E23.2 |
| `i128` / `u128` suffixes, integer literals above 2^64 − 1 | 128-bit integers are E12.1 | E12.1 (planning T212) |
| Float value conversion (correctly rounded) | floats are not typed in axiom0 | E12.2 (planning T212) |
| Documentation comment forms `/** */`, `//!`; attachment rules | no documentation generator yet | E19.5 (planning T219) |
| Lints for confusable or bidirectional control characters in literals and comments | tooling, not language | E19.4 (planning T219) |
| Token kinds for `move` closures, `union`, `yield` semantics | reserved words only | E11.1, E13.2, E14.3 |

## Sources
0152 §12; 0154; 0155 §29, §50; 0173; 0243 §2-16, §42-48; 0109 §88-90; tasks/0323 §8-12, §97;
tasks/0324 §1-27, §44, §100; tasks/0385 (token model); tasks/0476 §91-99, §103-111, §140;
`spec/requirements/OWNER.md`; ADR-0004 §1; ADR-0007; ADR-0008; ADR-0009; `axiom-syntax`.
