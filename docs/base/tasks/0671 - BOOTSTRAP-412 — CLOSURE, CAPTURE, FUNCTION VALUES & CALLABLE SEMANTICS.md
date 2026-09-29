# BOOTSTRAP-412 — CLOSURE, CAPTURE, FUNCTION VALUES & CALLABLE SEMANTICS

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 409 Type System + 410 Trait/Method Resolution + 411 Ownership/Capability/Effect

Mục tiêu của 412 là xác định hoàn chỉnh cách Axiom xử lý:

- function value;
- closure/lambda;
- capture;
- nested function;
- callback;
- function pointer;
- callable struct;
- generic callable;
- `Fn`/`FnMut`/`FnOnce` tương đương;
- conversion giữa callable forms;
- storage và ABI;
- interaction với async/thread/GPU.

Nguyên tắc trung tâm:

> **Closure là một value có behavior; compiler biến capture thành dữ liệu và function pointer/code pointer khi cần. Không có closure runtime bắt buộc hay heap allocation bắt buộc.**

---

# 412.1. Function là first-class value

Axiom cho phép function được sử dụng như value:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

let f = add

let x = f(1, 2)
```

Type semantic:

```text
fn(i32, i32) -> i32
```

Function value không đồng nghĩa với:

```text
closure object
```

Function không capture state có thể được biểu diễn cực kỳ nhỏ, thậm chí chỉ là code address.

---

# 412.2. Function Type

Function type gồm:

```text
FunctionType {
    Parameters
    ReturnType
    CallingConvention
    EffectSet
    Safety
    Asyncness
}
```

Ví dụ:

```text
fn(i32) -> i32
```

khác semantic với:

```text
async fn(i32) -> i32
```

và:

```text
unsafe fn(i32) -> i32
```

nếu các semantic contracts khác nhau.

ABI không làm thay đổi type identity trực tiếp nhưng được gắn trong function declaration/call boundary.

---

# 412.3. Closure

Ví dụ:

```axiom
let factor = 10

let f = |x| x * factor
```

Compiler tạo semantic closure:

```text
Closure {
    Code = generated_function
    Environment = { factor }
}
```

Conceptually:

```text
f
├── code
└── factor
```

Không yêu cầu runtime class/object.

---

# 412.4. Closure không bắt buộc heap allocation

Compiler được phép:

```text
REGISTER
STACK
INLINE
STATIC
HEAP
```

tùy escape analysis.

Ví dụ:

```axiom
fn compute(x: i32) -> i32 {
    let f = |y| y + x
    f(10)
}
```

Closure có thể được inline hoàn toàn:

```text
result = x + 10
```

Không còn closure object trong machine code.

---

# 412.5. Capture được compiler suy luận

Programmer viết:

```axiom
let x = 10

let f = || x + 1
```

Compiler xác định:

```text
capture(x)
access = READ
```

Nếu:

```axiom
let f = || {
    x = x + 1
}
```

thì:

```text
capture(x)
access = WRITE
```

Nếu closure cần ownership:

```axiom
let f = || consume(x)
```

compiler có thể xác định:

```text
capture(x)
access = MOVE
```

nếu call semantics thực sự consume `x`.

---

# 412.6. Capture Modes

Internal capture modes:

```text
READ
WRITE
MOVE
```

Tương ứng với semantic capability.

Không cần expose syntax kiểu:

```text
[&x]
[&mut x]
[x]
```

trừ khi sau này cần một explicit escape hatch.

Axiom ưu tiên:

```text
compiler inference
```

thay vì bắt programmer mô tả implementation detail.

---

# 412.7. Capture theo field

Compiler phải field-sensitive.

```axiom
struct State {
    position: Vec3
    velocity: Vec3
}

let state = State(...)

let f = || state.position.x
```

Không nhất thiết closure cần toàn bộ `state`.

Compiler có thể capture:

```text
state.position.x
```

hoặc representation tương đương.

Điều này giúp giảm:

- capture size;
- register pressure;
- copy;
- memory traffic.

---

# 412.8. Capture và ownership

Closure không được phá ownership model.

Ví dụ:

```axiom
let file = open(...)

let f = || file.read()
```

Nếu `f` chỉ sống trong scope:

```text
file
 ↓
READ capture
 ↓
closure call
 ↓
closure destroyed
 ↓
file remains valid
```

Compiler có thể tạo ephemeral view.

---

# 412.9. Escaping Closure

Nếu:

```axiom
fn make() -> ??? {
    let x = Data(...)
    return || use(x)
}
```

closure escaping scope phải mang theo ownership phù hợp.

Compiler có thể chuyển:

```text
x
```

vào closure environment.

Semantic:

```text
x ownership
      ↓
closure environment ownership
```

Không phải dangling reference.

Nếu không thể transfer ownership hợp lệ:

```text
→ compile error
```

---

# 412.10. Closure Environment

Mỗi closure type là một compiler-generated anonymous type:

```text
ClosureTypeId
```

Ví dụ:

```text
Closure#42 {
    captured_x: i32
    captured_buffer: Buffer
}
```

Nhưng anonymous type này không nhất thiết được expose cho source-level programmer.

Compiler vẫn có thể:

- layout;
- optimize;
- specialize;
- debug;
- inspect qua semantic API.

---

# 412.11. Closure không dùng class

Closure không tạo:

```text
class Closure42
```

theo mô hình OOP.

Nó là:

```text
anonymous struct
+
generated call function
```

Conceptually:

```axiom
struct Closure42 {
    x: i32
}

fn Closure42_call(self: view<Closure42>, y: i32) -> i32 {
    self.x + y
}
```

`f(y)` chỉ là syntactic sugar cho callable operation.

---

# 412.12. Callable Protocol

Axiom định nghĩa một callable protocol/compiler trait.

Conceptually:

```text
trait Call<Args> {
    type Output
    fn call(self, args: Args) -> Output
}
```

Nhưng compiler có thể treat call syntax specially để tránh overhead.

```axiom
f(x)
```

được resolve thành callable operation.

---

# 412.13. Function vs Closure

Một function không capture:

```axiom
fn square(x: i32) -> i32
```

có thể convert thành:

```text
fn(i32) -> i32
```

mà không cần environment.

Closure:

```axiom
|x| x * factor
```

có environment.

Do đó compiler phân biệt:

```text
FunctionPointer
ClosureValue
CallableObject
```

ở representation level.

---

# 412.14. Không ép mọi callable thành fat object

Nếu code:

```axiom
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}
```

compiler có thể dùng:

```text
code pointer
```

Nếu generic:

```axiom
fn apply<F>(f: F, x: i32) -> i32
where F: Callable(i32)
```

compiler mặc định monomorphize:

```text
apply<Closure42>
```

và biết chính xác implementation.

→ có thể inline.

---

# 412.15. Static Dispatch mặc định

Generic callable:

```axiom
fn map<F>(x: i32, f: F) -> i32
```

với:

```text
F: Callable
```

mặc định:

```text
static dispatch
```

Không tạo vtable.

Đây là lựa chọn quan trọng cho hiệu năng.

---

# 412.16. Dynamic Callable

Nếu programmer thực sự cần runtime-selected callable:

```text
dyn Callable(...)
```

compiler có thể dùng:

```text
data pointer
+
dispatch pointer
```

Dynamic dispatch là explicit.

Không có:

```text
"compiler thấy closure khác type nên tự động box/vtable"
```

trong semantic Core.

---

# 412.17. Callable Categories

Axiom định nghĩa ba semantic callable capabilities:

```text
CALL_READ
CALL_WRITE
CALL_MOVE
```

Conceptually tương ứng:

```text
Fn
FnMut
FnOnce
```

nhưng Axiom không nhất thiết phải expose ba trait này dưới đúng tên đó.

Ví dụ:

```text
Callable<R>
MutableCallable<R>
ConsumingCallable<R>
```

Điểm quan trọng là compiler phân biệt:

```text
call không consume
call có thể mutate environment
call consume environment
```

---

# 412.18. Read Callable

Ví dụ:

```axiom
let x = 10

let f = || x + 1
```

Có thể gọi nhiều lần:

```axiom
f()
f()
f()
```

Environment chỉ READ.

---

# 412.19. Mutable Callable

Ví dụ:

```axiom
let counter = 0

let f = || {
    counter += 1
    counter
}
```

Closure environment có mutable state.

Compiler semantic model:

```text
closure
  owns/mutably captures
      ↓
counter
```

Nếu callable được truyền vào function khác, capability phải phù hợp.

---

# 412.20. Consuming Callable

Ví dụ:

```axiom
let buffer = Buffer(...)

let f = || consume(buffer)
```

Nếu invocation chuyển ownership của capture:

```text
first call:
    valid

second call:
    compile error
```

trừ khi closure tạo một clone/new ownership.

---

# 412.21. Call State Machine

Closure có consuming behavior phải có semantic state:

```text
READY
CONSUMED
```

Compiler theo dõi:

```text
f()
```

→

```text
f = CONSUMED
```

Nếu closure environment chứa Drop-bearing values, chúng được drop đúng lúc.

---

# 412.22. Closure + Drop

Ví dụ:

```axiom
let file = open(...)
let f = || file.read()
```

Nếu closure sở hữu `file`, khi closure bị destroy:

```text
closure
 ↓
drop captured file
```

Compiler phải đảm bảo không:

- double-drop;
- leak;
- use-after-move.

---

# 412.23. Closure + async

Đây là boundary quan trọng.

```axiom
let x = Data(...)

let task = async || {
    await io()
    use(x)
}
```

Compiler phải phân tích:

```text
capture(x)
+
suspension
+
task lifetime
```

Nếu task có thể sống lâu hơn current scope:

```text
x
```

phải được promote/move vào coroutine state.

---

# 412.24. Closure + Thread

```axiom
let x = Data(...)

spawn(|| use(x))
```

Compiler xác định:

```text
closure escapes thread
```

→ yêu cầu:

```text
Send<Closure>
```

hoặc tương đương.

Nếu `x` không thể transfer:

```text
compile error
```

Không cần programmer viết lifetime.

---

# 412.25. Closure + GPU

Closure arbitrary không được mặc định chạy GPU.

GPU kernel có execution-domain rules riêng.

Ví dụ:

```text
@kernel
fn process(...)
```

phải satisfy GPU legality.

Compiler không cho:

```text
CPU closure
 ↓
implicit GPU execution
```

vì capture có thể chứa:

- host pointer;
- file;
- mutex;
- OS resource;
- arbitrary heap object.

Nếu GPU closure được hỗ trợ sau này, nó phải có explicit `DeviceCallable`/kernel-safe contract.

---

# 412.26. Nested Functions

Axiom hỗ trợ nested function:

```axiom
fn outer(x: i32) {
    fn inner(y: i32) -> i32 {
        y + 1
    }

    inner(x)
}
```

Nếu `inner` không capture:

```text
inner
```

có thể được compile như ordinary function.

Nếu capture outer variable:

```axiom
fn outer(x: i32) {
    fn inner(y: i32) -> i32 {
        x + y
    }
}
```

semantic model trở thành closure-like environment.

Compiler có thể thống nhất hai implementation.

---

# 412.27. Closure Type Identity

Hai closure expression:

```axiom
let f = |x| x + 1
let g = |x| x + 1
```

không mặc định cùng type.

Mỗi closure expression có:

```text
ClosureTypeId
```

riêng.

Điều này giúp compiler tránh structural equivalence phức tạp không cần thiết.

Chúng vẫn có thể cùng satisfy:

```text
Callable(i32) -> i32
```

---

# 412.28. Closure Conversion

Compiler có thể convert closure sang function representation nếu:

```text
capture set = empty
```

Ví dụ:

```axiom
let f = |x: i32| x + 1
```

→ ordinary function pointer là đủ.

Nếu có capture:

```text
environment + code
```

→ closure representation.

---

# 412.29. Closure Layout

Layout của closure là compiler-controlled.

Compiler có thể:

```text
reorder captures
pack fields
remove dead captures
scalarize
split environment
store in registers
```

miễn là semantic observable behavior không thay đổi.

Không có guarantee rằng:

```text
sizeof(closure)
```

ổn định trừ khi explicit representation contract được cung cấp.

---

# 412.30. Function ABI

Function ABI gồm:

```text
parameters
return convention
calling convention
register convention
stack convention
variadic state
exception/unwind state
```

Axiom ABI mặc định do compiler kiểm soát.

FFI:

```text
extern "C"
```

hoặc ABI tương ứng tạo explicit boundary.

---

# 412.31. Variadic Functions

Core có thể hỗ trợ variadic FFI:

```axiom
extern "C" fn printf(...)
```

nhưng **không coi variadic function là ordinary type-safe callable**.

Safe Axiom code nên dùng typed wrappers:

```text
format(...)
print(...)
```

Compiler biết đây là FFI boundary.

---

# 412.32. Generic Callable

Ví dụ:

```axiom
fn transform<T, F>(
    x: T,
    f: F
) -> F::Output
where
    F: Callable<T>
{
    f(x)
}
```

Compiler:

```text
T
F
 ↓
trait solving
 ↓
monomorphization
 ↓
specialized function
```

Không cần boxing.

---

# 412.33. Callable Trait Coherence

Callable protocol là compiler-known semantic protocol.

Programmer không được tạo implementation làm phá:

```text
f(x)
```

syntax.

Nếu custom callable types được cho phép, compiler phải kiểm tra:

```text
Callable implementation
+
coherence
+
receiver capability
+
argument types
```

giống các trait khác.

---

# 412.34. Partial Application / Function Binding

Axiom Core v1 **không cần currying tự động**.

Ví dụ:

```axiom
let f = add.bind(10)
```

nếu cần, đây là library/compiler-generated closure:

```text
closure {
    captured = 10
    call(y) = add(10, y)
}
```

Không cần thêm một primitive runtime.

---

# 412.35. Callback API

API native:

```axiom
fn for_each<T, F>(
    items: view<Array<T>>,
    f: F
)
where
    F: Callable<view<T>>
```

cho phép:

```axiom
for_each(items, |x| print(x))
```

Compiler có thể:

```text
inline callback
vectorize
parallelize
fuse
```

nếu semantic constraints cho phép.

Đây là cơ sở để Axiom có abstraction cao nhưng vẫn đạt zero-cost.

---

# 412.36. Closure + Parallelism

Nếu callback:

```axiom
parallel_for(items, |x| process(x))
```

compiler kiểm tra:

```text
capture capabilities
+
Send/Share
+
region disjointness
+
effect legality
```

Sau đó có thể tạo:

```text
thread partition
SIMD
GPU kernel
```

nếu API/annotations cho phép.

Closure vì thế trở thành một **semantic unit có thể được compiler transform**, chứ không chỉ là callback object.

---

# 412.37. Function Pointer Safety

Function pointer bình thường:

```text
fn(...) -> ...
```

không có capture.

Unsafe function pointer:

```text
unsafe fn(...) -> ...
```

không được tự động convert thành safe callable.

Ví dụ:

```text
unsafe fn dangerous(...)
```

không thể truyền vào API yêu cầu:

```text
safe callable
```

mà không có explicit unsafe boundary.

---

# 412.38. Effect của Callable

Callable type có thể mang effect contract.

Ví dụ conceptually:

```text
Callable<Input, Output, Effects>
```

Nếu API yêu cầu:

```text
PURE
```

thì callback:

```text
|x| write_file(x)
```

bị reject.

Điều này rất hữu ích cho:

- parallel execution;
- comptime;
- GPU;
- deterministic computation;
- query engine;
- optimizer.

---

# 412.39. Semantic Representation

Compiler IR nên thống nhất:

```text
FunctionValue {
    FunctionId
}

ClosureValue {
    ClosureTypeId
    Environment
}
```

và:

```text
CALL_DIRECT
CALL_INDIRECT
CALL_CLOSURE
CALL_DYNAMIC
```

Trong MIR.

Optimizer có thể hạ:

```text
CALL_CLOSURE
```

→

```text
CALL_DIRECT
```

sau khi specialize/inlining.

---

# 412.40. CompilerDB

Thêm:

```text
FunctionTypeDB
ClosureDB
CaptureDB
CallableDB
ClosureLayoutDB
ClosureEscapeDB
FunctionValueDB
CallTargetDB
CallableTraitDB
```

Compiler phải truy vấn được:

```text
closure captures
capture mode
capture provenance
escape state
call target
callable constraints
effect set
ownership requirements
```

---

# 412.41. Proof Artifacts

Các proof chính:

```text
ClosureCaptureProof
ClosureOwnershipProof
ClosureEscapeProof
ClosureDropProof
CallableResolutionProof
FunctionValueProof
CallableTraitProof
AsyncCaptureProof
ThreadCaptureProof
GPUCallableProof
CallTargetProof
```

Ví dụ:

```text
ClosureEscapeProof

closure:
    Closure#42

captures:
    x : Data

capture mode:
    MOVE

escape:
    thread spawn

required:
    Send<Data>

result:
    proven
```

---

# 412.42. Invariants `ACLOSURE`

```text
ACLOSURE-01  Every closure has stable compiler identity.
ACLOSURE-02  Closure type identity is expression-based.
ACLOSURE-03  Capture set is compiler-derived.
ACLOSURE-04  Capture mode is semantically verified.
ACLOSURE-05  READ capture requires valid read capability.
ACLOSURE-06  WRITE capture requires exclusive mutable capability.
ACLOSURE-07  MOVE capture transfers ownership exactly once.
ACLOSURE-08  Captured values cannot be double-dropped.
ACLOSURE-09  Captured values cannot become dangling.
ACLOSURE-10  Escaping closures require valid ownership.
ACLOSURE-11  Closure environment lifetime is compiler verified.
ACLOSURE-12  Closure allocation is not mandatory.
ACLOSURE-13  Closure layout is compiler controlled.
ACLOSURE-14  Empty closures may lower to function values.
ACLOSURE-15  Static callable dispatch is default.
ACLOSURE-16  Dynamic callable dispatch is explicit.
ACLOSURE-17  Callable effects are preserved.
ACLOSURE-18  Callable safety contracts are preserved.
ACLOSURE-19  Consuming callables cannot be reused after consumption.
ACLOSURE-20  Mutable callables require mutable capability.
ACLOSURE-21  Async captures survive suspension correctly.
ACLOSURE-22  Thread-crossing captures require Send semantics.
ACLOSURE-23  Shared captures require Share semantics.
ACLOSURE-24  GPU captures require device-safe semantics.
ACLOSURE-25  Function pointers do not implicitly acquire captures.
ACLOSURE-26  Unsafe function values cannot silently become safe values.
ACLOSURE-27  Generic callables participate in normal trait solving.
ACLOSURE-28  Closure transformations preserve semantics.
ACLOSURE-29  Unresolved callable targets cannot reach codegen.
ACLOSURE-30  Closure semantics are independent of optimization level.
```

---

# 412.43. Pipeline sau BOOTSTRAP-412

Semantic pipeline hiện trở thành:

```text
Source
 ↓
Parse
 ↓
Name Resolution
 ↓
Type Inference
 ↓
Trait Resolution
 ↓
Method / Overload Resolution
 ↓
Ownership / Capability / Effect Verification
 ↓
Closure & Capture Analysis
 ↓
Async / Thread / GPU Capture Verification
 ↓
Typed HIR
 ↓
MIR
```

Sau đó MIR có thể chứa:

```text
CALL_DIRECT
CALL_INDIRECT
CALL_CLOSURE
CALL_DYNAMIC
```

và optimizer có quyền biến:

```text
CALL_CLOSURE
        ↓
specialization
        ↓
inline
        ↓
CALL_DIRECT
```

hoặc thậm chí:

```text
CALL_CLOSURE
        ↓
constant propagation
        ↓
không còn call
```

---

## 412.44. Quyết định kiến trúc cuối

Axiom sẽ **không xây closure như một tính năng runtime nặng**.

Mô hình:

```text
Closure
=
Compiler-generated anonymous struct
+
Compiler-generated function
+
Inferred capture semantics
```

và:

```text
Function
=
Code identity

Closure
=
Code identity + Environment

dyn Callable
=
Explicit dynamic dispatch
```

Điều này cho phép cùng một abstraction:

```axiom
map(data, |x| x * 2)
```

được compiler biến thành:

```text
ordinary loop
```

hoặc:

```text
SIMD
```

hoặc:

```text
parallel loop
```

hoặc:

```text
GPU kernel
```

khi các semantic proof tương ứng tồn tại — **mà syntax của programmer không phải thay đổi chỉ vì backend thay đổi**.

**BOOTSTRAP-412 — SPECIFIED / FROZEN.**