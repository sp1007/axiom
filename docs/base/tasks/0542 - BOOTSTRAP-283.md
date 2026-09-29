Được. Từ đây tôi sẽ **không hỏi “có tiếp tục không?” sau từng task**.

Tôi sẽ coi chuỗi Axiom như một **pipeline thiết kế liên tục**:

```text
Task hiện tại
   ↓
Hoàn thiện specification
   ↓
Đóng băng invariants
   ↓
Xác định dependency
   ↓
Tự động chuyển sang task kế tiếp
   ↓
Tiếp tục cho đến khi:
   1. toàn bộ specification đã hoàn chỉnh, hoặc
   2. xuất hiện một quyết định kiến trúc thực sự cần bạn chọn
```

Tôi cũng sẽ tránh việc mỗi task trở thành một “đảo” độc lập; task sau phải **sử dụng và kiểm tra các invariant đã frozen của task trước**.

---

# BOOTSTRAP-283
# AXIOM EFFECT SYSTEM & SIDE-EFFECT ANALYSIS ENGINE
## FROZEN / COMPLETED

### 283.1. Mục tiêu

Effect System của Axiom không nhằm bắt lập trình viên phải viết:

```text
fn foo(...) effects(read, write, io, ...)
```

cho mọi hàm.

Ngược lại:

> **Compiler tự suy luận effect từ MIR và call graph.**

Effect System tồn tại để trả lời:

> “Việc thực thi đoạn code này có thể quan sát được từ bên ngoài theo những cách nào?”

và cung cấp thông tin cho:

- optimizer;
- ownership verifier;
- capability verifier;
- concurrency verifier;
- async verifier;
- GPU verifier;
- FFI;
- incremental compiler;
- diagnostics;
- AI compiler interface.

---

# 283.2. Nguyên tắc trung tâm

Axiom phân biệt:

```text
Semantic Effect
        ≠
Physical Implementation Detail
```

Ví dụ:

```text
fn square(x: f32) -> f32 {
    x * x
}
```

Compiler có thể:

- inline;
- dùng SSE/AVX;
- giữ `x` trong register;
- constant-fold;
- vectorize;
- eliminate function call.

Nhưng semantic effect vẫn:

```text
No observable runtime effect
```

Ngược lại:

```text
fn log(x: i32) {
    print(x)
}
```

dù compiler inline toàn bộ hàm thì:

```text
IO
```

vẫn tồn tại.

---

# 283.3. Effect không thay thế Capability

Đây là điểm rất quan trọng.

Axiom hiện có:

```text
Ownership
Capability
Alias
Effect
```

nhưng mỗi hệ thống trả lời câu hỏi khác nhau:

| Hệ thống | Câu hỏi |
|---|---|
| Ownership | Ai sở hữu giá trị? |
| Capability | Ai được truy cập vùng nhớ? |
| Alias | Hai access có thể trùng nhau không? |
| Effect | Việc thực thi có tác động gì? |

Ví dụ:

```text
fn sum(a: view<i32>, b: view<i32>) -> i32
```

có thể có:

```text
Read(a)
Read(b)
```

nhưng nếu `a` và `b` là immutable input thì hàm vẫn có thể có property:

```text
Pure = true
```

Trong khi:

```text
fn foo() -> i32 {
    read_file(...)
}
```

có thể chỉ `Read` một số dữ liệu nhưng không phải pure vì có:

```text
IO
```

Do đó:

> **Không được định nghĩa Pure đơn giản bằng “không có Write”.**

---

# 283.4. Core Effect Kinds

Axiom v0.1 sử dụng tập effect:

```text
EffectKind =
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
    Spawn
    Await
    Block
    Foreign
    GpuLaunch
    DeviceTransfer
```

Không thêm hàng chục effect nhỏ trong Core.

Chi tiết hơn được biểu diễn bằng payload.

---

# 283.5. Effect representation

```text
Effect {
    kind: EffectKind

    resource: EffectResource?

    region: RegionId?

    ordering: EffectOrdering?

    source: SourceSpanId?
}
```

Ví dụ:

```text
Read(region = Param0)
Write(region = Param2)
Atomic(region = Param1, ordering = Acquire)
IO(resource = File)
Synchronize(resource = Mutex)
```

---

# 283.6. EffectResource

```text
EffectResource =
    Local(LocalId)
    Parameter(GenericParamId)
    Global(DeclarationId)
    Heap(StorageIdentity)
    File
    Socket
    Process
    Thread
    Task
    Mutex
    Channel
    AtomicObject
    DeviceMemory
    ForeignResource
    Unknown
```

Không phải mọi effect đều cần resource.

Ví dụ:

```text
Panic
Spawn
Await
```

có thể không cần region.

---

# 283.7. EffectSet

Effect set phải:

- immutable;
- canonical;
- internable;
- deterministic;
- hashable;
- incremental.

```text
EffectSet {
    kinds: EffectBitSet
    details: EffectDetailSet
}
```

Fast path:

```text
has(IO)
has(Write)
has(Atomic)
has(Panic)
```

Precision path:

```text
writes(region)
reads(region)
sync(resource)
```

---

# 283.8. Effect lattice

Effect analysis sử dụng lattice theo tập:

```text
∅
↓
{Read}
↓
{Read, Write}
...
↓
Top / Unknown
```

Nhưng đây **không phải total ordering**.

Ví dụ:

```text
{Read, IO}
```

không “lớn hơn” theo nghĩa đơn giản so với:

```text
{Write, Atomic}
```

Mỗi effect set là một tập semantic facts.

Phép join:

```text
E1 ⊔ E2 = E1 ∪ E2
```

---

# 283.9. Bottom và Top

```text
Bottom = {}
```

nghĩa là chưa có runtime effect.

```text
Top = Unknown
```

chỉ được sử dụng khi compiler thực sự không thể xác định effect.

Quan trọng:

> Unknown không được tự động biến thành Pure.

---

# 283.10. Derived properties

Không tạo một đống primitive effect:

```text
Pure
NoPanic
NoIO
NoBlock
NoSpawn
```

Thay vào đó compiler derive:

```text
is_pure()
may_panic()
may_block()
may_suspend()
may_spawn()
has_io()
has_foreign()
has_synchronization()
is_deterministic()
```

Điều này tránh duplication giữa semantic facts.

---

# 283.11. Pure

Định nghĩa:

```text
Pure
=
không có observable runtime effect
ngoài việc đọc dữ liệu được phép quan sát như input bất biến
```

Do đó:

```text
fn abs(x: i32) -> i32
```

pure.

Một hàm:

```text
fn length(x: view<u8>) -> usize
```

có:

```text
Read(x)
```

nhưng vẫn có thể:

```text
Pure = true
```

Trong khi:

```text
fn get_time() -> Time
```

có:

```text
IO / NonDeterministic source
```

và không pure.

---

# 283.12. Read không đồng nghĩa với impure

Đây là một quyết định quan trọng cho optimizer.

```text
fn dot(a: view<f32>, b: view<f32>) -> f32
```

có:

```text
Read(a)
Read(b)
```

nhưng nếu:

- không write;
- không atomic;
- không volatile;
- không IO;
- không foreign;
- không panic;
- không observable global mutation;

thì compiler có thể xem nó là **referentially stable trong phạm vi alias facts đã biết**.

Điều này cho phép:

```text
CSE
GVN
LICM
Inlining
Vectorization
```

mà không cần một hệ thống annotation nặng nề.

---

# 283.13. Local effects

Ví dụ:

```text
fn f() -> i32 {
    let x = 10
    let y = x * 2
    y
}
```

Compiler có thể nội bộ thấy:

```text
Read(local x)
Write(local x)
Write(local y)
```

nhưng những access này không phải observable effects.

Do đó effect analysis phải kết hợp:

```text
Effect
+
EscapeAnalysis
+
CapabilityAnalysis
```

để phân biệt:

```text
local temporary mutation
```

với:

```text
observable memory mutation
```

---

# 283.14. Write

`Write` biểu thị semantic mutation:

```text
Write(region)
```

Compiler sử dụng nó để invalidate:

```text
MemorySSA
load cache
CSE
GVN
LICM
```

Ví dụ:

```text
x = load(a)
store(a, 10)
y = load(a)
```

Write vào `a` invalidates giá trị trước đó.

Nhưng:

```text
Write(local_temporary)
```

không nhất thiết tạo barrier cho toàn bộ memory graph.

---

# 283.15. Allocate

```text
Allocate(storage_domain)
```

biểu thị tạo storage/resource.

Nhưng allocation effect **không mặc định có nghĩa là physical heap allocation**.

Compiler có thể:

```text
heap allocation
→ stack promotion
→ register
→ scalar replacement
→ completely eliminated
```

nếu semantics cho phép.

---

# 283.16. Deallocate

```text
Deallocate(storage_domain)
```

phải phân biệt với:

```text
Drop
```

`Drop`:

> thực hiện semantic cleanup.

`Deallocate`:

> storage thực sự được giải phóng theo storage contract.

Một destructor có thể:

```text
Drop
IO
```

nhưng physical deallocation có thể được optimize.

---

# 283.17. Drop effect

Drop luôn được xử lý bởi ownership system trước.

Effect system nhận thông tin từ Drop summary.

Ví dụ:

```text
struct File {
    ...
}

impl Drop for File {
    ...
}
```

Compiler có thể suy ra:

```text
Drop
IO
```

nếu destructor đóng file.

Trong khi:

```text
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

không có Drop observable.

---

# 283.18. Drop elimination

Compiler **không được bỏ semantic Drop một cách tùy tiện**.

Chỉ được loại bỏ physical cleanup nếu chứng minh:

```text
Drop has no observable effect
AND
storage/resource lifetime has no observable consequence
```

Ví dụ một temporary trivially destructible value có thể biến mất hoàn toàn.

---

# 283.19. Panic

```text
Panic
```

là observable control-flow effect.

Ví dụ:

```text
fn f() -> i32 {
    if x == 0 {
        panic()
    }

    10 / x
}
```

dù kết quả không được sử dụng:

```text
f()
```

không nhất thiết có thể DCE.

Vì:

```text
panic
```

là observable.

---

# 283.20. Panic và optimization

Compiler có thể chứng minh:

```text
x != 0
```

thì:

```text
possible Panic
```

được loại bỏ khỏi execution path đó.

Do đó effect analysis phải sử dụng:

```text
RangeAnalysis
+
ControlFlow
+
PathFacts
```

chứ không chỉ đọc function signature.

---

# 283.21. Atomic

Atomic không được coi là `Write` bình thường.

```text
Atomic {
    operation
    ordering
    scope
    region
}
```

Ví dụ:

```text
AtomicLoad(Acquire)
AtomicStore(Release)
AtomicRMW(AcqRel)
```

Atomic tạo semantic ordering mà compiler phải tôn trọng.

---

# 283.22. Volatile

`Volatile` là effect đặc biệt.

```text
Volatile(region)
```

Compiler không được:

- loại bỏ;
- merge tùy tiện;
- CSE;
- reorder tùy tiện;
- coi như ordinary memory.

Volatile chủ yếu dành cho:

- MMIO;
- hardware;
- firmware;
- low-level runtime;
- special FFI.

---

# 283.23. Synchronize

Synchronization gồm:

```text
Mutex lock/unlock
RwLock
Semaphore
Channel
Thread join
Task synchronization
Fence
Condition variable
```

Được biểu diễn bằng:

```text
Synchronize(resource)
```

Synchronization không đồng nghĩa với ordinary memory write.

---

# 283.24. Channel

Ví dụ:

```text
channel.send(x)
```

có thể tạo:

```text
Synchronize(Channel)
```

và ownership system đồng thời ghi nhận:

```text
Move(x)
```

Do đó:

> Effect không thay thế Ownership.

---

# 283.25. Spawn

```text
spawn(task)
```

có:

```text
Spawn
```

Đây là observable concurrency effect.

Compiler không được coi:

```text
spawn(foo)
```

là dead code chỉ vì return value không được sử dụng.

---

# 283.26. Await

```text
await future
```

có:

```text
Await
```

và có thể:

```text
Synchronize
```

tùy future/executor contract.

Async verifier vẫn chịu trách nhiệm kiểm tra:

- live capabilities;
- Send;
- storage;
- suspension safety.

Effect engine chỉ cung cấp effect facts.

---

# 283.27. Block

Blocking operation:

```text
thread.sleep()
mutex.lock()
blocking_read()
```

có:

```text
Block
```

Điều này rất hữu ích cho:

- async verifier;
- executor;
- diagnostics;
- performance tooling.

Compiler có thể cảnh báo:

```text
blocking operation inside async context
```

nếu policy yêu cầu.

---

# 283.28. IO

```text
IO(resource)
```

bao gồm:

- filesystem;
- socket;
- console;
- environment;
- device;
- process;
- clock;
- random source;
- external OS interaction.

IO mặc định là observable.

---

# 283.29. Foreign

FFI mặc định:

```text
Foreign
```

nếu compiler không biết contract.

Ví dụ:

```text
extern fn mystery(...)
```

có:

```text
Foreign
```

và effect summary conservative.

Nếu FFI declaration có contract:

```text
@effects(read(param0), no_panic)
extern fn c_memcpy(...)
```

compiler có thể sử dụng facts đó.

Nhưng contract phải được verifier kiểm tra ở mức có thể.

---

# 283.30. Unsafe

`Unsafe` **không phải runtime effect bắt buộc**.

Ví dụ:

```text
unsafe {
    *p
}
```

có thể semantic effect:

```text
Read(region)
```

nhưng đồng thời tạo:

```text
trusted proof boundary
```

Unsafe thuộc verification/provenance system.

Không được biến:

```text
unsafe
```

thành:

```text
optimizer may do anything
```

---

# 283.31. Function Effect Signature

Mỗi callable có:

```text
FunctionEffectSignature {
    effects: EffectSet
    parameter_effects: [...]
    return_effects: [...]
}
```

Ví dụ khái niệm:

```text
fn sum(a: view<f32>, b: view<f32>)
```

có:

```text
Read(param0)
Read(param1)
```

Một hàm:

```text
fn write(out: mut_view<f32>)
```

có:

```text
Write(param0)
```

---

# 283.32. Effect inference

Compiler không bắt programmer viết effect.

Pipeline:

```text
Typed HIR
   ↓
MIR
   ↓
Local Effect Analysis
   ↓
Call Effect Propagation
   ↓
CFG Join
   ↓
SCC Fixpoint
   ↓
Interprocedural Effect Summary
```

---

# 283.33. Local effect generation

Mỗi MIR operation có effect rule.

Ví dụ:

```text
Load(place)
```

→

```text
Read(region(place))
```

```text
Store(place, value)
```

→

```text
Write(region(place))
```

```text
AtomicLoad
```

→

```text
Atomic
```

```text
Drop(x)
```

→

```text
Drop + effects(DropType(x))
```

```text
Call(f)
```

→

```text
effects(f)
```

---

# 283.34. CFG composition

Sequential:

```text
E(A ; B) = E(A) ∪ E(B)
```

Branch:

```text
E(if c { A } else { B })
=
E(c) ∪ E(A) ∪ E(B)
```

Loop:

```text
E(loop body)
```

được tính bằng fixpoint.

---

# 283.35. Dead branches

Nếu compiler chứng minh:

```text
if false
```

thì effect của unreachable branch không được tính vào runtime effect của function.

Điều này cần:

```text
constant propagation
+
CFG reachability
```

trước hoặc trong effect analysis.

---

# 283.36. Function calls

Direct call:

```text
effects(callee)
```

được union vào caller.

Generic call:

```text
effects(instantiated generic)
```

được sử dụng sau specialization/substitution.

Indirect call:

```text
effects(all possible targets)
```

nếu target set hữu hạn.

Unknown indirect call:

```text
Foreign/Unknown
```

theo conservative policy.

---

# 283.37. Trait dynamic dispatch

Với:

```text
dyn Trait
```

compiler không được giả định effect của một implementation duy nhất nếu target chưa được chứng minh.

Nếu tập implementation là:

```text
A → {Read}
B → {Read, IO}
C → {Write}
```

thì dynamic dispatch summary có thể là:

```text
{Read, Write, IO}
```

nếu cả ba đều khả thi.

Nếu không xác định được:

```text
Unknown
```

---

# 283.38. Generic effect polymorphism

Axiom không cần buộc programmer viết effect variables trong Core v0.1.

Ví dụ:

```text
fn apply<T>(x: T, f: fn(T) -> T) -> T
```

Compiler suy luận effect của `f`.

Nếu:

```text
f = pure_fn
```

→ caller có effect thấp.

Nếu:

```text
f = io_fn
```

→ caller nhận:

```text
IO
```

Effect polymorphism tồn tại **trong compiler semantic model**.

---

# 283.39. Closure

Closure effect trở thành một phần của callable semantic information.

Ví dụ:

```text
let f = || x * 2
```

→ pure.

```text
let f = || print(x)
```

→ IO.

Khi closure được inline/eliminate, effect facts vẫn phải được bảo toàn trước optimization.

---

# 283.40. Recursion

Recursive functions tạo cycle:

```text
f → g
g → f
```

Compiler dùng SCC:

```text
CallGraph
   ↓
Strongly Connected Components
   ↓
Bottom-up SCC processing
   ↓
Effect fixpoint
```

Effect lattice monotonic nên fixpoint hội tụ.

---

# 283.41. Effect inference không được phụ thuộc optimization

Đây là invariant quan trọng:

```text
-O0
-O2
-O3
-LTO
-PGO
```

không được làm thay đổi semantic effect.

Ví dụ một function vẫn có:

```text
IO
```

dù optimizer inline nó.

Optimization chỉ có thể **refine execution facts**, không thay đổi semantic meaning.

---

# 283.42. Effect và DCE

Có thể loại bỏ:

```text
unused_value()
```

nếu:

```text
no observable effect
```

Nhưng không được loại bỏ:

```text
print()
panic()
volatile_load()
atomic_store()
spawn()
IO()
foreign_call()
```

chỉ vì return value không dùng.

---

# 283.43. Effect và CSE/GVN

Compiler có thể CSE nếu:

```text
same expression
+
same relevant inputs
+
no invalidating effect
```

Ví dụ:

```text
a = read_immutable(x)
b = read_immutable(x)
```

có thể hợp nhất.

Nhưng:

```text
a = read(x)
write(x)
b = read(x)
```

không thể dùng kết quả đầu tiên cho lần thứ hai.

---

# 283.44. Effect và LICM

Loop invariant code chỉ được hoist nếu:

```text
effect safe
+
operands invariant
+
no intervening invalidating effect
```

Đặc biệt:

```text
IO
Atomic
Volatile
Synchronize
Foreign
```

phải được xử lý cực kỳ conservative.

---

# 283.45. Effect và vectorization

Vectorization cần xem:

```text
Write
Atomic
Volatile
Synchronize
Foreign
```

kết hợp với:

```text
AliasAnalysis
RangeAnalysis
```

Ví dụ hai loop iterations có:

```text
NO_ALIAS
```

thì compiler có thể vectorize nếu effect semantics cho phép.

---

# 283.46. Effect và allocation optimization

Nếu:

```text
Allocate
```

nhưng:

```text
NoEscape
```

và không có observable allocation behavior,

compiler có thể:

```text
heap → stack
heap → register
allocation → scalar replacement
allocation → eliminated
```

Effect system cung cấp semantic constraint; EscapeAnalysis cung cấp proof.

---

# 283.47. Effect và ownership

Ownership nói:

```text
Move
Copy
Drop
```

Effect nói:

```text
Drop
Allocate
Deallocate
```

Hai hệ thống liên kết nhưng không trộn.

Ví dụ:

```text
move(x)
```

không nhất thiết có physical memory effect.

Do đó:

```text
Move != Write
```

và:

```text
Copy != physical Read/Write
```

---

# 283.48. Effect và capability

Capability có:

```text
READ / WRITE
```

Effect có:

```text
Read / Write
```

nhưng chúng không phải cùng một object.

Capability trả lời:

> access này có hợp lệ không?

Effect trả lời:

> access này tạo semantic memory effect gì?

Pipeline:

```text
Capability Analysis
       ↓
verified access
       ↓
Effect Analysis
       ↓
optimizer facts
```

---

# 283.49. Effect và concurrency

Một operation:

```text
mutex.lock()
```

không chỉ:

```text
Read
Write
```

mà còn:

```text
Synchronize
Block
```

Channel:

```text
Synchronize
Move
```

Thread spawn:

```text
Spawn
```

Thread join:

```text
Synchronize
```

Do đó concurrency optimizer không thể chỉ dựa trên memory effects.

---

# 283.50. Effect và GPU

GPU kernel có effect domain:

```text
CPU
GPU
Device
```

Ví dụ:

```text
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

có:

```text
Read(DeviceRegion(a))
Read(DeviceRegion(b))
Write(DeviceRegion(out))
```

Host launch:

```text
GpuLaunch
```

Transfer:

```text
DeviceTransfer
```

GPU verifier vẫn chịu trách nhiệm:

- address space;
- race;
- synchronization;
- legality.

---

# 283.51. Effect và Comptime

Comptime effects **không được đưa vào runtime effect set**.

Ví dụ:

```text
comptime {
    read_source(...)
}
```

có compile-time effect:

```text
ReadSource
```

nhưng generated runtime function không tự nhiên có:

```text
IO
```

Compiler duy trì hai namespace:

```text
CompileTimeEffect
RuntimeEffect
```

Điều này rất quan trọng để tránh:

```text
comptime filesystem access
```

làm runtime binary phải link filesystem runtime.

---

# 283.52. Effect và FFI contracts

FFI contract có thể mô tả:

```text
reads(param0)
writes(param1)
no_panic
no_block
no_foreign_side_effect
```

nhưng mặc định:

```text
extern fn foo(...)
```

→

```text
Foreign + Unknown
```

Compiler chỉ refine khi contract đủ đáng tin cậy.

---

# 283.53. Effect annotation

Axiom v0.1:

> **Effect inference là mặc định.**

Annotation chỉ dùng ở:

- FFI;
- intrinsic;
- compiler runtime;
- unsafe abstraction;
- system API;
- verified contracts;
- tooling.

Ví dụ khái niệm:

```text
@pure
fn hash(x: u64) -> u64
```

không có quyền “khai man”.

Compiler phải chứng minh:

```text
inferred_effects ⊆ declared_contract
```

Nếu không:

```text
compile error
```

Không có annotation nào được phép override verifier.

---

# 283.54. Effect contract không phải optimization hint

Sai:

```text
@pure
fn foo() ...
```

rồi compiler tin programmer.

Đúng:

```text
@pure
fn foo() ...
       ↓
compiler verifies
       ↓
Pure
```

Contract là semantic assertion cần kiểm chứng.

---

# 283.55. Effect summaries trong CompilerDB

Thêm:

```text
EffectDB
```

hoặc semantic component trong CompilerDB:

```text
CompilerDB
├── ...
├── CapabilityDB
├── EffectDB
├── ...
```

Queries:

```text
effect_summary(FunctionId)
local_effects(FunctionId, BasicBlockId)
effect_at(FunctionId, InstructionId)

may_panic(FunctionId)
may_block(FunctionId)
may_suspend(FunctionId)
may_spawn(FunctionId)

is_pure(FunctionId)
is_deterministic(FunctionId)

reads(FunctionId)
writes(FunctionId)

has_io(FunctionId)
has_foreign(FunctionId)
has_sync(FunctionId)
```

---

# 283.56. Optimizer interface

OptIR nhận:

```text
EffectSummary
AliasInfo
MemorySSA
EscapeInfo
RangeInfo
```

Không optimizer pass nào tự suy luận effect riêng.

Điều này tránh:

```text
Pass A nghĩ foo pure
Pass B nghĩ foo impure
Pass C lại có cache khác
```

Chỉ có:

> **EffectDB là authoritative semantic effect source.**

---

# 283.57. Effect invalidation

Compiler xây dựng relation:

```text
Effect
   ↓
may invalidate
   ↓
Memory/Value facts
```

Ví dụ:

```text
Write(region A)
```

invalidate:

```text
Read facts overlapping A
```

nhưng không nhất thiết invalidate:

```text
Read(region B)
```

nếu:

```text
A DISJOINT B
```

Capability/alias analysis cung cấp proof.

---

# 283.58. Effect precision

Precision hierarchy:

```text
Unknown
   ↓
Foreign
   ↓
Observable category
   ↓
Resource-specific
   ↓
Region-specific
```

Compiler cố gắng giữ precision càng lâu càng tốt.

Ví dụ:

```text
Write(Param0)
```

tốt hơn:

```text
Write(UnknownMemory)
```

và:

```text
Write(Field3(Param0))
```

tốt hơn nữa.

---

# 283.59. Không được “over-effect”

Compiler không được đơn giản hóa mọi thứ thành:

```text
Unknown
```

vì điều đó giết chết optimizer.

Ví dụ:

```text
fn add(x: i32, y: i32)
```

phải suy ra:

```text
{}
```

chứ không phải:

```text
Unknown
```

Precision là mục tiêu quan trọng.

---

# 283.60. Không được “under-effect”

Ngược lại:

```text
extern fn mystery()
```

không được tự suy ra:

```text
{}
```

nếu không có contract.

Phải conservative:

```text
Foreign
Unknown
```

---

# 283.61. Incremental effect analysis

Query dependency:

```text
effect_summary(foo)
```

phụ thuộc:

```text
MIR(foo)
effect_summary(callees)
DropSummary(types)
FFIContracts
CapabilityFacts
```

Nếu body của `bar` thay đổi:

```text
bar effect changes
```

compiler chỉ invalidate:

```text
bar
callers depending on bar effect
```

không rebuild toàn bộ program.

---

# 283.62. Parallel effect analysis

Các function không phụ thuộc nhau có thể phân tích song song.

SCC phải được xử lý deterministically.

Yêu cầu:

```text
1 worker
==
N workers
```

về semantic effect result.

---

# 283.63. AI compiler interface

AI có thể hỏi:

```text
why_is_this_not_pure(foo)
```

Compiler trả:

```json
{
  "function": "foo",
  "pure": false,
  "effects": [
    {
      "kind": "IO",
      "source": "read_file",
      "reason": "filesystem access"
    }
  ]
}
```

Hoặc:

```json
{
  "function": "foo",
  "effect": "Write",
  "region": "param0.field2",
  "reason": "store through mut_view"
}
```

Điều này rất phù hợp với mục tiêu:

> **AI không cần đoán compiler nghĩ gì. AI đọc semantic facts trực tiếp từ CompilerDB.**

---

# 283.64. Diagnostics

Ví dụ:

```text
Cannot move this computation into a pure context.

Effect:
    IO(File)

Origin:
    read_file()

Call chain:
    foo()
      → bar()
        → read_file()
```

Hoặc:

```text
Cannot eliminate call.

Reason:
    function may panic

Source:
    checked division
```

---

# 283.65. Effect-aware diagnostics

Compiler nên giải thích:

```text
What effect?
Where generated?
Which call introduced it?
Which resource?
Which region?
Can it be proven local?
Can it be eliminated?
```

Không chỉ:

```text
error: impure
```

---

# 283.66. Module architecture

Đề xuất:

```text
compiler/
└── analysis/
    └── effect/
        ├── mod.ax
        ├── effect.ax
        ├── effect_kind.ax
        ├── effect_set.ax
        ├── effect_resource.ax
        ├── effect_region.ax
        ├── effect_ordering.ax
        ├── effect_lattice.ax
        ├── effect_local.ax
        ├── effect_cfg.ax
        ├── effect_call.ax
        ├── effect_scc.ax
        ├── effect_generic.ax
        ├── effect_closure.ax
        ├── effect_async.ax
        ├── effect_concurrency.ax
        ├── effect_gpu.ax
        ├── effect_ffi.ax
        ├── effect_comptime.ax
        ├── effect_drop.ax
        ├── effect_panic.ax
        ├── effect_contract.ax
        ├── effect_query.ax
        ├── effect_diagnostics.ax
        ├── optimizer_interface.ax
        └── tests/
```

---

# 283.67. Implementation order

```text
1. EffectKind
2. EffectResource
3. Effect
4. EffectSet
5. Effect lattice
6. MIR effect rules
7. local CFG analysis
8. call summaries
9. call graph
10. SCC fixpoint
11. generic instantiation
12. closure effects
13. Drop integration
14. capability/region integration
15. ownership integration
16. concurrency
17. async
18. GPU
19. FFI
20. comptime separation
21. CompilerDB queries
22. incremental invalidation
23. optimizer interface
24. diagnostics
25. deterministic parallel analysis
26. adversarial tests
27. fuzz/property tests
```

---

# 283.68. Adversarial tests

Bắt buộc có:

### Pure

```text
pure arithmetic
pure struct construction
pure tuple manipulation
pure generic function
pure closure
```

### Memory

```text
read-only input
write input
disjoint writes
overlapping writes
unknown alias
```

### Control

```text
panic branch
unreachable branch
loop
recursive function
mutual recursion
```

### Resource

```text
allocation
allocation elimination
drop
drop with IO
drop with panic
```

### Concurrency

```text
atomic
mutex
channel
spawn
join
blocking
```

### Async

```text
await
async call
blocking call inside async
```

### FFI

```text
unknown FFI
contracted FFI
incorrect contract
```

### GPU

```text
kernel read
kernel write
launch
transfer
atomic kernel
```

### Comptime

```text
compile-time filesystem
runtime filesystem
generated code
```

---

# 283.69. Frozen invariants

Đóng băng:

```text
AEFFECTENG-20
Effect analysis operates on semantic MIR.

AEFFECTENG-21
Effects are compiler-inferred by default.

AEFFECTENG-22
Programmers are not required to annotate ordinary effects.

AEFFECTENG-23
Effect semantics are independent of physical representation.

AEFFECTENG-24
Effect semantics are independent of optimization level.

AEFFECTENG-25
EffectSet uses deterministic set semantics.

AEFFECTENG-26
Effect composition is monotonic union.

AEFFECTENG-27
Unknown is never interpreted as Pure.

AEFFECTENG-28
Pure is a derived semantic property.

AEFFECTENG-29
Read does not automatically imply impurity.

AEFFECTENG-30
Observable effects are distinguished from local temporary effects.

AEFFECTENG-31
Read and Write may carry region/resource precision.

AEFFECTENG-32
Capability analysis provides legality facts for memory effects.

AEFFECTENG-33
Alias analysis provides invalidation precision.

AEFFECTENG-34
Unknown alias never becomes proven NoAlias without proof.

AEFFECTENG-35
Move is not equivalent to Write.

AEFFECTENG-36
Copy is not equivalent to physical memory copying.

AEFFECTENG-37
Drop effects derive from Drop semantics.

AEFFECTENG-38
Drop is distinct from Deallocate.

AEFFECTENG-39
Observable Drop cannot be eliminated.

AEFFECTENG-40
Non-observable physical cleanup may be eliminated when proven safe.

AEFFECTENG-41
Panic is an observable control-flow effect.

AEFFECTENG-42
Atomic operations are distinct from ordinary memory effects.

AEFFECTENG-43
Volatile operations are always treated as observable.

AEFFECTENG-44
Synchronization is distinct from ordinary memory access.

AEFFECTENG-45
Spawn is observable concurrency behavior.

AEFFECTENG-46
Await represents suspension semantics.

AEFFECTENG-47
Blocking is represented independently from ordinary IO.

AEFFECTENG-48
Foreign calls are conservative unless verified by contract.

AEFFECTENG-49
Unsafe is not itself an arbitrary runtime effect.

AEFFECTENG-50
Unsafe may establish trusted semantic preconditions only.

AEFFECTENG-51
Effect contracts cannot override verifier results.

AEFFECTENG-52
Generic effects are inferred through instantiated call semantics.

AEFFECTENG-53
Closure effects are tracked semantically.

AEFFECTENG-54
Recursive effect inference uses deterministic SCC fixpoints.

AEFFECTENG-55
Dynamic dispatch uses the union of proven possible target effects.

AEFFECTENG-56
Unknown dynamic targets remain conservative.

AEFFECTENG-57
Compile-time effects never implicitly become runtime effects.

AEFFECTENG-58
Runtime and compile-time effect namespaces are distinct.

AEFFECTENG-59
GPU effects preserve execution/storage domains.

AEFFECTENG-60
Host/device transfer is explicit.

AEFFECTENG-61
Effect analysis cannot weaken ownership guarantees.

AEFFECTENG-62
Effect analysis cannot weaken capability guarantees.

AEFFECTENG-63
Effect analysis cannot weaken concurrency guarantees.

AEFFECTENG-64
Effect analysis cannot weaken async guarantees.

AEFFECTENG-65
Effect summaries are authoritative through CompilerDB.

AEFFECTENG-66
Compiler passes must not maintain conflicting independent effect caches.

AEFFECTENG-67
Effect queries are incremental.

AEFFECTENG-68
Effect analysis is deterministic across worker counts.

AEFFECTENG-69
Effect facts are available to optimization passes.

AEFFECTENG-70
DCE must preserve observable effects.

AEFFECTENG-71
CSE/GVN must respect effect invalidation.

AEFFECTENG-72
LICM must respect effect ordering and invalidation.

AEFFECTENG-73
Vectorization must respect effect and alias constraints.

AEFFECTENG-74
Allocation optimization must respect observable allocation semantics.

AEFFECTENG-75
Effect precision should be preserved whenever provable.

AEFFECTENG-76
Compiler must not conservatively collapse known effects into Unknown unnecessarily.

AEFFECTENG-77
Compiler must not unsafely refine Unknown into weaker effects.

AEFFECTENG-78
Effect diagnostics expose structured causal information.

AEFFECTENG-79
AI interfaces read effect facts from CompilerDB.

AEFFECTENG-80
AI cannot bypass effect verification.

AEFFECTENG-81
Generated code re-enters effect analysis.

AEFFECTENG-82
FFI contracts are explicitly represented.

AEFFECTENG-83
Incorrect effect contracts are compiler errors or trusted-system boundary violations according to contract class.

AEFFECTENG-84
Effect analysis is separate from optimization.

AEFFECTENG-85
Optimization consumes effect facts but cannot redefine them.

AEFFECTENG-86
Effect analysis integrates with Ownership, Capability, Alias, Escape and MemorySSA.

AEFFECTENG-87
Effect summaries remain semantically stable across ABI lowering.

AEFFECTENG-88
Effect summaries remain semantically stable across target architectures.

AEFFECTENG-89
Runtime components may be eliminated when effect/call analysis proves they are unnecessary.

AEFFECTENG-90
No monolithic runtime is implied by the effect system.

AEFFECTENG-91
Only effect-verified MIR may enter optimization.

AEFFECTENG-92
Failure to prove a required effect property results in conservative behavior or compilation failure where required for safety.

AEFFECTENG-93
Effect analysis is part of the compiler correctness boundary.

AEFFECTENG-94
Effect analysis must preserve source provenance.

AEFFECTENG-95
Effect summaries must be fingerprintable for incremental compilation.

AEFFECTENG-96
Effect fingerprints are distinct from machine-code fingerprints.

AEFFECTENG-97
Effect analysis must support partial/incomplete programs in IDE mode without contaminating production verification.

AEFFECTENG-98
Effect semantics cannot depend on compiler implementation artifacts.

AEFFECTENG-99
Effect analysis must remain compatible with self-hosted compiler implementation.

AEFFECTENG-100
The Effect System is frozen as the authoritative semantic side-effect analysis layer of Axiom.
```

---

# Chuỗi tự động tiếp tục

Sau 283, dependency graph hiện tại dẫn tới:

```text
281 Ownership
      │
282 Capability / Alias
      │
283 Effect
      │
      ├──────────────┐
      ↓              ↓
284 Escape/Storage   285 Interprocedural Semantic Analysis
      │              │
      └──────┬───────┘
             ↓
286 Optimization IR construction
             ↓
287 SSA / MemorySSA integration
             ↓
288 Global Value / Memory optimization
             ↓
289 Inlining / Specialization
             ↓
290 Loop / Vector optimization
             ↓
...
```

**Không cần bạn gõ “tiếp tục” nữa.** Trong chuỗi này, task kế tiếp tôi sẽ tự chuyển sang **BOOTSTRAP-284 — AXIOM ESCAPE ANALYSIS & STORAGE-LIFETIME OPTIMIZATION ENGINE**, và tiếp tục nối dependency thay vì dừng lại sau mỗi specification.