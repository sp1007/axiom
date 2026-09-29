Tiếp tục với **BOOTSTRAP-032 — Closure, Function Values & Callable Semantics**.

Đây là chỗ tôi muốn Axiom **đơn giản hơn Rust đáng kể**. Ta không nhất thiết cần một bộ `Fn / FnMut / FnOnce` mà programmer phải học như ba loại function trait riêng biệt.

Nguyên tắc:

> **Closure là function + environment. Compiler tự suy ra cách environment được sử dụng. Programmer không phải khai báo capture mode.**

---

# BOOTSTRAP-032 — Closure, Function Values & Callable Semantics

## 1. Có 3 loại callable

Axiom phân biệt:

```text
Function
Function pointer
Closure
```

### Function

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Không có environment.

### Function pointer

```axiom
let f: fn(i32, i32) -> i32 = add
```

Chỉ trỏ tới callable code.

### Closure

```axiom
let factor = 10

let f = |x: i32| x * factor
```

Closure có:

```text
code
+
captured environment
```

---

# 2. Closure không phải object

Không mặc định:

```text
heap object
vtable
reference count
runtime type information
```

Compiler có thể biến:

```axiom
|x| x + offset
```

thành một anonymous struct:

```text
struct Closure$1 {
    offset: i32
}
```

và function:

```text
fn Closure$1_call(self: view<Closure$1>, x: i32) -> i32
```

Sau optimization, thậm chí toàn bộ environment có thể biến mất.

---

# 3. Capture mode compiler tự suy luận

Ví dụ:

```axiom
let x = 10

let f = || x + 1
```

Compiler thấy chỉ đọc `x`.

Semantic capture:

```text
READ
```

---

Nếu:

```axiom
var x = 10

let f = || {
    x += 1
}
```

Compiler thấy closure cần mutable access:

```text
WRITE
```

---

Nếu:

```axiom
let resource = File.open(path)?

let f = || {
    use(resource)
}
```

nếu closure cần sở hữu resource:

```text
MOVE
```

---

# 4. Programmer không viết capture mode

Không cần:

```text
|&x|
|&mut x|
|move x|
```

ở Core.

Chỉ:

```axiom
|x| ...
```

hoặc:

```axiom
|| ...
```

Compiler phân tích usage.

Đây phù hợp trực tiếp với triết lý:

> **Compiler Complexity Is Not Language Complexity.**

---

# 5. Nhưng phải có cách yêu cầu Move

Có một trường hợp quan trọng:

```text
closure được tạo trong scope hiện tại
nhưng muốn closure sở hữu giá trị
```

Ví dụ đưa vào task:

```axiom
spawn(|| process(data))
```

Nếu compiler biết closure sẽ sống lâu hơn scope, nó có thể tự chuyển sang capture ownership nếu semantics cho phép.

Nhưng khi cần ép rõ ràng, nên có:

```axiom
move || process(data)
```

Tôi đề xuất chỉ giữ **một modifier `move`**.

Không cần:

```text
borrow
mut
move
copy
```

capture syntax riêng biệt.

---

# 6. `move` có ý nghĩa rất rõ

```axiom
let data = Buffer(...)

let task = move || {
    process(data)
}
```

`data` được chuyển ownership vào closure.

Sau đó:

```axiom
use(data)
```

bị compiler reject.

Đây là một semantic move bình thường.

---

# 7. Closure capture theo capability

Compiler nội bộ có thể biểu diễn:

```text
Capture {
    source
    region
    access
    ownership
}
```

Ví dụ:

```text
x
READ
```

hoặc:

```text
x
WRITE
```

hoặc:

```text
resource
MOVE
```

Không cần expose metadata này cho programmer.

---

# 8. Capture không đồng nghĩa heap allocation

Ví dụ:

```axiom
fn compute() -> i32 {
    let x = 10

    let f = || x + 1

    f()
}
```

Compiler có thể inline:

```text
return 11
```

Không closure object.

---

# 9. Closure escape analysis

Nếu:

```axiom
let f = || x + 1
f()
```

closure không escape.

Compiler có thể:

```text
inline
scalar replace
eliminate closure
```

---

Nếu:

```axiom
return || x + 1
```

closure escape khỏi current function.

Compiler phải materialize environment.

Nhưng vẫn **không có nghĩa bắt buộc heap**.

Có thể:

```text
caller-owned storage
stack
arena
heap
```

theo storage analysis.

---

# 10. Closure return

Ví dụ:

```axiom
fn make_adder(x: i32) -> ??? {
    |y| x + y
}
```

Closure có anonymous type.

Axiom không nên bắt programmer viết tên anonymous closure type.

Có hai cách.

### Cách 1 — `impl Callable`

```axiom
fn make_adder(x: i32) -> impl Fn(i32) -> i32
```

### Cách 2 — compiler-inferred return

Tôi nghiêng về cách:

```axiom
fn make_adder(x: i32) := |y| x + y
```

hoặc một syntax tương đương.

Nhưng **không nên thêm syntax mới nếu chưa cần**.

V1 có thể dùng `dyn Callable` hoặc generic callback abstraction.

---

# 11. Tôi không muốn bê nguyên `Fn/FnMut/FnOnce`

Rust có:

```text
Fn
FnMut
FnOnce
```

vì capture semantics cần được biểu đạt trong trait system.

Axiom đã có compiler ownership/capability inference.

Do đó ba trait này tạo khá nhiều complexity cho programmer mà compiler vốn đã biết.

---

# 12. Đề xuất Axiom dùng một abstraction duy nhất

Có thể gọi:

```text
Callable
```

Semantic:

```text
Callable<Args, Return>
```

Compiler tự biết callable có:

```text
READ
WRITE
MOVE
```

capture requirements.

Ví dụ:

```axiom
fn apply<T, R>(
    f: Callable<T -> R>,
    value: T
) -> R
```

Compiler kiểm tra closure tương thích.

---

# 13. Nhưng invocation semantics vẫn phải phân biệt

Ví dụ closure:

```axiom
let x = Resource(...)

let f = || consume(x)
```

Sau khi gọi:

```axiom
f()
```

nếu closure đã consume resource thì lần gọi thứ hai có thể không hợp lệ.

Compiler phải biết callable này có **consuming invocation**.

Vì vậy bên trong compiler vẫn cần capability:

```text
CALL_READ
CALL_MUT
CALL_MOVE
```

nhưng programmer không nhất thiết phải nhìn thấy ba trait.

---

# 14. Có thể coi callable capability như sau

```text
Callable
├── Read-callable
├── Mut-callable
└── Move-callable
```

Nhưng đây là **compiler semantic categories**, không nhất thiết là public traits.

Điều này rất phù hợp Axiom:

```text
Compiler understands more than programmer needs to write.
```

---

# 15. Closure gọi nhiều lần

Ví dụ:

```axiom
let x = 10

let f = || x + 1

f()
f()
f()
```

READ capture.

Không vấn đề.

---

# 16. Mutable closure

```axiom
var count = 0

let next = || {
    count += 1
    count
}
```

Closure giữ mutable capability tới `count`.

Do đó:

```text
next()
next()
```

hợp lệ.

Nhưng:

```axiom
run_parallel(next, next)
```

không tự động hợp lệ.

Compiler thấy hai callable cùng cần WRITE access.

---

# 17. Closure concurrency

Ví dụ:

```axiom
var counter = 0

spawn(move || {
    counter += 1
})
```

Compiler phải reject nếu `counter` không thể an toàn vượt execution domain.

Programmer cần:

```axiom
let counter = Arc<Mutex<i32>>(0)

spawn(move || {
    let mut x = counter.lock()
    *x += 1
})
```

hoặc atomic.

Điều này tận dụng toàn bộ:

```text
Send
Share
Mutex
Atomic
Capability
```

đã thiết kế.

---

# 18. `Send` của closure

Closure là Send nếu environment có thể Send.

Ví dụ:

```text
Closure {
    a: A
    b: B
}
```

thì:

```text
Closure: Send
```

nếu:

```text
A: Send
B: Send
```

và capture không chứa invalid capability.

Compiler derive tự động.

---

# 19. `Share` của closure

Tương tự nhưng nghiêm ngặt hơn.

Closure chỉ Share nếu environment và callable semantics cho phép concurrent invocation.

Ví dụ immutable:

```axiom
let x = 100

let f = || x + 1
```

có thể Share.

Nhưng:

```axiom
var x = 0

let f = || {
    x += 1
}
```

không tự nhiên Share.

Phải có synchronization.

---

# 20. View capture

Ví dụ:

```axiom
fn make_processor(data: view<[u8]>) {
    let f = || process(data)
    ...
}
```

Closure capture một capability.

Nếu closure sống ngắn:

```text
OK
```

Nếu closure escape:

```text
compiler kiểm tra capability lifetime
```

Nếu data không còn tồn tại:

```text
compile error
```

---

# 21. Closure không thể "lách" ownership

Không cho:

```axiom
fn bad(data: view<[u8]>) -> ??? {
    return || use(data)
}
```

nếu closure escape khỏi `data`.

Compiler không cần programmer viết lifetime.

Đây chính là nơi ownership inference phát huy tác dụng.

---

# 22. `move` closure giải quyết escape ownership

```axiom
fn make_processor(data: Buffer) -> ??? {
    move || process(data)
}
```

`data` được chuyển vào closure.

Closure trở thành owner.

Do đó có thể escape.

---

# 23. Capture một phần struct

Ví dụ:

```axiom
struct State {
    config: Config
    buffer: Buffer
}

let state = State(...)

let f = || use(state.config)
```

Compiler không nhất thiết phải capture toàn bộ `state`.

Có thể capture:

```text
state.config
```

nếu ownership/capability semantics cho phép.

Đây là **field-sensitive capture**.

---

# 24. Partial capture

Compiler có thể transform:

```text
State {
    config,
    buffer
}
```

thành:

```text
ClosureEnv {
    config
}
```

`buffer` vẫn thuộc owner ban đầu.

Điều này vừa giảm memory vừa giảm false dependency.

---

# 25. Nhưng Drop phải được bảo toàn

Nếu capture:

```text
state.resource
```

mà `state` có Drop tùy biến:

```text
custom Drop
```

thì compiler phải tuân theo restriction partial move đã đóng băng.

Không được tùy tiện tách field khỏi custom Drop type.

---

# 26. Closure environment layout

Không ổn định mặc định.

Compiler có thể:

```text
reorder fields
pack
scalarize
remove unused capture
merge captures
```

Nếu closure ABI cần exposed:

```text
@repr(...)
```

hoặc explicit ABI contract.

---

# 27. Non-capturing closure

Ví dụ:

```axiom
let f = |x: i32| x * 2
```

không capture gì.

Compiler có thể chuyển trực tiếp thành:

```text
fn(i32) -> i32
```

function pointer.

Đây là optimization/semantic coercion hợp lệ.

---

# 28. Non-capturing closure → C function pointer

Nếu ABI-compatible:

```axiom
extern "C" fn(...)
```

non-capturing closure có thể được chuyển thành function pointer.

Capturing closure thì không.

Không tự tạo global context object.

---

# 29. Function → closure

Ngược lại:

```axiom
fn add(x: i32) -> i32
```

có thể dùng ở nơi yêu cầu callable.

Không cần wrap:

```text
Closure { function_pointer: add }
```

nếu compiler có thể dùng function pointer trực tiếp.

---

# 30. First-class function values

Function pointer:

```axiom
type IntFn = fn(i32) -> i32
```

là value.

Có thể:

```axiom
let f = add
let x = f(1)
```

Representation target-dependent.

Thông thường là code pointer.

---

# 31. Function pointer không có environment

Do đó function pointer:

```text
Copy
```

nếu representation là ordinary machine function pointer.

Không Drop.

Không ownership resource.

---

# 32. Closure type anonymous

Mỗi closure expression có một anonymous nominal compiler identity.

Ví dụ:

```axiom
let a = |x| x + 1
let b = |x| x + 1
```

`a` và `b` không nhất thiết cùng type.

Compiler identity:

```text
ClosureId(file, span)
```

hoặc stable semantic identity tương đương.

---

# 33. Vì sao không structural closure type?

Nếu hai closure cùng signature:

```text
(i32) -> i32
```

không có nghĩa environment giống nhau.

Ví dụ:

```axiom
|x| x + a
|x| x + b
```

có thể capture khác nhau.

Do đó anonymous closure identity là hợp lý.

---

# 34. Generic function nhận closure

Ví dụ:

```axiom
fn map<T, R>(
    items: view<[T]>,
    f: Callable<T -> R>
) -> Vec<R>
```

Compiler có thể specialize:

```text
map<i32, i64, Closure$1>
```

và inline closure.

Không cần dynamic dispatch.

---

# 35. Đây là con đường tới zero-cost functional programming

Ví dụ:

```axiom
let result =
    numbers
        .map(|x| x * 2)
        .filter(|x| x > 10)
        .sum()
```

Compiler có thể biến toàn bộ thành:

```text
single loop
```

không:

```text
temporary arrays
heap allocations
closure objects
virtual calls
```

nếu semantics cho phép.

---

# 36. Iterator chain

Đây là lý do closure system phải mạnh.

```text
Iterator
    ↓
map closure
    ↓
filter closure
    ↓
fold closure
```

Monomorphization + inlining:

```text
Iterator abstraction
        ↓
one optimized loop
```

Đây là mục tiêu rất phù hợp Axiom.

---

# 37. Closure và `comptime`

Closure có thể chạy tại compile time nếu callable và captured values đều comptime-valid:

```axiom
comptime {
    let f = |x| x * 2
    const VALUE = f(10)
}
```

Không tạo runtime closure.

---

# 38. Closure environment trong comptime

Vẫn áp dụng:

```text
ownership
Drop
capabilities
```

theo BOOTSTRAP-016.

Comptime closure không được:

```text
escape
```

sang runtime trừ khi compiler materialize được callable declaration/data tương ứng.

---

# 39. Closure và async

Đây là điểm quan trọng.

```axiom
async fn process(data: Buffer) {
    let f = || use(data)
    await ...
}
```

Nếu closure sống qua `await`, environment phải trở thành một phần state của Future nếu cần.

Compiler có thể:

```text
Closure env
    ↓
Future state
```

và optimize layout.

---

# 40. Closure không được giữ capability qua await nếu invalid

Ví dụ:

```axiom
async fn bad(data: Buffer) {
    let v = view(data)

    await something()

    use(v)
}
```

nếu storage/capability contract không cho phép:

```text
reject
```

Closure cũng không thể dùng nó để bypass rule.

---

# 41. Closure capture và Future Send

Ví dụ:

```axiom
async fn task() {
    let x = NonSend(...)
    
    await something()
    
    use(x)
}
```

Future không Send nếu `x` phải sống qua suspension.

Tương tự closure:

```text
Future state
    includes closure env
```

Compiler tính transitive `Send`.

---

# 42. Closure + Fiber

Fiber có stable stack storage.

Closure có thể nằm:

```text
stack
fiber stack
caller-owned storage
heap
```

tùy escape.

Không có:

```text
closure ⇒ heap
```

---

# 43. Closure + GPU

Không nên cho arbitrary closure chạy trên GPU.

Ví dụ:

```axiom
@kernel
fn launch(f: ???)
```

chỉ hợp lệ nếu closure environment:

```text
device-safe
```

và callable:

```text
GPU-compatible
```

Không có:

```text
File
Socket
OS pointer
host heap pointer
```

trong GPU closure.

---

# 44. Có nên cho closure capture host references vào GPU?

**Không.**

Nếu muốn truyền dữ liệu:

```text
Host
 ↓ explicit transfer
DeviceBuffer
 ↓
GPU closure/kernel
```

Điều này phù hợp AGPU semantics.

---

# 45. Callback C ABI

Capturing closure:

```text
|x| ...
```

không thể trực tiếp là:

```text
extern "C" fn(...)
```

vì C function pointer không có environment.

C API thường:

```c
callback(context, value)
```

Axiom wrapper có thể biểu diễn:

```text
function pointer
+
context pointer
```

nhưng đó là FFI/system abstraction.

---

# 46. Safe callback wrapper

Ví dụ conceptually:

```axiom
struct CCallback<T> {
    fn_ptr: extern "C" fn(*mut u8, T)
    context: *mut u8
}
```

`unsafe` ở boundary.

Safe wrapper đảm bảo:

```text
context lifetime
callback lifetime
thread affinity
ownership
```

Không đưa raw pointer model vào ordinary closure syntax.

---

# 47. Closure cloning

Closure có thể Copy nếu environment Copy.

Ví dụ:

```axiom
let x = 10
let f = || x + 1

let g = f
```

nếu capture chỉ là Copy values:

```text
f
g
```

có thể độc lập.

Nhưng closure capture resource:

```text
File
```

thì không Copy.

Move semantics áp dụng bình thường.

---

# 48. Closure `Clone`

Nếu environment Clone:

```text
Closure: Clone
```

compiler/library có thể derive.

Clone phải là explicit operation:

```axiom
let g = f.clone()
```

Không implicit.

---

# 49. Mutable closure không đồng nghĩa `Share`

Ví dụ:

```axiom
var x = 0
let f = || x += 1
```

`f` có mutable environment.

Không thể:

```text
share f across threads
```

trừ khi environment itself uses synchronization.

---

# 50. Callable invocation semantics

Đề xuất compiler semantic categories:

```text
CALL_READ
CALL_MUT
CALL_MOVE
```

### `CALL_READ`

Environment chỉ đọc.

Có thể gọi nhiều lần.

### `CALL_MUT`

Environment bị mutate.

Một invocation cần exclusive mutable access.

### `CALL_MOVE`

Invocation consumes closure/environment.

Sau call, closure có thể invalid.

---

# 51. Nhưng programmer không phải khai báo

Compiler suy ra:

```text
closure body
 ↓
capture usage
 ↓
call capability
```

Nếu một generic API yêu cầu callable có thể gọi nhiều lần, compiler kiểm tra capability tương ứng.

Ví dụ `map` thường yêu cầu callable không consume environment theo mỗi element.

`consume_each` có thể cho callable move semantics.

---

# 52. Điều này thay thế phần lớn `Fn/FnMut/FnOnce`

Thay vì programmer phải học:

```text
Fn
FnMut
FnOnce
```

Axiom chỉ cần hiểu:

```text
closure
capture
ownership
```

Compiler tự làm phần còn lại.

Đây là một simplification đáng giá.

---

# 53. Nhưng compiler vẫn có thể expose chúng trong diagnostics

Ví dụ:

```text
E-CALL-014

callable cannot be invoked repeatedly

reason:
    closure consumes captured value `resource`

required:
    reusable callable

found:
    consuming callable
```

AI agent sẽ hiểu ngay.

---

# 54. Function values và lifetime

Function pointer:

```text
program lifetime
```

Closure:

```text
lifetime = environment lifetime
```

Nếu closure owns environment:

```text
closure owns captures
```

Nếu closure chỉ view:

```text
closure depends on captured capability
```

Compiler đảm bảo dependency.

---

# 55. Closure drop

Khi closure bị drop:

```text
drop captured resources
```

theo environment declaration/initialization semantics.

Nếu closure moved một resource:

```text
closure Drop
    ↓
resource Drop
```

---

# 56. Closure partial capture + destruction

Compiler phải theo dõi:

```text
captured
moved
dropped
```

field-sensitive như ordinary structs.

Không được:

```text
drop original
+
drop closure capture
```

hai lần.

---

# 57. Closure ABI

Default:

```text
unstable/private
```

Compiler tự layout.

Nếu muốn FFI:

```text
extern "C"
```

phải dùng explicit adapter.

Không cho closure anonymous type tự nhiên trở thành stable ABI.

---

# 58. Closure size

Compiler có thể expose:

```axiom
size_of(typeof(f))
```

ở comptime nếu type được nameable/reflectable theo quy tắc.

Nhưng programmer không được giả định closure luôn:

```text
2 pointers
```

hoặc:

```text
pointer + environment pointer
```

---

# 59. Optimization opportunities

Closure compiler có thể:

```text
inline
constant-fold
capture elimination
capture scalarization
environment shrinking
dead capture elimination
closure fusion
function specialization
devirtualization
stack promotion
allocation elimination
```

Tất cả đều không thay đổi semantics.

---

# 60. Closure conversion trong compiler

Một pipeline hợp lý:

```text
Closure AST
   ↓
Capture Analysis
   ↓
Capture Classification
   ↓
Environment Type
   ↓
Closure Conversion
   ↓
Callable MIR
   ↓
Escape Analysis
   ↓
Storage Placement
   ↓
Inlining / Specialization
```

Backend không cần biết closure.

---

# 61. Ví dụ hoàn chỉnh

```axiom
fn make_multiplier(factor: i32) {
    move |x: i32| {
        x * factor
    }
}
```

Compiler:

```text
Closure$1 {
    factor: i32
}
```

semantic callable:

```text
(i32) -> i32
```

Environment:

```text
factor: MOVE
```

Storage:

```text
caller-selected / returned storage
```

Nếu caller ngay lập tức:

```axiom
let f = make_multiplier(10)
f(5)
```

optimizer có thể biến toàn bộ thành:

```text
50
```

---

# 62. Ví dụ concurrency

```axiom
fn launch(data: Buffer) {
    spawn(move || {
        process(data)
    })
}
```

Compiler:

```text
data
 ↓
MOVE
 ↓
Closure Environment
 ↓
Send verification
 ↓
Task
```

Nếu `Buffer: Send`:

```text
valid
```

Nếu `Buffer` không Send:

```text
compile error
```

Không cần programmer viết annotation.

---

# 63. Ví dụ mutable shared state

```axiom
let state = Arc<Mutex<State>>(...)

spawn(move || {
    let s = state.lock()
    update(s)
})
```

Closure capture:

```text
state → MOVE
```

`Arc<State>`:

```text
Send + Share
```

`MutexGuard`:

```text
exclusive capability
```

Toàn bộ chain đã thống nhất với concurrency model.

---

# 64. Invariants BOOTSTRAP-032

```text
ACLOS-20   A closure is callable code plus captured environment.

ACLOS-21   A closure does not inherently require heap allocation.

ACLOS-22   Closure capture mode is inferred by the compiler.

ACLOS-23   Read capture creates read capability semantics.

ACLOS-24   Mutable capture creates exclusive mutable capability semantics.

ACLOS-25   Owning capture transfers ownership into the closure.

ACLOS-26   Explicit move capture may force ownership capture.

ACLOS-27   Closure capture cannot bypass ownership verification.

ACLOS-28   Closure capture cannot create dangling capabilities.

ACLOS-29   Closure environment lifetime is compiler verified.

ACLOS-30   Closure environment layout is compiler controlled.

ACLOS-31   Closure field capture may be field-sensitive.

ACLOS-32   Partial capture preserves Drop semantics.

ACLOS-33   Captured resources are dropped with the closure when owned.

ACLOS-34   Closure Drop does not double-drop moved values.

ACLOS-35   Closure Send is derived from captured state.

ACLOS-36   Closure Share is derived from captured state and callable semantics.

ACLOS-37   Mutable closures are not implicitly Share.

ACLOS-38   Closure invocation respects capture capability.

ACLOS-39   Reusable invocation requires non-consuming callable semantics.

ACLOS-40   Consuming invocation invalidates the consumed closure state.

ACLOS-41   Compiler tracks callable capability internally.

ACLOS-42   Callable capability need not be exposed as multiple programmer-facing traits.

ACLOS-43   Function pointers have no captured environment.

ACLOS-44   Non-capturing closures may coerce to compatible function pointers.

ACLOS-45   Capturing closures cannot implicitly become raw function pointers.

ACLOS-46   Function pointers are ordinary first-class values.

ACLOS-47   Closure types are compiler-generated anonymous types.

ACLOS-48   Distinct closure expressions have distinct compiler identities.

ACLOS-49   Closure identity does not imply runtime identity.

ACLOS-50   Generic callable parameters use static dispatch by default.

ACLOS-51   Callable abstraction does not imply dynamic dispatch.

ACLOS-52   Dynamic callable dispatch requires explicit dynamic representation.

ACLOS-53   Closure allocation may be eliminated by escape analysis.

ACLOS-54   Closure environment may be stack, caller-owned, arena, heap, or register stored.

ACLOS-55   Storage placement does not change closure semantics.

ACLOS-56   Closure invocation may be inlined.

ACLOS-57   Closure specialization may remove callable abstraction.

ACLOS-58   Closure capture may be scalarized or eliminated.

ACLOS-59   Closure semantics remain observable under optimization.

ACLOS-60   Closure capabilities cannot outlive their provenance.

ACLOS-61   Views captured by closures obey normal capability lifetime rules.

ACLOS-62   Views cannot implicitly cross await without a valid storage contract.

ACLOS-63   Closure state participating in Future state is ownership checked.

ACLOS-64   Future Send includes captured closure state.

ACLOS-65   GPU closures must satisfy GPU execution-domain rules.

ACLOS-66   Host capabilities cannot implicitly enter GPU closures.

ACLOS-67   C ABI function pointers are distinct from capturing closures.

ACLOS-68   FFI closure adapters require explicit context/lifetime contracts.

ACLOS-69   Closure Copy follows captured-state Copy semantics.

ACLOS-70   Closure Clone follows captured-state Clone semantics.

ACLOS-71   Closure does not imply runtime object headers.

ACLOS-72   Closure does not imply virtual dispatch.

ACLOS-73   Closure does not imply reference counting.

ACLOS-74   Closure does not imply garbage collection.

ACLOS-75   Comptime closures use normal Axiom semantic rules.

ACLOS-76   Unmaterialized comptime closures do not enter runtime.

ACLOS-77   Closure conversion occurs before backend lowering.

ACLOS-78   Backend does not require closure-specific semantics.

ACLOS-79   Callable diagnostics expose compiler-derived invocation requirements.

ACLOS-80   Closure semantics are deterministic.
```

---

# 65. Kết luận kiến trúc

Tôi đề xuất **đóng băng hướng này**:

```text
             CALLABLE
                │
       ┌────────┴────────┐
       │                 │
   Function            Closure
       │                 │
 function ptr       code + environment
                         │
              ┌──────────┼──────────┐
              │          │          │
            READ       MUTATE      MOVE
              │          │          │
           reusable   exclusive   consuming
```

Nhưng:

> **READ/MUTATE/MOVE là semantic categories của compiler, không phải ba trait mà programmer phải học.**

Đây là một điểm tôi cho rằng Axiom có thể **đơn giản hơn Rust mà không mất khả năng biểu đạt**.

---

## Chuỗi architecture tiếp theo

Sau closure, mảnh còn thiếu rất quan trọng là:

**BOOTSTRAP-033 — FFI, ABI, C Interop & Native Boundary**

Phần đó sẽ chốt một vấn đề cực kỳ quan trọng đối với mục tiêu của Axiom:

> **Axiom phải gọi được C/C++/OS API/GPU API/native library, đồng thời tạo ra EXE/ELF/Mach-O/iOS/Android mà không biến FFI thành một vùng "mọi thứ đều unsafe và compiler bỏ cuộc".**

Ta sẽ thiết kế:

```text
Axiom ABI
C ABI
system ABI
raw pointer boundary
@repr(C)
extern "C"
export/import
calling convention
variadic FFI
struct/enum ABI
allocator boundary
string ABI
callback ABI
dynamic library
static library
symbol visibility
TLS
syscall
intrinsics
SIMD
GPU ABI
```

và đặc biệt tách rõ **Axiom semantic safety** khỏi **ABI compatibility**, để compiler vẫn kiểm tra được càng nhiều càng tốt ở biên native.