# BOOTSTRAP-119 — Formal AST / HIR Semantic Contract

**Trạng thái: FROZEN / COMPLETED**

Đây là task nối trực tiếp **surface syntax → compiler semantics**.

Nguyên tắc trung tâm:

> **AST mô tả cách programmer viết chương trình. HIR mô tả cách compiler hiểu chương trình.**

Sau HIR, compiler không nên còn phải suy đoán những thứ như method nào được gọi, tên nào resolve tới declaration nào, generic nào được chọn.

---

# 1. Frontend architecture

Axiom frontend chính thức:

```text
Source
  ↓
Lexer
  ↓
Token Stream
  ↓
Lossless Syntax Tree
  ↓
AST
  ↓
Name Resolution
  ↓
HIR Lowering
  ↓
Type / Trait Resolution
  ↓
Typed HIR
  ↓
Closure / Async / Comptime Analysis
  ↓
MIR
```

Có một nguyên tắc:

```text
AST = syntax-oriented
HIR = semantic-oriented
MIR = execution-oriented
```

---

# 2. Token

Mỗi token tối thiểu có:

```text
Token {
    kind
    source_span
    text_range
}
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

được tokenize thành:

```text
FN
IDENT(add)
LPAREN
IDENT(a)
COLON
IDENT(i32)
COMMA
IDENT(b)
COLON
IDENT(i32)
RPAREN
ARROW
IDENT(i32)
```

Trivia:

```text
whitespace
comments
documentation
```

được giữ trong Lossless Syntax Tree nhưng không cần tồn tại trong semantic HIR.

---

# 3. SourceSpan

Mọi semantic node phải truy ngược được source.

```text
SourceSpan {
    SourceFileId
    start
    end
}
```

Không dùng raw pointer vào source buffer làm identity.

---

# 4. Syntax Node

Lossless syntax node:

```text
SyntaxNode {
    kind
    children[]
    token_range
    source_span
}
```

Nó phải có khả năng round-trip:

```text
source
→ syntax tree
→ formatted/reconstructed source
```

mà không mất thông tin cần thiết cho tooling.

---

# 5. AST

AST loại bỏ phần lớn syntax noise.

Ví dụ:

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST:

```text
FunctionDecl
├── name = add
├── parameters
│   ├── Parameter(a, i32)
│   └── Parameter(b, i32)
├── return_type = i32
└── body
    └── BinaryExpr(+)
        ├── NameExpr(a)
        └── NameExpr(b)
```

---

# 6. AST declaration model

```text
AstDecl =
    Function
    Struct
    Enum
    Trait
    Impl
    TypeAlias
    Const
    Module
    Import
    Use
```

Mỗi declaration có:

```text
DeclarationSyntaxId
SourceSpan
Attributes
Visibility
```

---

# 7. AST expressions

```text
AstExpr =
    Literal
    Name
    Path
    Call
    MethodCall
    Field
    Index
    Unary
    Binary
    Cast
    Bitcast
    StructLiteral
    ArrayLiteral
    Tuple
    If
    Match
    Loop
    Closure
    AsyncBlock
    Comptime
    Block
    Break
    Return
    Await
```

AST vẫn giữ distinction giữa `MethodCall` và `Call`.

HIR thì không nhất thiết phải giữ distinction đó.

---

# 8. AST patterns

```text
AstPattern =
    Wildcard
    Binding
    Literal
    Tuple
    Struct
    Variant
    Array
    Range
```

Ví dụ:

```ax
Some(Point { x, y })
```

AST:

```text
VariantPattern(Some)
    StructPattern(Point)
        Binding(x)
        Binding(y)
```

---

# 9. AST types

```text
AstType =
    Primitive
    Path
    Generic
    Array
    Tuple
    Function
    View
    MutView
    DynTrait
    RawPointer
    Never
    Unit
```

Quan trọng:

> `AstType` chưa phải `TypeId`.

`TypeId` chỉ xuất hiện sau semantic type resolution.

---

# 10. Name resolution

Ví dụ:

```ax
foo(x)
```

AST chỉ biết:

```text
Name("foo")
```

Resolver biến nó thành:

```text
DeclarationRef {
    DeclarationId = 184
}
```

Từ đây compiler không nên tiếp tục dùng string `"foo"` làm semantic identity.

---

# 11. Symbol table

CompilerDB có:

```text
SymbolDB
```

với:

```text
SymbolId
Name
Namespace
DeclarationId[]
Visibility
ModuleId
```

Namespace:

```text
VALUE
TYPE
TRAIT
MODULE
LABEL
```

---

# 12. Name resolution phases

Resolver:

```text
1. module graph
2. imports
3. declarations
4. local scopes
5. paths
6. methods
7. associated items
8. generic candidates
```

Không giải quyết tất cả trong một pass.

---

# 13. Declaration identity

Mỗi declaration:

```text
DeclarationId
```

là semantic identity ổn định trong CompilerDB revision.

Ví dụ:

```text
std::io::File::read
```

không được biểu diễn nội bộ đơn thuần bằng string.

---

# 14. HIR declaration

Sau lowering:

```text
HirFunction {
    FunctionId
    name
    visibility
    generics
    params[]
    return_type: TypeId
    body: HirBody
    attributes
}
```

Struct:

```text
HirStruct {
    TypeId
    fields[]
    generics
    attributes
}
```

---

# 15. HIR expression

HIR expression phải gần semantic operation hơn:

```text
HirExpr =
    Const
    Local
    Global
    Call
    MethodResolved
    Field
    Index
    BinaryOp
    UnaryOp
    Cast
    Bitcast
    Aggregate
    VariantConstruct
    If
    Match
    Loop
    Closure
    Async
    Await
    Comptime
    Block
    Return
    Break
```

Nhưng `MethodResolved` sau resolution có thể canonicalize thành `Call`.

---

# 16. Canonicalization

Source:

```ax
user.rename(name);
```

có thể trở thành:

```text
Call {
    function: FunctionId(rename),
    receiver: CapabilityOperand(user),
    args: [name]
}
```

Sau đó HIR không còn cần “method lookup”.

---

# 17. Why this matters

Compiler backend không cần biết:

```text
user.rename(...)
```

là method syntax.

Nó chỉ cần biết:

```text
call FunctionId=42
receiver = user
arg = name
```

Điều này giảm đáng kể complexity downstream.

---

# 18. Place model

HIR/MIR phải có semantic `Place`.

```text
Place {
    base: LocalId
    projections[]
}
```

Projection:

```text
Field(FieldId)
Index(IndexValue)
Deref
Downcast(VariantId)
```

Ví dụ:

```ax
user.address.city
```

có thể thành:

```text
Place(
    Local(user)
    .Field(address)
    .Field(city)
)
```

---

# 19. Vì sao Place quan trọng

Ownership không được tracking chỉ theo variable.

Ví dụ:

```ax
struct User {
    id: u64,
    profile: Profile,
}
```

Có thể:

```text
move user.profile
```

nhưng vẫn giữ:

```text
user.id
```

Do đó verifier cần field-sensitive ownership.

---

# 20. HIR binding

Mỗi local binding:

```text
LocalId
```

có:

```text
name
type
mutability
source_span
scope
```

Sau resolution, string name không còn là identity chính.

---

# 21. Type resolution

AST:

```ax
Vec<Result<i32, Error>>
```

sau resolution:

```text
TypeId(271)
```

TypeDB:

```text
Vec
    └── Result
          ├── i32
          └── Error
```

Type được intern.

---

# 22. Type interning

Equivalent semantic types trong cùng compiler context nên có canonical identity:

```text
TypeId
```

Ví dụ:

```text
Vec<i32>
```

xuất hiện 1000 lần nhưng TypeDB có thể dùng cùng interned type.

Điều này giúp:

- trait solver;
- cache;
- incremental compilation;
- generic specialization.

---

# 23. Generic parameters

HIR giữ:

```text
GenericParamId
```

Ví dụ:

```ax
fn identity<T>(x: T) -> T {
    x
}
```

HIR:

```text
GenericParam(T)
Param x: T
Return T
```

---

# 24. Generic instances

Khi instantiate:

```ax
identity<i32>(42)
```

compiler tạo:

```text
GenericInstanceId
```

với:

```text
FunctionId
TypeArguments = [i32]
ConstArguments = []
```

---

# 25. Trait resolution

Ví dụ:

```ax
a + b
```

nếu operator cần trait:

```text
Add::add
```

Trait solver xác định:

```text
TraitId
ImplId
FunctionId
```

HIR cuối cùng phải chứa resolved semantic target.

---

# 26. Ambiguous trait resolution

Nếu có nhiều candidate và compiler không chứng minh được candidate duy nhất:

```text
ETRAIT_AMBIGUOUS
```

Không được chọn candidate theo:

```text
source order
hash order
compiler implementation accident
```

---

# 27. Method resolution

Resolution order đã khóa:

```text
inherent
→ trait
→ imported extension
→ generic extension
```

HIR phải ghi lại candidate được chọn.

Nếu ambiguity:

```text
EMETHOD_AMBIGUOUS
```

---

# 28. Type inference

Inference được thực hiện trên HIR.

Ví dụ:

```ax
let x = 10;
```

Compiler tạo type variable:

```text
T0
```

sau constraint resolution:

```text
T0 = integer literal type
```

Context quyết định final type nếu cần.

---

# 29. Literal typing

Integer literal ban đầu có:

```text
IntegerLiteral
```

và constraints.

Ví dụ:

```ax
let x: i64 = 10;
```

→ `10 : i64`.

Không tự động tạo conversion chain.

---

# 30. HIR type annotations

Sau type checking:

```text
TypedHirExpr {
    expr
    type: TypeId
}
```

Mọi expression semantic node quan trọng phải có resolved type.

---

# 31. Capability information

Typed HIR bắt đầu mang semantic access mode:

```text
READ
WRITE
MOVE
DROP
```

Ví dụ:

```ax
foo(user)
```

nếu `foo` yêu cầu:

```ax
fn foo(x: view<User>)
```

HIR biết:

```text
argument access = READ
```

---

# 32. Owner → view lowering

Source:

```ax
foo(user);
```

không cần programmer viết:

```ax
foo(view(user));
```

HIR có thể biểu diễn:

```text
MakeView {
    source = user
    expected_region = ...
}
```

Nhưng compiler có thể eliminate node này sau verification.

---

# 33. Explicit stored view

Source:

```ax
let v = view(user);
```

HIR phải giữ operation:

```text
MakeView {
    source
    capability_id
}
```

vì đây là semantic capability creation.

---

# 34. `mut_view`

Tương tự:

```ax
let v = mut_view(user);
```

HIR:

```text
MakeMutView {
    source
    capability_id
}
```

Verifier đảm bảo exclusivity.

---

# 35. Capability identity

Mỗi capability:

```text
CapabilityId
```

gắn với:

```text
owner/provenance
region
access mode
lifetime/use range
storage domain
execution domain
```

---

# 36. Ownership state không phải HIR type

Đây là distinction quan trọng:

```text
Type
```

khác:

```text
Ownership State
```

`User` luôn là `TypeId(User)`.

Nhưng một local có thể:

```text
OWNED
MOVED
PARTIALLY_MOVED
```

Ownership state thuộc dataflow analysis, không phải type identity.

---

# 37. Drop information

HIR có thể biết:

```text
TypeId(User)
Drop = required
```

nhưng **Drop placement** chưa nên hoàn toàn cố định ở HIR.

Drop elaboration xảy ra sau ownership verification.

---

# 38. `?` lowering

Source:

```ax
let x = read()?;
```

HIR canonicalization thành control flow tương đương:

```text
match read() {
    Ok(x) => continue,
    Err(e) => return Err(e),
}
```

nhưng giữ source provenance để diagnostics/debugging.

---

# 39. `for` lowering

Source:

```ax
for x in items {
    process(x);
}
```

HIR:

```text
iterator = IntoIterator::into_iter(items)

loop {
    match Iterator::next(iterator) {
        Some(x) => process(x),
        None => break,
    }
}
```

Sau đó optimizer có thể nhận diện iterator patterns và eliminate abstraction.

---

# 40. `if let`

Source:

```ax
if let Some(x) = value {
    use(x);
}
```

HIR canonical:

```text
match value {
    Some(x) => { use(x); }
    _ => {}
}
```

---

# 41. Method sugar

Source:

```ax
v.push(x)
```

HIR:

```text
Call {
    function = Vec::push,
    receiver = v,
    args = [x]
}
```

---

# 42. Closure lowering

Source:

```ax
let f = |x| x + offset;
```

HIR:

```text
Closure {
    ClosureId
    parameters
    body
    captures: [offset]
}
```

Compiler sau đó sinh semantic anonymous environment:

```text
ClosureEnv {
    offset: T
}
```

Không nhất thiết tồn tại runtime object.

---

# 43. Closure capture

Capture analysis xác định:

```text
offset → READ
```

hoặc:

```text
offset → MUT
```

hoặc:

```text
offset → MOVE
```

Sau đó verifier áp dụng ownership rules bình thường.

---

# 44. Async HIR

Source:

```ax
async fn load() -> Data {
    let x = await read();
    x
}
```

HIR giữ:

```text
AsyncFunction
    Body
        Await
            Future
```

Chưa biến thành machine state machine.

---

# 45. Async state analysis

Một pass riêng xác định:

```text
live_across_await
```

Ví dụ:

```text
a
await foo()
b
```

nếu `a` còn được sử dụng sau await:

```text
a → FutureStateField
```

nếu không:

```text
a → not captured
```

---

# 46. Comptime HIR

`comptime` cũng đi qua HIR.

Compiler có thể execute HIR/Comptime IR bằng compiler VM.

Không được tạo một semantics khác cho comptime.

---

# 47. FFI HIR

Foreign call:

```ax
extern "C" fn foo(x: i32) -> i32;
```

HIR ghi:

```text
ForeignFunction {
    abi = C
    symbol = foo
    signature = ...
}
```

ABI lowering xảy ra sau optimization semantic.

---

# 48. Unsafe HIR

Unsafe operation phải có marker:

```text
UnsafeOperation {
    kind
    source_span
    contract
}
```

Ví dụ raw dereference.

Verifier biết đây là trusted boundary nhưng không coi toàn function là “unchecked”.

---

# 49. HIR effect information

Không cần programmer viết effect annotation trong v0.1.

Compiler tự derive:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

Effect summary được cache trong CompilerDB.

---

# 50. HIR → MIR boundary

HIR vẫn còn:

```text
structured expressions
patterns
closures
async
comptime
high-level calls
```

MIR phải trở thành:

```text
basic blocks
places
operands
rvalues
statements
terminators
```

Do đó:

```text
HIR = semantic program
MIR = semantic execution graph
```

---

# 51. HIR invariants

### `AHIR-20`
Every resolved name has a deterministic semantic identity.

### `AHIR-21`
Semantic references use compiler IDs rather than source strings.

### `AHIR-22`
Every resolved type has a canonical `TypeId`.

### `AHIR-23`
Generic instances have deterministic identities.

### `AHIR-24`
Method resolution is complete before MIR generation.

### `AHIR-25`
Trait resolution is complete before MIR generation.

### `AHIR-26`
HIR does not depend on physical storage layout.

### `AHIR-27`
HIR ownership state is analyzed, not encoded as type identity.

### `AHIR-28`
Capability provenance is explicit in semantic representation.

### `AHIR-29`
Unknown aliasing is preserved as UNKNOWN.

### `AHIR-30`
Implicit owner-to-view conversion cannot silently create an escaping capability.

### `AHIR-31`
All closure captures have explicit inferred capture modes.

### `AHIR-32`
All async suspension points have stable `SuspensionPointId`.

### `AHIR-33`
Comptime-generated declarations re-enter ordinary HIR verification.

### `AHIR-34`
Unsafe operations are explicitly represented.

### `AHIR-35`
FFI operations retain ABI information.

### `AHIR-36`
HIR does not encode a mandatory heap representation.

### `AHIR-37`
HIR does not encode a mandatory runtime.

### `AHIR-38`
Surface syntax sugar is canonicalized before MIR where practical.

### `AHIR-39`
Source provenance survives canonicalization.

### `AHIR-40`
Every semantic HIR node can map back to source.

### `AHIR-41`
HIR is independent from target ISA.

### `AHIR-42`
HIR is deterministic for identical semantic inputs.

### `AHIR-43`
HIR contains sufficient information to construct MIR without reparsing source.

### `AHIR-44`
MIR generation must not perform unresolved name or trait lookup.

---

# 52. CompilerDB sau BOOTSTRAP-119

Cấu trúc trung tâm giờ rõ hơn:

```text
CompilerDB
│
├── SourceDB
├── SyntaxDB
├── AstDB
├── PackageDB
├── ModuleDB
├── SymbolDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── GenericDB
├── ConstDB
├── HIRDB
├── MIRDB
├── LayoutDB
├── AbiDB
├── CodegenDB
├── DiagnosticDB
└── SourceMapDB
```

Mỗi DB nên có dependency graph rõ ràng để incremental compilation.

---

# 53. Query model

Compiler nên tiến tới query-based architecture:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solve(goal)
lower_hir(function)
build_mir(function)
verify_mir(function)
optimize(function)
lower_abi(function)
codegen(function)
```

Các query được memoize.

---

# 54. Tại sao điều này rất quan trọng cho Axiom

Với compiler lớn, thay vì:

```text
compile entire project every time
```

ta có:

```text
source changed
   ↓
invalidate affected queries
   ↓
recompute only necessary semantic objects
```

Đây là nền tảng cho:

- IDE;
- incremental compile;
- AI inspection;
- parallel compiler;
- compiler daemon;
- fast builds.

---

# 55. AI inspection

Vì HIR có semantic IDs, Axiom compiler có thể cung cấp:

```text
ax inspect hir foo
ax inspect type Foo
ax inspect ownership foo
ax inspect capabilities foo
ax inspect traits foo
ax explain error EOWN...
```

AI không cần đọc lại toàn bộ source để hiểu compiler đang nghĩ gì.

---

# 56. Một điểm rất quan trọng

Axiom compiler **không nên cố nhồi mọi thứ vào AST**.

AST không nên chứa:

```text
ownership result
trait solver candidate
register
ABI class
alias lattice
physical layout
```

Ngược lại cũng không nên để HIR phụ thuộc vào:

```text
comment
whitespace
parentheses style
source formatting
```

Mỗi layer có trách nhiệm rõ ràng.

---

# 57. Final frontend contract

```text
SOURCE
  ↓
LOSSLESS SYNTAX
  └── exact source/tooling information

AST
  └── programmer-facing structure

RESOLVED HIR
  └── semantic identities/types/traits/capabilities

TYPED HIR
  └── fully typed canonical semantic program

MIR
  └── executable semantic control/dataflow
```

Đây là frontend architecture chính thức của Axiom v0.1.

---

# BOOTSTRAP-119 hoàn tất

Từ thời điểm này, chúng ta đã khóa được một nguyên tắc cực kỳ quan trọng:

> **Sau Typed HIR, compiler không còn cần hiểu “ý định cú pháp” của programmer; nó chỉ xử lý semantic representation.**

Điều này cho phép backend/compiler optimization được thiết kế độc lập với surface syntax.

---

# BOOTSTRAP-120 — Semantic Type System & Trait Solver Implementation Contract

Task tiếp theo sẽ đi sâu vào phần có khả năng trở thành **một trong những thành phần khó nhất của compiler**:

```text
TypeDB
   ↓
Type Unification
   ↓
Generic Constraints
   ↓
Trait Solver
   ↓
Associated Types
   ↓
Associated Constants
   ↓
Operator Resolution
   ↓
Method Resolution
   ↓
Coherence / Orphan Rules
   ↓
Specialization
   ↓
Type Properties
       ├── Copy
       ├── Drop
       ├── Send
       ├── Share
       ├── Sized
       ├── FFI-safe
       └── GPU-legal
```

Đặc biệt task 120 sẽ phải giải quyết một câu hỏi quan trọng cho Axiom:

> **Làm thế nào để trait/generic system đủ mạnh như Rust/C++ nhưng không biến compiler thành một hệ thống type inference và trait resolution quá phức tạp, chậm và khó debug?**

Mục tiêu sẽ là thiết kế **trait solver có giới hạn, deterministic, cache được, song song được và thân thiện với AI diagnostics**, thay vì xây một theorem prover tổng quát.