# SPEC-02 — Axiom v0.1 grammar

## Tóm tắt
Tài liệu này là ngữ pháp chuẩn (ISO-EBNF) của cú pháp bề mặt Axiom v0.1 — thứ mà lập trình viên và
AI thực sự viết. Parser của axiom0 (C) và axiomc (Axiom) phải cho cùng một cây cú pháp. Điểm chính:
- **Gán/khai báo chỉ dùng `=`** (`let x = 1`, `let mut n = 0`, `n = n + 1`); **đường dẫn chỉ dùng `.`**
  (`use std.io.print`, `Shape.Circle(r)`, `Vec<i32>.new()`); `use` là từ khoá import duy nhất
  (quyết định của chủ dự án, ADR-0007). Parser không đoán `a.b.c` là gì — nó dựng một `DottedChain`,
  resolver mới phân loại.
- **Câu lệnh kết thúc bằng xuống dòng hoặc `;`** theo một quy tắc cố định (ADR-0008): dòng kết thúc
  bằng toán tử thì nối tiếp; dòng bắt đầu bằng `.` nối chuỗi gọi; toán tử chỉ-hai-ngôi (`+`, `&&`,
  `==` …) ở đầu dòng là lỗi, còn `-`, `*`, `!`, `~`, `|`, `(`, `[`, `{` ở đầu dòng mở câu lệnh mới.
- Bảng ưu tiên toán tử cố định (§7.1); so sánh không kết hợp (`a < b < c` là lỗi); phép gán là câu
  lệnh, không phải biểu thức (ADR-0010).
- Kiểu: `[N]T` (mảng), `[T]` sau view (dãy độ dài động), `view<T>`, `mut_view<T>`, `*const T`,
  `*mut T`, kiểu hàm, tuple, `dyn Trait`.
- Có đủ các dạng mà compiler tự viết bằng Axiom cần: vòng lặp có nhãn, pattern ký tự/khoảng/hoặc,
  `let … else`, `enum as uN`, `extern "C"` / `extern "system"` với `@link`, `unsafe`, cắt dãy
  `s[a..b]`, `impl Drop for T`, hằng kiểu tổng hợp, và `@at(…)` trên `static`/`fn` (yêu cầu chủ dự án).
- §11 có 26 chương trình mẫu — chúng trở thành test của parser. Mỗi quy tắc có mã `AXS-GRM-NNN`.

Status: canonical (T001, 2026-10-01). Decisions: ADR-0001, ADR-0004, ADR-0006, ADR-0007, ADR-0008,
ADR-0010. Lexical layer: `spec/SPEC-01-lexical.md`. Consumers: T011, T012 (parser), T013 (fuzzing),
T014/T015/T015b (resolver, HIR), the parser port (P10).

---

## 1. Scope, notation, staging

**AXS-GRM-001 — Notation.** Productions are ISO EBNF: `=` defines, `,` concatenates, `|`
alternates (binds weaker than `,`), `[ ]` optional, `{ }` zero or more, `( )` grouping, `"…"` a
token spelled exactly so, `? … ?` a condition described in prose, `(* … *)` a comment, `;` ends a
rule. Nonterminals are `CamelCase`. Names in capitals are token classes of SPEC-01 (§2). The EBNF is
the specification; parsers are hand-written (recursive descent with precedence climbing for
expressions) and need not mirror the productions. Where the EBNF alone is ambiguous, the numbered
rule next to it decides. Rule ids are stable and never renumbered.
[tasks/0324 intro, §97; tasks/0476 §135; ADR-0007 §7]

**AXS-GRM-002 — Parser boundary.** The parser consumes the token sequence of SPEC-01 and produces
an AST with a span on every node. It never resolves names, infers types, checks ownership or
evaluates constants, and it needs no symbol table: every decision in this document depends only on
tokens. Its output is deterministic. [0155 §70-71 (AAST-20..32, APARSE-20..30); 0243 §52;
tasks/0476 §106 and its ASYNTAX-59, ASYNTAX-62]

**AXS-GRM-003 — Staging.** The whole grammar is Axiom v0.1 and is final syntax (ADR-0006).
- **S0** — parsed by axiom0 (T011 core, T012 the rest). This is every production not marked S1.
  Some S0 constructs are rejected by a *later* phase of axiom0 because they are outside the
  self-host subset (float types, `static`, `dyn`, `@at`, …): the owning phase reports its
  "unsupported in bootstrap" diagnostic (SPEC-00), never the parser.
- **S1** — grammar fixed here, keywords reserved, implemented in axiomc after self-hosting. The
  axiom0 parser reports `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` at the introducing keyword and recovers
  (it skips the modifier or the block): `async fn`, `.await` (E11.4); `comptime fn`, `comptime { }`
  (E14.1).
[ROADMAP R7; ADR-0010 §11]

## 2. Tokens used as terminals

| Terminal | SPEC-01 token | Rule |
|---|---|---|
| `IDENT` | `Ident` | AXS-LEX-030 |
| `INT` | `Int` (including byte literals) | AXS-LEX-050, AXS-LEX-066 |
| `FLOAT` | `Float` | AXS-LEX-055 |
| `STR` | `Str` (plain or raw) | AXS-LEX-060, AXS-LEX-064 |
| `BYTE_STR` | `ByteStr` | AXS-LEX-063 |
| `CHAR` | `Char` | AXS-LEX-065 |
| `LABEL` | `Label` | AXS-LEX-067 |
| `EOF` | `Eof` | AXS-LEX-005 |
| `"…"` | the keyword, punctuation or operator token with that spelling | AXS-LEX-040, AXS-LEX-080 |

`"package"` in `Visibility` is an `Ident` with that spelling (a contextual word, AXS-LEX-042).
After a `.`, `INT` is a tuple index lexed by AXS-LEX-057.

## 3. Newlines, terminators, separators

```ebnf
NL   = ? empty; succeeds iff newlines are significant here (AXS-GRM-010) and the next token has NL_BEFORE ? ;
Term = ";" | NL | ? empty; succeeds iff the next token is "}" or EOF ? ;
Sep  = "," | NL ;
```

**AXS-GRM-010 — Where newlines are significant.** The parser keeps a stack of modes. At file level
the mode is ON. `{` pushes ON; `(`, `[` and the `<` of a generic parameter or argument list push OFF;
the matching closer pops. In mode OFF the `NL_BEFORE` flag is ignored everywhere. [ADR-0008 §7]

**AXS-GRM-011 — Terminators.** Every statement, every top-level item and every member of a trait,
impl or extern block is followed by `Term`. `Term` is satisfied by a `;`, by a line break before the
next token, or — without consuming anything — when the next token is `}` or `EOF`. Otherwise the
parser reports `AX_PARSE_EXPECTED_TERMINATOR` at the next token ("expected a line break or `;`").
[ADR-0008 §2; tasks/0476 §3, §107]

**AXS-GRM-012 — Continuation points.** A *continuation point* is the position after a complete
operand inside an expression, where the next token could extend the expression: a binary operator,
`as`, `..`, `..=`, an assignment operator, a postfix `(`, `[`, `?`, `.`, `->`, the `<` of generic
arguments (AXS-GRM-056) or the `{` of a struct literal (AXS-GRM-058). In mode ON, a token that has
`NL_BEFORE` does not extend the expression, except as stated in AXS-GRM-013 and AXS-GRM-014. In
mode OFF it always extends it. [ADR-0008 §3-4]

**AXS-GRM-013 — Leading dot.** At a continuation point a `.` extends the expression even when it
has `NL_BEFORE` (method chains, field access, `.await`). No statement starts with `.`, so this is
never ambiguous. [tasks/0476 §108; ADR-0008 §4]

**AXS-GRM-014 — `else` on a new line.** After the block of an `if`, and after the initialiser of a
`let` (AXS-GRM-042), the keyword `else` continues the construct even when it has `NL_BEFORE`.
[0243 §5; ADR-0008 §4]

**AXS-GRM-015 — Labels and operands of jumps.** In mode ON, `break` and `continue` take a `LABEL`
only if the label token has no `NL_BEFORE`; `return` and `break` (after its label, if any) take an
operand only if the next token has no `NL_BEFORE` and can start an expression. A label or an
expression on the following line starts a new statement (`break` ↵ `'a: loop { }` is `break`
followed by a labelled loop). In mode OFF the flag is ignored and both are taken. [ADR-0008 §6]

**AXS-GRM-016 — Separators in brace lists.** In lists enclosed in `{ }` — struct fields, enum
variants, match arms, struct-literal fields, struct-pattern fields, `use` groups — elements are
separated by `Sep`: a `,`, or a line break; a separator after the last element is optional. If the
next token is `,` it is consumed even when it starts a line. Lists in `( )`, `[ ]`, `< >` and
closure parameters are separated by `,` only (trailing `,` allowed). [tasks/0476 §13, §24; 0155 §15;
ADR-0008 §8]

**AXS-GRM-017 — Everywhere else line breaks are ignored.** The `NL_BEFORE` flag is consulted only
at `Term` and `Sep` positions, at continuation points (AXS-GRM-012), for the label and operand of
`return`, `break` and `continue` (AXS-GRM-015), for the `(` of attribute arguments (AXS-GRM-024) and in the array/slice type
rule (AXS-GRM-083). At every other position a line break has no effect:
- before a construct the grammar requires — the operand after a binary or prefix operator, after
  `=`, `=>`, `->`, `:`, `,`, `(`, `[`; the block of an `if`/`while`/`for`/`match`/`loop` header;
- before an optional part of a declaration, which is recognised by its first token: `->`, `where`
  and the body `{` of a function; `{` or `(` of a struct; `for` in an `impl` header; `:` and `=` and
  `else` in a `let`; `=` in a `static`; `as` in a `use`; the `if` of a match-arm guard.

In these positions none of the listed tokens can begin a new statement, item, member or list
element, so no program changes meaning. A line that
ends with a binary operator, `,`, `(`, `[`, `{`, `.` or `=` therefore continues on the next line, and
a `where` clause or an opening `{` may stand on its own line. [ADR-0008 §3]

**AXS-GRM-018 — Empty statement.** A `;` where a statement, top-level item or member may start is
an empty statement and is ignored. [tasks/0476 §107; ADR-0008 §10]

**AXS-GRM-019 — Leading operator.** If a statement would start with a token that is only ever a
binary or postfix operator — `+ / % ^ & && << >> == != < <= > >= = += -= *= /= %= &= |= ^= <<= >>=
.. ..= ? -> =>` or `as` — the parser reports `AX_PARSE_LEADING_OPERATOR` ("a line continues only when
the previous line ends with an operator or this line starts with `.`; move the operator to the end
of the previous line"), then skips the operator and parses the rest of the line as an expression
statement. Tokens that can start a statement (`-`, `*`, `!`, `~`, `(`, `[`, `{`, `|`, `||`) start a
new statement **without any parser diagnostic** (matrix N03, N04, N14, N26): to continue an
expression with one of them, end the previous line with the operator or wrap the expression in
parentheses. [ADR-0008 §5]

Continuation matrix (normative; `↵` is a line break; mode ON unless inside brackets):

| # | Source | Result |
|---|---|---|
| N01 | `a +` ↵ `b` | one expression `a + b` |
| N02 | `a` ↵ `+ b` | statement `a`; `AX_PARSE_LEADING_OPERATOR` |
| N03 | `a` ↵ `- b` | two statements: `a` and `-b` |
| N04 | `f` ↵ `(x)` | two statements: `f` and `(x)` |
| N05 | `f(` ↵ `x` ↵ `)` | one call |
| N06 | `(a` ↵ `+ b)` | one expression (mode OFF) |
| N07 | `x` ↵ `.f()` | one chain `x.f()` |
| N08 | `x.` ↵ `f()` | one chain `x.f()` |
| N09 | `return` ↵ `x` | `return` (unit); statement `x` |
| N10 | `if c` ↵ `{ }` | valid `if` |
| N11 | `}` ↵ `else { }` | `else` belongs to the `if` |
| N12 | `let x =` ↵ `1` | one `let` |
| N13 | `let x: i32` ↵ `= 1` | one `let` with initialiser (AXS-GRM-017) |
| N14 | `a` ↵ `[0]` | two statements: `a` and `[0]` |
| N15 | `a[` ↵ `0` ↵ `]` | one index expression |
| N16 | `v` ↵ `as u8` | statement `v`; `AX_PARSE_LEADING_OPERATOR` |
| N17 | `g()` ↵ `?` | statement `g()`; `AX_PARSE_LEADING_OPERATOR` |
| N18 | `a; b` | two statements |
| N19 | `a b` | `AX_PARSE_EXPECTED_TERMINATOR` |
| N20 | `p` ↵ `{ x: 1 }` | statement `p`; then a block (which fails to parse as statements) |
| N21 | `x` ↵ `= 1` | statement `x`; `AX_PARSE_LEADING_OPERATOR` |
| N22 | `fn f()` ↵ `-> i32` ↵ `where T: A` ↵ `{ }` | one function |
| N23 | `break` ↵ `'a: loop { }` | `break` (no label); statement `'a: loop { }` |
| N24 | `continue` ↵ `'a: loop { }` | `continue` (no label); statement `'a: loop { }` |
| N25 | `break 'a` ↵ `x` | `break 'a` (no operand); statement `x` |
| N26 | `let d = a` ↵ `- b` | two statements, no diagnostic: `let d = a` and `-b` |

## 4. Source file, module, imports, visibility, attributes

```ebnf
SourceFile = [ ModuleDecl , Term ] , { TopItem } , EOF ;
TopItem    = ( UseDecl | Item ) , Term | ";" ;
ModuleDecl = "module" , DottedName ;
DottedName = IDENT , { "." , IDENT } ;
UseDecl    = [ Visibility ] , "use" , UseTree ;
UseTree    = DottedName , [ "as" , IDENT | "." , "{" , UseItem , { Sep , UseItem } , [ Sep ] , "}" ] ;
UseItem    = DottedName , [ "as" , IDENT ] ;
Visibility = "pub" , [ "(" , ( "package" | "module" ) , ")" ] ;
Attribute  = "@" , IDENT , [ "(" , [ AttrArg , { "," , AttrArg } , [ "," ] ] , ")" ] ;
AttrArg    = [ IDENT , "=" ] , Expr ;
```

**AXS-GRM-020 — Source file.** A file is an optional module declaration followed by `use`
declarations and items in any order. [0155 §5; tasks/0476 §134]

**AXS-GRM-021 — Module declaration.** `module a.b.c` names the module the file belongs to. At most
one, and it is the first construct of the file; a later one reports `AX_PARSE_MODULE_NOT_FIRST`. It
takes no attributes and no visibility. (File-to-module mapping and the check that the declaration
matches the file path: ADR-0006 §7, T060.) [0155 §6, tasks/0476 §79; ADR-0007 §5]

**AXS-GRM-022 — `use`.** `use a.b.C` imports one name; `use a.b.C as D` renames it;
`use a.b.{C, D as E, sub.F}` imports several names sharing a prefix (one level of braces);
`pub use …` re-exports. There are no glob imports. [tasks/0476 §79-80; 0243 §34; ADR-0007 §4]

**AXS-GRM-023 — Visibility.** `pub`, `pub(package)`, `pub(module)`; no modifier means private to
the module. After `pub`, a `(` belongs to the visibility only if it is followed by `package` or
`module` and then `)`. Visibility is not allowed on `impl` blocks, `extern` blocks, `module`
declarations and the fields of enum variants (`AX_PARSE_VIS_NOT_ALLOWED`). [tasks/0476 §78; ADR-0010 §9]

**AXS-GRM-024 — Attributes.** `@name` or `@name(args)`; the `(` must not have `NL_BEFORE`.
Arguments are expressions, optionally `key = expression`. Attributes precede items, members of
impl/trait/extern blocks, struct fields and enum variants; several may be stacked, on one line or on
separate lines. The parser stores them uninterpreted; which names exist, where they are allowed and
what their arguments mean is decided by the attribute registry (unknown attributes are errors
there, not in the parser). [0155 §8; 0243 §23; tasks/0476 §75-77, §133]

## 5. Items

```ebnf
Item           = { Attribute } , [ Visibility ] , ItemKind ;
ItemKind       = FnDecl | StructDecl | EnumDecl | TraitDecl | ImplDecl | TypeAlias
               | ConstDecl | StaticDecl | ExternBlock ;

FnDecl         = [ "async" | "comptime" ] , [ "unsafe" ] , [ "extern" , STR ] , "fn" , IDENT ,
                 [ GenericParams ] , "(" , [ ParamList ] , ")" , [ "->" , Type ] ,
                 [ WhereClause ] , [ Block ] ;
ParamList      = Param , { "," , Param } , [ "," ] ;
Param          = ParamName , ":" , Type ;
ParamName      = [ "mut" ] , ( IDENT | "self" ) | "_" ;
GenericParams  = "<" , GenericParam , { "," , GenericParam } , [ "," ] , ">" ;
GenericParam   = IDENT , [ ":" , Bounds ] ;
Bounds         = TypePath , { "+" , TypePath } ;
WhereClause    = "where" , WherePred , { "," , WherePred } , [ "," ] ;
WherePred      = Type , ":" , Bounds ;

StructDecl     = "struct" , IDENT , [ GenericParams ] , [ StructBody ] ;
StructBody     = [ WhereClause ] , "{" , [ FieldList ] , "}"
               | "(" , [ TupleFieldList ] , ")" , [ WhereClause ] ;
FieldList      = Field , { Sep , Field } , [ Sep ] ;
Field          = { Attribute } , [ Visibility ] , IDENT , ":" , Type ;
TupleFieldList = TupleField , { "," , TupleField } , [ "," ] ;
TupleField     = { Attribute } , [ Visibility ] , Type ;

EnumDecl       = "enum" , IDENT , [ GenericParams ] , [ WhereClause ] ,
                 "{" , [ Variant , { Sep , Variant } , [ Sep ] ] , "}" ;
Variant        = { Attribute } , IDENT , [ "(" , [ TypeList ] , ")" | "{" , [ FieldList ] , "}" ] ;
TypeList       = Type , { "," , Type } , [ "," ] ;

TraitDecl      = "trait" , IDENT , [ GenericParams ] , [ ":" , Bounds ] , [ WhereClause ] ,
                 "{" , { TraitMember , Term | ";" } , "}" ;
TraitMember    = { Attribute } , ( FnDecl | AssocType | AssocConst ) ;
AssocType      = "type" , IDENT , [ ":" , Bounds ] ;
AssocConst     = "const" , IDENT , ":" , Type , [ "=" , Expr ] ;

ImplDecl       = "impl" , [ GenericParams ] , Type , [ "for" , Type ] , [ WhereClause ] ,
                 "{" , { ImplMember , Term | ";" } , "}" ;
ImplMember     = { Attribute } , [ Visibility ] , ( FnDecl | TypeAlias | ConstDecl ) ;

TypeAlias      = "type" , IDENT , [ GenericParams ] , "=" , Type ;
ConstDecl      = "const" , IDENT , ":" , Type , "=" , Expr ;
StaticDecl     = [ "unsafe" ] , "static" , [ "mut" ] , IDENT , ":" , Type , [ "=" , Expr ] ;

ExternBlock    = "extern" , STR , "{" , { ExternMember , Term | ";" } , "}" ;
ExternMember   = { Attribute } , [ Visibility ] , ( FnDecl | StaticDecl ) ;
```

**AXS-GRM-025 — Functions.** `fn name<generics>(params) -> Ret where … { body }`. Without `->` the
return type is `()`. Qualifiers appear in the fixed order `[async | comptime] [unsafe] [extern "abi"]`;
the ABI string is mandatory after `extern`. `async` and `comptime` are S1. The body is recognised
by the next token being `{` (with or without a line break before it); otherwise the declaration has
no body and ends at its `Term`. A body is required except for: trait members (required methods),
members of `extern` blocks (which must not have one), and `extern "abi" fn` items (a foreign function
or an `@at` overlay). Violations report `AX_PARSE_FN_BODY_REQUIRED` / `AX_PARSE_FN_BODY_NOT_ALLOWED`.
Inside an `extern` block a function takes no `extern` qualifier.
[tasks/0476 §6-7, §59, §126; 0243 §20-21, §40; ADR-0001 §1; ADR-0010 §5]

**AXS-GRM-026 — Parameters and receivers.** A parameter is `name: Type`, `mut name: Type` (a
mutable by-value binding) or `_: Type`. The name `self` is allowed only for the first parameter and,
like every parameter, needs a type: `self: Self`, `self: view<Self>`, `self: mut_view<Self>` or a
concrete type. A bare `self` or `mut self` reports `AX_PARSE_SELF_NEEDS_TYPE` (fix-it suggestions
`self: view<Self>` / `self: mut_view<Self>` / `self: Self`). A function whose first parameter is
`self` is a method; it may be a free function or a member of an `impl` (resolution: T053).
Parameters are not patterns in v0.1. [tasks/0476 §8, §39-42; ADR-0010 §5]

**AXS-GRM-027 — Generic parameters.** `<T, U: Bound + Other>` after the name of a function, struct,
enum, trait or type alias, and directly after `impl`. After `impl`, a `<` always starts generic
parameters. [tasks/0476 §19-20]

**AXS-GRM-028 — `where` clauses.** Predicates are separated by `,` (line breaks are ignored). A
trailing `,` is allowed only when a `{` follows. [tasks/0476 §21; 0155 §20]

**AXS-GRM-029 — Structs.** Named-field struct, tuple struct `struct UserId(u64)`, unit struct
`struct Marker`. [tasks/0476 §13, §23; 0155 §12-14]

**AXS-GRM-030 — Enums.** Variants are unit (`Red`), tuple (`Circle(f32)`) or struct
(`Rect { w: f32, h: f32 }`). Variant fields take no visibility. Explicit discriminant values are not
part of v0.1. A fieldless enum converts to an integer with `as` (AXS-GRM-054; ADR-0004 §7).
[tasks/0476 §24-26; 0155 §15]

**AXS-GRM-031 — Traits.** Members: methods with or without a default body, associated types
(`type Item`, optionally bounded), associated constants (optionally with a default). Supertraits
follow the name: `trait Named: Shape + Display`. [tasks/0476 §43-48]

**AXS-GRM-032 — Impl blocks.** `impl Type { … }` (inherent) and `impl Trait for Type { … }`; when
`for` is present the first type must be a `TypePath` (the trait). Members: functions, associated type
definitions (`type Item = T`), constants. `impl Drop for T { fn drop(self: mut_view<T>) { … } }` is
the destructor form (ADR-0006 §1). [tasks/0476 §43; tasks/0323 §21; 0155 §17]

**AXS-GRM-033 — Type alias.** `type Name<T> = Type` — an alias, not a new type. [tasks/0476 §22]

**AXS-GRM-034 — Constants.** `const NAME: Type = expr`; the type is mandatory; the type may be an
aggregate (arrays, structs, tuples — constant tables, ADR-0004 §2). [tasks/0476 §71]

**AXS-GRM-035 — Statics.** `static NAME: Type = expr`, `static mut NAME: Type = expr`, optionally
prefixed by `unsafe`; the initialiser may be omitted only for an overlay (`@at` without initialiser,
ADR-0001 — checked after parsing). [0109 §80; ADR-0001 §1; ADR-0010 §9]

**AXS-GRM-036 — Foreign items.** `extern "C" { … }` / `extern "system" { … }` blocks contain
body-less function declarations and statics; attributes such as `@link("kernel32")` attach to the
block or to members. `extern "C" fn name(…) { … }` at item level defines an Axiom function with a
foreign ABI. Variadic parameters are not part of v0.1. [tasks/0476 §126-127; tasks/0323 §83-85; T065]

**AXS-GRM-037 — `@at`.** `@at(<constant expression>)` is admitted, by AXS-GRM-024, on `static`,
`static mut`, `fn` and `extern fn` items; `image("name")` and `image_self()` inside it are ordinary
call expressions. The parser attaches the attribute; semantics are E13.6/E13.7 and axiom0 reports
`AX_ADDR_UNSUPPORTED_STAGE0`. [REQ-OWNER-003, REQ-OWNER-005; ADR-0001]

**AXS-GRM-038 — Item-start diagnostics.** At a position where an item may start:
- the identifier `import` followed on the same line by an identifier: `AX_PARSE_IMPORT`, fix-it
  replace `import` by `use`; continue as a `use` declaration;
- the identifier `mod` followed on the same line by an identifier: `AX_PARSE_MOD` ("write
  `module a.b` at the top of the file; there are no inline modules"); skip to the end of the line or
  of the following `{ … }`;
- a reserved word (`move`, `union`, `yield`): `AX_PARSE_RESERVED_KEYWORD`;
- anything else that cannot start an item: `AX_PARSE_EXPECTED_ITEM`.
[ADR-0007 §4-5]

## 6. Blocks and statements

```ebnf
Block      = "{" , { Stmt } , "}" ;
Stmt       = ( LetStmt | AssignStmt | ExprStmt ) , Term | ";" ;
LetStmt    = "let" , Pattern , [ ":" , Type ] , [ "=" , Expr , [ "else" , Block ] ] ;
AssignStmt = Expr , AssignOp , Expr ;
ExprStmt   = Expr ;
AssignOp   = "=" | "+=" | "-=" | "*=" | "/=" | "%=" | "&=" | "|=" | "^=" | "<<=" | ">>=" ;
```

**AXS-GRM-040 — Block value.** A block is an expression. If its last statement is an `ExprStmt`
whose `Term` is not an explicit `;`, that expression is the block's *tail expression* and its value
is the value of the block. Otherwise the value is `()`. [tasks/0476 §4-5; 0243 §6; ADR-0008 §9]

**AXS-GRM-041 — `let`.** `let pattern = expr`, `let pattern: Type = expr`, and the deferred form
`let name: Type` (a single binding; assigned later, checked by definite-assignment analysis). A `let`
with neither type nor initialiser reports `AX_PARSE_LET_NEEDS_TYPE_OR_INIT`. Bindings are immutable
unless the pattern says `mut`. A second `let` of the same name shadows. [tasks/0476 §9-12;
`axiom-syntax` Rule 1]

**AXS-GRM-042 — `let … else`.** `let pattern = expr else { … }`: the pattern may be refutable and
the block must diverge (checked later). The `else` may start a line (AXS-GRM-014). If the
initialiser ends in an `if` without `else`, the `else` binds to that `if`. [T038b; ADR-0010 §10]

**AXS-GRM-043 — Assignment.** `place = expr` and the ten compound forms are statements, not
expressions. The left side is parsed as an expression; that it denotes a place (a name, field,
tuple index, index, `*pointer`, `pointer->field`) is checked after parsing. An assignment operator
found where an expression must continue (`if x = 5`, `f(x = 1)`, `a = b = c`) reports
`AX_PARSE_ASSIGN_IN_EXPR` with the hint "use `==` to compare". [tasks/0476 §11, §82; ADR-0010 §3]

**AXS-GRM-044 — Expression statement.** Any expression followed by `Term`.

**AXS-GRM-045 — `var`.** A statement that starts with the identifier `var` followed on the same
line by an identifier reports `AX_PARSE_VAR` with the fix-it "replace `var` by `let mut`" and is
parsed as a `let mut` statement. [REQ-OWNER-001; ADR-0007 §1]

**AXS-GRM-046 — No items in blocks.** Blocks contain statements only. An item keyword at statement
start (`fn`, `struct`, `enum`, `trait`, `impl`, `type`, `const`, `static`, `use`, `module`, `extern`,
`pub`, `unsafe` followed by `fn`/`static`/`extern`, or `async`/`comptime` followed by `fn`,
`unsafe` or `extern`) reports `AX_PARSE_ITEM_IN_BLOCK`; the parser
parses the item and discards it. [ADR-0010 §9]

## 7. Expressions

### 7.1 Precedence

**AXS-GRM-050 — Precedence and associativity.** From tightest to loosest:

| Level | Operators | Associativity |
|---|---|---|
| 1 | postfix: call `( )`, index `[ ]`, `.name`, `.0`, `.await`, `?`, `->name` | left |
| 2 | prefix: `-` `!` `~` `*` | right (prefix) |
| 3 | `as` | left |
| 4 | `*` `/` `%` | left |
| 5 | `+` `-` | left |
| 6 | `<<` `>>` | left |
| 7 | `&` | left |
| 8 | `^` | left |
| 9 | `\|` | left |
| 10 | `==` `!=` `<` `<=` `>` `>=` | **none** |
| 11 | `&&` | left |
| 12 | `\|\|` | left |
| 13 | `..` `..=` | **none** |
| 14 | closures `\|x\| e`; `return`, `break`, `continue` | prefix; operand extends as far as possible |

Assignment is not in the table: it is a statement (AXS-GRM-043). Precedence does not define
evaluation order (SPEC-03). [0109 §92 (the order adopted); ADR-0010 §2 — decided against the C
order of 0243 §35, 0155 §35, 0173 §30, tasks/0324 §28 and tasks/0476 §136; tasks/0476 §137-138]

```ebnf
Expr          = JumpExpr | ClosureExpr | RangeExpr ;
JumpExpr      = "return" , [ Expr ] | "break" , [ LABEL ] , [ Expr ] | "continue" , [ LABEL ] ;
ClosureExpr   = ClosureParams , ( Expr | "->" , Type , Block ) ;
ClosureParams = "||" | "|" , [ ClosureParam , { "," , ClosureParam } , [ "," ] ] , "|" ;
ClosureParam  = ( [ "mut" ] , IDENT | "_" ) , [ ":" , Type ] ;
RangeExpr     = OrExpr , [ ( ".." | "..=" ) , OrExpr ] ;
OrExpr        = AndExpr , { "||" , AndExpr } ;
AndExpr       = CmpExpr , { "&&" , CmpExpr } ;
CmpExpr       = BitOrExpr , [ CmpOp , BitOrExpr ] ;
CmpOp         = "==" | "!=" | "<" | "<=" | ">" | ">=" ;
BitOrExpr     = BitXorExpr , { "|" , BitXorExpr } ;
BitXorExpr    = BitAndExpr , { "^" , BitAndExpr } ;
BitAndExpr    = ShiftExpr , { "&" , ShiftExpr } ;
ShiftExpr     = AddExpr , { ( "<<" | ">>" ) , AddExpr } ;
AddExpr       = MulExpr , { ( "+" | "-" ) , MulExpr } ;
MulExpr       = CastExpr , { ( "*" | "/" | "%" ) , CastExpr } ;
CastExpr      = UnaryExpr , { "as" , Type } ;
UnaryExpr     = ( "-" | "!" | "~" | "*" ) , UnaryExpr | PostfixExpr ;
PostfixExpr   = PrimaryExpr , { PostfixOp } ;
PostfixOp     = "." , IDENT , [ GenericArgs ] | "." , INT | "." , "await"
              | CallArgs | "[" , IndexArg , "]" | "?" | "->" , IDENT ;
CallArgs      = "(" , [ Expr , { "," , Expr } , [ "," ] ] , ")" ;
IndexArg      = Expr | OrExpr , ".." | ".." , OrExpr ;
GenericArgs   = "<" , GenericArg , { "," , GenericArg } , [ "," ] , ">" ;
GenericArg    = Type | IDENT , "=" , Type ;
```

**AXS-GRM-051 — Comparisons do not chain.** `a < b < c`, `a == b == c`, `a < b == c` are syntax
errors: after one comparison at level 10, another comparison operator reports
`AX_PARSE_CHAINED_COMPARISON` ("comparison operators cannot be chained; use parentheses or `&&`").
[`axiom-syntax` Rule 2; ADR-0010 §2]

**AXS-GRM-052 — Ranges.** `a..b` (end excluded) and `a..=b` (end included) with both operands, at
level 13, non-associative. Open forms exist only inside index brackets (AXS-GRM-070).
[tasks/0476 §33; tasks/0324 §38]

**AXS-GRM-053 — Prefix operators.** `-x` negation, `!x` logical not (`bool`), `~x` bitwise not
(integers), `*p` raw-pointer dereference (unsafe, checked later). There is no unary `+`. A `&` or
`&&` where an operand is expected (not at statement start) reports `AX_PARSE_REFERENCE_OPERATOR`
("Axiom has no `&` reference operator; pass the value, or write `view(x)` / `mut_view(x)`"), then
parses the operand. `-x.f()` is `-(x.f())`. [tasks/0476 §58, §82; ADR-0010 §2]

**AXS-GRM-054 — Cast.** `expr as Type`, left-associative (`x as u8 as char`), binding tighter than
`*` and looser than prefix operators: `-x as u8` is `(-x) as u8`; `a * b as T` is `a * (b as T)`.
The type extends as far as possible, including dotted segments, so a cast followed by a postfix
operator needs parentheses: `(x as u32).max(1)`. A `<` after the type name is taken as generic
arguments only if the tentative parse of AXS-GRM-056 succeeds (no follower condition); otherwise it
is a comparison: `x as usize < n`. [0243 §38; 0155 §35; ADR-0010 §2]

### 7.2 Paths and postfix chains

**AXS-GRM-055 — DottedChain.** The parser does not classify dotted names. A `PostfixExpr` is
represented as one node `DottedChain { head, segments }` where `head` is the primary expression and
each segment is one of: `Name(ident, generic_args?)`, `TupleIndex(n)`, `Call(args)`, `Index(arg)`,
`Try`, `Await`, `Arrow(ident)`. `std.io.print(x)`, `v.length()`, `Shape.Circle(r)`, `p.x.y`,
`Vec<i32>.new()` all have the same shape. The resolver resolves the head with the lookup order
local → parameter → module item → import → re-export → prelude and walks right: after a value,
names are fields or methods (`Name` followed by `Call` is a method call); after a module, names are
its items; after a type, enum or trait, names are associated items or variants. [REQ-OWNER-002;
`axiom-syntax` Rule 2; ADR-0007 §2; 0155 §28-31; T014]

**AXS-GRM-056 — Generic arguments in expressions.** After the head name or a `Name` segment, a `<`
without `NL_BEFORE` starts a *tentative* parse of `GenericArgs` (line breaks inside are ignored, and
a closing `>` may be split from `>>`, `>=`, `>>=` — AXS-GRM-057). The parser **commits** to generic
arguments iff the tentative parse succeeds and the token after the closing `>` is `(`, `.`, or — in
a context where struct literals are allowed (AXS-GRM-059) — `{`, in each case without `NL_BEFORE`
unless it is `.`. Otherwise it backtracks and treats `<` as the comparison operator. The tentative
parse reports no diagnostics. Examples: `Vec<i32>.new()`, `size_of<T>()`, `parse<u32>(s)?`,
`Point<f32> { x: 1.0, y: 2.0 }` commit; `a < b`, `i < len(xs)`, `a < b >> c` do not. Consequence:
`f(a < b, c > (d))` is parsed as the generic call `a<b, c>(d)`; write `f((a < b), c > (d))` for two
comparisons. [`axiom-syntax` Rule 2; ADR-0007 §3; 0155 §51-52; tasks/0476 §106]

**AXS-GRM-057 — Splitting `>`.** When a generic argument or parameter list (in a type, a pattern
context or a committed/tentative expression parse) needs a closing `>` and the next token is `>>`,
`>=` or `>>=`, the parser consumes its first `>` and continues with the remainder (`>`, `=`, `>=`)
as the next token. [tasks/0324 §44, ALEX-62; SPEC-01 AXS-LEX-086]

### 7.3 Primary expressions

```ebnf
PrimaryExpr   = Literal | PathExpr | "self" | ParenExpr | ArrayExpr | StructLit | Block
              | IfExpr | MatchExpr | LoopExpr | WhileExpr | ForExpr | UnsafeBlock | ViewExpr
              | ComptimeBlock ;
Literal       = INT | FLOAT | STR | BYTE_STR | CHAR | "true" | "false" ;
PathExpr      = IDENT , [ GenericArgs ] | "Self" ;
ParenExpr     = "(" , ")" | "(" , Expr , ")" | "(" , Expr , "," , [ Expr , { "," , Expr } , [ "," ] ] , ")" ;
ArrayExpr     = "[" , [ Expr , { "," , Expr } , [ "," ] ] , "]" | "[" , Expr , ";" , Expr , "]" ;
StructLit     = StructPath , "{" , [ FieldInit , { Sep , FieldInit } , [ Sep ] ] , "}" ;
StructPath    = PathExpr , { "." , IDENT , [ GenericArgs ] } ;
FieldInit     = IDENT , [ ":" , Expr ] ;
IfExpr        = "if" , Cond , Block , [ "else" , ( IfExpr | Block ) ] ;
Cond          = "let" , Pattern , "=" , Expr | Expr ;
MatchExpr     = "match" , Expr , "{" , [ MatchArm , { Sep , MatchArm } , [ Sep ] ] , "}" ;
MatchArm      = Pattern , [ "if" , Expr ] , "=>" , Expr ;
LoopExpr      = [ LABEL , ":" ] , "loop" , Block ;
WhileExpr     = [ LABEL , ":" ] , "while" , Cond , Block ;
ForExpr       = [ LABEL , ":" ] , "for" , Pattern , "in" , Expr , Block ;
UnsafeBlock   = "unsafe" , Block ;
ViewExpr      = ( "view" | "mut_view" ) , "(" , Expr , ")" ;
ComptimeBlock = "comptime" , Block ;
```

**AXS-GRM-058 — Struct literal.** A `StructLit` is recognised when a chain made only of the head
name and `Name` segments (with or without generic arguments) is followed by `{` without `NL_BEFORE`,
in a context where struct literals are allowed. Fields are `name: expr` or the shorthand `name`
(meaning `name: name`), separated by `Sep`. `Self { … }` is allowed. The update form `..base` is not
part of v0.1. [tasks/0476 §13; tasks/0323 §17-18; ADR-0010 §7]

**AXS-GRM-059 — No struct literal in headers.** In the `Cond` of `if` and `while` (both forms),
the scrutinee of `match` and the iterable of `for`, a `{` that follows a path is the start of the
construct's block, not a struct literal, and `{` is not a follower for AXS-GRM-056. The restriction
ends inside any `( )`, `[ ]` or `{ }` nested in the header. [ADR-0010 §7]

**AXS-GRM-060 — Literals.** Integer (with optional suffix, including byte literals), float, string,
raw string, byte string, character, `true`, `false`. [SPEC-01 §4-5]

**AXS-GRM-061 — Parentheses, unit, tuples.** `()` is the unit value; `(e)` is grouping; `(e,)` is
a one-element tuple; `(a, b)` a tuple. [tasks/0476 §16; tasks/0324 §88]

**AXS-GRM-062 — Arrays.** `[a, b, c]` lists elements; `[value; count]` repeats `value` `count`
times (`count` is a constant expression); `[]` is the empty array. [tasks/0476 §17; tasks/0324 §87]

**AXS-GRM-063 — `if`.** `if cond { } else if cond { } else { }`; the blocks are mandatory; there
is no `then` and no parenthesised form requirement. `if let pattern = expr { }` tests a pattern.
`if` is an expression. [tasks/0476 §28-29, §113]

**AXS-GRM-064 — `match`.** Arms are `pattern => expr` or `pattern if guard => expr`, separated by
`Sep`. An arm that needs several statements or an assignment uses a block: `p => { x += 1 }`.
[tasks/0476 §27, §118-119]

**AXS-GRM-065 — Loops and labels.** `loop { }`, `while cond { }`, `while let pattern = expr { }`,
`for pattern in expr { }`. Each may be preceded by a label definition `'name:`. Loops are
expressions (`loop` yields the value of `break value`; `while` and `for` yield `()`). A label
followed by `:` and anything other than `loop`/`while`/`for` reports `AX_PARSE_EXPECTED_LOOP`.
[tasks/0476 §30-34, §114; tasks/0323 §97; ADR-0004 §7]

**AXS-GRM-066 — Jumps.** `return`, `return expr`; `break`, `break expr`, `break 'label`,
`break 'label expr`; `continue`, `continue 'label`. They are expressions of type `never` at the
loosest level, so they may be a match-arm body, a closure body or a call argument, but not an
operand of a binary operator (parenthesise). Same-line rule for the label and the operand:
AXS-GRM-015. [ADR-0010 §4]

**AXS-GRM-067 — Closures.** `|a, b| expr`, `|| expr`, typed `|a: i32, b: i32| -> i32 { … }` (a
return type requires a block body). The body extends as far as possible. A `|` or `||` where an
operand is expected starts a closure; after an operand it is the binary operator. Capture is
inferred; `move` is reserved and reports `AX_PARSE_RESERVED_KEYWORD`. [tasks/0476 §37-38; ADR-0010 §6]

**AXS-GRM-068 — `unsafe` block.** `unsafe { … }` is an expression with the value of its block.
[tasks/0476 §125]

**AXS-GRM-069 — View expressions.** `view(place)` and `mut_view(place)` create a stored capability
on a place; they are dedicated forms, not calls (the operand is not moved). [tasks/0476 §55-56;
ADR-0009 §2; ADR-0010 §8]

**AXS-GRM-070 — Indexing and sub-ranges.** `a[i]` indexes. Inside index brackets the open range
forms are available: `s[a..b]`, `s[a..]`, `s[..b]` (ADR-0006 §5). `a..` and `..b` are not
expressions elsewhere. [tasks/0476 §86-87; ADR-0006 §5]

**AXS-GRM-071 — Pointer member access.** `p->field` is sugar for `(*p).field` (unsafe; lowered when
building HIR). [tasks/0476 §60]

**AXS-GRM-072 — `?`.** Postfix propagation operator on `Result`/`Option` values. [tasks/0476 §65]

**AXS-GRM-073 — Calls.** `f(a, b)`; arguments are positional expressions; no named or default
arguments. A `(` continues an expression as a call only without `NL_BEFORE` (AXS-GRM-012).
[tasks/0323 §64-66]

**AXS-GRM-074 — S1 forms.** `expr.await` and `comptime { … }` are part of the grammar; axiom0
reports `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` (AXS-GRM-003). [tasks/0476 §69, §72]

**AXS-GRM-075 — `self` and `Self`.** `self` is the receiver value. `Self` is the implementing type
and may head a chain (`Self.new()`, `Self.Item`, `Self { … }`, `Self(x)`). [tasks/0476 §43-48]

## 8. Types

```ebnf
Type      = TypePath | TupleType | ArrayType | SliceType | ViewType | PtrType | FnType | DynType ;
TypePath  = ( IDENT , [ GenericArgs ] | "Self" ) , { "." , IDENT , [ GenericArgs ] } ;
TupleType = "(" , ")" | "(" , Type , ")" | "(" , Type , "," , [ Type , { "," , Type } , [ "," ] ] , ")" ;
ArrayType = "[" , Expr , "]" , Type ;
SliceType = "[" , Type , "]" ;
ViewType  = ( "view" | "mut_view" ) , "<" , Type , ">" ;
PtrType   = "*" , ( "const" | "mut" ) , Type ;
FnType    = [ "unsafe" ] , [ "extern" , STR ] , "fn" , "(" , [ TypeList ] , ")" , [ "->" , Type ] ;
DynType   = "dyn" , Bounds ;
```

**AXS-GRM-080 — Type paths.** `i32`, `Point`, `Vec<i32>`, `std.collections.Vec<i32>`, `Self`,
`Self.Item`, `T.Item`. In a type, `<` always starts generic arguments. Primitive type names
(`bool`, `char`, the integer and float types, `never`, `Str`) are ordinary names resolved through
the prelude. A generic argument is a type or, in bounds, an associated-type binding `Item = T`.
[tasks/0476 §19-20, §46; tasks/0324 §54; SPEC-01 AXS-LEX-042]

**AXS-GRM-081 — Unit and tuples.** `()` is the unit type; `(T)` is `T`; `(T,)` a one-element
tuple; `(A, B)` a tuple. [tasks/0324 §47]

**AXS-GRM-082 — Fixed arrays.** `[N]T`: `N` is a constant expression, `T` the element type;
`[2][3]i32` is an array of two `[3]i32`. The former spelling `[T; N]` — a `;` after the first
component inside the brackets of a type — reports `AX_PARSE_ARRAY_TYPE_ORDER` with the fix-it `[N]T`. [tasks/0476 §17; ADR-0010 §1]

**AXS-GRM-083 — Unsized sequences.** `[T]` is the dynamically sized sequence type, used behind a
view or pointer: `view<[u8]>`, `mut_view<[T]>`. Disambiguation after `[`: (1) parse the bracket
content tentatively as a `Type`; if that succeeds, the next token is `]`, and the token after `]`
has `NL_BEFORE` or cannot start a type, the result is `SliceType`; (2) otherwise parse the content
as an `Expr`, then `]`, then the element `Type`: `ArrayType`. When the length is a plain name
(`[N]T`), the element type must therefore start on the same line as the `]`. Conversely a slice
type directly followed on the same line by a token that starts a type (`p as *const [u8] * n`) is
read as an array type; parenthesise the cast. Tokens that start a type: `IDENT`, `Self`, `(`, `[`, `*`, `fn`,
`unsafe`, `extern`, `view`, `mut_view`, `dyn`. [T048b; ADR-0010 §1]

**AXS-GRM-084 — Views.** `view<T>` (read capability), `mut_view<T>` (mutable capability). There
are no `&T`, `&mut T` types. [tasks/0476 §51-53; ASYNTAX-32..34]

**AXS-GRM-085 — Raw pointers.** `*const T`, `*mut T`. [tasks/0476 §59]

**AXS-GRM-086 — Function types.** `fn(A, B) -> R`, `fn()`, with optional `unsafe` and
`extern "abi"` in that order; parameters are types without names. [tasks/0476 §36]

**AXS-GRM-087 — Trait objects.** `dyn Trait`, `dyn A + B` (parsed in S0; implemented by T058 after
self-hosting). [tasks/0476 §49]

**AXS-GRM-088 — Line breaks in types.** A type contains no continuation points; inside `< >`,
`( )` and `[ ]` line breaks are ignored; a `.` continues a `TypePath` even on a new line.

## 9. Patterns

```ebnf
Pattern    = PatNoOr , { "|" , PatNoOr } ;
PatNoOr    = "_" | RangePat | LiteralPat | BindingPat | PathPat | TuplePat ;
BindingPat = "mut" , IDENT ;
PathPat    = PatPath , [ "(" , [ Pattern , { "," , Pattern } , [ "," ] ] , ")" | "{" , [ FieldPats ] , "}" ] ;
PatPath    = ( IDENT | "Self" ) , { "." , IDENT } ;
FieldPats  = ".." | FieldPat , { Sep , FieldPat } , [ Sep , ".." ] , [ Sep ] ;
FieldPat   = IDENT , [ ":" , Pattern ] | "mut" , IDENT ;
TuplePat   = "(" , ")" | "(" , Pattern , ")" | "(" , Pattern , "," , [ Pattern , { "," , Pattern } , [ "," ] ] , ")" ;
LiteralPat = PatNumber | CHAR | "true" | "false" ;
RangePat   = RangeBound , ( "..=" | ".." ) , RangeBound ;
RangeBound = PatNumber | CHAR ;
PatNumber  = [ "-" ] , INT ;
```

**AXS-GRM-090 — Where patterns occur.** `let`, `let … else`, `if let`, `while let`, `for`, and
match arms. Whether a pattern must be irrefutable is checked later (T038b). [tasks/0476 §113-119]

**AXS-GRM-091 — Wildcard.** `_` matches anything and binds nothing. [tasks/0476 §117]

**AXS-GRM-092 — Identifier patterns.** `mut name` always introduces a mutable binding. A `PathPat`
that is a single identifier with no payload is an *identifier pattern*: the resolver treats it as a
constant pattern if the name resolves to a unit enum variant, unit struct or constant in scope, and
as a new immutable binding otherwise. A path with two or more segments never binds. [ADR-0010 §10]

**AXS-GRM-093 — Literal patterns.** Integer literals (optionally negated; byte literals included),
character literals, `true`, `false`. String and float literal patterns are not part of v0.1.
[ADR-0004 §7; T038b]

**AXS-GRM-094 — Range patterns.** `lo..=hi` (inclusive) and `lo..hi` (end excluded) with literal
integer or character bounds: `'a'..='z'`, `0..10`, `b'0'..=b'9'`. [ADR-0004 §7; 0243 §28]

**AXS-GRM-095 — Path, variant and tuple-struct patterns.** `Option.None`, `Shape.Circle(r)`,
`Some(x)`, `UserId(n)`. [tasks/0476 §25, §66]

**AXS-GRM-096 — Struct patterns.** `Point { x, y }`, `Point { x: px, y: _ }`, `Point { x, .. }`,
`Shape.Rect { w, h }`; `..` (last) ignores the remaining fields. [tasks/0476 §115-116]

**AXS-GRM-097 — Tuple patterns.** `()`, `(p)` (grouping), `(p,)`, `(a, b)`.

**AXS-GRM-098 — Or-patterns.** `p | q | r`, at the top of a pattern or nested inside parentheses,
tuple, variant and field patterns. No leading `|`. [tasks/0476 §118; ADR-0004 §7]

**AXS-GRM-099 — Guards.** `pattern if expr => body` in match arms only. [tasks/0476 §119]

## 10. Error recovery and diagnostics

**AXS-GRM-100 — Recovery.** The parser never stops at the first error and never crashes. After an
error it produces an error node carrying the span skipped, and resynchronises at the nearest of: a
`Term` position in the enclosing block (a line break in mode ON, or `;`), the closing delimiter of
the innermost open `( )`, `[ ]`, `{ }`, a `,` in a list, an item keyword that starts a line, or
`EOF`. At most one diagnostic is reported per erroneous construct; `Error` tokens and tokens with
the `ERROR` flag (already reported by the lexer) are not reported again. An unclosed delimiter
reports `AX_PARSE_UNCLOSED_DELIMITER` at the opener. Recovery is deterministic.
[0155 §71 (APARSE-27..29); 0243 §47; tasks/0324 §98; tasks/0476 §101]

**AXS-GRM-101 — Codes.** Area `PARSE` (registry `bootstrap/axiom0/src/diag/codes/PARSE.def`;
taxonomy by T002). All are errors.

| Code | Condition | Rule | Fix-it |
|---|---|---|---|
| `AX_PARSE_EXPECTED_TOKEN` | a specific token is required (message names it) | — | insert when unambiguous |
| `AX_PARSE_EXPECTED_EXPR` | an expression is required | — | — |
| `AX_PARSE_EXPECTED_TYPE` | a type is required | — | — |
| `AX_PARSE_EXPECTED_PATTERN` | a pattern is required | — | — |
| `AX_PARSE_EXPECTED_ITEM` | an item is required | AXS-GRM-038 | — |
| `AX_PARSE_EXPECTED_TERMINATOR` | two statements or items on one line without `;` | AXS-GRM-011 | — |
| `AX_PARSE_EXPECTED_LOOP` | label not followed by a loop | AXS-GRM-065 | — |
| `AX_PARSE_UNCLOSED_DELIMITER` | `(`, `[`, `{` without its closer | AXS-GRM-100 | — |
| `AX_PARSE_LEADING_OPERATOR` | line starts with a binary/postfix operator | AXS-GRM-019 | — |
| `AX_PARSE_CHAINED_COMPARISON` | `a < b < c` | AXS-GRM-051 | — |
| `AX_PARSE_ASSIGN_IN_EXPR` | assignment operator inside an expression | AXS-GRM-043 | — |
| `AX_PARSE_REFERENCE_OPERATOR` | prefix `&` / `&&` | AXS-GRM-053 | remove `&` |
| `AX_PARSE_VAR` | `var name …` | AXS-GRM-045 | `let mut` |
| `AX_PARSE_IMPORT` | `import a.b` | AXS-GRM-038 | `use` |
| `AX_PARSE_MOD` | `mod name` | AXS-GRM-038 | — |
| `AX_PARSE_MODULE_NOT_FIRST` | `module` after another construct, or twice | AXS-GRM-021 | — |
| `AX_PARSE_ITEM_IN_BLOCK` | item inside a block | AXS-GRM-046 | — |
| `AX_PARSE_LET_NEEDS_TYPE_OR_INIT` | `let x` alone | AXS-GRM-041 | — |
| `AX_PARSE_SELF_NEEDS_TYPE` | bare `self` parameter | AXS-GRM-026 | `self: view<Self>` |
| `AX_PARSE_FN_BODY_REQUIRED` | function without body where one is required | AXS-GRM-025 | — |
| `AX_PARSE_FN_BODY_NOT_ALLOWED` | body in an `extern` block | AXS-GRM-025 | — |
| `AX_PARSE_VIS_NOT_ALLOWED` | visibility where none is allowed | AXS-GRM-023 | remove it |
| `AX_PARSE_ARRAY_TYPE_ORDER` | type written `[T; N]` | AXS-GRM-082 | `[N]T` |
| `AX_PARSE_RESERVED_KEYWORD` | `move`, `union`, `yield` | AXS-GRM-038, AXS-GRM-067 | — |
| `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` | S1 construct in axiom0 | AXS-GRM-003 | — |

Rejected spellings and their diagnostics (parser ui tests; the lexer cases are in SPEC-01 §10):

| # | Input | Diagnostic |
|---|---|---|
| R01 | `var count = 0` | `AX_PARSE_VAR` |
| R02 | `import std.io` | `AX_PARSE_IMPORT` |
| R03 | `mod util` | `AX_PARSE_MOD` |
| R04 | `let xs: [i32; 4] = make()` | `AX_PARSE_ARRAY_TYPE_ORDER` |
| R05 | `fn len(self) -> usize { 0 }` | `AX_PARSE_SELF_NEEDS_TYPE` |
| R06 | `if a < b < c { }` | `AX_PARSE_CHAINED_COMPARISON` |
| R07 | `if x = 5 { }` | `AX_PARSE_ASSIGN_IN_EXPR` |
| R08 | `let r = &x` | `AX_PARSE_REFERENCE_OPERATOR` |
| R09 | `let f = move \|x\| x` | `AX_PARSE_RESERVED_KEYWORD` |
| R10 | `let a = 1 let b = 2` | `AX_PARSE_EXPECTED_TERMINATOR` |
| R11 | `fn f() { fn g() {} }` | `AX_PARSE_ITEM_IN_BLOCK` |
| R12 | `let x = (1 + ` then end of file | `AX_PARSE_UNCLOSED_DELIMITER` |
| R13 | `async fn f() {}` (axiom0) | `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` |
| R14 | `use a::b` | `AX_LEX_COLON_COLON` only (parses as `use a.b`) |
| R15 | `x := 1` | `AX_LEX_COLON_EQ` only (parses as `x = 1`) |

## 11. Example corpus

**AXS-GRM-110 — Conformance.** Every program below is syntactically valid Axiom v0.1: an S0
parser accepts EX-01 … EX-26 with zero diagnostics, and each becomes a golden parser test (T011,
T012). They are parser tests: several use names that are not declared in the example, and several use
features that axiom0 rejects after parsing (floats, traits before their task, `static`, `@at`). The
S1 examples (EX-S1) must parse in axiomc and produce `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` in axiom0.

### EX-01 — smallest program
```axiom
fn main() {}
```

### EX-02 — module, import, call, UTF-8 string
```axiom
module demo.hello

use std.io.print

fn main() {
    print("Xin chào thế giới\n")
}
```

### EX-03 — bindings, assignment, shadowing, deferred initialisation, optional `;`
```axiom
fn main() -> i32 {
    let a = 10
    let b: i32 = 20
    let mut total = a + b
    total += 1
    total = total * 2
    let total = total - 1
    let late: i32
    late = total
    let x = 1; let y = 2;
    late + x + y
}
```

### EX-04 — operators and precedence
```axiom
const MASK: u32 = 0x0f

fn ops(a: u32, b: u32, flags: u32) -> bool {
    let sum = a + b * 2 - (a % 3)
    let bits = (a << 2 | b >> 1) ^ ~flags
    let neg = -(a as i64) + b as i64
    let masked = flags & MASK == 0
    let ordered = a < b && b <= 100 || a == b
    let chained = sum +
        bits +
        (a
            * b)
    !masked && ordered && neg != 0 && chained >= 1
}
```

### EX-05 — control flow, loop values, labels, ranges
```axiom
fn classify(n: i32) -> i32 {
    if n < 0 {
        -1
    } else if n == 0 {
        0
    } else {
        1
    }
}

fn first_multiple(limit: u32, k: u32) -> u32 {
    let mut i = 1u32
    let found = loop {
        if i % k == 0 {
            break i
        }
        if i >= limit {
            break 0
        }
        i += 1
    }
    found
}

fn count_pairs(n: u32) -> u32 {
    let mut count = 0u32
    'outer: for a in 0..n {
        let mut b = 0u32
        while b < n {
            b += 1
            if a + b > n {
                continue 'outer
            }
            if count > 1000 {
                break 'outer
            }
            count += 1
        }
    }
    count
}

fn sum_inclusive(n: u32) -> u32 {
    let mut s = 0u32
    for i in 1..=n {
        s += i
    }
    s
}
```

### EX-06 — functions, recursion, tuples, tuple indices
```axiom
fn fib(n: u32) -> u32 {
    if n < 2 {
        return n
    }
    fib(n - 1) + fib(n - 2)
}

fn div_mod(a: i32, b: i32) -> (i32, i32) {
    (a / b, a % b)
}

fn unit_value() -> () {
    ()
}

fn main() -> i32 {
    let pair = div_mod(17, 5)
    let (q, r) = pair
    let nested = ((1, 2), (3,))
    let first = nested.0.1
    let single = nested.1.0
    q + r + first + single + fib(10) as i32
}
```

### EX-07 — structs: named, tuple, unit; literals; field access
```axiom
struct Point {
    x: f32
    y: f32
}

pub struct Rect { pub origin: Point, pub size: Point }

struct UserId(u64)

struct Marker

fn make(x: f32, y: f32) -> Point {
    Point { x, y }
}

fn area(r: view<Rect>) -> f32 {
    r.size.x * r.size.y
}

fn main() {
    let p = Point {
        x: 1.0
        y: 2.0
    }
    let r = Rect { origin: p, size: make(3.0, 4.0) }
    let id = UserId(42)
    let m = Marker
    let raw = id.0
    let a = area(r)
}
```

### EX-08 — enums, match, dotted variants, `enum as`
```axiom
enum Shape {
    Circle(f32)
    Rect { w: f32, h: f32 }
    Empty
}

enum Color { Red, Green, Blue }

fn area(s: Shape) -> f32 {
    match s {
        Shape.Circle(r) => 3.14159 * r * r
        Shape.Rect { w, h } => w * h
        Shape.Empty => 0.0
    }
}

fn code(c: Color) -> u8 {
    c as u8
}

fn name(c: Color) -> Str {
    match c {
        Color.Red => "red",
        Color.Green => "green",
        Color.Blue => { "blue" }
    }
}
```

### EX-09 — patterns: literal, range, or, guard, struct, tuple, `if let`, `while let`, `let … else`
```axiom
enum Maybe {
    Some(i32)
    None
}

struct Pair { left: i32, right: i32 }

fn classify(c: char) -> u8 {
    match c {
        'a'..='z' | 'A'..='Z' | '_' => 1
        '0'..='9' => 2
        ' ' | '\t' | '\n' => 3
        _ => 0
    }
}

fn bucket(n: i32) -> i32 {
    match n {
        -1 => 0
        0 | 1 => 1
        2..10 => 2
        x if x % 2 == 0 => 3
        _ => 4
    }
}

fn sum(p: Pair, m: Maybe) -> i32 {
    let Pair { left, right: r } = p
    let (mut a, _) = (left, r)
    if let Maybe.Some(v) = m {
        a += v
    }
    let Maybe.Some(w) = m else {
        return a
    }
    match (a, w) {
        (0, _) => 0
        (x, y) if x == y => x
        (x, y) => x + y
    }
}

fn drain(mut m: Maybe) -> i32 {
    let mut total = 0
    while let Maybe.Some(v) = m {
        total += v
        m = Maybe.None
    }
    total
}

fn flag(b: bool) -> i32 {
    match b {
        true => 1
        false => 0
    }
}
```

### EX-10 — arrays, slices, indexing, sub-ranges, constant table
```axiom
const PRIMES: [5]u32 = [2, 3, 5, 7, 11]

fn total(xs: view<[u32]>) -> u32 {
    let mut s = 0u32
    let mut i = 0usize
    while i < len(xs) {
        s += xs[i]
        i += 1
    }
    s
}

fn main() -> u32 {
    let zeros = [0u8; 16]
    let grid: [2][3]i32 = [[1, 2, 3], [4, 5, 6]]
    let mut buf: [4]u32 = [0, 0, 0, 0]
    buf[0] = PRIMES[4]
    buf[1] = grid[1][2] as u32 + zeros[0] as u32
    let middle = PRIMES[1..4]
    let head = PRIMES[..2]
    let tail = PRIMES[3..]
    total(middle) + total(head) + total(tail) + total(buf)
}
```

### EX-11 — views, methods as free functions and in `impl`, `Self`
```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length_sq(self: view<Vec2>) -> f32 {
    self.x * self.x + self.y * self.y
}

impl Vec2 {
    fn new(x: f32, y: f32) -> Self {
        Self { x: x, y: y }
    }

    fn scale(self: mut_view<Self>, k: f32) {
        self.x *= k
        self.y *= k
    }

    fn into_tuple(self: Self) -> (f32, f32) {
        (self.x, self.y)
    }
}

fn bump(p: mut_view<Vec2>) {
    p.x += 1.0
}

fn main() {
    let mut v = Vec2.new(3.0, 4.0)
    v.scale(2.0)
    bump(v)
    let stored = view(v)
    let d = stored.length_sq()
    let m = mut_view(v)
    m.y = d
    let t = v.into_tuple()
}
```

### EX-12 — generics, `where`, generic arguments in expressions
```axiom
struct Stack<T> {
    items: Vec<T>
}

fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}

fn show_all<T, U>(first: T, second: U) -> Str
where
    T: Display + Clone,
    U: Display,
{
    first.display()
}

fn main() {
    let v = Vec<i32>.new()
    let s = Stack<i32> { items: v }
    let n = size_of<Stack<i32>>()
    let big = max<u64>(1, 2)
    let parsed = parse<u32>("42")
    let less = n < big
    let both = (n < big) == (big > n)
}
```

### EX-13 — traits, impls, associated items, supertraits, qualified call
```axiom
trait Shape {
    const SIDES: u32
    fn area(self: view<Self>) -> f32
    fn describe(self: view<Self>) -> Str {
        "shape"
    }
}

trait Named: Shape + Display {
    type Label
    fn label(self: view<Self>) -> Self.Label
}

struct Square { side: f32 }

impl Shape for Square {
    const SIDES: u32 = 4
    fn area(self: view<Self>) -> f32 {
        self.side * self.side
    }
}

impl Display for Square {
    fn display(self: view<Self>) -> Str { "square" }
}

impl Named for Square {
    type Label = Str
    fn label(self: view<Self>) -> Str { "sq" }
}

struct Wrapper<T> { inner: T }

impl<T> Shape for Wrapper<T>
where
    T: Shape,
{
    const SIDES: u32 = T.SIDES
    fn area(self: view<Self>) -> f32 {
        self.inner.area()
    }
}

fn total_area<A: Shape, B: Shape>(a: view<A>, b: view<B>) -> f32 {
    a.area() + Shape.area(b)
}
```

### EX-14 — attributes, `impl Drop`, visibility forms
```axiom
@derive(Copy, Clone, Eq)
struct Id { raw: u32 }

struct Guard {
    name: Str
}

impl Drop for Guard {
    fn drop(self: mut_view<Guard>) {
        print(self.name)
    }
}

@repr(C)
@align(16)
pub struct Header {
    @cfg(target.arch == "x86_64")
    pub size: u32
    pub size64: u64
}

@entry
fn main() {
    let g = Guard { name: "guard" }
    drop(g)
}

@inline
@cfg(target = "x86_64")
pub(package) fn fast_path() -> u32 { 1 }

@export("axiom_version") pub fn version() -> u32 { 1 }
```

### EX-15 — closures and function values
```axiom
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}

fn main() -> i32 {
    let offset = 10
    let add = |x| x + offset
    let mul = |a: i32, b: i32| -> i32 {
        a * b
    }
    let zero = || 0
    let mut total = 0
    let bump = |n: i32| { total += n }
    bump(mul(2, 3))
    let masked = add(1) | 4
    apply(|v| v * 2, masked) + zero() + total
}
```

### EX-16 — `Result`, `Option`, `?`, jumps in arms
```axiom
enum ParseError {
    Empty
    BadDigit(char)
}

fn digit(c: char) -> Result<u32, ParseError> {
    match c {
        '0'..='9' => Ok(c as u32 - '0' as u32)
        _ => Err(ParseError.BadDigit(c))
    }
}

fn first_digit(s: view<[char]>) -> Result<u32, ParseError> {
    if len(s) == 0 {
        return Err(ParseError.Empty)
    }
    let d = digit(s[0])?
    Ok(d)
}

fn or_zero(r: Result<u32, ParseError>) -> u32 {
    match r {
        Ok(v) => v
        Err(_) => return 0
    }
}

fn lookup(o: Option<u32>) -> u32 {
    if let Some(v) = o { v } else { panic("missing") }
}
```

### EX-17 — imports with groups and aliases, re-export, visibility, dotted call
```axiom
module app.config

use std.io.print
use std.collections.HashMap as Map
use std.collections.{Vec, HashSet as Set}
use std.text.{
    Str
    StringBuilder
}
pub use app.defaults.DEFAULT_PORT

pub const VERSION: Str = "0.1"
pub(package) const RETRIES: u32 = 3
pub(module) fn helper() -> u32 { RETRIES }
const PRIVATE: u32 = 1

pub fn port(overrides: view<Map<Str, u32>>) -> u32 {
    std.math.max(DEFAULT_PORT, helper())
}
```

### EX-18 — FFI, `unsafe`, raw pointers, function types
```axiom
@link("kernel32")
extern "system" {
    fn GetTickCount64() -> u64
    fn WriteFile(handle: *mut u8, buf: *const u8, len: u32, written: *mut u32, overlapped: *mut u8) -> i32
    fn ExitProcess(code: u32) -> never
}

extern "C" fn callback(x: i32) -> i32 {
    x + 1
}

@export("axiom_add")
pub extern "C" fn add(a: i32, b: i32) -> i32 { a + b }

struct Node { value: i32, next: *mut Node }

unsafe fn read(p: *const i32) -> i32 {
    *p
}

fn sum(head: *mut Node) -> i32 {
    let mut total = 0
    let mut cur = head
    unsafe {
        while !is_null(cur) {
            total += cur->value
            cur = cur->next
        }
        let first = (*head).value
        total += read(address_of(first))
    }
    total
}

fn ticks() -> u64 {
    unsafe { GetTickCount64() }
}

type Handler = extern "C" fn(i32) -> i32
type UnsafeOp = unsafe fn(*mut u8, usize)
```

### EX-19 — statics and fixed-address declarations (`@at`, ADR-0001)
```axiom
@repr(C)
struct UartRegs {
    data: Mmio<u8>
    status: MmioRO<u32>
    ctrl: Mmio<u32>
}

const TX_READY: u32 = 1 << 5

@at(0x4000_1000)
unsafe static UART0: UartRegs

@at(0x0000_0000)
unsafe static VECTORS: [3]fn() = [reset, nmi, hard_fault]

static BOOT_COUNT: u32 = 0
static mut TICKS: u64 = 0

@at(0x0800_0100)
unsafe fn reset() -> never {
    loop {}
}

fn nmi() {}
fn hard_fault() {}

@at(0xFFFF_0400)
unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32

@at(image("game.exe") + 0x1A_2B30)
unsafe extern "C" fn game_add_item(player: *mut u8, item_id: u32, count: i32) -> bool

@at(image_self() + 0x2000)
unsafe static TABLE: [256]u8

fn put(b: u8) {
    while UART0.status & TX_READY == 0 {}
    UART0.data = b
}
```

### EX-20 — aggregate constants, byte literals, `u32 as char`
```axiom
enum TokenKind { Ident, Number, Plus, Eof }

struct Keyword {
    text: Str
    kind: TokenKind
    code: u8
}

const KEYWORDS: [3]Keyword = [
    Keyword { text: "fn", kind: TokenKind.Ident, code: 1 },
    Keyword { text: "let", kind: TokenKind.Ident, code: 2 },
    Keyword {
        text: "plus"
        kind: TokenKind.Plus
        code: b'+'
    },
]

const LIMITS: (u32, u32) = (0, 0x10FFFF)
const SIZE: usize = 4 * 1024

fn kind_code(k: TokenKind) -> u8 {
    k as u8
}

fn to_char(n: u32) -> char {
    n as char
}

fn upper(c: u8) -> char {
    (c - 32) as char
}
```

### EX-21 — line continuation rules
```axiom
fn compute(a: i32, b: i32) -> i32 { a + b }

fn chain(v: view<[i32]>) -> i32 {
    let result = v
        .iter()
        .map(|x| x * 2)
        .sum()
    let long = result +
        1 +
        2
    let call = compute(
        result,
        long
    )
    let cond = if call > 0 {
        call
    }
    else {
        -call
    }
    let a = cond
    -a
}
```

### EX-22 — blocks as values, explicit `;`, empty statement
```axiom
fn side_effect(n: i32) {}

fn block_values(flag: bool) -> i32 {
    let x = {
        let a = 10
        let b = 20
        a + b
    }
    let y = if flag { x } else { 0 }
    let unit = {
        side_effect(x);
    }
    ;
    {
        let inner = y
        inner * 2
    }
}
```

### EX-23 — literals
```axiom
const NEWLINE: char = '\n'
const TAB: u8 = b'\t'
const HELLO: Str = "Xin chào thế giới"
const ESCAPED: Str = "quote \" backslash \\ unicode \u{1F600} hex \x41 braces {not} interpolation"
const RAW: Str = r"C:\dir\file"
const DATA: view<[u8]> = b"\x7fELF\x00"
const BIG: u64 = 18_446_744_073_709_551_615
const RATIO: f64 = 1.5e-3

fn literals() -> bool {
    let t = true
    let f = false
    let i = 0b1010 + 0o17 + 0xFF + 42i64 as i32
    let r = 1..2
    t && !f && i > 0
}
```

### EX-24 — function types, `dyn`
```axiom
trait Draw {
    fn draw(self: view<Self>)
}

fn render(item: view<dyn Draw>) {
    item.draw()
}

fn pick(flag: bool) -> fn(i32) -> i32 {
    if flag { double } else { negate }
}

fn double(x: i32) -> i32 { x * 2 }
fn negate(x: i32) -> i32 { -x }

struct Table {
    handlers: [2]fn(i32) -> i32
    names: (Str, Str)
    sink: view<dyn Draw + Send>
}
```

### EX-25 — generic enums, nested generics, associated-type binding
```axiom
enum Tree<T> {
    Leaf(T)
    Node(Box<Tree<T>>, Box<Tree<T>>)
}

fn depth<T>(t: view<Tree<T>>) -> u32 {
    match t {
        Tree.Leaf(_) => 1
        Tree.Node(l, r) => 1 + max<u32>(depth(l), depth(r))
    }
}

fn sum_all<I>(it: I) -> i64
where
    I: Iterator<Item = i64>
{
    let mut total = 0i64
    let mut iter = it
    while let Some(v) = iter.next() {
        total += v
    }
    total
}
```

### EX-26 — a scanner in the self-host style (stored view, labels, byte ranges)
```axiom
struct Cursor {
    src: view<[u8]>
    pos: usize
}

fn is_ident_start(b: u8) -> bool {
    match b {
        b'a'..=b'z' | b'A'..=b'Z' | b'_' => true
        _ => false
    }
}

fn skip_spaces(c: mut_view<Cursor>) {
    while c.pos < len(c.src) {
        match c.src[c.pos] {
            b' ' | b'\t' | b'\r' | b'\n' => { c.pos += 1 }
            _ => { return }
        }
    }
}

fn count_words(src: view<[u8]>) -> u32 {
    let mut cur = Cursor { src: src, pos: 0 }
    let mut words = 0u32
    'scan: loop {
        skip_spaces(cur)
        if cur.pos >= len(cur.src) {
            break 'scan
        }
        if !is_ident_start(cur.src[cur.pos]) {
            cur.pos += 1
            continue 'scan
        }
        words += 1
        while cur.pos < len(cur.src) && is_ident_start(cur.src[cur.pos]) {
            cur.pos += 1
        }
    }
    words
}
```

### EX-S1 — forms implemented after self-hosting (S1)
```axiom
async fn fetch(url: Str) -> Result<Data, NetError> {
    let response = http.get(url).await?
    Ok(response.read().await?)
}

comptime fn table_size() -> usize {
    4 * 256
}

const SIZE: usize = comptime { table_size() }
```

Construct coverage of the corpus:

| Construct | Examples |
|---|---|
| module / use / groups / alias / re-export | EX-02, EX-17 |
| `let`, `let mut`, deferred `let`, assignment, compound, shadowing | EX-03 |
| operators, precedence, casts | EX-04, EX-06, EX-23 |
| `if`, `else if`, `loop`+`break` value, `while`, `for`, ranges, labels | EX-05, EX-26 |
| functions, tuples, tuple index | EX-06 |
| structs (named, tuple, unit), struct literals, shorthand | EX-07, EX-20 |
| enums, `match`, dotted variants, `enum as uN` | EX-08, EX-20 |
| patterns (all v0.1 forms), `if let`, `while let`, `let … else` | EX-09, EX-16, EX-26 |
| arrays, `[N]T`, `view<[T]>`, repeat literal, sub-ranges | EX-10 |
| `view` / `mut_view` types and expressions, receivers, `impl`, `Self` | EX-11 |
| generics, bounds, `where`, generic arguments in expressions | EX-12, EX-25 |
| traits, impls, associated const/type, supertraits, `Trait.method(x)` | EX-13 |
| attributes (items, fields, `key = value`), `impl Drop`, visibility | EX-14, EX-17 |
| closures, function values | EX-15 |
| `?`, `Option`/`Result`, jump expressions | EX-16 |
| `extern` blocks/items, `@link`, `unsafe fn`, `unsafe { }`, `*const`/`*mut`, `->`, fn types | EX-18 |
| `static`, `static mut`, `@at` on `static` / `fn` / `extern fn` | EX-19 |
| `const` of aggregate type, byte literal, `u32 as char` | EX-20 |
| newline continuation, leading dot, `else` on a new line | EX-21 |
| block values, `;`, empty statement | EX-22 |
| literals | EX-23 |
| `dyn`, function types in fields | EX-24 |
| `async`, `.await`, `comptime` (S1) | EX-S1 |

## 12. Deliberately deferred

| Item | Why deferred | Milestone that needs it |
|---|---|---|
| Fully qualified trait paths (`<T as Trait>` equivalent) | `Trait.method(x)` and `T.Item` cover the self-host subset | T055/T056; new ADR if trait resolution needs it |
| Wider follower set for generic arguments (function values such as `id<i32>` passed as an argument) | rare; the minimal set is provably safe | T054; decide before E23.2 |
| Const generic parameters and arguments | comptime 2.0 | E14.1 (planning T214) |
| `impl Trait` in type position | not in the frozen surface | planning T214 |
| Items inside blocks (local `fn`, `const`, types) | not needed for self-hosting; resolver cost | planning T214; decide before E23.2 |
| Struct update `..base`; explicit enum discriminants | "may support" in the corpus only | E13.2 for discriminants; T214 otherwise |
| Patterns: binding-at, slice patterns, string/float literals, `..` in tuples, patterns in parameters | not needed for self-hosting | planning T214 |
| `move` closures / explicit capture lists | capture is inferred | E11.1 (spawn capture rules, planning T211) |
| `async { }` blocks, generators and `yield` | concurrency / generators | E11.4, E14.3 |
| Item-level `comptime { }`, reflection syntax | comptime 2.0 | E14.1, E14.2 |
| Glob imports, nested `use` groups | not canonical style | E20.1 (planning T220) |
| Variadic `extern` functions; more ABI strings | FFI breadth | E13.1 / E16 (planning T213, T216) |
| `union` declarations | layout control | E13.2 |
| Named and default arguments | excluded from v1 by the corpus; syntax kept free (AXS-GRM-043) | not scheduled |
| Labelled blocks | no source requires them | not scheduled |
| Attributes on statements, expressions, parameters and generic parameters | no v0.1 attribute needs them | E14.2 / E19 |
| Inline modules | file = module (ADR-0006 §7) | not scheduled |

## Sources
0152 §12; 0154; 0155; 0173 §27-33; 0174; 0243; 0084; 0109; 0151; tasks/0323; tasks/0324; tasks/0386;
tasks/0476 (frozen v1.0 surface); `spec/requirements/OWNER.md`; ADR-0001; ADR-0004 §2, §7; ADR-0006;
ADR-0007; ADR-0008; ADR-0009; ADR-0010; `.claude/skills/axiom-syntax/SKILL.md`.
