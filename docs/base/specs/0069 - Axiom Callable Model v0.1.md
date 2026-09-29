Tiếp tục với **Axiom Callable & Closure Model v0.1**. Đây là phần rất quan trọng vì nếu closure được thiết kế theo kiểu “object + heap + vtable” thì Axiom sẽ mất khá nhiều ưu điểm mà ta đang xây dựng.

# Axiom Callable Model v0.1

Nguyên tắc:

> **Function là code. Closure là code + environment. Function pointer và closure là hai semantic type khác nhau.**

Và:

> **Closure không mặc định có allocation, heap, object header hay vtable.**

Mô hình:

```text
Function
    │
    ├── named function
    ├── function pointer
    │
    └── closure
          │
          ├── code
          └── captured environment
```

---

# 1. Function bình thường

```axiom
fn add(a: i64, b: i64) -> i64 {
    a + b
}
```

Semantic:

```text
fn(i64, i64) -> i64
```

Compiler có thể biến thành:

```text
symbol → machine code
```

Không có object.

---

# 2. Function pointer

Có thể có:

```axiom
let f: fn(i64, i64) -> i64 = add;
```

Đây là một **callable code pointer**.

Conceptually:

```text
f
 ↓
function address
```

Không có environment.

---

# 3. Closure

Ví dụ:

```axiom
fn make_adder(x: i64) {
    |y| x + y
}
```

Closure cần giữ:

```text
code
environment:
    x
```

Conceptually:

```text
Closure {
    code_ptr
    env {
        x: i64
    }
}
```

Nhưng đây chỉ là conceptual representation.

Compiler có thể biến thành:

```text
struct __Closure0 {
    x: i64
}

fn __Closure0_call(env: view<__Closure0>, y: i64) -> i64 {
    env.x + y
}
```

---

# 4. Closure thực chất là compiler-generated struct

Đây là điểm rất đẹp cho Axiom.

```axiom
let x = 10;

let f = |y| x + y;
```

Compiler conceptual lowering:

```text
struct Closure0 {
    x: i64
}

fn Closure0_call(self: view<Closure0>, y: i64) -> i64 {
    self.x + y
}
```

Tức closure **không cần một object model riêng**.

---

# 5. Capture mode

Đây là phần cần chính xác.

Closure có thể capture:

```text
READ
MUTATE
MOVE
```

Compiler tự suy luận dựa trên body.

Ví dụ:

```axiom
let x = 10;
let f = || x + 1;
```

→ capture READ.

---

```axiom
var x = 10;
let mut f = || {
    x = x + 1;
};
```

→ capture MUTABLE.

---

```axiom
let file = open();
let f = move || {
    process(file);
};
```

→ capture OWN/MOVE.

Nhưng tôi muốn tránh bắt programmer phải viết `move` trong trường hợp compiler có thể suy luận rõ.

Do đó syntax `move` chỉ cần khi programmer **muốn ép ownership transfer** hoặc để xử lý ambiguity.

---

# 6. Closure inference

Ví dụ:

```axiom
let x = Vec<i64>{...};

let f = || {
    println(x.len());
};
```

Compiler thấy:

```text
x
 ↓
READ
```

không cần:

```text
|&x|
```

hoặc lifetime annotation.

Đúng với triết lý:

> **Compiler quản lý capability/lifetime; programmer không viết bureaucracy.**

---

# 7. Mutable capture

Ví dụ:

```axiom
var counter = 0;

let next = || {
    counter += 1;
    counter
};
```

Compiler tạo conceptual environment:

```text
Closure0 {
    counter: i64
}
```

và:

```text
fn call(env: mut_view<Closure0>) -> i64
```

Không cần heap.

---

# 8. Closure environment là value

Closure mặc định là value:

```text
Closure<TEnv>
```

Nếu environment có:

```text
i64
```

thì closure chỉ cần chứa `i64`.

Nếu environment có:

```text
Vec<T>
```

thì closure sở hữu `Vec<T>`.

Nếu:

```text
File
```

thì closure sở hữu `File`.

Do đó Drop tự nhiên:

```text
closure destroyed
 ↓
drop captured resources
```

---

# 9. Closure không Copy mặc định

Nếu closure chứa:

```text
File
Vec
Box
```

thì closure không thể Copy.

Ví dụ:

```axiom
let f = || use(file);

let g = f;
```

Nếu `f` không Copy:

```text
f → MOVED
g → owns closure
```

Sau đó:

```axiom
f();
```

→ compile error.

Không cần một closure-specific ownership system.

---

# 10. Closure có thể Copy

Nếu tất cả captured values Copy:

```axiom
let x: i64 = 10;
let f = |y| x + y;
```

thì closure có thể tự động có property:

```text
Copy
```

vì environment là Copy.

Compiler-known property:

```text
Copy(Closure0)
```

---

# 11. Closure không cần vtable

Một closure cụ thể:

```text
|x| x + captured
```

compiler biết exact type.

Call có thể trở thành:

```text
direct call
```

hoặc inline.

Không cần:

```text
vtable lookup
```

---

# 12. Generic function nhận closure

Ví dụ:

```axiom
fn apply<F>(f: F, x: i64) -> i64 {
    f(x)
}
```

Compiler instantiate:

```text
apply<Closure0>
```

và biết exact closure type.

Có thể inline toàn bộ:

```text
captured + x
```

thành một vài instructions.

Đây là zero-cost functional abstraction.

---

# 13. Trait callable

Có thể dùng một capability trait:

```axiom
trait Callable<Args> {
    type Output;
    fn call(self: view<Self>, args: Args) -> Self.Output;
}
```

Nhưng tôi **không muốn programmer phải thấy trait này trong phần lớn trường hợp**.

Syntax:

```axiom
f(x)
```

nên được compiler xử lý như callable operation.

---

# 14. Function và closure vẫn khác nhau

Đây là điểm nên giữ.

```text
fn(A) -> B
```

có thể biểu diễn:

```text
code pointer
```

Trong khi:

```text
Closure<F>
```

có:

```text
code + environment
```

Không nên tự động coi closure là function pointer.

---

# 15. Captureless closure

Đây là exception hữu ích.

```axiom
let f = |x: i64| x * 2;
```

Không capture gì.

Compiler có thể cho phép:

```text
Closure0
    ↓
fn(i64) -> i64
```

coercion.

Vì environment rỗng.

Do đó:

```axiom
let f: fn(i64) -> i64 = |x| x * 2;
```

hợp lệ.

---

# 16. Capturing closure → function pointer?

Không.

Ví dụ:

```axiom
let offset = 10;

let f = |x| x + offset;
```

Không thể:

```text
Closure
→ fn(i64)->i64
```

vì function pointer không có nơi chứa `offset`.

Nếu cần dynamic callback:

```text
dyn Callable
```

hoặc explicit closure object.

---

# 17. ABI của closure

Ở compiler IR có thể conceptual:

```text
ClosureCall {
    code_ptr
    env_ptr
    args...
}
```

Machine ABI có thể trở thành:

```text
register X = env
register Y = arg
CALL code
```

Nhưng đây là implementation detail.

---

# 18. Closure call có thể bị eliminate

Ví dụ:

```axiom
fn test() -> i64 {
    let x = 10;
    let f = |y| x + y;
    f(32)
}
```

Compiler có thể:

```text
closure allocation
→ eliminate

closure environment
→ scalarize

indirect call
→ direct call

inline
→ arithmetic
```

Kết quả machine code có thể chỉ còn:

```text
return 42
```

Đây chính là:

> **Abstraction Erasure.**

---

# 19. Escape analysis

Closure allocation chỉ cần nếu closure thực sự escape.

Ví dụ:

```axiom
fn test() {
    let f = |x| x + 1;
    f(10);
}
```

Không escape.

→ stack/register/compiler-generated.

Nhưng:

```axiom
fn make() -> ??? {
    let x = 10;
    return || x + 1;
}
```

environment phải sống sau function.

Compiler cần chuyển ownership của environment sang returned closure.

Có thể heap allocate:

```text
Closure
 ├── code
 └── heap environment
```

nhưng chỉ khi representation/lifetime yêu cầu.

---

# 20. Return closure

Syntax cần hỗ trợ:

```axiom
fn make_adder(x: i64) -> impl Fn(i64) -> i64 {
    |y| x + y
}
```

Tôi đề xuất Axiom có:

```text
impl Trait
```

ở return position.

Ý nghĩa:

```text
anonymous concrete type
```

chứ không phải dynamic dispatch.

Ví dụ:

```text
make_adder(10)
 ↓
Closure0
```

Caller không cần biết tên `Closure0`.

---

# 21. `impl Trait` không phải `dyn Trait`

Rất quan trọng:

```axiom
fn make() -> impl Callable
```

→ concrete hidden type, static dispatch.

```axiom
fn make() -> dyn Callable
```

→ dynamic dispatch/runtime representation.

Bề ngoài chỉ khác `impl` / `dyn`, nhưng semantics rất rõ.

---

# 22. Closure + `view`

Đây là nơi ownership model phải phát huy tác dụng.

Ví dụ:

```axiom
fn make_view() -> ??? {
    var data = Array<i64, 4>{...};

    return || data[0];
}
```

Nếu closure giữ `view(data)`:

```text
data
 ↓
local owner
 ↓
closure escapes
```

→ invalid.

Compiler phải reject.

```text
AX_VIEW_000x:
closure contains capability whose owner does not outlive closure
```

Không cần lifetime annotation.

---

# 23. Closure + owner

Nhưng:

```axiom
fn make() -> impl Callable {
    let data = Vec<i64>{...};

    return move || data.len();
}
```

có thể hợp lệ.

Closure owns:

```text
Vec
```

và lifetime:

```text
function local
     ↓ move
closure
     ↓
caller
```

Ownership graph rất rõ.

---

# 24. Closure + mutable view

Ví dụ:

```axiom
fn foo(data: mut_view<Vec<i64>>) {
    let f = || data.push(1);
}
```

Closure chứa mutable capability.

Compiler phải đảm bảo:

```text
closure active
 ↓
mutable capability active
 ↓
no conflicting access to data
```

Nếu closure không escape, compiler có thể reason locally.

Nếu closure escape:

```text
return f
```

mà `data` không sống đủ lâu:

```text
reject
```

---

# 25. `mut_view` + closure + async

Đây là một boundary tôi đề nghị cực kỳ nghiêm:

```axiom
async fn foo(data: mut_view<Data>) {
    let f = || mutate(data);

    await something();

    f();
}
```

Compiler phải theo dõi:

```text
SUSPEND
```

và capability state.

Nếu `mut_view` không hợp lệ qua suspension:

```text
reject
```

hoặc compiler chỉ cho phép nếu chứng minh owner/capability state vẫn valid.

V0.1 nên conservative.

---

# 26. Async closure

Có thể sau này:

```axiom
let f = async |x| {
    let a = await foo(x);
    a + 1
};
```

Conceptually:

```text
Closure Environment
        +
Async State Machine
```

Compiler có thể tạo:

```text
struct AsyncClosureState {
    captured...
    state...
    locals...
}
```

Không cần runtime-specific object.

---

# 27. Async không phải closure runtime object

Đây là distinction:

```text
async fn
```

không nhất thiết trả:

```text
heap Future object
```

Compiler có thể tạo:

```text
concrete state-machine value
```

và optimize.

Executor chỉ poll/resume nó.

---

# 28. Callback API

Một API Axiom:

```axiom
fn sort<T>(data: mut_view<Vec<T>>, compare: ...)
```

có thể nhận generic callable:

```axiom
sort(values, |a, b| a < b)
```

Compiler instantiate:

```text
sort<i64, Closure0>
```

và inline comparator.

Không có:

```text
virtual call
heap allocation
```

nếu không escape.

---

# 29. Dynamic callback

Nếu cần runtime plugin:

```axiom
fn register(callback: dyn Handler)
```

thì explicit dynamic dispatch.

Có thể representation:

```text
data_ptr
dispatch_ptr
```

và runtime call:

```text
dispatch_ptr.call(data_ptr, ...)
```

Đây là lúc overhead xuất hiện — nhưng programmer đã yêu cầu abstraction dynamic.

---

# 30. C callback

Đây là trường hợp khác.

C thường cần:

```text
fn(*mut void, ...)
```

Axiom closure capturing environment không thể tự động biến thành C function pointer.

Wrapper cần:

```text
closure
 ↓
stable environment
 ↓
extern "C" trampoline
 ↓
void* userdata
```

Compiler/library có thể cung cấp helper:

```axiom
CCallback::from(closure)
```

nhưng representation phải explicit.

---

# 31. Capture environment layout

Compiler-generated closure:

```text
struct __Closure42 {
    x: i64
    file: File
}
```

Layout mặc định compiler-controlled.

Nếu closure phải đi qua FFI:

```text
không được tự động export
```

phải có explicit ABI wrapper.

---

# 32. Closure naming

Programmer không cần nhìn thấy:

```text
__Closure42
```

Đây là compiler-internal type.

Diagnostics có thể hiển thị:

```text
closure defined at foo.ax:17
```

thay vì tên generated type.

---

# 33. Closure equality

Không nên mặc định có:

```axiom
f == g
```

cho closures.

Hai closure có thể cùng code nhưng environment khác.

Semantic identity không rõ.

Nếu cần identity:

```text
pointer/reference identity
```

phải explicit.

---

# 34. Closure ordering/hash

Không có mặc định:

```text
Hash<Closure>
Ord<Closure>
```

trừ khi programmer tạo wrapper có semantics cụ thể.

Điều này tránh compiler-generated environment vô tình trở thành public data semantics.

---

# 35. Closure Send/Share

Closure properties được suy ra từ captures.

Nếu:

```text
Closure captures:
    i64
    Vec<i64>
```

và tất cả phù hợp:

```text
Send(Closure)
```

có thể true.

Nếu capture:

```text
non-Send resource
```

thì:

```text
Send(Closure) = false
```

Tương tự `Share`.

Không cần programmer khai báo:

```text
Closure: Send
```

trừ khi API yêu cầu constraint.

---

# 36. Spawn closure

Ví dụ:

```axiom
spawn(|| work(data));
```

Compiler thấy closure environment:

```text
data
```

và spawn semantics yêu cầu:

```text
Closure: Send
```

Nếu closure owns `data`:

```text
data MOVE → task
```

Nếu chỉ view local:

```text
reject
```

nếu task có thể outlive owner.

Đây là một ví dụ rất đẹp của việc **một ownership system dùng chung cho closure + thread + async**.

---

# 37. Function pointer Send/Share

Function pointer captureless:

```text
fn(A) -> B
```

không có mutable environment.

Thông thường có thể:

```text
Send
Share
```

nhưng compiler/platform semantics vẫn phải định nghĩa rõ đối với function pointers và code unloading/plugin scenarios.

V0.1 có thể coi native function pointers là process-lifetime code references.

---

# 38. Closure call ABI trong MIR

MIR nên có distinction:

```text
CALL_DIRECT
CALL_FUNCTION_PTR
CALL_CLOSURE
CALL_DYNAMIC
```

nhưng không nhất thiết cả bốn tồn tại mãi ở LIR.

Ví dụ:

```text
MIR:
CALL_CLOSURE f, x

optimization:
closure known
↓
CALL_DIRECT Closure0::call

further:
inline
```

Nếu dynamic:

```text
CALL_DYNAMIC
```

thì xuống LIR thành indirect call.

---

# 39. Closure lowering phase

Tôi đề xuất compiler pipeline:

```text
Typed HIR
   ↓
Closure Capture Analysis
   ↓
Closure Environment Generation
   ↓
Async Lowering
   ↓
MIR
```

Closure capture analysis phải chạy **trước ownership verification**, vì verifier cần biết closure thực sự giữ capability nào.

---

# 40. Closure capture algorithm

Conceptually:

```text
For each closure:
    collect referenced outer locals
    classify each use:
        READ
        WRITE
        MOVE
    derive minimum capture mode
    build environment
    rewrite captures as environment fields
```

Ví dụ:

```axiom
var x = 10;

let f = || {
    x += 1;
};
```

Kết quả:

```text
Capture(x, MUTABLE)
```

---

# 41. Capture by reference không phải source primitive

Tôi muốn đặc biệt tránh Rust-style:

```text
&T
&mut T
```

trong closure semantics.

Axiom source chỉ nói:

```axiom
let f = || use(x);
```

Compiler quyết định:

```text
READ capability
```

hoặc:

```text
MOVE ownership
```

hoặc:

```text
MUTABLE capability
```

Điều này rất phù hợp triết lý ban đầu của Axiom.

---

# 42. Nhưng programmer vẫn có thể ép move

Có trường hợp compiler inference có thể chọn read:

```axiom
let f = || x;
```

nhưng programmer muốn closure **own** `x` để nó sống lâu hơn.

Cần syntax:

```axiom
let f = move || x;
```

Tôi nghĩ nên giữ `move` chỉ như **capture policy override**, không phải lifetime annotation.

Nó rất dễ hiểu:

```text
move || ...
```

= closure lấy ownership của captured values.

---

# 43. Capture ordering

Environment field order không nên là source semantic contract.

Compiler có thể:

```text
reorder
pack
scalarize
eliminate
```

trừ khi closure representation explicit.

---

# 44. Closure allocation invariant

### ACL-01 — No Mandatory Closure Allocation

Closure creation không mặc định yêu cầu heap allocation.

### ACL-02 — Closure Is Environment + Code

Closure có thể biểu diễn bằng generated environment + call function.

### ACL-03 — Capture Inference

Compiler suy luận capture mode.

### ACL-04 — Explicit Move Capture

`move` chỉ ép ownership transfer.

### ACL-05 — No Closure Object Header

Closure không có object header mặc định.

### ACL-06 — Closure Ownership

Captured resources thuộc closure và được Drop theo ownership rules.

### ACL-07 — View Provenance

Closure không được giữ view vượt lifetime của owner.

### ACL-08 — Async Boundary

Capabilities không hợp lệ không được vượt suspension.

### ACL-09 — Static Closure Dispatch

Generic closure calls mặc định static.

### ACL-10 — Dynamic Closure Explicit

Runtime dynamic callback cần explicit dynamic representation.

### ACL-11 — Captureless Conversion

Captureless closure có thể chuyển thành compatible function pointer.

### ACL-12 — FFI Explicitness

Capturing closure không tự động trở thành foreign function pointer.

---

# 45. Tổng hợp call model

Đến đây ta có thể chốt 5 dạng callable:

```text
┌──────────────────────┬─────────────────────┬───────────────────┐
│ Callable             │ Environment         │ Dispatch          │
├──────────────────────┼─────────────────────┼───────────────────┤
│ Named function       │ none                │ direct            │
│ Function pointer     │ none                │ indirect          │
│ Concrete closure     │ compiler-generated  │ static/direct     │
│ Generic callable     │ concrete            │ static            │
│ dyn Callable/trait   │ runtime environment │ dynamic/indirect  │
└──────────────────────┴─────────────────────┴───────────────────┘
```

Và compiler có quyền biến:

```text
closure
 ↓
environment
 ↓
direct call
 ↓
inline
 ↓
zero closure overhead
```

nếu semantics cho phép.

---

# 46. Một hệ quả rất quan trọng cho Axiom

Ta đang dần đạt được một kiến trúc khá khác C++/Rust:

```text
C++
    programmer controls too much low-level object machinery

Rust
    compiler checks a lot of explicit reference/lifetime syntax

Axiom
    programmer expresses ownership intent
    compiler infers capabilities/lifetimes
    representation remains compiler-controlled
```

Ví dụ cùng một ý tưởng:

```axiom
fn apply<T, F>(x: T, f: F) -> T {
    f(x)
}
```

Axiom không cần programmer viết:

```text
borrow
lifetime
closure trait
```

nhưng compiler bên trong vẫn có:

```text
ownership
region
capability
effect
Send/Share
capture
ABI
```

Đây chính là **Compiler Complexity Is Not Language Complexity** được áp dụng trực tiếp.

---

## Mảnh ghép tiếp theo tôi đề xuất: **Module / visibility / namespace / import sâu hơn**

Không phải package manager — phần đó đã có. Ta cần khóa **semantic namespace model**, đặc biệt:

```text
module
namespace
import
alias
pub
private
re-export
cyclic dependency
initialization
generic visibility
trait visibility
```

và quan trọng nhất:

> **Axiom có nên có global mutable/static state không, và nếu có thì initialization/destruction của nó phải hoạt động thế nào mà không biến thành một “hidden runtime”.**

Đây là bước rất đáng làm trước khi đi vào **static/thread-local storage + startup + linker + executable initialization**, vì nó chạm trực tiếp vào mục tiêu của Axiom: `fn main(){}` phải cực nhẹ nhưng vẫn cho phép các chương trình lớn có global state khi thực sự cần.