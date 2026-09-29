# BOOTSTRAP-355 — AXIOM EXPRESSION, OPERATOR, OVERLOAD & CONVERSION RESOLUTION ENGINE

Đây là lớp ngữ nghĩa nằm ngay sau **Name Resolution + Type/Trait Solver**. Mục tiêu là biến mọi biểu thức Axiom thành một dạng **đã xác định duy nhất về kiểu, cách gọi, ownership/capability và semantics**, trước khi hạ xuống MIR.

---

## 1. Mục tiêu thiết kế

Axiom phải đạt được:

> **Một biểu thức hợp lệ → compiler luôn biết chính xác nó làm gì, trả về kiểu gì, đọc/ghi/move gì và có thể hạ xuống machine code như thế nào.**

Đồng thời:

- không có overload resolution dựa trên runtime;
- không có implicit boxing;
- không có implicit allocation;
- không tự động tạo dynamic dispatch;
- không có conversion ngầm nguy hiểm;
- không để syntax sugar tạo semantics khác biệt;
- evaluation order hoàn toàn deterministic;
- compiler được phép tối ưu nhưng không được thay đổi observable semantics.

---

# 2. Expression Model

Mọi biểu thức Axiom thuộc một trong các nhóm:

```text
Literal
Name
Path
Tuple
Array
StructInit
EnumInit

Unary
Binary
Assignment

Call
MethodCall
Index
Slice
FieldAccess

Block
If
Match
Loop
Break
Continue
Return

Closure
AsyncExpression
Await
Try

Cast
Bitcast

ComptimeExpression
```

Compiler không coi chúng đơn thuần là AST syntax.

Mỗi expression sau semantic resolution phải có:

```text
ExprId
TypeId
ValueCategory
OwnershipEffect
CapabilityEffect
ControlFlowEffect
ConstState
SourceSpan
```

Ví dụ:

```text
x + y
```

sau resolution có thể trở thành:

```text
Expr:
    type        = i32
    operator    = Add<i32>
    receiver    = x
    argument    = y
    ownership   = READ(x), READ(y)
    effect      = Pure
```

---

# 3. Value Category

Axiom không dùng mô hình C++ `lvalue/rvalue/xvalue` vì quá nhiều khái niệm programmer-facing.

Thay vào đó compiler sử dụng:

```text
VALUE
PLACE
CAPABILITY
```

### VALUE

Một giá trị độc lập:

```text
42
make_vec()
a + b
```

### PLACE

Một vị trí semantic có thể được đọc, ghi hoặc move:

```text
x
obj.field
array[i]
buffer[index]
```

Compiler tự xác định expression đang cần:

```text
READ
WRITE
MOVE
DROP
```

Programmer không phải viết `&x`, `*x`, `move(x)` cho các trường hợp thông thường.

---

# 4. Evaluation Order

Đây là invariant rất quan trọng.

Axiom sử dụng:

> **Left-to-right evaluation order.**

Ví dụ:

```text
f(a(), b(), c())
```

luôn:

```text
a()
b()
c()
f(...)
```

Không phụ thuộc:

- optimization;
- CPU;
- ABI;
- compiler version;
- register allocation.

Tương tự:

```text
a + b * c
```

phải đánh giá operand theo semantic order đã quy định.

Compiler có thể reorder khi và chỉ khi chứng minh:

```text
observable_semantics(reordered)
==
observable_semantics(original)
```

Do đó optimizer vẫn có tự do lớn nhưng language semantics không mơ hồ.

---

# 5. Operator Model

Operator được chia thành hai nhóm.

## 5.1 Built-in semantic operators

Một số operator không phải trait thông thường:

```text
&&
||
=
.
[]
?
await
```

vì chúng có control-flow hoặc capability semantics đặc biệt.

Ví dụ:

```text
a && b
```

không phải:

```text
And(a, b)
```

mà:

```text
evaluate a
if false:
    result = false
else:
    evaluate b
```

Do đó `b` có thể không được evaluate.

---

# 6. Trait-based Operators

Các operator thông thường có thể được biểu diễn bằng trait.

Ví dụ:

```text
a + b
```

semantic equivalent:

```text
Add::add(a, b)
```

Các trait cơ bản:

```text
Add<Rhs>
Sub<Rhs>
Mul<Rhs>
Div<Rhs>
Rem<Rhs>

BitAnd<Rhs>
BitOr<Rhs>
BitXor<Rhs>
Shl<Rhs>
Shr<Rhs>

Eq<Rhs>
Ord<Rhs>

Neg
Not
```

Nhưng syntax vẫn là:

```text
a + b
```

Không cần programmer viết:

```text
a.Add(b)
```

Compiler resolve operator thông qua TraitDB.

---

# 7. Không cho phép operator overloading tùy tiện

Axiom không nên cho phép định nghĩa:

```text
operator spaceship
operator magical_arrow
operator ??? 
```

Operator set là **closed set**.

Compiler biết trước:

```text
+
-
*
/
%
==
!=
<
<=
>
>=
&
|
^
<<
>>
!
~
&&
||
=
+=
-=
*=
/=
...
```

Điều này giúp:

- parser đơn giản;
- IDE đơn giản;
- compiler predictable;
- AI dễ sinh code;
- không xuất hiện DSL operator quá khó đọc.

---

# 8. Precedence

Precedence được frozen ở language level.

Ví dụ:

```text
a + b * c
```

là:

```text
a + (b * c)
```

Không cho library thay đổi precedence.

Operator associativity cũng cố định.

Ví dụ:

```text
a - b - c
```

=

```text
(a - b) - c
```

---

# 9. Call Resolution

Một call:

```text
foo(a, b)
```

được resolve theo pipeline:

```text
1. Resolve name/path
2. Collect callable candidates
3. Check visibility
4. Infer generic parameters
5. Match arguments
6. Apply allowed coercions
7. Solve trait constraints
8. Rank candidates
9. Select unique candidate
10. Instantiate generic
11. Determine ABI
```

Nếu có hai candidate ngang nhau:

```text
AMBIGUOUS_CALL
```

Không dựa vào:

- declaration order;
- hash order;
- filesystem order;
- compiler implementation accident.

---

# 10. Method Resolution

Ví dụ:

```text
v.length()
```

được resolve theo thứ tự đã frozen:

```text
1. inherent method
2. trait method
3. imported extension
4. generic extension
```

Semantic lowering:

```text
v.length()
```

→

```text
length(v)
```

nếu method có:

```text
fn length(self: Vec)
```

Không cần object/class/vtable.

---

# 11. Argument Matching

Axiom ưu tiên:

> **Exact match > safe coercion > explicit conversion**

Ví dụ:

```text
fn foo(x: i64)
foo(i64_value)
```

exact.

Nhưng:

```text
foo(i32_value)
```

không nên tùy tiện biến thành:

```text
i64_value
```

nếu conversion có thể gây semantic surprise.

---

# 12. Implicit Conversion

Đây là điểm cần giữ rất chặt.

Axiom chỉ cho implicit coercion trong những trường hợp **không làm mất thông tin và không thay đổi ownership semantics**.

Có thể cho:

```text
T → view<T>
```

trong argument position đã được xác định.

Ví dụ:

```text
fn sum(x: view<i32>) -> i32

sum(array)
```

Compiler tạo ephemeral view.

Có thể cho:

```text
T → dyn Trait
```

chỉ khi language semantics xác định rõ và conversion này **explicitly requests dynamic dispatch**.

Không cho implicit:

```text
i64 → i32
f64 → i32
pointer → integer
integer → pointer
T → Box<T>
T → Arc<T>
T → String
```

---

# 13. Explicit Conversion

Dùng:

```text
as
```

Ví dụ:

```text
let x: i32 = y as i32
```

Compiler kiểm tra conversion cụ thể.

Các conversion có thể có semantics:

```text
NumericCast
EnumCast
PointerCast
RepresentationCast
FFICast
```

Không gom tất cả thành một "cast thần kỳ".

---

# 14. CAST vs BITCAST

Đây là hai operation hoàn toàn khác nhau.

### CAST

Thay đổi semantic value:

```text
let x: i64 = y as i64
```

### BITCAST

Giữ nguyên bit pattern:

```text
let x: u32 = bitcast<f32, u32>(f)
```

`BITCAST` chỉ hợp lệ nếu:

```text
size(T) == size(U)
alignment contract hợp lệ
representation của U hợp lệ
```

Compiler không được biến `bitcast` thành numeric conversion.

---

# 15. Numeric Literal Resolution

Literal:

```text
42
```

không mặc định ngay lập tức thành `i32` trong parser.

Parser tạo:

```text
IntegerLiteral(42)
```

Type resolution quyết định type dựa trên context.

Ví dụ:

```text
let a: i64 = 42
```

→ `i64`.

```text
let b: u8 = 42
```

→ `u8`.

Nếu không có context, Axiom có một defaulting rule deterministic.

Ví dụ baseline:

```text
integer literal → i32
floating literal → f64
```

nhưng chỉ sau khi constraint solving không xác định được type.

---

# 16. Literal overflow

Ví dụ:

```text
let x: u8 = 300
```

phải là compile error.

Không:

```text
300 → 44
```

ngầm.

Nếu muốn wrapping:

```text
let x = 300 as u8
```

và conversion semantics phải được định nghĩa rõ.

---

# 17. Assignment

Assignment không phải function call thông thường.

```text
x = expr
```

semantic:

```text
evaluate RHS
verify destination writable
perform move/copy according to type semantics
drop old destination if required
```

Ví dụ:

```text
a = b
```

nếu `T: Copy`:

```text
copy b → a
```

nếu `T: !Copy`:

```text
move b → a
```

Sau đó:

```text
b
```

không còn usable nếu ownership đã chuyển.

---

# 18. Assignment vào field

```text
obj.value = x
```

Compiler kiểm tra capability:

```text
WRITE(obj.value)
```

Không cần programmer lấy mutable reference.

Đây chính là lợi thế của Axiom:

```text
obj.value = x
```

vẫn có semantics tương đương hệ thống ownership mạnh, nhưng syntax không mang theo borrow checker bureaucracy.

---

# 19. Compound Assignment

```text
x += y
```

không nhất thiết tương đương:

```text
x = x + y
```

vì `x` có thể:

- non-Copy;
- có side effect khi indexing;
- là một Place phức tạp.

Compiler semantic node riêng:

```text
CompoundAssign(
    place = x,
    operator = AddAssign,
    rhs = y
)
```

để tránh evaluate destination nhiều lần.

Ví dụ:

```text
get_array()[get_index()] += f()
```

không được biến thành một expression có thể gọi `get_array()` hoặc `get_index()` nhiều lần.

---

# 20. Indexing

```text
a[i]
```

có hai semantic form:

```text
READ_INDEX
WRITE_INDEX
```

Compiler có thể resolve thông qua:

```text
Index<T>
IndexMut<T>
```

nhưng capability semantics vẫn do compiler kiểm tra.

Ví dụ:

```text
let x = a[i]
```

→ READ.

```text
a[i] = x
```

→ WRITE.

---

# 21. Slice

```text
a[start:end]
```

tạo:

```text
view<T>
```

hoặc:

```text
mut_view<T>
```

tùy context.

Compiler phải chứng minh:

```text
0 <= start <= end <= len
```

hoặc hạ bounds checking xuống runtime nếu không chứng minh được.

Nếu runtime check cần thiết:

```text
bounds_check
```

được biểu diễn rõ trong MIR và có thể bị optimizer loại bỏ khi proven.

---

# 22. Field Access

```text
obj.field
```

là semantic projection:

```text
Place(
    base = obj,
    projection = Field(field_id)
)
```

Điều này cực kỳ quan trọng đối với ownership analysis.

Ví dụ:

```text
a.x
a.y
```

có thể được coi là hai region:

```text
Region(a.x)
Region(a.y)
```

và compiler có thể cho:

```text
mutate(a.x)
read(a.y)
```

nếu chứng minh disjoint.

---

# 23. `?` operator

`?` là built-in control-flow operator.

Ví dụ:

```text
let x = foo()?;
```

semantic equivalent:

```text
match foo() {
    Ok(v) => v,
    Err(e) => return Err(e)
}
```

nhưng compiler không thực sự cần tạo AST `match`.

Có thể lower trực tiếp:

```text
CALL foo
SWITCH_RESULT
RETURN_ERROR
CONTINUE_SUCCESS
```

Điều này cho phép zero-cost abstraction.

---

# 24. `await`

`await` cũng là built-in control-flow boundary.

```text
let x = future.await;
```

không phải function call bình thường.

Compiler phải:

```text
evaluate future
check live capabilities
check non-Send state
create suspension point
lower coroutine state
resume
```

Do đó Expression Engine chỉ resolve semantics; Async Lowering Engine xử lý transformation sau đó.

---

# 25. Closure Expression

Closure:

```text
|x| x + 1
```

được expression resolver xác định:

```text
parameter types
return type
captured variables
capture mode
trait implementation
```

Ví dụ:

```text
let f = |x| x + offset
```

Compiler xác định:

```text
capture offset
```

là:

```text
READ capture
```

hoặc:

```text
MOVE capture
```

tùy semantics.

Closure transformation sẽ thuộc task riêng sau Expression Engine.

---

# 26. No hidden allocation

Expression resolution tuyệt đối không được tự sinh:

```text
Box
heap allocation
Arc
temporary object header
runtime object
```

trừ khi semantics của expression thực sự yêu cầu.

Ví dụ:

```text
let x = a + b
```

không được mặc định tạo heap temporary.

Compiler có thể:

```text
SSA value
register
stack temporary
```

tùy backend.

---

# 27. Temporary Lifetime

Temporary value có lifetime semantic rõ ràng.

Ví dụ:

```text
foo(make_vec())
```

temporary phải sống đủ lâu cho call.

Nhưng compiler được phép:

```text
registerize
inline
scalarize
eliminate
```

nếu observable semantics không đổi.

Temporary không được vô tình trở thành một lifetime extension mechanism cho `view`.

---

# 28. Overload Ranking

Candidate ranking nên cực kỳ deterministic:

```text
Rank 0: exact type match
Rank 1: non-owning safe view coercion
Rank 2: approved lossless coercion
Rank 3: generic instantiation
Rank 4: trait-based operator resolution
```

Không nên có hàng chục mức conversion như C++.

Nếu hai candidate có cùng rank:

```text
AMBIGUOUS
```

→ yêu cầu programmer viết rõ:

```text
foo(x as i64)
```

thay vì compiler đoán.

---

# 29. Generic Inference

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

gọi:

```text
max(x, y)
```

Compiler tạo constraint:

```text
T = type(x)
T = type(y)
T : Ord
```

Sau đó trait solver kiểm tra.

Nếu:

```text
type(x) != type(y)
```

thì không tự động tìm conversion nếu không có rule phù hợp.

---

# 30. Expression Effect Summary

Mỗi resolved expression có effect summary:

```text
ExprEffect {
    reads
    writes
    moves
    drops
    allocates
    deallocates
    atomics
    volatile
    io
    panic
    synchronize
    suspend
    foreign
}
```

Ví dụ:

```text
x + y
```

thường:

```text
Read(x)
Read(y)
Pure
```

Trong khi:

```text
buffer[i] = foo()
```

có thể:

```text
Call(foo)
Write(buffer[i])
BoundsCheck
```

Effect information này được chuyển xuống HIR/MIR và dùng lại bởi:

- ownership;
- alias analysis;
- escape analysis;
- optimizer;
- async;
- GPU;
- parallel analysis.

---

# 31. Constant Evaluation

Expression Engine phải phân biệt:

```text
Runtime expression
Const-evaluable expression
Comptime expression
```

Ví dụ:

```text
const X = 10 * 20;
```

có thể được evaluate tại compile time.

Nhưng:

```text
let x = runtime() * 20;
```

không được compiler tự biến thành comptime semantics.

Optimizer có thể constant-fold nếu chứng minh được, nhưng:

> **optimization folding ≠ language-level comptime evaluation.**

Điều này giữ semantics deterministic.

---

# 32. Expression → HIR

Sau resolution:

```text
AST
 ↓
Resolved Expression
 ↓
Typed HIR Expression
```

Ví dụ:

```text
a + b
```

có thể thành:

```text
HirBinary {
    op: Add,
    lhs: HirPlaceRead(a),
    rhs: HirPlaceRead(b),
    resolved_impl: Add_i32,
    type: i32
}
```

Sau đó MIR không còn cần "đoán" operator.

---

# 33. CompilerDB bổ sung

Task này thêm:

```text
ExprDB
OperatorDB
CallResolutionDB
OverloadDB
ConversionDB
CastDB
LiteralDB
MethodResolutionDB
IndexResolutionDB
AssignmentDB
PlaceDB
TemporaryDB
ExpressionEffectDB
ConstExpressionDB
GenericInferenceDB
CandidateDB
CandidateRankingDB
```

Các query quan trọng:

```text
resolve_expr(expr_id)
type_of(expr_id)
place_of(expr_id)
resolve_call(call_id)
resolve_operator(op_id)
resolve_method(call_id)
resolve_index(index_id)
resolve_conversion(src, dst)
resolve_cast(src, dst, kind)
literal_type(literal_id)
expression_effect(expr_id)
```

---

# 34. Diagnostic Model

Không nên báo:

```text
cannot compile expression
```

mà phải chỉ rõ compiler reasoning.

Ví dụ:

```text
AXM-E355-001

Ambiguous call to `foo`

Candidates:
  foo(i32)
  foo(i64)

Argument:
  x : integer literal

No contextual type selects a candidate.

Help:
  specify the type explicitly:
      foo(x as i64)
```

Hoặc:

```text
AXM-E355-014

Implicit conversion from `i64` to `i32` is not allowed
because it may lose information.

Use an explicit conversion:
    value as i32

If wrapping semantics are intended:
    wrapping_cast(value)
```

AI có thể sử dụng structured diagnostic thay vì phải parse human prose.

---

# 35. Những gì compiler được phép làm

Sau khi expression semantics đã được resolve, optimizer có thể:

```text
constant fold
inline
devirtualize
eliminate temporary
eliminate bounds check
fuse operations
vectorize
scalarize
remove allocation
reorder independent operations
```

nhưng chỉ khi proof system xác nhận semantic equivalence.

---

# 36. Những gì compiler không được tự ý làm

Không được tự biến:

```text
i64 → i32
```

chỉ vì ABI nhanh hơn.

Không được biến:

```text
dyn Trait
```

thành static dispatch nếu việc đó thay đổi observable behavior của dynamic dispatch.

Không được bỏ:

```text
volatile
atomic
IO
synchronization
panic
```

chỉ vì expression "có vẻ không dùng kết quả".

Không được thay đổi evaluation order khi có observable effect.

---

# 37. Invariants bắt buộc

Task này đóng băng các invariant:

```text
AEXPR-01  Every resolved expression has exactly one semantic type.

AEXPR-02  Every callable expression resolves to exactly one callable or fails deterministically.

AEXPR-03  Overload resolution is independent of declaration/file/hash iteration order.

AEXPR-04  Evaluation order is deterministic.

AEXPR-05  No implicit lossy numeric conversion.

AEXPR-06  No implicit pointer/integer conversion.

AEXPR-07  Explicit cast and bitcast are semantically distinct.

AEXPR-08  Bitcast requires valid representation compatibility.

AEXPR-09  Assignment respects ownership semantics.

AEXPR-10  Move of non-Copy value invalidates its source.

AEXPR-11  Copy never creates implicit shared mutable ownership.

AEXPR-12  Place access is capability-checked.

AEXPR-13  Field projections preserve place identity.

AEXPR-14  Indexing has explicit read/write semantics.

AEXPR-15  Slice/view creation preserves provenance.

AEXPR-16  Operator overload cannot change operator precedence.

AEXPR-17  Operator set is closed in Core.

AEXPR-18  Short-circuit operators preserve lazy evaluation.

AEXPR-19  `?` is control-flow semantics, not ordinary function dispatch.

AEXPR-20  `await` is a suspension boundary.

AEXPR-21  Expression resolution cannot introduce hidden heap allocation.

AEXPR-22  Expression resolution cannot introduce hidden dynamic dispatch.

AEXPR-23  Generic inference is deterministic.

AEXPR-24  Ambiguous overloads are compile errors.

AEXPR-25  Literal defaulting occurs only after contextual constraints fail to determine type.

AEXPR-26  Literal overflow is diagnosed rather than silently truncated.

AEXPR-27  Expression effects are explicitly represented.

AEXPR-28  Const evaluation does not alter runtime semantics.

AEXPR-29  Only Verified HIR/MIR may enter optimization.

AEXPR-30  Optimization cannot change resolved expression semantics.
```

---

## 39. Vị trí trong compiler pipeline

Sau task này pipeline trở nên rõ:

```text
Lexer
  ↓
Parser
  ↓
Module Discovery
  ↓
Declaration Collection
  ↓
Name Resolution
  ↓
Type Resolution
  ↓
Trait Resolution
  ↓
★ Expression / Operator / Overload Resolution
  ↓
Typed HIR
  ↓
Closure Analysis
  ↓
Async Analysis
  ↓
Pattern Lowering
  ↓
MIR
  ↓
Ownership / Capability / Effect / Escape Verification
  ↓
Optimization
```

Điểm quan trọng là **MIR không còn phải giải quyết những câu hỏi ngôn ngữ cấp cao** như:

> "`+` nghĩa là gì?"  
> "hàm nào được gọi?"  
> "kiểu của literal này là gì?"  
> "conversion nào được dùng?"

Tất cả phải được quyết định trước khi bước vào MIR.

### Kết luận của BOOTSTRAP-355

Đây là lớp giúp Axiom đạt triết lý:

> **Syntax đơn giản cho programmer, semantic resolution mạnh cho compiler.**

Programmer viết:

```text
result = object.items[i] + offset
```

nhưng compiler bên dưới đã biết chính xác:

```text
name binding
→ type
→ place
→ capability
→ indexing implementation
→ operator implementation
→ conversions
→ ownership
→ effects
→ evaluation order
→ ABI
```

mà không cần bắt programmer viết ra hàng loạt pointer/reference/lifetime/operator-dispatch machinery.