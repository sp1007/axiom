Tiếp theo là **BOOTSTRAP-015 — Closure + Function Values**.

Đây là bước quan trọng vì Axiom đã có `fn`, generic và trait, nhưng cần một mô hình thống nhất cho **hàm như giá trị**, callback, lambda, closure, higher-order function và capture — mà vẫn giữ nguyên mục tiêu **không ép heap allocation, không ép object runtime**.

# BOOTSTRAP-015 — CLOSURE + FUNCTION VALUES

## 1. Nguyên tắc lõi

> **Function là giá trị có thể gọi. Closure là một aggregate chứa environment + callable code.**

Không có “closure runtime” bắt buộc.

Ví dụ:

```axiom
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    return f(x);
}
```

Closure:

```axiom
let add = |x| x + 10;
let y = add(5);
```

Compiler có thể biến thành:

```text
ClosureEnvironment {
    captured_value: i32
}

ClosureFunction(env*, x: i32) -> i32
```

Nhưng đây là **compiler lowering**, không phải source-level object model.

---

# 2. Phân biệt function và closure

Có hai loại callable chính:

```text
Function
    không có environment

Closure
    có environment
```

Ví dụ:

```axiom
fn square(x: i32) -> i32 {
    return x * x;
}
```

không capture gì.

Trong khi:

```axiom
let n = 10;

let add = |x: i32| x + n;
```

closure phải giữ `n`.

---

# 3. Function value

Một function có thể được đưa vào biến:

```axiom
fn square(x: i32) -> i32 {
    return x * x;
}

let f = square;
let x = f(10);
```

Type:

```text
fn(i32) -> i32
```

Function pointer/value không mang ownership của code.

---

# 4. Function pointer không phải closure

```text
fn(i32) -> i32
```

không cần environment.

Closure:

```axiom
let n = 10;
let f = |x| x + n;
```

có environment.

Không được âm thầm biến closure thành:

```text
fn(i32) -> i32
```

nếu nó capture state.

---

# 5. Non-capturing closure

Đây là ngoại lệ rất hữu ích:

```axiom
let square = |x: i32| x * x;
```

Vì không capture gì, compiler có thể chuyển thành:

```text
fn(i32) -> i32
```

Không cần environment.

Do đó:

```text
NonCapturingClosure
        ↓
FunctionValue
```

có thể zero-cost.

---

# 6. Capturing closure

Ví dụ:

```axiom
let n = 10;

let add = |x: i32| x + n;
```

Compiler tạo conceptual type:

```text
ClosureType#42 {
    n: i32
}
```

và:

```text
ClosureFn#42(env: &ClosureType#42, x: i32) -> i32
```

Call:

```text
add(5)
```

lower:

```text
ClosureFn#42(&env, 5)
```

---

# 7. Environment là aggregate bình thường

Không có:

```text
GC object
class instance
object header
```

Environment có thể được:

```text
register
stack
inline
caller-owned
heap
```

tùy escape analysis.

---

# 8. Capture mode

Axiom dùng đúng ownership model đã thiết kế.

Closure có ba capture semantics chính:

```text
READ
WRITE
MOVE
```

Ví dụ:

```axiom
let x = 10;

let f = || x;
```

→ READ capture.

---

```axiom
var x = 10;

let f = || {
    x += 1;
};
```

→ WRITE capture.

---

```axiom
let s = String(...);

let f = move || consume(s);
```

→ MOVE capture.

---

# 9. Không bắt buộc programmer khai báo capture mode

Compiler có thể infer:

```text
x được đọc
→ READ

x được mutate
→ WRITE

x bị consume
→ MOVE
```

Điều này phù hợp triết lý:

> Programmer mô tả ý định; compiler chứng minh ownership.

---

# 10. Nhưng cho phép `move`

Trong trường hợp cần ép ownership:

```axiom
let task = move || process(data);
```

`move` có ý nghĩa rõ:

```text
capture ownership
```

Không có nghĩa:

```text
heap allocation
```

---

# 11. Closure environment ownership

Ví dụ:

```axiom
let s = String(...);

let f = || use(s);
```

Compiler biết:

```text
s
↓
closure environment
```

Nếu closure không escape:

```text
stack/register
```

hoàn toàn có thể.

Nếu closure được trả về:

```axiom
fn make() -> ??? {
    let s = String(...);
    return || use(s);
}
```

environment phải có storage lifetime đủ dài.

Compiler có thể chọn dynamic storage hoặc caller-provided storage tùy representation.

---

# 12. Không mặc định heap

Đây là invariant quan trọng.

Không được định nghĩa:

```text
closure = heap object
```

Đúng phải là:

```text
closure = semantic aggregate + callable behavior
```

Storage là quyết định của compiler.

---

# 13. Closure type là anonymous nominal type

Hai closure:

```axiom
let a = |x| x + 1;
let b = |x| x + 1;
```

không nhất thiết cùng type.

Compiler có thể tạo:

```text
ClosureType#1
ClosureType#2
```

Điều này cho phép:

- capture khác nhau
- optimization độc lập
- layout khác nhau

---

# 14. Closure không phải `dyn Trait`

Đây là hai abstraction khác nhau.

Closure:

```text
compile-time known callable
```

`dyn Trait`:

```text
runtime dynamic dispatch
```

Không nên ép mọi closure vào trait object.

---

# 15. Closure generic

Ví dụ:

```axiom
fn apply<T, U>(
    x: T,
    f: ???,
) -> U {
    ...
}
```

Axiom nên cho phép compiler biểu diễn closure trực tiếp, thay vì bắt programmer viết một trait callable.

Conceptually:

```text
Callable<F, Args, Output>
```

có thể là compiler-known semantic relation.

---

# 16. Không cần Fn/FnMut/FnOnce trong Core

Một số ngôn ngữ dùng:

```text
Fn
FnMut
FnOnce
```

Axiom không cần bắt programmer tiếp xúc với ba trait này trong Core v1.

Compiler đã có:

```text
READ
WRITE
MOVE
```

capture/access semantics.

Có thể có library-level callable traits sau này nếu thực sự cần generic abstraction.

---

# 17. Closure call semantics

Compiler biết closure có environment:

```text
ClosureValue {
    code
    environment
}
```

Nhưng representation không cố định.

Có thể:

```text
(code_ptr, env_ptr)
```

hoặc:

```text
specialized direct call
```

hoặc inline hoàn toàn.

---

# 18. Closure invocation

MIR có thể dùng:

```text
CALL_CLOSURE closure, args
```

trước optimization.

Sau lowering:

```text
CALL ClosureFunction(env, args)
```

Nếu compiler biết closure:

```text
inline
```

→ không còn closure call.

---

# 19. Direct closure call

Ví dụ:

```axiom
let f = |x: i32| x + 1;
let y = f(10);
```

compiler không nhất thiết phải materialize:

```text
ClosureValue
```

Có thể trực tiếp:

```text
y = 10 + 1
```

Đây là **closure scalarization / closure elimination**.

---

# 20. Function pointer conversion

Noncapturing:

```axiom
let f = |x: i32| x * 2;

let p: fn(i32) -> i32 = f;
```

→ hợp lệ.

Capturing:

```axiom
let n = 2;
let f = |x| x * n;
```

không thể tự động decay thành ordinary function pointer vì thiếu environment.

Có thể cần explicit closure representation.

---

# 21. Closure storage type

Compiler internal:

```text
ClosureType {
    closure_id
    params
    return_type
    captures[]
    call_mode
}
```

Capture:

```text
Capture {
    source_place
    mode
    region
    type
}
```

Ví dụ:

```text
Capture {
    source = local#4
    mode = READ
    type = String
}
```

---

# 22. Closure capture và view

Ví dụ:

```axiom
let v = view(data);

let f = || read(v);
```

Closure environment không được tự động làm cho `v` sống lâu hơn owner.

Nếu closure escape:

```text
closure lifetime
    >
view lifetime
```

→ compile error.

Compiler phải xử lý closure environment như một nơi chứa capability.

---

# 23. Closure capture `mut_view`

```axiom
let v = mut_view(buffer);

let f = || write(v);
```

Closure giữ WRITE capability.

Trong thời gian closure còn có thể được gọi:

```text
owner cannot conflict
other mutable capability cannot conflict
```

Nếu closure được gọi nhiều lần, capability vẫn phải hợp lệ.

---

# 24. Closure capture Move

```axiom
let file = open(...);

let f = move || {
    process(file);
};
```

Ownership chuyển:

```text
file
 ↓ MOVE
closure environment
```

Sau đó:

```text
file = Moved
```

Không được dùng lại.

---

# 25. Closure drop

Nếu closure environment chứa:

```text
String
File
Box<T>
```

closure có Drop semantics.

Khi closure bị drop:

```text
DROP environment fields
```

theo thứ tự đã định nghĩa.

Không cần closure runtime riêng.

---

# 26. Closure Copy

Closure có thể Copy nếu:

```text
all captures are semantically Copy
```

Ví dụ:

```axiom
let n = 10;
let f = || n;
```

có thể Copy.

Nhưng:

```axiom
let file = open(...);
let f = move || use(file);
```

không Copy.

---

# 27. Closure Send/Share

Closure có:

```text
Send
Share
```

properties dựa trên captures.

Ví dụ:

```axiom
let x = Rc<T>(...);

spawn(move || use(x));
```

Nếu `Rc<T>` không Send:

```text
compile error
```

Không cần programmer tự viết:

```text
unsafe impl Send
```

---

# 28. Spawn + closure

Đây là use case cực quan trọng:

```axiom
spawn(move || {
    process(data);
});
```

Compiler kiểm tra:

```text
closure captures
↓
ownership
↓
Send
↓
thread migration
```

Nếu hợp lệ:

```text
closure environment
```

được transfer sang execution domain mới.

---

# 29. `spawn_local`

```axiom
spawn_local(|| {
    use(local_state);
});
```

Không cần Send nếu execution domain được đảm bảo same-domain.

Nhưng lifetime vẫn phải hợp lệ.

---

# 30. Closure + async

Ví dụ:

```axiom
spawn(async move {
    await process(data);
});
```

Ở đây có hai lowering:

```text
closure/task capture
        ↓
async state machine
```

Compiler phải hợp nhất hai environment khi có thể.

Không tạo:

```text
closure heap object
+
future heap object
```

một cách bắt buộc.

---

# 31. Closure + await

Nếu closure chứa capability:

```text
view<T>
mut_view<T>
```

và closure body có:

```text
await
```

thì capability không được mặc định sống qua suspension.

Compiler kiểm tra:

```text
capability live across await?
```

Nếu có:

```text
reject
```

trừ khi storage/execution-domain contract cho phép.

---

# 32. Closure recursion

Closure không thể đơn giản tự tham chiếu trước khi binding hoàn thành:

```axiom
let f = || f();
```

Đây là vấn đề recursive value.

Có thể hỗ trợ bằng explicit indirection:

```text
Box
Handle
function declaration
```

hoặc compiler-generated recursive environment sau này.

MVP nên reject self-reference trực tiếp nếu chưa có finite representation.

---

# 33. Higher-order function

Axiom hỗ trợ tự nhiên:

```axiom
fn map<T, U>(
    input: view<T>,
    f: ...
) -> ...
```

Closure:

```axiom
map(values, |x| x * 2);
```

Nếu `f` compile-time known:

```text
inline
specialize
vectorize
```

có thể biến toàn bộ abstraction thành loop machine code.

---

# 34. Function values và ABI

Internal:

```text
fn(i32) -> i32
```

có thể chỉ là:

```text
code pointer
```

Closure:

```text
(code pointer, environment pointer)
```

Nhưng ABI representation phải do ABI lowering quyết định.

Không hard-code vào MIR.

---

# 35. FFI function pointer

```axiom
extern "C" fn callback(x: i32) -> i32;
```

có ABI identity:

```text
FunctionType {
    params
    result
    calling_convention = C
}
```

Không được truyền Axiom closure capturing trực tiếp sang C function pointer.

Nếu cần callback có context:

```text
extern "C" fn(*mut void, i32) -> i32
```

và explicit context handle.

---

# 36. Noncapturing closure → FFI callback

Có thể cho phép:

```axiom
let cb: extern "C" fn(i32) -> i32 =
    |x| x + 1;
```

nếu closure:

- không capture
- signature tương thích
- ABI tương thích

Đây là optimization/convenience an toàn.

---

# 37. Closure identity

Mỗi closure expression có:

```text
ClosureId
```

Không dựa vào source text string.

Ví dụ:

```text
ClosureId {
    module
    function
    syntax_node
}
```

phải ổn định đủ cho incremental compilation.

---

# 38. Closure environment layout

Layout engine xử lý:

```text
ClosureLayout {
    captures[]
    size
    alignment
    drop
    copy
    send
    share
}
```

Có thể reorder captures nếu không observable.

Nếu capture address bị expose, layout constraints tăng lên.

---

# 39. Capture optimization

Ví dụ:

```axiom
let a = 10;
let b = 20;

let f = || a + 1;
```

`b` không được capture.

Compiler phải capture **actual semantic dependencies**, không capture toàn bộ lexical scope.

---

# 40. Capture projection

Nếu:

```axiom
let p = Point { x: 1, y: 2 };

let f = || p.x;
```

compiler có thể capture:

```text
p.x
```

thay vì toàn bộ:

```text
p
```

nếu ownership/Drop semantics cho phép.

Đây là một optimization rất đáng giá.

---

# 41. Nhưng không phá Drop semantics

Nếu `p` có custom Drop:

```text
p.x
```

không thể tùy tiện tách khỏi `p`.

Compiler phải giữ semantic ownership.

Do đó:

```text
capture projection
```

phụ thuộc:

```text
Copy
Move
Drop
partial-move rules
```

---

# 42. Closure ABI và generic

Closure type là concrete anonymous type.

Ví dụ:

```axiom
fn apply<F>(f: F, x: i32) -> i32
```

compiler có thể instantiate:

```text
apply<ClosureType#1>
```

Sau đó closure call có thể được devirtualized hoàn toàn.

Đây là con đường rất mạnh để đạt zero-cost higher-order programming.

---

# 43. Không cần dynamic callable mặc định

Không tạo type:

```text
Callable
```

với:

```text
vtable
```

cho mọi closure.

Nếu muốn runtime dynamic callable:

```text
dyn Callable
```

phải explicit.

---

# 44. Closure + trait

Sau này library có thể định nghĩa abstraction:

```axiom
trait Callable<A, R> {
    fn call(self, args: A) -> R;
}
```

nhưng compiler vẫn có thể special-case callable semantics.

Không để trait machinery làm closure chậm.

---

# 45. Closure lowering

Đề xuất pipeline:

```text
HIR
 │
 ├── closure expression
 │
 ▼
Closure Analysis
 │
 ├── capture analysis
 ├── ownership analysis
 ├── escape analysis
 ├── Send/Share analysis
 └── async interaction
 │
 ▼
Closure Environment Type
 │
 ▼
Closure Function
 │
 ▼
MIR
```

---

# 46. Closure elimination

Optimization:

```text
ClosureCreationElimination
ClosureEnvironmentScalarization
ClosureInlining
ClosureCallDevirtualization
DeadCaptureElimination
CaptureProjection
```

Ví dụ:

```axiom
let n = 10;
let f = |x| x + n;
let y = f(5);
```

có thể trở thành:

```text
y = 15
```

không allocation.

---

# 47. Escape analysis

Các trạng thái đã có:

```text
NoEscape
LocalEscape
ReturnEscape
ArgumentEscape
GlobalEscape
UnknownEscape
```

Closure:

```text
NoEscape
```

→ stack/register/inline.

```text
ReturnEscape
```

→ storage phải sống lâu hơn function frame.

Compiler quyết định cách materialize.

---

# 48. Closure và heap

Một closure **có thể** cần dynamic storage.

Ví dụ:

```axiom
fn make_callback() -> ??? {
    let huge = ...
    return || use(huge);
}
```

Nhưng semantics chỉ yêu cầu:

```text
environment survives returned closure
```

Không yêu cầu:

```text
malloc()
```

Compiler có thể dùng:

- caller allocation
- arena
- Box
- static storage
- heap

tùy API/storage contract.

---

# 49. Diagnostics

Đề xuất:

```text
AX1501 closure capture conflicts with owner
AX1502 closure captures moved value
AX1503 closure capture would outlive source
AX1504 mutable capture conflicts with existing capability
AX1505 closure is not Send
AX1506 closure is not Share
AX1507 capturing closure cannot convert to function pointer
AX1508 closure ABI mismatch
AX1509 invalid recursive closure
AX1510 closure capability cannot cross await
AX1511 closure environment contains invalid value
AX1512 closure type cannot be inferred
```

---

# 50. Invariants

```text
ACLOSURE-20  Closure Is A Compile-Time Abstraction
ACLOSURE-21  Closure Has A Stable Compiler Identity
ACLOSURE-22  Closure Environment Is An Aggregate
ACLOSURE-23  Closure Does Not Require Heap Allocation
ACLOSURE-24  Closure Storage Is Determined By Storage Analysis
ACLOSURE-25  Capture Mode Is READ WRITE Or MOVE
ACLOSURE-26  Capture Mode Is Compiler-Inferred
ACLOSURE-27  Explicit move Capture Forces Ownership Transfer
ACLOSURE-28  Closure Capture Respects Ownership
ACLOSURE-29  Closure Capture Respects Capability Rules
ACLOSURE-30  Closure Capture Respects Drop Semantics
ACLOSURE-31  Closure Capture Respects Send/Share
ACLOSURE-32  Closure Environment Cannot Outlive Its Dependencies
ACLOSURE-33  Closure Cannot Create Dangling Capability
ACLOSURE-34  Noncapturing Closure May Convert To Function Value
ACLOSURE-35  Capturing Closure Does Not Implicitly Become Function Pointer
ACLOSURE-36  Closure Call Is Resolved Before Machine Lowering
ACLOSURE-37  Closure Can Be Inlined
ACLOSURE-38  Closure Environment Can Be Scalarized
ACLOSURE-39  Dead Captures Can Be Eliminated
ACLOSURE-40  Capture Projection May Be Optimized
ACLOSURE-41  Optimization Cannot Change Capture Semantics
ACLOSURE-42  Closure Drop Follows Normal Drop Rules
ACLOSURE-43  Closure Copy Requires Semantic Copyability
ACLOSURE-44  Closure Send Requires Sendable Captures
ACLOSURE-45  Closure Share Requires Shareable Captures
ACLOSURE-46  Closure Cannot Cross Await With Invalid Capability
ACLOSURE-47  Closure And Future Lowering May Be Combined
ACLOSURE-48  Dynamic Callable Dispatch Must Be Explicit
ACLOSURE-49  Closure Does Not Imply Runtime Object Header
ACLOSURE-50  Closure Does Not Imply Runtime Type Metadata
ACLOSURE-51  Closure FFI Requires Explicit ABI Compatibility
ACLOSURE-52  Closure Semantics Are Independent Of Physical Representation
```

---

# 51. BOOT-015 gate

```text
Function value                  ✓
Noncapturing closure             ✓
Capturing closure                ✓
READ capture                     ✓
WRITE capture                    ✓
MOVE capture                     ✓
Closure ownership                ✓
Closure Drop                     ✓
Closure Copy                     ✓
Closure Send/Share               ✓
Closure + view                   ✓
Closure + mut_view               ✓
Closure + await legality         ✓
Closure escape analysis          ✓
Closure environment layout       ✓
Closure → function pointer       ✓
Generic closure                  ✓
Higher-order function            ✓
Closure in MIR                   ✓
Closure elimination              ✓
Closure inlining                 ✓
Native x86-64                    ✓
Interpreter/native equivalence   ✓
```

## Một quyết định rất đáng giữ

Axiom giờ có thể biểu đạt cả ba mức:

```text
fn
│
├── function value
│
└── closure
      │
      ├── no capture
      │     └── function pointer
      │
      └── capture
            └── environment + code
```

và quan trọng nhất:

```text
Source abstraction
       ↓
Compiler analysis
       ↓
Concrete representation
       ↓
Optimization
       ↓
có thể biến mất hoàn toàn
```

Do đó một đoạn code kiểu:

```axiom
map(values, |x| x * 2)
```

không mặc định đồng nghĩa với:

```text
allocate closure
allocate object
indirect call
heap
GC/RC
```

Nó hoàn toàn có thể trở thành một loop/vectorized machine code trực tiếp.

**Bước tiếp theo hợp lý: BOOTSTRAP-016 — Comptime + Compile-time Reflection**, nơi ta quyết định Axiom sẽ cho compiler thực thi chính Axiom semantics như thế nào mà không biến `comptime` thành một “ngôn ngữ thứ hai”.