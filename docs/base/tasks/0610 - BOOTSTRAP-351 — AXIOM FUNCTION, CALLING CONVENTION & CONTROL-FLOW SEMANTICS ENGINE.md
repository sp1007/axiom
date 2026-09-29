# BOOTSTRAP-351 — AXIOM FUNCTION, CALLING CONVENTION & CONTROL-FLOW SEMANTICS ENGINE

Sau numeric layer, bước tiếp theo nên khóa **function/call semantics**. Đây là nền tảng mà gần như toàn bộ compiler, ABI, closure, async, coroutine, FFI, generic specialization và optimization đều phụ thuộc.

Mục tiêu:

> **Một function trong Axiom phải có semantic rõ ràng ở source level, nhưng compiler được tự do biến nó thành register call, inline, tail call, closure conversion, coroutine state machine hoặc thậm chí loại bỏ hoàn toàn nếu không còn observable effect.**

---

## 1. Function là đơn vị behavior cơ bản

Axiom không cần class method như một semantic primitive.

Function là primitive:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Method:

```text
fn length(self: Vec) -> usize
```

chỉ là syntax sugar cho:

```text
length(v)
```

Do đó compiler chỉ cần một function model thống nhất.

---

# 2. Function signature

Semantic signature gồm:

```text
FunctionSignature {
    params
    return_type
    generic_params
    where_constraints
    effects
    calling_convention
    visibility
    async_kind
    unsafe_kind
    comptime_kind
    execution_domain
}
```

Không để những thông tin này bị rải rác trong nhiều compiler subsystem.

---

# 3. Evaluation order

Axiom phải có evaluation order **hoàn toàn xác định**.

Ví dụ:

```text
f(a(), b(), c())
```

không được cho phép compiler tự chọn:

```text
a → b → c
```

hoặc:

```text
c → a → b
```

nếu side effect có thể quan sát được.

Quy tắc v0.1:

> Argument expressions được evaluate từ trái sang phải.

Ví dụ:

```text
f(x(), y())
```

semantic:

```text
x()
→ y()
→ call f
```

Optimizer vẫn có thể reorder khi chứng minh rằng thứ tự không observable.

---

# 4. Return semantics

```text
return expr
```

phải:

1. evaluate `expr`;
2. materialize/move return value;
3. chạy Drop cần thiết của local resources;
4. thực hiện return.

Ví dụ:

```text
fn f() -> Buffer {
    let a = Buffer(...)
    let b = Buffer(...)

    return b
}
```

`b` được move ra ngoài.

`a` được Drop.

Không được tạo temporary copy vô nghĩa.

---

# 5. Return value không đồng nghĩa heap allocation

Ví dụ:

```text
fn make_vec() -> Vec3 {
    Vec3(...)
}
```

không mặc định tạo object trên heap.

Compiler có thể:

```text
register return
caller-allocated return
stack slot
SSA value
```

tùy ABI và optimization.

---

# 6. Large return value

Nếu:

```text
struct Huge {
    data: [u8; 4096]
}
```

compiler/ABI có thể sử dụng:

```text
sret / caller-allocated return storage
```

Source semantics vẫn là:

```text
Huge
```

Programmer không phải viết:

```text
out: *mut Huge
```

chỉ để tối ưu ABI.

---

# 7. Parameter passing

Semantic parameter có thể là:

```text
T
view<T>
mut_view<T>
```

và ownership semantics quyết định:

```text
Copy
Move
Read capability
Write capability
```

Compiler quyết định physical ABI:

```text
register
stack
memory
indirect
```

---

# 8. `self`

Axiom method:

```text
fn scale(self: Vec3, x: f32) -> Vec3
```

có semantic tương đương:

```text
fn scale(v: Vec3, x: f32) -> Vec3
```

Call:

```text
v.scale(2.0)
```

được resolve thành:

```text
scale(v, 2.0)
```

Không có hidden object pointer.

---

# 9. `self` modes

Có ba semantic mode chính:

```text
self: T
self: view<T>
self: mut_view<T>
```

Ví dụ:

```text
fn consume(self: Buffer) { ... }

fn size(self: view<Buffer>) -> usize { ... }

fn clear(self: mut_view<Buffer>) { ... }
```

Compiler có thể cung cấp syntax ngắn hơn:

```text
fn consume(self)
fn size(self)
fn clear(mut self)
```

nhưng semantic vẫn là ownership/capability model đã frozen.

---

# 10. Function purity không mặc định

Axiom không nên ép mọi function khai báo:

```text
pure
```

cho các function thông thường.

Compiler tự phân tích effect.

Ví dụ:

```text
fn square(x: i32) -> i32 {
    x * x
}
```

compiler biết function này không có observable side effect.

Nhưng:

```text
fn write_file(...)
```

có effect:

```text
IO
```

---

# 11. Effect system

Function effect summary có thể gồm:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Synchronize
IO
Panic
Foreign
Unsafe
GPU
Comptime
```

Effect không nhất thiết phải xuất hiện trong source signature v0.1.

Compiler suy luận:

```text
FunctionEffectSummary
```

và sử dụng cho optimization/verification.

---

# 12. Explicit effect constraints

Khi cần kiểm soát mạnh, API có thể khai báo:

```text
@noalloc
fn foo(...)
```

hoặc:

```text
@pure
fn ...
```

Nhưng đây là **contract**, không phải annotation bắt buộc cho mọi function.

Compiler sẽ verify.

Ví dụ:

```text
@noalloc
fn process(...) {
    Vec.new(...)
}
```

→ compile error nếu thực sự có allocation path.

---

# 13. `unsafe fn`

```text
unsafe fn read(ptr: *const u8) -> u8
```

chỉ có nghĩa function yêu cầu caller thỏa mãn unsafe preconditions.

Bên trong function vẫn có verifier.

Unsafe không biến toàn bộ function thành:

> compiler bỏ kiểm tra.

---

# 14. `extern fn`

FFI function:

```text
extern "C" fn memcpy(...)
```

là ABI contract.

Compiler không được giả định semantic nội bộ của foreign function.

Effect mặc định conservative:

```text
Foreign
Read
Write
Unknown
```

trừ khi FFI contract cung cấp summary đáng tin cậy.

---

# 15. Tail call

Axiom nên có semantic tail-call capability:

```text
return f(x)
```

có thể được compiler lower thành tail call nếu ABI cho phép.

Không nên bắt programmer viết:

```text
tailcall f(...)
```

trừ khi sau này cần một explicit guarantee.

Có thể thêm:

```text
@must_tail
```

cho system/ABI code.

Nếu contract không thể thỏa:

```text
compile error
```

thay vì âm thầm phá guarantee.

---

# 16. Inlining

Inlining hoàn toàn là compiler optimization.

Source:

```text
f(x)
```

không thay đổi semantic khi:

```text
inline
```

hay:

```text
noinline
```

`@inline`, `@noinline` chỉ là optimization directives.

Compiler không được để chúng thay đổi ownership/effect semantics.

---

# 17. Function identity

Mỗi function có:

```text
FunctionId
```

nhưng cần phân biệt:

```text
SourceFunctionId
GenericFunctionId
MonomorphizedFunctionId
CodeInstanceId
SymbolId
```

Ví dụ:

```text
fn max<T: Ord>(...)
```

là một generic source function.

Có thể tạo:

```text
max<i32>
max<i64>
max<f32>
```

mỗi cái là specialization/code instance riêng.

---

# 18. Generic specialization

Axiom ưu tiên:

> static dispatch trước, dynamic dispatch chỉ khi programmer yêu cầu.

Ví dụ:

```text
fn sum<T: Numeric>(...)
```

compiler có thể generate:

```text
sum_i32
sum_f32
sum_vector_f32_8
```

Không cần vtable.

Nếu muốn runtime polymorphism:

```text
dyn Trait
```

mới tạo dynamic dispatch.

---

# 19. Function pointers

Function pointer là first-class value:

```text
fn(i32) -> i32
```

Có thể:

```text
let f = add
let x = f(1, 2)
```

Representation có thể là:

```text
code pointer
```

hoặc target-specific representation.

Không mặc định có:

```text
object header
```

hay heap allocation.

---

# 20. Closures

Closure:

```text
let factor = 10

let f = |x: i32| x * factor
```

semantic là:

```text
Closure {
    environment
    function
}
```

Compiler phân tích capture:

```text
by_value
by_view
by_mut_view
```

và capture tối thiểu.

Không tạo heap allocation nếu compiler chứng minh closure không escape.

---

# 21. Closure conversion

Compiler có thể biến:

```text
|x| x + factor
```

thành conceptually:

```text
struct ClosureEnv {
    factor: i32
}

fn closure(env: view<ClosureEnv>, x: i32) -> i32
```

nhưng đây là compiler IR, không phải source-level requirement.

---

# 22. Escaping closure

Nếu closure:

```text
return |x| x + factor
```

thì `factor` phải sống đủ lâu.

Compiler có thể:

- move capture;
- promote environment;
- caller-allocate;
- heap allocate;
- arena allocate.

Không được để dangling capture.

---

# 23. Recursive function

Function có thể recursive:

```text
fn fib(n: u32) -> u32 {
    if n < 2 {
        n
    } else {
        fib(n - 1) + fib(n - 2)
    }
}
```

Không cần annotation.

Compiler phải hỗ trợ:

```text
direct recursion
mutual recursion
generic recursion
closure recursion
```

với cycle handling ở resolver/type checker.

---

# 24. Recursion depth

Axiom không đảm bảo recursion luôn không giới hạn.

Stack exhaustion là runtime/resource failure.

Compiler có thể:

```text
tail-call optimize
loop transform
inline bounded recursion
```

nhưng không được thay đổi semantic observable.

---

# 25. Control-flow primitives

Core control flow:

```text
if
else
match
loop
while
for
break
continue
return
```

và:

```text
defer
```

không nên trở thành primitive riêng nếu Drop đã giải quyết deterministic cleanup.

Axiom ưu tiên:

> resource cleanup bằng ownership + Drop, không bằng hidden control-flow cleanup mechanism.

---

# 26. `break` / `continue`

Loop:

```text
loop {
    if done {
        break value
    }

    continue
}
```

Có thể hỗ trợ loop result:

```text
let result = loop {
    ...
    break value
}
```

Điều này tránh nhiều temporary mutable state.

Compiler lower về CFG/MIR.

---

# 27. `never`

`never` là bottom type:

```text
fn abort() -> never
```

Một expression kiểu `never` có thể coerce vào mọi expected type trong control-flow context.

Ví dụ:

```text
let x: i32 =
    if condition {
        42
    } else {
        abort()
    }
```

---

# 28. Diverging functions

Compiler phải phân biệt:

```text
never return
```

với:

```text
return unit
```

Điều này ảnh hưởng:

```text
CFG
reachability
definite initialization
drop analysis
optimization
```

---

# 29. Unreachable code

Sau:

```text
abort()
```

block phía sau unreachable.

Verifier có thể loại khỏi normal-flow analysis.

Nhưng diagnostics có thể cảnh báo unreachable source code tùy lint policy.

---

# 30. Panic

Panic semantics phải thống nhất với runtime profile.

Có thể có:

```text
abort
unwind
custom
```

Nhưng source semantics:

> panic không phải ordinary recoverable return.

Recoverable failure dùng:

```text
Result<T, E>
```

---

# 31. `try` propagation

Axiom nên hỗ trợ syntax ngắn cho Result:

```text
let x = foo()?
```

semantic tương đương:

```text
match foo() {
    Ok(v) => v,
    Err(e) => return Err(e)
}
```

Không tạo exception machinery.

Compiler lowering trực tiếp về CFG.

---

# 32. Calls với ownership

Ví dụ:

```text
fn consume(x: Buffer) { ... }

let b = Buffer(...)
consume(b)
```

Sau call:

```text
b == MOVED
```

Nếu:

```text
consume(b)
use(b)
```

→ compile error.

Với:

```text
fn inspect(x: view<Buffer>) { ... }
```

compiler tạo ephemeral read capability.

---

# 33. Mutable calls

```text
fn modify(x: mut_view<Buffer>) { ... }

modify(buffer)
```

Compiler:

1. tạo mutable capability;
2. kiểm tra không có conflicting capability;
3. call;
4. kết thúc capability.

Không cần programmer viết `&mut`.

---

# 34. Call graph

Compiler phải xây:

```text
CallGraph
```

với edge kinds:

```text
Direct
Generic
Specialized
Virtual
FunctionPointer
Closure
Foreign
IndirectUnknown
AsyncSpawn
GpuLaunch
```

Call graph phục vụ:

- effect analysis;
- escape analysis;
- ownership;
- inlining;
- devirtualization;
- LTO;
- PGO;
- dead-code elimination;
- stack analysis.

---

# 35. Indirect calls

Với:

```text
fn(i32) -> i32
```

compiler phải track function set khi có thể.

Ví dụ:

```text
let f = add
f(x)
```

có thể devirtualize thành direct call.

Nếu tập target không xác định:

```text
IndirectUnknown
```

và optimizer phải conservative.

---

# 36. Dynamic dispatch

```text
dyn Trait
```

là explicit.

Compiler tạo representation kiểu:

```text
data pointer
vtable pointer
```

chỉ khi ABI yêu cầu.

Không có hidden object header.

---

# 37. Call effects và async

Một `async fn`:

```text
async fn fetch(...) -> Result<Data, Error>
```

**không phải ordinary function returning Data**.

Nó tạo:

```text
Future<Result<Data, Error>>
```

Call graph phải ghi:

```text
AsyncCall
```

và `.await` tạo:

```text
SuspensionPointId
```

đã được định nghĩa trong async model.

---

# 38. GPU function call

`@kernel` không phải ordinary CPU function.

Call:

```text
launch kernel(...)
```

phải tạo:

```text
GpuLaunch
```

thay vì CPU Call.

Compiler phải giữ execution/storage domain information.

---

# 39. FFI calls

FFI call:

```text
extern "C" fn foo(...)
```

là:

```text
ForeignCall
```

Compiler không tự động inline/alias-analyze/constant-fold nếu không có contract.

Nếu FFI metadata cung cấp:

```text
readonly
noalias
pure
nothrow
```

thì compiler có thể sử dụng **chỉ sau khi contract được xác minh/được đánh dấu trusted theo FFI rules**.

---

# 40. ABI lowering

Pipeline:

```text
Typed HIR
    ↓
MIR Function
    ↓
Semantic Optimization
    ↓
Generic Specialization
    ↓
Closure Conversion
    ↓
Async/GPU/FFI Lowering
    ↓
ABI Classification
    ↓
ABI MIR
    ↓
LIR
```

ABI classification quyết định:

```text
register
stack
indirect
sret
split aggregate
vector register
return register
calling sequence
```

---

# 41. Calling conventions

Core nên có:

```text
axiom
```

là default Axiom ABI.

Ngoài ra:

```text
"C"
"system"
"stdcall"
"fastcall"
"vectorcall"
"platform"
```

chỉ khi target yêu cầu.

Không đưa hàng chục calling conventions thành language semantics nếu compiler backend có thể encapsulate chúng.

---

# 42. Function attributes

Các attribute có semantic hoặc optimization contract:

```text
@inline
@noinline
@cold
@hot
@must_tail
@noalloc
@pure
@unsafe
@extern
@export
@import
@kernel
@comptime
```

Phải phân loại rõ:

```text
Semantic Contract
Optimization Hint
ABI Contract
Tooling Metadata
```

Compiler không được coi tất cả attribute như cùng một loại.

---

# 43. CompilerDB additions

Thêm:

```text
FunctionDB
FunctionSignatureDB
CallGraphDB
CallSiteDB
CallingConventionDB
AbiFunctionDB
ClosureDB
ClosureCaptureDB
FunctionEffectDB
FunctionSpecializationDB
FunctionPointerDB
IndirectCallDB
TailCallDB
InlineDB
ControlFlowDB
DivergenceDB
PanicDB
ForeignCallDB
KernelCallDB
```

---

# 44. MIR additions

MIR cần chuẩn hóa các operation:

```text
CALL
TAIL_CALL
RETURN
INVOKE
PANIC
UNREACHABLE
MAKE_CLOSURE
CALL_INDIRECT
CALL_FOREIGN
CALL_GPU
```

`CALL` phải chứa:

```text
callee
arguments
destination
effect summary
calling convention
```

---

# 45. Call verifier

Trước khi optimization:

```text
Verified MIR
```

phải chứng minh:

- argument types đúng;
- ownership đúng;
- moved values không được dùng;
- capability hợp lệ;
- mutable access không conflict;
- return type đúng;
- unsafe contract đúng;
- async suspension rules đúng;
- GPU legality đúng;
- FFI ABI đúng;
- closure captures còn sống;
- Drop ordering đúng;
- no invalid control-flow edge.

---

# 46. Invariants

```text id="1o4x6u"
AFUNC-01
Function is the fundamental behavior unit.

AFUNC-02
Methods are syntax sugar over functions.

AFUNC-03
Argument evaluation order is deterministic.

AFUNC-04
Return semantics are deterministic.

AFUNC-05
Returning a value does not imply heap allocation.

AFUNC-06
Physical parameter passing is an ABI concern.

AFUNC-07
Physical return representation is an ABI concern.

AFUNC-08
Ownership semantics are preserved across calls.

AFUNC-09
View capabilities are checked at call boundaries.

AFUNC-10
Mutable capability conflicts are compile-time errors in safe code.

AFUNC-11
Function effects are compiler-analyzable.

AFUNC-12
Unsafe functions do not disable all compiler verification.

AFUNC-13
FFI calls are conservatively modeled unless an explicit contract exists.

AFUNC-14
Generic dispatch is static by default.

AFUNC-15
Dynamic dispatch is explicit.

AFUNC-16
Closure environments obey ownership/capability rules.

AFUNC-17
Closure conversion is compiler-internal.

AFUNC-18
Function pointers are first-class values.

AFUNC-19
Indirect calls are tracked in the call graph.

AFUNC-20
Tail-call optimization cannot alter semantics.

AFUNC-21
Explicit tail-call guarantees require compiler verification.

AFUNC-22
Inlining cannot alter language semantics.

AFUNC-23
Never-returning functions participate in type and CFG analysis.

AFUNC-24
Panic is distinct from recoverable Result failure.

AFUNC-25
Async calls are distinct from ordinary synchronous calls.

AFUNC-26
GPU launches are distinct from CPU calls.

AFUNC-27
ABI lowering occurs after semantic verification.

AFUNC-28
Calling convention is explicit at ABI boundaries.

AFUNC-29
Function identity, generic identity and generated code identity are distinct.

AFUNC-30
All optimized calls must originate from Verified MIR.
```

---

## 47. Definition of Done

`BOOTSTRAP-351` hoàn thành khi compiler có:

```text
Function semantic model
        ↓
Deterministic evaluation
        ↓
Ownership-aware calls
        ↓
Capability-aware calls
        ↓
Effect summaries
        ↓
Closure conversion
        ↓
Generic specialization
        ↓
Call graph
        ↓
Indirect call analysis
        ↓
Tail-call support
        ↓
Panic/never control flow
        ↓
ABI classification
        ↓
Native calling convention
        ↓
FFI calls
        ↓
Async/GPU call integration
```

và toàn bộ call semantics đều được kiểm chứng **trước optimization**.

Điểm quan trọng nhất của task này là khóa một nguyên tắc xuyên suốt Axiom:

> **Source function chỉ mô tả behavior và semantic contract. Nó không mô tả cách CPU phải gọi function.**

Nhờ vậy compiler có toàn quyền biến cùng một function thành inline code, register call, tail call, specialized generic, closure-converted function, coroutine state machine hoặc GPU kernel mà không buộc programmer phải viết code theo ABI/memory layout cụ thể.