# BOOTSTRAP-357 — AXIOM FUNCTION, CALLING CONVENTION & CALL SEMANTICS ENGINE

Sau Expression/Operator và Closure/Capture, bước tiếp theo cần đóng băng **ngữ nghĩa của function và call**. Đây là điểm nối trực tiếp giữa ngôn ngữ cấp cao với ABI, ownership, capability, async, FFI và cuối cùng là machine code.

Mục tiêu:

> `foo(a, b)` phải có một semantic contract duy nhất từ source → HIR → MIR → ABI → machine code, nhưng programmer không phải quan tâm đến register, stack hay calling convention trong code thông thường.

---

## 1. Function là đơn vị behavior cơ bản

Axiom không dùng method/class làm đơn vị behavior chính.

Function là primitive:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Method chỉ là syntax sugar:

```text
fn length(self: Vec) -> usize
```

được gọi:

```text
v.length()
```

và semantic resolution biến thành:

```text
length(v)
```

---

# 2. Function identity

Tên function không phải identity cuối cùng.

Compiler dùng:

```text
FunctionId
DeclarationId
GenericInstanceId
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

có:

```text
FunctionId = F123
```

Nếu generic:

```text
fn add<T: Add>(a: T, b: T) -> T
```

thì mỗi specialization có:

```text
GenericInstanceId
```

nhưng vẫn liên kết về function template ban đầu.

---

# 3. Function signature

Signature gồm:

```text
FunctionSignature {
    params
    return_type
    generic_params
    where_constraints
    effects
    async
    unsafe
    comptime
    calling_abi
    visibility
}
```

Không chỉ có `(params) -> return`.

Ví dụ:

```text
unsafe fn read(p: *const u8) -> u8
```

khác semantic với:

```text
fn read(p: view<u8>) -> u8
```

dù machine-level representation có thể giống nhau.

---

# 4. Function body contract

Một function sau resolution phải có:

```text
Input ownership contract
Input capability contract
Return ownership contract
Effect contract
Panic contract
Concurrency contract
Execution domain
ABI
```

Ví dụ:

```text
fn sum(data: view<i32>) -> i32
```

compiler hiểu:

```text
READ(data)
NO_OWNERSHIP_TRANSFER(data)
NO_WRITE(data)
```

Không cần programmer viết annotation cho những thứ compiler tự chứng minh được.

---

# 5. Parameter modes

Axiom không dùng một hệ thống:

```text
T
&T
&mut T
T&&
```

phức tạp như C++/Rust.

Thay vào đó parameter semantic có:

```text
VALUE
VIEW
MUT_VIEW
```

Ví dụ:

```text
fn process(x: BigStruct)
```

→ ownership/value parameter.

```text
fn inspect(x: view<BigStruct>)
```

→ read capability.

```text
fn modify(x: mut_view<BigStruct>)
```

→ exclusive write capability.

---

# 6. Value parameter không đồng nghĩa physical copy

Ví dụ:

```text
fn consume(x: BigObject)
```

gọi:

```text
consume(obj)
```

có thể là:

```text
MOVE
```

không cần physical copy.

Nếu:

```text
T: Copy
```

thì semantic là copy.

Compiler backend quyết định:

```text
register
stack
memory
caller allocation
```

---

# 7. Implicit view argument

Với:

```text
fn sum(x: view<i32>) -> i32
```

có thể gọi:

```text
sum(array)
```

Compiler tự tạo ephemeral capability:

```text
array
  ↓
view(array)
  ↓
sum(...)
```

nhưng **không tạo escaping view**.

Nếu muốn lưu view:

```text
let v = view(array);
```

phải là explicit.

---

# 8. Mut-view argument

Ví dụ:

```text
fn sort(x: mut_view<i32>)
```

gọi:

```text
sort(array)
```

Compiler kiểm tra:

```text
WRITE(array)
```

và đảm bảo không có conflicting capability trong lifetime call.

Ví dụ:

```text
let r = view(array);
sort(array);
use(r);
```

có thể bị reject nếu `r` vẫn live trong thời gian mutation.

---

# 9. Call expression semantics

Một call:

```text
foo(a, b)
```

semantic sequence:

```text
1. Resolve callable
2. Evaluate receiver if method
3. Evaluate arguments left-to-right
4. Materialize required temporaries
5. Perform required moves/copies
6. Create ephemeral capabilities
7. Enter call
8. Receive return value
9. End ephemeral argument capabilities
```

Điều này phải được định nghĩa trước MIR.

---

# 10. Argument evaluation

Axiom cố định:

> Arguments được evaluate từ trái sang phải.

Ví dụ:

```text
foo(a(), b(), c())
```

luôn:

```text
a()
→ b()
→ c()
→ foo
```

Điều này cũng áp dụng cho method:

```text
obj.f(a(), b())
```

receiver `obj` được resolve/evaluate theo semantic order trước arguments.

---

# 11. No hidden evaluation duplication

Ví dụ:

```text
get_object().field(get_index())
```

Compiler không được vô tình evaluate:

```text
get_object()
```

hai lần.

AST/HIR phải giữ expression identity.

---

# 12. Return semantics

```text
fn make() -> BigObject
```

không mặc định:

```text
heap allocate
copy object
return pointer
```

Compiler có thể sử dụng:

```text
register return
caller-allocated return
hidden return slot
move elision
NRVO-like optimization
```

nhưng semantic vẫn là:

```text
return ownership transfer
```

---

# 13. Return view

Function có thể trả:

```text
fn first(x: view<i32>) -> view<i32>
```

nhưng compiler phải chứng minh returned view có provenance hợp lệ.

Không được:

```text
fn bad() -> view<i32> {
    let local = ...
    return view(local)
}
```

vì owner chết khi function kết thúc.

Diagnostic phải chỉ ra provenance:

```text
returned view originates from local storage
local storage ends at function return
```

---

# 14. Return mut_view

Tương tự:

```text
fn slice(x: mut_view<i32>) -> mut_view<i32>
```

có thể hợp lệ nếu returned capability vẫn thuộc vùng storage hợp lệ.

Compiler không cho phép escape vượt owner lifetime.

---

# 15. Multiple return values

Axiom hỗ trợ tuple return:

```text
fn divide(a: i32, b: i32) -> (i32, i32)
```

Backend có thể:

```text
return registers
```

hoặc caller return area.

Không cần object allocation.

---

# 16. Struct return

```text
fn make_point() -> Point
```

semantic là value return.

Compiler có thể:

```text
return registers
```

nếu nhỏ.

Hoặc:

```text
caller_allocated_return
```

nếu lớn.

Không có rule source-level buộc programmer phải dùng pointer output parameter như C.

---

# 17. Function effects

Function effect summary:

```text
EffectSet {
    Read
    Write
    Allocate
    Deallocate
    Drop
    Atomic
    Volatile
    IO
    Panic
    Synchronize
    Foreign
    Suspend
    GPU
}
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

có thể:

```text
Pure
```

Trong khi:

```text
fn write_file(...)
```

có:

```text
IO
```

Function effect được compiler dùng cho:

- optimization;
- parallelization;
- constexpr/comptime;
- GPU legality;
- async;
- purity reasoning;
- diagnostics.

---

# 18. Pure không phải programmer annotation bắt buộc

Compiler có thể suy ra:

```text
Pure
```

từ body.

Không bắt programmer phải viết:

```text
@pure
```

trừ khi sau này cần một contract mạnh hơn.

Triết lý:

> **Compiler inference trước, annotation khi semantics cần một guarantee mà inference không thể suy ra.**

---

# 19. Unsafe function

```text
unsafe fn read_memory(...)
```

gọi từ safe code:

```text
read_memory(...)
```

phải nằm trong:

```text
unsafe {
    read_memory(...)
}
```

hoặc một context đã có unsafe permission.

Unsafe là property của callable contract.

---

# 20. Comptime function

```text
comptime fn factorial(n: u32) -> u32
```

chỉ có thể được evaluate trong comptime context.

Không được gọi runtime như function bình thường.

Ngược lại, một function ordinary có thể được compiler constant-fold khi đủ điều kiện, nhưng điều đó không biến nó thành `comptime fn`.

---

# 21. Async function

```text
async fn fetch() -> Result<Data, Error>
```

không trực tiếp trả `Result`.

Semantic return type của source-level function là:

```text
Future<Result<Data, Error>>
```

hoặc equivalent compiler-generated future type.

Call:

```text
let f = fetch();
```

không chạy toàn bộ function.

Chỉ khi:

```text
await f
```

execution mới tiến đến suspension/resume semantics.

---

# 22. Async function ABI

Async function không dùng ABI giống synchronous function một cách máy móc.

Compiler có thể tạo:

```text
fn fetch(...) -> FutureState
```

hoặc:

```text
fn fetch(...) -> opaque_future
```

tùy lowering.

Future state vẫn phải obey:

```text
ownership
capability
Send
Share
Drop
```

---

# 23. Generic function call

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

call:

```text
max(a, b)
```

Expression resolver tạo:

```text
GenericInstance {
    function = max
    T = TypeOf(a)
}
```

Sau đó TraitDB chứng minh:

```text
T : Ord
```

Generic inference hoàn thành trước MIR.

---

# 24. Generic code sharing

Axiom không bắt buộc mọi generic phải monomorphize.

Compiler có thể chọn:

```text
Monomorphization
Code sharing
Partial specialization
Devirtualized shared body
```

theo:

```text
size
performance
optimization opportunity
ABI
target
LTO
```

Semantic không thay đổi.

---

# 25. Calling convention

Axiom phải có một abstraction layer:

```text
Axiom ABI
```

sau đó lower sang:

```text
x86_64 SysV
x86_64 Windows
ARM64
ARM64 Apple
RISC-V
WASM
GPU ABI
C ABI
...
```

Source code không trực tiếp phụ thuộc register convention.

---

# 26. ABI classification

Mỗi parameter/return được ABI classifier phân loại:

```text
Scalar
Pair
Vector
Aggregate
Indirect
Reference-like ABI representation
Opaque
```

Ví dụ:

```text
struct Vec2 {
    x: f32,
    y: f32
}
```

có thể truyền bằng:

```text
register pair
```

thay vì stack.

---

# 27. Semantic type ≠ ABI type

Đây là invariant quan trọng.

```text
view<T>
```

là semantic capability.

ABI có thể biểu diễn thành:

```text
(pointer, length)
```

nhưng programmer không được coi tuple này là semantic equivalent của `view<T>`.

Tương tự:

```text
mut_view<T>
```

có thể ABI là:

```text
(pointer, length)
```

nhưng compiler vẫn phải giữ:

```text
WRITE capability
provenance
lifetime
alias constraints
```

---

# 28. ABI lowering chỉ xảy ra sau verification

Pipeline:

```text
Typed HIR
   ↓
MIR
   ↓
Ownership / Capability Verification
   ↓
Semantic Optimization
   ↓
Representation Lowering
   ↓
ABI Classification
   ↓
ABI MIR
```

Không được đưa ABI representation ngược lên để thay đổi semantic ownership.

---

# 29. Tail calls

Compiler có thể tối ưu:

```text
return f(x)
```

thành tail call nếu ABI/target cho phép.

Nhưng source semantics không được phụ thuộc vào tail-call availability.

Debug information phải vẫn mô tả call stack hợp lý theo debug mode.

---

# 30. Inlining

Inlining là optimization, không phải language semantics.

```text
foo(x)
```

có thể trở thành:

```text
inline foo body
```

hoặc giữ nguyên call.

Không được để programmer phụ thuộc vào việc compiler inline.

---

# 31. Function address

Function có thể được lấy address:

```text
let p = address_of_function(foo);
```

nếu syntax/API hệ thống cho phép.

Khi function address observable, compiler không được loại bỏ function implementation nếu còn cần externally.

Dynamic loading/hot reload có contract riêng.

---

# 32. Function pointer

Function pointer là **code capability**, không phải data pointer.

Ví dụ:

```text
fn(i32) -> i32
```

có ABI riêng.

Không cho phép implicit:

```text
fn pointer ↔ data pointer
```

và không cho phép:

```text
integer → function pointer
```

trong safe code.

---

# 33. Closure call integration

Closure call:

```text
f(x)
```

có thể resolve thành:

```text
StaticClosureCall
FunctionPointerCall
DynamicCallableCall
```

Compiler phải quyết định tại semantic resolution.

Không để backend tự suy đoán.

---

# 34. Method call integration

```text
obj.method(x)
```

sau resolution phải biến thành một trong:

```text
DirectFunctionCall
GenericFunctionCall
TraitMethodCall
DynamicMethodCall
ExtensionFunctionCall
```

Không còn khái niệm "method lookup" khi MIR được tạo.

---

# 35. Recursive calls

Function có thể gọi chính nó:

```text
fn factorial(n: u32) -> u32 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Recursive call là direct call semantic.

Compiler có thể:

- inline một số recursion;
- transform tail recursion;
- specialize;
- hoặc giữ nguyên.

Không có implicit heap frame.

---

# 36. Stack semantics

Axiom không định nghĩa:

> "Mọi function call đều tạo stack frame."

Đó là implementation detail.

Compiler có thể:

```text
register-only
inline
stack frame
caller frame
tail call
continuation
```

miễn observable semantics không đổi.

Điều này rất quan trọng để tránh ngôn ngữ tự giới hạn optimizer.

---

# 37. Reentrancy

Ordinary function không mặc định cấm reentrancy.

Nếu function sử dụng:

```text
global mutable state
```

compiler effect system phải thấy:

```text
Write(Global)
```

và concurrency verifier xử lý synchronization nếu cần.

Function call không tự động tạo lock.

---

# 38. FFI calls

FFI function là function với ABI explicit:

```text
extern "C" fn puts(s: *const u8) -> i32
```

Semantic contract phải chứa:

```text
ABI = C
unsafe = true/false
foreign = true
```

FFI không được hưởng các assumption của Axiom safe semantics nếu contract không chứng minh được.

---

# 39. No hidden exception ABI

Axiom Core không có C++-style hidden exception propagation.

Function:

```text
fn foo() -> Result<T, E>
```

là explicit control flow.

Không có hidden:

```text
exception object
unwind table
catch mechanism
```

trừ khi program/profile thực sự yêu cầu panic/unwind runtime.

---

# 40. Panic semantics

Function có thể có:

```text
Panic
```

effect.

Profile có thể chọn:

```text
abort
unwind
custom
```

Nhưng source semantics vẫn xác định điểm panic có thể xảy ra.

Optimizer không được loại bỏ observable panic chỉ vì return value không dùng.

---

# 41. Function contract artifact

`.axif` nên lưu được:

```text
FunctionSummary {
    FunctionId
    signature
    generic_constraints
    effects
    panic_behavior
    Send
    Share
    FfiSafe
    GpuLegal
    ABI
    semantic_fingerprint
}
```

Nhờ đó package khác có thể compile mà không cần reanalyze toàn bộ body.

---

# 42. Call-site proof

Mỗi call sau semantic resolution có:

```text
CallProof {
    target
    argument_types
    generic_substitution
    ownership_transfers
    capability_requirements
    effect_summary
    ABI_signature
}
```

Đây là cầu nối rất quan trọng giữa front-end và optimizer.

---

# 43. CompilerDB bổ sung

Task này thêm:

```text
FunctionDB
FunctionSignatureDB
FunctionBodyDB
FunctionContractDB
CallDB
CallResolutionDB
CallProofDB
ReturnDB
ParameterDB
AbiSignatureDB
AbiClassifierDB
FunctionEffectDB
FunctionPointerDB
RecursiveCallDB
TailCallDB
FfiCallDB
AsyncCallDB
```

Các query chính:

```text
resolve_function(FunctionId)
resolve_call(CallId)
function_signature(FunctionId)
function_effects(FunctionId)
function_contract(FunctionId)
classify_abi(FunctionId)
classify_parameter(FunctionId, ParameterId)
classify_return(FunctionId)
call_proof(CallId)
```

---

# 44. HIR representation

```text
HirFunction {
    function_id
    signature
    body
    contracts
}
```

Call:

```text
HirCall {
    target
    args
    generic_args
    dispatch_kind
    call_proof
}
```

`dispatch_kind`:

```text
Direct
Generic
Closure
FunctionPointer
Dynamic
FFI
Intrinsic
```

---

# 45. MIR representation

Sau lowering:

```text
CALL {
    target
    args
    destination
    call_kind
    effects
}
```

MIR không còn phải hỏi:

> Function nào?

> Generic T là gì?

> Có cần move không?

> Capability nào cần?

Các quyết định đó đã được resolved.

---

# 46. Invariants

Đóng băng:

```text
AFN-01  Every function has a stable FunctionId.

AFN-02  Every resolved call has exactly one semantic target.

AFN-03  Call resolution is deterministic.

AFN-04  Function signatures include semantic contracts beyond parameter types.

AFN-05  Argument evaluation is left-to-right.

AFN-06  Argument expressions are never implicitly evaluated more than once.

AFN-07  Value parameters obey Copy/Move semantics.

AFN-08  View parameters create only valid ephemeral capabilities.

AFN-09  Mut-view parameters require exclusive write capability.

AFN-10  Returned views must preserve valid provenance.

AFN-11  A function cannot return a capability to dead local storage.

AFN-12  Return values do not imply heap allocation.

AFN-13  Aggregate return uses target-selected ABI lowering.

AFN-14  Semantic type is distinct from ABI representation.

AFN-15  ABI lowering occurs after semantic verification.

AFN-16  Static calls do not imply dynamic dispatch.

AFN-17  Dynamic dispatch must be explicitly represented.

AFN-18  Closure calls preserve closure capture semantics.

AFN-19  Function pointers are distinct from data pointers.

AFN-20  Unsafe functions require an unsafe calling context.

AFN-21  Comptime functions cannot be called as ordinary runtime functions.

AFN-22  Async functions produce Future semantics.

AFN-23  Async calls do not imply spawning.

AFN-24  Generic calls are resolved before MIR lowering.

AFN-25  Generic specialization cannot alter language semantics.

AFN-26  FFI calls require an explicit ABI contract.

AFN-27  Foreign calls are conservatively modeled for effects.

AFN-28  Hidden exception propagation is not part of Core function semantics.

AFN-29  Panic behavior is represented explicitly in function effects/contracts.

AFN-30  Optimization may transform calls only while preserving the resolved call contract.
```

---

## 47. Kết quả kiến trúc

Sau BOOTSTRAP-357, compiler đã có chuỗi semantic khá hoàn chỉnh:

```text
Name
  ↓
Type
  ↓
Trait
  ↓
Expression
  ↓
Closure
  ↓
Function / Call
  ↓
Typed HIR
```

Từ đây các abstraction lớn như:

```text
async/await
pattern lowering
defer/drop
generics
FFI
GPU kernel
concurrency
```

đều có một nền tảng call semantics thống nhất.

Đặc biệt, **ABI đã được tách khỏi semantic function**. Đây là điều rất quan trọng đối với mục tiêu của Axiom: cùng một source function có thể được compiler biến thành register call, stack call, SIMD call, GPU call hoặc FFI call mà không cần thay đổi semantics của ngôn ngữ.