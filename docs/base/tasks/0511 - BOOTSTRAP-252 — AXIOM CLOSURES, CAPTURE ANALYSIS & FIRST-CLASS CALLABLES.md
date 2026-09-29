# BOOTSTRAP-252 — AXIOM CLOSURES, CAPTURE ANALYSIS & FIRST-CLASS CALLABLES

**TRẠNG THÁI: FROZEN / COMPLETED**

## 1. Mục tiêu

Closure trong Axiom phải đạt được đồng thời:

- cú pháp ngắn gọn;
- capture tự động;
- không cần programmer khai báo lifetime;
- không mặc định heap allocation;
- không mặc định virtual dispatch;
- không mặc định object header;
- không mặc định garbage collection;
- generic closure có static dispatch;
- compiler có thể inline/eliminate hoàn toàn closure;
- closure có thể dùng trong iterator, async, GPU/comptime khi hợp lệ;
- ownership/capability/Send/Share vẫn được verifier kiểm soát.

Nguyên tắc:

> **Closure là một value có callable behavior và capture state; không phải một object/class đặc biệt.**

---

# 2. Cú pháp canonical

```axiom
let offset = 10

let add = |x: i32| x + offset
```

Closure có:

```text
parameters
body
captured environment
callable contract
```

---

# 3. Closure không phải function declaration

```axiom
fn add(x: i32, y: i32) -> i32 {
    x + y
}
```

là function declaration.

Trong khi:

```axiom
let add = |x| x + offset
```

là closure value.

---

# 4. Closure semantic model

Compiler có thể conceptualize:

```text
closure:
    fn_ptr
    environment
```

nhưng đây **không phải ABI bắt buộc**.

Compiler hoàn toàn có thể biến:

```axiom
let f = |x| x + 10
f(20)
```

thành:

```text
30
```

hoặc inline trực tiếp.

---

# 5. Hidden environment struct

Ví dụ:

```axiom
let a = 10
let b = 20

let f = |x| x + a + b
```

Compiler semantic model:

```text
struct ClosureEnv {
    a: i32
    b: i32
}

fn closure_fn(env: ClosureEnv, x: i32) -> i32 {
    x + env.a + env.b
}
```

Đây là **compiler-generated representation**, không phải source-level type mà programmer phải viết.

---

# 6. Environment không nhất thiết tồn tại

Nếu compiler chứng minh:

```text
a = constant
b = constant
```

environment có thể biến mất.

```text
f(x) = x + 30
```

---

# 7. Closure type là anonymous nominal compiler type

Mỗi closure expression tạo một semantic callable type riêng.

Ví dụ:

```axiom
let a = |x| x + 1
let b = |x| x + 1
```

`type(a)` và `type(b)` không mặc định giống nhau.

---

# 8. Nhưng cả hai có thể implement cùng callable trait

Ví dụ conceptual:

```text
Callable<(i32) -> i32>
```

Điều này cho phép generic code nhận closure.

---

# 9. Callable protocol

Axiom nên có các semantic callable capabilities:

```text
Fn
FnMut
FnOnce
```

theo ý nghĩa access/consumption, nhưng **không cần copy nguyên mô hình Rust một cách máy móc**.

Định nghĩa:

```text
Fn
    callable without consuming environment

FnMut
    callable with mutable access to environment

FnOnce
    callable by consuming environment
```

---

# 10. Đây là access capability, không phải inheritance

Không có:

```text
class Closure
```

và không có runtime inheritance tree.

Đây là trait contracts.

---

# 11. `Fn`

Ví dụ:

```axiom
let offset = 10

let f = |x: i32| x + offset
```

Nếu chỉ đọc capture:

```text
environment access = READ
```

closure có thể satisfy `Fn`.

---

# 12. `FnMut`

Ví dụ:

```axiom
let mut total = 0

let add = |x: i32| {
    total += x
}
```

Closure cần:

```text
WRITE(total)
```

nên callable contract là mutable.

---

# 13. `FnOnce`

Nếu closure consume captured owner:

```axiom
let data = make_data()

let consume = || process(data)
```

và `process` consumes `data`, closure environment có ownership obligation.

Closure invocation có thể consume environment.

---

# 14. Không tự động Clone capture

Đây là invariant quan trọng.

```axiom
let data = make_data()

let f = || consume(data)
```

Compiler không được:

```text
clone(data)
```

để làm closure callable nhiều lần.

---

# 15. Repeated invocation

Nếu closure là `FnOnce`:

```axiom
f()
f()
```

lần thứ hai phải bị reject nếu lần đầu đã consume environment.

---

# 16. Callable contract

Semantic callable type có thể được mô hình hóa:

```text
Callable {
    Parameters
    Return
    Effects
    CaptureMode
    Consumption
}
```

---

# 17. Effects

Closure có thể có effect:

```text
Pure
Read
Write
Allocate
IO
Async
Unsafe
...
```

theo Effect System đã frozen.

---

# 18. Function và closure thống nhất ở call site

Cả:

```axiom
f(x)
```

và:

```axiom
closure(x)
```

đều dùng một `Call` semantic operation.

Resolver xác định callable target.

---

# 19. Static dispatch mặc định

Generic:

```axiom
fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}
```

sẽ static dispatch.

---

# 20. Monomorphization

Ví dụ:

```axiom
apply(|x| x + 1, 10)
```

compiler có thể tạo specialization:

```text
apply::<ClosureType123>
```

và inline.

---

# 21. Không bắt buộc heap

Closure:

```axiom
let f = |x| x + 1
```

có thể nằm:

```text
register
stack
SSA
caller storage
```

---

# 22. Escape analysis

Nếu:

```axiom
fn test() {
    let f = |x| x + 1
    f(10)
}
```

closure không escape.

Compiler có thể eliminate environment + closure value.

---

# 23. Closure return

Nếu:

```axiom
fn make_adder(n: i32) -> ??? {
    |x| x + n
}
```

closure environment phải sống cùng returned closure.

Compiler có thể:

```text
return ClosureEnv { n }
```

không nhất thiết heap allocate.

---

# 24. Caller-allocated closure return

Compiler ABI có thể dùng:

```text
caller-provided return storage
```

nếu closure representation cần storage.

---

# 25. Closure passed to another function

```axiom
fn apply<F: Fn(i32) -> i32>(f: F) -> i32 {
    f(10)
}
```

`f` được truyền theo value semantics.

Nếu closure nhỏ:

```text
register passing
```

có thể được sử dụng.

---

# 26. Large closure

Closure capture:

```text
large environment
```

có thể được stack/heap/arena allocated theo escape analysis và ABI.

Không có guarantee rằng closure luôn stack.

---

# 27. Heap allocation is not closure semantics

Đây là invariant:

> Closure existence ≠ heap allocation.

---

# 28. Closure capture inference

Compiler phân tích body.

Ví dụ:

```axiom
let x = ...
let f = || inspect(x)
```

nếu `inspect` chỉ đọc:

```text
capture x → READ
```

---

# 29. Mutable capture

```axiom
let mut x = 0

let f = || x += 1
```

→

```text
capture x → WRITE
```

---

# 30. Move capture

```axiom
let x = make_resource()

let f = || consume(x)
```

→

```text
capture x → OWN
```

---

# 31. Capture inference không dựa vào cú pháp `move`

Axiom không cần:

```text
move |x| ...
```

làm syntax bắt buộc.

Compiler suy ra từ semantic use.

---

# 32. Tại sao?

Mục tiêu của Axiom:

> Programmer mô tả **ý định sử dụng**, compiler suy ra storage/ownership mechanics.

---

# 33. Nhưng compiler không được đoán mơ hồ

Nếu có nhiều semantic possibilities:

```text
Copy
Move
View
```

mà không thể xác định deterministic:

→ compile error hoặc yêu cầu explicit API boundary.

Không heuristic.

---

# 34. Closure capture of Copy value

```axiom
let x: i32 = 10
let f = || x + 1
```

Compiler có thể capture value.

Không tạo ownership obligation đặc biệt.

---

# 35. Closure capture of non-Copy owner

```axiom
let s = String(...)
let f = || inspect(s)
```

Compiler phải đảm bảo environment giữ access hợp lệ.

---

# 36. Environment field semantics

Mỗi capture có metadata:

```text
CaptureId
SourcePlace
CaptureMode
TypeId
Capability
OwnershipState
EscapeState
```

---

# 37. Capture by reference — semantic concept

Axiom có thể internally represent:

```text
environment field → reference/capability
```

nhưng programmer không cần viết `&T`.

---

# 38. View capture

Nếu closure chỉ cần đọc owner:

```text
environment:
    view<T>
```

Compiler phải chứng minh owner sống đủ lâu.

---

# 39. Escaping closure + view

Ví dụ:

```axiom
fn make() -> ??? {
    let x = data()
    || inspect(x)
}
```

Nếu closure giữ view tới local `x`, invalid.

Compiler không cho closure escape.

---

# 40. Compiler có thể chọn ownership capture

Nếu cần return closure:

```text
move x into environment
```

nếu semantics cho phép và không làm thay đổi observable behavior.

---

# 41. Nhưng không được silently change observable aliasing

Nếu external capability tồn tại:

```text
x
 └── active view
```

compiler không được biến ownership semantics thành cách khác làm thay đổi validity.

---

# 42. Closure capture + mutable alias

```axiom
let mut x = ...
let f = || mutate(x)
```

Closure giữ exclusive mutable capability.

Trong thời gian capability đang bị closure giữ:

```text
direct mutation x
```

có thể bị reject.

---

# 43. Example

```axiom
let mut x = 0

let f = || {
    x += 1
}

x += 2
```

Compiler phải xác định lifetime của closure capture.

Nếu `f` vẫn live và capture WRITE:

→ xung đột.

Nếu `f` đã dead:

→ compiler có thể kết thúc capture capability.

---

# 44. Lifetime inference

Không có:

```text
'a
```

trong source.

Compiler sử dụng:

```text
CaptureLifetime
```

nội bộ.

---

# 45. Closure destruction

Closure environment có Drop nếu captured resources có Drop.

```text
closure dropped
→ captured owners dropped
```

theo ownership semantics.

---

# 46. Capture order

Compiler cần deterministic environment field ordering.

Đề xuất:

```text
source capture order
```

là semantic ordering cho destruction.

Representation vẫn có thể reorder nếu không observable.

---

# 47. Environment layout

Default:

```text
compiler-controlled
```

Giống struct layout.

---

# 48. Explicit representation

Closure không được expose stable ABI layout mặc định.

Nếu cần FFI:

```text
closure → explicit function pointer + userdata contract
```

---

# 49. FFI closure

Không cho:

```axiom
extern "C" fn register_callback(f: Closure)
```

trừ khi ABI contract định nghĩa representation.

---

# 50. C callback adapter

Library có thể cung cấp:

```text
Callback {
    function_pointer
    context_pointer
    destructor
}
```

với unsafe/FFI boundary được kiểm soát.

---

# 51. Function pointer

Function pointer là callable machine-level value:

```text
fn(i32) -> i32
```

khác closure type.

---

# 52. Non-capturing closure

```axiom
let f = |x: i32| x + 1
```

có thể convert sang function pointer nếu không capture.

```text
Closure → FunctionPointer
```

là coercion compiler-defined.

---

# 53. Capturing closure không implicit function pointer

```axiom
let n = 10
let f = |x| x + n
```

không thể biến thành bare function pointer vì cần environment.

---

# 54. Explicit callback ABI

Nếu cần:

```text
fn_ptr + context
```

library/system layer định nghĩa ABI.

---

# 55. `dyn Fn`

Dynamic callable:

```axiom
dyn Fn(i32) -> i32
```

là explicit type erasure.

---

# 56. Representation

Conceptually:

```text
data pointer
+
call table
```

nhưng physical representation là ABI detail.

---

# 57. Dynamic callable không imply heap

Một `dyn Fn` có thể tham chiếu tới externally stored closure/environment.

Heap allocation chỉ xảy ra nếu chosen storage strategy yêu cầu.

---

# 58. But dynamic storage needs ownership contract

Nếu dynamic callable owns environment:

```text
Box<dyn Fn(...)>
```

là library ownership abstraction.

---

# 59. `dyn Fn` object safety

Callable trait phải object-safe theo trait rules.

Generic callable contracts không tự động dynamic.

---

# 60. Downcast

Không implicit:

```text
dyn Fn → concrete closure
```

Nếu runtime metadata/type identity được sử dụng:

→ explicit operation.

---

# 61. Closure + Send

Closure là `Send` nếu toàn bộ captured state và callable semantics đáp ứng Send.

Ví dụ:

```text
capture:
    i32       → Send
    SendData  → Send
```

→ closure có thể Send.

---

# 62. Closure + Share

Closure là Share nếu environment có thể được safely shared theo Share semantics.

Capture mutable state thường ngăn Share nếu không có synchronization abstraction.

---

# 63. Closure + thread spawn

```axiom
spawn(|| work(data))
```

`spawn` yêu cầu closure đáp ứng contract tương ứng:

```text
Send
appropriate lifetime/storage
```

Compiler kiểm tra closure environment.

---

# 64. No `'static`

Programmer không phải viết:

```text
F: Send + 'static
```

Compiler suy ra escape/storage requirement.

---

# 65. Closure + async

```axiom
let f = async |x| {
    await work(x)
}
```

Async closure tạo:

```text
closure environment
+
Future state machine
```

---

# 66. Capture across await

Captured value sống qua suspension phải được đưa vào Future state nếu cần.

---

# 67. Mutable capture across await

Compiler phải kiểm tra:

```text
mutable capability
live across suspension
```

và không cho xung đột concurrent access.

---

# 68. Async closure Send

Send của async closure phải xét:

```text
closure environment
+
Future state
```

chứ không chỉ capture ban đầu.

---

# 69. Closure + iterator

Đây là use case quan trọng:

```axiom
values.map(|x| x * 2)
```

Compiler nên biến thành:

```text
iterator adapter
+
inline closure
```

và loại bỏ mọi abstraction overhead khi có thể.

---

# 70. Closure + filter

```axiom
values.filter(|x| x > threshold)
```

`threshold` trở thành captured field nếu cần.

---

# 71. Closure + mutable iterator

Closure WRITE capability phải tương thích với iterator's `mut_view`.

---

# 72. Disjoint capture

Ví dụ:

```axiom
let mut p = Point(...)

let fx = || p.x += 1
let fy = || p.y += 1
```

Compiler có thể chứng minh:

```text
p.x
p.y
```

DISJOINT.

Hai mutable capabilities có thể tồn tại đồng thời nếu usage model cho phép.

---

# 73. Whole-object capture

Nếu closure dùng:

```axiom
p
```

toàn bộ object có thể bị capture.

Compiler không được tự ý chia nhỏ capture nếu điều đó làm thay đổi observable ownership/capability semantics.

---

# 74. Field-sensitive capture optimization

Ngược lại, nếu semantic use chỉ đọc `p.x`, compiler có thể internally capture field `p.x` nếu proof đảm bảo equivalent.

Đây là optimization, không phải source semantic rule.

---

# 75. Closure environment scalar replacement

Ví dụ:

```axiom
let a = 1
let f = |x| x + a
```

Optimizer có thể eliminate:

```text
ClosureEnv
```

hoàn toàn.

---

# 76. Closure inlining

Nếu call target statically known:

```text
closure call
→ inline body
```

---

# 77. Closure specialization

Generic:

```axiom
fn apply<F: Fn(i32) -> i32>(f: F, x: i32)
```

có thể specialize theo closure type.

---

# 78. Code sharing

Không bắt buộc tạo một machine-code copy cho mỗi closure.

Compiler có thể share code khi environment/calling convention cho phép.

---

# 79. No forced monomorphization explosion

Axiom sử dụng hybrid strategy:

```text
small hot closure
→ specialize/inlining

large/cold generic
→ code sharing
```

---

# 80. Closure ABI

Internal closure ABI có thể:

```text
ClosureValue {
    call_target
    environment
}
```

nhưng ABI optimizer được phép flatten:

```text
environment fields
+
direct function call
```

---

# 81. Stable ABI

Không expose anonymous closure ABI qua:

```text
@abi(stable)
```

trực tiếp.

---

# 82. Stable callback

Phải chuyển sang explicit contract:

```text
CallbackFn
CallbackContext
CallbackDrop
```

hoặc named trait ABI.

---

# 83. Closure type identity

Compiler tạo:

```text
ClosureId
ClosureTypeId
EnvironmentTypeId
```

---

# 84. Source identity

Closure identity phải ổn định qua incremental compilation dựa trên semantic source identity, không phụ thuộc memory address compiler.

---

# 85. Closure fingerprints

```text
ClosureFingerprint
    = source identity
    + parameter types
    + return type
    + captures
    + callable contract
    + relevant effects
```

---

# 86. Closure and comptime

Closure có thể chạy trong `comptime` nếu:

- body comptime-legal;
- captured values comptime-available;
- không dùng runtime-only capabilities.

---

# 87. Comptime closure

```axiom
comptime {
    let offset = 10
    let f = |x| x + offset
    const_value = f(20)
}
```

Compiler execution environment quản lý closure.

Không tạo runtime closure nếu value không escape.

---

# 88. Closure escape from comptime

Runtime closure chỉ được materialize khi semantic generation explicitly yêu cầu.

---

# 89. Closure + GPU

Closure trong GPU code phải satisfy GPU legality.

Compiler có thể inline closure.

---

# 90. GPU closure restrictions

Không cho closure capture:

```text
File
Socket
OS Handle
Host-only object
```

vào GPU kernel.

---

# 91. GPU capture

Capture chỉ có thể chứa data/storage hợp lệ cho execution domain.

---

# 92. Closure + unsafe

Closure có thể chứa unsafe operations:

```axiom
let f = |p| unsafe {
    *p
}
```

nhưng closure không làm mất verifier boundary.

Unsafe operation được kiểm tra tại chính operation.

---

# 93. Closure + raw pointer

Raw pointer capture là machine value.

Pointer không trở thành owner chỉ vì được capture.

---

# 94. Closure + Drop

Nếu:

```axiom
let resource = open()

let f = || inspect(resource)
```

và closure owns resource, Drop của closure environment phải release resource đúng một lần.

---

# 95. Closure cycle

Ví dụ closures tự giữ nhau qua shared ownership có thể tạo logical cycle.

Axiom không tự động garbage collect cycle.

Library `Weak`/cycle-breaking abstractions chịu trách nhiệm.

---

# 96. Closure recursive reference

Direct:

```axiom
let f = || f()
```

không tự động hợp lệ vì binding chưa hoàn tất.

Recursive closure cần explicit named function hoặc indirection abstraction.

---

# 97. Named function preferred for recursion

```axiom
fn factorial(n: u64) -> u64 {
    ...
}
```

đây là canonical route.

---

# 98. Closure and recursion through environment

Có thể hỗ trợ thông qua explicit:

```text
Box<dyn Fn(...)>
```

hoặc recursive callable abstraction của library.

Không đưa hidden recursive heap machinery vào Core.

---

# 99. Closure evaluation order

Closure creation evaluates captures theo semantic evaluation order.

Capture expressions phải được evaluate deterministic.

---

# 100. Closure creation does not execute body

```axiom
let f = |x| side_effect(x)
```

không gọi `side_effect`.

---

# 101. Capture side effects

Nếu capture expression thực sự là expression:

```axiom
let f = || use(make_data())
```

`make_data()` nằm trong body, không chạy khi closure tạo.

---

# 102. Immediate invocation

```axiom
(|x| x + 1)(10)
```

Compiler có thể inline hoàn toàn.

---

# 103. Closure as return value

```axiom
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    |x| x + n
}
```

`impl Trait` có thể là static opaque callable type.

---

# 104. `impl Trait`

Đây là cách expose:

```text
concrete closure behavior
```

mà không expose anonymous closure type name.

---

# 105. Dynamic alternative

Nếu caller thực sự cần runtime polymorphism:

```axiom
dyn Fn(i32) -> i32
```

explicit.

---

# 106. Static vs dynamic

Axiom principle:

```text
generic/impl Fn
    → static

dyn Fn
    → dynamic
```

Không compiler silently chuyển static callable thành dynamic.

---

# 107. Closure callable variance

Function parameter compatibility phải obey normal function type variance rules đã được type system định nghĩa.

Không tạo special closure variance model.

---

# 108. Closure parameter inference

```axiom
let f = |x| x + 1
```

`x` type có thể được infer từ body/expected context.

Nếu context không đủ để resolve:

→ diagnostic.

---

# 109. Deterministic inference

Không phụ thuộc:

```text
source order
hash order
optimizer
```

---

# 110. Closure overload resolution

Khi truyền closure vào overloaded/generic functions:

compiler resolve expected callable contract trước.

Không thử hàng trăm candidates heuristic.

---

# 111. Closure and trait bounds

Ví dụ:

```axiom
fn sort_by<F: Fn(Item, Item) -> Ordering>(f: F)
```

Trait solver chứng minh closure satisfies callable contract.

---

# 112. Closure and effects

Nếu API yêu cầu:

```text
Pure Fn
```

closure có IO effect không satisfy.

---

# 113. Example

```axiom
fn calculate<F: Fn(i32) -> i32>(f: F) -> i32
```

Closure:

```axiom
|x| x * 2
```

→ valid.

Closure:

```axiom
|x| {
    print(x)
    x * 2
}
```

→ chỉ valid nếu callable contract cho phép IO effect.

---

# 114. Effect-aware callable type

Conceptual:

```text
Fn<(i32) -> i32, Effects={Pure}>
```

hoặc equivalent internal representation.

Surface syntax có thể giữ đơn giản.

---

# 115. Closure and exception

Không có exception semantics.

Panic/Result là normal Axiom semantics.

---

# 116. Closure returning Result

```axiom
let f = |x| -> Result<i32, Error> {
    ...
}
```

ordinary value semantics.

---

# 117. Closure with `?`

```axiom
let f = |x| {
    parse(x)?
}
```

`?` applies to closure's return Result/Option context.

---

# 118. Closure environment and ownership verifier

Verifier input:

```text
CapturePlan
```

với mỗi capture:

```text
source place
access mode
ownership transition
lifetime
escape
```

---

# 119. Capture analysis pipeline

```text
Closure AST
    ↓
Closure Resolver
    ↓
Capture Discovery
    ↓
Capture Classification
    ↓
Callable Contract
    ↓
Ownership/Capability Verification
    ↓
Escape Analysis
    ↓
Closure Environment
    ↓
Typed HIR
```

---

# 120. Capture classification

Compiler dùng:

```text
READ
WRITE
MOVE
```

và có thể:

```text
ADDRESS/STABLE-ADDRESS
```

khi hệ thống code yêu cầu.

---

# 121. Capture lattice

Một capture không nên có nhiều mode mâu thuẫn.

Conceptual ordering:

```text
READ
  ↓
WRITE
  ↓
MOVE
```

nhưng đây không phải subtype relation.

Nó biểu diễn resource requirement tăng dần.

---

# 122. Upgrade capture

Nếu compiler ban đầu thấy READ:

```text
inspect(x)
```

sau đó body dùng:

```text
consume(x)
```

capture được nâng thành MOVE.

---

# 123. Capture conflict

Hai closures:

```axiom
let f = || mutate(x)
let g = || mutate(x)
```

không nhất thiết invalid ngay khi tạo.

Verifier xét **overlapping live capability periods**.

---

# 124. Non-overlap

Nếu:

```axiom
f()
drop(f)

g()
```

thì capability của `f` có thể kết thúc trước `g`.

---

# 125. Explicit `drop`

Programmer có thể dùng:

```axiom
drop(f)
```

để kết thúc ownership/capability sớm.

---

# 126. Compiler liveness

Compiler cũng có thể chứng minh closure không còn dùng sau một điểm.

Nó có thể kết thúc semantic lifetime sớm nếu không observable.

---

# 127. Environment borrowing

Closure không cần expose:

```text
&mut self
```

internally callable receiver có thể là:

```text
mut_view<Environment>
```

theo callable trait semantics.

---

# 128. `Fn` conceptual signature

```text
call(self: view<Self>, args...)
```

---

# 129. `FnMut`

```text
call(self: mut_view<Self>, args...)
```

---

# 130. `FnOnce`

```text
call(self: Self, args...)
```

conceptually.

Đây là semantic model; source syntax có thể không expose các signatures này.

---

# 131. Đây là cách Axiom tránh `this`

Closure environment cũng không cần class/object model.

Nó chỉ là compiler-generated struct + function.

---

# 132. Closure environment methods

Compiler internally có thể generate:

```text
call(env, args)
```

Không có hidden virtual method table nếu static.

---

# 133. Dynamic callable

Chỉ khi:

```text
dyn Fn
```

mới cần dynamic dispatch representation.

---

# 134. Closure environment layout optimization

Compiler có thể:

- reorder fields;
- eliminate fields;
- scalarize fields;
- constant-fold fields;
- merge equivalent captures;
- capture subfields;
- register-promote.

Miễn semantic ownership/capability không đổi.

---

# 135. Capture coalescing

Nếu:

```axiom
let a = ...
let f = || a.x + a.y
```

compiler có thể capture:

```text
a.x
a.y
```

thay vì entire `a`, nếu ownership/drop semantics vẫn equivalent.

---

# 136. Drop-sensitive capture

Nếu `a` có Drop:

```text
capture only a.x
```

không được bỏ qua semantic Drop của `a` nếu việc đó thay đổi resource lifetime.

---

# 137. Compiler must distinguish

```text
logical capture
```

và:

```text
physical capture
```

Logical capture belongs to semantic model.

Physical capture is optimization.

---

# 138. Closure + allocation

Escape analysis:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
```

giống global escape model.

---

# 139. NoEscape

Closure can be fully stack/register/SSA.

---

# 140. ReturnEscape

Closure environment must survive caller frame.

Compiler may use:

```text
caller allocation
heap
arena
static
```

depending on storage contract.

---

# 141. ThreadEscape

Closure sent to another execution domain requires:

```text
Send
storage validity
capability validity
```

---

# 142. ExternalEscape

Passing closure to foreign code requires explicit callback lifetime contract.

---

# 143. Closure + synchronization

Capturing:

```text
Arc<Mutex<T>>
```

is legal according to ordinary Share/Send rules.

Closure itself does not make access synchronized.

---

# 144. Closure + atomic

Capturing `Atomic<T>` allows concurrent semantics only through atomic API.

Compiler does not transform ordinary field into atomic.

---

# 145. Closure + GPU synchronization

Capture of device resources requires explicit device ownership and execution-domain contracts.

---

# 146. Closure + serialization

Anonymous closure is not serializable by default.

Reason:

```text
code identity
environment
compiler version
ABI
```

are not ordinary data interchange semantics.

---

# 147. Explicit closure serialization

Possible only through library-defined named function + serializable state abstraction.

---

# 148. Closure + reflection

Compile-time reflection can inspect closure metadata if compiler exposes it.

Runtime reflection is optional.

---

# 149. Closure + metadata

`.axmeta` may contain:

```text
ClosureId
callable signature
capture type metadata
```

only when required by tooling/ABI/debug/reflection profile.

---

# 150. Tiny binary principle

If closure is fully static and optimized:

```text
no closure metadata
no runtime closure support
no allocation
no vtable
```

need be linked.

---

# 151. Debugging

Debug build should still allow:

```text
closure source
capture source
environment fields
call target
```

mapping.

---

# 152. Optimized debugging

Even if environment eliminated:

debug metadata can describe:

```text
logical capture
→ optimized location / unavailable
```

---

# 153. AI tooling

`ax explain closure` can report:

```text
Closure C17

captures:
    x: READ
    buffer: MOVE

callable:
    FnOnce

effects:
    Read

escape:
    ThreadEscape

Send:
    proven
```

---

# 154. Why this is important

AI coding tools do not need to infer hidden ownership mechanics from syntax.

Compiler exposes the semantic facts directly.

---

# 155. Closure diagnostics

Recommended:

```text
ACLOSURE-E001
Cannot call consumed FnOnce closure

ACLOSURE-E002
Captured value would outlive its owner

ACLOSURE-E003
Mutable capture conflicts with active access

ACLOSURE-E004
Closure is not Send

ACLOSURE-E005
Closure is not Share

ACLOSURE-E006
Closure is not valid for target execution domain

ACLOSURE-E007
Closure cannot satisfy callable effect contract

ACLOSURE-E008
Capturing closure cannot coerce to function pointer

ACLOSURE-E009
Foreign callback requires explicit lifetime contract

ACLOSURE-E010
Recursive closure requires explicit indirection
```

---

# 156. Formal closure model

Define:

```text
Closure C = (Code, Environment, CallableContract)
```

Environment:

```text
E = { c1, c2, ... cn }
```

Each capture:

```text
ci = (Place, Mode, Type, Capability)
```

---

# 157. Invocation

For `C(args)`:

```text
verify callable contract
verify environment capability
evaluate arguments left-to-right
invoke Code(E,args)
```

---

# 158. `Fn`

Invocation preserves environment ownership.

---

# 159. `FnMut`

Invocation temporarily acquires exclusive mutable access to environment.

---

# 160. `FnOnce`

Invocation consumes environment.

---

# 161. Async closure

```text
AsyncClosure =
    (Environment, FutureStateMachine, CallableContract)
```

---

# 162. Closure optimization invariant

Any transformation:

```text
closure → function
closure → inline expression
closure → specialized function
closure → direct environment fields
```

is legal only when observable semantics remain identical.

---

# 163. No hidden semantic allocation

Compiler may allocate physically, but allocation itself is not observable unless storage/address/allocation failure is part of explicit semantic contract.

---

# 164. Address-sensitive closure

If closure environment address is externally observable through unsafe/system API:

```text
stable storage contract
```

becomes relevant.

Optimizer cannot relocate it without preserving contract.

---

# 165. Closure and `Box`

```axiom
let f = Box::new(|| work())
```

`Box` is library storage semantics.

Closure itself does not require Box.

---

# 166. Closure and `Arc`

```axiom
let f = Arc::new(|| work(shared))
```

shared closure environment obeys normal Arc/Share rules.

---

# 167. Closure cycles

Axiom does not introduce special closure cycle collector.

---

# 168. Closure and stack

A closure may live on stack only if its escape/storage constraints allow.

Returning it requires promotion/caller allocation/other storage.

---

# 169. Closure and register

Zero-sized/stateless closures may compile to nothing more than a direct function symbol or even disappear entirely.

---

# 170. Zero-sized closure

```axiom
let f = || 42
```

semantic closure value exists, but physical representation can be zero-sized.

---

# 171. Function pointer coercion

For zero-capture closure:

```text
ClosureType → fn(...)
```

allowed only when ABI and effects are compatible.

---

# 172. Effect compatibility

A closure requiring IO cannot coerce into a callable function type whose contract excludes IO.

---

# 173. Closure + generic callable

Generic callable parameters preserve static type information.

---

# 174. Closure + dynamic callable

`dyn Fn` intentionally erases concrete closure type.

---

# 175. Dynamic dispatch cost is explicit

The programmer/API author chooses:

```text
generic F
```

versus:

```text
dyn Fn
```

rather than compiler silently inserting dynamic dispatch.

---

# 176. No universal closure runtime

There is no mandatory:

```text
ClosureRuntime
```

in every Axiom executable.

---

# 177. Compiler architecture

Add to `CompilerDB`:

```text
ClosureDB
CaptureDB
CallableDB
ClosureEnvDB
ClosureEscapeDB
ClosureAbiDB
```

---

# 178. IDs

```text
ClosureId
CaptureId
CallableTypeId
EnvironmentFieldId
CallableInstanceId
```

---

# 179. HIR representation

Conceptual:

```text
ClosureExpr {
    closure_id
    params
    body
    expected_callable
}
```

After analysis:

```text
TypedClosure {
    closure_type
    captures[]
    callable_contract
    effects
}
```

---

# 180. MIR representation

Possible operations:

```text
MakeClosure
CallClosure
DropClosure
CaptureLoad
CaptureMove
CaptureWrite
```

---

# 181. `MakeClosure`

Semantic operation creates closure value/environment.

Backend may eliminate it.

---

# 182. `CallClosure`

Semantic callable invocation.

Backend may lower to:

```text
direct_call
indirect_call
inlined_body
specialized_call
```

---

# 183. `DropClosure`

Runs environment cleanup.

---

# 184. Closure verification

Before Verified MIR:

```text
Capture analysis
↓
Ownership
↓
Capability
↓
Send/Share
↓
Effect
↓
Escape
↓
Async/GPU/FFI legality
```

---

# 185. Optimization pipeline

After verification:

```text
ClosureInlining
ClosureSpecialization
ClosureEnvironmentElimination
CaptureScalarReplacement
CaptureConstantPropagation
ClosureCallDevirtualization
ClosureDeadFieldElimination
ClosureCodeSharing
```

---

# 186. Important separation

Compiler must not optimize:

```text
unknown capture
```

as if:

```text
no capture
```

---

# 187. UNKNOWN remains UNKNOWN

Giống alias system:

```text
UNKNOWN ≠ NO_CAPTURE
```

unless proof exists.

---

# 188. Closure safety does not depend on optimization

At `-O0`:

```text
closure semantics correct
```

At `-O3`:

```text
same semantics
```

---

# 189. Closure conformance tests

Test categories:

```text
capture-copy
capture-move
capture-write
partial-capture
drop
Fn
FnMut
FnOnce
Send
Share
escape
return
async
GPU
comptime
FFI
dynamic callable
function-pointer coercion
```

---

# 190. Adversarial tests

Đặc biệt:

```text
closure captures moved field
closure captures mutable field while view active
closure returned with dead capture owner
closure sent across thread with non-Send capture
closure shared with mutable non-Share capture
closure dropped twice
FnOnce invoked twice
closure environment relocation with stable-address contract
```

---

# 191. Formal correctness boundary

```text
AST
 ↓
Typed Closure
 ↓
Capture Plan
 ↓
Ownership/Capability Verification
 ↓
Verified MIR
```

Không được bỏ qua Capture Plan để trực tiếp optimize closure.

---

# 192. Semantic Oracle

Reference interpreter có thể model closure trực tiếp:

```text
ClosureValue {
    code
    environment
}
```

không cần mô phỏng physical ABI.

---

# 193. Differential testing

So sánh:

```text
reference closure
vs
MIR closure
vs
optimized closure
vs
native closure
```

---

# 194. Translation validation

Closure optimization phải preserve:

```text
return values
effects
ownership-visible behavior
resource cleanup
panic
external effects
```

---

# 195. Closure + panic

Nếu closure panic:

```text
closure environment
```

được cleanup theo normal panic/unwind profile.

---

# 196. Closure + cancellation

Nếu async closure bị cancellation:

```text
Future state
+
closure-owned resources
```

Drop theo async ownership rules.

Không có implicit asynchronous destructor.

---

# 197. Closure + mutex guard

Nếu closure captures sync guard:

```text
guard
```

không được cross `.await` nếu guard không async-safe.

---

# 198. Closure + UI

UI callbacks thường có:

```text
WidgetId
State handle
```

thay vì raw pointer capture.

Ownership/Send/Share rules vẫn áp dụng.

---

# 199. Closure + networking

Callback nhận:

```text
Buffer
view
mut_view
```

phải obey completion lifetime.

Không capture ephemeral network view qua asynchronous boundary nếu không hợp lệ.

---

# 200. Closure + database

Transaction closure có thể được API thiết kế:

```axiom
db.transaction(|tx| {
    ...
})
```

Transaction object có ownership/capability semantics riêng.

Closure chỉ là callable abstraction.

---

# 201. Closure + serialization

Không serialize anonymous executable code.

---

# 202. Closure + AI-generated code

AI có thể query:

```text
capture plan
callable contract
escape
Send/Share
effects
```

thay vì phải đoán.

---

# 203. Compiler explanation

Ví dụ:

```text
ax explain closure C17
```

có thể trả:

```text
Captured `buffer` by ownership because `send()` consumes it.

The closure is FnOnce.

The closure escapes through `spawn()`.

Send is proven because Buffer is Send.

No heap allocation is required by the semantic model.
```

---

# 204. Đây là điểm rất quan trọng đối với mục tiêu Axiom

Programmer viết:

```axiom
spawn(|| process(buffer))
```

không phải:

```text
spawn(move || 'static + Send + ...)
```

Compiler vẫn thực hiện lượng phân tích rất phức tạp phía dưới.

**Độ phức tạp compiler tăng; độ phức tạp ngôn ngữ không tăng tương ứng.**

Đây chính là triết lý Axiom.

---

# 205. Frozen invariants

```text
ACLOSURE-20
A closure is a first-class callable value with captured environment.

ACLOSURE-21
Closures are not classes or objects.

ACLOSURE-22
Closure semantics do not require heap allocation.

ACLOSURE-23
Closure semantics do not require object headers.

ACLOSURE-24
Closure semantics do not require garbage collection.

ACLOSURE-25
Each closure expression has a distinct semantic closure type.

ACLOSURE-26
Closures may satisfy callable traits.

ACLOSURE-27
Static callable dispatch is the default.

ACLOSURE-28
Dynamic callable dispatch requires explicit dyn callable semantics.

ACLOSURE-29
Closure capture is inferred by semantic use.

ACLOSURE-30
Capture inference is deterministic.

ACLOSURE-31
Capture inference never silently inserts Clone.

ACLOSURE-32
Captured Copy values do not create additional ownership obligations.

ACLOSURE-33
Captured non-Copy values obey normal ownership semantics.

ACLOSURE-34
Captured mutable state requires exclusive capability.

ACLOSURE-35
Captured read access requires valid provenance.

ACLOSURE-36
Closure-held capabilities cannot outlive their provenance.

ACLOSURE-37
Closure capture does not bypass capability verification.

ACLOSURE-38
Closure capture does not bypass Send verification.

ACLOSURE-39
Closure capture does not bypass Share verification.

ACLOSURE-40
Fn represents callable read access to the environment.

ACLOSURE-41
FnMut represents callable mutable access to the environment.

ACLOSURE-42
FnOnce represents callable ownership-consuming access to the environment.

ACLOSURE-43
Calling FnOnce consumes the required callable state.

ACLOSURE-44
A consumed FnOnce closure cannot be invoked again.

ACLOSURE-45
Closure Drop follows ordinary ownership and Drop semantics.

ACLOSURE-46
Captured Drop resources are released exactly once.

ACLOSURE-47
Closure environment representation is compiler-controlled by default.

ACLOSURE-48
Closure environment layout is not stable ABI by default.

ACLOSURE-49
Stable ABI callbacks require an explicit callback representation.

ACLOSURE-50
Non-capturing closures may coerce to compatible function pointers.

ACLOSURE-51
Capturing closures do not implicitly coerce to bare function pointers.

ACLOSURE-52
Closure callable effects are part of callable semantics.

ACLOSURE-53
A closure cannot satisfy a callable effect contract it violates.

ACLOSURE-54
Closure inference does not depend on optimization.

ACLOSURE-55
Closure ownership semantics do not depend on optimization.

ACLOSURE-56
Closure capability semantics do not depend on optimization.

ACLOSURE-57
Closure escape analysis is an optimization and storage analysis.

ACLOSURE-58
Closure escape analysis may eliminate physical environment allocation.

ACLOSURE-59
Closure environment elimination must preserve semantic ownership.

ACLOSURE-60
Closure environment elimination must preserve capability semantics.

ACLOSURE-61
Closure inlining preserves observable behavior.

ACLOSURE-62
Closure specialization may be used for zero-cost generic dispatch.

ACLOSURE-63
Generic closure calls use static dispatch unless explicitly erased.

ACLOSURE-64
Dynamic callable representation is an ABI/runtime concern, not a concrete closure requirement.

ACLOSURE-65
Closure types may be represented by compiler-generated environment structures.

ACLOSURE-66
Generated closure environments are not source-level classes.

ACLOSURE-67
Closure capture may be field-sensitive when semantic equivalence is proven.

ACLOSURE-68
Physical capture optimization cannot alter Drop obligations.

ACLOSURE-69
Unknown capture facts cannot be treated as no capture.

ACLOSURE-70
Closure capabilities participate in ordinary liveness analysis.

ACLOSURE-71
Closure capabilities may end when the closure becomes semantically dead.

ACLOSURE-72
Explicit drop may end closure-owned capabilities early.

ACLOSURE-73
Returned closures must preserve all required environment state.

ACLOSURE-74
Returned closures cannot contain dangling capabilities.

ACLOSURE-75
Thread-escaping closures must satisfy Send requirements.

ACLOSURE-76
Shared closures must satisfy Share requirements.

ACLOSURE-77
Closure Send does not imply closure Share.

ACLOSURE-78
Closure Share does not imply mutable sharing.

ACLOSURE-79
Async closures obey async suspension and ownership rules.

ACLOSURE-80
Captured state live across await becomes part of required async state.

ACLOSURE-81
Async closure Send is determined from its complete suspension state.

ACLOSURE-82
Closures in GPU code must satisfy GPU legality.

ACLOSURE-83
Host-only resources cannot be implicitly captured by GPU closures.

ACLOSURE-84
Comptime closures obey comptime capability restrictions.

ACLOSURE-85
Comptime closure execution does not imply runtime closure allocation.

ACLOSURE-86
Unsafe closure operations remain subject to unsafe verification boundaries.

ACLOSURE-87
Raw pointer capture does not create ownership.

ACLOSURE-88
Foreign callbacks require explicit ABI and lifetime contracts.

ACLOSURE-89
Anonymous closure code is not serializable by default.

ACLOSURE-90
Closure reflection is compile-time by default.

ACLOSURE-91
Runtime closure metadata is optional.

ACLOSURE-92
Closure debugging preserves source-to-capture provenance.

ACLOSURE-93
Closure diagnostics expose capture and callable facts.

ACLOSURE-94
AI tooling may query closure facts but cannot override verification.

ACLOSURE-95
Closure creation does not execute the closure body.

ACLOSURE-96
Closure capture evaluation follows deterministic evaluation order.

ACLOSURE-97
Closure recursive behavior requires explicit supported indirection.

ACLOSURE-98
Closure optimization occurs only after semantic verification.

ACLOSURE-99
Closure optimization cannot change observable external effects.

ACLOSURE-100
Closure semantics are represented by the Semantic Oracle.

ACLOSURE-101
Closure semantics are independent of physical storage location.

ACLOSURE-102
Closure semantics are independent of register allocation.

ACLOSURE-103
Closure semantics are independent of machine ABI unless explicitly exposed.

ACLOSURE-104
Closure abstraction overhead should be eliminated when provably unnecessary.

ACLOSURE-105
Closure compilation must preserve source-level callable semantics at every optimization level.
```

---

# 206. Kiến trúc sau BOOTSTRAP-252

Axiom hiện có một chuỗi rất đẹp:

```text
                 FUNCTION
                    │
              ┌─────┴─────┐
              │           │
           METHOD       CLOSURE
              │           │
              └─────┬─────┘
                    │
                 CALLABLE
                    │
          ┌─────────┴─────────┐
          │                   │
       STATIC              DYNAMIC
       Generic             dyn Trait
          │                   │
       inline             explicit dispatch
```

và closure:

```text
Closure
  │
  ├── Code
  │
  └── Environment
        │
        ├── Copy capture
        ├── Read capture
        ├── Write capture
        └── Move capture
```

nhưng tất cả cuối cùng vẫn quay về:

```text
Place
Ownership
Capability
Effect
Escape
Send/Share
Drop
```

Không cần thêm một memory model mới.

---

# BOOTSTRAP-253 — AXIOM GENERATORS, ITERATOR STATE MACHINES & LAZY CONTROL FLOW

Task kế tiếp nên chốt **generator/yield** và mối quan hệ giữa:

```text
Iterator
Generator
async/await
Future
state machine
yield
suspension
ownership
views
Drop
Send
```

Đây là phần còn thiếu để hoàn thiện abstraction control-flow của Axiom. Mục tiêu sẽ là quyết định liệu Axiom cần một keyword `yield` thực sự hay có thể xây toàn bộ generator bằng `Iterator + closure + state machine`, đồng thời tránh biến generator thành một runtime-heavy feature.