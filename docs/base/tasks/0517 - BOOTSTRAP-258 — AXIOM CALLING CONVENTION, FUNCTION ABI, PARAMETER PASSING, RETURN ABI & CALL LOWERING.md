# BOOTSTRAP-258 — AXIOM CALLING CONVENTION, FUNCTION ABI, PARAMETER PASSING, RETURN ABI & CALL LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng nối:

```text
Axiom Function
      ↓
Callable Type
      ↓
Semantic Signature
      ↓
ABI Classification
      ↓
Physical Signature
      ↓
Registers / Stack / Memory
      ↓
CALL / RET
```

Mục tiêu lớn nhất:

> **Function, method, generic, closure và trait abstraction phải có thể biến mất hoàn toàn sau compile-time khi semantics cho phép.**

Vì vậy:

```axiom
fn length(self: Vec2) -> f32
```

và:

```axiom
fn length(v: Vec2) -> f32
```

không được có overhead chỉ vì source sử dụng method syntax.

---

# 1. Ba loại function signature

Axiom cần phân biệt:

```text
Semantic Signature
ABI Signature
Machine Signature
```

Ví dụ:

```text
Semantic:
fn add(a: Vec2, b: Vec2) -> Vec2
```

ABI:

```text
Vec2 → registers
Vec2 → registers
Vec2 → registers
```

Machine:

```text
xmm0/xmm1...
```

---

# 2. Semantic signature

Bao gồm:

```text
FunctionId
Parameters
ReturnType
GenericParameters
Effects
Safety
Async
CallingMode
ExecutionDomain
```

---

# 3. Callable type

Callable type không chỉ gồm:

```text
(A, B) -> R
```

mà conceptually:

```text
(A, B) -> R
+
effects
+
async
+
safety
+
execution domain
```

---

# 4. Function effects

Ví dụ:

```text
Pure
Read
Write
Allocate
Panic
IO
Synchronize
Foreign
```

được giữ trong semantic contract.

---

# 5. ABI classification

Compiler nhận semantic type:

```text
T
```

và hỏi:

```text
How is T passed?
How is T returned?
```

---

# 6. Không có ABI chung cho mọi target

Ví dụ cùng:

```axiom
struct Vec4 {
    x: f32
    y: f32
    z: f32
    w: f32
}
```

có thể được pass:

```text
registers
```

trên một ABI nhưng:

```text
stack
```

trên ABI khác.

---

# 7. Target ABI

`TargetSpec` cung cấp:

```text
CallingConvention
RegisterClasses
StackAlignment
AggregateRules
ReturnRules
VectorRules
VariadicRules
TLSRules
UnwindRules
```

---

# 8. Default Axiom ABI

Axiom cần có ABI riêng:

```text
"Axiom"
```

Mục tiêu:

- tối ưu aggregate
- tối ưu return
- generic-friendly
- closure-friendly
- zero-cost abstraction
- deterministic
- versionable

---

# 9. C ABI

Interop:

```axiom
extern "C" fn foo(...)
```

sử dụng C ABI.

Không được mặc định dùng Axiom ABI rồi “hy vọng tương thích”.

---

# 10. Stable Axiom ABI

Stable ABI là một contract khác:

```axiom
@abi(stable)
pub fn foo(...)
```

Không đồng nghĩa với default internal ABI.

---

# 11. Internal ABI

Compiler có toàn quyền thay đổi:

```text
internal calling convention
```

miễn semantics được bảo toàn.

---

# 12. Parameter categories

ABI classifier xử lý:

```text
Scalar
Pointer
Vector
Aggregate
LargeAggregate
Reference/View representation
FunctionPointer
DynTrait
Future
ZST
Never
```

---

# 13. Scalar

Ví dụ:

```text
i32
f64
bool
```

thường có thể pass bằng register.

Nhưng ABI target quyết định.

---

# 14. Small aggregate

```axiom
struct Pair {
    a: i32
    b: i32
}
```

có thể được pass bằng:

```text
2 registers
```

hoặc một aggregate register class.

---

# 15. Large aggregate

Không được mặc định copy toàn bộ struct qua stack.

Compiler có thể dùng:

```text
indirect parameter
```

hoặc caller-provided storage.

---

# 16. Caller allocation

Ví dụ:

```axiom
fn make_big() -> Big
```

có thể lower:

```text
caller allocates return storage
        ↓
callee initializes it
```

---

# 17. SRET

Conceptual ABI mechanism:

```text
sret *Big
```

Nhưng đây là **ABI implementation detail**, không phải Axiom source reference.

---

# 18. Programmer vẫn thấy

```axiom
let x = make_big()
```

không cần:

```text
&mut x
```

hay:

```text
out parameter
```

---

# 19. Đây là điểm quan trọng

Axiom có thể dùng pointer-level ABI mà **không đưa pointer-level complexity vào source language**.

---

# 20. Return scalar

```axiom
fn f() -> i64
```

ABI có thể trả trong register.

---

# 21. Return small struct

```axiom
fn f() -> Pair
```

có thể return nhiều registers.

---

# 22. Return large struct

Có thể dùng:

```text
sret
```

hoặc ABI-specific indirect return.

---

# 23. Return ownership

Nếu:

```axiom
fn make() -> Box<T>
```

semantic result chuyển ownership cho caller.

Physical representation có thể là pointer/register.

---

# 24. Return `view<T>`

Nếu:

```axiom
fn get() -> view<T>
```

compiler phải verify provenance.

Không thể trả view trỏ tới local storage đã chết.

---

# 25. Return `mut_view<T>`

Ngoài provenance cần:

```text
exclusive capability
```

được duy trì sau function return.

---

# 26. Return `Option<T>`

ABI classifier có thể tận dụng niche.

Ví dụ:

```text
Option<Box<T>>
```

có thể vật lý là:

```text
pointer
```

với một niche biểu diễn None.

---

# 27. Nhưng niche không phải semantic representation

Semantic:

```text
Some
None
```

vẫn giữ nguyên.

---

# 28. `Result<T,E>`

Compiler có thể tối ưu layout theo target.

Không được giả định mọi `Result` có cùng physical layout.

---

# 29. Never

```axiom
fn abort() -> never
```

không cần return ABI.

---

# 30. `unit`

```axiom
fn f() -> unit
```

có thể không trả physical value.

---

# 31. ZST

Zero-sized type:

```axiom
struct Marker {}
```

có thể không chiếm register/stack storage.

---

# 32. ZST parameter

ABI có thể erase physical parameter nếu không observable.

---

# 33. ZST return

Có thể erase physical return.

---

# 34. Nhưng type vẫn tồn tại semantic

Generic constraints vẫn có thể depend on it.

---

# 35. Empty type / never

`never` không phải ZST thông thường.

Nó không có valid runtime value.

---

# 36. Parameter evaluation order

Axiom đã frozen:

```text
arguments evaluate left → right
```

ABI lowering không được thay đổi semantic evaluation order.

---

# 37. Nhưng machine argument preparation có thể reorder

Sau khi values đã được semantically evaluated, compiler có thể schedule instructions freely nếu effects không thay đổi.

---

# 38. Example

```axiom
foo(a(), b())
```

semantic:

```text
a()
↓
b()
↓
foo
```

Compiler có thể physically schedule independent computations nhưng observable effects phải tương đương.

---

# 39. Method call

```axiom
v.length(x())
```

semantic:

```text
evaluate v
evaluate x()
call length(v, x)
```

---

# 40. No implicit object pointer

Method receiver không cần:

```text
this pointer
```

ngoài representation mà ABI yêu cầu.

---

# 41. Struct receiver

```axiom
fn scale(self: Vec2, factor: f32) -> Vec2
```

là ordinary function.

---

# 42. Mutable receiver

Nếu:

```axiom
fn normalize(self: mut_view<Vec2>)
```

ABI có thể nhận:

```text
pointer
```

nhưng source không cần `&mut`.

---

# 43. View ABI

Conceptual:

```text
view<T>
    pointer
    length
```

nhưng compiler có thể optimize.

---

# 44. Length elimination

Nếu compiler biết static length:

```axiom
[4]i32
```

view length có thể không cần truyền.

---

# 45. View representation is not stable

Trừ khi ABI explicitly defines it.

---

# 46. FFI view

Không được export Axiom `view<T>` qua C ABI mà không có explicit representation contract.

---

# 47. Generic functions

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

semantic generic.

Default:

```text
monomorphization
```

---

# 48. Monomorphized ABI

Compiler tạo:

```text
max<i32>
max<f64>
max<MyType>
```

với ABI tối ưu từng instantiation.

---

# 49. Code sharing

Nếu hai instantiation có identical physical ABI/behavior:

→ compiler có thể share code.

---

# 50. Generic ABI không stable mặc định

Một public generic function không tự động có stable binary ABI.

---

# 51. Dynamic trait

```axiom
dyn Trait
```

là explicit dynamic dispatch.

---

# 52. Dyn ABI

Conceptual:

```text
data pointer
+
vtable/metadata pointer
```

Representation compiler/ABI controlled.

---

# 53. No implicit dyn conversion

Generic static function không tự nhiên biến thành dynamic dispatch.

---

# 54. Devirtualization

Nếu concrete target được chứng minh:

```text
dyn call
 ↓
known implementation
 ↓
direct call
```

có thể optimize.

---

# 55. Nhưng semantics vẫn dynamic contract

Devirtualization không thay đổi observable behavior.

---

# 56. Function pointer

```text
fn(A) -> B
```

function pointer có ABI-specific representation.

---

# 57. Capturing closure

Closure có:

```text
code
environment
```

nhưng static call thường được specialize/inlined.

---

# 58. Noncapturing closure

Có thể decay/coerce thành function pointer khi signature tương thích.

---

# 59. Capturing closure → function pointer

Không implicit.

---

# 60. FFI callback

Cần explicit stable representation:

```text
function pointer
+
context pointer
+
optional destructor/contract
```

---

# 61. Closure environment ABI

Internal only unless explicit stable callback ABI.

---

# 62. `async fn`

Semantic:

```text
async fn f() -> T
```

returns Future.

ABI của source function là ABI của Future value.

---

# 63. Future ABI

Future layout compiler-controlled.

Không stable ABI mặc định.

---

# 64. `dyn Future`

Dynamic future nếu library hỗ trợ phải explicit.

---

# 65. Async FFI

Không export raw Axiom Future qua C ABI.

Dùng:

```text
poll/callback/opaque handle
```

với explicit contract.

---

# 66. Calling convention attributes

System layer có thể hỗ trợ:

```text
@callconv("C")
@callconv("system")
@callconv("vectorcall")
```

target-dependent.

---

# 67. Core syntax

Không cần nhồi mọi ABI vào Core.

Một attribute đủ.

---

# 68. Variadic

C-style variadic chỉ dành cho FFI/system boundary.

Ví dụ:

```axiom
extern "C" fn printf(fmt: *const u8, ...)
```

---

# 69. Safe variadic functions

Không nên có arbitrary untyped variadic Core v1.

---

# 70. Typed variadic future

Có thể xây library/compiler feature sau này nếu có strong semantics.

---

# 71. Varargs ABI

Target ABI xác định:

- registers
- stack
- promotion
- metadata
- callee behavior

---

# 72. Calling convention

Function semantic type không nhất thiết encode machine calling convention.

ABI layer bổ sung:

```text
CallingConvention
```

---

# 73. ABI classification pipeline

```text
Semantic Function
       ↓
Resolve generic/trait/callable
       ↓
Semantic Signature
       ↓
Target ABI classifier
       ↓
Physical Signature
       ↓
Call lowering
```

---

# 74. Physical parameter descriptor

Conceptual:

```text
PhysicalParam {
    source_param
    mode
    location[]
    type
    alignment
    extension
}
```

---

# 75. Location

```text
Register
Stack
Indirect
CallerAllocated
Special
Erased
```

---

# 76. Register class

Target-specific:

```text
Integer
Float
Vector
Predicate
Capability
Special
```

---

# 77. Register allocation happens later

ABI classifier chỉ xác định register **class/ABI location policy**.

Actual register allocator assigns physical registers.

---

# 78. Stack parameters

ABI layer determines:

```text
offset
alignment
size
shadow/home space
```

nếu target yêu cầu.

---

# 79. Stack alignment

Function call must satisfy target ABI alignment at call boundary.

---

# 80. Red zone

Nếu target ABI hỗ trợ, backend có thể dùng.

Không phải Axiom semantic feature.

---

# 81. Caller-saved

ABI defines registers caller must preserve.

---

# 82. Callee-saved

ABI defines registers callee must preserve.

---

# 83. Prologue/epilogue

Backend generates:

```text
save callee-saved
stack frame
restore
return
```

only when necessary.

---

# 84. Leaf function

Axiom compiler may detect:

```text
no calls
no dynamic stack
no required frame
```

và eliminate prologue/epilogue.

---

# 85. Frame pointer

Không bắt buộc.

Compiler có thể omit frame pointer nếu debug/unwind/platform semantics cho phép.

---

# 86. Tail call

Tail call:

```text
caller
  ↓
callee
```

có thể reuse current frame.

---

# 87. Tail call legality

Cần:

```text
same compatible calling convention
+
return ABI compatible
+
cleanup completed
+
unwind semantics compatible
```

---

# 88. Tail recursion

Compiler có thể biến:

```axiom
fn loop(...)
```

thành loop nếu semantics tương đương.

---

# 89. Nhưng không guarantee

Tail-call elimination là optimization.

---

# 90. Calling convention + panic

If callee may unwind:

caller must have appropriate unwind metadata/cleanup path.

---

# 91. `noreturn`

Function returning `never` allows backend to eliminate continuation.

---

# 92. `cold`

System/compiler attribute có thể mark rarely executed function.

---

# 93. `hot`

Tương tự.

Nhưng đây là optimization hints, không thay đổi semantics.

---

# 94. `inline`

Có thể hỗ trợ:

```text
@inline
@inline(always)
@inline(never)
```

nhưng compiler vẫn phải respect correctness/ABI.

---

# 95. Inline does not mean ABI disappears across FFI

FFI boundary remains.

---

# 96. Interprocedural optimization

Internal Axiom calls có thể:

```text
inline
specialize
clone
devirtualize
merge
eliminate
```

---

# 97. External call

Không thể eliminate nếu observable effect unknown.

---

# 98. Pure external call

Chỉ tối ưu mạnh nếu FFI contract explicitly says pure/read-only/etc.

---

# 99. Function address

Taking function address may make function an external/codegen root.

---

# 100. Dynamic loading

Exported symbol may become linker/runtime root.

---

# 101. Function identity

Source function identity:

```text
FunctionId
```

khác machine address.

---

# 102. Function pointer equality

System/ABI-defined, không mặc định semantic identity của source declaration.

---

# 103. Generic function identity

`foo<i32>` và `foo<f64>` là distinct instantiated callable identities.

---

# 104. Generic code elimination

Nếu instantiation không reachable:

→ không emit machine code.

---

# 105. Function sections

Backend có thể emit mỗi function riêng section để dead-strip.

---

# 106. COMDAT/ICF

Linker có thể merge identical functions nếu observable identity/addresses/FFI contracts cho phép.

---

# 107. Address-observable function

Nếu code address được expose/compare theo system semantics:

→ ICF constraints apply.

---

# 108. ABI fingerprints

Mỗi stable ABI surface có:

```text
AbiFingerprint
```

được tính từ:

```text
symbol
calling convention
parameter ABI
return ABI
alignment
panic/error contract
effects
representation
version
```

---

# 109. Semantic fingerprint

Khác:

```text
SemanticFingerprint
```

ABI fingerprint.

---

# 110. Codegen fingerprint

Khác cả hai:

```text
CodegenFingerprint
```

---

# 111. Why three fingerprints?

Một source change có thể:

```text
semantic same
ABI same
codegen different
```

→ không cần rebuild dependent ABI.

---

# 112. Or:

```text
semantic same
ABI changed
```

→ dependent binary interface phải rebuild/revalidate.

---

# 113. ABI compatibility

Dynamic loading kiểm tra ABI fingerprint khi required.

---

# 114. Versioning

Stable ABI có version:

```text
AxiomABI v1
AxiomABI v2
```

Có thể coexist thông qua adapters.

---

# 115. C ABI

C ABI fingerprint dựa trên explicit contract + target ABI, không phải chỉ source type names.

---

# 116. Struct ABI

Default struct layout không stable.

Do đó public C ABI cần:

```axiom
@repr(C)
```

---

# 117. Transparent ABI

```axiom
@repr(transparent)
struct UserId(u64)
```

có thể expose như underlying representation nếu contract hợp lệ.

---

# 118. Stable function

```axiom
@abi(stable)
pub fn get_id(...) -> UserId
```

cần type ABI stable.

---

# 119. Generic stable ABI

Không được tự động cho phép:

```axiom
@abi(stable)
fn foo<T>(x: T)
```

nếu physical representation của T chưa được cố định bởi stable ABI contract.

---

# 120. Opaque types

Stable ABI nên ưu tiên:

```text id="2u8r3b"
opaque Handle
```

thay vì expose layout.

---

# 121. ABI adapters

Compiler/linker có thể generate:

```text
Axiom ABI
   ↓
adapter
   ↓
C ABI
```

---

# 122. No source overhead

Adapter code chỉ tồn tại tại boundary.

---

# 123. FFI ownership

Function ABI phải encode hoặc accompany:

```text
ownership
borrow/capability
nullability
lifetime
error
thread safety
```

---

# 124. Example

```axiom
extern "C" fn c_read(
    buffer: *mut u8,
    len: usize
) -> isize
```

raw pointer semantics are system-level.

Safe wrapper:

```text
File.read(mut_view<Bytes>)
```

có thể establish safety before calling.

---

# 125. ABI doesn't create safety

`extern "C"` chỉ chọn calling convention/ABI.

Nó không biến foreign function thành safe.

---

# 126. ABI + effects

Foreign call default:

```text
Foreign
Read
Write
```

conservative.

Contract can narrow.

---

# 127. Reentrancy

FFI contract có thể declare:

```text
MayReenter
NoReenter
```

nếu needed.

---

# 128. Call lowering

MIR:

```text id="3c0x1f"
Call {
    callee
    args
    destination
}
```

↓

```text id="n4j3os"
ABI Call
```

↓

```text id="qf8m8x"
PhysicalArg[]
PhysicalReturn
CallConv
Clobbers
UnwindTarget
```

---

# 129. ABI Call

Conceptual:

```text id="w0iwfg"
ABICall {
    calling_convention
    args
    return
    clobbers
    stack_requirements
    unwind
}
```

---

# 130. Machine call

Backend eventually emits:

```text id="mcewq5"
CALL symbol
```

or indirect call.

---

# 131. Indirect call

```text id="r4cc6b"
call function_pointer
```

requires callable ABI compatibility.

---

# 132. Dyn call

```text id="c2f8bd"
load vtable slot
call target
```

unless devirtualized.

---

# 133. Closure call

Static:

```text id="0z8fak"
direct code pointer
+
environment
```

Dynamic:

```text id="0c3w4p"
callable vtable
```

if explicitly erased.

---

# 134. Argument temporaries

ABI lowering must preserve ownership.

Example:

```axiom
foo(make_resource())
```

Temporary resource:

```text id="9am9fj"
create
→ pass
→ ownership transferred
```

No hidden clone.

---

# 135. Borrow/view arguments

Ephemeral view:

```text id="z9sjh6"
create capability
→ call
→ capability ends
```

---

# 136. Capability cannot escape unexpectedly

If callee returns/stores capability:

ABI semantic contract must reflect that.

---

# 137. `mut_view` argument

ABI representation can be pointer/length.

But semantic exclusive capability remains tracked before and after call.

---

# 138. Call clobber

Backend knows registers clobbered by call.

---

# 139. Semantic memory clobber

Separate:

```text
RegisterClobber
```

and:

```text
MemoryEffect
```

---

# 140. This distinction matters

A function may clobber:

```text
rax
```

without modifying memory.

Conversely it may modify memory while preserving many registers.

---

# 141. Call memory effects

MemorySSA uses semantic call effects.

---

# 142. Call optimizer

A pure function:

```text
no memory effect
```

can be CSE candidate.

---

# 143. Read-only call

May cache values if alias/effect facts permit.

---

# 144. Write call

Invalidates affected memory.

---

# 145. Atomic call

Carries synchronization semantics.

---

# 146. Foreign call

Potentially broad clobber.

---

# 147. Variadic ABI

Backend emits target-specific varargs setup.

---

# 148. Stack arguments

Stack layout must account for:

```text
alignment
padding
home slots
callee ABI
```

---

# 149. Return stack

sret/caller allocation must integrate with ownership.

---

# 150. Caller-owned return storage

Semantic ownership:

```text
caller receives initialized value
```

Physical:

```text
callee writes caller storage
```

---

# 151. No double Drop

Compiler must not generate:

```text
callee drops returned object
caller drops returned object
```

if ownership transferred.

---

# 152. ABI ownership transfer

ABI lowering cannot change semantic ownership.

---

# 153. Drop + call failure

If call panics/unwinds before ownership transfer completes, cleanup depends on exact call ABI and semantic transfer point.

Compiler must model it explicitly.

---

# 154. Argument move timing

Semantic model defines when argument ownership is consumed.

ABI lowering may rearrange physical moves but cannot alter that semantic boundary.

---

# 155. `Copy` argument

May pass register value without ownership transfer.

---

# 156. `Move` argument

Ownership consumed.

Physical copy may still occur.

---

# 157. Important principle

```text
semantic move ≠ machine move
```

---

# 158. Same for return

```text
semantic transfer ≠ physical memcpy
```

---

# 159. Large aggregate return optimization

Compiler may use:

```text
NRVO-like caller allocation
```

without requiring C++-style special language semantics.

---

# 160. Return value optimization

Because Axiom uses value semantics but semantic Move, compiler can often directly construct final destination.

---

# 161. Example

```axiom
let x = make_big()
```

can become:

```text id="f0c5l1"
caller allocates x
↓
make_big writes directly to x
```

---

# 162. No temporary

No semantic temporary if observable behavior doesn't require one.

---

# 163. Debug mode

Debug builds may materialize temporaries for debugging, provided semantics remain equivalent.

---

# 164. Optimization level independence

Observable program semantics cannot depend on whether:

```text
-O0
-O2
-O3
-size
```

---

# 165. ABI must be target deterministic

Same:

```text
source + target + ABI version
```

must yield same ABI classification.

---

# 166. Cache

ABI classification can be cached in CompilerDB:

```text id="v2k5bp"
AbiDB
```

key:

```text
TypeId
TargetId
AbiMode
AbiVersion
```

---

# 167. CompilerDB additions

```text
AbiSignatureDB
AbiClassifierDB
CallLoweringDB
RegisterClassDB
StackLayoutDB
ReturnAbiDB
FfiAbiDB
StableAbiDB
```

---

# 168. IDs

```text
AbiSignatureId
PhysicalParamId
PhysicalReturnId
CallingConventionId
RegisterClassId
StackSlotId
AbiFingerprintId
```

---

# 169. ABI classification algorithm

Conceptual:

```text
classify(type, target, abi):
    layout = LayoutDB[type,target]

    if ZST:
        erase

    if scalar:
        classify_scalar()

    if vector:
        classify_vector()

    if small aggregate:
        classify_aggregate()

    if large aggregate:
        classify_indirect()

    if special ABI type:
        classify_special()

    return PhysicalRepresentation
```

---

# 170. Aggregate classification

Must respect:

```text
size
alignment
field classes
padding
vector rules
target ABI
```

---

# 171. Do not recursively expose compiler layout as source ABI

Default struct layout remains compiler-controlled.

---

# 172. `repr(C)` changes that

For explicit C ABI representation:

```text
layout
alignment
field order
```

becomes constrained.

---

# 173. SIMD ABI

Vector types may use vector registers.

---

# 174. GPU ABI

GPU kernels do not use ordinary CPU calling convention.

They get:

```text
GPUKernelABI
```

with:

- resource bindings
- thread IDs
- address spaces
- workgroup data
- launch metadata.

---

# 175. Kernel function

```axiom
@kernel
fn add(...)
```

semantic function.

Physical ABI is GPU-specific.

---

# 176. Shader entry point

May have:

```text
@vertex
@fragment
@compute
```

and backend maps parameters to shader resources/built-ins.

---

# 177. WASM ABI

WASM has its own value types and linear-memory conventions.

Axiom must lower through `WasmABI`.

---

# 178. iOS/Android

Use platform target ABI descriptors rather than special frontend semantics.

---

# 179. Windows

PE/COFF calling conventions handled by TargetSpec.

---

# 180. Linux

ELF + platform ABI.

---

# 181. macOS

Mach-O + platform ABI.

---

# 182. ABI and dynamic libraries

Exports have stable ABI metadata.

Imports must validate:

```text id="0azxvf"
symbol
ABI
version
calling convention
```

---

# 183. Linker

Linker consumes physical ABI symbols, not HIR function semantics.

---

# 184. Symbol mangling

Internal Axiom symbols deterministic:

```text
package
module
function
generic instance
ABI
```

---

# 185. Stable export

`@export` gives explicit externally visible symbol identity.

---

# 186. No accidental exports

A public source declaration is not necessarily binary exported.

---

# 187. Generic exports

Stable binary generic export requires explicit policy.

Default:

```text
monomorphized instantiation
```

can be internal.

---

# 188. Dynamic loading

Plugin API should expose stable ABI declarations, typically opaque handles/functions.

---

# 189. ABI safety

Stable ABI must reject:

```text
unspecified layout
unstable generic representation
unstable dyn representation
compiler-private closure environment
```

unless explicitly wrapped.

---

# 190. ABI and exceptions

Axiom has no C++-style exception ABI in Core.

Panic ABI is Axiom-specific unless mapped explicitly.

---

# 191. Error ABI

`Result<T,E>` across stable ABI requires explicit representation contract.

Alternative:

```text
status code
out parameter
error handle
```

for C compatibility.

---

# 192. Panic ABI

Stable ABI must define whether:

```text
panic aborts
panic unwinds
panic crosses boundary
```

Recommendation:

> **Panic must not cross an `extern "C"` boundary unless an explicit ABI adapter contract exists.**

---

# 193. FFI adapter

Can convert:

```text
panic
→
error code
```

or abort according to explicit contract.

---

# 194. Thread ABI

Calling convention itself does not establish Send/Share.

A function can be callable from another thread only if semantic concurrency contract permits.

---

# 195. Async ABI

Calling an async function does not spawn execution.

ABI returns Future representation.

---

# 196. Closure ABI

Static closures can be completely optimized away.

---

# 197. Trait ABI

Static trait calls can disappear entirely through monomorphization.

---

# 198. This gives Axiom the desired abstraction model

Source:

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

can become:

```text
generic resolution
→ concrete implementation
→ direct call
→ inline
→ machine instructions
```

No object/vtable/heap required.

---

# 199. Dynamic version

Only:

```axiom
fn render(x: dyn Drawable)
```

requires dynamic dispatch semantics.

---

# 200. ABI pipeline

Final canonical pipeline:

```text
Semantic Function
       ↓
Callable Resolution
       ↓
Ownership/Capability verification
       ↓
Effect verification
       ↓
Generic specialization
       ↓
Verified MIR
       ↓
Semantic optimization
       ↓
Type Layout
       ↓
ABI Classification
       ↓
Physical Signature
       ↓
Call Lowering
       ↓
Register/Stack Assignment
       ↓
Machine Call Sequence
```

---

# 201. Important boundary

ABI lowering happens **after semantic optimization**, not before.

Điều này cho phép compiler:

- scalarize struct
- eliminate temporary
- inline
- specialize
- eliminate closure
- remove allocation

trước khi quyết định physical representation cuối cùng.

---

# 202. But FFI boundary freezes ABI earlier

Khi gặp:

```text
extern "C"
@abi(stable)
@export
```

compiler phải honor explicit ABI contract.

---

# 203. Internal function

Internal Axiom function:

```text
maximum optimization freedom
```

---

# 204. Stable function

Stable boundary:

```text
restricted representation
+
fixed ABI
+
fingerprint
```

---

# 205. ABI verifier

Compiler cần một phase:

```text
AbiVerification
```

kiểm tra:

```text
type representation
parameter classification
return classification
alignment
calling convention
panic/error
effects
FFI safety
stable ABI rules
```

---

# 206. ABI verifier không thay thế type verifier

Nó kiểm tra:

> Semantic program đã được compile thành physical interface hợp lệ chưa?

---

# 207. ABI mismatch

Diagnostic:

```text
AABI-E001

stable ABI function exposes type `T`
whose representation is not ABI-stable.

Use:
    @repr(C)
    @repr(transparent)
    or an opaque ABI handle.
```

---

# 208. Another diagnostic

```text
AABI-E002

return type requires indirect ABI,
but the declared stable ABI contract requires
a direct return representation.
```

---

# 209. Another

```text
AABI-E003

panic may cross an extern "C" boundary.

Define an explicit panic/error adapter.
```

---

# 210. Another

```text
AABI-E004

capturing closure cannot be exported directly.

Use an explicit callback ABI:
function pointer + context + lifetime/destructor contract.
```

---

# 211. Compiler optimization remarks

`ax explain call`:

```text
Call:
    foo<Vec4>

Dispatch:
    static

ABI:
    2 vector registers

Inlining:
    performed

Temporary:
    eliminated

Allocation:
    none
```

---

# 212. AI compiler interface

AI agent có thể query:

```text
why_is_this_indirect()
why_is_this_on_stack()
why_not_inlined()
why_sret()
why_dynamic_dispatch()
why_this_abi_is_unstable()
```

---

# 213. Đây là một ưu điểm lớn của Axiom

Compiler không chỉ compile:

> Nó có thể giải thích **tại sao abstraction không biến mất**.

---

# 214. ABI testing

Mỗi target cần:

```text
ABI conformance tests
```

với:

- scalar
- aggregate
- vector
- ZST
- Option
- Result
- large return
- sret
- variadic
- closure callback
- dyn trait
- FFI
- unwind
- alignment

---

# 215. Cross-language ABI tests

Ví dụ:

```text
Axiom → C
C → Axiom
Axiom → Rust C ABI
Axiom → Swift/ObjC bridge
Axiom → WASM host
```

---

# 216. ABI fuzzing

Random valid type signatures:

```text
generate type
→ classify
→ compare reference ABI
→ verify generated call
```

---

# 217. Miscompile regression

Nếu physical call sequence sai nhưng semantic MIR đúng:

→ permanent backend/ABI regression.

---

# 218. ABI invariants

```text id="9l3b6y"
AABI-CALL-20
Semantic function signatures are distinct from physical ABI signatures.

AABI-CALL-21
ABI classification occurs after semantic verification.

AABI-CALL-22
ABI classification is target-dependent.

AABI-CALL-23
ABI classification is deterministic for a fixed target and ABI version.

AABI-CALL-24
Default internal Axiom ABI is distinct from C ABI.

AABI-CALL-25
`extern "C"` explicitly selects the C ABI.

AABI-CALL-26
Stable ABI is an explicit contract.

AABI-CALL-27
`pub` does not imply stable binary ABI.

AABI-CALL-28
Stable ABI requires stable physical representations.

AABI-CALL-29
Unspecified aggregate layout cannot be exposed as stable ABI.

AABI-CALL-30
`@repr(C)` establishes C-compatible representation where applicable.

AABI-CALL-31
`@repr(transparent)` may preserve underlying ABI representation under its contract.

AABI-CALL-32
Default struct layout remains compiler-controlled.

AABI-CALL-33
ABI lowering cannot change semantic ownership.

AABI-CALL-34
ABI lowering cannot change semantic evaluation order.

AABI-CALL-35
Semantic Move does not imply physical memory copy.

AABI-CALL-36
Semantic Copy does not imply physical memory copy.

AABI-CALL-37
Returning an owning value transfers ownership exactly once.

AABI-CALL-38
Caller-allocated return storage may implement semantic value return.

AABI-CALL-39
Caller allocation does not expose pointer syntax to the programmer.

AABI-CALL-40
Large aggregates may use indirect return ABI.

AABI-CALL-41
Indirect return representation is an ABI detail.

AABI-CALL-42
Small aggregates may use registers when target ABI permits.

AABI-CALL-43
Scalar values may use ABI-defined register classes.

AABI-CALL-44
ZST parameters may be physically erased when ABI permits.

AABI-CALL-45
ZST erasure does not remove semantic type identity.

AABI-CALL-46
`unit` may have no physical return value.

AABI-CALL-47
`never` has no ordinary return ABI.

AABI-CALL-48
Niche optimizations may alter physical representation without altering semantics.

AABI-CALL-49
Niche representations are not stable ABI unless explicitly specified.

AABI-CALL-50
View representations are compiler-controlled unless an ABI contract specifies them.

AABI-CALL-51
Mutable view ABI does not weaken exclusive capability semantics.

AABI-CALL-52
Returned views must preserve provenance and validity.

AABI-CALL-53
Returned mutable views must preserve exclusivity.

AABI-CALL-54
Generic functions use compile-time specialization by default.

AABI-CALL-55
Generic monomorphization may produce independently optimized ABI instances.

AABI-CALL-56
Generic code sharing may occur when physical and semantic conditions permit.

AABI-CALL-57
Generic functions do not automatically have stable ABI.

AABI-CALL-58
Static trait dispatch does not require a vtable.

AABI-CALL-59
Dynamic trait dispatch is explicit.

AABI-CALL-60
Dynamic dispatch may be devirtualized when target identity is proven.

AABI-CALL-61
Devirtualization cannot change observable semantics.

AABI-CALL-62
Capturing closures do not implicitly become function pointers.

AABI-CALL-63
Noncapturing closures may coerce to compatible function pointers.

AABI-CALL-64
Closure environment ABI is compiler-controlled unless explicitly stabilized.

AABI-CALL-65
Stable callbacks require explicit callback representation.

AABI-CALL-66
Async functions return Future values semantically.

AABI-CALL-67
Future layout is compiler-controlled unless explicitly stabilized.

AABI-CALL-68
Async FFI requires an explicit ABI adapter.

AABI-CALL-69
Variadic C ABI is a system/FFI boundary.

AABI-CALL-70
Variadic ABI lowering is target-specific.

AABI-CALL-71
Calling convention is distinct from semantic function type.

AABI-CALL-72
Calling convention determines physical call rules.

AABI-CALL-73
Caller-saved and callee-saved rules are target ABI properties.

AABI-CALL-74
Stack alignment at call boundaries must satisfy target ABI requirements.

AABI-CALL-75
Prologue and epilogue generation is a backend concern.

AABI-CALL-76
Frame-pointer omission is legal when debug/unwind/ABI constraints permit.

AABI-CALL-77
Leaf functions may omit unnecessary call-frame machinery.

AABI-CALL-78
Tail-call optimization requires ABI compatibility.

AABI-CALL-79
Tail-call optimization requires cleanup correctness.

AABI-CALL-80
Tail-call optimization requires unwind correctness.

AABI-CALL-81
Function effects remain part of semantic call information.

AABI-CALL-82
Register clobbers are distinct from semantic memory effects.

AABI-CALL-83
Memory effects participate in MemorySSA.

AABI-CALL-84
Unknown foreign calls are conservatively modeled.

AABI-CALL-85
FFI contracts may narrow memory effects.

AABI-CALL-86
FFI ABI selection does not imply FFI safety.

AABI-CALL-87
FFI ownership requires explicit contract.

AABI-CALL-88
FFI nullability requires explicit contract.

AABI-CALL-89
FFI alignment requires explicit contract.

AABI-CALL-90
FFI lifetime requirements require explicit contract.

AABI-CALL-91
FFI Send/Share requirements require explicit contract.

AABI-CALL-92
Stable ABI panic behavior must be explicitly defined.

AABI-CALL-93
Axiom panic must not silently cross C ABI boundaries.

AABI-CALL-94
Error conversion across ABI boundaries must be explicit.

AABI-CALL-95
Stable ABI surfaces carry ABI fingerprints.

AABI-CALL-96
ABI fingerprints are distinct from semantic fingerprints.

AABI-CALL-97
ABI fingerprints are distinct from code-generation fingerprints.

AABI-CALL-98
ABI version changes participate in artifact identity.

AABI-CALL-99
Dynamic loading may validate ABI fingerprints.

AABI-CALL-100
ABI adapters may bridge compatible but distinct ABIs.

AABI-CALL-101
ABI adapters are boundary artifacts and need not infect Core syntax.

AABI-CALL-102
Exported symbols require explicit binary-export semantics.

AABI-CALL-103
Public source visibility does not automatically create binary exports.

AABI-CALL-104
Function address observability may constrain code merging.

AABI-CALL-105
Identical code may be merged only when observable function identity permits.

AABI-CALL-106
Generic instances may be dead-stripped when unreachable.

AABI-CALL-107
Function sections may enable dead stripping.

AABI-CALL-108
ABI lowering must preserve ownership/drop behavior.

AABI-CALL-109
ABI lowering must preserve capability validity.

AABI-CALL-110
ABI lowering must preserve panic/unwind semantics.

AABI-CALL-111
ABI lowering must preserve atomic/synchronization semantics.

AABI-CALL-112
ABI lowering must preserve external effects.

AABI-CALL-113
ABI lowering must preserve source evaluation order.

AABI-CALL-114
ABI lowering must preserve semantic return behavior.

AABI-CALL-115
ABI lowering must preserve semantic argument behavior.

AABI-CALL-116
Physical register assignment occurs after ABI classification.

AABI-CALL-117
Actual register allocation is distinct from ABI register classes.

AABI-CALL-118
Stack slot assignment is distinct from semantic local variables.

AABI-CALL-119
Physical temporaries may be introduced without semantic temporaries.

AABI-CALL-120
Physical copies may occur without semantic Copy operations.

AABI-CALL-121
Semantic Move may be implemented without physical copying.

AABI-CALL-122
Caller-allocated returns may eliminate intermediate storage.

AABI-CALL-123
Return-value optimization must preserve ownership semantics.

AABI-CALL-124
ABI classification must be independently testable.

AABI-CALL-125
ABI conformance tests must cover all supported target ABIs.

AABI-CALL-126
FFI ABI conformance must be tested against foreign compilers/runtimes where applicable.

AABI-CALL-127
ABI fuzzing must cover valid aggregate and callable signatures.

AABI-CALL-128
ABI failures must be diagnosable through structured compiler diagnostics.

AABI-CALL-129
AI tooling may inspect ABI decisions but cannot override ABI verification.

AABI-CALL-130
Stable ABI violations are compile-time errors.

AABI-CALL-131
ABI semantics are independent of optimization level.

AABI-CALL-132
Internal ABI may be freely optimized when not externally observable.

AABI-CALL-133
Stable ABI boundaries restrict optimization only where representation is observable.

AABI-CALL-134
ABI lowering must not introduce mandatory runtime machinery.

AABI-CALL-135
ABI lowering must not introduce hidden GC requirements.

AABI-CALL-136
ABI lowering must not introduce implicit reference-counting requirements.

AABI-CALL-137
ABI lowering must not require programmer-visible pointer syntax.

AABI-CALL-138
ABI lowering must preserve zero-cost abstraction opportunities.

AABI-CALL-139
ABI classification must be target- and version-deterministic.

AABI-CALL-140
ABI behavior is part of the compiler conformance contract.
```

---

# Kết quả rất quan trọng

Sau 258, ta có một ranh giới cực kỳ rõ:

```text
                    SEMANTIC WORLD
────────────────────────────────────────
Function
Method
Generic
Trait
Closure
Ownership
Capability
Effects
Async
                    │
                    ▼
              Verified MIR
                    │
────────────────────┼───────────────────
                    ▼
                ABI WORLD
                    │
          Type Layout
          ABI Classification
          Calling Convention
          Parameter Passing
          Return ABI
          Stack Layout
          Register Classes
                    │
                    ▼
               Machine World
────────────────────────────────────────
                    │
              CALL / RET
```

Đặc biệt, **`sret`, register passing, stack slots, hidden context pointers... đều có thể tồn tại trong compiler mà programmer không cần biết đến chúng.**

Đây chính là hướng phù hợp với mục tiêu Axiom mà chúng ta đã thống nhất: **ngôn ngữ không cần đơn giản vì compiler đơn giản; ngôn ngữ đơn giản vì compiler đủ thông minh để gánh phần phức tạp.**

---

# BOOTSTRAP-259 — bước tiếp theo

Bây giờ logical next step là:

## **AXIOM REGISTER MODEL, MACHINE IR, INSTRUCTION SELECTION & TARGET LOWERING**

Từ:

```text
Physical ABI
     ↓
Virtual registers
     ↓
Machine operands
     ↓
Instruction selection
     ↓
Target-specific instructions
     ↓
Register classes
     ↓
calling convention
     ↓
prologue/epilogue
```

sẽ đi sâu vào việc **Axiom tự sinh machine code trực tiếp**, không cần LLVM trong kiến trúc cuối cùng.

Đây sẽ là một trong những phần quan trọng nhất để đạt mục tiêu:

```text
Axiom source
    ↓
MIR
    ↓
Axiom LIR
    ↓
Machine IR
    ↓
x86-64 / ARM64 / RISC-V / WASM
    ↓
Object
```

và đặc biệt phải thiết kế sao cho **compiler backend đủ nhỏ để cuối cùng có thể self-host hoàn toàn bằng Axiom**.