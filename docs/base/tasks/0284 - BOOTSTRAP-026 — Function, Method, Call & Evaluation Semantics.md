Tiếp tục với **BOOTSTRAP-026 — Function, Method, Call & Evaluation Semantics**.

Phần này sẽ khóa cách Axiom **gọi code**. Tôi đề xuất ưu tiên một nguyên tắc:

> **Function call trong source phải đơn giản; mọi complexity về ABI, register, stack, inlining, closure environment, generic specialization… thuộc compiler.**

---

# BOOTSTRAP-026 — Function, Method, Call & Evaluation Semantics

## 1. Function là primitive behavior duy nhất

Axiom không cần:

- method object
- member-function đặc biệt
- virtual function
- constructor/destructor function category
- delegate type riêng

Chỉ cần:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Mọi abstraction khác đều hạ xuống function.

---

# 2. Method chỉ là syntax sugar

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Có thể gọi:

```axiom
v.length()
```

Semantic:

```text
length(v)
```

Không tồn tại một "method object" bắt buộc.

Điều này tiếp tục đúng với generic:

```axiom
fn push<T>(self: mut_view<Vec<T>>, value: T)
```

---

# 3. `self` chỉ là parameter đặc biệt về syntax

Các dạng:

```axiom
fn foo(self: view<Self>)
fn foo(self: mut_view<Self>)
fn foo(self: Self)
```

tương ứng với:

```text
read receiver
mutable receiver
owning receiver
```

Không cần:

```text
this
super
virtual
override
```

---

# 4. Ba loại receiver

Đây là một quyết định rất đẹp cho Axiom.

### Read

```axiom
fn area(self: view<Circle>) -> f32
```

Không thay đổi object.

### Mutable

```axiom
fn resize(self: mut_view<Circle>, scale: f32)
```

Có quyền thay đổi.

### Owning

```axiom
fn into_buffer(self: Buffer) -> RawBuffer
```

Function tiêu thụ ownership.

Ví dụ:

```axiom
let raw = buffer.into_buffer()
```

Sau đó:

```axiom
buffer
```

không còn hợp lệ.

---

# 5. Method resolution

Compiler tìm theo thứ tự:

```text
1. inherent function
2. trait implementation
3. explicitly imported extension
4. generic extension
```

Ví dụ:

```axiom
struct Vec2 { ... }

fn normalize(self: mut_view<Vec2>) { ... }
```

gọi:

```axiom
v.normalize()
```

Compiler tìm function có receiver phù hợp.

---

# 6. Không cho implicit extension method toàn hệ thống

Ví dụ package A có:

```axiom
fn foo(self: view<MyType>)
```

package B cũng có:

```axiom
fn foo(self: view<MyType>)
```

Không nên để cả hai tự nhiên xuất hiện trong namespace.

Extension function phải được import:

```axiom
use math.geometry.normalize
```

hoặc thông qua trait.

Mục tiêu:

> **Method resolution phải deterministic và local.**

---

# 7. Function overload

Axiom có thể hỗ trợ overload, nhưng nên **hạn chế overload dựa trên type**.

Ví dụ:

```axiom
fn print(x: i32)
fn print(x: f64)
fn print(x: String)
```

hợp lệ.

Compiler chọn dựa trên static type.

Nhưng không nên có overload dựa trên:

- runtime value
- implicit conversion chain
- generic ranking quá phức tạp
- arbitrary contextual heuristics.

---

# 8. Không có implicit conversion chain khi overload

Ví dụ:

```axiom
fn foo(x: i64)
fn foo(x: f64)

let x: i32 = ...
foo(x)
```

Compiler không nên thử:

```text
i32 → i64 → f64
```

để "đoán".

Nếu cả hai candidate đều yêu cầu conversion:

```text
ambiguous call
```

hoặc programmer phải cast.

Điều này giúp compiler và AI agent đều dễ reasoning.

---

# 9. Generic overload

Ví dụ:

```axiom
fn process<T>(x: T)
fn process(x: i32)
```

Nếu:

```axiom
process(10)
```

compiler có thể ưu tiên exact concrete overload.

Nhưng rule phải được formal hóa, không để "best match" thành một hệ thống hàng trăm quy tắc.

Tôi đề xuất:

```text
exact match
    >
generic exact match
    >
explicitly permitted coercion
```

Không có implicit numeric conversion để phá ambiguity.

---

# 10. Không có default arguments trong Core

Tôi nghiêng mạnh về **không có default argument**:

Không:

```axiom
fn connect(host: String, port: u16 = 80)
```

Thay bằng:

```axiom
fn connect(host: String, port: u16)
```

và:

```axiom
fn connect_default(host: String) {
    connect(host, 80)
}
```

Hoặc tốt hơn, API có named configuration:

```axiom
connect(
    host,
    Config {
        port: 80
    }
)
```

Lý do:

- ABI rõ
- function identity rõ
- FFI dễ
- overload dễ
- compiler đơn giản
- IDE/AI dễ hiểu.

Default values phù hợp library API nhưng không cần language feature.

---

# 11. Named arguments: có thể có, nhưng không phải Core requirement

Tôi đề xuất v1 **không cần named arguments**.

```axiom
connect(
    host = "...",
    port = 80
)
```

có lợi cho readability nhưng lại mở thêm semantics:

- parameter names trở thành API contract
- overload resolution phức tạp hơn
- ABI mapping
- refactoring concerns.

Có thể thêm sau ở syntax layer mà không thay đổi semantic Core.

---

# 12. Variadic function

Cần phân biệt hai loại.

### C-style variadic

```axiom
extern "C" fn printf(format: *const u8, ...)
```

→ FFI/system feature.

### Axiom variadic

```axiom
fn log(args...)
```

Tôi **không đưa vào Core v1**.

Thay bằng generic/tuple/slice:

```axiom
fn log(args: view<[LogArg]>)
```

hoặc compile-time formatting:

```axiom
log("x={}, y={}", x, y)
```

được xử lý bởi comptime.

Như vậy tránh runtime variadic machinery.

---

# 13. Argument evaluation order

Axiom phải **chốt deterministic evaluation order**.

Tôi đề xuất:

> **Arguments được evaluate từ trái sang phải.**

Ví dụ:

```axiom
foo(a(), b(), c())
```

luôn:

```text
a()
 ↓
b()
 ↓
c()
 ↓
foo(...)
```

Không giống kiểu:

> compiler thích evaluate cái nào trước cũng được.

Điều này quan trọng cho:

- side effects
- logging
- resource acquisition
- deterministic debugging
- AI code generation.

Compiler vẫn được phép reorder machine instructions **sau khi semantic effects đã được xác định**.

---

# 14. Receiver evaluation

```axiom
object.method(a(), b())
```

thứ tự:

```text
object
 ↓
a()
 ↓
b()
 ↓
method(object, ...)
```

Receiver được evaluate trước arguments.

---

# 15. Field evaluation

```axiom
foo(x.a, x.b)
```

có deterministic semantic order:

```text
x.a
x.b
foo(...)
```

Compiler vẫn có thể optimize load order nếu không thay đổi observable semantics.

---

# 16. Return

Function:

```axiom
fn make_vec() -> Vec {
    Vec { ... }
}
```

không đồng nghĩa:

```text
heap allocation
```

Compiler có thể:

```text
caller allocated return
register return
stack return
sret
move
```

tùy ABI.

Điều này kế thừa:

```text
AMEM-28 Return Does Not Imply Heap Allocation
AMEM-29 Caller-Allocated Returns Are Permitted
```

---

# 17. Return là ownership transfer

Ví dụ:

```axiom
fn create() -> Buffer {
    let b = Buffer(...)
    return b
}
```

`b` được Move ra ngoài.

Không copy bắt buộc.

Compiler có thể tối ưu thành:

```text
construct directly in caller storage
```

---

# 18. `return` không phải cleanup bypass

Ví dụ:

```axiom
fn foo() -> Result<()> {
    let a = ResourceA()
    let b = ResourceB()

    if error {
        return Err(...)
    }

    Ok(())
}
```

Compiler phải generate:

```text
error path:
    drop(b)
    drop(a)
    return
```

theo Drop semantics.

Không có "return nhanh bỏ qua destructor".

---

# 19. `defer`

Tôi đề xuất **không đưa `defer` vào Core v1**.

Ví dụ Go:

```text
defer close()
```

không thực sự cần nếu Axiom đã có deterministic Drop.

Thay:

```axiom
fn process() -> Result<()> {
    let file = File.open(...)
    ...
}
```

Drop của `file` tự động cleanup.

Nếu cần cleanup logic có thứ tự đặc biệt:

```axiom
let guard = resource.acquire()
...
drop(guard)
```

Điều này explicit hơn.

---

# 20. `drop(x)` là primitive escape khỏi scope

Đã có:

```axiom
drop(resource)
```

Ví dụ:

```axiom
let lock = mutex.lock()

critical_section()

drop(lock)

do_other_work()
```

Compiler biết capability đã kết thúc.

Đây là cách Axiom thay phần lớn nhu cầu của `defer`.

---

# 21. `?` operator

Tôi đề xuất **có**.

Ví dụ:

```axiom
fn load() -> Result<Data, Error> {
    let file = open("data.bin")?
    let bytes = file.read()?
    parse(bytes)
}
```

Semantic:

```text
Ok(x) → continue
Err(e) → return Err(e)
```

Không phải exception.

---

# 22. `?` phải generic trên Result-like protocol

Không hard-code chỉ `Result`.

Có thể có trait/compiler protocol:

```text
Try
```

nhưng Core v1 nên giữ behavior rất đơn giản.

Ví dụ:

```axiom
Result<T,E>
Option<T>
```

được compiler hiểu trực tiếp.

Các custom Try-like type có thể mở rộng sau.

---

# 23. Panic

Panic không phải exception.

```axiom
panic("invalid state")
```

là abnormal control flow.

Profile:

```text
abort
```

hoặc:

```text
unwind
```

được chọn ở compilation/runtime profile.

Nếu unwind:

```text
panic
 ↓
drop initialized resources
 ↓
unwind
```

Nếu abort:

```text
panic
 ↓
terminate
```

---

# 24. Không có exception catch trong Core

Không:

```axiom
try {
    ...
}
catch e {
    ...
}
```

Recoverable failure:

```axiom
Result<T,E>
```

Unexpected failure:

```axiom
panic
```

System-level exceptions/signals/SEH có thể được expose bởi platform library/FFI.

Nhưng không biến chúng thành universal language mechanism.

---

# 25. Function pointer

Syntax:

```axiom
type Callback = fn(i32, i32) -> i32
```

Gọi:

```axiom
callback(a, b)
```

Function pointer có thể là:

- direct symbol
- function address
- indirect call

Compiler chọn representation.

---

# 26. Closure call

Closure:

```axiom
let f = |x| x * 2
```

gọi:

```axiom
f(10)
```

Semantic giống function call.

Compiler có thể specialize:

```text
closure
 ↓
known call target
 ↓
inline
 ↓
eliminate environment
```

Nếu escape:

```text
closure environment
 ↓
storage analysis
```

Có thể stack/heap/arena tùy tình huống.

---

# 27. Tail call

Axiom nên **cho phép compiler tự tối ưu tail call**, không cần keyword.

Ví dụ:

```axiom
fn loop(x: i32) -> i32 {
    if x == 0 {
        return 0
    }

    loop(x - 1)
}
```

Nếu ABI/semantics cho phép:

```text
call
```

có thể trở thành:

```text
jump
```

Không cần:

```text
tailcall
```

trong source.

Nếu programmer cần **bắt buộc** tail call vì algorithm correctness/stack guarantee, có thể bổ sung annotation system-level sau.

---

# 28. `noreturn`

Compiler-known attribute:

```axiom
@noreturn
fn abort_process() -> never
```

Nhưng type `never` mới là semantic mechanism.

```axiom
fn fail() -> never {
    panic("fatal")
}
```

Compiler biết function không return bình thường.

---

# 29. `inline`

Không nên coi:

```axiom
@inline
```

là "hãy inline bằng mọi giá".

Tôi đề xuất:

```text
@inline
```

= **optimization hint**.

Compiler vẫn có thể từ chối nếu ABI/code-size/optimization policy không phù hợp.

Có:

```text
@inline
@noinline
@cold
```

ở compiler attribute layer.

Không để những attribute này thay đổi semantic meaning.

---

# 30. `@noinline`

Có ích cho:

- profiling
- code size
- debugging
- hot/cold boundary
- JIT-like experimentation.

Nhưng vẫn là optimization contract, không phải language semantics.

---

# 31. `@export`

Public function không nhất thiết trở thành symbol ABI.

Ví dụ:

```axiom
pub fn foo() { ... }
```

chỉ có nghĩa là source-level visibility.

Muốn export binary:

```axiom
@export("foo")
pub fn foo() { ... }
```

Điều này kế thừa BOOTSTRAP-023:

> **public != binary exported**

---

# 32. Calling convention

Mặc định:

```axiom
fn
```

dùng Axiom ABI.

FFI:

```axiom
extern "C" fn ...
```

Có thể:

```text
extern "system"
extern "stdcall"
extern "aapcs"
extern "sysv64"
```

khi target cần.

Không để programmer phải tự quản lý registers/stack.

---

# 33. Syscall

System programming cần khả năng gọi syscall trực tiếp.

Không nhất thiết biến syscall thành function type đặc biệt.

Có thể:

```axiom
@syscall
fn write(fd: i32, buf: *const u8, len: usize) -> isize
```

hoặc target-specific ABI intrinsic.

`@syscall` chỉ định semantics ABI/lowering.

Không tạo runtime dependency.

---

# 34. Function purity

Tôi đề xuất **không đưa effect system đầy đủ vào Core v1**.

Không bắt:

```text
fn foo() pure
fn bar() throws
fn baz() io
```

Lý do:

- type/effect explosion
- ecosystem complexity
- khó FFI
- compiler complexity tăng mạnh.

Compiler vẫn có thể internally track:

```text
read/write
panic
allocation
suspend
unsafe
```

để optimize/verify.

Nhưng programmer không phải annotate mọi function.

---

# 35. `unsafe fn`

Giữ:

```axiom
unsafe fn read(p: *const T) -> T
```

gọi nó:

```axiom
unsafe {
    read(p)
}
```

hoặc trong `unsafe fn`.

Điều này giúp unsafe boundary rất rõ.

---

# 36. `unsafe` propagation

Nếu:

```axiom
unsafe fn foo()
```

thì function gọi `foo()` phải nằm trong unsafe context.

Nhưng nếu ta tạo safe wrapper:

```axiom
fn safe_foo(...) -> Result<...> {
    unsafe {
        ...
    }
}
```

thì caller không cần biết implementation bên dưới dùng unsafe.

Đây là pattern quan trọng:

```text
unsafe implementation
        ↓
validated abstraction
        ↓
safe API
```

---

# 37. Function call có thể được hoàn toàn erase

Ví dụ:

```axiom
fn square(x: i32) -> i32 {
    x * x
}

let y = square(10)
```

Compiler có thể biến thành:

```text
100
```

hoặc:

```asm
imul
```

không còn function call.

Nhưng semantics vẫn là function call.

---

# 38. `call` là semantic operation trước khi là machine instruction

MIR có thể có:

```text
CALL
    target = foo
    args = [...]
    destination = ...
```

Sau optimization:

```text
CALL
→ INLINE
→ SSA
→ constant fold
```

hoặc:

```text
CALL
→ direct call
```

hoặc:

```text
CALL
→ indirect call
```

Backend không quyết định source semantics.

---

# 39. ABI lowering diễn ra sau semantic optimization

Pipeline:

```text
Typed HIR
   ↓
Ownership / Capability
   ↓
MIR
   ↓
Semantic optimization
   ↓
Inlining / specialization
   ↓
Representation analysis
   ↓
ABI classification
   ↓
ABI MIR
   ↓
LIR
   ↓
Machine code
```

Điều này đặc biệt quan trọng cho Axiom vì function abstraction không được khóa quá sớm vào ABI.

---

# 40. Một ví dụ đầy đủ

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}

struct Circle {
    radius: f32
}

impl Drawable for Circle {
    fn draw(self: view<Circle>) {
        ...
    }
}

fn render<T: Drawable>(item: view<T>) {
    item.draw()
}

fn main() {
    let circle = Circle {
        radius: 10.0
    }

    render(circle)
}
```

Compiler có thể biến:

```text
render<Circle>(circle)
       ↓
static dispatch
       ↓
Circle.draw(circle)
       ↓
inline
       ↓
machine code
```

Không có:

```text
object
vtable
heap
reference
runtime generic metadata
```

---

# 41. Dynamic dispatch vẫn có

Nếu programmer muốn:

```axiom
fn render_all(items: view<[dyn Drawable]>) {
    for item in items {
        item.draw()
    }
}
```

thì compiler phải giữ dynamic dispatch representation.

Đây là trade-off **explicit**.

---

# 42. Invariants BOOTSTRAP-026

```text id="1k4x7a"
AFUNC-20  Function is the fundamental behavior primitive.

AFUNC-21  Methods are syntax over functions.

AFUNC-22  self is a receiver parameter.

AFUNC-23  Read receivers use view semantics.

AFUNC-24  Mutable receivers use mut_view semantics.

AFUNC-25  Owning receivers consume ownership.

AFUNC-26  Method resolution is deterministic.

AFUNC-27  Extension methods require explicit visibility/import.

AFUNC-28  Overload resolution is compile-time.

AFUNC-29  Implicit conversion chains are not used for overload resolution.

AFUNC-30  Numeric narrowing is never implicit.

AFUNC-31  Argument evaluation is left-to-right.

AFUNC-32  Receiver evaluation precedes argument evaluation.

AFUNC-33  Compiler optimization may reorder operations when semantics are preserved.

AFUNC-34  Return transfers ownership when returning an owning value.

AFUNC-35  Return does not imply heap allocation.

AFUNC-36  Return preserves deterministic Drop semantics.

AFUNC-37  defer is not a Core requirement.

AFUNC-38  Explicit drop provides early resource release.

AFUNC-39  ? provides structured Result/Option propagation.

AFUNC-40  Recoverable failure uses Result/Option rather than exceptions.

AFUNC-41  Panic is distinct from recoverable failure.

AFUNC-42  Exception catching is not a Core mechanism.

AFUNC-43  Function pointers are first-class callable values.

AFUNC-44  Capturing closures are distinct from function pointers.

AFUNC-45  Closure capture follows ownership/capability semantics.

AFUNC-46  Closure representation is compiler-controlled.

AFUNC-47  Tail-call optimization is compiler permitted.

AFUNC-48  Inline/noinline are optimization controls, not semantic changes.

AFUNC-49  noreturn is represented by the never type.

AFUNC-50  Public visibility does not imply binary export.

AFUNC-51  Binary export requires an explicit ABI/export contract.

AFUNC-52  Axiom functions use Axiom ABI by default.

AFUNC-53  Foreign functions require explicit ABI declarations.

AFUNC-54  Syscalls require explicit system-level ABI semantics.

AFUNC-55  Unsafe functions require unsafe calling context.

AFUNC-56  Safe wrappers may encapsulate unsafe implementation.

AFUNC-57  Core v1 does not require a programmer-facing effect system.

AFUNC-58  Function calls are semantic MIR operations.

AFUNC-59  Function calls may be eliminated by optimization.

AFUNC-60  Function abstraction does not imply runtime call overhead.

AFUNC-61  ABI lowering occurs after semantic optimization.

AFUNC-62  Generic function dispatch is static by default.

AFUNC-63  Dynamic dispatch requires explicit dynamic representation.

AFUNC-64  Dynamic dispatch does not imply class semantics.

AFUNC-65  Default arguments are not Core semantics.

AFUNC-66  Named arguments are not required by Core v1.

AFUNC-67  C-style variadics are restricted to FFI/system boundaries.

AFUNC-68  Axiom variadic functions are not required in Core v1.

AFUNC-69  Function evaluation order is deterministic.

AFUNC-70  Compiler transformations cannot alter observable evaluation order semantics.
```

---

# 43. Một điểm tôi muốn điều chỉnh so với thiết kế ngôn ngữ thông thường

Axiom đang hình thành một nguyên tắc khá mạnh:

### Programmer sees

```text
value
struct
enum
trait
function
view
mut_view
Handle
```

### Compiler sees

```text
place
ownership
capability
provenance
lifetime
alias region
generic obligation
ABI
SSA
register
storage
```

### Machine sees

```text
register
stack
memory
branch
call
load
store
SIMD
atomic
syscall
```

**Ba tầng này không nên trộn vào nhau.**

Đây có lẽ là một trong những điểm quan trọng nhất của toàn bộ Axiom.

---

# 44. Trạng thái Core hiện tại

Sau BOOTSTRAP-026, ta đã khóa được:

```text
                    AXIOM CORE
                        │
       ┌────────────────┼────────────────┐
       │                │                │
    TYPE SYSTEM      MEMORY          EXECUTION
       │                │                │
 struct/enum        ownership       function
 trait/generic      capability      method
 Option/Result      view            closure
 dyn Trait          pointer         async
       │                │                │
       └────────────────┼────────────────┘
                        │
                     CONCURRENCY
                        │
             thread/fiber/task/future
                        │
                        ▼
                       MIR
                        │
              semantic optimization
                        │
                        ▼
                       ABI
                        │
                        ▼
                  machine code
```

Điểm đáng chú ý là **không còn cần thêm một object model lớn** để kết nối các phần này.

---

## Bước tiếp theo — BOOTSTRAP-027

Phần hợp lý tiếp theo là **Control Flow & Pattern Semantics**.

Ta sẽ khóa:

- `if / else`
- `loop`
- `while`
- `for`
- `break`
- `continue`
- `return`
- `match`
- pattern destructuring
- guard
- `if let`
- `while let`
- `?`
- `never`
- unreachable
- labeled loop
- `defer`/scope cleanup đã quyết định không cần
- compiler lowering toàn bộ control flow → CFG/MIR
- exhaustiveness
- unreachable pattern
- pattern ownership/move
- partial move
- branch optimization
- `switch`/jump table
- tail recursion
- zero-cost iteration

Đây sẽ là bước khóa **control-flow semantics** trước khi chuyển sang các phần như **collection/iterator/string**, rồi mới tiến tới **Core Standard Library và compiler bootstrap**.