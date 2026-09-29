# BOOTSTRAP-170 — Collections, Containers & Memory-Efficient Data Structures
**FROZEN / COMPLETED**

Đây là một task rất quan trọng vì Collections là nơi Axiom phải chứng minh được triết lý:

> **API high-level cho programmer, nhưng representation và codegen có thể gần như C/C++.**

Programmer không phải quản lý pointer, lifetime, borrow hay allocator; compiler vẫn có đủ thông tin để tối ưu layout, allocation, aliasing, vectorization và cache. memcite

---

## 170.1. Phân tầng Collection

Axiom không biến mọi collection thành một primitive của language.

```text
Axiom Core
│
├── Array<T, N>
├── view<T>
├── mut_view<T>
│
└── ownership / capability semantics
        │
        ▼
std::collections
├── Vec<T>
├── Deque<T>
├── Map<K,V>
├── Set<T>
├── BTreeMap<K,V>
├── HashMap<K,V>
├── SmallVec<T,N>
├── InlineVec<T,N>
├── RingBuffer<T,N>
├── Arena<T>
└── SoA<T>
```

Core chỉ cần semantic primitives đủ mạnh.

Collection cụ thể thuộc standard library.

---

# 170.2. `Array<T, N>`

Array cố định:

```ax
let a: Array<i32, 4> = [1, 2, 3, 4];
```

Semantic:

```text
fixed length
contiguous
ordered
inline by value
```

`Array<T,N>` không tự động heap allocate.

Compiler có thể biến:

```text
Array<i32, 4>
```

thành:

```text
4 registers
```

nếu phù hợp.

---

# 170.3. `view<T>` và `mut_view<T>` là collection primitives

Đây là nền tảng của zero-copy API.

```ax
fn sum(xs: view<i32>) -> i32
```

và:

```ax
fn fill(xs: mut_view<i32>, value: i32)
```

không tạo collection mới.

Ví dụ:

```ax
let values = Vec<i32>::new();

fill(values.view_mut(), 0);
```

Compiler theo dõi capability và provenance như đã định nghĩa trong memory model.

---

# 170.4. `Vec<T>`

`Vec<T>` là dynamic contiguous sequence.

Semantic:

```text
length
capacity
ordered elements
owned storage
```

Có thể có representation:

```text
ptr + len + capacity
```

nhưng không bắt buộc.

```ax
let v = Vec<i32>::new();

v.push(10);
v.push(20);
v.push(30);
```

`push` có thể relocation khi capacity không đủ.

Không có guarantee stable address mặc định.

---

# 170.5. Không có hidden pointer bureaucracy

Programmer không viết:

```text
T*
T&
T&&
iterator pointer
manual realloc
manual free
```

nhưng compiler vẫn có thể lower:

```text
Vec<T>
```

thành machine-level:

```text
base pointer
length
capacity
```

hoặc thậm chí scalarize/eliminate toàn bộ structure.

Đây chính là:

> **semantic abstraction ≠ physical representation.**

---

# 170.6. Allocation strategy

Collection không được hard-code vào một allocator duy nhất.

Ví dụ `Vec<T>` có thể sử dụng:

```text
system allocator
Axiom allocator
arena
pool
custom allocator
stack-backed storage
inline storage
device allocator
```

thông qua abstraction của library.

Compiler có thể phát hiện:

```text
Vec created
↓
never escapes
↓
fixed maximum size
```

và biến nó thành stack/inline storage hoặc thậm chí loại bỏ allocation hoàn toàn.

---

# 170.7. `Vec` và ownership

```ax
let a = Vec<i32>::new();
let b = a;
```

là **Move**.

Không clone toàn bộ vector.

Sau move:

```text
a → MOVED
b → OWNER
```

Nếu cần duplicate:

```ax
let b = a.clone();
```

là explicit và có cost.

---

# 170.8. `Vec` và `view`

```ax
let v = Vec<i32>::new();

let xs = v.view();
```

`xs` là READ capability.

Nếu vector có thể relocate hoặc mutate theo cách làm invalid `xs`, compiler phải ngăn operation đó.

Ví dụ:

```text
Vec
 │
 └── Str/View
       │
       └── READ capability
```

Không cần programmer viết lifetime.

---

# 170.9. Mutable view

```ax
let xs = v.view_mut();
```

là exclusive WRITE capability.

Trong thời gian capability tồn tại:

```text
conflicting read/write
conflicting write/write
relocation
```

không được phép nếu compiler không chứng minh an toàn.

---

# 170.10. Collection mutation invalidation

Axiom không dùng một bảng "iterator invalidation" đơn giản cho mọi collection.

Thay vào đó compiler/library contract mô tả:

```text
operation
+
storage effect
+
region effect
+
capability invalidation
```

Ví dụ:

```text
Vec.push
    may:
        change length
        write new element
        relocate storage
```

Trong khi một operation chỉ sửa giá trị của element có thể không invalidate toàn bộ collection view nếu capability analysis chứng minh vùng không xung đột.

---

# 170.11. Iterator không phải object bắt buộc

Iterator từ `Vec`:

```ax
for x in v {
    ...
}
```

có thể compile trực tiếp thành:

```text
index
+
bounds
+
load
```

Không bắt buộc:

```text
heap allocation
virtual call
iterator object
reference counting
```

Do đó iterator abstraction vẫn zero-cost.

---

# 170.12. `into_iter`

Ba semantics cần phân biệt:

```text
iter()
    → read

iter_mut()
    → exclusive mutation

into_iter()
    → ownership transfer
```

`into_iter()` không clone elements.

```ax
for x in v.into_iter() {
    ...
}
```

chuyển ownership từng element.

Nếu loop kết thúc sớm, phần còn lại vẫn phải được Drop đúng semantic rules.

---

# 170.13. `SmallVec` / `InlineVec`

Một collection có thể có inline storage:

```ax
SmallVec<i32, 8>
```

Ý nghĩa:

```text
0..8 elements
    → inline storage

>8
    → dynamic storage
```

Đây là **library abstraction**, không phải language primitive.

Compiler vẫn có thể tối ưu representation.

---

# 170.14. Quan trọng: không biến SmallVec thành "stack-only"

Inline capacity không đồng nghĩa toàn bộ object luôn nằm stack.

Semantic contract chỉ nói:

```text
up to N elements may use inline storage
```

Storage location thực tế vẫn do compiler quyết định.

Nếu object nằm trong heap thì inline buffer cũng có thể nằm trong heap object.

---

# 170.15. `Deque`

`Deque<T>` không cần contiguous representation.

Có thể dùng:

```text
ring buffer
segmented buffer
block deque
```

Semantic chỉ cần:

```text
ordered sequence
front insertion/removal
back insertion/removal
```

Nếu programmer cần contiguous:

```ax
deque.contiguous_view()
```

có thể trả capability hoặc materialize một buffer tùy contract.

---

# 170.16. Ring buffer

`RingBuffer<T,N>` là fixed-capacity collection đặc biệt hữu ích cho:

```text
network
audio
logging
producer/consumer
embedded
GPU staging
streaming
```

Có thể có representation:

```text
buffer[N]
head
tail
```

Không allocation.

Compiler biết capacity compile-time.

---

# 170.17. Map/Set

Map và Set không phải language primitives.

```text
HashMap<K,V>
BTreeMap<K,V>
HashSet<T>
BTreeSet<T>
```

là library types.

Lựa chọn cấu trúc dữ liệu trở thành lựa chọn semantic/performance của programmer, nhưng không kéo theo pointer/lifetime complexity.

---

# 170.18. `HashMap`

HashMap semantic:

```text
key → value
```

Không guarantee thứ tự iteration trừ khi collection contract nói rõ.

Hash function phải là explicit component/trait abstraction.

Không được phụ thuộc vào random process ngầm nếu deterministic behavior được yêu cầu.

Ví dụ:

```ax
HashMap<K,V, H>
```

hoặc default hasher của std.

---

# 170.19. Hashing và security

Hashing có thể có hai mục tiêu khác nhau:

```text
fast deterministic hashing
security-oriented hashing
```

Axiom không ép mọi HashMap sử dụng cryptographic hash vì sẽ làm mất performance.

Nhưng security-sensitive collection có thể chọn hasher phù hợp.

---

# 170.20. BTree

`BTreeMap` phù hợp khi cần:

```text
ordered keys
range query
stable ordering semantics
```

API:

```ax
map.range(a..b)
```

có thể trả view/iterator thay vì tạo collection mới.

---

# 170.21. Collection views

Một nguyên tắc xuyên suốt:

```text
Collection
   ↓
view
   ↓
algorithm
```

thay vì:

```text
Collection
   ↓
copy
   ↓
temporary collection
   ↓
algorithm
```

Ví dụ:

```ax
sum(values.view())
```

không allocation.

Slice:

```ax
let part = values.slice(10..20);
```

nên tạo `view<T>` chứ không copy.

---

# 170.22. Slice/view provenance

Một view phải giữ semantic provenance:

```text
owner
region
access
lifetime
storage domain
```

Ví dụ:

```text
Vec A
 ├── element 0..10
 │      └── view X
 │
 └── element 10..20
        └── view Y
```

Compiler có thể chứng minh:

```text
X ∩ Y = ∅
```

và cho phép hai mutable operations song song.

Đây là nền tảng cho auto-vectorization và parallelism.

---

# 170.23. Parallel collection operations

Không tự động biến:

```ax
values.map(f)
```

thành parallel.

Parallel phải explicit:

```ax
values.par_map(f)
values.par_reduce(...)
```

Lý do:

- scheduling observable ở một số trường hợp
- ordering
- synchronization
- performance không phải lúc nào cũng tốt
- side effects.

Compiler vẫn có thể auto-parallelize trong những context có semantic contract phù hợp.

---

# 170.24. Collection + SIMD

Compiler có thể nhận ra:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

và kết hợp:

```text
Vec
+
view
+
range
+
alias proof
+
bounds proof
+
Scalar Evolution
+
SIMD
```

để sinh vectorized code.

Programmer không cần chuyển sang raw pointers.

Đây chính là lợi thế lớn của capability model Axiom.

---

# 170.25. Collection + data-oriented design

Axiom nên có các abstraction rõ ràng cho:

```text
Array of Structures
Structure of Arrays
Array of Structures of Arrays
packed arrays
sparse arrays
```

Không nên bắt compiler đoán mọi transformation nếu representation đã observable.

Ví dụ:

```ax
SoA<Particle>
```

có thể cung cấp:

```text
positions[]
velocities[]
mass[]
health[]
```

để SIMD/cache/GPU tối ưu tự nhiên.

---

# 170.26. `SoA` là library type

Không biến:

```text
struct Particle
```

thành SoA một cách âm thầm nếu programmer có thể quan sát layout/address.

Thay vào đó:

```ax
SoA<Particle>
```

có semantic contract rõ.

Compiler có thể tối ưu nó mạnh hơn nữa.

Điều này giữ nguyên nguyên tắc:

```text
implicit optimization
≠
implicit semantic representation change
```

---

# 170.27. Arena collections

Arena:

```ax
Arena<T>
```

cho phép allocation hàng loạt với lifetime của arena.

Ví dụ:

```text
Arena
 ├── object A
 ├── object B
 ├── object C
 └── ...
```

Khi arena bị drop:

```text
toàn bộ storage được release
```

Không cần từng object phải được individually heap-freed nếu semantic contract cho phép.

Tuy nhiên các object có custom Drop vẫn phải được xử lý đúng semantic cleanup.

---

# 170.28. Generational handles

Khi cần identity ổn định mà không cần stable pointer:

```ax
EntityId
Handle<T>
GenerationHandle<T>
```

Ví dụ:

```text
Handle
    index
    generation
```

Handle là **logical identity**, không phải memory capability.

Điều này rất phù hợp cho:

```text
game
GUI
ECS
resource manager
GPU resource tables
```

và tránh ép programmer giữ raw pointer.

---

# 170.29. Concurrent collections

Concurrent collections không được biến `Vec` bình thường thành thread-safe một cách implicit.

Ví dụ:

```text
ConcurrentQueue
ConcurrentMap
AtomicRingBuffer
MpscQueue
```

có synchronization contract riêng.

Axiom giữ nguyên:

```text
Ownership
+
Send
+
Share
+
Capability
+
Synchronization
```

không gộp thành một "thread-safe collection magic".

---

# 170.30. Collection thread safety

Ví dụ:

```text
Arc<Vec<T>>
```

chỉ nói về shared ownership.

Không tự động có nghĩa:

```text
concurrent mutation safe
```

Muốn mutate:

```text
Arc<Mutex<Vec<T>>>
```

hoặc concurrent collection phù hợp.

`Arc` không biến `Vec<T>` thành concurrent mutable structure.

---

# 170.31. Collection Drop

Collection phải obey Drop semantics.

Ví dụ:

```text
Vec<Resource>
```

khi drop:

```text
for each initialized element:
    Drop(element)
```

theo deterministic order được collection contract xác định.

Compiler có thể tối ưu nếu:

```text
T: trivial Drop
```

và không có observable cleanup.

---

# 170.32. Partial initialization

Collection construction không được yêu cầu:

```text
initialize all N elements first
```

nếu semantic operation chỉ tạo một phần.

Ví dụ:

```text
Vec<T>
```

có:

```text
capacity = 1024
length = 10
```

chỉ 10 elements là initialized.

Các slot còn lại không phải `T` values.

Điều này rất quan trọng cho performance và safety.

---

# 170.33. Uninitialized storage

Collection implementation có thể sử dụng uninitialized backing storage nội bộ.

Nhưng:

```text
uninitialized bytes
```

không được coi là:

```text
valid T
```

Compiler verifier phải phân biệt:

```text
UNINIT
INIT
MOVED
DROPPED
```

như ownership model đã quy định.

---

# 170.34. Growth policy

Growth factor của `Vec` không phải language semantic.

Standard library có thể thay đổi:

```text
capacity growth
allocation strategy
small-buffer optimization
```

miễn là không phá API contract.

Do đó programmer không nên dựa vào implementation detail như:

```text
push luôn tăng x2
```

trừ khi collection documentation explicit contract.

---

# 170.35. `reserve`

```ax
v.reserve(n);
```

là performance hint/semantic capacity guarantee tùy API.

Sau `reserve`, compiler/library có thể đảm bảo đủ capacity cho số lượng element đã yêu cầu.

Nhưng:

> `reserve` không biến storage thành stable-address storage.

Live view vẫn phải được tôn trọng.

---

# 170.36. Allocation failure

Allocation failure phải thuộc profile/runtime policy.

Các profile có thể chọn:

```text
Result
panic
abort
custom allocator failure
```

Core không hard-code một global behavior.

Ví dụ library API có thể:

```text
try_push(...)
    → Result<(), AllocError>
```

cho code cần recoverable allocation failure.

---

# 170.37. Collection API không giấu cost

Axiom ưu tiên API khiến cost rõ ràng về mặt semantic.

Ví dụ:

```text
view       → không ownership/copy
clone      → duplicate
collect    → materialize
sort       → mutation
to_string  → owned String
```

Compiler được phép tối ưu physical cost xuống thấp hơn, nhưng abstraction không được làm programmer hiểu sai semantic cost.

---

# 170.38. Collection algorithm composition

Ví dụ:

```ax
let result =
    values
        .view()
        .filter(...)
        .map(...)
        .take(...)
        .collect();
```

Compiler có thể biến toàn bộ thành một loop:

```text
load
check
predicate
transform
store
```

Không nhất thiết tạo:

```text
Filter object
Map object
Take object
temporary arrays
```

Đây là zero-cost generic programming.

---

# 170.39. Fusion

Các operation:

```text
map
filter
zip
take
skip
fold
```

có thể fuse khi semantics cho phép.

Compiler có thể loại bỏ abstraction boundary.

Nhưng side effects và evaluation order vẫn phải được giữ nguyên.

---

# 170.40. Collection và cache

Compiler/library có thể dùng:

```text
element size
access frequency
stride
working set
hot/cold data
```

để tối ưu.

Các collection chuyên biệt có thể cung cấp:

```text
PackedVec
AlignedVec
SoA
BlockedMatrix
RingBuffer
```

thay vì ép một collection universal làm mọi việc.

---

# 170.41. Alignment

Collection có thể có explicit alignment contract:

```ax
AlignedVec<f32, 64>
```

nếu library cần.

Nhưng compiler không được giả định alignment cao hơn contract.

Nếu alignment là observable/ABI-relevant thì LayoutDB phải giữ constraint.

---

# 170.42. Device/GPU collections

GPU collection phải phân biệt:

```text
HostVec<T>
DeviceVec<T>
DeviceBuffer<T>
UnifiedBuffer<T>
```

Không có implicit:

```text
host collection
→
GPU memory
```

vì đó có thể gây allocation/copy/synchronization lớn.

GPU views tiếp tục sử dụng:

```text
view<T>
mut_view<T>
```

nhưng storage domain là Device.

---

# 170.43. Collection và FFI

Không được truyền trực tiếp:

```text
Vec<T>
```

sang C ABI chỉ vì physical representation "trông giống":

```text
pointer + length + capacity
```

Nếu muốn FFI:

```text
@repr(C)
```

hoặc explicit FFI wrapper.

Semantic ownership của allocation cũng phải được xác định.

---

# 170.44. Collection representation contract

Mặc định:

```text
semantic collection
    ≠
physical representation
```

Nếu programmer cần layout cụ thể:

```text
@repr(...)
```

hoặc specialized FFI/container contract.

Compiler được phép:

```text
reorder
scalarize
split
inline
promote
eliminate
```

khi không phá representation contract.

---

# 170.45. Compiler hooks

Collections nên expose compiler-readable metadata:

```text
CollectionKind
ElementType
LengthKnowledge
CapacityKnowledge
Contiguity
Ordering
MutationInvalidation
AliasContract
StorageDomain
IteratorProperties
Complexity
```

Nhờ đó compiler có thể hiểu:

```text
Vec
```

mà không cần hard-code toàn bộ stdlib implementation.

---

# 170.46. Complexity contracts

Library có thể mô tả:

```text
push       amortized O(1)
index      O(1)
pop        O(1)
HashMap lookup expected O(1)
BTree lookup O(log n)
```

Nhưng complexity là API contract, không phải compiler semantic primitive.

Compiler có thể tối ưu implementation.

---

# 170.47. Collection trait architecture

Không tạo một trait khổng lồ kiểu:

```text
Collection<T>
```

chứa mọi thứ.

Thay vào đó compositional traits:

```text
Iterable
Collection
Sequence
MutableSequence
Contiguous
RandomAccess
Capacity
Resizable
MapLike
SetLike
```

Giống triết lý numeric/iterator trước đó.

---

# 170.48. Generic specialization

Ví dụ:

```ax
fn sum<T: Numeric>(xs: view<T>) -> T
```

với:

```text
T = i32
T = f32
T = f64
```

có thể được specialization.

Compiler có thể sinh:

```text
scalar i32
SIMD i32
scalar f32
SIMD f32
...
```

mà API vẫn giữ nguyên.

---

# 170.49. Collection không được ép dynamic dispatch

Generic:

```ax
fn process<T: Iterator>(x: T)
```

mặc định static dispatch.

Không tạo:

```text
vtable
heap object
indirect call
```

trừ khi programmer sử dụng:

```text
dyn Trait
```

---

# 170.50. Collection identity

Axiom giữ ba tầng:

```text
Value Identity
Storage Identity
Logical Identity
```

Ví dụ `Vec<T>`:

```text
Vec value
    ↓
storage allocation
    ↓
elements
```

Nếu storage relocate:

```text
storage identity thay đổi
```

nhưng collection value vẫn là cùng semantic object.

Nếu application cần identity ổn định:

```text
Handle<T>
EntityId
```

không dựa vào physical address.

---

# 170.51. Collection và compiler optimization pipeline

Collections là consumer trực tiếp của:

```text
Ownership
Capability
Alias
Escape
Effect
SSA
MemorySSA
Loop Analysis
Range Analysis
SIMD
Layout
PGO
LTO
```

Ví dụ:

```text
Vec<T>
 ↓
view<T>
 ↓
range
 ↓
bounds proof
 ↓
alias proof
 ↓
MemorySSA
 ↓
loop optimization
 ↓
SIMD
 ↓
machine code
```

Mục tiêu cuối:

```text
high-level Axiom
        ↓
không pointer arithmetic
không borrow syntax
không manual lifetime
        ↓
machine code tương đương một implementation C tối ưu
```

Đây là một trong những điểm mà kiến trúc Axiom hiện tại có lợi thế rõ rệt. memcite

---

# 170.52. Các invariant đóng băng

### Collection semantics

- **ACOL-20** — Collections là library abstractions ngoại trừ Array/View primitives.
- **ACOL-21** — Collection ownership tuân theo Axiom ownership model.
- **ACOL-22** — Collection không yêu cầu programmer quản lý raw pointers/lifetimes.
- **ACOL-23** — `Vec` là owned growable sequence.
- **ACOL-24** — `Vec` không mặc định stable-address.
- **ACOL-25** — relocation phải tôn trọng live capabilities.
- **ACOL-26** — `view` không allocation/copy theo semantic contract.
- **ACOL-27** — `mut_view` là exclusive WRITE capability.
- **ACOL-28** — `into_iter` chuyển ownership, không implicit clone.
- **ACOL-29** — collection Drop deterministic.
- **ACOL-30** — uninitialized capacity không phải initialized elements.

### Performance

- **ACOL-31** — collection abstraction không được yêu cầu heap allocation nếu semantics không cần.
- **ACOL-32** — compiler được phép stack/register/inline-promote collection storage.
- **ACOL-33** — allocation elimination được phép khi escape/identity/address semantics cho phép.
- **ACOL-34** — iterator và collection adapters có thể được fusion.
- **ACOL-35** — bounds checks có thể được loại bỏ khi Range/Capability analysis chứng minh an toàn.
- **ACOL-36** — capability facts có thể cung cấp NoAlias cho optimizer.
- **ACOL-37** — UNKNOWN alias không được coi là NoAlias.
- **ACOL-38** — contiguous collections có thể được vectorize khi legality/profitability cho phép.
- **ACOL-39** — representation optimization không được thay đổi observable semantics.

### Specialized collections

- **ACOL-40** — Small/Inline collections là library abstractions.
- **ACOL-41** — SoA là explicit data-layout abstraction khi layout semantics cần bảo đảm.
- **ACOL-42** — Arena storage có lifetime contract riêng.
- **ACOL-43** — Handle là logical identity, không phải memory capability.
- **ACOL-44** — concurrent collections phải có synchronization contract riêng.
- **ACOL-45** — `Arc<T>` không tự biến `T` thành mutable thread-safe.
- **ACOL-46** — GPU collections phải phân biệt storage domain.
- **ACOL-47** — FFI collection layout/ownership phải explicit.

### API/Compiler

- **ACOL-48** — collection complexity contract không phải semantic optimization assumption.
- **ACOL-49** — compiler có thể specialization generic collections.
- **ACOL-50** — dynamic dispatch chỉ xuất hiện khi explicit hoặc ABI yêu cầu.
- **ACOL-51** — collection metadata có thể được compiler/IDE/AI query.
- **ACOL-52** — optimization không được thay đổi collection ownership/capability semantics.
- **ACOL-53** — collection behavior không phụ thuộc optimization level.
- **ACOL-54** — deterministic/reproducible compilation không được phụ thuộc task scheduling.
- **ACOL-55** — safe collection APIs không tạo dangling capabilities.

---

# Kết luận BOOTSTRAP-170

Kiến trúc collection của Axiom nên xoay quanh:

```text
        SEMANTIC
           │
   ┌───────┼────────┐
   │       │        │
Ownership Capability Iterator
   │       │        │
   └───────┼────────┘
           ↓
      Collection
           ↓
    Escape + Alias
           ↓
      MemorySSA
           ↓
   Loop + SIMD + Cache
           ↓
       Machine Code
```

Điểm quan trọng nhất là **không cần lựa chọn giữa "dễ dùng" và "hiệu năng thấp"**.

Axiom để programmer viết:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

nhưng compiler có thể chứng minh:

```text
ownership ✓
bounds ✓
alias ✓
capability ✓
escape ✓
```

rồi sinh code vectorized, bounds-check-free, allocation-free.

Đó chính là hướng **"compiler understands more than programmer must write"** mà Axiom đang theo đuổi. memcite

**BOOTSTRAP-170 — FROZEN.**

---

# BOOTSTRAP-171 — Error Handling, Result/Option, Panic, Contracts & Failure Semantics

Task kế tiếp cần giải quyết một phần còn rất quan trọng của ngôn ngữ systems:

```text
Result<T,E>
Option<T>
?
panic
abort
unwind
recoverable failure
resource cleanup
error propagation
error composition
FFI errors
OS errors
allocation failure
async cancellation
GPU/device failure
contracts
```

Đặc biệt cần chốt một vấn đề nền tảng:

> **Làm sao Axiom có error handling mạnh như ngôn ngữ hiện đại nhưng không biến mọi function call thành exception machinery, hidden allocation hoặc runtime overhead?**