Tiếp tục từ **ERROR/PANIC/UNWIND-001**, bước hợp lý tiếp theo là đóng băng **ABI-002 — Calling Convention & Return ABI**. Đây là lớp nối trực tiếp từ semantic MIR sang LIR/Machine IR, và quyết định Axiom có thực sự đạt được hiệu năng kiểu C/C++ hay không.

# ABI-002 — CALLING CONVENTION & RETURN ABI

## 1. Nguyên tắc nền tảng

Axiom phải tách rõ:

```text
Source-level type
        ↓
Semantic type
        ↓
ABI classification
        ↓
Physical locations
        ↓
Machine registers / stack
```

Một kiểu dữ liệu **không được mặc định có một ABI cố định chỉ vì representation của nó trông đơn giản**.

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

có thể được truyền:

```text
XMM0
```

hoặc:

```text
XMM0 + XMM1
```

hoặc:

```text
RDI/RAX
```

tùy target ABI.

Đó là trách nhiệm của:

```text
ABI Classifier
```

chứ không phải programmer.

---

# 2. ABI Classification

Mỗi argument/return value đi qua một bước:

```text
classify(type, ABI, target)
    ↓
ABIValueClass
    ↓
LocationPlan
```

Ví dụ:

```text
ABIValueClass =
    Integer
    Float
    Vector
    Aggregate
    Indirect
    Memory
    Void
```

Nhưng không nên dừng ở đó.

Nên có classification chi tiết hơn:

```text
Scalar
Integer
Float
Vector
AggregateRegister
AggregateMemory
Indirect
Split
Ignore
```

Ví dụ:

```text
u64
→ Integer

f64
→ Float

Vec2
→ AggregateRegister

LargeStruct
→ Indirect

unit
→ Ignore
```

---

# 3. Scalar arguments

Primitive types nên được truyền trực tiếp vào register theo target ABI.

Ví dụ conceptual:

```text
fn add(a: i64, b: i64) -> i64
```

có thể hạ thành:

```text
RDI = a
RSI = b

RAX = result
```

Axiom source code không cần biết điều này.

Không tạo:

```text
Box<i64>
```

không tạo object header.

Không heap allocate.

Không runtime call.

---

# 4. Float

Ví dụ:

```text
fn distance(a: f64, b: f64) -> f64
```

target ABI có thể dùng:

```text
XMM0
XMM1
→ XMM0
```

Axiom phải cho phép backend quyết định register class.

Đây là lý do LIR cần hiểu:

```text
IntegerRegisterClass
FloatRegisterClass
VectorRegisterClass
```

thay vì chỉ có một loại register.

---

# 5. Multi-register return

Đây là một điểm rất quan trọng.

Ví dụ:

```text
struct Pair {
    a: u64
    b: u64
}
```

và:

```text
fn make_pair() -> Pair
```

Axiom **không được ép mọi aggregate return qua memory**.

Trên target phù hợp:

```text
RAX = a
RDX = b
```

Caller nhận trực tiếp:

```text
Pair {
    a: RAX,
    b: RDX
}
```

Không cần:

```text
malloc
memcpy
free
```

Đây là một trong những điều quyết định hiệu năng aggregate-heavy code.

---

# 6. Small aggregate return

Đề xuất:

> Aggregate nhỏ phải được return bằng register nếu target ABI cho phép.

Ví dụ:

```text
struct Vec2 {
    x: f64
    y: f64
}
```

có thể:

```text
XMM0 = x
XMM1 = y
```

hoặc target có thể sử dụng một vector register.

Axiom semantic layer không được hard-code cách này.

---

# 7. Large aggregate return

Ví dụ:

```text
struct Big {
    a: u64
    b: u64
    c: u64
    d: u64
    e: u64
    f: u64
}
```

Thay vì:

```text
return Big
```

vật lý bằng hàng loạt register, ABI có thể dùng:

```text
sret
```

Conceptually:

```text
fn make_big(out: *mut Big)
```

Nhưng **source-level signature vẫn là**:

```text
fn make_big() -> Big
```

`sret` chỉ xuất hiện sau ABI lowering.

---

# 8. `sret` không phải allocation

Đây là điểm cần đóng băng.

```text
fn create() -> Big
```

không có nghĩa:

```text
heap allocate Big
```

Compiler có thể biến:

```text
let x = create()
```

thành:

```text
reserve caller-local storage for x
create(&mut x)
```

Conceptually:

```text
caller:
    allocate x
    call create(sret=&x)
```

Storage có thể là:

```text
register
stack
caller frame
inline aggregate
```

tùy optimizer.

### ABI invariant

**ABI-20 — Indirect Return Does Not Imply Heap Allocation**

---

# 9. Caller-allocated return

Axiom nên coi caller-allocated aggregate return là first-class.

Ví dụ:

```text
fn parse() -> LargeResult
```

có thể hạ:

```text
fn parse(sret: *mut LargeResult)
```

nhưng compiler phải đảm bảo:

```text
parse()
```

vẫn có value semantics.

Programmer không thấy pointer.

---

# 10. Argument aggregate

Tương tự return.

```text
fn consume(v: Vec4)
```

không mặc định phải:

```text
pass pointer
```

Nếu nhỏ:

```text
registers
```

Nếu lớn:

```text
stack
```

hoặc indirect ABI.

Ví dụ:

```text
struct Vec4 {
    a: f32
    b: f32
    c: f32
    d: f32
}
```

target có thể truyền bằng SIMD register.

---

# 11. `view<T>` ABI

Đây là abstraction rất quan trọng của Axiom.

Source:

```text
fn sum(v: view<i32>) -> i32
```

Semantic representation có thể tương đương:

```text
(pointer, length)
```

nhưng **đó không phải source-level pointer type**.

ABI classifier có thể biến thành:

```text
RDI = data
RSI = length
```

hoặc target-specific equivalent.

Không tạo:

```text
ViewObject
```

Không tạo heap.

Không runtime.

### Quan trọng

`view<T>` vẫn giữ semantic invariant:

```text
READ capability
+
provenance
+
validity
```

Sau khi verification hoàn tất, provenance metadata có thể biến mất khỏi runtime representation.

---

# 12. `mut_view<T>`

Ví dụ:

```text
fn fill(out: mut_view<u8>, value: u8)
```

ABI có thể là:

```text
RDI = data
RSI = length
RDX = value
```

Nhưng semantic verifier đã đảm bảo:

```text
mut_view
```

không xung đột với capability khác.

Runtime không cần mang theo:

```text
borrow flag
lock
reference count
lifetime object
```

Đây chính là:

> **Compiler-enforced safety, zero runtime bookkeeping.**

---

# 13. `Option<T>` ABI

Đây là nơi ABI và type system gặp nhau.

Ví dụ:

```text
Option<NonNull<T>>
```

có thể sử dụng niche:

```text
null = None
non-null = Some(ptr)
```

nhưng source-level:

```text
None
Some(x)
```

vẫn là algebraic semantics.

Compiler được phép tối ưu representation.

### Quy tắc

```text
Option<T>
```

có thể có:

```text
NormalTagRepresentation
NicheRepresentation
CompressedRepresentation
RegisterRepresentation
```

tùy:

```text
T
target
ABI
optimization
```

---

# 14. Niche optimization không được làm thay đổi semantics

Ví dụ:

```text
enum Option<T> {
    Some(T),
    None
}
```

không có nghĩa programmer được phép dựa vào:

```text
None == bit pattern 0
```

trừ khi ABI/repr explicit guarantee.

Do đó:

```text
representation optimization
≠
semantic representation guarantee
```

---

# 15. `Result<T,E>` ABI

Ví dụ:

```text
Result<u64, Error>
```

có thể được:

```text
RAX = value/error payload
RDX = discriminant
```

hoặc:

```text
RAX = packed representation
```

hoặc indirect.

Không được giả định một representation cố định.

Điều quan trọng:

```text
Result
```

không cần exception runtime.

---

# 16. `dyn Trait`

Đây là trường hợp đặc biệt.

Ví dụ:

```text
dyn Drawable
```

phải có dynamic dispatch metadata.

Conceptually:

```text
(data_pointer, vtable_pointer)
```

Nhưng:

```text
dyn Trait
```

**không phải ownership mechanism**.

Ví dụ:

```text
view<dyn Drawable>
```

không đồng nghĩa:

```text
Box<dyn Drawable>
```

Còn:

```text
Box<dyn Drawable>
```

có ownership.

Đây là ba tầng khác nhau:

```text
dyn Trait
    = dynamic dispatch representation

view<dyn Trait>
    = borrowed access

Box<dyn Trait>
    = owned dynamic storage
```

---

# 17. Closure ABI

Closure:

```text
let f = |x| x + captured;
```

semantic value chứa:

```text
code
+
capture environment
```

Compiler có thể lower thành:

```text
struct ClosureEnv {
    captured: T
}
```

và:

```text
fn invoke(env: *Env, x: i32) -> i32
```

Nhưng programmer không cần nhìn thấy `env`.

---

# 18. Closure không capture

Closure không capture:

```text
let f = |x: i32| x + 1;
```

có thể decay thành:

```text
fn(i32) -> i32
```

tức function pointer.

Không cần environment.

Không cần allocation.

---

# 19. Capturing closure không mặc định heap allocate

Ví dụ:

```text
fn foo() {
    let a = 10;

    let f = || a + 1;

    f();
}
```

Compiler có thể:

```text
inline
```

hoặc:

```text
SSA scalar
```

hoặc stack environment.

Không được ép closure lên heap chỉ vì nó là closure.

Heap chỉ cần nếu semantic escape/storage contract yêu cầu.

---

# 20. Function pointer ABI

Function pointer phải có ABI rõ ràng.

```text
fn(i32, i32) -> i32
```

không thể tùy tiện tương thích với:

```text
extern "C" fn(i32, i32) -> i32
```

Hai loại ABI khác nhau phải là hai semantic function types hoặc có conversion explicit.

Ví dụ:

```text
type AxiomFn = fn(i32) -> i32;
type CFn = extern "C" fn(i32) -> i32;
```

---

# 21. `extern "C"`

Ví dụ:

```text
extern "C" fn printf(...);
```

Axiom phải chuyển sang C ABI ở ABI lowering.

C ABI quyết định:

```text
registers
stack
alignment
aggregate passing
aggregate return
variadic arguments
name mangling
unwind
```

Không được để backend tự đoán.

---

# 22. Variadic functions

Ví dụ:

```text
extern "C" fn printf(format: *const u8, ...) -> i32;
```

Variadic ABI phải là target-specific.

Axiom không nên tạo:

```text
Array<Any>
```

để implement `...`.

Không được có implicit boxing.

Không runtime type object.

Caller phải tuân theo ABI của variadic foreign function.

---

# 23. Axiom variadic

Tôi đề xuất:

### Core v1

Không hỗ trợ arbitrary Axiom variadic functions.

Chỉ hỗ trợ:

```text
extern variadic
```

ở FFI boundary.

Sau này nếu cần:

```text
fn log(format: Format, args: ...)
```

nên được thiết kế bằng compile-time formatting/generic mechanism thay vì C-style untyped variadic.

Lý do:

```text
C variadic
```

làm mất type safety và tạo nhiều vấn đề ABI.

---

# 24. `async fn` ABI

`async fn` không thể đơn giản coi như:

```text
fn(...) -> Result
```

Nó tạo Future state machine.

Source:

```text
async fn fetch(x: Request) -> Result<Response, Error>
```

semantic:

```text
Future<Result<Response, Error>>
```

Compiler có thể lower thành:

```text
struct FetchFuture {
    state: ...
    x: Request
    ...
}
```

và:

```text
poll(self: mut_view<FetchFuture>, cx: &mut Context)
```

Conceptually.

Nhưng Future representation có thể được:

```text
stack allocated
embedded
optimized
boxed
```

tùy escape.

---

# 25. Async ABI không được heap-by-default

Ví dụ:

```text
async fn foo() -> i32
```

gọi:

```text
let f = foo();
let x = f.await;
```

không được bắt buộc:

```text
malloc(Future)
```

Compiler có thể đặt state machine trực tiếp vào caller frame.

Đây là rất quan trọng đối với hiệu năng async.

---

# 26. `spawn` mới có thể yêu cầu storage lâu dài

Ví dụ:

```text
spawn(foo());
```

scheduler cần giữ Future sau khi caller return.

Lúc đó:

```text
Future storage
```

có thể cần dynamic/pool/task storage.

Nhưng đó là semantic requirement của:

```text
spawn
```

không phải của:

```text
async fn
```

---

# 27. Panic ABI

Ở source:

```text
panic("bad state")
```

không quy định representation duy nhất.

Profile:

```text
panic=abort
```

có thể hạ:

```text
call axiom_panic
→ noreturn
```

Hoặc compiler inline trực tiếp:

```text
diagnostic/abort/trap
```

Nếu:

```text
panic=unwind
```

thì function có thể cần unwind metadata.

---

# 28. `no_unwind`

Ở FFI boundary cần ABI fact:

```text
may_unwind
no_unwind
```

Không nhất thiết biến thành user-facing effect system.

Ví dụ:

```text
extern "C" fn foo() noexcept
```

hoặc Axiom equivalent:

```text
extern "C" @no_unwind fn foo(...)
```

đây là ABI contract.

---

# 29. ABI lowering phải xảy ra trước Machine IR

Pipeline chính thức nên là:

```text
Verified MIR
    ↓
ABI Lowering
    ↓
ABI MIR
    ↓
Axiom LIR
    ↓
Target Legalization
    ↓
Machine IR
```

`Verified MIR` vẫn dùng semantic types:

```text
Vec<T>
Result<T,E>
view<T>
mut_view<T>
dyn Trait
Future<T>
```

Sau ABI lowering mới xuất hiện:

```text
physical argument locations
sret
split aggregate
register classes
stack arguments
return locations
hidden parameters
```

---

# 30. Hidden parameters

Compiler có thể thêm:

```text
sret
closure environment
vtable
generic metadata
context
```

nhưng phải phân biệt:

### Required runtime parameter

Ví dụ:

```text
closure env
vtable
sret
```

### Compile-time-only parameter

Ví dụ:

```text
T
const N
trait constraints
```

Sau monomorphization:

```text
T
N
constraints
```

có thể hoàn toàn biến mất.

Không được truyền generic metadata nếu static dispatch không cần.

---

# 31. Generic ABI

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

với:

```text
max<i32>
```

compiler biết:

```text
T = i32
```

sau monomorphization.

Machine code chỉ còn:

```text
i32
```

Không:

```text
TypeInfo*
VTable*
Box
```

trừ khi programmer sử dụng dynamic abstraction.

---

# 32. Dynamic generic metadata

Nếu sau này Axiom hỗ trợ abstraction cần runtime type metadata, nó phải xuất hiện explicit ở semantic layer.

Không được biến mọi generic thành:

```text
fat pointer
runtime TypeInfo
```

Đây là một trong những điểm giúp Axiom tránh overhead kiểu dynamic-language.

---

# 33. ABI ownership

Một vấn đề cực quan trọng:

```text
fn foo() -> Box<T>
```

return ownership chuyển sang caller.

ABI phải preserve:

```text
ownership transfer
```

chứ không chỉ:

```text
bits transfer
```

Ví dụ:

```text
caller
    |
    | owns Box
    ↓
callee
```

Move không nhất thiết copy memory.

---

# 34. ABI + Drop

Ví dụ:

```text
fn create() -> Resource
```

Nếu `Resource: Drop`:

```text
callee creates Resource
↓
return ownership
↓
caller owns Resource
```

Compiler phải đảm bảo:

```text
callee does NOT Drop returned Resource
```

Caller sẽ chịu trách nhiệm.

Nếu return bằng `sret`:

```text
caller storage
↓
callee initializes
↓
ownership transfers as result
```

Cleanup graph phải hiểu transfer này.

---

# 35. Partial initialization

Đây là vấn đề backend rất dễ sai.

Ví dụ:

```text
struct S {
    a: ResourceA,
    b: ResourceB,
}
```

callee khởi tạo:

```text
a
b
```

nếu panic giữa hai bước:

```text
a → Drop
b → chưa initialized
```

Nếu return thành công:

```text
ownership → caller
```

Do đó MIR cần phân biệt:

```text
Uninitialized
Initialized
Moved
Dropped
```

cho aggregate fields.

ABI lowering **không được phá vỡ initialization state**.

---

# 36. ABI + `Option`

Ví dụ:

```text
fn find() -> Option<&T>
```

Axiom không có nullable reference semantic.

Nhưng compiler có thể lower:

```text
Option<view<T>>
```

thành representation tối ưu.

Semantic layer vẫn giữ:

```text
Some
None
```

ABI layer quyết định:

```text
pointer + tag
```

hoặc:

```text
niche
```

---

# 37. ABI + `Result`

Ví dụ:

```text
fn read() -> Result<usize, IoError>
```

Nếu representation nhỏ:

```text
RAX = value
EDX = discriminant
```

thì `?` có thể trở thành branch/register operation.

Không có:

```text
exception object
stack unwinding
runtime catch
```

Đây là mục tiêu rất tốt cho hot path.

---

# 38. ABI + SIMD

Axiom nên cho phép aggregate/vector type được ABI classify thành:

```text
VectorRegister
```

Ví dụ:

```text
struct Float4 {
    x: f32
    y: f32
    z: f32
    w: f32
}
```

có thể:

```text
XMM0
```

nếu target ABI/legalization cho phép.

Nhưng:

```text
Float4
```

không nên mặc định là SIMD machine type trong semantic type system.

Semantic type:

```text
Float4
```

Backend quyết định:

```text
scalar
vector
split
memory
```

---

# 39. ABI và `@repr`

Cần phân biệt:

```text
semantic representation
```

và:

```text
ABI representation guarantee
```

Default:

```text
@repr(auto)
```

compiler tự quyết.

Explicit:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

mới tạo guarantee.

---

# 40. ABI verifier

Trước khi xuống Machine IR cần:

```text
ABIVerifier
```

kiểm tra:

- tất cả argument đã có location
- return có location
- register class hợp lệ
- stack alignment hợp lệ
- sret đúng vị trí
- hidden parameters đúng thứ tự
- callee/caller ABI tương thích
- variadic ABI đúng
- aggregate split hợp lệ
- no illegal aggregate passing
- ownership transfer không bị mất
- Drop obligations vẫn đúng
- unwind contract khớp
- TLS/ABI-specific requirements hợp lệ

---

# 41. ABI Plan

Tôi đề xuất mỗi function sau lowering có một object nội bộ:

```text
ABIPlan {
    calling_convention
    args[]
    returns[]
    hidden_args[]
    sret
    stack_size
    stack_alignment
    callee_saved
    caller_saved
    variadic
    unwind_mode
}
```

Ví dụ conceptual:

```text
ABIPlan {
    convention: AxiomNative

    args: [
        {
            type: i64,
            location: GPR0
        },
        {
            type: Vec2,
            location: [FPR0, FPR1]
        }
    ]

    returns: [
        {
            type: Result,
            location: [GPR0, GPR1]
        }
    ]

    sret: false
    variadic: false
    unwind_mode: Abort
}
```

Đây là representation cực kỳ hữu ích cho compiler và AI agent.

---

# 42. Native Axiom ABI

Axiom nên có ABI riêng:

```text
extern "axiom"
```

hoặc default:

```text
extern "Axiom"
```

Đặc điểm:

- compiler-controlled
- tối ưu cho Axiom
- không cần stable binary compatibility giữa mọi compiler version
- có thể thay đổi theo target/version
- tối ưu aggregate/register passing
- tối ưu closure/generic
- tối ưu Result/Option
- có thể dùng internal conventions không phù hợp C ABI

Còn:

```text
extern "C"
```

là ABI interoperability.

Đừng ép native Axiom ABI phải giống C ABI.

---

# 43. ABI versioning

Dynamic library/public ABI cần:

```text
Axiom ABI version
```

Ví dụ conceptual:

```text
axiom-abi-1
```

Compiler nội bộ có thể dùng:

```text
axiom-internal
```

và không hứa binary compatibility.

Điều này giúp compiler optimizer tự do phát triển.

---

# 44. Các invariant nên đóng băng

### ABI-20
**ABI Classification Is Target-Specific**

### ABI-21
**Source Types Are Independent Of Physical Calling Locations**

### ABI-22
**Scalar Values Prefer Direct Register Passing**

### ABI-23
**Small Aggregates May Be Passed In Registers**

### ABI-24
**Small Aggregates May Be Returned In Registers**

### ABI-25
**Large Aggregate Return May Use Hidden sret Storage**

### ABI-26
**Indirect Return Does Not Imply Heap Allocation**

### ABI-27
**Caller-Allocated Return Is Permitted**

### ABI-28
**Move Does Not Imply Physical Copy During ABI Transfer**

### ABI-29
**ABI Lowering Preserves Ownership Semantics**

### ABI-30
**ABI Lowering Preserves Drop Obligations**

### ABI-31
**view ABI May Use Fat-Value Representation**

### ABI-32
**Capability Metadata May Erase After Verification**

### ABI-33
**mut_view ABI Carries No Mandatory Runtime Borrow Metadata**

### ABI-34
**Option May Use Target-Dependent Niche Representation**

### ABI-35
**Result May Use Compact Register Representation**

### ABI-36
**Generic Static Dispatch Requires No Runtime Type Metadata**

### ABI-37
**Dynamic Dispatch Requires Explicit Runtime Representation**

### ABI-38
**Closure Environment Is Explicit Only After Lowering**

### ABI-39
**Noncapturing Closure May Decay To Function Pointer**

### ABI-40
**Capturing Closure Does Not Imply Heap Allocation**

### ABI-41
**Async Function Does Not Imply Heap Allocation**

### ABI-42
**Spawn May Require Persistent Future Storage**

### ABI-43
**FFI ABI Must Be Explicit**

### ABI-44
**Variadic ABI Is Target/Foreign-ABI Defined**

### ABI-45
**Foreign Exceptions Do Not Cross ABI Implicitly**

### ABI-46
**Panic ABI Is Profile Dependent**

### ABI-47
**Unwind Metadata Exists Only When Required**

### ABI-48
**@repr Controls Representation Guarantees Explicitly**

### ABI-49
**Default Layout Is Compiler Controlled**

### ABI-50
**ABI Plan Is Explicit Compiler IR**

### ABI-51
**ABI Verifier Must Run Before Machine Lowering**

### ABI-52
**ABI Lowering Must Preserve Initialization State**

### ABI-53
**Partial Aggregate Initialization Must Remain Drop-Safe**

### ABI-54
**Generic Compile-Time Information May Be Erased**

### ABI-55
**Native Axiom ABI Is Distinct From C ABI**

### ABI-56
**Stable External ABI Must Be Versioned**

---

# 45. Kiến trúc compiler sau khi đóng ABI-002

Pipeline lúc này đã khá hoàn chỉnh:

```text
                    SOURCE
                       │
                       ▼
                  ┌─────────┐
                  │   AST   │
                  └────┬────┘
                       ▼
                  ┌─────────┐
                  │   HIR   │
                  └────┬────┘
                       ▼
               ┌──────────────┐
               │  Typed HIR  │
               └──────┬───────┘
                      ▼
               ┌──────────────┐
               │ Trait Solver │
               └──────┬───────┘
                      ▼
                  ┌───────┐
                  │  MIR  │
                  └───┬───┘
                      ▼
          ┌─────────────────────────┐
          │ Semantic Verification   │
          │ Ownership               │
          │ Capability              │
          │ Drop                    │
          │ Concurrency             │
          │ Async                   │
          │ Unsafe                  │
          └────────────┬────────────┘
                       ▼
                Verified MIR
                       │
                       ▼
                ┌────────────┐
                │ ABI Lower  │
                └─────┬──────┘
                      ▼
                  ABI MIR
                      │
                      ▼
                ┌──────────┐
                │ Axiom LIR│
                └────┬─────┘
                     ▼
             Target Legalization
                     ▼
               Machine IR
                     ▼
             Register Allocation
                     ▼
             Machine Optimization
                     ▼
               Machine Encoder
                     ▼
                 Object File
                     ▼
                  Linker
                     ▼
                Native Binary
```

Điểm rất đáng chú ý: **từ `Verified MIR` trở xuống, compiler không còn được phép “suy đoán” semantic ownership/safety nữa.** Những thứ đó đã được chứng minh. Các tầng sau chỉ được phép preserve semantics và tối ưu representation.

---

# 46. Bước tiếp theo: `ABI-003 — Target ABI Database`

Sau ABI-002, phần tiếp theo nên **không nhảy ngay vào codegen**. Ta cần thiết kế database mô tả ABI của từng target.

Nó sẽ trả lời chính xác các câu hỏi như:

```text
x86-64 System V:
    i64       → GPR
    f64       → XMM
    Vec2      → ?
    BigStruct → memory/sret
```

```text
Windows x64:
    argument registers?
    return registers?
    shadow space?
```

```text
AArch64:
    integer registers
    FP/SIMD registers
    aggregate classification
    HFA/HVA
```

```text
WASM:
    scalar ABI
    multi-value return
    aggregate lowering
```

Và quan trọng nhất, chúng ta sẽ thiết kế nó sao cho **không hard-code ABI vào codegen**:

```text
TargetDescription
        +
ABIConvention
        +
TypeLayout
        +
ABIClassifier
        ↓
ABIPlan
```

Sau đó mới chuyển sang **`LIR-002 — Call/Return/Stack/Register Operations`**, tức lớp thực sự biến ABIPlan thành các instruction-level operations.