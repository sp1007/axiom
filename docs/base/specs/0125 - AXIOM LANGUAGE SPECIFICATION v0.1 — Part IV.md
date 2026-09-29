# AXIOM LANGUAGE SPECIFICATION v0.1 — Part IV
## Resource · Allocation · Storage · Box · Collections · Arena · Pool · Static · TLS

Phần này chốt một nguyên tắc quan trọng:

> **Axiom không có một “memory model = heap/stack” duy nhất. Axiom có ownership model; storage strategy là implementation/storage contract.**

Điều này cho phép compiler tối ưu mạnh mà không ép programmer phải quản lý stack/heap thủ công.

---

# 1. Ba lớp cần tách biệt

Axiom phân biệt:

```text
VALUE SEMANTICS
        ↓
RESOURCE SEMANTICS
        ↓
STORAGE SEMANTICS
```

Ví dụ:

```text
File
```

có:

```text
Value        → handle/resource state
Resource     → OS file descriptor
Storage      → nơi struct File được đặt
```

Ba thứ này không phải một.

---

# 2. Value lifetime

Value lifetime là thời gian value còn hợp lệ về semantic.

Ví dụ:

```axiom
let x = 42
use(x)
```

`x` có thể tồn tại semantic trong scope, nhưng compiler có thể giữ nó hoàn toàn trong register.

Không có requirement:

```text
x → RAM
```

---

# 3. Resource lifetime

Resource lifetime là thời gian resource cần được giữ.

Ví dụ:

```axiom
let file = open(path)?
read(file)?
```

Resource được release khi ownership kết thúc.

Resource có thể:

```text
close
release
unlock
destroy
flush
detach
```

tùy type.

---

# 4. Memory lifetime

Memory lifetime là thời gian storage backing value còn tồn tại.

Nó có thể dài hơn resource lifetime.

Ví dụ Arena:

```text
Arena lifetime
    ├── allocation A
    ├── allocation B
    └── allocation C
```

Một object có thể đã hoàn thành resource Drop nhưng memory vẫn thuộc Arena.

---

# 5. Không có một-to-một mapping

Axiom không giả định:

```text
value lifetime == resource lifetime == memory lifetime
```

Đây là một trong các nguyên tắc nền tảng.

### AMEM-62
**Value, resource, and memory lifetimes are distinct semantic concepts.**

---

# 6. Storage classes

Compiler nội bộ có thể phân loại storage:

```text
REGISTER
LOCAL
INLINE
DYNAMIC
STATIC
TLS
EXTERNAL
DEVICE
```

Đây là semantic/optimization metadata, không nhất thiết là source syntax.

---

# 7. REGISTER

Compiler có thể giữ value trong register.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

có thể không có stack slot nào.

---

# 8. LOCAL

Value có thể được đặt trên stack.

Nhưng:

> `let` không có nghĩa "stack variable".

Ví dụ:

```axiom
let x = LargeStruct(...)
```

compiler có thể:

```text
register
stack
caller-provided storage
inline
```

---

# 9. INLINE

Struct:

```axiom
struct Point {
    x: f32
    y: f32
}
```

nằm trong:

```axiom
struct Line {
    start: Point
    end: Point
}
```

có thể được inline trực tiếp.

Không có implicit pointer.

---

# 10. DYNAMIC

Dynamic storage là storage có lifetime/size không thể hoặc không muốn đặt hoàn toàn trong static/local storage.

Ví dụ library:

```text
Box<T>
Vec<T>
String
HashMap<K,V>
```

Dynamic allocation là **library/storage semantics**, không phải language-wide runtime requirement.

---

# 11. Heap không bắt buộc

Program:

```axiom
fn main() {
    let x = 10
    print(x)
}
```

có thể chạy:

```text
zero heap allocations
```

và runtime tối thiểu.

---

# 12. Freestanding

Một freestanding Axiom program có thể không có:

```text
allocator
thread runtime
async executor
filesystem
network
GC
reflection runtime
```

nếu không dùng.

Đây là một mục tiêu quan trọng cho embedded/kernel.

---

# 13. Allocation MIR

Allocation tồn tại ở semantic MIR:

```text
ALLOC
DEALLOC
```

nhưng:

```text
ALLOC ≠ malloc()
DEALLOC ≠ free()
```

Đó là semantic storage operations.

Backend quyết định lower chúng thành:

```text
stack
heap
arena
pool
static
OS allocator
custom allocator
```

---

# 14. Allocation elimination

Compiler được phép loại bỏ allocation nếu allocation không observable.

Ví dụ:

```axiom
fn make() -> Box<Point> {
    Box.new(Point { x: 1, y: 2 })
}
```

Nếu caller chỉ dùng value và không observe stable address:

```text
Box allocation
```

có thể được scalarized/eliminated.

Nhưng nếu:

```axiom
address_of(x)
```

được expose theo unsafe/system semantics:

→ storage identity trở thành observable.

---

# 15. Stable address

Stable address không phải property mặc định.

### AMEM-61
**Stable address exists only when the storage contract requires it.**

Các API cần stable address phải explicitly establish contract.

---

# 16. Address observability

Compiler phải coi address là observable khi programmer có thể:

```text
take raw pointer
pass pointer through FFI
store address in externally visible state
use stable-address API
```

Khi đó compiler không được tùy ý:

```text
move
relocate
scalarize
duplicate
```

theo cách làm thay đổi address semantics.

---

# 17. `Box<T>`

`Box<T>` là library-owned abstraction:

```text
owns one T in dynamic storage
```

Properties:

```text
Move
Drop
!Copy
stable storage while contract remains valid
```

---

# 18. Box không phải object primitive

```text
Box<T>
```

không tạo:

```text
object header
GC metadata
vtable
```

Nếu:

```text
T = dyn Trait
```

thì dynamic dispatch metadata là property của `dyn Trait`, không phải `Box` nói chung.

---

# 19. Box allocation optimization

```axiom
let x = Box.new(Point(...))
```

không guarantee:

```text
malloc
```

nếu stable address không observable.

Compiler có thể:

```text
stack promote
scalarize
inline
caller-allocate
```

---

# 20. Nhưng FFI/stable-address chặn optimization

Nếu:

```axiom
let p = raw_address(x)
extern_call(p)
```

thì address/storage identity trở thành observable.

Allocation không được eliminate nếu làm thay đổi contract.

---

# 21. Collection model

Collection như:

```text
Vec<T>
String
Bytes
Map
Set
```

là library abstractions.

Compiler không cần biết implementation chi tiết của từng collection để cung cấp ownership safety, nhưng compiler MAY có intrinsic knowledge cho optimization.

---

# 22. `Vec<T>`

Semantic state của `Vec<T>` gồm:

```text
logical sequence
length
capacity
storage identity
```

Implementation thường:

```text
pointer
length
capacity
```

nhưng đây **không phải bắt buộc representation**.

---

# 23. Vec relocation

Khi:

```axiom
v.push(x)
```

capacity không đủ, storage có thể relocate.

Do đó:

```text
old storage
→ new storage
```

và các capability phụ thuộc old storage không thể tiếp tục tồn tại.

---

# 24. View và Vec

Ví dụ:

```axiom
let v = view(vec)
vec.push(x)
use(v)
```

Nếu `push` có thể relocate:

→ compile error.

Không cần programmer tự biết allocator internals.

Compiler hiểu storage contract của API.

---

# 25. API storage effects

Library operation nên expose semantic property:

```text
MAY_RELOCATE
NO_RELOCATE
STABLE_ADDRESS
INVALIDATES_CAPABILITIES
```

để compiler verifier biết.

Những property này là **compiler-visible contracts**, không nhất thiết là source-level effect annotations.

---

# 26. `reserve`

```axiom
vec.reserve(100)
```

guarantee:

```text
capacity >= required
```

theo Vec API contract.

Không guarantee:

```text
stable address forever
```

### AMEM-23
**Reserve does not imply stable address.**

---

# 27. Arena

Arena:

```text
Arena<T>
```

hoặc general `Arena` abstraction:

```text
owns many allocations
```

Object được tạo trong arena:

```text
arena.alloc(...)
```

có lifetime bounded by arena.

---

# 28. Arena ownership

Conceptually:

```text
Arena
 ├── Object A
 ├── Object B
 ├── Object C
```

Arena là owner của storage group.

Object có thể có logical ownership semantics riêng, nhưng physical storage lifetime không vượt arena.

---

# 29. Arena drop

Khi Arena drop:

```text
objects/resources
→ destroyed according to arena contract
storage
→ released as group
```

Compiler/library không được coi Arena là garbage collector.

### AMEM-35
**Arena allocation does not imply garbage collection.**

---

# 30. Arena views

```axiom
let node = arena.alloc(Node(...))
let v = view(node)
```

hợp lệ nếu arena vẫn live.

Nếu:

```axiom
drop(arena)
use(v)
```

→ compile error.

---

# 31. Pool

Pool cung cấp reusable slots.

Ví dụ:

```text
Pool<Node>
```

có thể có:

```text
slot 0
slot 1
slot 2
...
```

Object destruction không nhất thiết release backing storage.

---

# 32. Slab

Slab là pool tối ưu cho fixed-size objects.

Ví dụ:

```text
Slab<Entity>
```

có thể cung cấp:

```text
stable slot address
generation
free-list
```

nếu API contract yêu cầu.

---

# 33. Handle

Handle là logical identity:

```text
Handle<T>
```

không phải pointer.

Ví dụ:

```text
(index, generation)
```

Compiler không cần coi handle là memory capability.

---

# 34. Stale handle

Nếu:

```text
slot 10 generation 4
```

được freed rồi reused:

```text
slot 10 generation 5
```

thì:

```text
Handle(10,4)
```

không còn hợp lệ.

Library trả:

```text
Option<T>
Result<T,E>
```

hoặc tương đương.

---

# 35. Fragmentation

Axiom không tuyên bố:

> flat virtual address space eliminates fragmentation.

Điều đó sai về mặt allocator semantics.

Fragmentation phụ thuộc:

```text
allocation pattern
lifetime distribution
size classes
free strategy
allocator policy
locality
```

---

# 36. Flat address space

Axiom native processes sử dụng flat virtual address model khi target cung cấp.

Nhưng:

```text
virtual address space
```

và:

```text
physical allocation strategy
```

là hai vấn đề khác nhau.

---

# 37. Fragmentation mitigation

Library/runtime MAY cung cấp:

```text
arena
pool
slab
segregated allocator
region allocator
custom allocator
```

Compiler không ép một allocator duy nhất.

---

# 38. Custom allocator

Custom allocator là library/system abstraction.

Ví dụ conceptual:

```axiom
trait Allocator {
    ...
}
```

Các collection có thể hỗ trợ allocator-specific APIs.

Nhưng v0.1:

> allocator không phải generic parameter bắt buộc của mọi collection.

---

# 39. Why allocator không nằm trong type mặc định?

Tránh:

```text
Vec<T, Allocator>
Box<T, Allocator>
String<Allocator>
```

ở mọi API.

Nếu allocator trở thành một phần type identity mặc định:

```text
Vec<A>
Vec<B>
```

sẽ làm type system và generic APIs phức tạp không cần thiết.

Axiom chọn:

```text
allocator choice = storage implementation/API concern
```

trừ khi semantics thực sự cần expose nó.

---

# 40. Resource allocation failure

Allocation failure khác resource cleanup.

Ví dụ:

```axiom
let buffer = Buffer.try_new(size)?
```

có thể:

```text
Ok(Buffer)
Err(OutOfMemory)
```

---

# 41. Convenience allocation

Library MAY có:

```text
Buffer.new(size)
```

với semantics:

```text
panic/abort on allocation failure
```

tùy API contract.

Không bắt buộc mọi allocation API phải trả Result.

---

# 42. OOM

OOM là process/resource failure riêng.

Không được xử lý như:

```text
Drop failure
```

và `Drop` không được trả `Result`.

---

# 43. Allocation failure và cleanup

Ví dụ:

```axiom
let a = allocate_a()?
let b = allocate_b()?
```

Nếu `b` allocation fails:

```text
a
→ cleanup
→ propagate allocation failure
```

nếu API dùng fallible allocation.

---

# 44. Caller-allocated return

Function:

```axiom
fn make_large() -> Large
```

không bắt buộc allocate return object.

Compiler có thể lower thành:

```text
caller provides return storage
callee writes result
```

hoặc register return nếu đủ nhỏ.

---

# 45. Escape analysis

Compiler MAY phân tích:

```text
Does value escape?
Does address escape?
Does capability escape?
Does resource escape?
```

Nếu không escape:

```text
heap allocation
```

có thể được loại bỏ.

---

# 46. Escape analysis không thay đổi semantics

Ví dụ:

```text
Box<T>
```

được stack-promote chỉ khi không có observable difference.

Nếu API yêu cầu:

```text
stable address
```

thì escape analysis phải tôn trọng contract.

---

# 47. Static

```axiom
static COUNTER: u64 = 0
```

là storage identity có:

```text
program lifetime
```

Không phải compile-time constant.

---

# 48. `const`

```axiom
const MAX: u64 = 100
```

là compile-time value.

`const` không yêu cầu runtime storage identity.

Compiler có thể inline.

---

# 49. `static` vs `const`

| | `const` | `static` |
|---|---|---|
| compile-time | Có | initializer có thể compile-time |
| storage identity | Không bắt buộc | Có |
| address observable | Không mặc định | Có |
| lifetime | compile-time value | program lifetime |
| mutable | Không | có thể |
| inline | Có thể | không nếu address observable |

---

# 50. Mutable static

```axiom
static mut COUNTER: u64 = 0
```

nếu cho phép trong system/core profile thì phải tuân thủ concurrency rules.

Safe concurrent mutation không được mặc định.

Nên dùng:

```text
Atomic<T>
Mutex<T>
RwLock<T>
```

hoặc abstraction tương ứng.

---

# 51. Static Drop

v0.1:

> Không có implicit language-level Drop-all-statics-at-process-exit.

Nếu resource cần shutdown:

```axiom
shutdown()
```

phải explicit hoặc do host/runtime API quản lý.

Điều này tránh hidden global destruction order.

---

# 52. Thread-local storage

TLS:

```text
static thread_local STATE: T
```

conceptually có:

```text
one storage identity per thread
```

Không phải một global object duy nhất.

---

# 53. TLS lifetime

TLS tồn tại theo thread/runtime contract.

v0.1 không yêu cầu hidden arbitrary destructor chain khi thread exits.

Nếu resource cleanup cần deterministic semantic point:

```text
explicit shutdown/drop
```

được ưu tiên.

---

# 54. External memory

External memory:

```text
mmap
DMA
shared memory
GPU buffer
foreign allocation
```

là `EXTERNAL` storage domain.

Axiom không tự đoán ownership.

Phải có explicit ownership contract.

---

# 55. FFI allocation

Nếu C API:

```text
malloc()
```

trả pointer, Axiom không được tự động giả định:

```text
Axiom allocator owns it
```

Wrapper phải định nghĩa:

```text
who frees?
which allocator?
which ABI?
which lifetime?
```

---

# 56. Device memory

GPU/device memory là storage domain riêng:

```text
HOST
DEVICE
SHARED
```

Ownership/capability model vẫn áp dụng.

Nhưng host pointer không tự động có nghĩa device pointer.

---

# 57. Memory domains

Compiler semantic model có thể biểu diễn:

```text
HOST
DEVICE
EXTERNAL
STATIC
TLS
```

để ngăn invalid operations.

Ví dụ:

```text
host view
```

không tự biến thành:

```text
device view
```

---

# 58. Memory alignment

Compiler tự quyết alignment mặc định theo target/type.

Programmer có thể yêu cầu:

```axiom
@align(64)
struct CacheLine {
    ...
}
```

Compiler phải đảm bảo contract.

---

# 59. Packed representation

```axiom
@repr(packed)
struct Header {
    ...
}
```

là system/unsafe-level representation.

Compiler không được tạo aligned access giả định nếu field có alignment không phù hợp.

Có thể:

```text
generate unaligned load
```

hoặc yêu cầu unsafe access tùy semantics.

---

# 60. Zero-sized types

Axiom hỗ trợ ZST.

Ví dụ:

```axiom
struct Marker {}
```

có thể có size:

```text
0
```

nhưng vẫn có type identity.

Compiler không được suy luận rằng mọi instance phải có unique physical address.

---

# 61. Address identity của ZST

Hai ZST values có thể:

```text
share address
have no storage
be optimized away
```

trừ khi một explicit storage contract yêu cầu khác.

---

# 62. Allocation invariants

### AMEM-16
Address space is independent from allocation strategy.

### AMEM-17
Flat address space does not guarantee fragmentation freedom.

### AMEM-18
Storage strategy is not part of ordinary value semantics.

### AMEM-19
Heap allocation is not mandatory.

### AMEM-20
Compiler may eliminate unobservable allocation.

### AMEM-21
Stable address is an explicit storage contract.

### AMEM-22
Relocatable storage may move.

### AMEM-23
Reserve does not imply stable address.

### AMEM-24
Dependent capabilities block invalid relocation.

### AMEM-25
Escape analysis determines storage optimization opportunities.

### AMEM-26
Allocation is a semantic MIR operation before lowering.

### AMEM-27
Move does not imply physical copy.

### AMEM-28
Return does not imply heap allocation.

### AMEM-29
Caller-allocated returns are permitted.

### AMEM-30
Stack storage is a compiler strategy.

### AMEM-31
Register storage is a compiler strategy.

### AMEM-32
Static storage has program lifetime.

### AMEM-33
TLS has per-thread storage identity.

### AMEM-34
Arena ownership bounds arena allocations.

### AMEM-35
Arena allocation does not imply garbage collection.

### AMEM-36
Pool storage supports reusable slots.

### AMEM-37
Slab storage is a fixed-size pool strategy.

### AMEM-38
Handles are logical identity, not raw addresses.

### AMEM-39
Generation handles can prevent stale logical references.

### AMEM-40
Custom allocators are library/system abstractions.

### AMEM-41
Allocator choice is not a mandatory generic parameter.

### AMEM-42
Collection APIs do not expose allocator parameters by default.

### AMEM-43
Resource lifetime is distinct from memory lifetime.

### AMEM-44
Drop does not necessarily deallocate memory.

### AMEM-45
Drop is non-fallible.

### AMEM-46
Allocation failure is distinct from resource cleanup.

### AMEM-47
Freestanding programs need not have a heap.

### AMEM-48
Device memory is a distinct storage domain.

### AMEM-49
External memory requires an explicit ownership contract.

### AMEM-50
Stable ABI must define allocation ownership.

### AMEM-51
FFI must not guess allocation domains.

### AMEM-52
GC is not a core runtime requirement.

### AMEM-53
Reference counting is not an implicit language mechanism.

### AMEM-54
Compiler lifetime analysis may shorten storage lifetime.

### AMEM-55
Observable addresses constrain storage optimization.

### AMEM-56
Storage identity is distinct from value identity.

### AMEM-57
Fragmentation is an allocation-strategy property.

### AMEM-58
Allocation placement is an allocator responsibility.

### AMEM-59
Allocation elimination is a compiler responsibility.

### AMEM-60
Memory strategy is explicit only when semantically relevant.

### AMEM-61
Stable address exists only when the storage contract requires it.

---

# 63. Một kết luận quan trọng cho mục tiêu "hiệu năng bằng/hơn C/C++"

Memory model hiện tại **không buộc Axiom phải chậm hơn C/C++**.

Một đoạn:

```axiom
fn sum(a: view<i32>) -> i64 {
    var total: i64 = 0

    for x in a {
        total = total + x as i64
    }

    total
}
```

sau verification có thể trở thành gần như:

```text
pointer
length
loop
load
add
```

Compiler có thể:

```text
bounds-check elimination
vectorization
unrolling
register allocation
```

mà không cần runtime ownership machinery.

Điểm khác là Axiom dùng compiler proof để có được một số guarantee mà C/C++ thường để programmer tự chịu trách nhiệm.

---

# 64. Nhưng có một giới hạn cần ghi rõ

Axiom **không thể đảm bảo mọi chương trình luôn nhanh hơn C/C++**.

Điều thực tế có thể cam kết là:

> **Axiom không đưa thêm mandatory runtime machinery vào machine code chỉ để thực hiện safety abstractions.**

Vì vậy:

```text
safe abstraction
→ compile-time verification
→ erase
→ native code
```

là mục tiêu zero-cost.

---

# 65. Part IV freeze

Đến đây memory/storage architecture đã khá hoàn chỉnh:

```text
                  Axiom Value
                       │
          ┌────────────┴────────────┐
          │                         │
      Resource                  Storage
          │                         │
       Drop                    register
       close                    stack
       release                  inline
       unlock                   heap
                                arena
                                pool
                                static
                                TLS
                                device
```

Không có một abstraction nào bắt buộc tất cả chương trình phải đi qua heap hoặc runtime.

---

# AXIOM LANGUAGE SPECIFICATION v0.1 — Part V
## Concurrency · Send · Share · Threads · Synchronization

Phần tiếp theo sẽ khóa phần còn thiếu rất quan trọng của memory model:

```text
Send
Share
Thread
spawn
spawn_local
Join
Channel
Mutex
RwLock
Atomic
memory ordering
happens-before
data race
deadlock
lock guard
await + lock
cancellation
structured concurrency
```

Đặc biệt sẽ phải giải quyết một vấn đề mà nhiều language thiết kế chưa thật sạch:

> **Làm sao để concurrency safety dùng cùng ownership/capability system, thay vì tạo thêm một hệ thống "borrow/thread" riêng.**