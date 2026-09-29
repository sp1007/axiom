# AXIOM LANGUAGE SPECIFICATION v0.1
# Part X — Functions · Closures · Calling Semantics · ABI

Part IX đã khóa expression semantics. Part X khóa **đơn vị thực thi quan trọng nhất của Axiom: function**.

Mục tiêu của phần này:

> Function phải là abstraction cấp cao nhưng khi không cần runtime machinery thì compiler phải có thể biến nó thành machine code trực tiếp.

Vì vậy Axiom phân biệt rõ:

```text
Function declaration
Function value
Function pointer
Closure
Dynamic callable
Extern function
Async function
Comptime function
```

---

# 1. Function là primitive behavior abstraction

Function là cơ chế behavior cơ bản của Axiom.

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Không có requirement rằng function phải thuộc một class/object.

Method:

```axiom
fn length(self: view<Text>) -> usize {
    ...
}
```

chỉ là function có receiver parameter đầu tiên.

---

# 2. Function signature

Signature gồm:

```text
name
generic parameters
parameters
return type
effects/attributes nếu có
ABI nếu explicit
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

signature:

```text
(i32, i32) -> i32
```

Tên function không phải một phần của function type.

---

# 3. Function types

Function type:

```axiom
fn(i32, i32) -> i32
```

là type của một callable không capture environment.

Ví dụ:

```axiom
let f: fn(i32, i32) -> i32 = add
```

`f` có thể được gọi:

```axiom
f(10, 20)
```

---

# 4. Function value không phải function pointer

Axiom phân biệt semantic:

```text
function item
function value
function pointer
closure
```

Một named function:

```axiom
add
```

có thể được dùng như function value.

Compiler có thể represent nó bằng:

```text
machine code address
```

nhưng representation đó không phải semantic requirement.

---

# 5. Function pointer

Khi programmer cần một callable representation có machine-address semantics:

```axiom
fnptr<i32(i32, i32)>
```

hoặc syntax canonical được compiler/library định nghĩa tương ứng.

Tuy nhiên v0.1 nên **không có hai function-pointer syntax khác nhau nếu không có semantic khác biệt rõ ràng**.

Do đó quyết định:

> `fn(A...) -> R` là callable function type; ABI representation của nó chỉ trở thành raw code pointer khi context/ABI yêu cầu.

---

# 6. Function type không capture state

Một function type:

```axiom
fn(i32) -> i32
```

không chứa hidden environment.

Vì vậy:

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

có thể được lower trực tiếp thành:

```text
code pointer
```

khi cần first-class function value.

---

# 7. Function parameters

Parameter mặc định là **owning/value parameter**:

```axiom
fn process(data: Buffer) { ... }
```

Caller chuyển ownership:

```axiom
let buffer = create()
process(buffer)

// buffer không còn usable
```

Nếu chỉ cần đọc:

```axiom
fn inspect(data: view<Buffer>) { ... }
```

Nếu cần mutation:

```axiom
fn modify(data: mut_view<Buffer>) { ... }
```

---

# 8. Parameter passing does not imply ABI copying

```axiom
fn consume(x: LargeStruct) { ... }
```

không có nghĩa compiler phải copy `LargeStruct` qua stack.

Compiler có thể dùng:

```text
registers
stack slots
caller-allocated storage
hidden pointer
sret-like convention
scalar replacement
```

miễn semantic ownership đúng.

---

# 9. Value parameter semantics

Value parameter:

```axiom
fn consume(x: T)
```

nhận ownership của argument.

Conceptually:

```text
caller ownership
       ↓
parameter ownership
```

Không tạo alias owner thứ hai.

---

# 10. Copy parameter

Nếu:

```axiom
fn inspect(x: i32)
```

và caller:

```axiom
let a = 10
inspect(a)
use(a)
```

`i32` là `Copy`, nên caller vẫn sở hữu semantic value của `a`.

---

# 11. Non-Copy parameter

```axiom
fn consume(x: Text)
```

và:

```axiom
let s = make_text()

consume(s)

use(s)
```

→ compile error.

Đây là Move, không phải hidden clone.

---

# 12. View parameters

```axiom
fn print(data: view<Text>) {
    ...
}
```

caller có thể viết:

```axiom
print(text)
```

Compiler tạo ephemeral READ capability.

Đây là **một trong số ít implicit conversions được Core cho phép**.

---

# 13. Mutable view parameters

```axiom
fn sort(data: mut_view<i32>) {
    ...
}
```

caller:

```axiom
sort(array)
```

Compiler tạo exclusive mutable capability trong phạm vi call.

Nếu caller đang có:

```axiom
let v = view(array)
sort(array)
```

và `v` còn live:

→ compile error.

Nếu `v` đã semantic last-use:

```axiom
print(v)
sort(array)
```

compiler có thể xác định capability đã hết sống trước `sort`.

---

# 14. Return values

Function return:

```axiom
fn create() -> Buffer {
    Buffer(...)
}
```

chuyển ownership:

```text
function local
      ↓
caller
```

Không có implicit clone.

---

# 15. Return does not imply heap allocation

```axiom
fn make() -> Vec2 {
    Vec2 { x: 1.0, y: 2.0 }
}
```

không yêu cầu heap.

Compiler có thể trả:

```text
registers
```

hoặc:

```text
caller-allocated return slot
```

---

# 16. Named return storage

Axiom không yêu cầu syntax:

```text
return value in named slot
```

Compiler tự chọn ABI.

Ví dụ:

```axiom
fn make() -> LargeStruct {
    LargeStruct { ... }
}
```

có thể lower thành:

```text
caller allocates result
callee writes result
```

mà programmer không cần biết.

---

# 17. Multiple return values

Axiom v0.1 nên **không thêm một semantic category "multiple return values" riêng**.

Dùng tuple:

```axiom
fn divmod(a: i32, b: i32) -> (i32, i32) {
    (a / b, a % b)
}
```

Caller:

```axiom
let (q, r) = divmod(a, b)
```

Tuple là ordinary value.

Compiler có thể scalarize thành nhiều registers.

---

# 18. Function argument evaluation

Theo Part IX:

```axiom
foo(a(), b(), c())
```

luôn:

```text
a()
b()
c()
foo()
```

Không có unspecified argument order.

---

# 19. Named arguments

Axiom v0.1:

> **Không cần named-argument syntax trong Core.**

Ví dụ không có:

```axiom
foo(width: 10, height: 20)
```

Lý do: giảm overload/name-resolution complexity.

Nếu API cần clarity, dùng struct:

```axiom
struct WindowConfig {
    width: u32
    height: u32
}

create_window(WindowConfig {
    width: 10,
    height: 20
})
```

Đồng thời struct có thể mở rộng mà không làm signature phình ra.

---

# 20. Default arguments

Axiom v0.1:

> **Không có default function arguments.**

Thay bằng:

```axiom
fn create(config: Config)
```

hoặc convenience functions:

```axiom
fn create_default() -> Window
```

Điều này tránh việc default argument trở thành hidden API behavior.

---

# 21. Variadic functions

Core v0.1 không có arbitrary variadic functions:

```axiom
fn printf(...)
```

thay vào đó:

```axiom
fn printf(args: view<FormatArg>)
```

hoặc FFI-specific variadic declaration.

---

# 22. C variadic FFI

C ABI có thể yêu cầu:

```axiom
extern "C" fn printf(format: *const u8, ...)
```

Nhưng đây là:

```text
FFI/system-level semantics
```

không phải ordinary Axiom function semantics.

Safe wrappers nên cung cấp typed interface.

---

# 23. Generic functions

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Generic function là compile-time abstraction.

Default implementation:

```text
monomorphization
```

Ví dụ:

```text
max<i32>
max<f64>
max<MyType>
```

có thể trở thành những machine implementations khác nhau.

---

# 24. Generic code must have one semantic meaning

Compiler không được để specialization làm thay đổi source semantics.

Ví dụ không được:

```text
T = i32 → overflow behavior A
T = MyType → overflow behavior B
```

trừ khi đó là kết quả rõ ràng của trait implementation.

Generic source semantics phải deterministic.

---

# 25. Generic specialization

Compiler **được phép internally specialize**:

```text
generic
  ↓
specialized IR
  ↓
optimized machine code
```

Nhưng programmer không được viết:

```text
if T == i32 { ... }
```

để thay đổi semantic behavior dựa trên compiler specialization trong v0.1.

---

# 26. Function overloading

Axiom v0.1 không có unrestricted same-name overload sets dựa trên implicit conversions.

Ví dụ:

```axiom
fn foo(x: i32)
fn foo(x: i64)
```

không tự động được chọn dựa trên conversion.

Có thể hỗ trợ overload nếu resolution **exact và deterministic**, nhưng khuyến nghị:

> **Trait-based dispatch là cơ chế chính; name overloading nên rất hạn chế.**

Ví dụ:

```axiom
Add.add(a, b)
```

thay vì một hệ thống overload conversion phức tạp.

---

# 27. Recursive functions

Ordinary recursion:

```axiom
fn factorial(n: u64) -> u64 {
    if n <= 1 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

được hỗ trợ.

Compiler không cần runtime stack object đặc biệt.

---

# 28. Tail calls

Compiler được phép tối ưu tail recursion thành jump nếu ABI/control-flow semantics cho phép.

Ví dụ:

```axiom
fn loop(n: i32) -> i32 {
    if n == 0 {
        0
    } else {
        loop(n - 1)
    }
}
```

có thể lower thành:

```text
jump loop
```

Nhưng Axiom v0.1 **không bắt compiler phải guarantee tail-call optimization** cho mọi target.

Nếu programmer cần guaranteed tail-call ABI, đó là explicit low-level attribute sau này.

---

# 29. Function address and identity

Function values có identity logic:

```text
function declaration identity
```

Không được coi:

```text
code address
```

là stable portable identity.

Address equality chỉ có ý nghĩa khi target/ABI/system contract nói rõ.

---

# 30. First-class functions

Axiom hỗ trợ:

```axiom
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}
```

Named function:

```axiom
apply(square, 10)
```

có thể truyền như value.

---

# 31. Closures

Closure:

```axiom
|x| x + 1
```

là callable có thể capture environment.

Ví dụ:

```axiom
let offset = 10

let f = |x| x + offset
```

Closure type là một **anonymous compiler-generated type**.

Không có requirement rằng closure là heap object.

---

# 32. Closure is not automatically dynamic

Đây là quyết định quan trọng.

Closure:

```axiom
|x| x + offset
```

không mặc định trở thành:

```text
Box
vtable
heap allocation
GC object
```

Compiler có thể represent nó hoàn toàn bằng:

```text
{ offset }
```

và inline toàn bộ call.

---

# 33. Closure environment

Conceptually:

```text
Closure<TCode, TEnv>
```

gồm:

```text
code
environment
```

Nhưng đây chỉ là semantic model.

Compiler có thể:

```text
inline
scalarize
capture register
eliminate environment
```

---

# 34. Capture analysis

Compiler xác định closure capture gì.

Ví dụ:

```axiom
let a = 10
let b = 20

let f = |x| x + a
```

closure chỉ capture:

```text
a
```

`b` không được capture.

Không có hidden capture toàn bộ lexical scope.

---

# 35. Capture mode

Capture mode được compiler infer từ usage.

Có ba semantic modes chính:

```text
READ
MUTATE
MOVE
```

Ví dụ:

```axiom
let x = 10

let f = || x
```

→ READ capture.

---

```axiom
var x = 10

let f = || {
    x += 1
}
```

→ MUTATE capture.

---

```axiom
let buffer = create_buffer()

let f = move || {
    consume(buffer)
}
```

→ MOVE capture.

---

# 36. `move` closure

Syntax:

```axiom
move || {
    use(resource)
}
```

buộc closure lấy ownership của captured values.

Sau:

```axiom
let f = move || consume(resource)
```

thì:

```axiom
use(resource)
```

→ invalid.

Đây đặc biệt quan trọng khi:

```axiom
spawn(move || worker(state))
```

---

# 37. Why `move` is explicit

Nếu closure được truyền sang một execution domain khác:

```axiom
spawn(move || work(data))
```

thì source thể hiện rõ:

```text
closure owns data
```

Compiler không cần programmer viết lifetime.

Nhưng ownership transfer vẫn là semantic boundary nên phải explicit.

---

# 38. Mutable capture

```axiom
var counter = 0

let increment = || {
    counter += 1
}
```

Closure cần WRITE capability tới captured state.

Compiler đảm bảo không có conflicting access:

```axiom
print(counter)
increment()
```

nếu READ và WRITE capability overlap tại cùng thời điểm → compiler có thể yêu cầu capability kết thúc trước mutation.

---

# 39. Closure capture does not imply heap

Ví dụ:

```axiom
fn apply(x: i32) -> i32 {
    let offset = 10
    let f = |v| v + offset
    f(x)
}
```

Compiler có thể biến toàn bộ thành:

```text
x + 10
```

Không allocation.

---

# 40. Escaping closure

Nếu closure sống lâu hơn lexical scope:

```axiom
fn make_adder(x: i32) -> ??? {
    |y| x + y
}
```

environment `x` phải sống đủ lâu.

Compiler có nhiều lựa chọn:

```text
stack → heap promotion
caller storage
arena
boxed closure
```

tùy context.

Source semantics không buộc heap.

---

# 41. Closure return type

Axiom không cho phép anonymous closure type viết trực tiếp.

Do đó:

```axiom
fn make_adder(x: i32) -> ??? 
```

không hợp lệ.

Sử dụng:

```axiom
fn make_adder(x: i32) -> impl Fn(i32) -> i32 {
    |y| x + y
}
```

`impl Trait` ở return position là static opaque return type.

---

# 42. `impl Trait` closure return

```axiom
fn make_adder(x: i32) -> impl Fn(i32) -> i32 {
    |y| x + y
}
```

có nghĩa:

```text
caller knows:
    callable with i32
    returns i32

caller does not name:
    concrete closure type
```

Compiler vẫn biết concrete type hoàn toàn.

Do đó:

```text
no vtable
no dynamic dispatch
no mandatory heap
```

---

# 43. `impl Trait` is not dynamic dispatch

```axiom
impl Fn(i32) -> i32
```

→ static.

```axiom
dyn Fn(i32) -> i32
```

→ dynamic.

Đây là một semantic distinction quan trọng.

---

# 44. Dynamic callable

Khi programmer thực sự cần runtime polymorphism:

```axiom
Box<dyn Fn(i32) -> i32>
```

hoặc:

```axiom
view<dyn Fn(i32) -> i32>
```

Compiler có thể sử dụng conceptual:

```text
data pointer
dispatch pointer
```

Dynamic dispatch chỉ xuất hiện vì source yêu cầu.

---

# 45. Closure → function pointer

Một **capturing closure** không tự động convert thành:

```text
fn(...)
```

vì function pointer không chứa environment.

Ví dụ:

```axiom
let offset = 10
let f = |x| x + offset

let p: fn(i32) -> i32 = f
```

→ compile error.

---

# 46. Non-capturing closure

Closure không capture:

```axiom
let f = |x: i32| x * 2
```

có thể convert thành ordinary function value:

```axiom
let p: fn(i32) -> i32 = f
```

vì không cần environment.

Compiler có thể lower trực tiếp thành function pointer.

---

# 47. Closure traits

Axiom dùng callable traits conceptually:

```text
Fn
FnMut
FnOnce
```

Semantic distinction:

```text
Fn
    read-only invocation

FnMut
    mutable environment

FnOnce
    consumes closure/environment
```

Tên chính thức có thể giữ các trait này trong std/core trait namespace.

---

# 48. Closure call semantics

Closure call:

```axiom
f(x)
```

được resolve tới callable trait phù hợp.

Compiler không tạo một "magic object call".

Conceptually:

```text
Fn::call(f, x)
```

hoặc:

```text
FnMut::call_mut(...)
FnOnce::call_once(...)
```

depending on usage.

---

# 49. Closure consumption

Nếu closure move-captures a non-Copy resource:

```axiom
let f = move || consume(resource)
```

closure có thể là `FnOnce`.

Sau khi gọi:

```axiom
f()
```

closure có thể trở thành consumed/moved state nếu invocation tiêu thụ captured resource.

Gọi lại:

```axiom
f()
```

→ compile error nếu closure đã consumed.

---

# 50. Closure mutability

Ví dụ:

```axiom
var count = 0

let f = || {
    count += 1
}
```

closure environment chứa mutable state.

Compiler phải bảo đảm:

```text
no conflicting access
```

Không cần syntax:

```text
&mut
```

hoặc lifetime parameter.

---

# 51. Closure and concurrency

```axiom
let data = make_data()

spawn(move || {
    process(data)
})
```

Closure chuyển ownership của `data`.

Để `spawn` chạy trên execution context khác:

```text
closure must satisfy Send
```

Nếu closure capture:

```text
non-Send type
```

→ compile error.

---

# 52. `spawn_local`

Nếu execution context không rời thread:

```axiom
spawn_local(|| {
    use(local_state)
})
```

không nhất thiết yêu cầu `Send`.

Nhưng lifetime/capability safety vẫn được compiler kiểm tra.

---

# 53. Closure cannot hide unsafe

Closure:

```axiom
|| {
    unsafe {
        ...
    }
}
```

chỉ có unsafe region ở bên trong.

Việc closure tồn tại không biến toàn bộ code thành unsafe.

---

# 54. Closure and views

Closure capture một view:

```axiom
let v = view(buffer)

let f = || read(v)
```

closure không được escape owner lifetime.

Nếu closure được trả về:

```axiom
fn make() -> impl Fn() {
    let buffer = ...
    let v = view(buffer)

    || read(v)
}
```

→ compile error.

Compiler không cần lifetime syntax để phát hiện.

---

# 55. Closure and `mut_view`

Closure capture:

```axiom
let v = mut_view(buffer)

let f = || mutate(v)
```

closure giữ exclusive capability.

Do đó:

```axiom
mutate(buffer)
```

trong khi `f` còn live → conflict.

Nếu closure được consume và capability kết thúc, mutation có thể tiếp tục.

---

# 56. Closure cannot cross `await` with view

Theo concurrency freeze:

```text
view
mut_view
```

không được sống qua `.await`.

Do đó closure environment cũng không được chứa capability sống qua suspension.

Ví dụ:

```axiom
async fn task(buffer: Buffer) {
    let v = view(buffer)

    await_something().await

    use(v)
}
```

→ compile error.

Owned `buffer` có thể sống qua await.

---

# 57. Async function

```axiom
async fn fetch(url: Text) -> Result<Data, Error> {
    ...
}
```

không phải function trả về `Result` ngay.

Semantic result là một future/state-machine value.

Conceptually:

```text
async fn
    ↓
Future<Output = Result<Data, Error>>
```

---

# 58. Async does not imply thread

```axiom
fetch(url)
```

không tự tạo thread.

Async function chỉ tạo/lấy state machine.

Executor là library/runtime component riêng.

---

# 59. Async lowering

Compiler có thể lower:

```text
async fn
```

thành:

```text
state machine
```

với các state:

```text
START
WAIT_1
WAIT_2
DONE
PANIC
```

Các local variables sống qua suspension trở thành state-machine fields.

---

# 60. Async ownership

Nếu:

```axiom
async fn process(data: Buffer) -> Result<(), Error>
```

và `data` sống qua await:

```text
state machine owns data
```

không cần heap nếu compiler/executor representation cho phép stack-pinning phù hợp.

Nếu future escape:

```text
storage may need promotion
```

nhưng đó là compiler/storage decision.

---

# 61. Async future is ordinary value

Future:

```text
Copy?        usually no
Drop?        yes if resources/state require
Send?        derived
Share?       derived/explicit
```

Không có special hidden GC object.

---

# 62. Dropping Future

Theo invariant đã freeze:

> **Dropping a Future does not imply cancellation of external operations.**

Ví dụ:

```axiom
let f = network_request()
drop(f)
```

không được compiler giả định rằng network operation bên ngoài chắc chắn đã bị cancel.

Cancellation phải là explicit API/protocol.

---

# 63. Async function + `?`

```axiom
async fn load() -> Result<Data, Error> {
    let a = fetch_a().await?
    let b = fetch_b(a).await?

    Ok(b)
}
```

`?` vẫn chỉ là:

```text
Result control flow
```

Không liên quan trực tiếp đến executor.

---

# 64. `unsafe fn`

```axiom
unsafe fn read_raw(ptr: *const u8) -> u8 {
    ...
}
```

gọi `unsafe fn` yêu cầu unsafe context.

```axiom
unsafe {
    read_raw(ptr)
}
```

Nhưng `unsafe fn` không có nghĩa compiler bỏ qua:

- type checking
- ownership
- ABI correctness
- atomic semantics
- control-flow correctness
- machine-code validity.

---

# 65. `extern fn`

FFI:

```axiom
extern "C" fn foo(x: i32) -> i32
```

là function có ABI contract khác Axiom ABI.

Các contract cần xác định:

```text
calling convention
parameter representation
return representation
layout
ownership
error boundary
panic behavior
allocation ownership
```

---

# 66. Panic across FFI

Default:

```text
Axiom panic
    X
cross C ABI boundary
```

Panic không được tự động xuyên qua foreign stack.

Wrapper phải chuyển:

```text
panic → error/result/status
```

hoặc terminate theo explicit policy.

---

# 67. FFI ownership

Ví dụ:

```axiom
extern "C" fn foreign_free(ptr: *mut u8)
```

Axiom không được tự suy đoán:

```text
malloc/free domain
```

Ownership contract phải explicit.

Đây là invariant:

> **FFI Must Not Guess Allocation Domains.**

---

# 68. `comptime fn`

Function có thể chạy compile-time:

```axiom
comptime fn fibonacci(n: u32) -> u64 {
    ...
}
```

Nó sử dụng cùng:

```text
type system
expression semantics
ownership semantics
```

nhưng execution environment là compile-time.

---

# 69. Compile-time function cannot leak resources

Ví dụ conceptual:

```axiom
comptime fn load() -> File {
    ...
}
```

nếu `File` là runtime resource thì không được trả trực tiếp thành runtime value.

Comptime có thể đọc file nếu capability cho phép và trả:

```text
Bytes
Text
generated constant
generated source/artifact
```

nhưng resource handle không được escape.

---

# 70. Function effects

Axiom v0.1 **không đưa một effect system đầy đủ vào source syntax**.

Compiler vẫn có thể track internal effects:

```text
PURE
READ_MEMORY
WRITE_MEMORY
ALLOC
DROP
PANIC
ATOMIC
SYNC
FFI
IO
UNSAFE
SUSPEND
```

Nhưng đây là compiler metadata.

Không yêu cầu programmer viết:

```axiom
fn foo() effects(IO, Alloc, Panic)
```

trong v0.1.

---

# 71. Why effects stay internal

Điều này phù hợp với nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

Effect analysis rất hữu ích cho:

- optimizer
- parallelization
- purity analysis
- dead-code elimination
- AI tooling
- diagnostics

nhưng không nhất thiết phải trở thành syntax mà programmer phải duy trì.

---

# 72. Function purity

Compiler có thể **prove** một function không có side effect observable.

Nhưng không được suy luận ngược rằng:

```text
"không thấy mutation trong source"
```

→ pure.

External calls, FFI, atomics, globals, Drop đều có thể tạo effects.

---

# 73. Inlining

Compiler có thể inline bất kỳ function nào khi semantic conditions cho phép.

```axiom
fn square(x: i32) -> i32 {
    x * x
}
```

call:

```axiom
square(5)
```

có thể biến thành:

```text
25
```

Không cần programmer viết `inline`.

---

# 74. `@inline`

Nếu cần target/compiler hint:

```axiom
@inline
fn ...
```

chỉ là optimization request/hint.

Không được biến thành semantic requirement nếu ABI/size/debug constraints không cho phép.

Có thể có:

```text
@inline(always)
@inline(never)
```

ở system/compiler layer sau này.

---

# 75. Function call optimization

Compiler có thể:

```text
direct call
→ inline

indirect call
→ devirtualize

closure call
→ specialize

generic call
→ monomorphize

trait call
→ static dispatch

dyn call
→ indirect dispatch
```

Nhưng semantic distinction vẫn được giữ ở source/typed IR.

---

# 76. Dynamic dispatch

```axiom
fn render(x: view<dyn Renderable>) {
    x.render()
}
```

call có thể lower thành:

```text
data_ptr
dispatch_ptr
    ↓
method slot
```

Không có object header requirement.

---

# 77. Dynamic dispatch + ownership

Có thể:

```axiom
Box<dyn Renderable>
```

→ owning dynamic object.

Hoặc:

```axiom
view<dyn Renderable>
```

→ non-owning dynamic capability.

Do đó:

```text
dispatch mechanism
```

và:

```text
ownership mechanism
```

hoàn toàn độc lập.

---

# 78. Function ABI

Mỗi function cuối cùng có ABI representation:

```text
parameters
return
calling convention
register usage
stack layout
alignment
unwind/panic behavior
```

Nhưng source-level function signature không expose machine details.

---

# 79. Native Axiom ABI

Default:

```axiom
fn foo(...)
```

→

```text
extern "axiom"
```

conceptually.

Native ABI có thể thay đổi giữa compiler versions.

Nếu cần stable ABI:

```axiom
extern "C"
```

hoặc ABI version explicit sau này.

---

# 80. ABI is not type semantics

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

semantic type:

```text
(i32, i32) -> i32
```

ABI có thể là:

```text
EDI = a
ESI = b
EAX = result
```

nhưng đó chỉ là machine representation.

Compiler có quyền thay đổi:

```text
register assignment
stack usage
inlining
tail call
calling sequence
```

miễn ABI contract yêu cầu không bị phá vỡ ở boundary.

---

# 81. Function pointers and ABI

Một function value chỉ có thể chuyển thành foreign function pointer nếu ABI compatible.

Ví dụ:

```axiom
extern "C" fn callback(x: i32) -> i32
```

có thể dùng trong C callback API.

Một Axiom closure không-capture:

```axiom
|x| x + 1
```

không tự động trở thành C callback nếu ABI chưa được xác nhận.

---

# 82. Closure callback to C

Khi cần callback có environment:

```text
C API
    callback(void* userdata)
```

Axiom wrapper có thể tạo:

```text
userdata → closure environment
callback pointer → trampoline
```

Nhưng đây là FFI library mechanism.

Không được đưa hidden allocation/trampoline vào ordinary closure semantics.

---

# 83. Recursive closure

Closure có thể cần self-reference.

Axiom v0.1 không cần special `self` closure syntax.

Có thể dùng named function khi recursion là static:

```axiom
fn recurse(...) { ... }
```

Dynamic/self-referential closure patterns dùng explicit storage abstraction.

Điều này tránh capture cycle vô tình.

---

# 84. Closure cycles

Ví dụ conceptual:

```text
closure A captures B
B owns closure A
```

không được tự động giải quyết bằng GC.

Nếu programmer tạo cycle bằng:

```text
Rc
Arc
Shared
```

thì cycle management là trách nhiệm của abstraction (`Weak`, arena, handles...).

Không có hidden cycle collector.

---

# 85. Function local storage

Local function values:

```axiom
let f = |x| x + offset
```

có lifetime determined by semantic uses.

Compiler có thể:

```text
register
stack
inline
heap
```

tùy escape analysis.

---

# 86. Escape analysis

Compiler phân tích:

```text
closure escapes?
future escapes?
function value escapes?
reference/capability escapes?
```

Nếu không escape:

```text
closure environment
```

có thể nằm hoàn toàn trong registers/stack.

Nếu escape:

```text
promotion
```

có thể cần storage lâu hơn.

Programmer không phải viết:

```text
heap closure
stack closure
```

trừ khi storage identity là semantic requirement.

---

# 87. Function contracts

Axiom v0.1 không yêu cầu full dependent contracts.

Có thể có compiler assertions:

```axiom
assert(condition)
```

và static constraints:

```axiom
T: Trait
```

Không có:

```axiom
fn foo(x: i32)
    requires x > 0
```

trong Core v0.1.

Nếu sau này thêm contract system, phải tích hợp với verifier/Oracle chứ không tạo runtime exception model riêng.

---

# 88. Function semantic invariants

### AFN-20 — Functions Are First-Class Behavior Units

Function là abstraction behavior cơ bản của Axiom.

### AFN-21 — Function Parameters Have Explicit Semantic Modes

Parameter là value, `view`, hoặc `mut_view`; không có hidden borrow mode.

### AFN-22 — Value Parameters Transfer Ownership

Non-Copy value argument được move vào parameter.

### AFN-23 — Copy Arguments Preserve Value Ownership

Copy type có thể được truyền mà caller vẫn giữ value.

### AFN-24 — View Parameters Create Ephemeral Read Capability

Owner→view implicit conversion chỉ tại call boundary.

### AFN-25 — Mutable View Parameters Require Exclusive Capability

`mut_view<T>` không được conflict với live overlapping capability.

### AFN-26 — Return Transfers Ownership

Owned return value chuyển semantic ownership tới caller.

### AFN-27 — Return Does Not Imply Heap Allocation

Aggregate return có thể được register/caller-allocated.

### AFN-28 — Tuple Is The Multiple-Value Mechanism

Không có separate multi-return semantic category.

### AFN-29 — Function Arguments Have Deterministic Evaluation Order

Arguments evaluate left-to-right.

### AFN-30 — Generic Functions Have Compile-Time Semantics

Generic abstraction không yêu cầu runtime generic metadata.

### AFN-31 — Specialization Is Not Observable

Compiler specialization không thay đổi source semantics.

### AFN-32 — Function Values Are Distinct From Raw Code Pointers

Machine address là representation detail trừ khi ABI contract yêu cầu.

### AFN-33 — Closures Have Explicit Environment Semantics

Closure có thể capture lexical state.

### AFN-34 — Closure Capture Is Precise

Closure chỉ capture values thực sự được sử dụng.

### AFN-35 — Capture Mode Is READ/MUTATE/MOVE

Compiler infer capture mode từ usage.

### AFN-36 — Move Capture Transfers Ownership

`move` closure lấy ownership của captured values.

### AFN-37 — Closure Does Not Imply Heap Allocation

Capturing closure không mặc định là heap object.

### AFN-38 — Closure Environment Is Compiler-Represented

Concrete environment type không phải programmer-visible object requirement.

### AFN-39 — Escaping Closure Requires Valid Storage Lifetime

Closure environment phải sống đủ lâu.

### AFN-40 — Closure May Be Stack/Register Allocated

Nếu không escape và semantics cho phép.

### AFN-41 — Non-Capturing Closure May Convert To Function Value

Closure không capture có thể trở thành ordinary function value.

### AFN-42 — Capturing Closure Cannot Implicitly Become Function Pointer

Environment không thể biến mất một cách implicit.

### AFN-43 — Callable Trait Dispatch Is Deterministic

`Fn/FnMut/FnOnce` resolution không ambiguous.

### AFN-44 — Closure Consumption Is Tracked

`FnOnce` invocation có thể consume closure.

### AFN-45 — Closure Capture Obeys Ownership Rules

Closure không tạo alias ownership ngầm.

### AFN-46 — Closure Cannot Extend Capability Lifetime Illegally

Captured view/mut_view không thể escape owner.

### AFN-47 — View Cannot Cross Await

Closure/future state machine không được giữ live view qua suspension.

### AFN-48 — Async Does Not Imply Thread Creation

Async function tạo future/state machine, không tự spawn thread.

### AFN-49 — Async State Owns Values Live Across Suspension

Owned values có thể trở thành state-machine fields.

### AFN-50 — Dropping Future Does Not Imply External Cancellation

Cancellation phải explicit.

### AFN-51 — Unsafe Function Boundaries Are Explicit

Calling `unsafe fn` yêu cầu unsafe context.

### AFN-52 — FFI ABI Is Explicit

Foreign calling conventions không tự suy đoán.

### AFN-53 — Panic Does Not Cross FFI By Default

Panic phải được xử lý tại ABI boundary.

### AFN-54 — FFI Allocation Ownership Is Explicit

Compiler không đoán allocator domain.

### AFN-55 — Comptime Functions Use The Same Type Semantics

Comptime không có type system riêng.

### AFN-56 — Comptime Resources Cannot Escape

Compile-time resource không trở thành runtime resource implicit.

### AFN-57 — Internal Effects Are Compiler Metadata

Effect tracking không bắt programmer viết effect annotations trong v0.1.

### AFN-58 — Inlining Preserves Function Semantics

Inlining không được thay đổi observable behavior.

### AFN-59 — Dynamic Dispatch Is Explicit

`dyn Trait` mới yêu cầu dynamic dispatch.

### AFN-60 — Static Callable Abstractions Have No Required Runtime Dispatch

Generic/`impl Trait` callable có thể compile trực tiếp.

---

# 89. Một điểm rất quan trọng về closure

Sau khi khóa phần này, Axiom đạt được mô hình:

```text
                    Callable
                       │
          ┌────────────┴────────────┐
          │                         │
       Function                  Closure
          │                         │
   no environment          environment optional
          │                         │
     direct code             compiler-generated
          │                         │
          └────────────┬────────────┘
                       │
                static dispatch
                       │
                  optimized
                       │
               machine code
```

Chỉ khi programmer viết:

```text
dyn Fn(...)
```

mới xuất hiện:

```text
runtime dispatch
```

Đây là cách giữ được **functional programming ergonomics** mà không biến mọi callable thành heap object.

---

# Part XI — Struct · Enum · Algebraic Data · Layout · Destructuring

Phần tiếp theo nên khóa **data model thực sự của Axiom**.

Đây là phần đặc biệt quan trọng vì ta đã quyết định:

> **Struct thay thế class làm aggregate chính.**

Nhưng chỉ nói "struct không có class" là chưa đủ. Cần xác định chính xác:

```text
struct
tuple struct
unit struct
enum
variant payload
recursive type
generic struct
zero-sized type
field initialization
field visibility
field update
destructuring
pattern ownership
Option
Result
niche optimization
discriminant
layout
repr
packed
alignment
union
bitfield/system layout
```

và quan trọng hơn:

```text
Struct identity
Storage identity
Logical identity
```

để Axiom có thể biểu diễn từ:

```text
Vec2
```

đến:

```text
Entity
Graph
AST
GPU buffer descriptor
OS handle
network packet
```

mà không cần quay lại mô hình class/object truyền thống.