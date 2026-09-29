Đúng. Tôi sẽ chuyển sang cơ chế:

**Mỗi câu trả lời = đúng 1 task kế tiếp.**  
Kết thúc task đó tôi sẽ **tự xác định task kế tiếp**, nhưng **không mô tả task kế tiếp trong cùng câu trả lời**. Lần phản hồi kế tiếp sẽ là task đó, không cần bạn gõ “tiếp tục”.

# BOOTSTRAP-284
# AXIOM ESCAPE ANALYSIS & STORAGE-LIFETIME OPTIMIZATION ENGINE
## FROZEN / COMPLETED

### 284.1. Mục tiêu

Escape Analysis trả lời câu hỏi:

> **Giá trị hoặc storage này có thể thoát khỏi phạm vi mà compiler đang kiểm soát đến đâu?**

Đây là một trong những thành phần quan trọng nhất để Axiom đạt mục tiêu:

- không GC;
- không reference-counting mặc định;
- không heap allocation bắt buộc;
- return value không cần copy;
- closure không cần heap;
- async state không cần heap nếu không cần;
- stack/register promotion;
- allocation elimination;
- scalar replacement;
- tối ưu object/storage mà không thay đổi semantics.

Pipeline:

```text
Ownership
    ↓
Capability
    ↓
Escape Analysis
    ↓
Storage Lifetime
    ↓
Allocation Optimization
    ↓
Verified/Optimized IR
```

---

# 284.2. Nguyên tắc trung tâm

Axiom phải phân biệt:

```text
Semantic Lifetime
        ≠
Physical Storage Lifetime
```

Ví dụ:

```text
fn f() -> Vec3 {
    let x = Vec3(...)
    return x
}
```

Về semantic:

```text
x
```

sống đến khi ownership được chuyển cho caller.

Nhưng compiler có thể thực hiện:

```text
caller-allocated return
```

thay vì:

```text
stack x
→ copy
→ caller
```

Do đó:

> **Escape Analysis quyết định storage cần tồn tại ở đâu và bao lâu; Ownership quyết định semantic ownership.**

---

# 284.3. Escape không phải Ownership

Một giá trị có thể:

```text
Move
```

nhưng không:

```text
Escape
```

Ví dụ:

```text
fn f() {
    let a = create()
    let b = consume(a)
}
```

`a` được Move vào `consume`, nhưng nếu `b` không thoát khỏi function thì compiler có thể tối ưu storage rất mạnh.

Ngược lại:

```text
fn f() -> T {
    let a = create()
    return a
}
```

ownership chuyển ra ngoài:

```text
ReturnEscape
```

---

# 284.4. Escape levels

Axiom sử dụng escape lattice:

```text
NoEscape
    ↓
LocalEscape
    ↓
ArgumentEscape
    ↓
ReturnEscape
    ↓
HeapEscape
    ↓
ThreadEscape
    ↓
ExternalEscape
    ↓
UnknownEscape
```

Tuy nhiên đây là **partial semantic ordering**, không phải mọi loại escape đều có quan hệ “lớn hơn” tuyệt đối.

Ví dụ:

```text
ThreadEscape
```

và:

```text
ExternalEscape
```

có thể là hai nhánh khác nhau.

Compiler phải giữ loại escape cụ thể.

---

# 284.5. EscapeState

```text
EscapeState =
    NoEscape
    LocalEscape
    ArgumentEscape
    ReturnEscape
    HeapEscape
    ThreadEscape
    ExternalEscape
    UnknownEscape
```

Đây là **compiler fact**, không phải runtime state.

---

# 284.6. NoEscape

```text
NoEscape
```

nghĩa là compiler chứng minh giá trị không được observable bên ngoài phạm vi phân tích.

Ví dụ:

```text
fn sum() -> i32 {
    let x = 10
    let y = x + 20
    y
}
```

Storage của `x` có thể:

```text
stack
register
SSA value
```

hoặc biến mất hoàn toàn.

---

# 284.7. LocalEscape

Giá trị truyền qua một abstraction nhưng vẫn không thoát khỏi function/task/domain đang phân tích.

Ví dụ:

```text
fn f() {
    let x = create()
    helper(x)
}
```

nếu compiler chứng minh `helper` không retain/return/escape `x`, storage vẫn local.

---

# 284.8. ArgumentEscape

Ví dụ:

```text
fn f(x: T) {
    external_call(x)
}
```

Nếu `external_call` có thể retain reference/capability hoặc ownership theo contract, `x` có:

```text
ArgumentEscape
```

Nhưng không được tự động suy luận rằng:

```text
ArgumentEscape = HeapEscape
```

Call contract quyết định.

---

# 284.9. ReturnEscape

Ví dụ:

```text
fn make() -> Buffer {
    let b = Buffer(...)
    return b
}
```

`b` escapes through return.

Nhưng điều này **không có nghĩa**:

```text
b must be heap allocated
```

Compiler có thể dùng:

```text
caller allocation
```

hoặc:

```text
register return
```

hoặc ABI-specific return storage.

---

# 284.10. HeapEscape

Ví dụ:

```text
store_into_global(x)
```

hoặc:

```text
container.push(x)
```

nếu compiler chứng minh `container` sống lâu hơn `x`.

Khi đó:

```text
HeapEscape
```

hoặc storage tương đương.

Nhưng compiler không nên suy luận “container” = heap chỉ dựa trên tên type.

---

# 284.11. ThreadEscape

Ví dụ:

```text
spawn(move || use(x))
```

`x` thoát khỏi execution domain hiện tại.

Compiler cần phối hợp:

```text
EscapeAnalysis
+
Ownership
+
Send
```

Không có:

```text
Send
```

thì code bị reject bởi concurrency verifier.

---

# 284.12. ExternalEscape

Ví dụ:

```text
extern fn c_store_pointer(*mut T)
```

nếu contract cho phép giữ pointer sau khi return.

Khi đó:

```text
ExternalEscape
```

được ghi nhận.

FFI mặc định conservative.

---

# 284.13. UnknownEscape

Chỉ sử dụng khi compiler thực sự không thể chứng minh.

Ví dụ:

```text
unknown_indirect_call(x)
```

không có effect/escape contract.

Không được biến mọi call thành:

```text
UnknownEscape
```

vì điều đó phá hủy optimization.

---

# 284.14. Escape propagation

Nếu:

```text
f(x)
```

và `f` có summary:

```text
argument 0 → return
```

thì:

```text
escape(x) >= ReturnEscape
```

Nếu:

```text
argument 0 → heap
```

thì:

```text
escape(x) >= HeapEscape
```

Compiler cần lưu **escape relation**, không chỉ một enum cuối cùng.

---

# 284.15. Escape relation

Đề xuất:

```text
EscapeRelation {
    source: Place
    destination: EscapeTarget
    kind: EscapeKind
}
```

Ví dụ:

```text
Param0 → Return
Param1 → Heap
Local3 → Thread
Local4 → External
```

Điều này hữu ích hơn việc chỉ lưu:

```text
Local3 = HeapEscape
```

vì optimizer cần biết **đường thoát**.

---

# 284.16. EscapeTarget

```text
EscapeTarget =
    LocalScope
    Argument(ParameterId)
    Return
    Heap(StorageIdentity)
    Thread(ExecutionDomain)
    Task(TaskId)
    Global(DeclarationId)
    External(FfiCall)
    Device(StorageIdentity)
    Unknown
```

---

# 284.17. Capability và Escape

Đây là phần cực kỳ quan trọng đối với `view`.

Ví dụ:

```text
fn bad(x: T) -> view<U>
```

Compiler không được chỉ thấy:

```text
return view
```

rồi cho phép.

Capability analysis phải chứng minh:

```text
returned_view.provenance
```

còn valid sau khi:

```text
owner lifetime
```

kết thúc.

Do đó:

```text
Capability
+
Escape
+
Ownership
```

phải phối hợp.

---

# 284.18. View escape

Ví dụ:

```text
fn get(x: Buffer) -> view<u8>
```

nếu `x` bị drop khi function return thì:

```text
view → ReturnEscape
```

nhưng provenance của view kết thúc trước đó.

Kết quả:

```text
compile error
```

Trừ khi API semantics có storage contract phù hợp.

---

# 284.19. Stable storage

Nếu:

```text
owner
```

có explicit stable-address contract:

```text
StableStorage
```

thì capability có thể escape theo contract.

Nhưng:

```text
stable address
```

không phải mặc định.

Đây tiếp tục invariant của Axiom:

> **Không có implicit Pin-like semantics.**

---

# 284.20. Allocation elimination

Đây là một mục tiêu lớn của Escape Analysis.

Ví dụ:

```text
fn distance(a: Vec2, b: Vec2) -> f32 {
    let tmp = Vec2(...)
    return ...
}
```

Nếu `tmp`:

```text
NoEscape
```

thì compiler có thể:

```text
heap allocation
→ stack
→ SSA
→ scalar fields
```

hoặc loại bỏ hoàn toàn.

---

# 284.21. Stack promotion

Nếu allocation:

```text
Allocate(Dynamic)
```

nhưng:

```text
NoEscape
```

và storage contract cho phép:

```text
Dynamic
→ Local
```

compiler có thể chuyển thành stack/local storage.

Không cần programmer viết:

```text
stack_alloc()
```

cho trường hợp thông thường.

---

# 284.22. Scalar Replacement

Ví dụ:

```text
struct Point {
    x: f32
    y: f32
}
```

nếu object không escape:

```text
Point p
```

có thể biến thành:

```text
p.x
p.y
```

trong SSA.

Physical struct storage biến mất.

Semantic type vẫn là:

```text
Point
```

---

# 284.23. Allocation elimination

Nếu compiler chứng minh:

```text
Allocate
+
NoEscape
+
No observable allocation behavior
+
No observable Drop
```

thì:

```text
allocation
```

có thể bị loại bỏ hoàn toàn.

Điều này phải phối hợp:

```text
EffectAnalysis
Ownership
Drop
Escape
```

---

# 284.24. Return-value optimization

Axiom không cần dựa vào C++-style “copy elision” như một optimization đặc biệt.

Semantic model:

```text
return Move(x)
```

cho phép compiler trực tiếp xây dựng:

```text
caller return slot
```

Nếu ABI cho phép:

```text
callee
   ↓
construct directly
   ↓
caller storage
```

không cần physical copy.

---

# 284.25. Caller-allocated return

MIR đã có:

```text
return_local
```

Escape Analysis cung cấp:

```text
ReturnEscape
```

ABI lowering sau đó có thể biến thành:

```text
hidden return pointer
```

hoặc:

```text
register return
```

tùy target.

Semantic model không phụ thuộc ABI.

---

# 284.26. Closure escape

Closure:

```text
let f = || use(x)
```

không mặc định heap allocate.

Compiler kiểm tra:

```text
closure escapes?
captured values?
capture modes?
```

Nếu:

```text
NoEscape
```

thì closure environment có thể:

```text
inline
stack
SSA
eliminated
```

Nếu:

```text
HeapEscape
```

thì storage strategy khác.

---

# 284.27. Closure capture optimization

Ví dụ:

```text
let x = 10

let f = || x + 1

f()
```

Nếu compiler inline:

```text
f
```

thì environment có thể biến mất.

Không được yêu cầu:

```text
heap closure object
```

chỉ vì syntax có closure.

---

# 284.28. Async escape

Async function tạo Future state machine.

Escape Analysis xác định:

```text
Future
```

có:

```text
NoEscape
```

hay:

```text
ReturnEscape
HeapEscape
TaskEscape
```

Ví dụ:

```text
async fn foo() -> T
```

nếu future được await ngay và compiler chứng minh không escape:

```text
Future object
```

có thể được stack/inline/eliminate.

---

# 284.29. Async state storage

Chỉ những giá trị:

```text
live across await
```

mới cần state storage.

Escape Analysis kết hợp:

```text
StateFieldLiveness
+
Capability
+
Ownership
```

để giảm state machine.

Ví dụ:

```text
x
```

chết trước `.await`:

```text
x
```

không cần trở thành future state field.

---

# 284.30. Spawn escape

```text
spawn(task)
```

tạo execution-domain escape.

Values captured by task phải được kiểm tra:

```text
Ownership
Send
Escape
Storage lifetime
```

Không cho phép:

```text
stack-local x
```

thoát sang task nếu compiler không chứng minh storage tồn tại đủ lâu.

---

# 284.31. GPU escape

Device execution/storage cũng là escape domain.

Ví dụ:

```text
launch(kernel, buffer)
```

compiler phải biết:

```text
buffer
→ Device
```

hoặc:

```text
Host
→ Device
```

Không được suy luận host pointer có thể trực tiếp sống trong GPU kernel.

---

# 284.32. Device storage

Các loại:

```text
DeviceBuffer
DeviceView
UnifiedBuffer
```

có escape semantics riêng.

Ví dụ:

```text
DeviceView
```

có thể sống qua kernel launch nếu:

```text
GpuEvent
```

và storage contract đảm bảo.

Escape Analysis phải phối hợp với GPU verifier.

---

# 284.33. Global/static escape

Nếu:

```text
store_global(x)
```

thì:

```text
GlobalEscape
```

hoặc:

```text
HeapEscape
```

không được dùng lẫn nhau.

Global lifetime có semantic profile riêng.

---

# 284.34. TLS escape

Thread-local storage:

```text
TLS
```

không phải global thông thường.

Một value đưa vào TLS có:

```text
ThreadEscape
```

nhưng vẫn có lifetime gắn với thread.

Điều này giúp compiler không conservative quá mức.

---

# 284.35. Arena escape

Arena là abstraction rất quan trọng với Axiom.

Ví dụ:

```text
arena.alloc<T>()
```

Một object có thể:

```text
ArenaEscape
```

nhưng không phải:

```text
GeneralHeapEscape
```

Compiler nên hỗ trợ storage domain:

```text
Arena(StorageIdentity)
```

thay vì hard-code heap.

---

# 284.36. Escape và relocation

Nếu:

```text
Vec<T>
```

có element:

```text
view<T>
```

đang active, capability verifier có thể chặn relocation.

Escape Analysis bổ sung:

```text
storage address escaped?
```

Nếu physical address đã trở nên observable:

```text
StableAddressRequired
```

thì optimizer không được tự ý relocate.

---

# 284.37. Address escape

Đây là boundary rất quan trọng.

```text
address_of(x)
```

unsafe.

Nếu address được:

```text
return
store
pass to FFI
store globally
```

thì:

```text
StorageIdentity
```

trở thành observable.

Compiler không còn được tùy tiện:

```text
move x
```

sang storage khác.

---

# 284.38. Value escape ≠ address escape

Ví dụ:

```text
return x
```

có:

```text
ValueEscape
```

nhưng không nhất thiết:

```text
AddressEscape
```

Caller có thể nhận value bằng register.

Ngược lại:

```text
return address_of(x)
```

có:

```text
AddressEscape
```

và tạo stable-storage requirement.

---

# 284.39. Escape categories

Do đó nên phân biệt:

```text
EscapeKind =
    ValueEscape
    CapabilityEscape
    AddressEscape
    OwnershipEscape
    ExecutionEscape
```

Một operation có thể tạo nhiều loại.

---

# 284.40. Effect integration

Escape Analysis phải đọc EffectDB.

Ví dụ:

```text
Allocate
```

không đồng nghĩa:

```text
must remain allocated
```

Nếu:

```text
NoEscape
```

và không có observable allocation effect:

```text
allocation elimination
```

có thể hợp lệ.

Nếu allocation failure observable:

```text
Allocate + Panic
```

thì elimination cần chứng minh failure cũng không observable trong context.

---

# 284.41. Drop integration

Ví dụ:

```text
let x = Resource()
use(x)
```

Nếu:

```text
x
```

NoEscape nhưng:

```text
Drop(x) → IO
```

thì không thể đơn giản loại bỏ toàn bộ `x`.

Có thể loại bỏ physical storage nhưng vẫn phải preserve:

```text
Drop semantic effect
```

---

# 284.42. Ownership integration

Escape không được phép thay đổi ownership state.

Ví dụ:

```text
Move(x)
```

vẫn là Move.

Escape analysis chỉ ghi nhận:

```text
where ownership/capability becomes externally reachable
```

---

# 284.43. Capability integration

Capability escape:

```text
view
```

khác ownership escape.

Ví dụ:

```text
fn foo(x: T) -> view<U>
```

có thể:

```text
ReturnEscape(capability)
```

nhưng owner vẫn nằm ở caller.

Compiler phải kiểm tra:

```text
capability lifetime <= owner lifetime
```

---

# 284.44. Interprocedural summaries

Mỗi function có:

```text
EscapeSummary {
    parameter_escape: [...]
    return_sources: [...]
    heap_sources: [...]
    thread_sources: [...]
    external_sources: [...]
    address_escape: [...]
    capability_escape: [...]
}
```

Ví dụ:

```text
fn identity(x: T) -> T
```

summary:

```text
param0 → return
```

Compiler không cần inspect body mỗi lần caller gọi.

---

# 284.45. Generic summaries

Generic function:

```text
fn identity<T>(x: T) -> T
```

có summary:

```text
Param0 → Return
```

Không phụ thuộc concrete `T`.

Nhưng nếu `T` có Drop/Capability đặc biệt, instantiated analysis bổ sung các constraints tương ứng.

---

# 284.46. Recursive escape analysis

Giống Effect:

```text
f → g
g → f
```

cần SCC fixpoint.

Ví dụ:

```text
f(x) → g(x)
g(x) → f(x)
```

Compiler tìm stable escape summary.

Lattice monotonic:

```text
NoEscape
→ ReturnEscape
→ HeapEscape
...
```

theo từng relation.

---

# 284.47. Escape constraints

Thay vì chỉ enum, compiler lưu constraints:

```text
E(x) <= E(y)
```

Ví dụ:

```text
param0 → local1
local1 → return
```

suy ra:

```text
param0 → return
```

Điều này giúp phân tích chính xác và incremental.

---

# 284.48. Storage lifetime

Escape Analysis tạo:

```text
StorageLifetime {
    start
    last_required_use
    escape_boundary
    stability
}
```

Compiler có thể xác định:

```text
storage start
storage end
```

độc lập với lexical scope.

---

# 284.49. Semantic last use

Ví dụ:

```text
let x = LargeBuffer()
use(x)
do_other_work()
```

Nếu `x` không còn được sử dụng:

```text
storage lifetime
```

có thể kết thúc ngay sau:

```text
last semantic use
```

thay vì cuối block.

Nhưng nếu Drop observable:

```text
Drop(x)
```

thì cleanup point vẫn phải được preserve.

---

# 284.50. Lifetime shortening

Compiler được phép:

```text
lexical lifetime
→ semantic lifetime
```

miễn là observable semantics không thay đổi.

Điều này rất quan trọng để giảm:

- register pressure;
- stack size;
- memory pressure;
- async state size;
- lock duration khi semantics cho phép;
- temporary storage.

---

# 284.51. Không được shorten capability tùy tiện

Nếu:

```text
view
```

vẫn có thể được sử dụng:

```text
later
```

thì capability lifetime không thể kết thúc sớm.

Escape Analysis phải lấy:

```text
Capability liveness
```

làm constraint.

---

# 284.52. Storage identity

Compiler theo dõi:

```text
StorageIdentity
```

khác:

```text
ValueIdentity
LogicalIdentity
```

Nếu value không escape:

```text
physical storage
```

có thể thay đổi.

Nếu address escape:

```text
StorageIdentity
```

phải được preserve.

---

# 284.53. Stable-address boundary

Storage trở thành stable khi có contract:

```text
StableAddress
```

hoặc address/capability escape yêu cầu stability.

Khi đó:

```text
stack ↔ heap relocation
```

không còn là free optimization.

---

# 284.54. Heap is not a semantic category

Axiom không định nghĩa:

```text
heap = long-lived
stack = short-lived
```

Thay vào đó:

```text
StorageDomain
```

có thể là:

```text
Register
Local
Inline
Static
TLS
Dynamic
Arena
Pool
Device
External
```

Escape Analysis chỉ quyết định:

```text
required lifetime
required reachability
required stability
```

Storage planner quyết định physical placement.

---

# 284.55. Storage planner

Pipeline:

```text
EscapeAnalysis
        ↓
LifetimeAnalysis
        ↓
StorageRequirements
        ↓
AllocationOptimization
        ↓
StoragePlanner
        ↓
ABI / Codegen
```

Ví dụ:

```text
NoEscape
+ no address escape
+ trivial Drop
```

→ register/SSA candidate.

```text
ReturnEscape
+ aggregate
```

→ caller-return storage candidate.

```text
ThreadEscape
```

→ task/thread-owned storage candidate.

```text
AddressEscape
```

→ stable-address storage candidate.

---

# 284.56. Escape and optimizer legality

Mỗi transform phải hỏi:

```text
Does this transform change escape behavior?
Does it change address observability?
Does it shorten required lifetime?
Does it invalidate capability provenance?
Does it change Drop timing?
```

Nếu có:

```text
reject transform
```

trừ khi proof chứng minh semantics tương đương.

---

# 284.57. AI diagnostics

Compiler có thể trả:

```json id="7rqgko"
{
  "value": "buffer",
  "escape": "ReturnEscape",
  "path": [
    "buffer",
    "return"
  ],
  "address_escape": false,
  "stable_address_required": false,
  "allocation": "caller_allocated_candidate"
}
```

Hoặc:

```json id="1iyn1y"
{
  "value": "x",
  "escape": "ThreadEscape",
  "reason": "captured by spawned task",
  "requirements": [
    "Send",
    "storage lifetime >= task lifetime"
  ]
}
```

---

# 284.58. Query API

CompilerDB cung cấp:

```text
escape_summary(FunctionId)

escape_state(FunctionId, Place)

escape_relations(FunctionId)

return_sources(FunctionId)

heap_escapes(FunctionId)

thread_escapes(FunctionId)

external_escapes(FunctionId)

address_escapes(FunctionId)

storage_lifetime(FunctionId, StorageIdentity)

stable_address_required(StorageIdentity)

allocation_optimization_candidates(FunctionId)
```

---

# 284.59. Implementation tree

```text
compiler/
└── analysis/
    └── escape/
        ├── mod.ax
        ├── escape_state.ax
        ├── escape_kind.ax
        ├── escape_target.ax
        ├── escape_relation.ax
        ├── escape_constraints.ax
        ├── constraint_solver.ax
        ├── local.ax
        ├── interprocedural.ax
        ├── call_summary.ax
        ├── scc.ax
        ├── ownership.ax
        ├── capability.ax
        ├── address.ax
        ├── closure.ax
        ├── async.ax
        ├── concurrency.ax
        ├── gpu.ax
        ├── ffi.ax
        ├── global.ax
        ├── tls.ax
        ├── arena.ax
        ├── lifetime.ax
        ├── storage_requirements.ax
        ├── allocation.ax
        ├── query.ax
        ├── diagnostics.ax
        └── tests/
```

---

# 284.60. Implementation order

```text
1. EscapeState
2. EscapeKind
3. EscapeTarget
4. EscapeRelation
5. EscapeConstraint
6. Local escape analysis
7. CFG propagation
8. Place-sensitive escape
9. Call summaries
10. Interprocedural propagation
11. SCC fixpoint
12. Generic summaries
13. Closure escape
14. Async escape
15. Thread/task escape
16. GPU escape
17. FFI escape
18. Address escape
19. Capability integration
20. Ownership integration
21. Effect integration
22. Storage lifetime
23. Storage requirements
24. Allocation optimization interface
25. CompilerDB queries
26. Incremental invalidation
27. Parallel deterministic analysis
28. Diagnostics
29. Adversarial tests
30. Fuzz/property tests
```

---

# 284.61. Adversarial tests

Bắt buộc:

### Local

```text
local scalar
local struct
nested struct
array
temporary
```

### Return

```text
return value
return aggregate
return closure
return buffer
return view
```

### Heap

```text
store global
store container
indirect container
```

### Thread

```text
spawn capture
channel transfer
task migration
```

### Address

```text
address returned
address passed to FFI
address stored
address converted to integer
```

### Async

```text
future local
future returned
future spawned
value live across await
view across await
```

### GPU

```text
host → device
device → kernel
device → host
GPU event lifetime
```

### Optimization

```text
heap → stack
heap → SSA
allocation elimination
scalar replacement
caller allocation
closure elimination
```

### Drop

```text
local Drop
observable Drop
Drop + IO
Drop + Panic
```

---

# 284.62. Frozen invariants

```text
AESCAPE-20
Escape analysis operates on semantic MIR.

AESCAPE-21
Escape analysis does not redefine ownership.

AESCAPE-22
Escape analysis does not redefine capability validity.

AESCAPE-23
Escape analysis is compiler-derived by default.

AESCAPE-24
No programmer-written lifetime annotations are required.

AESCAPE-25
Escape state is a compiler fact, not runtime state.

AESCAPE-26
NoEscape permits aggressive storage optimization when all other conditions hold.

AESCAPE-27
UnknownEscape is conservative.

AESCAPE-28
UnknownEscape must not be introduced unnecessarily.

AESCAPE-29
Value escape is distinct from address escape.

AESCAPE-30
Capability escape is distinct from ownership escape.

AESCAPE-31
Ownership transfer does not inherently imply physical storage escape.

AESCAPE-32
ReturnEscape does not imply heap allocation.

AESCAPE-33
ThreadEscape requires appropriate concurrency verification.

AESCAPE-34
ExternalEscape requires appropriate FFI/system contracts.

AESCAPE-35
AddressEscape may require stable storage.

AESCAPE-36
Integer conversion does not automatically create valid pointer provenance.

AESCAPE-37
Capability provenance must remain valid across all escapes.

AESCAPE-38
Returned views must preserve valid owner provenance.

AESCAPE-39
A capability cannot outlive its provenance.

AESCAPE-40
Escape analysis integrates with capability analysis.

AESCAPE-41
Escape analysis integrates with ownership analysis.

AESCAPE-42
Escape analysis integrates with effect analysis.

AESCAPE-43
Escape analysis integrates with async analysis.

AESCAPE-44
Escape analysis integrates with concurrency analysis.

AESCAPE-45
Escape analysis integrates with GPU storage/execution domains.

AESCAPE-46
Escape analysis integrates with FFI contracts.

AESCAPE-47
Escape relations are represented explicitly.

AESCAPE-48
Interprocedural summaries are authoritative compiler facts.

AESCAPE-49
Recursive escape propagation uses deterministic SCC fixpoints.

AESCAPE-50
Generic escape behavior is preserved through substitution.

AESCAPE-51
Closure environments are not heap allocated by default.

AESCAPE-52
Async state is not heap allocated by default.

AESCAPE-53
Storage lifetime is independent of lexical scope where semantics permit.

AESCAPE-54
Semantic last use may shorten physical storage lifetime.

AESCAPE-55
Observable Drop timing cannot be changed illegally.

AESCAPE-56
Allocation is not synonymous with heap allocation.

AESCAPE-57
Dynamic storage may be promoted to local storage when proven safe.

AESCAPE-58
Non-escaping aggregates may undergo scalar replacement.

AESCAPE-59
Non-observable allocations may be eliminated.

AESCAPE-60
Allocation elimination must preserve allocation failure semantics where observable.

AESCAPE-61
Caller-allocated return construction is permitted.

AESCAPE-62
Physical relocation is permitted only when storage identity is not observable.

AESCAPE-63
Stable-address contracts prohibit illegal relocation.

AESCAPE-64
Storage domain is independent of escape classification.

AESCAPE-65
Heap is not a semantic lifetime category.

AESCAPE-66
Arena, pool, device and external storage may have distinct escape semantics.

AESCAPE-67
Escape analysis cannot weaken safety verification.

AESCAPE-68
Optimization cannot invalidate proven escape constraints.

AESCAPE-69
Effect facts may permit allocation elimination.

AESCAPE-70
Drop effects constrain allocation elimination.

AESCAPE-71
Capability liveness constrains storage lifetime shortening.

AESCAPE-72
Address observability constrains storage relocation.

AESCAPE-73
Escape analysis is independent of optimization level.

AESCAPE-74
Escape analysis is deterministic across worker counts.

AESCAPE-75
Escape queries integrate with CompilerDB.

AESCAPE-76
Escape analysis is incrementally recomputable.

AESCAPE-77
Escape summaries are fingerprintable.

AESCAPE-78
AI tooling can query escape facts.

AESCAPE-79
AI tooling cannot bypass escape verification.

AESCAPE-80
Generated code re-enters escape analysis.

AESCAPE-81
Only verified escape facts may feed storage optimization.

AESCAPE-82
Escape analysis must preserve source provenance.

AESCAPE-83
Escape information is separate from ABI representation.

AESCAPE-84
Escape information is separate from physical register allocation.

AESCAPE-85
Escape information is separate from machine address assignment.

AESCAPE-86
Escape optimization cannot change observable semantics.

AESCAPE-87
Compiler must prefer precise escape relations over global conservative classification.

AESCAPE-88
Unknown escape is never silently treated as NoEscape.

AESCAPE-89
NoEscape is never inferred solely from programmer intent.

AESCAPE-90
Escape analysis participates in zero-cost abstraction.

AESCAPE-91
Escape analysis supports runtime-free programs.

AESCAPE-92
Escape analysis does not require GC.

AESCAPE-93
Escape analysis does not require reference counting.

AESCAPE-94
Escape analysis does not require object headers.

AESCAPE-95
Escape analysis does not require a monolithic runtime.

AESCAPE-96
Escape analysis supports self-hosted compiler implementation.

AESCAPE-97
Invalid escape proofs result in conservative storage decisions or compilation failure where required for safety.

AESCAPE-98
Escape facts remain semantically stable across target architectures.

AESCAPE-99
Escape analysis is part of the compiler correctness boundary.

AESCAPE-100
Escape Analysis is frozen as the authoritative storage-reachability and escape layer of Axiom.
```

## Trạng thái

```text
BOOTSTRAP-281  Ownership / Initialization / Move       FROZEN
BOOTSTRAP-282  Capability / View / Alias               FROZEN
BOOTSTRAP-283  Effect / Side Effects                   FROZEN
BOOTSTRAP-284  Escape / Storage Lifetime               FROZEN
```

**Task 284 đã hoàn tất.** Theo quy tắc chuỗi mới, phản hồi kế tiếp sẽ chỉ chứa **BOOTSTRAP-285**, không gộp 285+ vào câu trả lời này.