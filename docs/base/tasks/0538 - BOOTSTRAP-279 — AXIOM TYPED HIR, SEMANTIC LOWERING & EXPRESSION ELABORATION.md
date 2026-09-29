# BOOTSTRAP-279 — AXIOM TYPED HIR, SEMANTIC LOWERING & EXPRESSION ELABORATION
## FROZEN / COMPLETED

Sau **278 — Type Inference, Constraint Generation & Overload Resolution**, bước tiếp theo hợp lý là khóa **Typed HIR**.

Đây là tầng rất quan trọng vì từ đây compiler phải chuyển từ:

> “Compiler hiểu source code có nghĩa gì”

sang:

> “Compiler đã biến toàn bộ nghĩa đó thành một biểu diễn trung gian không còn mơ hồ để các verifier và MIR có thể xử lý.”

---

# 1. Mục tiêu

Typed HIR phải là điểm mà:

- name resolution đã hoàn tất;
- type inference đã hoàn tất;
- generic substitution đã hoàn tất;
- overload đã được chọn;
- coercion đã được chèn;
- trait obligations cần thiết đã được resolve;
- expression type đã xác định;
- control-flow semantics đã rõ;
- closure/async/generator/gpu/FFI boundaries đã được đánh dấu.

Nhưng Typed HIR **chưa** quyết định:

- stack/register;
- physical layout;
- machine instruction;
- allocation strategy;
- ABI register classification;
- instruction scheduling.

---

# 2. Nguyên tắc trung tâm

> **Typed HIR là semantic elaboration của source program, không phải optimization IR.**

```text
AST
 ↓
Name Resolution
 ↓
Type Inference
 ↓
Trait / Overload Resolution
 ↓
Typed HIR
 ↓
Semantic Verification
 ↓
MIR
```

Typed HIR phải loại bỏ ambiguity của source language.

---

# 3. AST vs Typed HIR

Ví dụ source:

```ax
let x = identity(10)
```

AST:

```text
Let
 ├── name: x
 └── initializer:
      Call
       ├── identity
       └── 10
```

Typed HIR:

```text
Let
 ├── binding: LocalId(42)
 ├── type: i32
 └── initializer:
      Call
       ├── function: identity<i32>
       ├── arguments:
       │    IntegerLiteral<i32>(10)
       └── result: i32
```

Không còn:

```text
identity ?
?T
which overload?
which coercion?
```

---

# 4. Typed HIR không được chứa semantic ambiguity

Invariant:

```text
AHIR-20
Every production Typed HIR expression has a resolved semantic type.

AHIR-21
Every production function call has exactly one selected callable target.

AHIR-22
Every generic invocation has canonical generic arguments.

AHIR-23
Every inserted coercion is explicit in Typed HIR.

AHIR-24
No unresolved inference variable may enter production Typed HIR.

AHIR-25
Unresolved overload ambiguity cannot enter production Typed HIR.

AHIR-26
Unproven trait obligations cannot enter production Typed HIR.
```

---

# 5. Typed HIR không phải MIR

Đây là distinction phải giữ rất rõ.

### Typed HIR

```text
Call
MethodCall
If
Match
Closure
Async
QuestionMark
Index
FieldAccess
For
While
```

vẫn có thể tồn tại.

### MIR

Các construct này được lower thành:

```text
BasicBlock
Branch
Switch
Call
Load
Store
Move
Drop
Capability
Await
Return
```

Do đó:

```text
Typed HIR
    = semantic high-level IR

MIR
    = executable semantic control-flow IR
```

---

# 6. HIR expression model

Đề xuất:

```text
HirExprKind =
    Literal
    Local
    Global
    Function
    Call
    MethodCall
    Field
    Index
    Unary
    Binary
    Assign
    Block
    If
    Match
    Loop
    While
    For
    Break
    Continue
    Return
    Closure
    AsyncBlock
    Await
    QuestionMark
    Cast
    Bitcast
    Coerce
    Tuple
    Array
    Struct
    Enum
    Range
    UnsafeBlock
    Comptime
    Error
```

---

# 7. Mỗi HIR expression có TypeId

Ví dụ:

```text
HirExpr {
    id: HirExprId
    kind: HirExprKind
    type_id: TypeId
    source_span: SourceSpanId
}
```

Không để các stage sau phải gọi lại inference chỉ để hỏi:

> Expression này có type gì?

---

# 8. Value category

Axiom không cần C++-style `lvalue/rvalue/xvalue`.

Thay vào đó HIR phân biệt semantic use:

```text
ValueUse =
    Read
    Move
    Mutate
    AddressOfUnsafe
    Discard
```

Nhưng đây là **semantic intent**, ownership verifier vẫn là authority cuối cùng.

Ví dụ:

```ax
consume(x)
```

HIR:

```text
Call
    argument:
        Use(Local x, Move)
```

---

# 9. Copy và Move phải được explicit hóa

Source:

```ax
let b = a
```

Nếu `a: Copy`:

```text
Use(a, Copy)
```

Nếu `a` là owning non-Copy:

```text
Use(a, Move)
```

Compiler đã xác định semantic mode trước khi xuống MIR.

Nhưng physical copy/move vẫn do optimizer quyết định.

---

# 10. Copy semantic ≠ machine copy

Ví dụ:

```text
Copy(i32)
```

có thể machine implementation là:

```text
register move
```

hoặc:

```text
constant propagation
```

hoặc:

```text
không có instruction
```

Do đó HIR ghi:

```text
semantic Copy
```

chứ không ghi:

```text
MOV registerA, registerB
```

---

# 11. Coercion elaboration

Source:

```ax
sum(array)
```

Sau 278:

```text
array : [4]i32
sum expects view<i32>
```

Typed HIR:

```text
Call(sum)
    Coerce(
        ArrayToView,
        array,
        from=[4]i32,
        to=view<i32>
    )
```

Từ đây không stage nào được tự ý tạo coercion mới.

---

# 12. Cast và Bitcast

Typed HIR phân biệt:

```text
Cast
Bitcast
Coerce
```

Ví dụ:

```ax
x as i64
```

→

```text
Cast(x, i64)
```

Còn:

```text
bitcast<T>(x)
```

→

```text
Bitcast(x, T)
```

Không được normalize cả ba thành một operation.

---

# 13. Function reference

Source:

```ax
let f = identity
```

Typed HIR phải lưu declaration identity:

```text
FunctionRef {
    function_id: FunctionId
    instantiated_type: FunctionType
}
```

Không dùng:

```text
string "identity"
```

ở semantic backend.

---

# 14. Generic call

Source:

```ax
identity(42)
```

HIR:

```text
Call {
    target: FunctionId(identity)
    generic_args: [i32]
    args: [...]
    result_type: i32
}
```

Generic substitution đã canonicalized bởi TypeDB.

---

# 15. Method call elaboration

Source:

```ax
v.length()
```

HIR có thể giữ:

```text
MethodCall {
    receiver: v
    target: length
}
```

hoặc elaborated ngay thành:

```text
Call {
    target: length
    args: [v]
}
```

### Đề xuất

Giữ `MethodCall` trong Typed HIR để diagnostics/debugging tốt hơn, sau đó lower thành ordinary call trước MIR.

Như vậy compiler vẫn bảo toàn source provenance:

```text
v.length()
```

thay vì chỉ còn:

```text
length(v)
```

---

# 16. Operator elaboration

Source:

```ax
a + b
```

Typed HIR:

```text
Binary {
    operator: Add
    lhs: a
    rhs: b
    resolved_semantics: BuiltinAdd(i32)
}
```

Nếu là trait implementation:

```text
resolved_semantics:
    TraitMethod(Add::add, MyType)
```

Backend không phải chạy overload resolution lần nữa.

---

# 17. Field access

```ax
user.name
```

HIR:

```text
Field {
    base: user
    field_id: FieldId(17)
    type: Str
}
```

Không lưu chỉ:

```text
field_name = "name"
```

`FieldId` là semantic identity.

---

# 18. Indexing

```ax
array[i]
```

Nếu built-in array:

```text
Index {
    base
    index
    semantics: BuiltinIndex
    result_type: i32
}
```

Nếu custom indexing:

```text
Index {
    semantics: TraitIndex(...)
}
```

Bounds checking vẫn là semantic requirement.

Optimizer sau đó có thể loại bỏ check nếu chứng minh được range.

---

# 19. Assignment

```ax
x = y
```

HIR:

```text
Assign {
    target: PlaceExpr(x)
    value: y
}
```

Target phải là writable semantic location.

Type inference đã xác định:

```text
type(target)
type(value)
```

Capability/ownership verifier xác định legality.

---

# 20. Assignment không phải Copy

Ví dụ:

```ax
x = y
```

có thể nghĩa là:

```text
Move
Copy
```

tùy type/use semantics.

HIR phải preserve semantic operation:

```text
Assign {
    value_use: Move
}
```

hoặc:

```text
value_use: Copy
```

---

# 21. Block

Source:

```ax
{
    let x = 10
    x + 1
}
```

HIR:

```text
Block {
    statements: [
        Let(x, 10)
    ]
    result:
        Binary(Add, x, 1)
    type: i32
}
```

---

# 22. Unit block

```ax
{
    foo()
}
```

HIR result:

```text
unit
```

Nếu expression cuối có giá trị nhưng bị discarded:

```text
Discard(expr)
```

semantic distinction phải tồn tại.

---

# 23. If

```ax
if condition {
    a
} else {
    b
}
```

HIR:

```text
If {
    condition
    then_block
    else_block
    result_type
}
```

Type đã được unify.

MIR mới lower thành branch:

```text
BB0
 ├── condition
 ├── branch BB1
 └── branch BB2
```

---

# 24. Match

Typed HIR:

```text
Match {
    scrutinee
    arms: [
        {
            pattern
            guard?
            body
        }
    ]
    result_type
}
```

Mỗi pattern đã được resolve thành semantic constructor:

```text
VariantId
FieldId
BindingId
```

Không còn name lookup ở MIR.

---

# 25. Pattern binding

Source:

```ax
match value {
    Some(x) => x
}
```

HIR:

```text
Pattern::Variant {
    variant: Some
    bindings: [
        BindingId(x)
    ]
}
```

`x` có TypeId đã xác định.

---

# 26. Exhaustiveness boundary

Exhaustiveness checker chạy trước production Typed HIR.

Do đó:

```text
Typed HIR
```

có thể giả định rằng:

```text
match
```

đã thỏa pattern correctness.

Nhưng MIR lowering vẫn phải bảo vệ compiler invariants.

---

# 27. Loop

Source:

```ax
while condition {
    work()
}
```

HIR:

```text
While {
    condition
    body
}
```

MIR:

```text
header
  ↓
condition
  ├── false → exit
  └── true → body
                 ↓
               header
```

---

# 28. `for`

Axiom `for` nên được elaborated tại HIR.

Ví dụ:

```ax
for x in collection {
    process(x)
}
```

thành semantic iterator operations:

```text
iterator = IntoIterator(collection)
loop:
    next(iterator)
    match:
        Some(x) → body
        None    → exit
```

Nhưng HIR vẫn có thể giữ:

```text
For {
    iterable
    binding
    body
}
```

để diagnostics/debugging.

Sau đó lowering query tạo iterator HIR.

---

# 29. Closure

Typed HIR:

```text
Closure {
    closure_id
    params
    result_type
    captures
    body
    callable_traits
}
```

Capture đã được closure analysis xác định:

```text
Capture {
    local
    mode: ByValue | ByView | ByMutView
}
```

Ownership verifier vẫn kiểm tra legality.

---

# 30. Closure type identity

Mỗi closure expression có:

```text
ClosureId
```

và TypeDB tạo unique closure type.

Ví dụ:

```ax
let f = |x| x + 1
let g = |x| x + 1
```

`f` và `g` không mặc định cùng concrete closure type.

---

# 31. Closure conversion

Typed HIR:

```text
Closure
```

sau đó được lower thành conceptual:

```text
ClosureEnvironment struct
ClosureFunction(env, args)
```

nhưng đây là compiler transformation.

Programmer không nhìn thấy class/object header.

---

# 32. Async

Source:

```ax
async fn fetch() -> Data
```

Typed HIR:

```text
AsyncFunction {
    function_id
    params
    result: Data
    future_type
    body
}
```

Chưa tạo heap.

Chưa tạo executor.

Chưa tạo runtime object.

---

# 33. Await

```ax
let x = foo().await
```

HIR:

```text
Await {
    future: Call(foo)
    result_type: T
    suspension_point_id
}
```

Async lowering sau đó biến thành state machine.

---

# 34. `?`

Source:

```ax
let x = read()?
```

Typed HIR nên giữ:

```text
QuestionMark {
    operand: Call(read)
    success_type: T
    error_type: E
    enclosing_result_type: Result<T2,E2>
}
```

sau semantic elaboration có thể lower thành:

```text
match result {
    Ok(x) => continue,
    Err(e) => return converted_error(e)
}
```

Nhưng source-level `?` vẫn giữ provenance.

---

# 35. `return`

HIR:

```text
Return {
    value?
    function_id
}
```

MIR mới biến thành:

```text
cleanup
↓
Return
```

Đây là nơi ownership/drop verifier sau này đảm bảo cleanup.

---

# 36. `break` / `continue`

HIR phải lưu:

```text
Break {
    target_loop_id
    value?
}
```

```text
Continue {
    target_loop_id
}
```

Resolver xác định loop target trước khi MIR lowering.

Không để MIR phải tìm lexical loop bằng tên.

---

# 37. Unsafe

Source:

```ax
unsafe {
    *p
}
```

HIR:

```text
UnsafeBlock {
    operations
    unsafe_boundary_id
}
```

Unsafe boundary có provenance:

```text
UnsafeBoundaryId
SourceSpan
```

Nhưng:

> Unsafe không tắt verifier.

---

# 38. Comptime

```ax
comptime {
    ...
}
```

HIR:

```text
ComptimeBlock {
    expression
    required_capabilities
}
```

Compiler thực thi trong Comptime VM.

Kết quả materialized vào Typed HIR nếu cần.

---

# 39. GPU kernel

```ax
@kernel
fn add(...) { ... }
```

HIR lưu:

```text
FunctionAttributes {
    kernel: true
}
```

và `GpuInfo`.

GPU legality được query trước khi codegen.

Không để backend CPU/GPU tự đoán function có phải kernel hay không.

---

# 40. FFI

```ax
extern "C" fn foo(...)
```

Typed HIR:

```text
ExternFunction {
    function_id
    abi: C
    signature
    ffi_contract
}
```

ABI lowering xử lý sau.

---

# 41. Global/static

HIR phải phân biệt:

```text
LocalBinding
GlobalBinding
StaticBinding
TLSBinding
Constant
```

Không gom tất cả thành variable.

Ví dụ:

```ax
const X: i32 = 10
```

→ compile-time constant.

```ax
static X: i32 = 10
```

→ program storage identity.

Hai semantics khác nhau.

---

# 42. Evaluation order

Typed HIR phải preserve evaluation order.

Ví dụ:

```ax
foo(a(), b())
```

semantic order phải deterministic theo Core expression semantics.

HIR có thể biểu diễn:

```text
Call foo
    arg0 = a()
    arg1 = b()
```

nhưng lowering không được reorder nếu observable semantics bị thay đổi.

---

# 43. Temporary values

Compiler có thể tạo:

```text
HirTemporaryId
```

nhưng temporary không phải user-visible variable.

Ví dụ:

```ax
foo(make())
```

có thể elaborated thành:

```text
tmp0 = make()
foo(tmp0)
```

nếu cần cho:

- ownership;
- drop;
- evaluation order;
- diagnostics.

---

# 44. Drop scopes

Typed HIR phải đánh dấu lexical/semantic scopes đủ để Drop elaboration biết:

```text
ScopeId
DropScope
```

Ví dụ:

```ax
{
    let a = A()
    {
        let b = B()
    }
}
```

→

```text
inner scope:
    Drop(b)

outer scope:
    Drop(a)
```

MIR mới biến thành explicit Drop.

---

# 45. Nhưng HIR không tự chèn tất cả Drop

Đề xuất:

```text
Typed HIR:
    records semantic scope/lifetime boundaries

Drop elaboration:
    inserts exact Drop operations
```

Điều này giữ HIR sạch.

---

# 46. Semantic places

HIR cần một representation cho location:

```text
HirPlace =
    Local(LocalId)
    Global(GlobalId)
    Field(base, FieldId)
    Index(base, index)
    Deref(raw_pointer)      // unsafe
```

Place sẽ trở thành nền tảng cho MIR `Place`.

---

# 47. Ownership information

Typed HIR có thể chứa:

```text
OwnershipUse {
    local
    semantic_use
}
```

nhưng **ownership state machine** vẫn thuộc verifier/MIR.

Không duplicate state machine ở HIR.

---

# 48. Capability information

Tương tự:

```text
view(x)
mut_view(x)
```

được elaborated thành:

```text
MakeView
MakeMutView
```

nhưng:

```text
CapabilityId
Region
Lifetime
```

được hoàn thiện ở semantic verification/MIR.

---

# 49. ErrorType

IDE có thể có:

```text
ErrorExpr
ErrorType
```

để tiếp tục phân tích.

Production:

```text
ErrorType
```

không được đi tiếp:

```text
Typed HIR → Verified MIR
```

---

# 50. HIR source provenance

Mọi HIR node cần:

```text
SourceSpanId
```

và transformation có thể giữ:

```text
Origin {
    primary_source
    secondary_sources
}
```

Ví dụ một generated coercion:

```text
Coerce
origin:
    call argument span
reason:
    Array<T,N> → view<T>
```

---

# 51. HIR IDs

Đề xuất:

```text
HirModuleId
HirFunctionId
HirExprId
HirStmtId
HirPatternId
HirBlockId
HirBindingId
HirCaptureId
HirScopeId
HirPlaceId
```

Tất cả typed ID.

---

# 52. HIR immutable publication

Theo BOOTSTRAP-274:

```text
AST → HIR construction
```

có thể mutable trong local builder.

Sau publication:

```text
Typed HIR
```

là immutable semantic database object nếu có thể.

Điều này giúp:

- incremental;
- parallel analysis;
- cache;
- deterministic compiler behavior.

---

# 53. HIR query model

CompilerDB:

```text
lower_to_typed_hir(FunctionId)
typed_hir_expr(HirExprId)
typed_hir_function(HirFunctionId)
typed_hir_body(FunctionId)
```

Không tạo cache riêng.

---

# 54. Lowering phải deterministic

Cùng:

```text
source
compiler revision
target semantic configuration
```

phải cho:

```text
identical Typed HIR semantics
```

bất kể:

```text
worker count
query execution order
cache hit/miss
```

---

# 55. HIR canonicalization

Hai source khác nhau nhưng cùng semantic meaning **không nhất thiết** phải có byte-identical HIR.

Ví dụ:

```ax
x + 1
```

và:

```ax
Add::add(x, 1)
```

có thể giữ source distinction.

Nhưng sau elaboration chúng phải có cùng semantic operation classification nếu cùng overload resolution.

---

# 56. HIR không được optimize quá sớm

Không làm trong Typed HIR:

```text
constant folding
dead code elimination
inline
SSA
scalar replacement
register allocation
```

Ngoại lệ: compile-time evaluation cần thiết để xác định semantic constants.

Optimization bắt đầu sau Verified MIR.

---

# 57. HIR → MIR boundary

Pipeline chính thức:

```text
Typed HIR
    ↓
Semantic Elaboration
    ↓
Drop Elaboration
    ↓
Capability / Ownership Lowering
    ↓
Control-Flow Lowering
    ↓
Async Lowering
    ↓
Closure Lowering
    ↓
Pattern Lowering
    ↓
MIR
```

Một số bước có thể được thực hiện trong một lowering pass nhưng semantic boundaries phải tồn tại về mặt architecture.

---

# 58. MIR phải không còn high-level ambiguity

Sau lowering:

```text
if
match
for
method resolution
generic resolution
overload
coercion
closure syntax
```

không còn là vấn đề semantic discovery.

MIR chỉ thực hiện semantics đã được xác định.

---

# 59. Typed HIR invariant quan trọng nhất

```text
AHIR-50

Typed HIR is a fully elaborated semantic representation:
all names, types, generic substitutions, overload selections,
trait obligations, coercions and control-flow targets required
for subsequent semantic lowering are resolved before production
MIR construction.
```

---

# 60. Không để backend quay ngược lên AST

Sau Typed HIR:

```text
MIR
 ↓
OptIR
 ↓
LIR
 ↓
Machine
```

không stage nào được phép hỏi:

```text
"What did this source identifier mean?"
```

Nếu cần thông tin source:

```text
CompilerDB / provenance
```

phải cung cấp semantic fact.

---

# 61. AI compiler interface

Typed HIR trở thành một nguồn dữ liệu cực tốt cho AI.

Ví dụ API:

```text
explain_expr(expr_id)
show_typed_hir(function_id)
show_resolution(call_id)
show_coercions(expr_id)
show_capture(closure_id)
show_control_flow(function_id)
show_semantic_origin(hir_node)
```

AI có thể hỏi:

```text
Why is this call using implementation X?
```

và compiler trả lời bằng semantic facts, thay vì AI phải tự đọc toàn bộ source.

---

# 62. Diagnostic architecture

Typed HIR diagnostics nên structured:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    suggestions
    semantic_facts
}
```

Không hard-code diagnostic thành một chuỗi duy nhất.

---

# 63. Testing strategy

Bắt buộc có ba lớp:

### AST → HIR tests

```text
source
→ AST
→ Typed HIR snapshot
```

### Semantic equivalence

```text
different syntax
→ same semantic classification
```

### HIR → MIR

```text
Typed HIR
→ MIR
```

với invariant checks.

---

# 64. Snapshot tests

Ví dụ:

```text
input:
    let x = identity(10)

expected:
    x: i32
    call: identity<i32>
    literal: i32
    result: i32
```

Snapshot phải ổn định.

Không phụ thuộc ID allocation ngẫu nhiên.

---

# 65. Adversarial tests

Bắt buộc:

```text
nested generic calls
overload + trait
closure + generic
closure + mutation
async + closure
async + view
match + ? 
nested match
unsafe pointer operations
FFI
GPU kernel
comptime generated declarations
deep nested blocks
early return + Drop
partial move + Drop
```

---

# 66. Performance

HIR construction phải:

- arena-based;
- typed IDs;
- immutable after publication;
- tránh clone AST lớn;
- tận dụng interned TypeId;
- source span compact;
- query-incremental.

Không tạo một object graph nặng kiểu OOP cho mỗi token/expression nếu không cần.

---

# 67. Bộ module

```text
compiler/
└── semantic/
    └── hir/
        ├── mod.ax
        ├── hir_id.ax
        ├── hir_expr.ax
        ├── hir_stmt.ax
        ├── hir_pattern.ax
        ├── hir_function.ax
        ├── hir_module.ax
        ├── hir_place.ax
        ├── hir_scope.ax
        ├── hir_binding.ax
        ├── hir_capture.ax
        ├── hir_coercion.ax
        ├── hir_call.ax
        ├── hir_method.ax
        ├── hir_operator.ax
        ├── hir_async.ax
        ├── hir_closure.ax
        ├── hir_match.ax
        ├── hir_comptime.ax
        ├── hir_gpu.ax
        ├── hir_ffi.ax
        ├── provenance.ax
        ├── elaboration.ax
        ├── lowering.ax
        └── tests/
```

---

# 68. Implementation order

```text
1. HirId family
2. HIR arenas/storage
3. HirExpr
4. HirStmt
5. HirPattern
6. HirBinding
7. HirPlace
8. source provenance
9. typed expression construction
10. call elaboration
11. generic substitution elaboration
12. overload result materialization
13. coercion materialization
14. operator elaboration
15. method elaboration
16. block/if/match elaboration
17. loop elaboration
18. closure elaboration
19. async elaboration
20. ? elaboration
21. unsafe/comptime/GPU/FFI markers
22. semantic scopes
23. Typed HIR publication
24. HIR validation
25. CompilerDB queries
26. incremental HIR
27. snapshot tests
28. HIR → MIR lowering tests
```

---

# 69. Frozen invariants — BOOTSTRAP-279

```text
AHIR-20
Typed HIR is the canonical elaborated semantic representation before MIR.

AHIR-21
Production Typed HIR contains resolved semantic types.

AHIR-22
Production Typed HIR contains resolved declarations.

AHIR-23
Production calls contain exactly one selected callable target.

AHIR-24
Generic calls contain canonical generic arguments.

AHIR-25
Coercions are explicit HIR operations.

AHIR-26
Cast and bitcast remain distinct semantic operations.

AHIR-27
Method resolution is complete before production MIR.

AHIR-28
Operator resolution is complete before production MIR.

AHIR-29
Field access contains semantic FieldId.

AHIR-30
Pattern constructors contain semantic VariantId.

AHIR-31
Pattern bindings contain semantic BindingId.

AHIR-32
Loop control targets are resolved before MIR.

AHIR-33
Every production HIR expression has a TypeId.

AHIR-34
ErrorType cannot enter Verified MIR.

AHIR-35
Inference variables cannot enter production Typed HIR.

AHIR-36
Ambiguous overloads cannot enter production Typed HIR.

AHIR-37
Unproven trait obligations cannot enter production Typed HIR.

AHIR-38
HIR preserves source provenance.

AHIR-39
HIR transformations do not destroy semantic source mapping.

AHIR-40
Typed HIR does not encode physical register allocation.

AHIR-41
Typed HIR does not encode target-specific machine instructions.

AHIR-42
Typed HIR does not determine physical allocation strategy.

AHIR-43
Typed HIR does not perform optimization requiring MIR facts.

AHIR-44
Semantic evaluation order is preserved.

AHIR-45
Semantic Copy and Move intent is preserved.

AHIR-46
Physical copies and moves remain implementation decisions.

AHIR-47
Ownership state remains authoritative in verification/MIR.

AHIR-48
Capability validity remains authoritative in verification/MIR.

AHIR-49
Drop elaboration is explicit before Verified MIR.

AHIR-50
Typed HIR is fully semantically elaborated.

AHIR-51
Method syntax may be preserved for diagnostics while lowering to ordinary calls.

AHIR-52
Closure expressions have unique semantic closure identity.

AHIR-53
Closure capture modes are preserved.

AHIR-54
Async suspension points have semantic identities.

AHIR-55
Async HIR does not imply heap allocation or executor presence.

AHIR-56
Unsafe boundaries remain explicit.

AHIR-57
Unsafe does not disable later verification.

AHIR-58
Comptime boundaries remain explicit.

AHIR-59
GPU kernel boundaries remain explicit.

AHIR-60
FFI ABI boundaries remain explicit.

AHIR-61
Static, TLS, constant and local storage semantics remain distinct.

AHIR-62
Typed HIR does not contain unresolved name lookup.

AHIR-63
Typed HIR does not require backend target information.

AHIR-64
Typed HIR queries use CompilerDB.

AHIR-65
Typed HIR objects are immutable after publication where practical.

AHIR-66
Typed HIR construction is deterministic.

AHIR-67
Typed HIR construction is independent of worker count.

AHIR-68
Typed HIR incremental recomputation is dependency-driven.

AHIR-69
Typed HIR IDs use typed compiler identifiers.

AHIR-70
HIR storage identity is independent of physical memory address.

AHIR-71
HIR does not create independent TypeId identity.

AHIR-72
HIR uses canonical TypeDB types.

AHIR-73
HIR does not reimplement trait solving.

AHIR-74
HIR does not reimplement overload resolution.

AHIR-75
HIR records the results of trait and overload resolution.

AHIR-76
Generated HIR from comptime re-enters normal validation.

AHIR-77
Generated HIR cannot bypass ownership or capability verification.

AHIR-78
HIR diagnostics remain structured.

AHIR-79
HIR snapshots are semantically stable.

AHIR-80
MIR lowering consumes semantic HIR facts rather than rediscovering source meaning.

AHIR-81
MIR lowering cannot introduce arbitrary semantic coercions.

AHIR-82
MIR lowering cannot silently change evaluation order.

AHIR-83
MIR lowering cannot silently change ownership semantics.

AHIR-84
MIR lowering cannot silently change capability semantics.

AHIR-85
HIR is independent of Axiom runtime presence.

AHIR-86
HIR does not require GC.

AHIR-87
HIR does not require object headers.

AHIR-88
HIR does not require mandatory heap allocation.

AHIR-89
HIR semantics remain independent of optimization level.

AHIR-90
Typed HIR is a semantic boundary between source language and executable IR.
```

---

## Trạng thái

**BOOTSTRAP-279 — FROZEN / COMPLETED.**

Chuỗi compiler hiện đã khá rõ:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
Name Resolution
  ↓
TypeDB
  ↓
Type Inference
  ↓
Trait Solver
  ↓
Overload Resolution
  ↓
┌───────────────────────┐
│     TYPED HIR         │  ← BOOTSTRAP-279
│ fully elaborated      │
└──────────┬────────────┘
           ↓
   Drop / Ownership
   Capability
   Control Flow
   Async / Closure
   Pattern
           ↓
          MIR
           ↓
      Verified MIR
           ↓
         OptIR
           ↓
          LIR
           ↓
       Machine Code
```

**Bước kế tiếp hợp lý là BOOTSTRAP-280: `AXIOM HIR → MIR LOWERING & CONTROL-FLOW CONSTRUCTION`** — nơi ta khóa chính xác cách `if/match/loop/closure/async/?/defer/drop` biến thành CFG + MIR, đồng thời đặt nền cho ownership/capability verifier hoạt động trên `Place` và `BasicBlock`.