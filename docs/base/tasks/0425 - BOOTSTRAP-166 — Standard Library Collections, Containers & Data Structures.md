# BOOTSTRAP-166 — Standard Library Collections, Containers & Data Structures
**STATUS: FROZEN / COMPLETED**

> **Container là library abstraction; ownership, capability, lifetime và representation semantics vẫn thuộc Axiom Core. Compiler chỉ cần hiểu những semantic properties cần thiết để tối ưu container mà không biến từng container thành language primitive.**

Mục tiêu của bước này là chốt **hệ container nền tảng**, đặc biệt vấn đề đã được quan tâm từ đầu: relocation, stable address, fragmentation, cache locality, ownership và khả năng tối ưu thành code gần như viết tay.

---

# 1. Phân loại container

Không coi tất cả container là một nhóm.

Axiom chia thành:

```text
Value Containers
    ├── Array
    ├── Tuple
    └── Struct

View Containers
    ├── view<T>
    ├── mut_view<T>
    └── Str / ByteStr

Owning Sequential
    ├── Vec
    ├── SmallVec
    ├── VecDeque
    └── RingBuffer

Associative
    ├── HashMap
    ├── HashSet
    ├── BTreeMap
    └── BTreeSet

Storage/Lifetime
    ├── Box
    ├── Arena
    ├── Pool
    ├── Slab
    └── StablePool

Data-Oriented
    ├── SoA
    ├── SparseSet
    ├── BitSet
    └── PackedArray
```

---

# 2. Array là semantic primitive

```ax
let a: [i32; 4];
```

Array có:

- fixed length;
- element type;
- value semantics;
- contiguous representation;
- known compile-time length.

Đã chốt trước đó:

> **Fixed-size array có contiguous representation guarantee.**

Compiler có thể scalarize array thành registers/SSA nhưng semantics vẫn là contiguous array.

---

# 3. Array không phải Vec

```text
[i32; 16]
```

khác:

```text
Vec<i32>
```

về semantic properties.

| | Array | Vec |
|---|---|---|
| Length | compile-time | runtime |
| Ownership | value | owning container |
| Resize | không | có |
| Relocation | không resize | có thể |
| Capacity | length | runtime |
| Stack/register optimization | rất mạnh | tùy escape |

---

# 4. View là access capability

```ax
fn sum(x: view<i32>) -> i32
```

không phải container owning.

Nó biểu diễn:

```text
owner/provenance
+
region
+
READ capability
```

`view<T>` không được tự tạo lifetime vượt owner.

---

# 5. Mutable view

```ax
fn fill(x: mut_view<i32>) {
    ...
}
```

là:

```text
exclusive WRITE capability
```

Không được duplicate thành hai `mut_view` overlapping.

---

# 6. Slice API

Không cần một kiểu `Slice<T>` riêng trong Core.

Library có thể cung cấp API trên:

```text
view<T>
mut_view<T>
```

Ví dụ:

```ax
xs.subview(10, 20)
xs.split_at(10)
xs.chunks(8)
xs.windows(4)
```

Compiler theo dõi region.

---

# 7. Vec

Semantic contract:

```text
Vec<T>
=
owned
+
ordered
+
contiguous logical elements
+
runtime length
+
capacity
+
relocatable storage
```

---

# 8. Vec relocation là observable khi address observable

Ví dụ:

```ax
let v = Vec<i32>();
let x = view(v);

v.push(1);
```

Nếu `push` cần relocate thì compiler thấy `x` còn sống.

→ **không được phép relocation phá capability**.

API/compiler phải:

- kết thúc capability trước mutation; hoặc
- thực hiện mutation không relocate; hoặc
- reject.

Không có dangling view.

---

# 9. Capacity

```ax
v.reserve(100);
```

chỉ đảm bảo capacity đủ theo contract.

Không biến thành:

```text
permanent stable address
```

và cũng không ngăn compiler thay đổi physical storage nếu semantic contract không yêu cầu.

---

# 10. Stable address

Khi cần:

```text
stable storage
```

phải dùng abstraction khác.

Ví dụ:

```text
StableBox<T>
StablePool<T>
Arena<T>
Slab<T>
```

Không ép `Vec` thành stable container.

---

# 11. SmallVec

```text
SmallVec<T, N>
```

semantic contract:

```text
logical sequence
```

physical representation:

```text
inline capacity N
+
spill storage
```

Compiler có thể biết:

```text
InlineCapacity
```

để tối ưu nhưng không được phụ thuộc implementation detail nếu API không contract.

---

# 12. SmallVec relocation

Ngay cả inline→heap cũng là relocation semantic nếu address observable.

Vì vậy:

```text
active view
+
operation requiring migration
```

phải được compiler/API kiểm soát.

---

# 13. VecDeque

```text
VecDeque<T>
```

dùng circular buffer.

Semantic:

```text
ordered sequence
```

Physical:

```text
ring storage
```

không nhất thiết contiguous toàn bộ sequence về memory.

Do đó không tự động convert:

```text
VecDeque → view<T>
```

như Vec.

Có thể cung cấp:

```text
as_slices()
```

trả hai views.

---

# 14. RingBuffer

RingBuffer nên là abstraction riêng cho:

- producer/consumer;
- streaming;
- audio;
- networking;
- real-time.

Có thể có specialization:

```text
SpscRing<T>
MpscRing<T>
```

với synchronization contract rõ ràng.

---

# 15. Queue

Không cần một implementation duy nhất.

API semantic:

```text
Queue<T>
push
pop
front
len
is_empty
```

Implementation có thể là:

```text
VecDeque
RingBuffer
linked
lock-free
```

nhưng type identity nên phản ánh performance/concurrency contract nếu khác biệt observable.

---

# 16. LinkedList

Có thể cung cấp nhưng **không nên là default abstraction** cho sequence.

Lý do:

- pointer chasing;
- cache locality kém;
- allocation fragmentation;
- khó vectorize.

Nhưng vẫn hữu ích cho workload đặc biệt.

---

# 17. Stack

Có hai nghĩa khác nhau.

### Logical container

```text
Stack<T>
push
pop
peek
```

### Execution stack

```text
call stack
```

Không được nhập hai khái niệm.

`Stack<T>` là library container.

---

# 18. HashMap

Semantic:

```text
key → value
```

Không đảm bảo iteration order mặc định.

Hash function là policy.

---

# 19. HashMap layout

Implementation có thể:

```text
open addressing
Swiss-table-like
Robin Hood
cuckoo
```

Không đóng băng implementation.

Nhưng API phải expose các property cần thiết:

```text
lookup
insert
remove
reserve
capacity
```

---

# 20. HashMap relocation

Resize có thể relocate entries.

Nếu user có:

```text
view<Value>
```

và resize có thể di chuyển storage:

→ active capability phải ngăn operation hoặc API phải kết thúc capability.

Không cho dangling references.

---

# 21. Entry API

Cần có abstraction tương tự:

```ax
map.entry(key)
```

để tránh:

```text
lookup
+
insert
```

hai lần.

Ví dụ semantic:

```ax
match map.entry(key) {
    Vacant(e) => e.insert(value),
    Occupied(e) => e.update(...)
}
```

Entry capability phải quản lý alias/relocation.

---

# 22. HashSet

Không duplicate implementation nếu có thể.

Có thể xây trên HashMap-like table:

```text
HashSet<T>
≈ HashMap<T, Unit>
```

nhưng compiler/library có thể specialize representation để bỏ value storage.

---

# 23. BTreeMap

Dùng khi cần:

- sorted keys;
- predictable traversal;
- range query;
- locality tương đối tốt.

API:

```text
first
last
range
lower_bound
upper_bound
```

---

# 24. BTreeSet

Tương tự HashSet nhưng ordered.

Không cần hidden virtual dispatch.

---

# 25. Deterministic Map

Compiler/build tooling cần map có iteration deterministic.

Đề xuất:

```text
OrderedMap<K,V>
```

hoặc:

```text
BTreeMap
```

Không yêu cầu `HashMap` phải deterministic.

---

# 26. Arena

Arena là **lifetime/storage abstraction**, không chỉ allocator.

```text
Arena
 ├── allocations
 └── arena lifetime
```

Objects trong arena có thể sống tới:

```text
arena.reset()
arena.drop()
```

---

# 27. Arena và ownership

Nếu:

```ax
let x = arena.alloc(value);
```

thì ownership semantics phải nói rõ:

- `x` là arena-owned capability/handle;
- không thể outlive arena;
- compiler phải ngăn escape invalid.

Không giả vờ mỗi allocation là independent `Box`.

---

# 28. Arena không nhất thiết stable address

Một arena có thể:

```text
bump allocate
```

và không relocate.

Nhưng một container có thể compact.

Vì vậy:

> **Stable address là contract của abstraction, không phải property của từ “Arena”.**

---

# 29. StableArena

Có thể cung cấp:

```text
StableArena<T>
```

với explicit contract:

```text
allocated object address remains stable
until destruction of arena/object
```

Khi đó compiler không được stack-promote/relocate theo cách phá observable address.

---

# 30. Pool

Pool:

```text
Pool<T>
```

dành cho object reuse.

Semantic:

```text
allocate
release
reuse
```

Không nhất thiết contiguous.

---

# 31. Pool và logical identity

Nếu object có:

```text
EntityId
```

thì object có thể bị physical relocation mà logical identity không đổi.

Đây là cách Axiom ưu tiên cho ECS/data-oriented systems.

---

# 32. Slab

```text
Slab<T>
```

phù hợp:

- stable-ish slot;
- handles;
- networking;
- server entities;
- resource tables.

Có:

```text
Handle<T>
```

với generation để phát hiện stale handle.

---

# 33. Handle

Handle:

```text
index
+
generation
```

không phải raw pointer.

Ví dụ:

```text
Handle<Entity>
```

cho phép:

```text
remove entity
reuse slot
```

mà stale handle bị phát hiện.

---

# 34. Handle không phải capability

Điểm này phải đóng băng:

```text
Handle<T> ≠ view<T>
```

Handle biểu diễn:

```text
logical identity
```

View biểu diễn:

```text
access capability
```

Một Handle không tự cấp quyền truy cập.

---

# 35. PackedArray

```text
PackedArray<T>
```

cho:

- dense storage;
- swap-remove;
- cache locality.

Nhưng removal có thể thay đổi vị trí physical của element.

Do đó:

```text
index identity
```

không ổn định.

---

# 36. StablePackedArray

Có thể cung cấp abstraction nếu cần:

```text
StablePackedArray<T>
```

nhưng stable logical identity vẫn nên dùng Handle.

Không nên bắt programmer giữ raw pointer.

---

# 37. SparseSet

Đặc biệt hữu ích cho ECS:

```text
SparseSet<Entity, T>
```

có:

```text
sparse index
dense data
```

Compiler không cần biết ECS semantics.

Chỉ cần optimize generic array/index operations.

---

# 38. SoA

Đây là container rất đáng có.

```text
SoA<Particle>
```

về semantic:

```text
collection of Particle
```

nhưng physical:

```text
xs[]
ys[]
zs[]
velocity[]
...
```

---

# 39. SoA không phải compiler magic

Axiom không cần compiler tự động biến mọi AoS thành SoA.

Thay vào đó:

```text
std::data::SoA
```

là explicit library abstraction.

Compiler có thể optimize tiếp.

---

# 40. AoS → SoA compiler transformation

Vẫn có thể cho optimizer thực hiện khi:

- layout không observable;
- address không escape;
- ABI không phụ thuộc;
- reflection không quan sát layout;
- semantics preserved.

Nhưng explicit `SoA` là cách programmer yêu cầu physical data orientation rõ ràng.

---

# 41. BitSet

```text
BitSet
```

nên có representation packed bits.

Không dùng:

```text
Vec<bool>
```

làm semantic assumption.

API:

```text
set
clear
test
count
find_first
find_next
```

Compiler có thể map population count/bit scan sang target instruction.

---

# 42. PackedArray

Cho dữ liệu compact:

```text
PackedArray<T>
```

nhưng cần phân biệt:

```text
semantic T
```

với:

```text
serialized/packed bit representation
```

Nếu packing làm mất natural alignment, access có thể cần specialized operations.

---

# 43. ByteBuffer

Cho networking/I/O:

```text
ByteBuffer
```

có thể hỗ trợ:

```text
read_u16_le
read_u32_be
write_u64_le
...
```

Endian là explicit.

Không phụ thuộc host layout.

---

# 44. ByteBuffer và unsafe

API safe phải kiểm tra:

- length;
- alignment nếu cần;
- endian;
- valid encoding.

Unsafe low-level APIs có thể bỏ checks khi programmer cung cấp contract.

---

# 45. Matrix

Matrix không cần Core.

Có thể:

```text
Matrix<T, R, C>
```

với compile-time dimensions.

Compiler có thể:

- unroll;
- vectorize;
- scalarize;
- use SIMD.

---

# 46. Tensor

Tensor nên là package/library layer:

```text
Tensor<T, Shape, Device>
```

với:

```text
CPU
GPU
```

storage domain explicit.

---

# 47. Container capability model

Mọi mutable container operation phải conceptually answer:

```text
Có capability nào đang active?
Operation có relocate không?
Operation có invalidate view không?
Operation có thay đổi logical identity không?
```

Đây là điểm compiler phải hiểu qua contracts.

---

# 48. Container contracts

Standard library metadata nên cho compiler biết:

```text
@may_relocate
@stable_address
@preserves_views
@invalidates_views
@returns_view
@returns_mut_view
@noalias
```

Nhưng **không cho programmer tự khai báo bừa** những property này.

Implementation/compiler phải verify hoặc đánh dấu trusted unsafe boundary.

---

# 49. `@may_relocate`

Ví dụ:

```text
Vec.push
Vec.reserve
HashMap.insert
```

có thể có:

```text
MayRelocateStorage
```

Effect metadata.

Compiler dùng để kiểm tra capability.

---

# 50. `@returns_view`

Ví dụ:

```text
Vec.as_view()
```

compiler biết:

```text
returned capability
→ owner = Vec
```

và giữ provenance.

---

# 51. `@returns_mut_view`

Tương tự nhưng WRITE capability.

Do đó:

```ax
let a = v.mut_view();
let b = v.mut_view();
```

nếu overlapping:

→ reject.

---

# 52. Container effect summaries

Ví dụ:

```text
Vec.push
```

có thể có:

```text
Read elements
Write storage
Allocate
PotentiallyRelocate
```

trong Effect/Storage model.

Không cần programmer annotation mỗi lần gọi.

---

# 53. Compiler-known container properties

Không hard-code:

```text
if type == Vec
```

trong optimizer càng nhiều càng tốt.

Thay vào đó compiler hiểu semantic traits/contracts:

```text
Contiguous
Resizable
Relocatable
StableStorage
RandomAccess
Sequential
```

---

# 54. Marker traits

Có thể:

```text
trait ContiguousStorage<T>
trait RandomAccess<T>
trait StableStorage<T>
trait Resizable
```

nhưng cần tránh tạo hàng chục trait chỉ để compiler optimization.

Một số có thể là compiler-known metadata properties thay vì public traits.

---

# 55. Public trait vs compiler property

Phân biệt:

```text
public semantic trait
```

với:

```text
compiler optimization fact
```

Ví dụ `Contiguous` có thể là semantic contract.

Nhưng:

```text
"this function vectorizes well"
```

không nên là trait.

---

# 56. Container optimization

Ví dụ:

```ax
for i in 0..v.len() {
    sum += v[i];
}
```

compiler có thể:

1. prove `i < len`;
2. prove storage contiguous;
3. eliminate bounds checks;
4. prove alias;
5. vectorize;
6. select SIMD width;
7. emit efficient loop.

Không cần:

```text
unsafe
pointer arithmetic
restrict
```

---

# 57. Container abstraction erasure

```ax
fn sum<T: Numeric>(x: view<T>) ...
```

có thể specialize thành machine loop.

Không cần runtime generic object.

---

# 58. Iterator fusion

Ví dụ:

```ax
let result =
    xs.map(f)
      .filter(p)
      .map(g)
      .sum();
```

compiler có thể tạo một loop:

```text
for x:
    y = f(x)
    if p(y):
        sum += g(y)
```

không tạo:

```text
temporary Vec
temporary iterator objects
```

nếu không observable.

---

# 59. Allocation elimination

Ví dụ:

```ax
fn f() -> Vec<i32> {
    let v = Vec();
    v.push(1);
    v.push(2);
    return v;
}
```

compiler có thể:

```text
caller allocation
stack construction
register/scalarization
```

nếu ABI/escape semantics cho phép.

---

# 60. No accidental fragmentation

Axiom không tuyên bố:

> “mọi heap allocation đều không phân mảnh.”

Thay vào đó standard library cung cấp:

```text
general allocator
arena
pool
slab
bump
```

và programmer chọn abstraction khi workload yêu cầu.

Compiler không thể loại bỏ fragmentation bằng language semantics alone.

---

# 61. Recommended container hierarchy

Đóng khung:

```text
Default sequence:
    Array / Vec

Small sequence:
    SmallVec

Queue:
    VecDeque / RingBuffer

Associative:
    HashMap / BTreeMap

Set:
    HashSet / BTreeSet

Stable storage:
    Box / StablePool / Slab

Batch lifetime:
    Arena

Dense entity data:
    PackedArray / SparseSet

Data oriented:
    SoA

Bit-oriented:
    BitSet

Logical identity:
    Handle<Entity>
```

---

# 62. Container selection philosophy

Không có:

```text
"one universal container"
```

Thay vào đó:

```text
semantic requirement
+
access pattern
+
lifetime
+
locality
+
concurrency
```

quyết định container.

---

# 63. API không ép pointer thinking

Ví dụ ECS:

Không:

```text
Entity*
```

mà:

```ax
let e: Handle<Entity>;
let entity = entities.get(e)?;
```

Compiler kiểm tra handle/capability.

---

# 64. Stable identity

Nếu programmer cần:

```text
identity
```

thì dùng:

```text
Handle
EntityId
Key
```

Nếu cần:

```text
physical address
```

thì explicit stable-storage API.

Đây là hướng quan trọng để giảm pointer/reference complexity mà vẫn giữ system-level power.

---

# 65. Container concurrency

Container thường **không tự thread-safe**.

Ví dụ:

```text
Vec<T>
```

không tự trở thành concurrent container.

Nếu cần:

```text
Mutex<Vec<T>>
RwLock<Vec<T>>
Arc<Vec<T>>
ConcurrentQueue<T>
```

lựa chọn phải explicit.

---

# 66. Concurrent containers

Có thể có:

```text
ConcurrentHashMap
ConcurrentQueue
LockFreeRing
AtomicQueue
```

nhưng chúng là specialized library abstractions.

Compiler vẫn sử dụng memory model chung.

---

# 67. Container Send/Share

Compiler tự derive:

```text
Send<Vec<T>>
```

nếu:

```text
Send<T>
```

và container implementation semantics phù hợp.

`Share<Vec<T>>` không tự động đồng nghĩa mutable-safe.

---

# 68. Container Drop

`Vec<T>` Drop:

```text
drop each initialized element
release storage
```

Compiler có thể optimize:

- trivial element Drop;
- known-empty vector;
- moved elements;
- partial initialization.

---

# 69. Partial initialization

Low-level containers có thể cần:

```text
uninitialized storage
```

nhưng phải đi qua verified abstraction.

Không cho ordinary safe code tạo:

```text
Vec<T>
```

có arbitrary uninitialized logical elements.

---

# 70. `MaybeUninit`-style abstraction

Có thể cung cấp:

```text
Uninit<T>
```

trong:

```text
std::mem
```

với API rất constrained.

Mục tiêu:

```text
unsafe implementation
→ safe initialization protocol
```

không để uninitialized value lọt vào safe semantic value.

---

# 71. Zero-sized types

Containers phải hỗ trợ:

```text
struct Marker;
Vec<Marker>
```

mà không cần allocation tương ứng với số phần tử.

Compiler có thể optimize mạnh.

---

# 72. Capacity for ZST

`Vec<ZST>` có semantics length nhưng physical storage có thể không cần bytes.

Đây là ví dụ rõ:

> semantic size ≠ physical allocation size.

---

# 73. Container equality

Không mặc định:

```text
memory bytes == semantic equality
```

Ví dụ:

- padding;
- NaN;
- niche representation.

`PartialEq`/`Eq` quyết định semantic equality.

---

# 74. Hashing

Hash phải tương thích:

```text
Eq
Hash
```

và không được hash arbitrary padding bytes.

---

# 75. Serialization

Container serialization phải đi theo:

```text
logical values
```

không dump raw memory trừ khi API explicit binary-layout contract.

---

# 76. Compiler cooperation boundary

Compiler cần hiểu trực tiếp rất ít container:

### Semantic built-in / compiler-known

```text
Array
view
mut_view
Option
Result
```

### Compiler-optimized through contracts

```text
Vec
String
Slice
Iterator
Box
Arc
```

### Pure library

```text
HashMap
BTreeMap
Arena
Slab
SparseSet
SoA
```

Compiler vẫn có thể optimize generic implementations mà không cần hard-code type names.

---

# 77. Đây là điểm kiến trúc rất quan trọng

Không làm:

```text
Compiler
 ├── special Vec optimizer
 ├── special HashMap optimizer
 ├── special String optimizer
 ├── special Arena optimizer
 └── ...
```

vì vài năm sau compiler sẽ thành một đống special cases.

Thay vào đó:

```text
Library API
     ↓
Semantic contracts
     ↓
Generic compiler analyses
     ↓
Optimization
```

Đây chính là cách giữ compiler mạnh nhưng language/library không bị coupling quá chặt.

---

# 78. Container metadata

Có thể mở rộng `.axmeta` với:

```text
ContainerContract {
    storage_kind
    contiguous
    relocatable
    stable_address
    random_access
    preserves_order
    concurrency_model
    invalidation_rules
}
```

Compiler/IDE/AI có thể đọc.

---

# 79. AI-friendly container explanation

Ví dụ:

```text
axc inspect container Vec<i32>
```

có thể trả:

```text
Ownership:
    owning

Storage:
    contiguous

Relocation:
    possible

Stable address:
    no

Random access:
    yes

Mutation:
    exclusive

Send:
    derived from T

Share:
    immutable sharing only unless synchronized
```

Đây là thông tin rất hữu ích cho AI agent.

---

# 80. Frozen invariants

### `ACONT-20`
Containers are library abstractions unless explicitly defined as language semantics.

### `ACONT-21`
Ownership semantics remain defined by Axiom Core.

### `ACONT-22`
Capability validity remains enforced for container views.

### `ACONT-23`
Fixed arrays have contiguous representation.

### `ACONT-24`
Fixed arrays have compile-time length.

### `ACONT-25`
Arrays and growable vectors are semantically distinct.

### `ACONT-26`
`Vec<T>` represents an owning ordered contiguous sequence.

### `ACONT-27`
`Vec<T>` does not guarantee stable physical addresses.

### `ACONT-28`
Operations capable of relocating storage must respect active capabilities.

### `ACONT-29`
Capacity reservation does not imply permanent address stability.

### `ACONT-30`
Stable storage requires an explicit storage contract.

### `ACONT-31`
`SmallVec` may migrate between inline and external storage.

### `ACONT-32`
Migration cannot invalidate safe active capabilities.

### `ACONT-33`
`VecDeque` does not guarantee globally contiguous logical storage.

### `ACONT-34`
Ring buffers expose explicit ordering and capacity semantics.

### `ACONT-35`
HashMap does not guarantee iteration order unless its specific type contract does.

### `ACONT-36`
Hashing strategy is a library concern.

### `ACONT-37`
Map mutation that may relocate entries must respect active capabilities.

### `ACONT-38`
Entry APIs preserve ownership and capability correctness.

### `ACONT-39`
Ordered maps provide deterministic key ordering according to their contract.

### `ACONT-40`
Arena allocation is a lifetime/storage abstraction.

### `ACONT-41`
Arena-allocated values cannot safely outlive the arena.

### `ACONT-42`
Stable address is not implied merely by using an arena.

### `ACONT-43`
Stable storage is an explicit semantic contract.

### `ACONT-44`
Pool and slab reuse cannot invalidate live safe capabilities.

### `ACONT-45`
Handles represent logical identity rather than memory capabilities.

### `ACONT-46`
Stale handles must be detectable where generation-based handles are used.

### `ACONT-47`
Packed and dense containers may move elements unless explicitly stable.

### `ACONT-48`
Sparse-set and packed data structures preserve their documented logical semantics independently of physical movement.

### `ACONT-49`
SoA containers explicitly represent data-oriented physical organization.

### `ACONT-50`
Compiler AoS→SoA transformations are permitted only when representation is not observably constrained.

### `ACONT-51`
BitSet may use packed-bit representation.

### `ACONT-52`
Packed representations do not redefine semantic value identity.

### `ACONT-53`
Byte buffers use explicit endian semantics for encoded integers.

### `ACONT-54`
Matrix/tensor containers remain library abstractions.

### `ACONT-55`
Container APIs may expose compiler-readable semantic contracts.

### `ACONT-56`
Compiler-derived container facts must be proven or originate from trusted verified implementations.

### `ACONT-57`
Programmer annotations cannot fabricate false compiler semantic properties.

### `ACONT-58`
Container relocation effects participate in the capability verifier.

### `ACONT-59`
Container effect summaries participate in alias and optimization analysis.

### `ACONT-60`
Container generic abstractions must remain statically optimizable where semantics permit.

### `ACONT-61`
Iterator pipelines may be fused without intermediate allocation when unobservable.

### `ACONT-62`
Container allocation may be eliminated, promoted or scalarized when semantic constraints permit.

### `ACONT-63`
Container Drop follows deterministic ownership and initialization rules.

### `ACONT-64`
Trivial element Drop may be eliminated.

### `ACONT-65`
Zero-sized element types must be supported without requiring proportional physical storage.

### `ACONT-66`
Semantic equality does not imply bytewise memory equality.

### `ACONT-67`
Container hashing must respect semantic equality rather than padding representation.

### `ACONT-68`
Serialization operates on logical values unless an explicit memory-layout contract is requested.

### `ACONT-69`
Containers are not implicitly thread-safe.

### `ACONT-70`
Concurrent containers use explicit synchronization/concurrency contracts.

### `ACONT-71`
Send and Share properties of containers are compiler-derived.

### `ACONT-72`
Shared ownership does not imply mutable thread-safe access.

### `ACONT-73`
Uninitialized storage is isolated behind explicit verified abstractions.

### `ACONT-74`
Safe containers cannot expose invalid uninitialized semantic values.

### `ACONT-75`
Compiler optimization should rely on generic semantic contracts rather than type-name-specific special cases where practical.

### `ACONT-76`
Container metadata may be emitted into `.axmeta`.

### `ACONT-77`
Container semantics remain independent of optimization level.

### `ACONT-78`
Container semantics remain independent of physical storage selection unless explicitly contracted.

### `ACONT-79`
Container APIs must not force programmer-facing pointer/lifetime syntax.

### `ACONT-80`
Container design must support both high-level application development and low-level systems programming.

---

# Kiến trúc container cuối cùng

Có thể xem hệ thống nền như sau:

```text
                     Axiom Core
                         │
              ┌──────────┴──────────┐
              │                     │
          Array/View             Ownership
              │                     │
              └──────────┬──────────┘
                         ▼
                  std::containers
                         │
       ┌─────────┬───────┼────────┬─────────┐
       ▼         ▼       ▼        ▼         ▼
     Vec      HashMap   Arena     SoA      Slab
       │         │       │        │         │
       └─────────┴───────┼────────┴─────────┘
                         ▼
                Compiler Analysis
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      Escape           Alias          Effect
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                   Optimization
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           SROA       SIMD       Cache/DOD
```

Đây là hướng phù hợp với mục tiêu ban đầu của Axiom: **lập trình viên không phải suy nghĩ liên tục về pointer/reference/lifetime, nhưng compiler vẫn có đủ thông tin để tạo machine code rất thấp tầng và hiệu quả.**

---

# BOOTSTRAP-167 — Iterator, Range, Algorithms & Zero-Cost Generic Programming

Bước kế tiếp sẽ chốt một phần cực kỳ quan trọng của trải nghiệm Axiom:

```text
for
range
iterator
map
filter
fold
reduce
sort
search
parallel algorithms
```

Đặc biệt cần giải quyết **làm thế nào viết code rất giống high-level functional programming nhưng compiler biến nó thành một vòng lặp machine-level duy nhất**, không allocation, không iterator object runtime, không virtual dispatch và có thể tự động vectorize/parallelize khi chứng minh được an toàn.