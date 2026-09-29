Tiếp tục với **COLLECTION-001 — Collections & Storage Model**. Đây là phần rất quan trọng vì collection là nơi các quyết định về ownership, `view`, relocation và allocation va chạm trực tiếp với trải nghiệm lập trình.

# COLLECTION-001 — Collections & Storage Model

## 1. Nguyên tắc tổng thể

Axiom không nên biến collection thành một hệ thống quản lý lifetime phức tạp.

Nguyên tắc:

> **Collection quản lý storage; compiler quản lý validity của capability.**

Programmer không viết:

```text
'a
'b
T: 'a
where 'a: ...
```

và cũng không phải tự theo dõi iterator invalidation bằng lifetime annotation.

Thay vào đó compiler biết:

```text
owner
  ↓
storage
  ↓
capability/view
```

và tự phát hiện khi một mutation có thể làm capability mất hiệu lực.

---

# 2. Phân loại collection

Core language chỉ cần một số primitive rất nhỏ:

| Type | Ý nghĩa |
|---|---|
| `[T; N]` | fixed-size array |
| `view<T>` | read-only contiguous view |
| `mut_view<T>` | mutable contiguous view |

Các collection còn lại thuộc standard library:

```text
Vec<T>
String
StringView
Deque<T>
Map<K,V>
Set<T>
SmallVec<T,N>
Arena<T>
Pool<T>
```

Điểm quan trọng:

**Không biến mỗi collection thành một primitive của compiler.**

Compiler chỉ cần hiểu semantic operation như:

```text
ALLOC
REALLOC
MOVE
DROP
VIEW
MUT_VIEW
INDEX
SLICE
```

Library quyết định cách tổ chức chúng.

---

# 3. `[T; N]` — Array

Array là value type:

```axiom
let a: [i32; 4] = [1, 2, 3, 4]
```

Semantics:

```text
size = N * sizeof(T)
storage = inline
ownership = value
```

Nếu `T: Copy`:

```axiom
let b = a
```

thì `b` là một value độc lập.

Nếu `T` không `Copy`:

```axiom
let b = a
```

là Move.

Compiler có thể scalarize:

```text
a[0]
a[1]
a[2]
a[3]
```

thành registers nếu tối ưu được.

Không được mặc định hiểu rằng array luôn nằm trên stack.

---

# 4. `view<T>` — primitive contiguous view

Ví dụ:

```axiom
fn sum(xs: view<i32>) -> i32 {
    ...
}

let a = [1, 2, 3, 4]
sum(a)
```

Implicit owner → temporary view chỉ được phép ở **argument boundary**.

Nếu muốn giữ:

```axiom
let xs = view(a)
```

thì capability tồn tại độc lập trong semantic analysis.

Representation có thể là:

```text
pointer + length
```

nhưng đó là ABI/implementation detail.

---

# 5. `Vec<T>`

`Vec<T>` là collection có storage relocatable mặc định.

Semantic state:

```text
Vec<T>
 ├── logical sequence
 ├── length
 ├── capacity
 └── storage identity
```

Không nên đóng đinh semantic layout thành:

```text
ptr + len + cap
```

vì compiler có thể tối ưu hoặc library có thể dùng representation khác.

Thông thường implementation có thể là:

```text
pointer
length
capacity
```

nhưng đây không phải language guarantee.

---

# 6. Vấn đề quan trọng nhất: View + Vec mutation

Ví dụ:

```axiom
var v = Vec<i32>(...)
let xs = v.view()

v.push(10)

use(xs)
```

Nếu `push()` reallocates:

```text
old storage
    ↓
[1,2,3]
    ↓
new storage
    ↓
[1,2,3,10]
```

thì `xs` không còn hợp lệ.

Axiom **không** giải quyết bằng lifetime annotation.

Thay vào đó:

## Quy tắc

> Một operation có khả năng làm invalid một live capability sẽ bị compiler chặn.

Do đó:

```axiom
var v = ...
let xs = v.view()

v.push(10)   // ERROR
use(xs)
```

Không cần biết `push()` thực tế có realloc hay không.

Chỉ cần semantic contract của `push` là:

```text
MAY_RELOCATE
```

thì mutation conflict với active view.

---

# 7. Nhưng điều này không được làm API trở nên khó chịu

Đây là điểm rất quan trọng.

Ta không muốn programmer phải viết:

```axiom
drop(xs)
v.push(10)
```

mọi nơi.

Compiler nên thực hiện **capability lifetime shortening**.

Ví dụ:

```axiom
var v = Vec<i32>(...)

{
    let xs = v.view()
    print(xs)
}

v.push(10)
```

hoàn toàn hợp lệ.

Nhưng thậm chí trường hợp này:

```axiom
var v = Vec<i32>(...)

let xs = v.view()
print(xs)

v.push(10)
```

compiler có thể xác định `xs` không còn được sử dụng sau `print(xs)`.

Do đó capability kết thúc semantic lifetime tại:

```text
last use(xs)
```

và `push()` hợp lệ.

Đây là **non-lexical capability lifetime**.

Không phải lifetime syntax.

---

# 8. Đây là một trong những lợi thế lớn của Axiom

Programmer nhìn thấy:

```axiom
let xs = v.view()
print(xs)
v.push(x)
```

Compiler nhìn thấy:

```text
v
 │
 ├── READ capability xs ──→ print
 │                         X
 │
 └── mutation push ─────────→ OK
```

Capability chết tại last semantic use.

Không cần:

```text
drop(xs)
```

trừ khi programmer muốn ép cleanup/capability termination sớm.

---

# 9. Mutation categories của collection

Mỗi operation của collection nên được compiler/library gắn semantic effect về storage.

Không cần expose thành effect-system phức tạp cho programmer.

Ví dụ:

### Read-only

```text
len()
is_empty()
get()
view()
```

```text
NO_RELOCATE
NO_MUTATION
```

### In-place mutation

```text
set()
swap()
sort_in_place()
```

```text
MUTATE_STORAGE
NO_RELOCATE
```

### Potential relocation

```text
push()
insert()
reserve()
resize()
append()
```

```text
MUTATE_STORAGE
MAY_RELOCATE
```

### Destructive

```text
clear()
truncate()
remove()
drain()
```

```text
MUTATE_STORAGE
INVALIDATE_REGION
```

### Ownership-changing

```text
into_iter()
drain()
remove()
pop()
```

có thể tiêu thụ ownership của phần tử hoặc collection.

---

# 10. `reserve()` không tạo stable address

Ví dụ:

```axiom
v.reserve(1000)
let xs = v.view()

v.push(x)
```

Không nên đảm bảo `xs` luôn hợp lệ chỉ vì `reserve()` đã đủ capacity.

Lý do:

```text
reserve != stable-address contract
```

Axiom đã có:

```text
AMEM-23 Reserve Does Not Imply Stable Address
AMEM-21 Stable Address Is An Explicit Storage Contract
```

Do đó vẫn:

```text
view active
     ↓
push
     ↓
potential relocation
     ↓
reject
```

Nếu programmer thực sự cần stable storage, dùng abstraction khác.

---

# 11. Collection cần stable-address variant

Đây là chỗ không nên ép `Vec` làm mọi thứ.

Standard library có thể cung cấp:

```axiom
StableVec<T>
```

hoặc tốt hơn:

```axiom
SlotVec<T>
```

Semantic guarantee:

```text
element address remains stable
until element is removed
```

Implementation có thể dùng:

```text
segmented storage
stable slots
indirection
pool
```

Compiler không cần biết implementation cụ thể.

---

# 12. Đừng tạo quá nhiều collection type

Ban đầu chỉ cần:

```text
Vec<T>        relocatable contiguous
Deque<T>      double-ended
Map<K,V>
Set<T>
```

và storage abstractions:

```text
Arena<T>
Pool<T>
```

Sau đó:

```text
SmallVec<T,N>
StableVec<T>
```

là specialization/library.

Không nên có:

```text
HeapVec
StackVec
StableHeapVec
ThreadVec
AtomicVec
...
```

chỉ vì storage implementation khác nhau.

---

# 13. Iterator

Iterator không nên là một raw pointer primitive.

Semantic:

```axiom
for x in v {
    ...
}
```

compiler có thể lower thành:

```text
iterator state
index/pointer
termination
```

hoặc vectorized loop.

Iterator có capability dependency vào collection.

---

# 14. Iterator invalidation

Ví dụ:

```axiom
var v = ...

for x in v {
    v.push(x)
}
```

Compiler phải reject nếu iterator đang giữ capability khiến mutation không hợp lệ.

Không cần programmer học một bảng dài kiểu:

> `push` invalidates iterators only when capacity changes...

Axiom abstraction:

> **Nếu operation có thể phá capability hiện tại → compiler reject.**

Điều này đơn giản hơn rất nhiều.

---

# 15. Nhưng `Vec::push()` trong loop phải vẫn dễ dùng

Trường hợp:

```axiom
for x in v.view() {
    ...
}
v.push(x)
```

OK vì iterator/view kết thúc trước mutation nếu control flow chứng minh được.

Nếu mutation nằm ngoài iteration:

```axiom
for x in v {
    process(x)
}

v.push(1)
```

compiler thấy iterator đã dead.

Không có vấn đề.

---

# 16. String

Axiom nên **tách byte string và Unicode text**.

Không nên để một `String` mơ hồ giữa:

```text
raw bytes
UTF-8 text
UTF-16
platform string
```

Đề xuất:

```axiom
Bytes
String
StringView
```

Trong đó:

```text
Bytes       = arbitrary byte sequence
String      = valid UTF-8 owned text
StringView  = non-owning UTF-8 text view
```

---

# 17. UTF-8 validity

`String` invariant:

```text
bytes form valid UTF-8
```

Điều này cho phép compiler/library tối ưu rất nhiều API.

Ví dụ:

```axiom
s.length_bytes()
s.chars()
s.slice(...)
```

Nhưng:

```text
length
index
slice
```

phải phân biệt byte index và Unicode scalar boundary.

---

# 18. Không nên giả định `String[i]` là character

Đây là thiết kế quan trọng.

Không nên:

```axiom
s[5] -> char
```

vì UTF-8 variable width.

Thay vào đó:

```axiom
s.byte_at(i)
s.char_at(i)
s.bytes()
s.chars()
```

và compiler/library có thể tối ưu khi context cho phép.

---

# 19. `StringView`

```axiom
let name = String("Axiom")
let v = name.view()
```

`StringView` về semantic nên tương đương một read capability trên UTF-8 storage.

Do đó:

```axiom
var s = String(...)
let v = s.view()

s.push(...)
```

có cùng quy tắc như `Vec`.

Compiler tự kết thúc capability ở last use.

---

# 20. COW không phải default

Không nên biến:

```axiom
String
Vec
```

thành implicit copy-on-write.

Ví dụ:

```axiom
let a = ...
let b = a
```

phải tuân theo ownership/value semantics.

Nếu muốn COW:

```axiom
Cow<T>
```

là abstraction explicit.

Điều này tránh:

```text
hidden atomic refcount
hidden allocation
hidden synchronization
hidden copy
```

trong các operation tưởng như đơn giản.

---

# 21. `Map<K,V>`

Không nên đưa implementation vào language semantics.

Standard library có thể có:

```axiom
Map<K,V>
HashMap<K,V>
TreeMap<K,V>
```

Nhưng semantic contract chỉ quy định:

```text
key equality
lookup semantics
insert/remove
ownership
iteration validity
```

Không quy định bucket layout.

---

# 22. Hashing

Cần tách:

```text
Hash
Hasher
HashMap
```

`Hash` là trait.

Ví dụ:

```axiom
trait Hash {
    fn hash(self, state: mut_view<Hasher>)
}
```

hoặc equivalent API.

Hashing algorithm không nên cố định ở Core.

---

# 23. Hash randomization

`HashMap` mặc định nên có khả năng sử dụng randomized seed để chống collision attacks.

Nhưng:

> deterministic iteration không nên là guarantee của HashMap.

Nếu cần deterministic ordering:

```axiom
OrderedMap<K,V>
```

hoặc:

```axiom
TreeMap<K,V>
```

Không nên làm `HashMap` chậm chỉ để đảm bảo thứ tự.

---

# 24. `Set`

```axiom
Set<T>
```

chỉ là collection semantic wrapper trên key structure.

Không cần compiler primitive.

---

# 25. `Deque`

`Deque<T>` là collection riêng vì semantics khác `Vec`.

Có thể implementation:

```text
ring buffer
segmented buffer
```

Không cần guarantee contiguous storage.

Do đó:

```axiom
view<T>
```

không nhất thiết có thể tạo trực tiếp từ toàn bộ `Deque`.

Có thể có:

```axiom
chunks() -> Iterator<view<T>>
```

---

# 26. SmallVec

`SmallVec<T, N>` là optimization abstraction:

```text
N elements
    ↓
inline

> N
    ↓
dynamic storage
```

Quan trọng:

**SmallVec không được làm thay đổi semantic ownership.**

Compiler có thể tự scalarize hoặc stack-promote một `Vec` nhỏ nếu semantics cho phép.

Do đó `SmallVec` hữu ích khi programmer muốn **explicit storage behavior**, còn compiler vẫn có quyền optimize.

---

# 27. Arena

Arena:

```axiom
let arena = Arena<T>()

let a = arena.alloc(...)
let b = arena.alloc(...)
```

Arena sở hữu storage tập thể.

Quy tắc:

```text
Arena lifetime
      ↓
all allocations
      ↓
views cannot outlive arena
```

Drop arena:

```text
destroy all contained resources
```

Arena không phải GC.

Nó chỉ là:

```text
bulk ownership / allocation strategy
```

---

# 28. Arena + collection

Có thể:

```axiom
Arena<String>
```

hoặc generic allocator abstraction nội bộ.

Nhưng không nên làm mọi API:

```axiom
Vec<T, Allocator>
Map<K,V,Allocator>
String<Allocator>
...
```

mặc định.

Điều này làm type signatures phình to và khiến allocator strategy trở thành một phần của type identity.

Axiom giữ:

> **Allocator choice is not a mandatory generic parameter.**

---

# 29. Pool

Pool phù hợp với object có lifecycle lặp lại:

```text
allocate slot
use
release slot
reuse slot
```

Ví dụ game/server/entity systems.

Pool có thể cung cấp:

```axiom
handle = pool.insert(value)
value = pool.get(handle)
pool.remove(handle)
```

Ở đây `handle` là:

```text
logical identity
```

không phải pointer.

---

# 30. Generation Handle

Đây là abstraction rất hữu ích cho Axiom.

Ví dụ:

```text
Handle {
    index
    generation
}
```

Pool:

```text
slot 17 generation 4
```

xóa:

```text
slot 17 generation 5
```

handle cũ:

```text
17:4
```

không còn hợp lệ.

Nhờ vậy:

```text
stale handle
```

có thể phát hiện mà không cần GC.

Đây đặc biệt hữu ích cho:

```text
game engine
GUI
ECS
editor
resource manager
async systems
```

---

# 31. Iterator và mutation trong Map

Tương tự Vec:

```axiom
for (k, v) in map {
    map.insert(...)
}
```

phải được kiểm tra capability.

Nhưng library có thể cung cấp explicit APIs:

```axiom
map.retain(...)
map.entry(...)
map.modify(...)
```

để mutation được compiler/library thiết kế an toàn ngay trong iteration.

Ví dụ:

```axiom
map.retain(fn(k, v) -> bool {
    ...
})
```

Không cần programmer tự xử lý iterator invalidation.

---

# 32. Collection API nên ưu tiên ownership-aware operations

Ví dụ `Vec`:

```axiom
push(value)
pop() -> Option<T>
remove(index) -> T
swap_remove(index) -> T
clear()
truncate(n)
append(other)
extend(iter)
```

Không nên trả về raw pointer.

Nếu cần view:

```axiom
view()
view_range(...)
mut_view()
mut_view_range(...)
```

---

# 33. Mutation qua view

Ví dụ:

```axiom
var v = Vec<i32>(...)

let x = mut_view(v)

x[0] = 10
```

Trong thời gian `x` sống:

```text
v.push(...)
v.remove(...)
v.clear(...)
```

không hợp lệ nếu có thể ảnh hưởng region.

Nhưng mutation trên vùng **disjoint** có thể được phép.

Ví dụ:

```axiom
let a = mut_view_range(v, 0..10)
let b = mut_view_range(v, 20..30)

a[0] = 1
b[0] = 2
```

Compiler có thể chứng minh:

```text
[0,10)
[20,30)
```

DISJOINT.

Đây là nơi capability region model thực sự tạo giá trị.

---

# 34. Slice range

Range nên có semantics rõ:

```text
[start, end)
```

Ví dụ:

```axiom
view_range(v, 10..20)
```

là:

```text
10 <= i < 20
```

Không có ambiguity inclusive/exclusive.

---

# 35. Out-of-bounds

Safe indexing:

```axiom
v[i]
```

phải đảm bảo bounds.

Compiler có thể eliminate bounds check nếu chứng minh:

```text
0 <= i < len
```

Ví dụ:

```axiom
for i in 0..v.len() {
    sum += v[i]
}
```

MIR có thể chứng minh bounds.

Runtime check biến mất.

Đây là một ví dụ điển hình của:

> **Safety semantics ≠ runtime overhead.**

---

# 36. Unsafe indexing

System code có thể có:

```axiom
unsafe {
    v.get_unchecked(i)
}
```

Nhưng unsafe không biến compiler thành “không kiểm tra gì”.

Contract:

```text
caller guarantees i < len
```

sau đó optimizer có thể tận dụng.

---

# 37. Iterator zero-cost

Ví dụ:

```axiom
for x in v {
    sum += x
}
```

không nên bắt buộc tạo object iterator runtime.

Compiler có thể lower thành:

```text
ptr
end
loop:
    load
    ...
    ptr += sizeof(T)
    compare
```

hoặc vectorize toàn bộ.

Iterator abstraction phải là zero-cost abstraction khi có thể.

---

# 38. Collection ABI

Không nên expose layout mặc định.

Ví dụ không được coi:

```text
Vec<T> == {ptr,len,cap}
```

là ABI guarantee.

Nếu FFI cần:

```axiom
@repr(C)
struct CBuffer {
    ptr: *mut u8
    len: usize
}
```

Đây là ABI type riêng.

---

# 39. Collection và FFI

Không truyền trực tiếp:

```axiom
extern fn foo(v: Vec<u8>)
```

trừ khi ABI Axiom-to-Axiom.

C ABI nên dùng:

```axiom
extern "C" fn foo(data: *const u8, len: usize)
```

hoặc explicit FFI view descriptor.

Allocation ownership phải được xác định rõ:

```text
who allocates?
who frees?
which allocator?
```

Không bao giờ để FFI đoán.

---

# 40. Collection semantic matrix

| Collection | Contiguous | Relocatable | Stable element address | View |
|---|---:|---:|---:|---:|
| Array | yes | no | yes | yes |
| Vec | yes | yes | no | yes |
| SmallVec | usually | possible | no | yes |
| Deque | no/segmented | possible | implementation-dependent | chunks |
| Map | no | implementation | no guarantee | entry-specific |
| Pool | no | no slot relocation | yes | element view |
| Arena | implementation | normally bulk-stable | contract-dependent | yes |
| String | yes | yes | no | StringView |

Điểm quan trọng nhất:

**“stable address” phải là semantic contract, không phải implementation accident.**

---

# 41. COLLECTION-001 invariants

Ta nên khóa các invariant sau:

```text
ACOLL-20  Collection ownership is explicit.
ACOLL-21  Collection storage strategy is not ordinary value type identity.
ACOLL-22  Array has value semantics.
ACOLL-23  Vec has relocatable storage semantics by default.
ACOLL-24  Active capabilities block conflicting collection mutation.
ACOLL-25  MAY_RELOCATE operations cannot invalidate live capabilities.
ACOLL-26  Capability lifetime may end at last semantic use.
ACOLL-27  Programmer need not write lifetime annotations.
ACOLL-28  Reserve does not guarantee stable address.
ACOLL-29  Stable address requires explicit storage contract.
ACOLL-30  Iterator validity follows capability validity.
ACOLL-31  Iterator invalidation is compiler-verifiable.
ACOLL-32  Disjoint regions may be mutated concurrently/sequentially.
ACOLL-33  Unknown overlap cannot be assumed disjoint.
ACOLL-34  Bounds checks are semantic safety requirements.
ACOLL-35  Proven bounds checks may be eliminated.
ACOLL-36  Unsafe unchecked access requires explicit unsafe boundary.
ACOLL-37  String represents valid UTF-8.
ACOLL-38  Bytes represents arbitrary bytes.
ACOLL-39  StringView is non-owning.
ACOLL-40  COW is explicit, not implicit.
ACOLL-41  HashMap iteration order is not a semantic ordering guarantee.
ACOLL-42  Deterministic ordering requires an ordered collection.
ACOLL-43  Allocator selection is not a mandatory collection type parameter.
ACOLL-44  Arena owns its allocations collectively.
ACOLL-45  Arena is not garbage collection.
ACOLL-46  Pool supports stable logical slots.
ACOLL-47  Handles represent logical identity, not memory addresses.
ACOLL-48  Generation handles may detect stale references.
ACOLL-49  Collection layout is not ABI-stable unless explicitly represented.
ACOLL-50  FFI allocation ownership must be explicit.
ACOLL-51  Collection abstractions may be zero-cost after optimization.
ACOLL-52  Compiler may specialize collection operations.
ACOLL-53  Compiler may eliminate allocation when storage is unobservable.
ACOLL-54  Collection APIs must not require programmer lifetime annotations.
ACOLL-55  Stable storage and relocatable storage are distinct semantic contracts.
ACOLL-56  Collection mutation semantics include region invalidation.
ACOLL-57  Views do not transfer collection ownership.
ACOLL-58  Mutable views are exclusive over their region.
ACOLL-59  Read views may be duplicated.
ACOLL-60  A collection operation cannot invalidate a live capability.
```

---

# 42. Một quyết định kiến trúc rất quan trọng

Sau phần này, mô hình collection của Axiom có thể được rút gọn thành:

```text
                    COLLECTION
                         │
             ┌───────────┴───────────┐
             │                       │
        VALUE STORAGE          LOGICAL STORAGE
             │                       │
     Array / Vec / String       Pool / Arena
             │                       │
             └───────────┬───────────┘
                         │
                    CAPABILITY
                         │
               ┌─────────┴─────────┐
               │                   │
             view              mut_view
               │                   │
             READ                WRITE
```

Compiler không cần biết “Vec dùng malloc hay jemalloc hay arena”.

Compiler chỉ cần biết:

```text
does this operation mutate?
does it invalidate storage?
what region?
what capability depends on it?
```

Đây là abstraction boundary rất sạch.

---

# 43. Bước tiếp theo: ERROR-001

Sau **Collections**, task logic tiếp theo nên là:

## **ERROR-001 — Error, Result, Panic & Failure Model**

Phần này cần khóa trước khi đi sâu vào standard library vì nó ảnh hưởng trực tiếp tới:

- `Result<T,E>`
- `Option<T>`
- `panic`
- `trap`
- `abort`
- unwind
- allocation failure
- thread failure
- async cancellation
- destructor/Drop
- FFI error ABI
- OS errors
- GPU errors
- `?` propagation
- zero-cost error handling
- exception-like control flow nhưng **không dùng C++ exception model**

Đặc biệt cần giải quyết một vấn đề rất quan trọng của Axiom:

```axiom
fn foo() -> Result<T, E>
```

làm sao để `?` vừa cực kỳ tiện cho programmer, vừa compile xuống code gần như:

```text
branch + return
```

không có hidden exception runtime.

memcite