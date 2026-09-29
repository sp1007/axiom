Tiếp tục với **OPT-001 — Optimization Contract**. Đây là phần rất quan trọng vì Axiom đang theo triết lý:

> **Compiler có thể phức tạp đến đâu cũng được, miễn là programmer không phải gánh sự phức tạp đó và semantics vẫn xác định.**

# OPT-001 — Optimization Contract

## 1. Nguyên tắc nền tảng

Axiom phải phân biệt rõ:

```text
Semantic correctness
        ↓
Optimization freedom
        ↓
Machine implementation
```

Compiler được phép thay đổi:

- vị trí lưu trữ;
- thứ tự thực thi không quan sát được;
- số lần copy vật lý;
- số lần allocation;
- register/stack;
- layout nội bộ;
- instruction sequence;
- function boundaries;

nhưng **không được thay đổi observable behavior** của chương trình hợp lệ.

---

# 2. "As-if rule" nhưng mạnh hơn C

C có as-if rule, nhưng C còn có rất nhiều vùng undefined behavior khiến compiler có quyền suy luận cực mạnh.

Axiom nên đi theo hướng:

> **Safe Axiom có semantics xác định; optimizer không được dựa vào programmer “chắc chắn không làm điều đó”.**

Ví dụ:

```text
var x: i32 = 2_000_000_000
x += x
```

không được biến thành UB rồi optimizer tùy ý.

Semantics overflow đã được định nghĩa từ trước:

```text
checked
wrapping
saturating
```

tùy operation/API.

---

# 3. Nhưng Axiom vẫn có `unsafe`

`unsafe` mở machine-level behavior.

Ví dụ:

```text
unsafe {
    let p: *mut u32 = ...
    *p = 10
}
```

Compiler không cần đảm bảo programmer đã cung cấp pointer hợp lệ.

Nhưng:

> **unsafe không biến toàn bộ function thành vùng optimizer muốn làm gì thì làm.**

Nó chỉ cho phép những operation mà safe code không được phép.

---

# 4. Hai loại assumption

Compiler có:

### Proven fact

```text
x != null
view valid
regions disjoint
T: Send
```

được verifier chứng minh.

### Programmer assumption

```text
unsafe pointer is valid
```

do programmer chịu trách nhiệm.

Optimizer có thể sử dụng semantic facts đã được xác lập, nhưng không tự tạo facts không có bằng chứng.

---

# 5. Ownership là nguồn alias information rất mạnh

Ví dụ:

```text
fn process(a: mut_view<i32>, b: mut_view<i32>)
```

Nếu compiler biết:

```text
Region(a) DISJOINT Region(b)
```

thì có thể tối ưu tương tự trường hợp có `restrict`:

```text
load a
load b
store a
store b
```

mà không cần programmer viết `restrict`.

---

# 6. Nhưng UNKNOWN không được coi là DISJOINT

Ví dụ:

```text
fn foo(a: mut_view<i32>, b: mut_view<i32>)
```

nếu compiler không chứng minh được:

```text
a ∩ b = ∅
```

thì:

```text
reject
```

hoặc API phải cung cấp abstraction đảm bảo điều kiện.

Không được:

```text
assume noalias
```

chỉ để optimizer chạy nhanh hơn.

---

# 7. Đây là điểm khác biệt lớn với C

C programmer thường phải nói:

```text
restrict
```

để optimizer biết alias contract.

Axiom muốn:

```text
ownership + capability + region analysis
```

tạo information đó tự động.

---

# 8. Escape analysis

Ví dụ:

```text
fn make() -> Vec<i32> {
    let x = Vec.new()
    x
}
```

Không có nghĩa:

```text
x → malloc()
return heap pointer
```

Compiler có thể:

```text
caller allocation
```

hoặc:

```text
register/stack
```

nếu semantics cho phép.

---

# 9. Allocation elimination

Ví dụ:

```text
fn distance(a: Vec2, b: Vec2) -> f32 {
    let temp = Vec2(...)
    ...
}
```

Nếu `temp` không escape:

```text
NO ALLOCATION
```

Có thể hoàn toàn scalarize:

```text
temp.x → register
temp.y → register
```

---

# 10. `Box<T>` cũng có thể được tối ưu

Đây là quyết định quan trọng đã chốt:

```text
Box<T>
```

mang semantic:

> owned dynamic storage.

Không mang nghĩa:

> bắt buộc phải tồn tại trên heap vật lý.

Ví dụ:

```text
let x = Box.new(Foo(...))
use(x)
```

Nếu địa chỉ không observable:

```text
Box allocation → eliminated
```

Nếu:

```text
let p = address_of(x)
```

thì stable-address/storage contract trở nên observable và compiler phải tôn trọng.

---

# 11. Address observability là optimization barrier

Ví dụ:

```text
let x = Box.new(...)
let p = raw_address(x)
```

Từ thời điểm đó compiler không thể tùy tiện:

```text
move x
scalarize x
merge x
```

nếu làm thay đổi observable address semantics.

Đây là:

```text
AMEM-55
AMEM-70
```

và phải trở thành optimizer rule.

---

# 12. Stack promotion

Ngược lại:

```text
Box.new(x)
```

nếu không escape:

```text
dynamic storage
       ↓
stack
```

hoặc:

```text
stack
       ↓
register
```

hoàn toàn hợp lệ.

---

# 13. Register promotion

Một struct:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

có thể:

```text
memory representation
```

trên source semantics.

Optimizer có thể biến thành:

```text
x → xmm0
y → xmm1
```

Không thay đổi semantics.

---

# 14. SROA

Aggregate:

```text
struct Particle {
    x: f32
    y: f32
    z: f32
    velocity: Vec3
}
```

có thể được scalar replacement thành:

```text
x
y
z
vx
vy
vz
```

nếu không có observable address/layout requirement.

---

# 15. Khi nào không được SROA?

Nếu:

```text
@repr(C)
```

và:

```text
extern "C"
```

hoặc:

```text
raw address exposed
```

thì representation trở thành observable.

Optimizer phải giữ ABI contract.

---

# 16. NRVO / return optimization

Axiom không nên định nghĩa:

```text
return
```

là copy.

Ví dụ:

```text
fn make() -> Large {
    let x = Large(...)
    return x
}
```

Compiler có thể:

```text
caller allocates return slot
       ↓
construct x directly there
```

Không copy.

Đã có:

```text
AMEM-28
AMEM-29
```

---

# 17. Move cũng không phải copy

```text
let y = x
```

nếu `x` là Move type:

```text
ownership(x) → ownership(y)
```

physical bytes có thể:

```text
0 bytes copied
```

Compiler không cần materialize source/destination.

---

# 18. Copy cũng không bắt buộc physical copy

Nếu:

```text
Copy
```

nhưng compiler biết value chỉ cần tồn tại ở một register:

```text
x + x
```

có thể dùng:

```text
same register
```

hoặc duplicate register as needed.

`Copy` là semantic property.

Không phải instruction requirement.

---

# 19. Inlining

Compiler được tự động inline:

```text
fn square(x) -> x * x
```

Không cần:

```text
@inline
```

`@inline` nếu có chỉ là optimization hint.

Không được trở thành semantic guarantee.

---

# 20. `@inline` semantics

Tôi đề xuất:

```text
@inline
@noinline
```

là **optimization hints**.

`@noinline` có thể hữu ích cho:

- profiling;
- debugging;
- ABI boundaries;
- security-sensitive code.

Nhưng compiler vẫn phải bảo toàn semantics.

---

# 21. Constant folding

```text
const X = 10 * 20
```

→ `200`.

Nhưng compiler cũng có thể fold:

```text
fn foo() {
    let x = 10 * 20
}
```

nếu không observable.

---

# 22. Dead code elimination

```text
if false {
    expensive()
}
```

→ eliminate.

Nhưng:

```text
if volatile_condition()
```

không được eliminate nếu volatile operation observable.

Tương tự:

```text
atomic
IO
FFI
```

có observable semantics.

---

# 23. Dead store elimination

```text
x = 10
x = 20
return x
```

có thể:

```text
x = 20
```

Nếu `x = 10` không có observable effect.

Nhưng:

```text
volatile_write(...)
```

không được xóa.

---

# 24. Reordering

Compiler có thể reorder:

```text
a = f()
b = g()
```

nếu:

```text
f/g
```

không có observable ordering dependency.

Nhưng không được reorder qua:

```text
atomic ordering
volatile
synchronization
IO contract
FFI observable operation
```

---

# 25. Memory ordering

Đây là nơi Atomic-001 kết nối trực tiếp optimizer.

Ví dụ:

```text
atomic.store(x, 1, Release)
```

không thể được compiler biến thành ordinary store.

Và:

```text
Acquire
```

không được loại bỏ nếu semantics yêu cầu synchronization.

---

# 26. `volatile` không phải atomic

Optimizer phải phân biệt:

```text
volatile
atomic
normal memory
```

### Normal

Có thể reorder/eliminate/cache.

### Atomic

Phải tuân memory ordering.

### Volatile

Phải giữ observable machine access nhưng không tạo inter-thread synchronization.

---

# 27. Bounds-check elimination

Axiom có bounds-safe arrays/slices.

Ví dụ:

```text
for i in 0..len(a) {
    sum += a[i]
}
```

Compiler nên chứng minh:

```text
0 <= i < len(a)
```

và eliminate check trong loop.

Kết quả:

```text
safe source
→ machine code gần như raw pointer loop
```

Đây là một optimization cực kỳ quan trọng.

---

# 28. Không cần `unsafe` để có tốc độ

Đây phải là mục tiêu:

```text
safe loop
```

sau optimization:

```text
pointer arithmetic
load
add
branch
```

nhưng safety đã được chứng minh ở compile time.

---

# 29. Loop optimization

Cho phép:

```text
loop invariant code motion
strength reduction
induction variable elimination
unrolling
peeling
fusion
fission
vectorization
```

miễn semantic contract được giữ.

---

# 30. Vectorization

Ví dụ:

```text
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Nếu regions:

```text
out DISJOINT a
out DISJOINT b
```

compiler có thể vectorize.

```text
AVX2
AVX-512
NEON
SVE
```

tùy target.

Không cần programmer viết intrinsic trong trường hợp thông thường.

---

# 31. Nếu overlap?

Ví dụ:

```text
a = out
```

compiler không được tự vectorize nếu write/read dependency làm thay đổi semantics.

Capability verifier/alias analysis phải cung cấp fact.

---

# 32. Devirtualization

Dynamic dispatch:

```text
x.draw()
```

nếu compiler chứng minh concrete type:

```text
x = Circle
```

có thể biến:

```text
vtable call
```

thành:

```text
Circle.draw
```

Sau đó inline.

Đây là một optimization rất đáng giá.

---

# 33. Generic code

Generic:

```text
fn process<T: Trait>(x: T)
```

đã static dispatch.

Optimizer có thể:

```text
specialize
inline
constant propagate
vectorize
```

sau monomorphization.

---

# 34. Closure optimization

```text
let f = |x| x + 1
```

không có nghĩa:

```text
heap allocate closure object
```

Nếu closure không escape:

```text
closure → inline
```

thậm chí:

```text
closure object → eliminated
```

---

# 35. Captures

Ví dụ:

```text
let x = 10
let f = |y| x + y
```

Compiler có thể biến thành:

```text
fn(y) -> 10 + y
```

nếu `x` constant.

Nếu capture runtime value:

```text
closure environment
```

có thể được:

```text
register
stack
inline field
heap
```

tùy escape.

---

# 36. Escape analysis

Đây sẽ là một compiler subsystem chính thức:

```text
EscapeAnalysis
```

phân loại:

```text
NO_ESCAPE
CALL_ESCAPE
THREAD_ESCAPE
HEAP_ESCAPE
GLOBAL_ESCAPE
UNKNOWN
```

Nó quyết định:

- stack vs dynamic storage;
- scalarization;
- closure allocation;
- temporary lifetime;
- buffer placement.

---

# 37. Async optimization

Async Future:

```text
async fn foo()
```

không nhất thiết tạo heap allocation.

Nếu:

```text
foo().await
```

compiler có thể inline state machine.

Nếu Future không escape:

```text
Future object → stack/register
```

Nếu spawn:

```text
spawn(foo())
```

thì scheduler cần persistent task state.

---

# 38. Task allocation

Ngay cả:

```text
spawn(foo())
```

cũng không nhất thiết:

```text
malloc
```

Scheduler có thể sử dụng:

- intrusive task;
- task pool;
- arena;
- stack;
- embedded state.

Runtime policy quyết định.

---

# 39. Tail call

Compiler có thể biến:

```text
fn loop(...) {
    return next(...)
}
```

thành tail call nếu ABI/target cho phép.

Nhưng Axiom không nên đảm bảo:

```text
tail recursion = always O(1) stack
```

trừ khi có semantic construct riêng.

Có thể sau này thêm:

```text
loop
```

cho guaranteed iteration.

---

# 40. PGO

PGO nên là compiler optimization, không phải language semantics.

```text
axiom build --profile=...
axiom build --use-profile=...
```

Profile có thể hướng:

- inlining;
- branch layout;
- hot/cold splitting;
- function ordering;
- vectorization;
- register allocation.

Không thay đổi semantics.

---

# 41. LTO

Axiom compiler sở hữu object/linker nên LTO có thể tích hợp:

```text
MIR/LIR
   ↓
cross-module optimization
   ↓
machine code
```

Không cần external LLVM.

---

# 42. Nhưng debug/release phải cùng semantics

Điều này cực kỳ quan trọng.

```text
debug
release
```

có thể khác:

- performance;
- inlining;
- allocation;
- checks;
- code layout.

Nhưng không được khác **defined semantics** của safe program.

---

# 43. Bounds checking và release

Không nên có:

```text
debug → check
release → UB
```

như một semantics mặc định.

Thay vào đó:

```text
debug:
    check + diagnostic

release:
    check
    hoặc
    proven elimination
```

Nếu compiler không chứng minh được:

```text
check remains
```

---

# 44. Trap profile

Có thể có:

```text
@unchecked
```

hoặc unsafe primitive cho programmer thực sự muốn bỏ bounds check.

Nhưng đó là explicit unsafe/system-level choice.

Không:

```text
-O3 = unsafe semantics
```

---

# 45. Integer overflow optimization

Ví dụ:

```text
i32 + i32
```

nếu semantics là checked:

compiler phải preserve trap/error semantics.

Nếu:

```text
wrapping_add
```

compiler được optimize modulo arithmetic.

Nếu:

```text
saturating_add
```

compiler phải preserve saturation.

Điều này tránh C-style optimizer assumptions.

---

# 46. Alias analysis không được dựa vào UB giả

Compiler không được làm:

```text
assume pointers don't alias
```

chỉ vì code “thường không nên alias”.

Nó phải có fact từ:

```text
ownership
view
mut_view
regions
unique storage
```

hoặc explicit unsafe contract.

---

# 47. Memory model

Đây là phần cần freeze:

### Safe Axiom

Không có data race.

### Atomic

Synchronization rõ ràng.

### Unsafe

Programmer chịu trách nhiệm cho raw-memory invariants.

### Volatile

Machine-observable memory operation.

Nhưng:

> Compiler vẫn phải giữ semantics của valid program.

---

# 48. Undefined behavior nên cực kỳ hẹp

Tôi đề xuất safe Axiom có các loại failure:

```text
Compile-time error
Runtime panic
Runtime trap
Result error
```

thay vì UB.

UB chủ yếu nằm ở:

```text
unsafe machine-level misuse
FFI contract violation
invalid external memory
invalid platform assumptions
```

---

# 49. Điều này làm optimizer yếu hơn C ở một số trường hợp?

Có thể.

Nhưng compiler có một nguồn thông tin C thường thiếu:

```text
Ownership
Capability
Region
Provenance
Send/Share
Type identity
```

Nên Axiom có thể lấy lại rất nhiều optimization freedom một cách **được chứng minh**.

---

# 50. Ví dụ rất quan trọng

```text
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..a.len() {
        out[i] = a[i] + b[i]
    }
}
```

Compiler biết:

```text
a READ
b READ
out WRITE
```

Nếu API/analysis chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

thì:

```text
bounds checks
alias checks
```

có thể biến mất.

Sau đó:

```text
vector load
vector load
vector add
vector store
```

Đây chính xác là kiểu **safe high-level code → low-level machine code** mà Axiom nên hướng tới.

---

# 51. Optimization phases

Pipeline nên freeze thành:

```text
Verified MIR
      ↓
Semantic Optimization
      ├── constant propagation
      ├── ownership simplification
      ├── copy/move elimination
      ├── lifetime shortening
      ├── alias/region analysis
      ├── bounds analysis
      ├── escape analysis
      ├── devirtualization
      └── generic specialization
      ↓
ABI MIR
      ↓
Axiom LIR
      ↓
LIR Optimization
      ├── CFG
      ├── SSA
      ├── GVN
      ├── LICM
      ├── DCE
      ├── loop optimization
      └── vectorization preparation
      ↓
Machine IR
      ↓
Target Optimization
```

---

# 52. SSA

MIR không nhất thiết phải là SSA.

Tôi đề xuất:

```text
MIR
```

giữ semantics gần source/control flow.

Sau đó:

```text
MIR → SSA-form optimization IR
```

để optimizer dễ làm:

- constant propagation;
- GVN;
- DCE;
- LICM;
- range analysis.

Sau optimization:

```text
SSA → lowerable LIR
```

---

# 53. Không để SSA lộ ra programmer

SSA là compiler implementation detail.

Programmer không cần biết:

```text
x1
x2
x3
phi
```

---

# 54. `noalias` internal fact

Compiler có thể có:

```text
NoAlias(a,b)
```

trong internal IR.

Nhưng source v1 không có:

```text
restrict
```

đúng với quyết định trước đây.

---

# 55. `noalias` không phải assumption tùy tiện

Chỉ tạo fact từ:

```text
exclusive capability
disjoint region
unique owner
verified storage contract
```

hoặc:

```text
unsafe trusted boundary
```

và phải giữ provenance.

---

# 56. Optimization legality checker

Tôi muốn thêm một compiler component:

```text
OptimizationVerifier
```

Mỗi optimization pass phải khai báo:

```text
Preconditions
Transformation
Preserved invariants
```

Ví dụ:

```text
BoundsCheckElimination:
    requires RangeProof
    removes Check
    preserves MemorySafety
```

Điều này rất phù hợp với Axiom compiler architecture.

---

# 57. Không cần formal proof compiler v1

Không cần biến Axiom thành theorem prover.

Có thể dùng:

```text
IR verifier
semantic invariants
differential tests
fuzzing
optimization regression tests
```

sau đó mới formalize các phần quan trọng.

---

# 58. Optimization contract invariants

```text id="h4tyqw"
AOPT-20 — Optimization Must Preserve Observable Semantics

AOPT-21 — Safe Programs Have Defined Semantics

AOPT-22 — Unsafe Does Not Disable All Compiler Verification

AOPT-23 — Proven Facts May Guide Optimization

AOPT-24 — Unproven Alias Disjointness Cannot Be Assumed

AOPT-25 — Ownership May Provide NoAlias Information

AOPT-26 — Capability Analysis May Provide Region Information

AOPT-27 — Allocation May Be Eliminated If Unobservable

AOPT-28 — Storage Placement Is Not Normally Observable

AOPT-29 — Observable Addresses Constrain Optimization

AOPT-30 — Move Does Not Require Physical Copy

AOPT-31 — Copy Does Not Require Physical Copy

AOPT-32 — Return Does Not Require Temporary Copy

AOPT-33 — Caller-Allocated Returns Are Valid

AOPT-34 — Escape Analysis May Change Storage Strategy

AOPT-35 — Stack Promotion Is Semantically Valid When Address Is Not Observable

AOPT-36 — Scalar Replacement Is Allowed When Representation Is Not Observable

AOPT-37 — ABI Contracts Constrain Representation Optimization

AOPT-38 — Bounds Checks May Be Eliminated Only With Valid Proof

AOPT-39 — Atomic Ordering Must Be Preserved

AOPT-40 — Volatile Operations Remain Observable

AOPT-41 — FFI Calls Are Conservative Optimization Boundaries

AOPT-42 — Dynamic Dispatch May Be Devirtualized When Proven

AOPT-43 — Generic Dispatch May Be Fully Erased

AOPT-44 — Closure Allocation May Be Eliminated

AOPT-45 — Async State Allocation May Be Optimized

AOPT-46 — Debug And Release Preserve Defined Semantics

AOPT-47 — Optimization Hints Are Not Semantic Guarantees

AOPT-48 — PGO Does Not Change Program Semantics

AOPT-49 — LTO Does Not Change Program Semantics

AOPT-50 — Optimization Passes Must Preserve IR Invariants
```

---

# 59. Một quyết định kiến trúc rất quan trọng

Từ toàn bộ những gì ta đã thiết kế, tôi đề xuất Axiom **không cố bắt compiler phải chọn một memory model duy nhất ở source level**.

Thay vào đó:

```text
Source semantics
      ↓
Ownership
Capability
Region
Provenance
      ↓
Compiler decides
      ↓
register / stack / inline / dynamic / arena / pool
```

Đây chính là câu trả lời cho vấn đề bạn đặt ra trước đây về **flat memory vs fragmentation**.

**Flat address space không phải memory-management strategy.**

Axiom nên cho allocator/library/compiler quyết định chiến lược.

---

# 60. Và điều này dẫn đến một kiến trúc rất đẹp

Axiom programmer nhìn thấy:

```text
value
owner
view
mut_view
Box
Arc
Arena
Channel
Mutex
Atomic
```

nhưng compiler nhìn thấy:

```text
ownership graph
capability graph
region graph
escape graph
storage graph
execution graph
```

Sau khi verification:

```text
↓
ERASE
```

những graph không cần thiết.

Cuối cùng machine code chỉ còn:

```text
registers
stack
memory
branches
calls
instructions
```

Đây chính là **Abstraction Erasure** mà chúng ta đặt làm một trong các nguyên tắc gốc.

---

## Bước tiếp theo: DATA/CONTROL REPRESENTATION — MIR-001

Bây giờ phần semantic gần như đã chín. Bước tiếp theo tôi sẽ chốt **MIR-001** thật cụ thể:

```text
Block
Value
Place
Projection
Move
Copy
Drop
View
MutView
Load
Store
Call
Return
Branch
Switch
Await
Spawn
Atomic
Lock
Unlock
Alloc
Dealloc
Panic
Trap
```

và quan trọng nhất:

> **MIR sẽ biểu diễn ownership/capability như thế nào mà không biến MIR thành một “borrow checker thứ hai”.**

Đây là cầu nối trực tiếp từ toàn bộ specification hiện tại sang **compiler implementation thực sự**.