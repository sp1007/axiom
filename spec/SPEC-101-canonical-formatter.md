# SPEC-101 — Canonical Language Form, Lossless CST Trivia Model, and Deterministic Formatter Specification

- **Spec ID**: `SPEC-101`
- **Status**: `draft`
- **Owner task**: `T804` (`E19.2`)
- **Consumers**: `T805` (lossless CST trivia attachment & Wadler-Lindig `Doc` algebra engine in `compiler/fmt/cst` and `compiler/fmt/printer`), `T806` (AST-equivalence verification gate in `compiler/fmt/verify`, `axiomc fmt` CLI in `compiler/driver/fmt_cmd`, and LSP formatting handlers in `compiler/lsp/handlers`), `T807` (`E19.2` conformance suite in `tests/conformance/p19/e19_2_formatter`), `T808` (`E19.3` lint engine & machine-applicable `TextEdit` fixes), `T319` (`P19` certification gate)
- **Covers**: `REQ-TOOL-183`, `REQ-TOOL-298`
- **Depends on**: `SPEC-01` (Lexical Structure), `SPEC-02` (Surface Grammar & Newline Statement Termination), `SPEC-30` (Compiler Architecture & Query Engine), `SPEC-31` (CLI Driver & Workspace Commands), `SPEC-100` (LSP Server & IDE Query Engine)
- **Diagnostics**: `AX_LEX_*`, `AX_PARSE_*`, `AX_IO_*`, `AX_DRIVER_USAGE`, `AX_DRIVER_UNKNOWN_OPTION`, `AX_ICE_INTERNAL`
- **Invariants**: `INV-FMT-001`, `INV-FMT-002`, `INV-FMT-003`

## Tóm tắt

Đặc tả `SPEC-101` định nghĩa hình thức ngôn ngữ chuẩn tắc (*canonical language form*), mô hình cây cú pháp cụ thể bảo toàn toàn vẹn (*lossless Concrete Syntax Tree — CST*) kèm cơ chế gắn kết trivia (*trivia attachment model*), đại số bố cục tất định Wadler-Lindig (*deterministic Wadler-Lindig layout algebra*), giao diện dòng lệnh `axiomc fmt`, tích hợp định dạng LSP (`textDocument/formatting`, `textDocument/rangeFormatting`), và cổng kiểm chứng tương đương AST sau định dạng cho trình biên dịch tự thân Axiom (`compiler/fmt/*`).

Các nguyên tắc thiết kế cốt lõi:
1. **Nguồn sự thật cú pháp duy nhất (*Single Frontend Authority*)**: Trình định dạng dùng chung bộ phân tích từ vựng (`compiler/lex`) và phân tích cú pháp (`compiler/syntax`) của `CompilerDB` (`SPEC-30`, `SPEC-100`). Nghiêm cấm viết bộ parser phụ dựa trên biểu thức chính quy hoặc heuristic tách rời.
2. **Bảo toàn 100% token và chú thích (*Lossless CST & Trivia Conservation*)**: Mọi byte trong tệp nguồn hợp lệ được phân hoạch đầy đủ thành chuỗi token chuẩn tắc và luồng trivia (`//`, `///`, `//!`, `/* ... */` lồng nhau, chỉ thị `#region`/`#endregion`, và khoảng trắng/dòng trống). Trình định dạng gắn kết từng phần tử trivia vào nút cú pháp theo quy tắc 5 vị trí tất định (header đầu tệp, leading trước nút, trailing cùng dòng, inline bên trong biểu thức/danh sách, và dangling ở cuối khối hoặc danh sách rỗng), đảm bảo không bao giờ làm rơi hoặc đảo thứ tự chú thích.
3. **Định dạng chuẩn tắc không cấu hình (*Zero-Configuration Canonical Policy*)**: Axiom áp dụng một phong cách chuẩn tắc duy nhất trên toàn hệ sinh thái: thụt lề 4 khoảng trắng (`0x20`), độ rộng dòng mục tiêu 100 cột Unicode scalar, ký tự xuống dòng `LF` (`\n`), cú pháp gắn kết/gán chuẩn tắc `=` và đường dẫn phân tách bằng dấu chấm `.`, tự động loại bỏ dấu `;` dư thừa nhưng bảo toàn dấu `;` có ý nghĩa ngữ nghĩa ở câu lệnh biểu thức cuối khối (`has_semi == true` biến giá trị đuôi thành `()`), và giữ nguyên toán tử nhị phân ở cuối dòng trước khi ngắt dòng để tuân thủ luật kết thúc câu lệnh bằng xuống dòng của `SPEC-02`.
4. **Cổng kiểm chứng tương đương AST và tính lũy đẳng (*AST-Equivalence Verification Gate & Idempotence*)**: Mọi kết quả định dạng đều phải vượt qua cổng kiểm chứng nội bộ `parse(fmt(src)) == parse(src)` (bỏ qua `Span` và cờ `;` dư thừa không mang ngữ nghĩa) cùng điều kiện bảo toàn số lượng/nội dung chú thích trước khi ghi xuống đĩa hoặc trả `TextEdit` cho LSP, đồng thời thỏa mãn tính lũy đẳng một bước `fmt(fmt(src)) == fmt(src)`.

---

## 1. Unified Frontend Authority & Lossless CST / Trivia Attachment Model (`compiler/fmt/cst`)

### AXS-FMT-001: Shared `CompilerDB` Frontend & Lossless Source Partition
1. **Single Lexer/Parser Authority**: The formatter (`compiler/fmt/*`) MUST consume the exact token stream (`LexResult.tokens`), comment stream (`LexResult.comments`), and parsed syntax tree (`ParseResult`) produced by `compiler/lex` and `compiler/syntax` inside `CompilerDB` (`SPEC-01`, `SPEC-02`, `SPEC-30`). Separate regex-based, line-based, or standalone third-party formatting parsers are strictly forbidden (`REQ-TOOL-183`, `REQ-TOOL-298`).
2. **Lossless Byte Partition**: Every valid UTF-8 `.ax` source buffer $S$ of byte length $N$ (`0..N`) is partitioned without gaps or overlaps into:
   - An optional leading UTF-8 BOM (`EF BB BF` at byte range `0..3`, stripped in canonical output per `SPEC-01 AXS-LEX-001`),
   - Significant lexical tokens (`Token` entries from `LexResult.tokens` up to `TOK_EOF`),
   - Non-token trivia spans covering all intervening bytes: horizontal whitespace (`0x20`, `0x09`), line terminators (`LF`, `CRLF`), blank-line runs, and comments (`LexResult.comments`).
3. **Lossless CST Decoration (`CstFile`)**: Because the compiler's core `AstModule` / `AstItem` / `AstStmt` / `AstExpr` / `AstType` arena nodes are compact semantic-syntax records (`compiler/syntax/ast.ax`), `compiler/fmt/cst` constructs a side-table CST decoration (`CstFile`) over the parsed AST and token/comment streams without mutating semantic AST nodes used by `hir_of`.

### AXS-FMT-002: Trivia Taxonomy & Lexical Preservation
`compiler/fmt/cst` classifies non-whitespace trivia items (`TriviaPiece`) extracted from `LexResult.comments` and inter-token byte ranges in strictly ascending source byte order (`Span.lo`):

| Trivia Kind | Lexical Form (`SPEC-01`) | `Comment.kind` / Source Rule | Normalization & Preservation Rule |
|---|---|---|---|
| `TriviaLineComment` | `// ...` (where third byte is not `/` or `//` is followed by `///`) | `COMMENT_LINE` (`0`) | Preserve comment body verbatim after `//`, stripping only trailing horizontal spaces (`0x20`, `0x09`) and `CR` (`0x0D`) before `LF`. Ensure a single space after `//` when the body begins with a non-space, non-`/` character (`//x` $\rightarrow$ `// x`), except for `#region` / `#endregion` directives and ASCII divider lines (`// ---`, `// ===`) which preserve their exact interior bytes. |
| `TriviaOuterDoc` | `/// ...` (triple slash, not `////`) | `COMMENT_DOC` (`1`) with prefix `///` | Preserve doc-comment Markdown payload verbatim (with `CR` normalized to `LF` and trailing horizontal whitespace trimmed). Attach strictly to the immediately following declaration or item. |
| `TriviaInnerDoc` | `//! ...` | `COMMENT_DOC` (`1`) with prefix `//!` | Preserve module/inner doc-comment payload verbatim. Attach strictly to the enclosing module header or block interior. |
| `TriviaBlockComment` | `/* ... */` (including nested `/* /* ... */ */`) | `COMMENT_BLOCK` (`2`) | Preserve exact byte sequence from opening `/*` through matching closing `*/` (with internal `CRLF` normalized to `LF` and multi-line interior indentation preserved relative to the opening column). |
| `TriviaRegionDirective` | `// #region [label]` and `// #endregion [label]` | `COMMENT_LINE` (`0`) matching `^//[ \t]*#(end)?region\b` | Treat as structural section markers: canonicalize prefix to `// #region` or `// #endregion` (plus optional trimmed label), preserve vertical placement, and prohibit import sorting or item formatting from moving declarations across a `#region` / `#endregion` boundary (`SPEC-100 AXS-LSP-054`). |
| `TriviaBlankLine` | Two or more consecutive line breaks between tokens/comments with only horizontal whitespace between them | Inter-token newline count $\ge 2$ | Collapse any run of $\ge 2$ consecutive line breaks (`\n\n...`) into at most **one** canonical blank line (`\n\n`, i.e. `blank_lines = 1`) inside blocks and between sibling items. |

### AXS-FMT-003: Deterministic Five-Slot Trivia Attachment Algorithm
Every comment or directive in `LexResult.comments` MUST be assigned to exactly one CST attachment slot in a single linear pass ($O(T + C)$ in token count $T$ and comment count $C$). No comment may be left unattached or attached to multiple slots:

1. **Slot 1 — File Header Trivia (`CstFile.header_trivia`)**:
   - Inner doc comments (`//! ...`) and leading file-banner comments (`// ...` or `/* ... */` appearing before the first `module`, `use`, attribute, or declaration token and separated from the first declaration by at least one blank line, or `//!` comments at the top of the file) attach to `CstFile.header_trivia`.
   - File header trivia is emitted at the very top of the formatted file before the `module` declaration or first item, followed by a single blank line if non-empty.
2. **Slot 2 — Same-Line Trailing Trivia (`trailing_trivia` on preceding token/node)**:
   - A `TriviaLineComment` (`// ...`, excluding `///`, `//!`, and `#region`/`#endregion`) or single-line `TriviaBlockComment` (`/* ... */`) whose `Span.lo` lies on the **exact same source line** as the immediately preceding token $t_{\text{prev}}$ (i.e. the byte slice `t_prev.span.hi .. comment.span.lo` contains zero `\n` bytes) and where no token follows a `TriviaLineComment` on that line attaches as **same-line trailing trivia** to the smallest AST/CST node ending at $t_{\text{prev}}$ (or to $t_{\text{prev}}$ itself inside comma-separated lists).
   - Same-line trailing comments are emitted via the `LineSuffix` combinator (`AXS-FMT-012`) separated from the preceding token by **two spaces** (`"  // ..."`), forcing a line break immediately after the comment.
3. **Slot 3 — Inline Interior Trivia (`inline_trivia` between adjacent tokens on the same line)**:
   - A single-line `TriviaBlockComment` (`/* ... */`) that has a token $t_{\text{prev}}$ before it on the same line **and** a token $t_{\text{next}}$ after it on the same line (e.g. `f(a /* width */, b)`) attaches as inline trivia on token $t_{\text{prev}}$ and is emitted immediately after $t_{\text{prev}}$ with a single space before $t_{\text{next}}$.
4. **Slot 4 — Leading Trivia (`leading_trivia` on following node)**:
   - Any comment (`//`, `///`, `/* ... */`, `#region`, `#endregion`) starting on a new line after $t_{\text{prev}}$ and preceding a non-closing token $t_{\text{next}}$ (where $t_{\text{next}}$ is not `}`, `)`, `]`, or `TOK_EOF`) attaches as **leading trivia** to the outermost AST/CST node whose span starts at $t_{\text{next}}$ (including any leading `@attribute` or `pub` modifier of that declaration).
   - Outer doc comments (`///`) attach strictly prior to any `@attribute` list on the target item (`///` doc block first, then `@attribute` lines, then `[pub] fn/struct/...`), normalizing any inverted attribute/doc order while preserving the internal line order of both the `///` block and the `@attribute` list.
5. **Slot 5 — Dangling / End-of-Scope Trivia (`dangling_trivia` on enclosing container)**:
   - Any comment appearing after the last child node inside a delimited container (`{ ... }`, `( ... )`, `[ ... ]`) before the closing delimiter (`}`, `)`, `]`), or inside an empty container (`{ /* empty */ }`), or after the last item of a file before `TOK_EOF`, attaches to the enclosing container's `dangling_trivia` slot.
   - Inside a non-empty block or multi-line list, `dangling_trivia` is emitted at the container's inner indentation level before the closing delimiter. Inside an empty block or empty parameter/argument list containing comments, the container breaks across lines or emits the inline block comment inside `{ ... }` so the comment is preserved verbatim.

### AXS-FMT-004: Trivia Conservation Invariant
Let $\text{Comments}(S)$ be the ordered sequence of `Comment` records produced by `compiler/lex` on source $S$, and let $\text{Comments}(S')$ be the ordered sequence produced by re-lexing formatted output $S' = \text{fmt}(S)$. The formatter MUST satisfy:
1. $|\text{Comments}(S')| = |\text{Comments}(S)|$ (zero comment loss and zero synthetic comment injection).
2. For every index $i \in [0, |\text{Comments}(S)|)$, $\text{Comments}(S')[i].\text{kind} = \text{Comments}(S)[i].\text{kind}$ and the normalized comment text of $\text{Comments}(S')[i]$ equals the normalized comment text of $\text{Comments}(S)[i]$ (exact order preservation).

---

## 2. Zero-Configuration Canonical Policy & Deterministic Wadler-Lindig Layout Algebra (`compiler/fmt/printer`)

### AXS-FMT-010: Fixed Canonical Style Parameters & `axiom.toml` `[format]` Policy
1. **Fixed Canonical Parameters (Non-Configurable)**: To eliminate style bikeshedding and guarantee identical output across CLI, LSP, CI, and AI code generators (`REQ-TOOL-183`, `REQ-TOOL-298`), the following formatting parameters are fixed constants of the Axiom language specification and CANNOT be overridden by command-line flags or `axiom.toml`:
   - **Indentation unit**: **4 ASCII spaces** (`0x20`). Hard tab characters (`\t`, `0x09`) are never emitted in indentation or inter-token spacing (tabs inside string/char literals and raw strings are preserved verbatim).
   - **Maximum target line width**: **100 columns**, measured in **Unicode scalar values** (UTF-8 codepoints) from the start of the line up to the line break. Multi-byte UTF-8 characters (such as Vietnamese characters in `"Xin chào thế giới"` or comments) count as 1 column per Unicode scalar value, never by raw UTF-8 byte length.
   - **Line endings**: **LF** (`\n`, `0x0A`) on all host operating systems (Linux, Windows, macOS). Any input `CRLF` (`\r\n`) is normalized to `LF`, and every non-empty formatted `.ax` file ends with **exactly one** trailing `LF` (`\n`). An empty file (0 tokens, 0 comments) formats to `""` (0 bytes).
   - **Maximum consecutive blank lines**: **1 blank line** (`\n\n`) anywhere in formatted output.
2. **Workspace `axiom.toml` `[format]` Section**:
   - `axiomc fmt` operates with zero configuration out of the box.
   - An optional `[format]` table in `axiom.toml` may specify only workspace file-discovery filters:
     ```toml
     [format]
     exclude = ["generated/**", "vendor/**"]
     ```
   - Any attempt to set style-altering keys in `[format]` (such as `indent_width`, `max_width`, `use_tabs`, `brace_style`, or `semicolons`) MUST be rejected with diagnostic `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`), enforcing a single canonical style across all Axiom workspaces.

### AXS-FMT-011: Wadler-Lindig `Doc` Algebra Combinators
`compiler/fmt/printer` lowers the decorated `CstFile` into an arena-allocated tree of Wadler-Lindig layout documents (`Doc`) defined by the following inductive algebra:

| `Doc` Constructor | Parameters | Semantics in `Flat` Mode | Semantics in `Break` Mode |
|---|---|---|---|
| `Doc.Nil` | — | Emits nothing (`""`). | Emits nothing (`""`). |
| `Doc.Text(slice)` | UTF-8 string slice (no `\n`, precomputed scalar width $w$) | Appends `slice` to current line; advances column by $w$. | Appends `slice` to current line; advances column by $w$. |
| `Doc.HardLine` | — | Unconditionally flushes pending `LineSuffix` docs, emits `\n`, and indents to current indentation level $i$ (forces enclosing `Group` to break). | Flushes pending `LineSuffix` docs, emits `\n`, and indents to current indentation level $i$. |
| `Doc.BlankLine` | — | Unconditionally flushes pending `LineSuffix` docs, emits `\n\n` (no trailing spaces on the empty line), and indents the second line to $i$. | Same as `Flat` mode. |
| `Doc.Line` | — | Emits a single ASCII space `" "` (advances column by 1). | Flushes pending `LineSuffix` docs, emits `\n`, and indents to $i$. |
| `Doc.SoftLine` | — | Emits `" "` if the whole enclosing `Group` fits; breaks if the current element exceeds column 100. | Emits `\n` + indent $i$ as NEEDED per item (fill-layout for long argument/element lists). |
| `Doc.SoftLineEmpty` | — | Emits nothing `""` (0 width). | Flushes pending `LineSuffix` docs, emits `\n`, and indents to $i$. |
| `Doc.Indent(n, doc)` | Indent delta $n$ (typically `4`), child `doc` | Evaluates `doc` with indentation level $i + n$ (affects only line breaks inside `doc`). | Evaluates `doc` with indentation level $i + n$. |
| `Doc.Group(doc)` | Child `doc` | Probes `fits(100 - col, [(i, Flat, doc), ...])`; if true, renders `doc` in `Flat` mode, otherwise in `Break` mode. | Renders `doc` in `Break` mode (nested `Group` nodes inside `doc` still independently probe `fits`). |
| `Doc.IfBreak(break_doc, flat_doc)` | `break_doc`, `flat_doc` | Evaluates `flat_doc` when the immediately enclosing `Group` renders in `Flat` mode. | Evaluates `break_doc` when the immediately enclosing `Group` renders in `Break` mode (e.g. emitting trailing `,` only on multi-line lists). |
| `Doc.LineSuffix(doc)` | Trailing comment `doc` | Buffers `doc` in a pending suffix queue; flushed immediately before the next line break (`HardLine`, `BlankLine`, `Line`/`SoftLineEmpty` in `Break` mode) or at `EOF`. | Same as `Flat` mode; presence of a non-empty `LineSuffix` inside a `Group` before the group's closing delimiter forces the group to break after the comment. |
| `Doc.Concat(lhs, rhs)` | `lhs`, `rhs` | Evaluates `lhs` followed by `rhs`. | Evaluates `lhs` followed by `rhs`. |

### AXS-FMT-012: Deterministic `fits()` Solver & `LineSuffix` Flushing Rules
1. **Linear Bounded Lookahead (`fits`)**:
   - The printer maintains a work stack of triples $(i, m, d)$ where $i \in \mathbb{N}$ is indentation column, $m \in \{\text{Flat}, \text{Break}\}$ is group mode, and $d$ is a `Doc` node, along with the current column $c \in \mathbb{N}$ (measured in Unicode scalar values) and a FIFO queue $Q_{\text{suffix}}$ of pending `LineSuffix` documents.
   - When evaluating `Doc.Group(d)`, the printer invokes `fits(w, stack)` with remaining budget $w = 100 - c$ and `(i, Flat, d)` pushed onto the probe stack:
     - `fits(w, _)` immediately returns `false` if $w < 0$.
     - `Doc.Text(s)` decrements $w \leftarrow w - \text{scalar\_len}(s)$.
     - `Doc.Line` in `Flat` mode decrements $w \leftarrow w - 1$.
     - `Doc.SoftLineEmpty` in `Flat` mode leaves $w$ unchanged.
     - `Doc.HardLine` or `Doc.BlankLine` encountered while probing a `Flat` group returns `false` (any group containing a hard newline or line comment MUST break), unless the newline terminates the group at top level after the probe target.
     - If the probe reaches the first actual line break or empties the probe stack with $w \ge 0$, `fits` returns `true`.
   - Because `fits` stops after at most $100$ scalar columns of lookahead, total layout complexity is strictly $O(N)$ in document size $N$ with zero backtracking exponential blowup.
2. **`LineSuffix` Flushing & Trailing Whitespace Prevention**:
   - Whenever a line break (`\n`) is about to be emitted, if $Q_{\text{suffix}}$ is non-empty, all queued `LineSuffix` documents are rendered in FIFO order on the current line before emitting `\n`.
   - If a line break is followed immediately by another line break (`BlankLine`), the intermediate empty line MUST contain **zero** spaces (never indent an empty line).
   - Before emitting `\n`, any trailing ASCII spaces (`0x20`) at the end of the current line buffer are stripped.

### AXS-FMT-013: Oversized Atomic Token Rule
If a single atomic lexical token or comment (such as a long string literal `"..."`, a long URL inside a `//` comment, or a long identifier) exceeds column 100 even after all enclosing `Group` nodes have switched to `Break` mode, the printer MUST emit that atomic token intact on its line without splitting or corrupting the token (`REQ-TOOL-183`).

---

## 3. Canonical Formatting Rules for Axiom Surface Constructs

### AXS-FMT-020: Module Header & Top-Level Item Spacing
1. **Module Declaration**:
   - When a file begins with a `module` declaration (`module a.b.c`), it is emitted at column 0 (immediately after any `CstFile.header_trivia`) in canonical dot-separated form (`module a.b.c`) with no trailing semicolon, followed by **one blank line** (`\n\n`) before the first `use` group or declaration.
2. **Top-Level Item Separation**:
   - Top-level declarations (`fn`, `struct`, `enum`, `union`, `trait`, `impl`, `extern`, `comptime`) are separated from adjacent top-level declarations by **one blank line** (`\n\n`).
   - Consecutive `const` or `type` alias declarations may remain on adjacent lines (`\n`) when they have no blank line between them in the source and no outer doc comments (`///`), or be separated by at most one blank line (`\n\n`) when the source contains one or more blank lines between them.

### AXS-FMT-021: `use` Import Path Normalization & Deterministic Sorting
1. **Canonical Dot Path Form**:
   - All `use` declarations are emitted using dot-separated paths (`use std.io`, `use std.collections.{HashMap, Vec}`, `use std.mem.*`, `use std.fs.File as FsFile`) with no trailing semicolon (`SPEC-02 AXS-GRM-030`).
   - Single-item brace groups are unwrapped to plain paths (`use std.io.{Read}` $\rightarrow$ `use std.io.Read`), except when `self` is imported (`use std.io.{self, Read}`).
2. **Import Block Grouping & Sorting**:
   - Contiguous runs of `use` items that are **not** separated by blank lines, `#region` / `#endregion` directives, or non-import declarations form an **import group**.
   - Within each import group, `use` statements that have no attached leading/trailing comments or `@cfg` attributes are sorted lexicographically by their canonical dot-path prefix (ASCII byte order of path segments, with `pub use` sorted as a separate subgroup after private `use`).
   - Inside a braced import list `use a.b.{...}`, identifiers are sorted lexicographically (`self` placed first if present, followed by identifiers in ASCII order). If the single-line `use` item fits within 100 columns, it is rendered on one line with spaces after commas (`use a.b.{Alpha, Beta, Gamma}`). If it exceeds 100 columns, the brace group breaks across lines with 4-space indentation, one item per line, and a trailing comma on the final item:
     ```axiom
     use compiler.syntax.{
         AstArena,
         AstExpr,
         AstItem,
         AstModule,
         AstStmt,
         ParseResult,
     }
     ```
   - `use` items that carry attached comments or `@cfg` attributes act as barriers within the import group so that comment-to-import associations are never scrambled.

### AXS-FMT-022: Attribute Placement (`@at`, `@repr`, `@derive`, `@cfg`, `@inline`)
1. **Item Attributes**:
   - Outer doc comments (`///`) are always emitted immediately before item attributes (`@repr(...)`, `@derive(...)`, `@cfg(...)`, `@inline`, `@cold`, `@must_use`), followed by the item signature (`pub struct ...`, `pub fn ...`).
   - Each item-level attribute is placed on its own line at the item's indentation level with no blank line between the attribute and its target declaration:
     ```axiom
     /// Packet header in network byte order.
     @repr(C)
     @derive(Clone, Eq)
     pub struct PacketHeader {
         pub magic: u32,
         pub length: u32,
     }
     ```
2. **Field and Parameter Attributes**:
   - Short layout attributes on `struct` fields (`@at(0)`, `@align(16)`) that appear on the same source line as the field and fit within 100 columns are emitted inline before the field (`@at(0) pub flags: u32,`); if preceded by a newline or `///` doc comment, they are placed on the line immediately above the field.

### AXS-FMT-023: Functions, Receivers, Generics, `where` Clauses & `extern` Blocks
1. **Signature Spacing & Receivers**:
   - Canonical spacing: `[pub] [unsafe] [comptime] [async] fn name[T: Bound](self: view<Self>, x: i32) -> i32 ! IoError {`.
   - Receiver parameters (`self`, `self: view<Self>`, `self: mut<Self>`, `self: move<Self>`, `self: *mut Self`) are always the first parameter and formatted identically to typed parameters.
   - Generic parameter lists `[T, U: Clone + Debug]` have no space before `[`, no spaces immediately inside `[` and `]`, a single space after `,`, and spaces around `+` in trait bounds (`T: Read + Write`).
   - Return types use ` -> Type` (single space before and after `->`). Error-effect clauses use ` ! ErrorType` after the return type (or after `)` when the return type is omitted `()`).
2. **Parameter List Line Breaking**:
   - If the entire signature (from `[pub] fn` through the opening `{` of the body, or end of signature in `trait`/`extern`) fits within 100 columns and contains no line comments, parameters are rendered on a single line (`fn add(a: i32, b: i32) -> i32 {`).
   - If the signature exceeds 100 columns, the parameter list breaks after `(`, indents each parameter by 4 spaces on its own line with a **trailing comma** after the last parameter, and places `)` (followed by ` -> RetType {`) at the declaration's base indentation column:
     ```axiom
     pub fn resolve_symbol_in_scope(
         db: *mut CompilerDB,
         module_id: u32,
         symbol_name: Slice<u8>,
         allow_private: bool,
     ) -> Option<SymbolId> {
         return query_symbol(db, module_id, symbol_name, allow_private)
     }
     ```
3. **`where` Clauses**:
   - When a `where` clause is present, if the entire signature including `where` fits within 100 columns, it may remain on one line; otherwise `where` starts on a new line at the function's base indentation level, with predicates indented by 4 spaces (or aligned after `where `) and separated by trailing commas, followed by `{` on the last predicate line or on its own line at column 0.
4. **Function Body Blocks**:
   - The opening brace `{` of a function, `struct`, `enum`, `union`, `trait`, `impl`, `extern`, or control-flow block is always placed on the **same line** as the header (`K&R` / Axiom canonical brace style), preceded by a single space (`) -> i32 {`).
   - Empty function or block bodies with no interior comments are rendered as `{}` with no spaces inside.
   - Single-expression functions stay multi-line if the source body is multi-line or exceeds 80 columns; short trivial bodies without comments may render on a single line only inside closure expressions (`|x| x + 1`), whereas named `fn` declarations with a block body always place statements on indented lines between `{\n` and `\n}`.

### AXS-FMT-024: `struct`, `enum`, `union`, `trait`, `impl` & `type` Declarations
1. **`struct` and `union` Definitions**:
   - Empty structs render as `pub struct Unit {}`.
   - Non-empty structs always place one field per line indented by 4 spaces, using canonical `,` as the field terminator (including a **mandatory trailing comma** on the last field). Legacy semicolon field separators (`;`) permitted by the parser for compatibility are normalized to `,`:
     ```axiom
     pub struct Span {
         pub file_id: u32,
         pub lo: u32,
         pub hi: u32,
     }
     ```
2. **`enum` Definitions**:
   - Variants are placed one per line indented by 4 spaces, terminated by a trailing comma `,`:
     - Unit variant: `None,`
     - Tuple variant: `Some(T),` (wrapping with 4-space indent + trailing comma if $> 100$ columns)
     - Struct variant: `Node { id: u32, left: *mut Expr, right: *mut Expr },` (wrapping fields like a struct when $> 100$ columns or multi-line)
     - Explicit discriminant: `Error = 1,` (single spaces around `=`).
3. **`trait` and `impl` Blocks**:
   - Header: `pub trait Iterator[Item] {` and `impl[T: Clone] Clone for Vec[T] {`.
   - Items inside `trait` and `impl` blocks are indented by 4 spaces. Required method declarations without bodies have no trailing semicolon (`fn next(self: mut<Self>) -> Option[Item]`). Method implementations with bodies are separated by one blank line (`\n\n`).

### AXS-FMT-025: Statements, Bindings, Assignments & Semicolon Canonicalization
1. **Bindings and Assignments (`SPEC-02 AXS-GRM-020..022`)**:
   - Immutable binding: `let x: i32 = 42` or `let x = 42` (single space around `=`, single space after `:`).
   - Mutable binding: `let mut count = 0`.
   - Assignment and compound assignment: `count = count + 1`, `count += 1` (single space around `=`, `+=`, `-=`, `*=`, `/=`, `%=`, `&=`, `|=`, `^=`, `<<=`, `>>=`).
2. **Semicolon Normalization & Tail-Expression Semantics (`SPEC-02 AXS-GRM-040`, `REQ-GRM-148`)**:
   - Axiom is a newline-terminated expression-oriented language where the parser (`compiler/syntax/parse.ax`) records `stmt.has_semi: bool` on `STMT_EXPR` and lowering (`compiler/hir/lower.ax`) uses `has_semi == false` on the final statement of a block to produce the block's tail value (while `has_semi == true` suppresses the tail value so the block evaluates to `()`).
   - Therefore, the formatter MUST enforce the following exact semicolon rules so that `parse(fmt(src)) == parse(src)` and `hir_of(fmt(src)) == hir_of(src)` hold unconditionally:
     - **Rule S1 (Declarations & Control Statements)**: All trailing semicolons after `let`, assignment (`x = v`), `return`, `break`, `continue`, `defer`, `while`, `for`, `loop`, and item declarations are unconditionally stripped (`let x = 10;` $\rightarrow$ `let x = 10`).
     - **Rule S2 (Non-Final `STMT_EXPR` Statements)**: Any `STMT_EXPR` that is **not** the final statement of its enclosing block (`stmt.next != null`) is placed on its own line with its trailing `;` stripped (`foo(); bar()` $\rightarrow$ `foo()\nbar()`).
     - **Rule S3 (Final `STMT_EXPR` in a Block — Semantic Tail Preservation)**:
       - If the final statement of a block (`stmt.next == null`) is `STMT_EXPR` with `stmt.has_semi == false`, it is a tail value expression and is emitted **without** a semicolon (`{ compute(x) }`).
       - If the final statement of a block (`stmt.next == null`) is `STMT_EXPR` with `stmt.has_semi == true` inside a value-capable block (or any block where `parse.ax` records `has_semi = true` on the final `STMT_EXPR`), the trailing `;` is **semantically significant** (it suppresses the tail expression and yields `()`, as specified in `SPEC-02 EX-22`) and MUST be preserved on that final statement (`{ side_effect(x); }`) so that re-parsing produces `has_semi == true`!

### AXS-FMT-026: Expressions, Operator Continuation & Method Chains
1. **Binary & Unary Operators**:
   - Binary operators (`+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `<=`, `>`, `>=`, `&&`, `||`, `&`, `|`, `^`, `<<`, `>>`) always have a single space on both sides (`a + b`, `x == 0 && y > 1`).
   - Range operators (`..`, `..=`) have **no** spaces around them (`0..n`, `0..=255`).
   - Unary prefix operators (`-`, `!`, `~`, `&`, `&mut `, `*`) have no space between the operator symbol and operand (`-x`, `!flag`, `*ptr`, `&val`, `&mut buf`), except keyword-like prefix forms (`&mut expr`, `move expr`, `copy expr`).
   - Postfix `?`, index `a[i]`, call `f(x)`, and field/method access `a.b` have no space before `?`, `[`, `(`, or `.` (on the same line).
   - Type casts use single spaces around `as` (`x as u64`).
2. **Multi-Line Binary Expression Continuation (`SPEC-02 AXS-GRM-019`)**:
   - Because `SPEC-02` terminates a statement at a newline unless the line ends with a continuation token (an infix operator or open delimiter) or the next line begins with `.` (`SPEC-02` continuation matrix `N03`, `N04`, `N14`), **when a binary expression wraps across lines, the binary operator MUST remain at the end of the preceding line**, never at the start of the continuation line!
   - Continuation lines of a broken binary expression are indented by +4 spaces relative to the enclosing statement/expression base:
     ```axiom
     let is_valid_range = span.lo <= offset &&
         offset <= span.hi &&
         span.file_id == active_file_id
     ```
   - Placing `-`, `+`, `*`, `&`, or `|` at the start of the next line (`let d = a\n    - b`) is strictly forbidden because `SPEC-02` parses `- b` as a separate unary statement on the second line.
3. **Method & Field Call Chains (`SPEC-02 AXS-GRM-013`)**:
   - Because `.` at the start of a line is a legal postfix continuation token in `SPEC-02` (`P02`), a method/field chain (`receiver.first().second().third()`) that fits within 100 columns stays on one line; when it exceeds 100 columns (or contains a multi-line closure argument), each `.segment(...)` after the receiver breaks onto its own line with **leading `.`** indented by +4 spaces:
     ```axiom
     let result = items
         .iter()
         .filter(|x| x.is_active())
         .map(|x| x.score)
         .collect()
     ```

### AXS-FMT-027: Delimited Literals (`struct`, Array, Tuple, Call Arguments)
1. **Call Arguments, Tuple Expressions & Array Literals**:
   - Empty delimiters render with no interior space: `f()`, `()`, `[]`.
   - When a `Group` for `f(a, b, c)`, `(a, b, c)`, or `[a, b, c]` fits within 100 columns in `Flat` mode, elements are separated by `", "` with **no** trailing comma (except 1-element tuples `(x,)` which always retain their mandatory disambiguating comma).
   - When the `Group` breaks (`Break` mode), it breaks immediately after the opening delimiter, indents elements by +4 spaces, places one element per line (or uses `SoftLine` fill-layout for pure numeric/literal arrays of $> 8$ elements), emits a **trailing comma** `,` after the final element via `IfBreak(Text(","), Nil)`, and places the closing delimiter at the base indentation level.
2. **Struct Literals (`Point { x: 1, y: 2 }`)**:
   - Empty struct literal: `Empty {}`.
   - Short struct literals that fit within 100 columns on a single line render with single spaces inside `{` and `}` (`Point { x: 10, y: 20 }`) and no trailing comma.
   - Multi-line struct literals break after `{`, indent each `field: value,` by +4 spaces with a trailing comma on the final field, and place `}` at the base indentation level:
     ```axiom
     let cfg = FormatConfig {
         indent_width: 4,
         max_width: 100,
         check_only: false,
     }
     ```

### AXS-FMT-028: Control Flow (`if`/`else`, `match`, `while`, `for`, `loop`), Closures & Blocks
1. **`if` / `else if` / `else` (`SPEC-02 AXS-GRM-017`)**:
   - Conditions are **never** wrapped in redundant outer parentheses (`if (x > 0) {` $\rightarrow$ `if x > 0 {`), unless the parenthesized expression is the left operand of a sub-expression (`if (a || b) && c {`).
   - `else` and `else if` are always placed on the same line as the preceding closing brace (`} else if cond {` and `} else {`), unless a comment sits between `}` and `else` (in which case the comment is emitted after `}` or on the intervening line before `else`).
   - Short value-producing `if cond { a } else { b }` expressions that are used in expression position (e.g. `let y = if flag { 1 } else { 0 }`) and fit within 100 columns with single-expression branches and no comments may render on a single line; statement-level `if` blocks always use multi-line blocks.
2. **`match` Expressions**:
   - Header: `match scrutinee {`.
   - Each arm is indented by +4 spaces: `Pattern if guard => body,`.
   - Single-line expression arms end with a comma `,` (`Option.Some(v) => v + 1,`, `Option.None => 0,`).
   - Block-body arms (`Pattern => { ... }`) place `{` after `=> `, indent statements inside by an additional 4 spaces, and close with `}` (optional comma after `}` normalized to no comma or consistent trailing comma when followed by another arm).
3. **`while`, `for`, `loop`, `defer`, `unsafe`, `comptime`**:
   - Formatted with a single space before `{`: `while i < n {`, `for item in items {`, `loop {`, `defer {`, `unsafe {`, `comptime {`.
   - Single-call `defer cleanup(x)` without braces stays `defer cleanup(x)`.
4. **Closures**:
   - Parameter pipes have no interior spaces: `|x: i32, y: i32| x + y` or `|x| { ... }`.

### AXS-FMT-029: Literal Spelling & UTF-8 Fidelity
1. **Numeric Literals**:
   - The formatter MUST preserve the exact lexical spelling of numeric literals from the source slice (`Token.span`): radix prefixes (`0x`, `0b`, `0o` normalized to lowercase prefix while preserving hex digit casing or canonicalizing per `SPEC-01`), digit separators (`1_000_000`, `0xff_00`), and type suffixes (`42u64`, `3.14f32`) are preserved verbatim without re-evaluating or base-converting the number.
2. **String, Raw String, Byte String & Character Literals**:
   - Standard strings (`"..."`), raw strings (`r"..."`, `r#"..."#`), byte strings (`b"..."`), and char literals (`'a'`) MUST be copied byte-for-byte from the source buffer (`Token.span`) without altering escape sequences, embedded newlines, or multi-byte UTF-8 sequences (such as `"Xin chào thế giới"`).

---

## 4. AST-Equivalence Verification Gate, Idempotence & Error Refusal (`compiler/fmt/verify`)

### AXS-FMT-030: Syntax-Error Refusal Gate (Zero Partial/Corrupt Formatting)
1. **Strict Pre-Format Gate**:
   - Before constructing `CstFile` or invoking the layout engine on any source buffer $S$, the formatter queries `lex_tokens(db, file_id)` and `parse_syntax(db, file_id)`.
   - If `LexResult.error_count > 0` (`AX_LEX_*`) or `ParseResult.error_count > 0` (`AX_PARSE_*`), the formatter MUST immediately refuse to format $S$:
     - In `axiomc fmt` CLI mode, it emits the standard compiler diagnostics (`SPEC-31` / `spec/diagnostics.md`), leaves the file on disk untouched, and exits with code **`1`**.
     - In LSP `textDocument/formatting` and `textDocument/rangeFormatting` modes (`SPEC-100 AXS-LSP-053`), it returns `result: null` (or an empty edit list `[]`) so the editor buffer is never corrupted while the user is mid-edit on broken syntax.
2. **Legacy Banned Syntax Handling**:
   - Any input containing banned non-canonical tokens rejected by `SPEC-01` / `SPEC-02` (such as the legacy colon-equals binding operator, the legacy `var` keyword, or the legacy double-colon path separator) triggers `AX_PARSE_*` diagnostics during `parse_syntax` (`SPEC-02 AXS-GRM-020..021`) and is therefore refused by the pre-format gate (`exit 1`) while providing the parser's structured `fix_Edits` replacement in the diagnostic payload.

### AXS-FMT-031: Post-Format AST-Equivalence & Comment-Conservation Verification Gate
Before `compiler/fmt` returns formatted text $S' = \text{fmt}(S)$ to the CLI writer or LSP response handler, `compiler/fmt/verify` MUST execute the following mandatory internal verification gate (`REQ-TOOL-183`, `REQ-TOOL-298`):
1. **Re-Lex and Re-Parse $S'$**:
   - Run `compiler/lex` and `compiler/syntax` on the formatted byte buffer $S'$.
   - Verify `LexResult(S').error_count == 0` and `ParseResult(S').error_count == 0`.
2. **Comment Conservation Check (`AXS-FMT-004`)**:
   - Verify that `LexResult(S').comment_count == LexResult(S).comment_count` and that every comment `i` has identical `Comment.kind` and identical normalized text payload.
3. **Structural AST Equivalence (`ast_equiv(AstModule(S), AstModule(S'))`)**:
   - Traverse `AstModule(S)` and `AstModule(S')` recursively and verify exact structural isomorphism modulo byte spans (`Span`), redundant parenthesization (`EXPR_PAREN` unwrapped around `if`/`while`/`match` conditions or trivial precedence-preserving groups), sorted `use` import groups (`AXS-FMT-021`), and non-semantic semicolons (`AXS-FMT-025`):
     - Every `AstItem`, `AstStmt`, `AstExpr`, `AstType`, `AstPattern`, `AstParam`, and `AstField` node kind, operator code, modifier flag (`is_pub`, `is_mut`, `is_unsafe`, `is_comptime`), identifier slice, and literal slice MUST match identically.
     - On the **final** statement of every `STMT_BLOCK` (`stmt.next == null`), if `stmt.kind == STMT_EXPR`, `stmt.has_semi` in `AstModule(S')` MUST equal `stmt.has_semi` in `AstModule(S)`.
4. **Hard Abort on Verification Failure**:
   - If any check in steps 1–3 fails, the formatter MUST abort before touching the target file on disk, emit internal compiler error diagnostic `AX_ICE_INTERNAL` (`data.stage = "fmt_verify"`), and return exit code `3` per `spec/diagnostics.md` `AXD-042` / `AXD-043` (or `null` in LSP mode). A formatter bug MUST NEVER silently corrupt user source code or drop a comment.

### AXS-FMT-032: Single-Step Idempotence Invariant
For every syntactically valid Axiom source buffer $S$, formatting is a projection onto the canonical subspace:
$$\text{fmt}(\text{fmt}(S)) = \text{fmt}(S)$$
byte-for-byte (`INV-FMT-001`, `INV-FMT-003`). Running `axiomc fmt` a second time on already-formatted code MUST produce zero bytes of diff and zero disk writes.

---

## 5. `axiomc fmt` CLI (`compiler/driver/fmt_cmd`) & LSP Formatting Integration (`compiler/lsp/handlers`)

### AXS-FMT-040: `axiomc fmt` Command-Line Interface & Exit Codes
`axiomc fmt` (and workspace alias `axiom fmt`) provides the following deterministic CLI contract (`SPEC-31`, `REQ-TOOL-183`):

| Invocation | Target Discovery & Behavior | Output | Exit Code |
|---|---|---|---|
| `axiomc fmt` (no paths) | Discovers `axiom.toml` in the current or ancestor directory and formats all `.ax` files under the workspace/package roots (`src/`, `compiler/`, `tests/`, `benches/`), excluding paths matched by `[format].exclude`. If no `axiom.toml` exists, formats all `.ax` files recursively under `.`. | Rewrites only files where $\text{fmt}(S) \neq S$ via atomic temp-file rename (`write` + `rename`); leaves already-canonical files untouched (preserving `mtime`). | `0` if all files succeeded; `1` on any lex/parse/IO error; `2` on invalid CLI flags. |
| `axiomc fmt <path>...` | Each `<path>` may be a `.ax` file or a directory (traversed recursively for `.ax` files in deterministic lexicographical path order). | Same atomic in-place rewrite only when $\text{fmt}(S) \neq S$. | `0` on success; `1` on lex/parse/IO error; `2` on invalid CLI flags. |
| `axiomc fmt --check [<path>...]` | Read-only verification mode for CI gates. Never modifies any file on disk. | Prints a deterministic unified diff (or list of non-canonical file paths when `--quiet` is passed) to `stdout` for every file where $\text{fmt}(S) \neq S$. | `0` if every file satisfies $\text{fmt}(S) == S$; `1` if one or more files require formatting or have lex/parse/IO errors; `2` on usage error. |
| `axiomc fmt --stdin` | Reads UTF-8 source from `stdin` up to `EOF`, formats in memory, and writes canonical UTF-8 (`LF`) to `stdout`. Supports `--check` with `--stdin` (exits `1` if `stdin` is not canonical). Cannot be combined with `<path>` arguments (`AX_DRIVER_USAGE`, exit `2`). | Canonical source on `stdout`; diagnostics on `stderr`. | `0` on success; `1` on lex/parse error or `--check` mismatch; `2` on usage error. |

### AXS-FMT-041: Deterministic File Discovery & Atomic In-Place Write
1. **Lexicographical Traversal Order**:
   - Directory traversal in `compiler/driver/fmt_cmd` MUST sort directory entries in deterministic UTF-8 byte order before formatting or emitting `--check` diffs, ensuring identical output across operating systems and filesystems.
   - Hidden directories starting with `.` (`.git`, `.claude`, `_workspaces`) and build artifact directories (`build/`, `target/`, `out/`) are skipped by default during recursive directory discovery unless explicitly passed as a command-line path argument.
2. **Idempotent Timestamp Preservation & Atomic Write**:
   - When `fmt(S) == S` (including the case where $S$ already has `LF` line endings and canonical bytes), `axiomc fmt` MUST NOT open the file for writing or touch its filesystem modification timestamp (`mtime`), avoiding unnecessary rebuilds in timestamp-based build tools.
   - When `fmt(S) != S` and `--check` is not set, `axiomc fmt` writes the verified buffer $S'$ to a sibling temporary file (or truncates-and-writes atomically after the `AXS-FMT-031` verification gate succeeds) in binary mode (`"wb"`, preventing Windows CRT `\n` $\rightarrow$ `\r\n` translation).

### AXS-FMT-042: LSP `textDocument/formatting` & `textDocument/rangeFormatting` Parity (`compiler/lsp/handlers`)
1. **Engine Unification (`SPEC-100 AXS-LSP-053`)**:
   - The LSP server (`compiler/lsp/handlers/mod.ax`) MUST invoke the exact same `compiler/fmt` pipeline (`cst` $\rightarrow$ `printer` $\rightarrow$ `verify`) over the latest in-memory VFS buffer in `CompilerDB`.
   - LSP `FormattingOptions` (`tabSize`, `insertSpaces`, `trimTrailingWhitespace`, `insertFinalNewline`) sent by the client are ignored in favor of Axiom's fixed canonical policy (`4` spaces, `100` columns, `LF`, final newline) so that editor format-on-save and `axiomc fmt --check` in CI are 100% identical.
2. **Minimal `TextEdit[]` Computation**:
   - For `textDocument/formatting`:
     - If $\text{fmt}(S) == S$, return `[]` (empty `TextEdit` array) so the editor preserves cursor state and undo history.
     - If $\text{fmt}(S) \neq S$, compute the minimal changed line window (or single whole-document replacement `Range` covering lines `0..line_count` with UTF-16 `Position` coordinates per `SPEC-100 AXS-LSP-012`) transforming $S$ into $\text{fmt}(S)$.
3. **Range Formatting (`textDocument/rangeFormatting`)**:
   - Given a requested UTF-16 `range`, `compiler/fmt` formats the full file $S$ into $S' = \text{fmt}(S)$ (ensuring global CST trivia attachment and `AXS-FMT-031` AST equivalence) and extracts the smallest enclosing syntactic node/line span in $S'$ corresponding to the smallest AST declaration or statement range covering `range`, returning a `TextEdit[]` restricted to that syntactic boundary.

---

## 6. Diagnostics, Canonical Examples & Verification Matrix

### AXS-FMT-050: Formatter Diagnostic & Exit-Code Mapping
`axiomc fmt` emits structured diagnostics conforming to `spec/diagnostics.md` (`AXD-001`..`AXD-021`):

| Condition | Diagnostic Code | Severity | CLI Exit Code | Notes |
|---|---|---|---|---|
| All files already canonical (`--check`) or formatted cleanly | *(none)* | — | `0` | Zero warnings/errors. |
| File differs from canonical form under `axiomc fmt --check` | *(unified diff on `stdout`)* | — | `1` | Non-destructive CI gate failure. |
| Lexical error in input (e.g. unclosed string/comment, invalid UTF-8) | `AX_LEX_*` | `error` | `1` | File untouched; LSP returns `null`. |
| Syntax error or banned legacy syntax in input | `AX_PARSE_*` | `error` | `1` | File untouched; includes `fix_Edits` for legacy tokens. |
| Unreadable file or directory / write permission failure | `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` | `error` | `1` | File untouched. |
| Invalid CLI flag (`--stdin` with file args, unknown flag) or invalid `[format]` key in `axiom.toml` | `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` | `error` | `2` | Usage error before formatting. |
| Post-format verification gate (`AXS-FMT-031`) detects AST or comment mismatch | `AX_ICE_INTERNAL` (`data.stage = "fmt_verify"`) | `error` (`ice`) | `3` | Aborts before writing file; never corrupts source. |

### AXS-FMT-051: Positive Canonical Formatting Examples (`EX-FMT-01` .. `EX-FMT-03`)

#### `EX-FMT-01`: Trivia Attachment, Import Sorting, Attributes & Tail-Semicolon Preservation
Input before `axiomc fmt`:
```axiom
//! Module header doc comment.
module   demo.formatter;


use std.io.{Write, Read, self};
use std.collections.Vec;
use std.alloc.Arena;

@derive(Clone,Eq)
/// Compute packet checksum.
@repr(C)
pub struct Packet {
    pub id: u32; // packet identifier
    pub payload: Slice<u8>,
}

pub fn process(p: view<Packet>,   limit: u32) -> u32 {
    let mut total = 0u32;
    let greeting = "Xin chào thế giới"; // UTF-8 preserved
    if (p.id > 0 && limit > 0) {
        total = p.id + limit;
    }
    /* inline comment */ log_msg(greeting);
    total
}

pub fn fire_and_forget(x: u32) {
    side_effect(x);
}
```

Canonical output after `axiomc fmt`:
```axiom
//! Module header doc comment.

module demo.formatter

use std.alloc.Arena
use std.collections.Vec
use std.io.{self, Read, Write}

/// Compute packet checksum.
@repr(C)
@derive(Clone, Eq)
pub struct Packet {
    pub id: u32,  // packet identifier
    pub payload: Slice<u8>,
}

pub fn process(p: view<Packet>, limit: u32) -> u32 {
    let mut total = 0u32
    let greeting = "Xin chào thế giới"  // UTF-8 preserved
    if p.id > 0 && limit > 0 {
        total = p.id + limit
    }
    /* inline comment */ log_msg(greeting)
    total
}

pub fn fire_and_forget(x: u32) {
    side_effect(x);
}
```
Notice that:
- `/// Compute packet checksum.` is normalized above `@repr(C)` and `@derive(Clone, Eq)`.
- Redundant `;` on `module`, `use`, `let`, assignment, and non-final `log_msg(greeting)` are stripped, while the `struct` field `;` is normalized to `,`.
- In `fire_and_forget`, `side_effect(x);` is the **final** `STMT_EXPR` of the block with `has_semi == true` (`AXS-FMT-025` Rule S3), so its trailing `;` is preserved to keep the block's tail value suppressed (`()`).

#### `EX-FMT-02`: Multi-Line Binary Continuation vs Method Chains
Canonical output demonstrating `AXS-FMT-026`:
```axiom
pub fn compute_layout_score(
    line_width: u32,
    max_columns: u32,
    overflow_penalty: u32,
    items: view<Vec<LayoutItem>>,
) -> u32 {
    let fits_within_budget = line_width <= max_columns &&
        overflow_penalty == 0 &&
        items.len() > 0

    let total_weight = items
        .iter()
        .filter(|item| item.is_visible())
        .map(|item| item.scalar_width)
        .fold(0u32, |acc, w| acc + w)

    if fits_within_budget { total_weight } else { total_weight + overflow_penalty }
}
```

#### `EX-FMT-03`: Dangling Comments in Empty Blocks & Delimited Lists
Canonical output demonstrating `AXS-FMT-003` Slot 5:
```axiom
pub fn placeholder_handler() {
    // TODO: wire up telemetry sink
}
```

### AXS-FMT-052: Negative / Forbidden Formatter Behaviors (`NEG-FMT-01` .. `NEG-FMT-03`)
1. **`NEG-FMT-01` (Forbidden Leading Binary Operator on Continuation Line)**:
   - Emitting a binary operator `-`, `+`, `*`, `/`, `%`, `&`, `|`, `&&`, or `||` at the start of a continuation line (e.g. breaking `let d = a - b` into `let d = a` followed by `- b` on the next line) is **strictly forbidden** (`AXS-FMT-026`), because `SPEC-02` terminates `let d = a` at the newline and parses `- b` as a separate unary negation statement, violating `AXS-FMT-031` (`parse(fmt(src)) == parse(src)`).
2. **`NEG-FMT-02` (Forbidden Stripping of Tail-Suppression Semicolon on Final `STMT_EXPR`)**:
   - Stripping the trailing `;` from the final `STMT_EXPR` of a block when `stmt.has_semi == true` (turning `{ side_effect(x); }` into `{ side_effect(x) }`) is **strictly forbidden** (`AXS-FMT-025` Rule S3), because it changes `stmt.has_semi` from `true` to `false` and alters the block's evaluated value in `hir_of`.
3. **`NEG-FMT-03` (Forbidden Comment Reordering Across `#region` or Statement Boundaries)**:
   - Moving a comment across a token or `#region` boundary, or sorting `use` statements across a comment or `#region` directive (`AXS-FMT-002`, `AXS-FMT-021`), is **strictly forbidden** (`AXS-FMT-004`).

### AXS-FMT-053: Invariants & Downstream Verification Matrix

| Invariant ID | Rule Summary | Implementing Task | Verification Target |
|---|---|---|---|
| `INV-FMT-001` | Lossless CST trivia attachment (`compiler/fmt/cst`) and deterministic Wadler-Lindig `Doc` printer (`compiler/fmt/printer`) preserve 100% of tokens and comments (`//`, `///`, `//!`, nested `/* */`, `#region`) in exact source order, enforce canonical 4-space / 100-column / `LF` / `=` / `.` formatting, keep binary operators trailing on line wraps, preserve semantic tail-suppression `;` on final `STMT_EXPR`, and satisfy single-step idempotence `fmt(fmt(src)) == fmt(src)`. | `T805` | `tests/run/fmt_engine` |
| `INV-FMT-002` | Post-format verification gate (`compiler/fmt/verify`) enforces `parse(fmt(src)) == parse(src)` and comment conservation before any disk write or LSP edit; `axiomc fmt` CLI (`compiler/driver/fmt_cmd`) supports workspace/directory/file formatting, `--check` (exit `0`/`1` + unified diff), and `--stdin`; LSP `textDocument/formatting` and `textDocument/rangeFormatting` (`compiler/lsp/handlers`) invoke the identical engine. | `T806` | `tests/run/fmt_cli` |
| `INV-FMT-003` | End-to-end `E19.2` conformance suite certifies idempotence `fmt(fmt(src)) == fmt(src)`, AST equivalence, comment and UTF-8 preservation (`"Xin chào thế giới"`), syntax-error refusal (`exit 1` with zero file mutation), `--check` and `--stdin` workflows, and native vs `--interp` parity (`0 WEAK-NATIVE`). | `T807` | `tests/conformance/p19/e19_2_formatter` |

---

## Sources

- `docs/base/tasks/0476*` (`BOOTSTRAP-217 §217.1–217.142`, `ASYNTAX-20..70`) — Canonical language form (`=` bindings/assignments, `.` paths, newline termination, brace & semicolon canonicalization)
- `docs/base/tasks/0374*` (`BOOTSTRAP-115 §1, §13, §29, §56`, `ATOOL-20..28`) — Deterministic `axiom fmt` zero-config design, CST trivia preservation, and AST-equivalence check
- `docs/base/tasks/0448*` (`BOOTSTRAP-189 §1, §18, §36`, `ATOOL-20..40`) — Wadler-Lindig `Doc` algebra (`Group`, `Indent`, `Line`, `SoftLine`, `LineSuffix`), `--check`/`--stdin` CLI, and LSP formatting parity
- `docs/base/tasks/0693*`, `docs/base/tasks/0695*`, `docs/base/tasks/0696*` (`BOOTSTRAP-434 §434.1–§434.13, §434.132, §434.198`, `BOOTSTRAP-435 §435.6–§435.7, §435.195`) — Self-hosted `compiler/fmt/*` architecture, lossless trivia attachment, and `P19` certification gates
- `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`, `spec/SPEC-30-compiler-architecture.md`, `spec/SPEC-31-cli-driver.md`, `spec/SPEC-100-lsp-server-ide-engine.md`
