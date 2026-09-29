# BOOTSTRAP-429 — LEXICAL MODEL, SYNTAX, OPERATORS, LITERALS & FORMATTING

Task này khóa **surface syntax** của Axiom. Mục tiêu là syntax đủ hiện đại, AI-friendly, dễ parse, ít ambiguity và ánh xạ trực tiếp xuống semantic model đã khóa ở 420–428.

---

## 429.1 — Nguyên tắc syntax

Axiom ưu tiên:

```text
explicit
predictable
compact
machine-readable
human-readable
```

Không dùng syntax chỉ để làm ngôn ngữ “trông khác biệt”.

---

# 429.2 — Source encoding

Source code mặc định:

```text
UTF-8
```

Không yêu cầu BOM.

Identifier Unicode được hỗ trợ nhưng convention khuyến nghị ASCII cho API/system symbols.

---

# 429.3 — Unicode normalization

Compiler không được tự ý normalize toàn bộ source.

Identifier phải được xử lý theo một normalization policy cố định để tránh hai identifier nhìn giống nhau nhưng khác binary representation.

Khuyến nghị:

```text
Unicode NFC
```

cho identifier comparison.

String literal giữ nguyên code points/bytes theo semantic của literal.

---

# 429.4 — Newline

Compiler hỗ trợ:

```text
LF
CRLF
```

và normalize line endings trong lexical processing.

---

# 429.5 — Whitespace

Whitespace:

```text
space
tab
newline
```

thường không mang semantic.

Indentation không phải syntax bắt buộc.

---

# 429.6 — Semicolon

Axiom không bắt buộc `;` ở cuối statement.

Ví dụ:

```text
x := 10
y := 20
```

Có thể cho phép `;` như explicit statement separator:

```text
x := 10; y := 20
```

nhưng formatter mặc định không sinh chúng.

---

# 429.7 — Automatic semicolon insertion

Không nên dùng ASI kiểu phức tạp.

Parser dựa chủ yếu vào:

```text
newline
brace
token grammar
```

nhưng các trường hợp continuation phải deterministic.

---

# 429.8 — Braces

Block:

```text
{
    ...
}
```

là syntax chuẩn.

Không có indentation-sensitive grammar.

---

# 429.9 — Parentheses

Parentheses dùng cho:

```text
function parameters
grouping
tuple expressions
conditions where useful
```

Không bắt buộc:

```text
if (condition)
```

Khuyến nghị:

```text
if condition {
    ...
}
```

---

# 429.10 — Function declaration

Syntax chính:

```text
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

---

# 429.11 — Return type

Return type dùng:

```text
-> Type
```

Ví dụ:

```text
fn length(v: Vec2) -> f32
```

---

# 429.12 — No implicit return keyword requirement

Expression cuối block có thể là result:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`return` vẫn tồn tại cho early exit:

```text
if invalid {
    return 0
}
```

---

# 429.13 — Variable declaration

Axiom dùng:

```text
x := expression
```

cho inferred local.

Explicit:

```text
x: i32 = expression
```

---

# 429.14 — Immutable default

```text
x := 10
```

là immutable binding mặc định.

Mutable:

```text
mut x := 10
```

hoặc syntax tương đương được parser khóa thống nhất.

Khuyến nghị giữ `mut x`.

---

# 429.15 — Assignment

```text
x = 20
```

chỉ hợp lệ với mutable binding/storage.

---

# 429.16 — Constant

Compile-time constant:

```text
const PI: f64 = 3.141592653589793
```

`const` không phải mutable static storage.

---

# 429.17 — Static storage

```text
static counter: AtomicU64
```

là storage có lifetime toàn chương trình.

Initialization semantics theo 427.

---

# 429.18 — Function visibility

```text
pub fn foo() {}
```

Default:

```text
fn foo() {}
```

private.

---

# 429.19 — Struct syntax

```text
struct Vec2 {
    x: f32
    y: f32
}
```

---

# 429.20 — Struct construction

```text
v := Vec2 {
    x: 1.0
    y: 2.0
}
```

Field names explicit.

---

# 429.21 — Positional construction

Có thể cho phép tuple-like structs:

```text
struct Pair<T, U>(T, U)
```

nhưng ordinary structs ưu tiên named fields.

---

# 429.22 — Struct methods

Đúng theo model 426:

```text
fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Call:

```text
v.length()
```

---

# 429.23 — Mutable receiver

```text
fn normalize(mut self: Vec2) {
    ...
}
```

Exact ownership/view qualifiers sẽ được parser semantic layer xử lý theo 423.

---

# 429.24 — Trait declaration

```text
trait Drawable {
    fn draw(self)
}
```

---

# 429.25 — Trait implementation

```text
impl Drawable for Button {
    fn draw(self) {
        ...
    }
}
```

---

# 429.26 — Generic syntax

```text
fn max<T: Ordered>(a: T, b: T) -> T {
    ...
}
```

---

# 429.27 — Multiple generic parameters

```text
fn convert<T, U>(value: T) -> U {
    ...
}
```

Constraints:

```text
fn convert<T: Into<U>, U>(value: T) -> U
```

---

# 429.28 — Where clause

Complex constraints:

```text
fn process<T, U>(x: T, y: U)
where
    T: Readable + Send
    U: Writable
{
    ...
}
```

---

# 429.29 — Const generic

```text
struct Array<T, const N: usize> {
    ...
}
```

---

# 429.30 — Type alias

```text
type UserId = u64
```

Generic:

```text
type Result2<T> = Result<T, Error>
```

---

# 429.31 — Enum syntax

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

---

# 429.32 — Unit variant

```text
enum State {
    Ready
    Running
    Finished
}
```

---

# 429.33 — Named enum payload

```text
enum Message {
    Data {
        id: u64
        value: String
    }
    Error {
        code: i32
    }
}
```

---

# 429.34 — Tuple enum payload

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

---

# 429.35 — Pattern syntax

```text
match result {
    Ok(value) => value
    Err(error) => handle(error)
}
```

---

# 429.36 — Match arm separator

Newline separates arms.

Optional comma/semicolon should not be necessary.

This keeps patterns readable.

---

# 429.37 — Wildcard

```text
_ => default_value
```

---

# 429.38 — OR pattern

```text
0 | 1 | 2 => small()
```

---

# 429.39 — Range pattern

```text
0..10 => ...
```

Meaning remains `[0,10)`.

Inclusive:

```text
0..=10
```

---

# 429.40 — Guard

```text
Some(x) if x > 10 => ...
```

---

# 429.41 — Function call

```text
foo(a, b)
```

No special distinction between static function and method at lexical level.

---

# 429.42 — Method call

```text
object.method(a)
```

is syntax sugar for struct-first function invocation.

---

# 429.43 — Generic call

Axiom needs an unambiguous generic argument syntax.

Recommended:

```text
foo::<i32>(value)
```

when explicit generic arguments are required.

Normal code can infer:

```text
foo(value)
```

---

# 429.44 — Why `::<T>`

Using:

```text
foo<T>(x)
```

can create parser ambiguity with comparison operators in some grammar contexts.

Therefore:

```text
foo::<T>(x)
```

is preferred for explicit function generic arguments.

---

# 429.45 — Generic type construction

Type syntax remains:

```text
Array<i32, 16>
Result<String, Error>
Map<String, User>
```

---

# 429.46 — Generic method

```text
fn convert<T>(self: Value) -> T {
    ...
}
```

---

# 429.47 — Trait generic

```text
trait Convert<T> {
    fn convert(self) -> T
}
```

---

# 429.48 — Associated type

```text
trait Iterator {
    type Item
    fn next(self) -> Option<Self::Item>
}
```

---

# 429.49 — Associated constant

```text
trait Numeric {
    const ZERO: Self
}
```

---

# 429.50 — `Self`

Inside trait:

```text
Self
```

means implementing type.

Outside trait, it has no implicit meaning.

---

# 429.51 — Self associated type

```text
type Output = Self
```

is valid where type semantics permit.

---

# 429.52 — Trait qualification

When ambiguity exists:

```text
<T as Iterator>::Item
```

or a simpler Axiom equivalent may be introduced.

Recommended to retain this explicit form because it is machine-readable.

---

# 429.53 — Trait method qualification

```text
Drawable::draw(x)
```

can force a specific trait implementation.

This is useful when multiple capabilities provide same method name.

---

# 429.54 — Interface syntax

Dynamic interface:

```text
dyn Drawable
```

Example:

```text
fn render(x: dyn Drawable) {
    x.draw()
}
```

---

# 429.55 — Owned dynamic interface

```text
Box<dyn Drawable>
```

or equivalent owned container.

`dyn` itself does not imply ownership.

---

# 429.56 — Array

```text
[i32; 16]
```

means fixed-size array.

---

# 429.57 — Slice

```text
[]i32
```

means dynamically sized view/sequence abstraction.

Conceptual representation derives from 422.

---

# 429.58 — String

Axiom standard text type:

```text
String
```

UTF-8.

String literal:

```text
"hello"
```

---

# 429.59 — Raw byte string

For binary data:

```text
b"hello"
```

produces bytes rather than Unicode string semantics.

---

# 429.60 — Character literal

A character literal represents a Unicode scalar value:

```text
'a'
'Đ'
'中'
```

Its type:

```text
char
```

not UTF-8 byte.

---

# 429.61 — Escape sequences

Support:

```text
\n
\r
\t
\\
\"
\'
\xNN
\u{NNNN}
```

`\u{...}` is preferred for Unicode code points.

---

# 429.62 — Raw strings

Long prompts/data:

```text
r"raw text"
```

should avoid excessive escaping.

Multiline raw syntax can be supported:

```text
r"""
...
"""
```

---

# 429.63 — Multiline string

```text
"""
line 1
line 2
"""
```

Formatting semantics must preserve intended newline content.

---

# 429.64 — Integer literals

Supported bases:

```text
123
0b1010
0o755
0xFF
```

---

# 429.65 — Digit separators

Readable numeric constants:

```text
1_000_000
0xFF_FF
```

underscores ignored semantically.

---

# 429.66 — Integer suffix

Explicit type:

```text
42i32
42u64
```

---

# 429.67 — Floating literals

```text
3.14
1.0e-5
```

Suffix:

```text
3.14f32
```

---

# 429.68 — Boolean literals

```text
true
false
```

---

# 429.69 — Null absence

Không có:

```text
null
nil
```

trong ordinary safe type semantics.

Dùng:

```text
Option<T>
```

---

# 429.70 — Unit value

Một function không trả meaningful value có thể dùng:

```text
void
```

hoặc `Unit`.

Khuyến nghị core canonical type là:

```text
unit
```

với syntax return:

```text
fn log(x: String) {
    ...
}
```

implicit return type `unit`.

---

# 429.71 — Never

Diverging function:

```text
fn abort_now() -> never
```

`never` là bottom/diverging type.

---

# 429.72 — Pointer syntax

Pointer là low-level feature:

```text
*const T
*mut T
```

hoặc equivalent canonical form.

Pointer syntax phải visually khác safe views.

---

# 429.73 — Unsafe block

```text
unsafe {
    ...
}
```

Raw pointer operations yêu cầu unsafe context khi semantic cần.

---

# 429.74 — Unsafe function

```text
unsafe fn read_raw(...)
```

Call site phải nằm trong unsafe context.

---

# 429.75 — Address-of

```text
&x
```

tạo address/view tùy context.

Compiler semantic phase quyết định representation.

---

# 429.76 — Dereference

```text
*ptr
```

là low-level operation.

Unsafe nếu pointer validity không được compiler đảm bảo.

---

# 429.77 — Reference/view syntax

Do Axiom muốn tránh pointer/reference complexity, syntax safe view nên rõ ràng:

```text
view T
```

ví dụ:

```text
fn print(x: view String)
```

Thay vì bắt programmer phân biệt nhiều loại `&T`, `&mut T`, lifetime annotations.

Exact ownership/view syntax sẽ được khóa cùng task 430 memory syntax integration nếu cần.

---

# 429.78 — Operators

Arithmetic:

```text
+
-
*
/
%
```

Comparison:

```text
==
!=
<
<=
>
>=
```

Logical:

```text
&&
||
!
```

Bitwise:

```text
&
|
^
~
<<
>>
```

---

# 429.79 — Assignment operators

```text
=
+=
-=
*=
/=
%=
&=
|=
^=
<<=
>>=
```

---

# 429.80 — Range operators

```text
a..b
a..=b
```

---

# 429.81 — Pipe operator

Không đưa pipe operator vào core nếu không có semantic necessity.

Function/method composition có thể được viết rõ ràng.

---

# 429.82 — Optional chaining

Không cần:

```text
x?.foo()
```

nếu muốn giữ core nhỏ.

`Option` + pattern matching/propagation đã cung cấp semantic đầy đủ.

Một convenience operator có thể được thêm ở standard syntax layer sau này mà không thay đổi core IR.

---

# 429.83 — Null-coalescing

Không cần:

```text
x ?? default
```

trong core.

Có thể xây từ Option API.

---

# 429.84 — Operator precedence

Precedence từ cao xuống thấp:

```text
postfix/call/index
unary
multiplicative
additive
shift
bitwise &
bitwise ^
bitwise |
comparison
equality
logical &&
logical ||
range
assignment
```

Assignment thấp nhất.

---

# 429.85 — Chained comparison

Không tự động coi:

```text
a < b < c
```

là:

```text
a < b && b < c
```

Nếu cần viết:

```text
a < b && b < c
```

để semantic rõ ràng.

---

# 429.86 — Operator overload

Operator mapping:

```text
a + b
```

→ `Add`.

```text
a == b
```

→ equality capability.

Primitive operators có compiler intrinsic implementation.

---

# 429.87 — No implicit arithmetic promotion

Không tự động biến:

```text
i32 + f64
```

thành một type tùy ý.

Programmer phải explicit convert.

Điều này tránh precision surprise và generic ambiguity.

---

# 429.88 — Cast

Syntax:

```text
x as f64
```

cho explicit conversion.

---

# 429.89 — Bitcast

Low-level representation conversion:

```text
bitcast<f32>(bits)
```

hoặc intrinsic equivalent.

Không nhầm với numeric cast.

---

# 429.90 — Comments

Single-line:

```text
// comment
```

Multi-line:

```text
/*
    comment
*/
```

---

# 429.91 — Documentation comment

```text
/// Vector length.
fn length(...)
```

Compiler có thể đưa documentation vào interface metadata.

---

# 429.92 — Attributes

Syntax thống nhất:

```text
@inline
@repr(C)
@deprecated("...")
@no_panic
```

Attributes là metadata, không nên tạo hidden runtime behavior trừ khi attribute explicitly định nghĩa điều đó.

---

# 429.93 — Attribute arguments

```text
@repr(align(16))
```

Nested attribute arguments được parser xử lý như structured metadata.

---

# 429.94 — Compiler directives

Directive compiler-specific nên có namespace:

```text
@compiler(...)
@target(...)
```

để không nhầm với language semantics.

---

# 429.95 — Module syntax

File module:

```text
module math.vector
```

Imports:

```text
import math.vector.Vector
```

Exports:

```text
pub fn length(...)
```

---

# 429.96 — Package declaration

Root project metadata chứa package identity.

Không cần lặp:

```text
package ...
```

trong mọi source file.

---

# 429.97 — Formatting

Axiom nên có formatter canonical:

```text
axiom fmt
```

Formatter quyết định:

```text
indentation
line breaks
spacing
brace placement
import ordering
```

---

# 429.98 — Formatter stability

Invariant:

```text
fmt(fmt(source)) == fmt(source)
```

Formatter phải idempotent.

---

# 429.99 — Canonical formatting

Khuyến nghị:

```text
4 spaces
no tabs for indentation
K&R-style braces
one declaration per line
```

Ví dụ:

```text
fn distance(a: Vec2, b: Vec2) -> f32 {
    dx := a.x - b.x
    dy := a.y - b.y

    sqrt(dx * dx + dy * dy)
}
```

---

# 429.100 — Import formatting

Canonical:

```text
import core.math
import core.string
import graphics.image
```

Có thể group theo package.

---

# 429.101 — No formatter semantic changes

Formatter không được:

```text
rename symbols
change inferred types
insert conversions
change ownership
```

Nó chỉ thay đổi presentation.

---

# 429.102 — Lexer token categories

Lexer canonical categories:

```text
identifier
keyword
integer
float
char
string
operator
punctuation
attribute
comment
newline
EOF
```

---

# 429.103 — Keywords

Core keyword set nên nhỏ:

```text
fn
struct
enum
trait
impl
type
const
static
let / := syntax
mut
pub
import
module
match
if
else
for
in
while
loop
break
continue
return
defer
unsafe
async
await
true
false
self
Self
dyn
where
as
```

Không reserve hàng trăm từ chỉ vì tương lai có thể cần.

---

# 429.104 — Contextual keywords

Một số từ có thể là contextual keyword nếu grammar cho phép.

Mục tiêu là tránh breaking source quá lớn khi language evolution.

---

# 429.105 — Identifier

Identifier:

```text
[A-Za-z_][A-Za-z0-9_]*
```

và Unicode extension.

Không cho identifier bắt đầu bằng digit.

---

# 429.106 — Naming convention

Compiler không enforce style, formatter/tooling có thể khuyến nghị:

```text
TypeName
function_name
field_name
CONSTANT_NAME
```

---

# 429.107 — Reserved prefix

Compiler-generated names nên dùng namespace/prefix không thể xung đột với ordinary user identifier.

Ví dụ internal mang tính compiler-only.

---

# 429.108 — Macro/token future compatibility

Lexer phải giữ source span chính xác cho từng token để sau này hỗ trợ macro/compile-time transformation.

---

# 429.109 — Source spans

Mọi AST node quan trọng phải có:

```text
file_id
start_offset
end_offset
line
column
```

hoặc compact equivalent.

---

# 429.110 — Error recovery

Lexer/parser phải tạo diagnostics như:

```text
unexpected token
unterminated string
invalid numeric literal
invalid escape
missing '}'
```

với source span chính xác.

---

# 429.111 — AI-friendly syntax principle

Compiler error:

```text
expected `)`
found `}`
```

không đủ tốt.

Nên cung cấp machine-readable:

```text
code: E429021
expected: closing_paren
found: closing_brace
span: ...
suggestion: ...
```

---

# 429.112 — Syntax examples

Một đoạn Axiom tổng hợp:

```text
module math.vector

pub struct Vec2 {
    x: f32
    y: f32
}

pub fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}

pub trait Add<Rhs> {
    type Output
    fn add(self, rhs: Rhs) -> Self::Output
}

impl Add<Vec2> for Vec2 {
    type Output = Vec2

    fn add(self, rhs: Vec2) -> Vec2 {
        Vec2 {
            x: self.x + rhs.x
            y: self.y + rhs.y
        }
    }
}

pub fn example<T: Add<T>>(a: T, b: T) -> T {
    a + b
}
```

Đây là syntax có thể parse thành AST mà không cần class/object hierarchy.

---

# 429.113 — Syntax philosophy

Axiom không cố gắng loại bỏ mọi syntax.

Thay vào đó:

```text
simple syntax
+
rich semantic system
```

để tránh tình trạng core quá nghèo khiến library/API trở nên phức tạp.

---

# 429.114 — Parser architecture

Khuyến nghị:

```text
Lexer
  ↓
Token stream
  ↓
Recursive-descent parser
  +
Pratt expression parser
  ↓
AST
```

Pratt parser phù hợp với operator precedence và expression-oriented design.

---

# 429.115 — Parser determinism

Cùng token stream phải tạo cùng AST.

Không có parser behavior phụ thuộc:

```text
compiler thread timing
filesystem order
hash iteration
```

---

# 429.116 — AST không phải IR

AST giữ source structure.

IR giữ executable semantics.

Không dùng AST trực tiếp làm backend representation.

---

# 429.117 — Syntax sugar lowering

Các syntax sugar như:

```text
x.foo()
a..b
for x in items
```

được lower semantic trước IR.

Backend không cần biết syntax sugar tồn tại.

---

# 429.118 — Conformance tests

429 phải có:

```text
LEX-001 UTF8
LEX-002 identifiers
LEX-003 unicode identifiers
LEX-004 integers
LEX-005 floats
LEX-006 strings
LEX-007 escapes
LEX-008 comments
LEX-009 attributes

PARSE-001 functions
PARSE-002 structs
PARSE-003 enums
PARSE-004 traits
PARSE-005 impl
PARSE-006 generics
PARSE-007 const generics
PARSE-008 match
PARSE-009 patterns
PARSE-010 operators
PARSE-011 async
PARSE-012 unsafe

FMT-001 canonical format
FMT-002 idempotence
FMT-003 import formatting
FMT-004 source preservation
```

---

# 429.119 — Hard invariants

1. UTF-8 mặc định.
2. Không indentation-sensitive.
3. Braces xác định block.
4. `;` không bắt buộc.
5. Expression-oriented.
6. Inferred local dùng `:=`.
7. Immutable mặc định.
8. `mut` explicit.
9. Struct không có class semantics.
10. Method = function với receiver đầu tiên.
11. Trait/generic syntax rõ ràng.
12. Explicit generic call dùng `::<T>`.
13. `dyn Trait` biểu diễn dynamic interface.
14. `Option` thay cho implicit null.
15. `Result` là failure value.
16. Không implicit numeric promotion.
17. `as` là explicit conversion.
18. Unsafe operations được đánh dấu rõ.
19. Pattern matching là core.
20. Operator semantics có thể map qua traits.
21. Parser deterministic.
22. AST tách khỏi IR.
23. Formatter canonical và idempotent.
24. Source spans đầy đủ.
25. Diagnostics machine-readable.
26. Syntax surface không chứa unnecessary historical complexity.

**BOOTSTRAP-429 hoàn tất.**

---

# BOOTSTRAP-430 — TYPE SYSTEM, INFERENCE, COERCION, CASTING & TYPE CHECKING

429 đã khóa cách **viết** type; 430 khóa cách compiler **hiểu type**.

Đây là một trong những task quan trọng nhất của Axiom, vì mục tiêu là đạt:

```text
C/C++ performance
+
modern type safety
-
GC
-
mandatory borrow checker
-
implicit runtime type machinery
```

## 430.1 — Type-system goals

```text
430.1    type-system goals
430.2    primitive types
430.3    integer types
430.4    floating types
430.5    bool
430.6    char
430.7    unit
430.8    never
430.9    arrays
430.10   slices/views
430.11   structs
430.12   enums
430.13   tuples
430.14   function types
430.15   closures
430.16   pointers
430.17   dynamic interfaces
430.18   generic types
430.19   associated types
430.20   aliases
430.21   nominal typing
430.22   structural typing
430.23   type identity
430.24   inference
430.25   local inference
430.26   generic inference
430.27   return inference
430.28   numeric inference
430.29   coercion
430.30   conversion
430.31   casts
430.32   bitcasts
430.33   literals
430.34   type compatibility
430.35   assignment compatibility
430.36   function compatibility
430.37   variance
430.38   subtyping
430.39   trait satisfaction
430.40   overload resolution
430.41   method resolution
430.42   ambiguity
430.43   recursive types
430.44   opaque types
430.45   type erasure
430.46   compile-time type queries
430.47   layout queries
430.48   type identity
430.49   diagnostics
430.50   type-checking pipeline
430.51   optimization interaction
430.52   conformance tests
430.53   final type-system contract
```

### 430.1 — Nominal typing là mặc định

Axiom nên dùng **nominal identity** cho:

```text
struct
enum
trait
```

Hai struct có cùng fields vẫn là hai type khác nhau:

```text
struct Meter {
    value: f64
}

struct Second {
    value: f64
}
```

Không được tự động coi `Meter == Second`.

Điều này rất quan trọng để tránh nhầm đơn vị và semantic type.

---

### 430.2 — Structural typing chỉ ở nơi phù hợp

Structural compatibility có thể dùng cho:

```text
tuple
anonymous function signatures
compile-time patterns
```

nhưng không biến ordinary structs thành structural types.

---

### 430.3 — Primitive types

Core:

```text
bool
char
unit
never

i8   i16   i32   i64
u8   u16   u32   u64
isize
usize

f16
f32
f64
```

Có thể bổ sung:

```text
i128
u128
```

nhưng không nên bắt backend nào cũng có native instruction cho chúng.

---

### 430.4 — `usize` / `isize`

Dùng cho:

```text
index
length
pointer-sized values
allocation sizes
```

kích thước phụ thuộc target.

---

### 430.5 — Integer literal inference

```text
x := 10
```

không nhất thiết mặc định cứng `i32` trong mọi context.

Compiler infer dựa trên expected type khi có thể.

Nếu không có context, Axiom cần một default numeric policy deterministic.

Khuyến nghị:

```text
integer → i32
float   → f64
```

ở ordinary unconstrained context.

---

### 430.6 — Explicit integer conversion

```text
x as u64
```

là explicit.

Compiler không tự chuyển:

```text
i32 → i64
```

trong generic arithmetic chỉ vì “type lớn hơn”.

---

### 430.7 — Safe narrowing

```text
u64 as u8
```

phải có semantics được định nghĩa rõ.

Có thể:

```text
wrapping cast
checked conversion
saturating conversion
```

thông qua explicit APIs/operators.

Không để programmer đoán.

---

### 430.8 — Numeric conversion

Khuyến nghị phân biệt:

```text
as
try_as
bitcast
```

về semantic.

---

### 430.9 — Boolean conversion

Không có:

```text
i32 → bool
pointer → bool
```

implicit.

---

### 430.10 — Pointer conversion

Raw pointer conversions thuộc unsafe domain nếu chúng có thể phá validity/alignment.

---

### 430.11 — Function types

Ví dụ:

```text
fn(i32, i32) -> i32
```

là function type.

Function pointer không chứa hidden environment.

---

### 430.12 — Closure type

Closure có anonymous concrete type.

Nếu:

```text
fn apply<F: Callable>(f: F)
```

compiler biết concrete closure type.

Nếu dynamic:

```text
dyn Callable
```

thì dùng interface representation.

---

### 430.13 — Array type

```text
[i32; 16]
```

là type với size compile-time known.

---

### 430.14 — Slice/view type

```text
[]i32
```

là view/sequence abstraction, không phải owning array.

---

### 430.15 — Struct layout

Type checker phải chuyển type → layout query khi cần:

```text
sizeof(T)
alignof(T)
offsetof(T, field)
```

như 422.

---

### 430.16 — Enum type

Enum là nominal type.

Discriminant/payload layout được compiler quyết định theo representation rules.

---

### 430.17 — Tuple

```text
(i32, f32, bool)
```

là anonymous product type.

Hai tuple cùng sequence type tương thích.

---

### 430.18 — Type alias

```text
type UserId = u64
```

không tạo nominal type mới.

Do đó:

```text
UserId
```

và:

```text
u64
```

cùng type identity.

Nếu muốn type riêng:

```text
struct UserId {
    value: u64
}
```

---

### 430.19 — Generic identity

```text
Array<i32, 4>
Array<f32, 4>
```

là các concrete types khác nhau.

---

### 430.20 — Type constructor

Compiler semantic model nên xem:

```text
Array<T, N>
```

là type constructor được instantiate thành concrete type.

---

### 430.21 — Type inference

Inference hoạt động mạnh ở local scope:

```text
x := 10
y := x + 20
```

Compiler infer:

```text
x: i32
y: i32
```

---

### 430.22 — Không infer quá xa

Public API nên yêu cầu explicit types khi inference không ổn định.

Ví dụ public function:

```text
pub fn parse(...)
```

return type nên explicit.

Điều này làm ABI/API predictable.

---

### 430.23 — Generic inference

```text
max(a, b)
```

compiler infer:

```text
T = type(a)
```

và kiểm tra:

```text
type(b) == T
```

hoặc constraint-compatible.

---

### 430.24 — Return type inference

Private/local function có thể cho phép infer return type.

Public exported function nên khuyến nghị hoặc bắt buộc explicit return type.

---

### 430.25 — Constraint inference

Nếu:

```text
fn foo<T: Add<T>>(x: T)
```

compiler có thể infer implementation từ T.

Không cần programmer chỉ rõ trait implementation.

---

### 430.26 — Bidirectional type checking

Compiler nên dùng:

```text
synthesis
+
checking
```

Ví dụ:

```text
x := expression
```

→ synthesize type.

Còn:

```text
let x: i32 = expression
```

→ check expression against `i32`.

Đây là architecture tốt cho inference mà không cần hệ thống type inference quá phức tạp.

---

### 430.27 — Expected type propagation

Ví dụ:

```text
x: f64 = 1
```

literal `1` được check trong context `f64`.

Không cần tạo temporary `i32` rồi cast.

---

### 430.28 — Generic expected type

```text
x: Result<String, Error> = Ok("hello")
```

compiler infer:

```text
T = String
E = Error
```

từ expected type.

---

### 430.29 — Coercion

Axiom phải **hạn chế implicit coercion**.

Có thể cho phép các coercion an toàn như:

```text
array → view/slice
concrete closure → compatible callable view
T → dyn Trait
```

khi semantic rõ ràng.

---

### 430.30 — No arbitrary coercion chain

Compiler không tìm:

```text
A → B → C → D
```

để làm call compile được.

Điều này tránh ambiguity và compile-time explosion.

---

### 430.31 — One-step coercion

Nếu coercion được phép, tối đa một conversion step implicit trong một context.

Các conversion phức tạp phải explicit.

---

### 430.32 — Concrete → dynamic interface

Được phép trong context:

```text
dyn Drawable
```

từ:

```text
Button
```

compiler tạo interface representation.

---

### 430.33 — Dynamic interface → concrete

Không implicit.

Phải dùng explicit downcast/type test nếu RTTI/type identity được bật.

---

### 430.34 — Trait satisfaction

`T: Trait` đúng khi compiler tìm thấy một implementation hợp lệ.

Resolution phải deterministic.

---

### 430.35 — Orphan/coherence check

Type checker tích hợp coherence rules từ 426.

Không chấp nhận conflicting implementations.

---

### 430.36 — Method resolution

Compiler:

```text
x.foo()
```

resolve:

```text
inherent method
→ trait method
→ extension
```

theo rules 426/429.

---

### 430.37 — Overload resolution

Axiom có thể hỗ trợ function overloading có giới hạn:

```text
fn print(i32)
fn print(String)
```

Nhưng không cho overload dựa chỉ trên return type.

---

### 430.38 — Generic overload

Generic và concrete overload có thể cùng tồn tại:

```text
fn foo(i32)
fn foo<T>(T)
```

Resolution phải có specificity ordering deterministic.

Không được tạo “magic ranking” quá phức tạp.

---

### 430.39 — Ambiguous overload

Nếu:

```text
foo(x)
```

match nhiều candidate tương đương:

```text
AMBIGUOUS_CALL
```

Compiler không tự đoán.

---

### 430.40 — Trait overload ambiguity

Nếu hai traits cung cấp:

```text
foo()
```

và cả hai đều applicable:

```text
x.foo()
```

→ ambiguity.

Có thể disambiguate:

```text
TraitA::foo(x)
```

---

### 430.41 — Subtyping

Axiom không có general class subtyping.

Các subtype relationships được giới hạn ở:

```text
dyn Trait
```

và các compiler-defined coercion.

---

### 430.42 — Variance

Generics mặc định **invariant**.

Không tự động suy ra covariance/contravariance cho mutable containers.

Đây là lựa chọn an toàn và dễ reason.

---

### 430.43 — Read-only views

Một số immutable view types có thể có covariance-like behavior nếu compiler chứng minh an toàn.

Nhưng không cần expose variance annotations trong v0 core.

---

### 430.44 — Recursive types

Direct recursive value:

```text
struct Node {
    next: Node
}
```

không có finite size → error.

Phải dùng indirection:

```text
struct Node {
    next: *mut Node
}
```

hoặc owning container:

```text
next: Box<Node>
```

---

### 430.45 — Recursive enum

Compiler có thể hỗ trợ recursive enum thông qua implicit/explicit indirection tùy type design, nhưng v0 nên yêu cầu explicit indirection để layout predictable.

---

### 430.46 — Opaque type

Library có thể export:

```text
opaque type Handle
```

client biết type identity nhưng không biết internal layout.

Điều này hữu ích cho ABI/API stability.

---

### 430.47 — Private fields

```text
pub struct User {
    id: u64
}
```

Struct public nhưng field private.

Client phải dùng API public.

---

### 430.48 — Type abstraction boundary

Public interface metadata cần expose:

```text
type identity
size/alignment nếu ABI yêu cầu
public methods
traits
```

Private representation không cần expose.

---

### 430.49 — Compile-time type query

Core compiler cung cấp:

```text
sizeof<T>()
alignof<T>()
```

và:

```text
is_same<T, U>
implements<T, Trait>
```

hoặc equivalent intrinsic.

---

### 430.50 — Type equality

Nominal type identity:

```text
T == U
```

nếu canonical type identity giống nhau.

Aliases được canonicalize.

---

### 430.51 — Layout equality

Hai type có cùng layout **không có nghĩa** chúng cùng type.

Ví dụ:

```text
Meter
Second
```

có thể đều 8 bytes nhưng semantic khác nhau.

---

### 430.52 — ABI compatibility

Type checker phải có khả năng query:

```text
ABI representation
```

để FFI validator phát hiện mismatch.

---

### 430.53 — `repr(C)`

`@repr(C)` thay đổi layout/ABI representation nhưng không thay đổi nominal type identity.

---

### 430.54 — Packed types

`@repr(packed)` có thể tạo unaligned fields.

Access tới packed field phải được compiler xử lý đúng; reference/view tới unaligned field có thể bị cấm.

---

### 430.55 — Alignment

Compiler kiểm tra:

```text
alignof(T)
```

và pointer/reference alignment requirements.

Unsafe code chịu trách nhiệm nếu bypass.

---

### 430.56 — Integer overflow

Type checker phân biệt static constant evaluation và runtime arithmetic.

Ví dụ constant:

```text
const x: u8 = 300
```

→ compile-time error nếu không có explicit wrapping semantics.

---

### 430.57 — Runtime overflow

Operations có semantics đã khóa ở 422:

```text
checked
wrapping
saturating
```

Operator mặc định phải được chọn một cách rõ ràng.

Khuyến nghị debug/release có thể khác strategy kiểm tra nhưng **không được làm thay đổi language-level result một cách âm thầm**.

---

### 430.58 — Floating semantics

`f32/f64` theo IEEE-754 representation đã khóa ở 422.

Compiler được phép tối ưu nhưng không được tùy tiện biến:

```text
NaN
-0
infinity
```

thành semantics khác nếu không có fast-math flag explicit.

---

### 430.59 — Fast math

Có thể:

```text
@fast_math
```

hoặc build flag.

Đây là explicit contract cho phép optimizer thay đổi floating-point assumptions.

---

### 430.60 — Generic arithmetic

Nếu:

```text
fn add<T: Add<T>>(a: T, b: T)
```

compiler dispatch tới trait implementation.

Primitive specializations có thể được intrinsic hóa.

---

### 430.61 — Type-directed operator resolution

`a + b`:

```text
1. determine type(a)
2. determine type(b)
3. resolve Add implementation
4. determine Output
5. type-check result
```

---

### 430.62 — Conversion trait resolution

`x as T` không dùng overload resolution arbitrary.

Explicit conversion phải resolve theo conversion rules/compiler intrinsic.

Điều này tránh `as` trở thành một “magic universal operator”.

---

### 430.63 — Generic recursion

Compiler phải phát hiện:

```text
Foo<Foo<Foo<...>>>
```

vượt depth giới hạn.

---

### 430.64 — Type normalization

Compiler cần normalize:

```text
type aliases
associated types
generic substitutions
trait projections
```

trước khi so sánh type trong nhiều trường hợp.

---

### 430.65 — Projection

Ví dụ:

```text
T::Item
```

phải resolve associated type dựa trên trait implementation.

Nếu compiler không thể resolve tại compile time → diagnostic.

---

### 430.66 — Higher-kinded types

Không đưa HKT vào core v0.

Generics thường:

```text
T
```

và associated types đã đủ cho phần lớn library architecture.

Có thể mở rộng sau mà không phá generic ABI.

---

### 430.67 — Type-level arithmetic

Không cho arbitrary type-level programming trong core.

Const generics chỉ nên hỗ trợ tập giá trị rõ ràng:

```text
integer
bool
char
enum constants
```

---

### 430.68 — Type inference termination

Inference phải có giới hạn và termination guarantee.

Không để một expression làm compiler chạy vô hạn vì constraint recursion.

---

### 430.69 — Type-checking phases

Recommended pipeline:

```text
parse
 ↓
name resolution
 ↓
declaration collection
 ↓
type skeleton
 ↓
generic/trait resolution
 ↓
expression checking
 ↓
ownership checking
 ↓
constant evaluation
 ↓
layout
 ↓
lowering
```

---

### 430.70 — Declaration-first analysis

Compiler nên collect declarations trước khi check bodies để cho phép:

```text
fn A() → B()
fn B() → A()
```

trong cùng module mà không phụ thuộc source order.

---

### 430.71 — Body dependency

Sau declaration collection, compiler xây semantic dependency graph để xử lý function/type bodies.

---

### 430.72 — Public API checking

Public declaration phải được kiểm tra:

```text
generic visibility
trait visibility
type visibility
field visibility
ABI validity
```

Ví dụ public function không được expose private type trong public signature trừ khi opaque mechanism cho phép.

---

### 430.73 — Private type leakage

```text
struct Secret {}

pub fn get_secret() -> Secret
```

phải bị reject nếu `Secret` không public/opaque appropriately.

---

### 430.74 — Generic visibility leakage

```text
pub fn foo<T: PrivateTrait>(x: T)
```

không hợp lệ nếu external caller không thể satisfy/see `PrivateTrait`.

---

### 430.75 — Trait visibility

Một public trait implementation có thể yêu cầu trait/type public theo package boundary.

Compiler kiểm tra API consistency.

---

### 430.76 — Type checking + ownership

Type checker không tách hoàn toàn khỏi ownership.

Ví dụ method:

```text
fn consume(self: Resource)
```

sẽ consume value.

Call:

```text
r.consume()
r.consume()
```

→ second call invalid.

---

### 430.77 — Move-aware type checking

Compiler state phải track:

```text
initialized
owned
moved
borrowed/viewed
destroyed
```

theo 423.

---

### 430.78 — Generic ownership

Generic `T` phải preserve ownership semantics.

Compiler không được giả định:

```text
T = Copy
```

nếu constraint không đảm bảo.

---

### 430.79 — Trait-derived Copy

Nếu:

```text
T: Copy
```

compiler có thể duplicate value theo Copy semantics.

Nếu không:

```text
x2 := x1
```

là move.

---

### 430.80 — Drop-aware typing

Generic local:

```text
x: T
```

cần drop glue nếu `T` có destructor.

Specialization có thể loại bỏ drop code nếu `T` trivial.

---

### 430.81 — Type checking + concurrency

`spawn(fn() { ... })` phải kiểm tra closure environment:

```text
captured values
Send
ownership
lifetime
```

theo 424.

---

### 430.82 — Dynamic interface safety

`dyn Trait` phải kiểm tra object safety.

Trait có generic method không object-safe sẽ không được chuyển thành dynamic interface nếu method đó cần unavailable runtime information.

---

### 430.83 — Type erasure boundary

Khi:

```text
Concrete → dyn Trait
```

compiler tạo explicit erasure boundary.

Sau boundary, chỉ operations trong trait contract được phép.

---

### 430.84 — Downcast

Downcast là explicit:

```text
if x is Button {
    ...
}
```

hoặc API tương đương.

Không tự động downcast.

---

### 430.85 — RTTI optional

Nếu binary không yêu cầu:

```text
TypeId
reflection
downcast
```

compiler không emit runtime type metadata.

---

### 430.86 — Type diagnostics

Ví dụ:

```text
cannot add `Vec2` and `String`

required:
    Add<String>

found:
    no matching implementation
```

Diagnostic phải chỉ ra **constraint failure**, không chỉ nói “type mismatch”.

---

### 430.87 — Generic diagnostics

```text
T does not satisfy `Serializable`

required by:
    save<T>

at:
    foo.ax:42
```

---

### 430.88 — Candidate diagnostics

Khi overload ambiguity:

```text
ambiguous call to `foo`

candidate 1:
    foo(i32)

candidate 2:
    foo<T: Numeric>(T)
```

Compiler không tự chọn.

---

### 430.89 — Error codes

Type errors có namespace:

```text
E430xxx
```

để IDE/AI có thể xử lý programmatically.

---

### 430.90 — Fix-it suggestions

Compiler có thể đề xuất:

```text
consider `as f64`
consider importing `math.Vector`
add trait bound `T: Clone`
```

Nhưng suggestion không tự động sửa source trong compiler core.

---

### 430.91 — Type-check cache

Semantic result có thể cache theo:

```text
source fingerprint
dependency interface fingerprints
compiler version
target configuration
```

kế thừa 427.

---

### 430.92 — Type-check parallelism

Independent modules/type bodies có thể được check song song.

Compiler phải tránh global mutable semantic state.

---

### 430.93 — Type representation

Compiler internal type representation nên canonicalize:

```text
Primitive
Tuple
Array
Slice
Struct
Enum
Function
Pointer
GenericParam
GenericInstance
TraitObject
Opaque
Never
Unit
```

---

### 430.94 — Interned types

Equivalent canonical types có thể được intern để:

```text
pointer equality
fast comparison
lower memory
```

trong compiler.

Đây là compiler implementation detail, không phải language runtime.

---

### 430.95 — Type identity hash

Mỗi canonical type có stable semantic hash để:

```text
generic cache
incremental compilation
ABI validation
AI metadata
```

---

### 430.96 — Optimization interaction

Type system phải cung cấp compiler facts cho optimizer:

```text
type size
alignment
copy/drop properties
trait implementation
constant values
alias assumptions
```

Nhưng type checker không được tự thêm `noalias` nếu semantic contract không cho phép.

---

### 430.97 — Zero-cost principle

Nếu generic/trait usage có thể resolve compile-time:

```text
no runtime type check
no runtime generic metadata
no vtable
no heap allocation
```

trừ khi programmer/API semantics yêu cầu.

---

### 430.98 — Conformance tests

```text
TYPE-001 primitive types
TYPE-002 nominal structs
TYPE-003 aliases
TYPE-004 enums
TYPE-005 tuples
TYPE-006 arrays
TYPE-007 slices
TYPE-008 function types
TYPE-009 inference
TYPE-010 generic inference
TYPE-011 trait resolution
TYPE-012 associated types
TYPE-013 associated constants
TYPE-014 overload resolution
TYPE-015 ambiguity
TYPE-016 coercion
TYPE-017 explicit cast
TYPE-018 bitcast
TYPE-019 recursive types
TYPE-020 opaque types
TYPE-021 visibility leakage
TYPE-022 ownership integration
TYPE-023 Send integration
TYPE-024 dynamic interface
TYPE-025 object safety
TYPE-026 RTTI-free build
TYPE-027 layout queries
TYPE-028 ABI validation
TYPE-029 incremental type cache
TYPE-030 diagnostic quality
```

---

# 430.99 — Final type-system contract

Axiom type system chính thức có các đặc tính:

```text
nominal structs/enums
+
generic types
+
trait constraints
+
associated types
+
associated constants
+
local type inference
+
limited safe coercions
+
explicit conversion
+
explicit unsafe pointer operations
+
explicit dynamic interfaces
+
ownership-aware checking
+
ABI-aware layout
```

và **không** mặc định có:

```text
class subtyping
GC typing
runtime RTTI
implicit numeric promotion
implicit null
arbitrary conversion chains
mandatory lifetime annotations
higher-kinded types
```

---

# 430.100 — Semantic pipeline sau 430

```text
                    SOURCE
                       │
                       ▼
                    LEXER
                       │
                       ▼
                    PARSER
                       │
                       ▼
                      AST
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   MODULE RESOLUTION           DECLARATION INDEX
          │                         │
          └────────────┬────────────┘
                       ▼
                 TYPE CHECKER
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     GENERICS        TRAITS       OWNERSHIP
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                 CONSTANT EVAL
                       │
                       ▼
                    LAYOUT
                       │
                       ▼
                     CFG
                       │
                       ▼
                     SSA
                       │
                       ▼
                  AXIOM IR
```

**BOOTSTRAP-430 hoàn tất về mặt kiến trúc.**

---

# BOOTSTRAP-431 — CONSTANT EVALUATION, COMPTIME, METAPROGRAMMING & CODE GENERATION

Task tiếp theo sẽ khóa **khả năng tính toán tại compile-time**. Đây là nền tảng cho:

- `const`;
- const generics;
- compile-time validation;
- generated serialization;
- SIMD/matrix dimensions;
- lookup-table generation;
- reflection metadata;
- AI/compiler tooling;
- và sau này macro/code generation.

Điểm quan trọng sẽ là **comptime mạnh nhưng không biến Axiom thành một ngôn ngữ compile-time quá phức tạp**, đồng thời không để compile-time execution ảnh hưởng runtime binary khi không cần.