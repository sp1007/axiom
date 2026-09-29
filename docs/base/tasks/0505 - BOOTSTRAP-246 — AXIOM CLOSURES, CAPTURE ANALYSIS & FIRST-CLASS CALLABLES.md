# BOOTSTRAP-246 — AXIOM CLOSURES, CAPTURE ANALYSIS & FIRST-CLASS CALLABLES

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần hoàn thiện mô hình **behavior** của Axiom. Mục tiêu là closure phải mạnh như closure hiện đại, nhưng không biến thành một object runtime nặng nề.

Nguyên tắc trung tâm:

> **Closure là một giá trị callable có environment được compiler sinh ra; capture mode, layout, lifetime và allocation đều do compiler suy luận từ cách closure được sử dụng.**

Không có `this`, không có object header bắt buộc, không có GC, không có hidden clone.

---

# 1. Closure là gì?

Ví dụ:

```axiom
let offset = 10

let add = |x| x + offset
```

Semantic:

```text
Closure {
    code = generated_function
    environment = { offset }
}
```

Nhưng đây chỉ là **semantic model**.

Physical representation có thể là:

```text
registers
stack
inline struct
caller storage
heap
```

hoặc closure hoàn toàn bị compiler loại bỏ.

---

# 2. Closure không phải class/object

Closure không tạo:

```text
object header
virtual table
GC metadata
```

trừ khi programmer/API explicitly yêu cầu dynamic callable representation.

---

# 3. Closure type là anonymous compiler-generated type

Ví dụ:

```axiom
let f = |x| x + offset
```

compiler conceptually tạo:

```text
ClosureType$123
```

với:

```text
call(...)
capture: offset
```

Nhưng type name này không cần xuất hiện trong source.

---

# 4. Closure type có identity

Hai closure:

```axiom
let a = |x| x + 1
let b = |x| x + 1
```

không mặc định có cùng nominal type.

Mỗi closure expression tạo một callable type riêng.

---

# 5. Closure không nhất thiết có runtime identity

Nếu:

```axiom
let x = 10
let y = (|a| a + x)(5)
```

compiler có thể inline:

```text
y = 15
```

Closure không tồn tại runtime.

---

# 6. Capture analysis

Compiler phân tích:

```text
Free variables
```

của closure.

Ví dụ:

```axiom
let a = 10
let b = 20

let f = |x| x + a
```

capture set:

```text
{ a }
```

`b` không được capture.

---

# 7. Không capture thừa

Compiler **không capture toàn bộ lexical scope**.

Đây là invariant quan trọng để environment nhỏ.

---

# 8. Capture mode

Capture mode được compiler suy luận:

```text
READ
COPY
MOVE
VIEW
MUT_VIEW
```

dựa trên cách variable được sử dụng.

---

# 9. Read capture

```axiom
let n = 10
let f = || n + 1
```

Nếu `n: Copy`:

```text
capture(n) = Copy
```

Environment có thể chứa một value.

---

# 10. Owning non-Copy capture

```axiom
let file = open_file()

let f = || use(file)
```

Nếu closure không escape:

compiler có thể borrow/view nội bộ trong thời gian cần thiết.

Nếu closure escape:

compiler phải đảm bảo ownership của `file` tồn tại cùng closure.

---

# 11. Move capture

Axiom không yêu cầu Rust-style:

```text
move || ...
```

Capture mode được suy luận từ semantic requirements.

Ví dụ:

```axiom
let data = make_large_buffer()

let f = || consume(data)
```

Closure cần ownership:

```text
capture(data) = MOVE
```

---

# 12. Capture inference là semantic analysis

Compiler xem:

```text
closure body
+
usage context
+
escape analysis
+
callable expected type
```

để xác định capture.

Không dựa đơn thuần vào syntax.

---

# 13. Capture chỉ đủ sống khi cần

Ví dụ:

```axiom
let x = 10

let f = || x

use(f)
```

Sau `use(f)` nếu không còn closure:

compiler kết thúc closure/environment lifetime.

---

# 14. Closure escaping

Ví dụ:

```axiom
fn make_adder(x: i32) -> ??? {
    |y| x + y
}
```

Closure escape khỏi function.

Compiler phải đảm bảo:

```text
x
```

vẫn tồn tại.

Do đó environment thường sở hữu capture hoặc chứa representation có lifetime hợp lệ.

---

# 15. Không bắt programmer khai báo lifetime

Không cần:

```text
'a
```

hoặc:

```text
move
'static
```

trong Core closure syntax.

Compiler tự kiểm tra escape.

---

# 16. Closure returning view

Ví dụ:

```axiom
fn make_view(x: String) -> ??? {
    || view(x)
}
```

Nếu closure escape cùng `x`, compiler phải preserve provenance.

Nếu `x` local sẽ bị Drop trước closure:

→ reject.

---

# 17. Closure cannot hide dangling capability

Ví dụ:

```axiom
fn bad() {
    let s = make_string()
    let f = || view(s)
    return f
}
```

Nếu returned closure không own `s` và capability có thể outlive `s`:

→ compile error.

Compiler không cho closure trở thành “lifetime loophole”.

---

# 18. Closure + Place Model

Capture thực chất là capture từ một Place.

Ví dụ:

```axiom
let user = make_user()

let f = || user.name
```

compiler có thể capture:

```text
Place(user.name)
```

thay vì toàn bộ:

```text
user
```

nếu semantics cho phép.

---

# 19. Field-sensitive capture

Đây là optimization rất quan trọng.

```axiom
let user = User {
    name: ...,
    age: ...
}

let f = || user.age
```

compiler có thể capture:

```text
user.age
```

chứ không cần giữ toàn bộ `User`.

---

# 20. Partial ownership capture

Nếu:

```axiom
let user = User {
    name: String,
    age: u32
}
```

và closure consumes:

```axiom
let f = || consume(user.name)
```

compiler có thể đánh dấu:

```text
user.name → Move
user.age  → remains
```

theo Place ownership tree.

---

# 21. Closure environment

Semantic:

```text
ClosureEnv {
    capture_0
    capture_1
    ...
}
```

Environment layout được compiler tối ưu.

Không có stable layout mặc định.

---

# 22. Environment layout

Compiler có thể:

```text
reorder fields
remove padding
pack captures
scalarize
split environment
```

miễn semantics không expose layout.

---

# 23. Closure environment có thể biến mất

```axiom
let a = 10
let f = |x| x + a
let y = f(20)
```

Inlining:

```text
y = 30
```

Không closure allocation.

---

# 24. Closure allocation elimination

Nếu closure:

```text
does not escape
```

compiler ưu tiên:

```text
stack/register/SSA
```

hoặc eliminate hoàn toàn.

---

# 25. Escaping closure

Nếu:

```axiom
return |x| x + captured
```

closure representation phải survive caller lifetime.

Compiler có thể:

```text
caller allocate
inline environment
heap allocate
arena allocate
```

tùy ownership/storage contract.

---

# 26. Không có mặc định “closure = heap”

Đây là invariant quan trọng.

Closure không đồng nghĩa:

```text
heap allocation
```

---

# 27. Callable categories

Axiom phân biệt:

```text
Function
Function Pointer
Non-capturing Closure
Capturing Closure
Dyn Callable
```

---

# 28. Ordinary function

```axiom
fn add(x: i32, y: i32) -> i32 {
    x + y
}
```

có compile-time known function identity.

---

# 29. Function pointer

Function pointer là runtime machine-level callable value:

```text
fn(i32, i32) -> i32
```

Có thể chứa:

```text
code address
```

theo target ABI.

Không có capture environment.

---

# 30. Non-capturing closure

```axiom
let f = |x| x + 1
```

Không capture.

Có thể decay/coerce sang compatible function pointer:

```text
Closure
   ↓
Function Pointer
```

nếu signature tương thích.

---

# 31. Capturing closure không tự decay

```axiom
let n = 10
let f = |x| x + n
```

không thể tự chuyển thành function pointer vì cần environment.

Phải dùng callable abstraction phù hợp.

---

# 32. Generic callable

Ví dụ:

```axiom
fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}
```

Static dispatch mặc định.

Compiler có thể specialize:

```text
apply::<ClosureType$1>
```

và inline.

---

# 33. Callable traits

Conceptual:

```axiom
trait Fn<Args> {
    type Output
    fn call(self: view<Self>, args: Args) -> Self::Output
}
```

Tương tự:

```text
Fn
FnMut
FnOnce
```

nhưng semantic distinction cần chính xác.

---

# 34. `Fn`

Callable có thể gọi nhiều lần mà không consume environment.

Ví dụ:

```axiom
let f = |x| x + 1
```

---

# 35. `FnMut`

Closure cần mutable access vào captured state.

Ví dụ:

```axiom
let mut total = 0

let mut add = |x| {
    total += x
}
```

Compiler nhận ra:

```text
capture(total) = mutable capability
```

---

# 36. `FnOnce`

Closure consumes captured value:

```axiom
let resource = acquire()

let consume = || use_and_consume(resource)
```

Closure chỉ có thể invoke theo ownership semantics phù hợp.

---

# 37. Không cần programmer annotate

Không cần:

```text
impl FnMut
```

hay annotation capture mode.

Compiler derives callable capabilities.

---

# 38. Callable trait hierarchy

Conceptually:

```text
Fn
↑
FnMut
↑
FnOnce
```

Nhưng cần tránh hiểu đây là class inheritance.

Đây là capability relation:

```text
callability guarantees
```

---

# 39. Recommended semantic direction

Axiom coi:

```text
Fn
FnMut
FnOnce
```

là compiler/library traits có relationship logic.

Không phải object inheritance.

---

# 40. Calling closure

```axiom
f(x)
```

resolver xác định:

```text
Function
Closure
Function Pointer
Callable Trait
```

và canonicalize thành callable invocation.

---

# 41. Method syntax không cần riêng

Nếu callable type cung cấp:

```text
call(...)
```

compiler có thể lower:

```text
f(x)
```

thành callable operation.

Không cần object dispatch.

---

# 42. Closure + ownership

Closure invocation phải obey:

```text
Copy
Move
View
MutView
Drop
```

giống mọi value khác.

---

# 43. Calling `FnOnce`

Nếu closure consumes itself:

```text
Move(environment)
```

→ sau call closure không còn valid.

---

# 44. Calling `FnMut`

Compiler cần exclusive mutable access vào environment:

```text
mut_view(environment)
```

nên không thể đồng thời invoke cùng mutable closure từ conflicting contexts.

---

# 45. Calling `Fn`

Read-only access:

```text
view(environment)
```

nhiều concurrent calls có thể hợp lệ nếu closure/environment là `Share`.

---

# 46. Closure + Send

Một closure được gửi sang thread:

```axiom
spawn(|| work(data))
```

phải satisfy:

```text
Send
```

đối với toàn bộ captured state.

---

# 47. Closure + Share

Closure có thể được shared nếu:

```text
closure: Share
```

và tất cả captured state thỏa relevant synchronization rules.

Không phải closure nào cũng tự động Share.

---

# 48. Closure + async

```axiom
let f = async || {
    await work()
}
```

có thể được hỗ trợ nếu surface syntax cần.

Semantic result là Future-producing closure.

---

# 49. Async closure state

Compiler-generated environment + Future state có thể được hợp nhất:

```text
Closure Environment
        +
Future State
        ↓
optimized state machine
```

Không bắt buộc tạo hai object.

---

# 50. Await capture rules

Nếu captured view không hợp lệ qua suspension:

```text
closure
  ↓
await
  ↓
view remains live
```

→ compiler reject nếu storage contract không cho phép.

---

# 51. Async closure Send

Nếu future được `spawn`:

```text
Future: Send
```

phải được kiểm tra dựa trên **state sống qua await**, không chỉ source-level capture.

---

# 52. Closure + GPU

Không cho closure arbitrary trở thành GPU kernel.

GPU callable phải thỏa:

```text
@kernel
```

hoặc GPU execution annotation thích hợp.

Compiler kiểm tra GPU legality riêng.

---

# 53. Closure capture on GPU

GPU closure/kernel capture chỉ được chứa:

```text
GPU-legal values
```

và storage domains phù hợp.

Không capture:

```text
File
Socket
OS Handle
Host-only pointer
```

vào GPU kernel.

---

# 54. Closure + comptime

Comptime closure có thể chạy trong compiler VM nếu:

```text
comptime callable
```

nhưng capability sandbox vẫn áp dụng.

Không tự động biến thành runtime closure.

---

# 55. Closure + FFI

Capturing closure không tự động chuyển thành:

```text
C function pointer
```

vì C function pointer không có environment.

---

# 56. FFI callback

Library có thể tạo callback representation:

```text
extern "C" fn(...)
+
context pointer
```

và chịu trách nhiệm lifetime/context contract.

Unsafe boundary phải bảo vệ environment.

---

# 57. Closure callback lifetime

Ví dụ:

```axiom
register_callback(|| use(state))
```

Compiler phải biết callback:

```text
synchronous
asynchronous
retained
one-shot
```

từ API contract.

Nếu retained:

captured values phải survive callback lifetime.

---

# 58. No hidden clone for callback

Nếu callback API yêu cầu ownership:

```text
register(callback)
```

closure được Move.

Không tự động Clone environment.

---

# 59. Closure and recursion

Closure:

```axiom
let f = |x| f(x - 1)
```

không tự động hợp lệ vì `f` chưa fully initialized khi capture.

Recursive closures cần explicit mechanism.

Ví dụ library/generic indirection có thể cung cấp:

```text
FnBox
Recursive<T>
```

hoặc named function.

---

# 60. Named function preferred for recursion

Core:

```axiom
fn factorial(n: u64) -> u64 {
    if n == 0 { 1 }
    else { n * factorial(n - 1) }
}
```

không cần closure recursion.

---

# 61. Closure equality

Closures không mặc định:

```text
Eq
Hash
```

vì environment/function identity không có universal semantic equality.

---

# 62. Closure Copy

Closure có thể là `Copy` nếu:

```text
all captures Copy
+
closure semantics permit Copy
```

Ví dụ noncapturing closure thường có thể Copy.

Nhưng compiler phải derive theo semantic rules, không chỉ bitwise representation.

---

# 63. Closure Clone

Nếu captures Clone:

```text
f.clone()
```

có thể explicit clone.

Không bao giờ implicit Clone chỉ vì closure cần được passed somewhere.

---

# 64. Closure Drop

Nếu environment chứa Drop values:

```text
Closure
    ↓
Drop
    ↓
Drop captures
```

theo deterministic reverse initialization semantics.

---

# 65. Partial closure capture

Compiler có thể capture fields separately:

```text
capture user.name
capture user.age
```

thay vì:

```text
capture user
```

nếu semantic access cho phép.

---

# 66. Closure environment and alias analysis

Ví dụ:

```axiom
let f = || x + y
let g = || x + z
```

Compiler có thể biết:

```text
f.environment.x
g.environment.x
```

cùng provenance nếu capture strategy preserves shared access.

Điều này feed AliasInfo.

---

# 67. Closure environment and optimization

Closure environment được coi như ordinary aggregate cho optimizer.

Có thể áp dụng:

```text
SROA
scalar replacement
constant propagation
dead capture elimination
field pruning
inlining
specialization
```

---

# 68. Dead capture elimination

Nếu closure capture:

```text
x
y
```

nhưng sau optimization `y` không được sử dụng:

Compiler có thể loại bỏ `y` nếu capture itself has no observable semantic effect.

---

# 69. Capture initialization may have effects

Ví dụ capture expression:

```axiom
let f = || use(make_resource())
```

Nếu capture requires executing something at closure creation, compiler không được xóa execution nếu observable.

---

# 70. Capture is not arbitrary expression evaluation

Lexical capture captures variables, not arbitrary expression result unless source semantics creates such value.

---

# 71. Evaluation order

Closure creation:

```axiom
let f = || use(x)
```

does not execute `use(x)`.

Only capture initialization, if semantically required, happens at closure creation.

---

# 72. Move capture timing

Nếu ownership transfer occurs at closure construction:

```text
x
 ↓
closure environment
```

`x` becomes moved at construction.

Compiler must preserve this observable ownership semantics.

---

# 73. Closure invocation timing

Captured value is used when closure executes, not when created, unless constant propagation proves equivalence.

---

# 74. Mutable capture

```axiom
let mut n = 0

let mut inc = || {
    n += 1
}
```

Compiler models:

```text
closure.environment
    └── n
         WRITE capability
```

---

# 75. Aliasing mutable closure

```axiom
let a = inc
let b = inc
```

Không được silently duplicate mutable environment.

Nếu closure is not Copy:

→ Move.

Nếu muốn shared mutable callable, cần explicit synchronization/shared abstraction.

---

# 76. Calling same `FnMut` concurrently

Ví dụ:

```text
spawn(inc)
spawn(inc)
```

không mặc định hợp lệ.

Cần ownership transfer hoặc synchronized shared state.

---

# 77. Closure and thread migration

Closure moved to another thread:

```text
Closure
    ↓ Move
Thread B
```

all owned captures must satisfy Send.

---

# 78. Closure and thread-local state

TLS capture semantics must remain explicit.

Compiler cannot silently turn ordinary value into TLS.

---

# 79. Closure and static variables

Capturing static/global state is different from local capture.

Compiler tracks:

```text
GlobalRead
GlobalWrite
```

effects/capabilities.

---

# 80. Closure and effects

Callable type includes effect contract:

```text
Fn(...) -> T
```

conceptually includes:

```text
effects
```

from BOOTSTRAP-232.

Thus two callables with incompatible effects cannot silently substitute for one another where effect restrictions matter.

---

# 81. Closure and purity

If Axiom later supports explicit pure functions:

```text
pure fn
```

closure purity derives from:

```text
body effects
+
capture effects
```

not from syntax alone.

---

# 82. Closure and dynamic dispatch

Explicit:

```text
dyn Fn(i32) -> i32
```

creates dynamic callable representation.

Potential runtime representation:

```text
data pointer
call pointer
```

or equivalent ABI.

---

# 83. No object header

The captured concrete closure type itself still has:

```text
no mandatory object header
```

Only dynamic callable representation may carry metadata/function pointer.

---

# 84. `dyn Fn` does not imply heap

A dynamic callable may live:

```text
stack
arena
inline storage
heap
```

depending on API.

Heap allocation is not semantic requirement.

---

# 85. Dynamic callable ownership

```text
dyn Fn(...)
```

is an ordinary type-level dynamic capability/value.

Its environment obeys:

```text
ownership
Drop
Send
Share
capability
```

---

# 86. Dynamic callable object safety

Callable traits intended for `dyn` must satisfy object-safety rules from BOOTSTRAP-240.

---

# 87. Upcasting

If callable trait relationships exist:

```text
FnMut → FnOnce
```

upcasting must obey explicit trait semantics.

No arbitrary runtime cast.

---

# 88. Downcasting

Dynamic callable downcast requires runtime metadata and is not implicit safe Core behavior.

---

# 89. Closure ABI

Closure concrete ABI is unstable/internal by default.

Compiler controls:

```text
capture layout
alignment
calling convention
environment representation
```

---

# 90. Stable ABI

Do not expose anonymous closure types through stable public ABI by default.

For FFI/plugin ABI, use:

```text
extern function
explicit callback struct
stable trait ABI
```

rather than compiler-private closure layout.

---

# 91. Closure and generic ABI

Generic functions accepting closure:

```axiom
fn apply<F: Fn(i32) -> i32>(f: F)
```

are not stable ABI unless monomorphized/internal.

Public stable ABI should use an explicit stable representation.

---

# 92. Closure specialization

Compiler can specialize:

```text
apply::<ClosureType$42>
```

and potentially inline the closure.

---

# 93. Closure code sharing

If many closure instances have identical code but different environment layouts, compiler may share generated code where profitable.

---

# 94. Closure environment representation

Possible physical forms:

```text
Environment {
    capture0
    capture1
}
```

or:

```text
register capture0
register capture1
```

or split fields.

No source-visible guarantee.

---

# 95. Closure and debug information

Debugger should expose:

```text
closure expression
capture list
capture values
```

when available.

Optimized-away captures should be marked unavailable rather than fabricated.

---

# 96. AI compiler interface

`ax explain` should be able to answer:

```text
Why does this closure capture X?
```

Example:

```text
Closure captures `buffer` because:
    body reads buffer
    call site requires closure to escape
    closure lifetime exceeds local use
```

Or:

```text
Capture eliminated:
    value constant-propagated
```

---

# 97. Closure diagnostic

If a closure cannot be returned:

```text
CLOSURE_ESCAPE_CONFLICT
```

proof:

```text
closure
 ↓
captures view
 ↓
view provenance = local variable
 ↓
local variable destroyed at function exit
 ↓
closure escapes function
```

---

# 98. Closure + view

Safe:

```axiom
fn use_now(data: view<i32>) {
    let f = || data[0]
    f()
}
```

because closure does not escape beyond `data`.

Potentially unsafe:

```axiom
fn bad(data: view<i32>) -> ??? {
    || data[0]
}
```

unless return contract permits the closure and its captured capability to preserve provenance.

---

# 99. Closure + mut_view

Mutable captured capability is stricter:

```axiom
fn f(data: mut_view<i32>) {
    let update = || data[0] += 1
    update()
}
```

valid if exclusive capability remains valid.

Concurrent aliasing is rejected.

---

# 100. Closure capture + ownership verification

The closure compiler must feed a capture plan into the same verifier:

```text
CapturePlan
     ↓
Ownership
     ↓
Capability
     ↓
Escape
     ↓
Send/Share
     ↓
Drop
```

Không tạo một “closure ownership system” riêng.

---

# 101. Closure lowering

Pipeline:

```text
Closure AST
    ↓
Free Variable Analysis
    ↓
Capture Classification
    ↓
Capture Place Analysis
    ↓
Ownership/Capability Check
    ↓
Escape Analysis
    ↓
Callable Trait Derivation
    ↓
Closure Environment Type
    ↓
Closure MIR
    ↓
Optimization
```

---

# 102. Closure MIR

Ví dụ:

```axiom
let n = 10
let f = |x| x + n
```

Conceptual:

```text
ClosureType$1 {
    n: i32
}

fn ClosureType$1::call(self: view<Self>, x: i32) -> i32 {
    self.n + x
}
```

Đây là compiler-generated representation, không phải source-level class.

---

# 103. Closure MIR có thể collapse

Sau inlining:

```text
ClosureType$1
```

có thể không còn tồn tại.

---

# 104. Closure state machine

Async closure:

```text
ClosureEnv
+
FutureState
```

có thể được combined into one compiler-generated state object.

---

# 105. Closure and recursion

Compiler-generated recursive closure types would be infinitely sized nếu environment chứa chính nó.

Do đó recursive closure phải dùng explicit indirection/dynamic mechanism.

---

# 106. Closure and generics

Closure có thể capture generic values:

```axiom
fn make<T>(x: T) -> ??? {
    || use(x)
}
```

Closure type parameterized internally by `T`.

Trait requirements for callable derive from body.

---

# 107. Closure and const generics

Captures of compile-time constants can disappear:

```axiom
const N: usize = 16
let f = |x| x + N
```

`N` may become compile-time constant rather than environment field.

---

# 108. Closure and comptime specialization

Comptime may generate closure types, but generated closure still passes:

```text
normal type checking
ownership verification
capability verification
effect verification
```

---

# 109. Closure and binary size

Naive monomorphization could produce many copies.

Axiom therefore permits:

```text
specialize hot cases
share cold/general cases
```

according to code-size/performance profile.

---

# 110. Closure and LTO

LTO can:

```text
inline closure
remove environment
merge identical code
specialize captures
```

subject to semantic contracts.

---

# 111. Closure and PGO

PGO can guide:

```text
inline
specialize
clone
share
```

but cannot alter callable semantics.

---

# 112. Closure and allocation

Allocation decision:

```text
Semantic closure
       ↓
Escape analysis
       ↓
No escape → register/stack/SSA/eliminate
Escape → caller/arena/heap/etc.
```

---

# 113. No mandatory closure runtime

There is no global:

```text
closure runtime
```

needed merely to use:

```axiom
|x| x + 1
```

---

# 114. Closure and binary output

A simple closure:

```axiom
fn main() {
    let f = |x| x + 1
    print(f(10))
}
```

can compile to code equivalent to direct:

```text
print(11)
```

if optimizer proves it.

---

# 115. Core syntax remains tiny

No new closure keywords are needed beyond:

```text
|params| expression
```

and optionally block body:

```text
|params| {
    ...
}
```

---

# 116. Closure parameter typing

Inference:

```axiom
let f = |x| x + 1
```

expected context can determine `x`.

Otherwise constraints infer a concrete type from body/use.

Ambiguous unresolved type → diagnostic.

---

# 117. Explicit annotation

When needed:

```axiom
let f = |x: i32| x + 1
```

Return type can generally be inferred.

---

# 118. Closure effects

Closure body determines effects.

For example a closure performing IO cannot be treated as pure merely because syntax looks simple.

---

# 119. Closure and deterministic evaluation

Capture initialization follows ordinary expression evaluation rules.

Invocation follows normal left-to-right argument evaluation.

No special hidden ordering.

---

# 120. FROZEN invariants

```text
ACLOSURE-20
A closure is a first-class callable value with compiler-generated environment semantics.

ACLOSURE-21
Closure syntax does not imply a runtime object header.

ACLOSURE-22
A closure type is compiler-generated and normally anonymous to source code.

ACLOSURE-23
Each closure expression has a distinct closure type unless a language rule explicitly establishes otherwise.

ACLOSURE-24
Closure capture is determined by free-variable analysis.

ACLOSURE-25
Only semantically required captures are included.

ACLOSURE-26
Capture mode is compiler-derived from usage, context, ownership, and escape requirements.

ACLOSURE-27
Capture may use value, move, view, or mutable capability semantics as appropriate.

ACLOSURE-28
Closure capture never implicitly performs Clone.

ACLOSURE-29
Closure capture participates in ordinary ownership verification.

ACLOSURE-30
Closure capture participates in ordinary capability verification.

ACLOSURE-31
Closure capture participates in escape analysis.

ACLOSURE-32
Closure capture participates in Send and Share derivation.

ACLOSURE-33
Closure environments obey ordinary Drop semantics.

ACLOSURE-34
Closure environment layout is implementation-defined unless explicitly exposed by an ABI contract.

ACLOSURE-35
Closure environments have no mandatory object header.

ACLOSURE-36
Capturing a field does not require capturing the entire enclosing object when semantic access permits field-sensitive capture.

ACLOSURE-37
Closure environments may be scalarized or eliminated.

ACLOSURE-38
Non-escaping closures need not be heap allocated.

ACLOSURE-39
Escaping closures may use caller storage, stack storage, arena storage, heap storage, or another valid storage strategy.

ACLOSURE-40
Closure allocation strategy is independent of closure semantics.

ACLOSURE-41
Non-capturing closures may coerce to compatible function pointers.

ACLOSURE-42
Capturing closures do not implicitly coerce to ordinary function pointers.

ACLOSURE-43
Function pointers and capturing closures are distinct semantic types.

ACLOSURE-44
Generic callable parameters use static dispatch by default.

ACLOSURE-45
Dynamic callable dispatch requires explicit dynamic callable representation.

ACLOSURE-46
`Fn`, `FnMut`, and `FnOnce` represent distinct callable capability guarantees.

ACLOSURE-47
Callable capability is not class inheritance.

ACLOSURE-48
`Fn` invocation requires only permitted read access to the environment.

ACLOSURE-49
`FnMut` invocation requires permitted exclusive mutable access to the environment.

ACLOSURE-50
`FnOnce` invocation may consume the closure environment.

ACLOSURE-51
Closure callable capabilities are compiler-derived where possible.

ACLOSURE-52
Closure invocation obeys ordinary Copy/Move/View/MutView semantics.

ACLOSURE-53
A closure cannot be duplicated through hidden cloning.

ACLOSURE-54
A moved closure cannot be invoked again unless validly reinitialized or otherwise represented as reusable.

ACLOSURE-55
Mutable closure environments cannot be concurrently accessed through conflicting safe capabilities.

ACLOSURE-56
Closure values moved across execution domains must satisfy Send requirements.

ACLOSURE-57
Closure sharing across execution domains must satisfy Share requirements.

ACLOSURE-58
Send does not imply Share.

ACLOSURE-59
Share does not imply mutable thread-safe access.

ACLOSURE-60
Closure captures may contain views only while their provenance remains valid.

ACLOSURE-61
A closure cannot safely escape while retaining a capability whose provenance ends earlier.

ACLOSURE-62
Closure capture of a mutable view obeys normal exclusivity rules.

ACLOSURE-63
Closure capture may be field-sensitive.

ACLOSURE-64
Closure capture may be partially moved where ownership semantics permit.

ACLOSURE-65
Custom Drop restrictions apply to partial closure captures.

ACLOSURE-66
Closure creation does not execute the closure body.

ACLOSURE-67
Capture initialization follows normal evaluation semantics.

ACLOSURE-68
Move capture establishes ownership transfer at the semantic point required by closure construction.

ACLOSURE-69
Closure invocation occurs according to ordinary function-call evaluation semantics.

ACLOSURE-70
Closure effects are derived from the closure body and captures.

ACLOSURE-71
Closure effects participate in callable type compatibility.

ACLOSURE-72
Closure allocation and environment representation may be eliminated when semantics permit.

ACLOSURE-73
Closure optimization may include inlining, scalar replacement, dead-capture elimination, specialization, and code sharing.

ACLOSURE-74
Optimization cannot change capture ownership or observable behavior.

ACLOSURE-75
Closure ABI is unstable by default.

ACLOSURE-76
Stable ABI must use an explicit stable callable representation.

ACLOSURE-77
Capturing closures cannot be exposed through a stable ABI merely by exposing their compiler-generated type.

ACLOSURE-78
FFI callbacks require explicit environment and lifetime contracts.

ACLOSURE-79
Foreign callback registration does not implicitly clone or extend closure lifetime.

ACLOSURE-80
Dynamic callable representations may exist without requiring heap allocation.

ACLOSURE-81
Dynamic callable representations obey ownership, Drop, Send, Share, and capability semantics.

ACLOSURE-82
Downcasting dynamic callables requires explicit runtime metadata and is not implicit safe behavior.

ACLOSURE-83
Recursive closures require an explicit finite-indirection mechanism when their environment would otherwise be recursively sized.

ACLOSURE-84
Async closures obey ordinary closure rules plus Future and suspension rules.

ACLOSURE-85
Closure state live across await is subject to async storage and Send verification.

ACLOSURE-86
GPU closures/kernel closures require explicit GPU legality.

ACLOSURE-87
Host-only values cannot be implicitly captured into GPU execution.

ACLOSURE-88
Comptime closures obey comptime capability and sandbox rules.

ACLOSURE-89
Generated closures re-enter normal type, ownership, capability, effect, and ABI verification.

ACLOSURE-90
Closure semantics are independent of physical storage location.

ACLOSURE-91
Closure semantics are independent of optimization level.

ACLOSURE-92
Closure debugging preserves source-to-capture provenance where available.

ACLOSURE-93
AI/compiler diagnostics can explain capture, escape, callable capability, and allocation decisions.

ACLOSURE-94
Closure analysis is incremental and cacheable.

ACLOSURE-95
Closure analysis may execute in parallel while preserving deterministic semantic results.

ACLOSURE-96
Closure environments participate in alias and effect analysis.

ACLOSURE-97
Closure environments may be optimized using the same aggregate optimization machinery as ordinary structs.

ACLOSURE-98
Closure lowering produces ordinary compiler IR rather than requiring a dedicated runtime.

ACLOSURE-99
Closure abstraction is zero-cost by design where optimization and target constraints permit.

ACLOSURE-100
No closure transformation may violate ownership, capability, lifetime, effect, Send/Share, ABI, or observable-behavior semantics.
```

---

# Kiến trúc sau BOOTSTRAP-246

Axiom hiện có mô hình callable hoàn chỉnh:

```text
                         CALLABLE
                            │
             ┌──────────────┼──────────────┐
             │              │              │
          Function      Function Ptr     Closure
                                           │
                              ┌────────────┼────────────┐
                              │            │            │
                           Fn-like      FnMut-like    FnOnce-like
                              │            │            │
                              └────────────┼────────────┘
                                           │
                                      Environment
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                            Value        View       MutView
                              │            │            │
                              └────────────┼────────────┘
                                           ▼
                                  Ownership / Capability
                                           │
                                           ▼
                                      Escape / Send
                                           │
                                           ▼
                                         MIR
```

Điểm rất quan trọng:

**Axiom không cần `class` để có abstraction có state.**

Closure environment chính là một ví dụ điển hình:

```text
state
+
function
+
compiler-derived capabilities
```

nhưng vẫn không cần object hierarchy.

---

# TASK TIẾP THEO

## **BOOTSTRAP-247 — AXIOM GENERIC INSTANTIATION, MONOMORPHIZATION, SPECIALIZATION & CODE SHARING**

Phần tiếp theo sẽ giải quyết vấn đề cực kỳ quan trọng đối với mục tiêu **hiệu năng C/C++ + binary nhỏ**:

```text
generic
    ↓
type substitution
    ↓
trait constraints
    ↓
monomorphization
    ↓
specialization
    ↓
inlining
    ↓
code sharing
    ↓
dead instantiation elimination
```

Đặc biệt phải thiết kế sao cho:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

có thể đạt hiệu năng static dispatch gần như viết riêng cho `i32`, nhưng nếu một generic được instantiate 50 kiểu thì **không biến binary thành 50 bản sao vô ích**.

Đây sẽ là nền tảng trực tiếp cho mục tiêu Axiom:

> **Generic abstraction miễn phí về runtime khi có thể, nhưng compiler phải kiểm soát code-size thay vì mù quáng monomorphize mọi thứ.**