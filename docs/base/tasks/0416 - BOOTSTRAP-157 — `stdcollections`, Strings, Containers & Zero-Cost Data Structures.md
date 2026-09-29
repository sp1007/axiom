# BOOTSTRAP-157 — `std::collections`, Strings, Containers & Zero-Cost Data Structures
**STATUS: FROZEN / COMPLETED**

> **Programmer mô tả cấu trúc dữ liệu theo semantic need; compiler có quyền chọn representation tối ưu khi representation đó không observable.**

Đây là bước quan trọng vì Axiom không nên biến `Vec`, `HashMap`, `String` thành những container “cứng” khiến programmer phải tự quyết stack/heap/layout.

---

## 1. Nguyên tắc container

Axiom phân biệt:

```text
Semantic Container
        ↓
Representation
        ↓
Storage strategy
        ↓
Machine layout
```

Ví dụ:

```ax
Vec<i32>
```

chỉ có nghĩa:

```text
ordered, growable, owned sequence
```

Không có nghĩa bắt buộc:

```text
heap + pointer + length + capacity
```

---

# 2. Container mặc định: `Vec<T>`

`Vec<T>` là dynamic contiguous sequence.

Semantic guarantees:

- phần tử có thứ tự;
- indexable;
- contiguous logical storage;
- grow/shrink;
- ownership của elements;
- relocation có thể xảy ra.

Không guarantee:

- stable address;
- heap allocation;
- một representation cụ thể.

---

# 3. Compiler có thể tối ưu `Vec`

Ví dụ:

```ax
fn sum(xs: Vec<i32>) -> i32 {
    ...
}
```

Nếu compiler chứng minh `xs`:

```text
NoEscape
```

và lifetime ngắn:

```text
Vec
 ↓
allocation
 ↓
scalarization
 ↓
SSA/registers
```

thậm chí allocation có thể biến mất hoàn toàn.

---

# 4. Nhưng không biến `Vec` thành container khác tùy tiện

Compiler **không được thay đổi semantic contract**.

Ví dụ API yêu cầu:

```text
contiguous
```

thì compiler không thể biến nó thành linked list.

Đây là khác biệt giữa:

```text
representation optimization
```

và:

```text
semantic substitution
```

---

# 5. `Array<T, N>`

Fixed-size array:

```ax
let a: [i32; 8];
```

được đảm bảo:

```text
fixed length
ordered
contiguous
```

đã frozen từ memory/layout model.

---

# 6. Stack array

Compiler có thể đặt:

```ax
[i32; 1024]
```

trên:

```text
register
stack
inline aggregate
```

tùy escape/lifetime.

Không có keyword:

```text
stack_array
```

trong Core.

---

# 7. `ArrayVec`

Đối với workload có giới hạn:

```ax
ArrayVec<i32, 64>
```

semantic:

```text
capacity fixed at compile time
inline storage
```

Ở đây **inline storage là observable contract** nếu API phụ thuộc vào nó.

Vì vậy compiler không được tự biến nó thành arbitrary heap storage.

---

# 8. `SmallVec`

Có thể có:

```ax
SmallVec<T, N>
```

semantic:

```text
inline up to N
grow beyond N
```

Đây là một **hybrid storage contract**, khác `Vec`.

Compiler vẫn có thể tối ưu implementation nhưng phải giữ behavior của threshold nếu threshold observable.

---

# 9. Arena collections

```ax
Arena<T>
```

có semantic:

```text
bulk lifetime
```

Các object sống cùng arena.

Drop:

```text
Arena.drop()
 ↓
release contained resources
```

theo contract.

---

# 10. Pool

```ax
Pool<T>
```

phù hợp object reuse:

```text
acquire
release
acquire
```

Nhưng `release` không nhất thiết hủy physical storage.

Do đó:

```text
object lifetime
```

và:

```text
storage lifetime
```

vẫn tách biệt.

---

# 11. Slab

```ax
Slab<T>
```

thích hợp identity/slot-based storage:

```text
Handle
 ↓
Slab slot
 ↓
T
```

Có thể hỗ trợ:

```text
generation
```

để tránh stale handle.

---

# 12. Handle

Handle không phải pointer:

```text
Handle<T>
```

có thể chứa:

```text
index
generation
```

Compiler không coi nó là memory capability.

---

# 13. Logical identity

Đây là một trong những abstraction quan trọng của Axiom:

```text
Value Identity
Storage Identity
Logical Identity
```

Ví dụ game entity:

```text
EntityId
```

giữ identity ngay cả khi object:

```text
move
relocate
compact
reorder
```

---

# 14. Vì sao Handle quan trọng với Data-Oriented Design

Nếu application dùng:

```ax
EntityId
```

thay vì raw pointer:

```text
EntityId
 ↓
storage can move
 ↓
SoA transformation possible
 ↓
cache optimization possible
```

Đây chính là cơ sở để Axiom tối ưu layout mạnh mà không phá semantic identity.

---

# 15. `HashMap`

Semantic:

```text
key → value
```

không đảm bảo physical bucket layout.

Compiler/library có thể lựa chọn:

```text
open addressing
Robin Hood
Swiss-table-like
chaining
specialized hash table
```

tùy implementation.

---

# 16. HashMap specialization

Compiler có thể nhận ra:

```ax
HashMap<Enum, T>
```

hoặc:

```ax
HashMap<u8, T>
```

và specialize thành representation hiệu quả hơn nếu semantics vẫn tương đương.

---

# 17. `BTreeMap`

Dùng khi cần:

```text
ordered keys
range query
```

Không nên ép `HashMap` làm tất cả.

Axiom standard library nên cung cấp nhiều container có semantic contract rõ ràng.

---

# 18. `HashSet`

```ax
HashSet<T>
```

là set semantics:

```text
unique elements
```

Không được dựa vào hash-table byte representation cho equality.

---

# 19. `BTreeSet`

Ordered set.

Có thể hỗ trợ:

```text
range
min
max
predecessor
successor
```

mà không cần expose tree implementation.

---

# 20. `Deque`

```ax
Deque<T>
```

semantic:

```text
push_front
push_back
pop_front
pop_back
```

Không đảm bảo contiguous representation.

---

# 21. `List`

Axiom **không nên có một `List<T>` mặc định mang semantics mơ hồ**.

Nếu linked list thực sự cần:

```ax
LinkedList<T>
```

phải nói rõ semantics/performance characteristics.

---

# 22. Container specialization

Một generic container có thể được compiler specialize theo:

```text
T size
T alignment
T Drop
T Copy
T access pattern
capacity
target
hotness
```

Ví dụ:

```text
Vec<u8>
```

có thể được tối ưu rất khác:

```text
Vec<LargeDropType>
```

---

# 23. `Drop` ảnh hưởng container

Container chứa:

```text
T: Drop
```

phải cleanup từng element.

Nếu:

```text
T: trivial Drop
```

compiler có thể eliminate toàn bộ element destruction.

---

# 24. Partial initialization

Một container đang xây dựng:

```text
capacity = 100
initialized = 37
```

phải được verifier hiểu.

Nếu construction thất bại tại element 38:

```text
drop elements 0..37
release storage
```

Không double-drop.

---

# 25. `Vec` growth

Growth semantic:

```text
capacity < required
        ↓
allocate/grow
        ↓
move elements
        ↓
old storage release
```

Compiler phải đảm bảo:

```text
live view
```

ngăn relocation.

---

# 26. View và container

Ví dụ:

```ax
let v = view(xs);
```

Trong khi `v` còn sống:

```ax
xs.push(...)
```

nếu có khả năng relocate vùng đang được view:

```text
E_CAPABILITY_CONFLICT
```

Đây là safety rule, không phải runtime check.

---

# 27. Slice/view

Axiom nên có abstraction:

```text
view<T>
mut_view<T>
```

làm nền cho container APIs.

Ví dụ:

```ax
fn sort(xs: mut_view<i32>)
```

không cần pointer/reference syntax.

---

# 28. String architecture

```text
String
Str
Bytes
```

giữ nguyên ba semantic categories.

---

# 29. `String` representation

Semantic:

```text
owned UTF-8 text
```

Physical có thể:

```text
SSO
heap buffer
inline buffer
rope
```

**nhưng chỉ được dùng rope nếu API semantics cho phép các đặc tính tương ứng.**

---

# 30. SSO

`String` có thể dùng:

```text
Small String Optimization
```

với short strings.

Compiler/library có thể lựa chọn representation.

Nếu inline capacity không observable, compiler có thể thay đổi nó.

---

# 31. `Str`

`Str` là read-only UTF-8 view:

```text
provenance
region
length
```

Không sở hữu bytes.

---

# 32. Mutable string view

Có thể dùng:

```ax
mut_view<u8>
```

cho low-level UTF-8 manipulation.

Nhưng việc tạo `String` hợp lệ phải đảm bảo UTF-8 invariant.

---

# 33. UTF-8 mutation

Không cho safe API tạo:

```text
invalid String
```

Nếu sửa raw bytes:

```text
Bytes
```

sau đó validate:

```text
Bytes → String
```

---

# 34. Unicode iteration

Không đồng nhất:

```text
byte
code point
grapheme
```

Standard library nên cung cấp từng abstraction.

Ví dụ:

```text
bytes()
chars()
graphemes()
```

Unicode-heavy operations có thể nằm ngoài `std::core`.

---

# 35. String indexing

Không nên cho:

```ax
s[i]
```

trả `char` nếu indexing theo byte làm người dùng hiểu sai.

Có thể:

```ax
s.byte_at(i)
s.char_at(i)
```

với semantics rõ ràng.

---

# 36. `Bytes`

```ax
Bytes
```

là owning byte buffer.

Không có UTF-8 invariant.

Có thể dùng trực tiếp cho:

```text
network
file
serialization
crypto
compression
```

---

# 37. `ByteView`

Có thể alias semantic:

```text
view<u8>
```

hoặc có newtype:

```text
BytesView
```

khi cần API clarity.

Không cần thêm Core primitive.

---

# 38. Zero-copy

API nên ưu tiên:

```text
Buffer ownership transfer
```

thay vì:

```text
copy
```

Ví dụ:

```text
File.read()
 ↓
Bytes
 ↓
Network.send(Bytes)
```

có thể transfer ownership.

---

# 39. Async zero-copy

Đã có model:

```text
read_async(buffer)
    → Future<(Buffer, usize)>
```

Storage phải giữ valid đến completion.

---

# 40. Container + Send

`Vec<T>` chỉ Send khi semantic contents/storage contract đáp ứng Send.

Không có:

```text
unsafe impl Send
```

để programmer tự gắn thuộc tính giả.

---

# 41. Container + Share

`Arc<Vec<T>>`:

```text
shared ownership
```

không biến:

```text
Vec<T>
```

thành mutable concurrent container.

Muốn mutate cần synchronization abstraction.

---

# 42. Hashing

Trait:

```text
Hash
```

phải hash semantic value.

Không mặc định hash:

```text
raw object bytes
```

---

# 43. Equality

Container equality:

```text
Vec<A> == Vec<B>
```

dựa trên semantic element equality và sequence semantics.

Không phụ thuộc capacity.

---

# 44. Ordering

`Vec` ordering:

```text
lexicographic
```

nếu trait contract yêu cầu.

Physical layout không liên quan.

---

# 45. Iterators

Container API phải expose iterator abstraction.

Ví dụ:

```ax
for x in xs {
    ...
}
```

compiler có thể:

```text
inline iterator
 ↓
induction variable
 ↓
bounds elimination
 ↓
vectorization
```

Không tạo iterator heap object.

---

# 46. Iterator fusion

Ví dụ:

```ax
xs
    .map(...)
    .filter(...)
    .map(...)
    .sum()
```

có thể được compiler biến thành **một loop**.

Không cần intermediate arrays.

---

# 47. Allocation elimination

Ví dụ:

```ax
let a = xs.map(f);
let b = a.map(g);
return b.sum();
```

có thể trở thành:

```text
single traversal
```

nếu semantics/effects cho phép.

---

# 48. `collect`

Khi thực sự cần materialize:

```ax
let result = iterator.collect<Vec<_>>();
```

thì allocation là observable nếu API contract làm nó observable.

Compiler vẫn có thể:

```text
pre-size
reserve
eliminate intermediate
```

nhưng không được thay đổi externally visible semantics.

---

# 49. Container growth hints

Có thể:

```ax
reserve(n)
```

nhưng đây là optimization/storage operation.

Không được biến:

```text
reserve
```

thành stable-address guarantee.

---

# 50. Explicit stable container

Nếu cần stable addresses:

```text
StableVec
SlotMap
Slab
Arena
```

là các semantic abstractions thích hợp.

---

# 51. SoA

Axiom nên cung cấp explicit:

```text
SoA<T>
```

hoặc:

```text
StructOfArrays<T>
```

trong std.

Ví dụ:

```ax
struct Particle {
    pos: Vec3,
    velocity: Vec3,
    mass: f32,
}
```

Có thể có:

```text
SoA<Particle>
```

representation:

```text
positions[]
velocities[]
mass[]
```

---

# 52. Tại sao SoA không mặc định

Nếu compiler tự động biến mọi:

```text
Vec<Particle>
```

thành SoA:

```text
&particle
```

address/identity/FFI/layout semantics có thể thay đổi.

Do đó:

```text
Vec<Particle>
```

giữ contiguous array-of-struct semantics.

`SoA` là explicit semantic container.

---

# 53. Nhưng compiler vẫn có thể structure-split

Nếu:

```text
address never observed
identity irrelevant
layout not externally visible
```

compiler có thể thực hiện structure splitting nội bộ.

Đó là optimization, không phải semantic API guarantee.

---

# 54. Data-oriented APIs

Có thể cung cấp:

```text
columns()
column<T>()
```

cho SoA.

Nhưng các column views phải tuân capability model.

---

# 55. Parallel containers

Không nên có:

```text
ConcurrentVec
```

chỉ bằng cách thêm atomic vào mọi field.

Concurrent container phải có semantic synchronization contract riêng.

---

# 56. Lock-free containers

Có thể nằm ở:

```text
std::sync
```

không phải `std::core`.

Ví dụ:

```text
MPSCQueue
SPSCQueue
MPMCQueue
```

được specialize theo topology.

---

# 57. Memory locality

Container metadata có thể được optimizer dùng:

```text
element size
stride
alignment
access frequency
```

để tối ưu:

```text
prefetch
vectorization
cache layout
```

nhưng không thay đổi semantic contract.

---

# 58. Hot/cold containers

Compiler có thể phát hiện:

```text
hot path → fields A/B
cold path → field C/D
```

và áp dụng layout transformation nếu không observable.

Đây là sự kết hợp:

```text
ALAYOUT
+
AMEMOPT
+
APGO
```

---

# 59. Container ABI

Public API:

```ax
pub fn foo(xs: Vec<i32>)
```

không mặc định có stable binary representation.

Nếu FFI:

```ax
extern "C"
```

thì `Vec` **không tự động trở thành C ABI-compatible**.

Phải dùng explicit FFI-safe representation.

---

# 60. FFI buffers

Ví dụ:

```ax
extern "C" fn process(data: view<u8>)
```

ABI lowering có thể là:

```text
pointer + length
```

nhưng semantic type vẫn là:

```text
view<u8>
```

---

# 61. Serialization

Không serialize bằng raw memory layout mặc định.

Phải có:

```text
Encode
Decode
```

hoặc serialization traits.

Như vậy:

```text
memory layout
```

và:

```text
wire format
```

vẫn độc lập.

---

# 62. Container memory safety

Các invariant chính:

```text
index < len
initialized element
valid ownership
valid capability
valid storage
```

được verifier/compiler chứng minh.

Runtime bounds check chỉ tồn tại khi compile-time proof chưa đủ.

---

# 63. Bounds-check elimination

Ví dụ:

```ax
for i in 0..xs.len {
    sum += xs[i];
}
```

Compiler:

```text
Scalar Evolution
+
Range Analysis
+
Loop Analysis
```

có thể chứng minh:

```text
0 <= i < len
```

→ loại bounds check.

---

# 64. Container specialization theo target

Ví dụ CPU có:

```text
AVX2
AVX-512
NEON
SVE
RVV
```

thì implementation có thể chọn thuật toán phù hợp.

Không cần thay đổi API.

---

# 65. Generic specialization

Ví dụ:

```ax
sort<T: Ord>(xs: mut_view<T>)
```

có thể specialize:

```text
sort<i32>
sort<f64>
sort<SmallStruct>
```

và inline comparator.

---

# 66. `Vec<u8>` specialization

Một trường hợp đặc biệt quan trọng:

```text
Vec<u8>
```

có thể được tối ưu thành byte buffer operations:

```text
memcpy
memmove
SIMD
vectorized search
```

nhưng vẫn giữ ownership semantics.

---

# 67. String specialization

Tương tự:

```text
String.find(...)
```

có thể dùng:

```text
SIMD byte search
specialized Unicode algorithms
```

tùy operation.

---

# 68. Container API không được “compiler magic”

Đây là nguyên tắc:

```text
Vec
HashMap
String
Arena
```

là ordinary Axiom code.

Compiler chỉ:

```text
understands generic/type/effect/layout
+
optimizes
```

không phải hard-code toàn bộ behavior.

---

# 69. `std::collections` architecture

Đề xuất:

```text
std::collections
├── Vec
├── Deque
├── ArrayVec
├── SmallVec
├── LinkedList
├── HashMap
├── HashSet
├── BTreeMap
├── BTreeSet
├── Arena
├── Pool
├── Slab
├── SlotMap
└── SoA
```

và:

```text
std::string
├── String
├── Str
├── Bytes
└── parsing/encoding helpers
```

---

# 70. Không cần một container “thần kỳ”

Quyết định quan trọng:

**Không tạo `SmartContainer<T>` để compiler tự quyết mọi thứ.**

Thay vào đó:

```text
Vec       → contiguous dynamic
ArrayVec  → fixed inline capacity
SmallVec  → inline + growth
Arena     → bulk lifetime
Slab      → stable slots
SoA       → data-oriented representation
HashMap   → associative unordered
BTreeMap  → ordered associative
```

Compiler tối ưu **bên trong từng semantic contract**.

Điều này dễ dự đoán hơn rất nhiều.

---

# 71. Invariants

Đóng băng:

### `ACOLLECT-20`
Containers are library abstractions, not language primitives unless required for semantic typing.

### `ACOLLECT-21`
Container semantics are distinct from physical representation.

### `ACOLLECT-22`
Compiler may optimize representation when semantic observability permits.

### `ACOLLECT-23`
Compiler may not replace a container with a representation violating its semantic contract.

### `ACOLLECT-24`
`Vec<T>` provides ordered growable contiguous storage semantics.

### `ACOLLECT-25`
`Vec<T>` does not guarantee stable physical address.

### `ACOLLECT-26`
Live capabilities can prevent vector relocation.

### `ACOLLECT-27`
Fixed arrays retain contiguous representation guarantees.

### `ACOLLECT-28`
`ArrayVec` provides explicit inline fixed-capacity semantics.

### `ACOLLECT-29`
`SmallVec` provides explicit inline-plus-growth semantics.

### `ACOLLECT-30`
Arena containers provide explicit bulk-lifetime semantics.

### `ACOLLECT-31`
Pool containers provide explicit storage-reuse semantics.

### `ACOLLECT-32`
Slab/slot containers may provide stable logical slots without exposing raw addresses.

### `ACOLLECT-33`
Handles provide logical identity and are distinct from memory capabilities.

### `ACOLLECT-34`
Logical identity may survive physical relocation.

### `ACOLLECT-35`
Hash maps provide associative semantics independent of bucket representation.

### `ACOLLECT-36`
Ordered maps provide ordering semantics independent of tree representation.

### `ACOLLECT-37`
Container equality is semantic, not bytewise.

### `ACOLLECT-38`
Container hashing is semantic, not raw-memory hashing.

### `ACOLLECT-39`
Container Drop follows element ownership and initialization state.

### `ACOLLECT-40`
Partially initialized containers are cleaned up exactly once.

### `ACOLLECT-41`
Container APIs preserve ownership/capability verification.

### `ACOLLECT-42`
Container views preserve provenance and lifetime constraints.

### `ACOLLECT-43`
Active views can constrain mutation, growth and relocation.

### `ACOLLECT-44`
Bounds checks may be eliminated only through compiler proof.

### `ACOLLECT-45`
Iterator abstractions are intended to be zero-cost.

### `ACOLLECT-46`
Iterator chains may be fused when observable semantics are preserved.

### `ACOLLECT-47`
Intermediate allocations may be eliminated when allocation identity and other observable semantics do not escape.

### `ACOLLECT-48`
`String` contains valid UTF-8.

### `ACOLLECT-49`
`Str` is non-owning UTF-8 text.

### `ACOLLECT-50`
`Bytes` has no UTF-8 validity requirement.

### `ACOLLECT-51`
String representation is not fixed by the semantic type unless explicitly contracted.

### `ACOLLECT-52`
SSO is an implementation optimization unless explicitly exposed as a contract.

### `ACOLLECT-53`
Memory representation and serialization representation remain distinct.

### `ACOLLECT-54`
FFI-safe container representation requires an explicit ABI contract.

### `ACOLLECT-55`
Axiom containers do not become C-compatible merely by being passed to `extern "C"`.

### `ACOLLECT-56`
SoA is an explicit semantic data-oriented container.

### `ACOLLECT-57`
Ordinary contiguous arrays are not silently redefined as SoA.

### `ACOLLECT-58`
Compiler may internally perform structure splitting/AoS transformations when representation is unobservable.

### `ACOLLECT-59`
Container specialization may depend on element type, target, layout, effects and access patterns.

### `ACOLLECT-60`
Generic container specialization cannot bypass safety verification.

### `ACOLLECT-61`
Container implementations may contain unsafe internals behind safe verified APIs.

### `ACOLLECT-62`
Zero-copy ownership transfer is preferred where semantic ownership allows it.

### `ACOLLECT-63`
Concurrent containers require explicit synchronization semantics.

### `ACOLLECT-64`
`Send` and `Share` requirements remain independent for containers.

### `ACOLLECT-65`
Container storage strategy is not automatically equivalent to heap allocation.

### `ACOLLECT-66`
Allocation elimination may remove physical allocation without changing container semantics.

### `ACOLLECT-67`
Container operations remain subject to effect, alias, escape and capability analysis.

### `ACOLLECT-68`
Target SIMD/vector capabilities may specialize container implementations.

### `ACOLLECT-69`
Container abstractions must remain usable without compiler-specific magic.

### `ACOLLECT-70`
`std::collections` must remain implementable primarily in Axiom.

---

# Một quyết định quan trọng đã được chốt

Câu hỏi ở bước trước là:

> Có nên để compiler tự chọn `Vec`/stack/heap/arena/SoA tùy tình huống?

Câu trả lời chính xác là:

**Có, nhưng chỉ bên trong semantic contract của container.**

Ví dụ:

```text
Vec<T>
```

→ compiler được phép:

```text
heap
stack
register
scalarized
SROA
eliminate allocation
```

nếu không observable.

Nhưng:

```text
Vec<T>
```

→ **không tự ý biến thành `SoA<T>`**, vì SoA là một semantic/data-layout contract khác.

Điều này giữ được cả hai mục tiêu:

```text
PROGRAMMER
    ↓
simple semantic choice
    ↓
COMPILER
    ↓
aggressive representation optimization
    ↓
MACHINE
```

mà không biến language thành một hệ thống “compiler đoán mọi thứ” khó dự đoán.

---

# BOOTSTRAP-158 — Error Handling, Panic, Result, Diagnostics & Failure Semantics

Bước tiếp theo nên chốt **failure model hoàn chỉnh của Axiom**, vì hiện tại `Result`, `Option`, `panic`, `abort`, `unwind`, syscall errors, async cancellation, allocation failure và hardware faults đã xuất hiện ở nhiều subsystem nhưng chưa được gom thành một semantic architecture duy nhất.

Trọng tâm:

```text
Normal value
     │
     ├── Option<T>
     ├── Result<T,E>
     ├── panic
     ├── abort
     ├── OS/System error
     ├── cancellation
     └── hardware/process fault
```

và đặc biệt phải quyết định rõ:

> **Axiom có cần exception/`try-catch` kiểu C++/Java/.NET hay không, hay `Result + panic/unwind` đã đủ cho một systems language hiệu năng cao?**