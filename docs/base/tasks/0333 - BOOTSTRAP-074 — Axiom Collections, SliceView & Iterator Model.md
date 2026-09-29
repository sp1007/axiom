Tiếp tục.

# BOOTSTRAP-074 — Axiom Collections, Slice/View & Iterator Model

**Trạng thái: FROZEN**

Đây là phần đặc biệt quan trọng vì nó phải giải quyết đồng thời:

- `Array`
- `Vec`
- `view<T>` / `mut_view<T>`
- `String` / `Str`
- iterator
- nested/multidimensional data
- relocation
- ownership
- zero-copy
- SIMD/vectorization
- GPU buffers
- arena/pool
- collection API nhưng không biến Axiom thành “Rust với quá nhiều trait”.

Mục tiêu:

> **Một mô hình region/capability thống nhất cho dữ liệu tuần tự, nhưng không bắt mọi collection phải có cùng representation.**

---

# 1. Quyết định nền tảng: `view<T>` là element view

Ta giữ quyết định trước đây:

```axiom
view<T>
mut_view<T>
```

không đổi thành một loại slice đặc biệt kiểu `view<[T]>`.

Ý nghĩa:

```text
view<T>
    = non-owning read capability đối với một contiguous region của T

mut_view<T>
    = non-owning exclusive write capability đối với một contiguous region của T
```

Ví dụ:

```axiom
fn sum(xs: view<i32>) -> i32
```

có nghĩa:

```text
một vùng liên tiếp các i32
```

Representation thường có thể là:

```text
(pointer, length)
```

nhưng đó **không phải semantic requirement**.

---

# 2. Array

Array là giá trị cố định kích thước:

```axiom
let a: [i32; 4] = [1, 2, 3, 4]
```

Semantic:

```text
type = [T; N]
size = N * sizeof(T) + padding/alignment
ownership = value
length = compile-time constant N
```

Array không phải heap object.

---

# 3. Array có thể nằm ở đâu?

Không có quy định:

```text
[T; N] → stack
```

Compiler có thể đặt nó:

```text
register
stack
inline trong struct
static
heap
GPU local/shared
```

nếu semantics cho phép.

Đây tiếp tục theo `AMEM-30`, `AMEM-31`.

---

# 4. Array → view

Có thể implicit khi truyền trực tiếp vào function:

```axiom
fn sum(xs: view<i32>) -> i32

let a = [1, 2, 3, 4]

sum(a)
```

Compiler tạo capability:

```text
a
 ↓
READ capability
 ↓
view<i32>
```

Không copy array.

---

# 5. Persistent view vẫn explicit

Không cho:

```axiom
let xs: view<i32> = a
```

tự động tạo escaping capability.

Dùng:

```axiom
let xs = view(a)
```

để programmer nói rõ:

> Tôi muốn giữ một capability tới vùng dữ liệu này.

---

# 6. Mutable view

```axiom
fn zero(xs: mut_view<i32>) {
    for x in xs {
        *x = 0
    }
}
```

Tên syntax dereference ở ví dụ trên chỉ mang tính minh họa; API iterator cuối cùng nên tránh ép programmer phải thao tác pointer.

Idiomatic hơn:

```axiom
fn zero(xs: mut_view<i32>) {
    xs.fill(0)
}
```

hoặc:

```axiom
for x in xs.mut_items() {
    x.set(0)
}
```

Cần tránh đưa pointer/reference syntax trở lại cửa sau.

---

# 7. `mut_view<T>` không phải collection

Đây là điểm rất quan trọng.

```text
Vec<T>
Array<T,N>
```

là **storage/value abstractions**.

Trong khi:

```text
view<T>
mut_view<T>
```

là **access capabilities**.

Do đó:

```text
Vec<T> → view<T>
Array<T,N> → view<T>
Buffer<T> → view<T>
DeviceBuffer<T> → DeviceView<T>
```

có thể cùng dùng tư duy region/capability nhưng không nhất thiết cùng physical representation.

---

# 8. Vec

`Vec<T>` là growable owned collection.

Semantic state:

```text
Vec<T>
├── logical storage region
├── length
└── capacity
```

Không quy định source-level representation:

```text
pointer + length + capacity
```

đó chỉ là implementation thường gặp.

---

# 9. Vec ownership

```axiom
var xs = Vec<i32>()
xs.push(10)
xs.push(20)
```

`Vec<T>` là owning value.

Thông thường:

```text
Copy = false
Clone = explicit
Drop = deterministic
```

---

# 10. Vec relocation

```axiom
var xs = Vec<i32>()
...
xs.push(x)
```

có thể làm storage relocate.

Nếu có:

```axiom
let v = view(xs)
```

đang live, operation có thể relocate phải bị compiler chặn.

Đây chính là:

```text
live capability
      ↓
relocation prohibited
```

không cần programmer viết lifetime.

---

# 11. `reserve`

```axiom
xs.reserve(1000)
```

cho phép compiler/library chuẩn bị capacity.

Nhưng:

> **reserve không phải stable-address contract.**

Ngay cả sau `reserve`, Axiom không mặc định cho phép programmer dựa vào physical address.

---

# 12. Stable storage

Nếu cần:

```text
address không thay đổi
```

thì phải chọn abstraction có contract tương ứng:

```text
StableBox<T>
StableVec<T>
Pool<T>
Arena<T>
```

tùy nhu cầu.

Không biến `Vec` thành stable container chỉ vì một số ứng dụng cần nó.

---

# 13. Slice không cần thêm primitive

Không tạo thêm:

```text
Slice<T>
RefSlice<T>
BorrowedVec<T>
ArrayView<T>
```

trong Core.

`view<T>` chính là semantic contiguous read region.

Standard Library có thể đặt alias/type helper nếu tiện API, nhưng không tạo thêm semantic reference model.

---

# 14. Range slicing

Ví dụ:

```axiom
let middle = view(xs)[10..20]
```

có thể tạo:

```text
view<T>
```

với region:

```text
xs[10..20]
```

Compiler biết provenance:

```text
owner = xs
region = [10,20)
```

---

# 15. Mutable slicing

```axiom
let left  = mut_view(xs)[0..10]
let right = mut_view(xs)[10..20]
```

hai capability có thể cùng tồn tại nếu compiler chứng minh:

```text
DISJOINT
```

Ngược lại:

```axiom
let a = mut_view(xs)[0..10]
let b = mut_view(xs)[5..15]
```

phải reject nếu cả hai cùng live.

---

# 16. Đây là điểm mạnh lớn của Axiom

Không cần:

```text
lifetime annotations
borrow annotations
'static
'a
```

Programmer chỉ viết:

```axiom
let a = mut_view(xs)[0..10]
let b = mut_view(xs)[10..20]
```

Compiler tự chứng minh:

```text
region A ∩ region B = ∅
```

và cho phép.

---

# 17. Dynamic index

Nếu:

```axiom
let a = mut_view(xs)[start..mid]
let b = mut_view(xs)[mid..end]
```

compiler có thể prove:

```text
start <= mid <= end
```

thì disjoint.

Nếu không prove được:

```text
UNKNOWN
```

→ không được giả định disjoint.

---

# 18. Đây không phải runtime bounds checking bắt buộc

Range proof có thể loại bỏ:

```text
bounds checks
```

khi compiler chứng minh được.

Ví dụ:

```axiom
for i in 0..xs.len() {
    xs[i] += 1
}
```

compiler có thể chứng minh:

```text
0 <= i < len
```

→ loại bỏ bounds check trong loop.

---

# 19. `get`

API checked:

```axiom
let x = xs.get(i)?
```

nếu index không chắc chắn.

Unchecked/system API:

```text
unsafe
```

chỉ dành cho low-level code.

Nhưng optimizer không cần programmer dùng unsafe để đạt performance nếu có proof.

---

# 20. Iterator là trait

Iterator nên là abstraction library:

```text
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Conceptually.

Tên receiver chính xác có thể điều chỉnh theo trait API, nhưng nguyên tắc:

> iterator state là mutable state, không phải một reference hierarchy mới.

---

# 21. Iterator không nhất thiết heap allocate

```axiom
for x in xs {
    ...
}
```

không tạo object iterator trên heap.

Compiler có thể biến thành:

```text
index loop
pointer loop
SIMD loop
```

hoặc thậm chí eliminate iterator hoàn toàn.

---

# 22. `for` lowering

Semantic:

```text
for x in collection {
    body
}
```

→ iterator protocol.

Sau đó:

```text
Iterator
 ↓
MIR
 ↓
OptIR
 ↓
inline
 ↓
loop
```

Abstraction biến mất nếu không observable.

---

# 23. Iterator state

Ví dụ range:

```text
0..100
```

iterator có thể chỉ cần:

```text
current
end
```

Không allocation.

---

# 24. Iterator ownership

Phải phân biệt:

```text
iterate by value
iterate by view
iterate mutably
```

nhưng không tạo syntax kiểu:

```text
for &x
for &mut x
```

như Rust.

Collection/iterator API quyết định Item semantics.

---

# 25. Ba iterator phổ biến

Một collection có thể cung cấp:

```text
items()
views()
mut_items()
```

hoặc API tương đương.

Ví dụ:

```axiom
for x in xs.items() {
    ...
}
```

```axiom
for x in xs.views() {
    ...
}
```

```axiom
for x in xs.mut_items() {
    ...
}
```

Tên cuối cùng có thể tinh chỉnh ở API audit.

---

# 26. Nhưng không nên quá nhiều iterator type

Axiom không nên biến mỗi biến thể thành hàng chục traits:

```text
Iter
DoubleEndedIter
ExactSizeIter
TrustedIter
IndexedIter
ParallelIter
AsyncIter
...
```

trong Core.

Có thể tồn tại trong Standard Library nếu thực sự cần, nhưng:

> **Core language chỉ cần iteration protocol cơ bản.**

---

# 27. `IntoIterator`

Có thể hỗ trợ trait:

```text
IntoIterator
```

để:

```axiom
for x in collection
```

chuyển collection thành iterator.

Nhưng semantics ownership phải rõ:

```text
for x in xs
```

có thể consume `xs` nếu iterator yêu cầu ownership.

Trong khi:

```text
for x in xs.view()
```

là borrowed iteration.

---

# 28. Không tạo implicit clone trong `for`

Nếu:

```axiom
for x in xs {
    ...
}
```

consume `xs`, compiler không được tự clone để cứu programmer.

Nếu muốn giữ collection:

```axiom
for x in xs.view() {
    ...
}
```

hoặc API tương ứng.

---

# 29. `Copy` item

Nếu:

```text
T: Copy
```

iterator có thể trả value mà không tạo ownership complication.

Ví dụ:

```axiom
for x in numbers {
    total += x
}
```

có thể rất gần với C loop.

---

# 30. Non-Copy item

Với:

```text
Vec<String>
```

iteration by value có thể Move từng element.

Sau đó collection có thể ở trạng thái:

```text
partially moved
```

hoặc consume toàn bộ collection tùy iterator semantics.

Compiler verification đã có Place Tree để xử lý.

---

# 31. Mutable iteration

```axiom
for x in xs.mut_items() {
    ...
}
```

tạo các mutable capabilities tuần tự.

Compiler phải đảm bảo:

```text
không có capability khác xung đột
```

trong thời gian cần thiết.

---

# 32. Iterator có thể giữ capability

Ví dụ iterator trên `Vec<T>` có thể conceptually giữ:

```text
owner/provenance
current region
remaining region
```

Compiler tracking ở MIR.

Không cần runtime lifetime metadata.

---

# 33. Iterator invalidation

Đây là quy tắc quan trọng:

> Một operation có thể relocate hoặc structurally modify collection không được thực hiện khi iterator/capability phụ thuộc storage vẫn live.

Ví dụ:

```axiom
var xs = Vec<i32>()

let it = xs.iter()

xs.push(10)   // có thể reject
```

nếu `push` có khả năng invalidate iterator.

---

# 34. Nhưng compiler có thể biết operation không relocate

Ví dụ:

```text
xs[3] = 10
```

không thay đổi capacity/storage.

Nếu capability hợp lệ:

```text
write element
```

có thể được cho phép.

---

# 35. Semantic effect của collection operation

Compiler không cần một source-level effect system.

Nó có thể biết nội bộ:

```text
push:
    WRITE
    MAY_RELOCATE
    MAY_ALLOCATE

set:
    WRITE
    NO_RELOCATE

clear:
    WRITE
    DROP_ELEMENTS
    MAY_RETAIN_STORAGE
```

Đây là compiler effect facts.

---

# 36. `clear`

```axiom
xs.clear()
```

phải:

- Drop các phần tử;
- length → 0;
- không nhất thiết deallocate capacity.

Do đó:

```text
resource lifetime
```

của elements kết thúc, nhưng:

```text
storage lifetime
```

có thể tiếp tục.

---

# 37. `truncate`

```axiom
xs.truncate(n)
```

Drop elements:

```text
[n .. old_len)
```

nhưng không nhất thiết relocate storage.

---

# 38. `shrink_to_fit`

Đây có thể relocate.

Vì vậy live view có thể ngăn operation.

---

# 39. `drain`

Operation:

```text
xs.drain(range)
```

có semantics mạnh hơn vì:

- remove elements;
- Drop/Move elements;
- thay đổi logical region;
- có thể shift storage.

Capability verifier phải xem đây là structural mutation.

---

# 40. `retain`

```axiom
xs.retain(predicate)
```

có thể:

```text
Move/Drop elements
```

và thay đổi logical indices.

Iterator/capability đang phụ thuộc index region phải được xử lý theo semantic effects.

---

# 41. Deque

Không ép mọi sequence vào `Vec`.

Có:

```text
Deque<T>
```

với logical sequence nhưng physical storage có thể ring buffer.

`view<T>` chỉ được cung cấp cho **contiguous region thực sự**.

---

# 42. Đây là giới hạn quan trọng của `view<T>`

Không được nói:

```text
Deque<T> → view<T>
```

một cách mặc định.

Nếu deque wrap:

```text
physical:
[ A B C D | _ _ _ | E F ]
```

logical sequence:

```text
A B C D E F
```

không contiguous.

API có thể trả:

```text
view<T> + view<T>
```

hoặc iterator.

Không giả vờ contiguous.

---

# 43. Linked collection

Ví dụ:

```text
LinkedList<T>
```

không cung cấp `view<T>` toàn collection.

Chỉ:

```text
iterator
```

hoặc từng element view.

Điều này giữ `view<T>` semantic chính xác.

---

# 44. HashMap

`HashMap<K,V>` không phải contiguous collection.

Không:

```text
view<Pair<K,V>>
```

trừ khi implementation contract thực sự cung cấp contiguous iteration representation.

Thay vào đó:

```text
iterator
```

---

# 45. HashMap iteration order

Mặc định không guarantee deterministic order nếu không có explicit ordered map.

Có:

```text
HashMap
OrderedMap / BTreeMap
```

nếu application cần ordering.

---

# 46. HashMap mutation

Một iterator đang live có thể bị invalidated bởi:

```text
insert
remove
rehash
reserve
```

Compiler/library contract phải khai báo semantic invalidation.

Không cần programmer manually annotate iterator lifetime.

---

# 47. BTree

`BTreeMap` có logical ordering.

Iterator:

```text
O(n)
```

nhưng storage không contiguous toàn map.

Không ép thành `view`.

---

# 48. Set

`HashSet<T>` tương tự HashMap.

Không cần Core primitive.

Library:

```text
HashSet
BTreeSet
```

---

# 49. Stack / Queue

Không cần Core types.

Có thể xây từ:

```text
Vec
Deque
```

hoặc specialized implementations.

---

# 50. SmallVec

Có thể có:

```text
SmallVec<T, N>
```

với:

```text
inline storage
```

khi nhỏ và dynamic storage khi lớn.

Đây là library abstraction.

Compiler không cần special-case.

---

# 51. Arena collection

```text
Arena<T>
```

có thể cấp storage theo arena.

Ownership:

```text
Arena owns storage
```

object/capability không được escape arena lifetime.

Compiler verification xử lý provenance.

---

# 52. Pool

```text
Pool<T>
```

có thể cung cấp stable slots.

Điều này rất hữu ích cho:

```text
entity systems
game engines
object pools
network connections
```

nhưng stable identity phải phân biệt:

```text
storage identity
logical identity
```

---

# 53. Handle

Ví dụ:

```text
Handle<Entity>
```

không phải:

```text
*Entity
```

và không phải:

```text
view<Entity>
```

Nó là logical identity.

Có thể chứa:

```text
index
generation
```

để phát hiện stale handle.

---

# 54. Multidimensional array

Đây là điểm cần khóa.

```axiom
let a: [f32; 4; 4]
```

không nên tạo syntax mơ hồ.

Khuyến nghị dùng nested array:

```axiom
let a: [[f32; 4]; 4]
```

Semantic:

```text
4 arrays
    each containing 4 f32
```

Compiler biết toàn bộ layout.

---

# 55. Multidimensional view

Không nên tạo:

```text
view2<T>
view3<T>
view4<T>
```

trong Core.

Có thể dùng:

```text
view<T>
```

cùng shape metadata ở library abstraction khi cần.

Ví dụ tensor library:

```text
TensorView<T>
```

có:

```text
data: view<T>
shape
stride
```

nhưng `TensorView` là library type.

---

# 56. Vì sao không làm `view2<T>`?

Vì:

```text
matrix
tensor
image
volume
strided data
```

không phải lúc nào contiguous theo toàn bộ shape.

Ví dụ:

```text
shape  = [3, 4]
stride = [4, 1]
```

vs:

```text
stride = [1, 3]
```

Do đó generic multidimensional data cần:

```text
data + shape + stride
```

chứ không phải một primitive `view2`.

---

# 57. Tensor

Có thể:

```text
Tensor<T, Rank>
TensorView<T, Rank>
```

ở ML library.

Semantic core chỉ cần:

```text
view<T>
```

và capability region.

GPU:

```text
DeviceView<T>
```

là storage-domain-specific analogue.

---

# 58. Contiguous vs strided

Nên có semantic distinction:

```text
ContiguousView<T>
StridedView<T>
```

nhưng đây là library abstraction.

`view<T>` luôn có semantics contiguous.

---

# 59. SIMD

Contiguous `view<T>` cho compiler information mạnh:

```text
contiguous
typed
bounds
provenance
alias capability
```

Nếu hai mutable views disjoint:

```text
a: [0..N)
b: [N..2N)
```

optimizer có thể suy ra NoAlias.

Điều này hỗ trợ auto-vectorization mà không cần:

```text
restrict
```

ở source.

---

# 60. `view<T>` và `mut_view<T>` không mang stride

Đây là quyết định nên freeze:

```text
view<T>
```

= contiguous.

Không dùng nó cho arbitrary strided data.

Strided data cần library type.

---

# 61. View conversion

```text
Array → view
Vec → view
String → Str
```

có thể zero-copy.

Nhưng:

```text
HashMap → view
Deque → view
```

không được implicit nếu physical region không contiguous.

---

# 62. Collection trait model

Standard Library có thể định nghĩa những abstraction như:

```text
Iterable
Collection
Sequence
Map
Set
```

nhưng không nên bắt mọi collection implement một hierarchy khổng lồ.

Axiom ưu tiên:

```text
small traits
composable constraints
```

---

# 63. `Collection` không nhất thiết là trait Core

Thậm chí `Collection` generic umbrella có thể không cần thiết.

Ví dụ function chỉ cần:

```axiom
fn sum(xs: view<i32>) -> i32
```

thì không cần:

```text
T: Collection + Iterable + ...
```

Điều này làm API đơn giản hơn.

---

# 64. Generic algorithms

Ví dụ:

```axiom
fn max<T: Ord>(xs: view<T>) -> Option<T>
```

Không cần biết xs đến từ:

```text
Array
Vec
Arena
Buffer
```

Miễn tạo được `view<T>`.

---

# 65. Mutation algorithm

```axiom
fn fill(xs: mut_view<i32>, value: i32) {
    ...
}
```

là API rất mạnh.

Nó có thể nhận:

```text
Array
Vec
Buffer
Tensor contiguous region
```

mà không cần collection hierarchy.

---

# 66. Collection API nên ưu tiên view

Thay vì:

```text
Vec<T>::sum()
Vec<T>::sort()
Array<T,N>::sum()
Array<T,N>::sort()
Buffer<T>::sum()
...
```

có thể có generic algorithms:

```text
sum(view<T>)
sort(mut_view<T>)
fill(mut_view<T>)
copy(view<T>, mut_view<T>)
```

Giảm duplication.

---

# 67. Nhưng method syntax vẫn được

Do method là function syntax:

```axiom
xs.sum()
```

có thể là sugar cho:

```axiom
sum(view(xs))
```

nếu extension/inherent method resolution cho phép.

Do đó programmer vẫn có ergonomic API.

---

# 68. Copy giữa regions

```text
copy(src: view<T>, dst: mut_view<T>)
```

phải xử lý overlap semantics rõ.

Có thể có:

```text
copy
copy_nonoverlap
move
```

tùy library.

Không được compiler tự assume non-overlap nếu chưa proof.

---

# 69. `copy_nonoverlap`

Nếu contract:

```text
src ∩ dst = ∅
```

compiler có thể dùng:

```text
memcpy-like
vectorized copy
```

Nếu overlap:

```text
memmove-like
```

Hai semantic operation nên khác nhau.

---

# 70. Move range

Move elements từ:

```text
view<T>
```

không giống byte copy.

Nếu `T` có Drop/resource semantics:

```text
bitwise copy
```

không được coi là semantic Move.

Collection implementation phải dùng element-wise semantic Move hoặc compiler intrinsic được verify.

---

# 71. `memcpy`

Low-level:

```text
memcpy
```

chỉ là byte operation.

Không được dùng nó để giả định:

```text
T = semantic trivially relocatable
```

trừ khi compiler có representation/type fact tương ứng.

---

# 72. Trivially relocatable

Có thể cần compiler-internal property:

```text
TriviallyRelocatable
```

nhưng **không nên đưa thành user-facing Core trait v1** ngay.

Compiler có thể suy ra từ:

```text
Drop
representation
ownership
```

sau này nếu cần expose API contract mới.

---

# 73. `Vec` relocation của non-Copy T

Khi resize/relocate:

```text
Vec<T>
```

với `T` không Copy:

```text
Move elements
```

không phải:

```text
Copy elements
```

Nếu T có Drop, old storage phải được xử lý đúng.

---

# 74. Relocation optimization

Compiler có thể nhận ra:

```text
T
```

có representation cho phép bulk relocation.

Khi đó:

```text
element-wise moves
```

có thể được optimize thành:

```text
bulk memory operation
```

nhưng semantic result phải giống nhau.

---

# 75. Parallel iteration

Không cần Core syntax:

```text
parallel for
```

ngay lập tức.

Library có thể có:

```text
parallel_iter()
```

và yêu cầu:

```text
Send
Share
```

cũng như phân vùng region.

Compiler có thể sau này auto-parallelize loop nếu semantics cho phép, nhưng đó là optimization.

---

# 76. Async iteration

Async iteration là library abstraction:

```text
AsyncIterator
```

không phải Core collection primitive.

`await` vẫn là control-flow mechanism.

---

# 77. Collection + async

Không cho một synchronous iterator giữ:

```text
mut_view
```

qua `.await`.

Ví dụ conceptually:

```text
mut_view(xs)
    ↓
await
```

phải reject nếu capability sống qua suspension.

Đây là `AVERIFY-60`.

---

# 78. Collection + threads

Không cho:

```text
mut_view(xs)
```

được chuyển sang thread khác chỉ vì representation là pointer+length.

Phải kiểm tra:

```text
provenance
storage domain
Send
```

---

# 79. Collection + GPU

Host:

```text
view<f32>
```

không tự biến thành:

```text
DeviceView<f32>
```

GPU storage domain khác.

Phải transfer/map explicitly.

---

# 80. DeviceBuffer

GPU library:

```text
DeviceBuffer<T>
```

có thể cung cấp:

```text
DeviceView<T>
DeviceMutView<T>
```

với semantics tương tự nhưng storage domain:

```text
DEVICE
```

---

# 81. Collection API không ép allocator generic

Không thiết kế:

```text
Vec<T, Allocator>
```

làm mặc định.

Allocator là storage implementation concern.

Nếu cần custom allocation:

```text
Arena
Pool
CustomBuffer
```

được chọn explicit.

---

# 82. Vì sao?

Nếu mọi collection đều:

```text
Vec<T, A>
HashMap<K,V,A>
Deque<T,A>
...
```

thì API trở nên nặng và generic type explosion.

Axiom muốn:

> **Allocator chỉ xuất hiện trong API khi allocation strategy thực sự là một phần semantics của abstraction.**

---

# 83. `Vec` allocator customization

Nếu sau này cần:

```text
Vec<T, MyAllocator>
```

có thể thêm library-level generic.

Nhưng Core v1 không cần khóa allocator parameter vào collection type.

---

# 84. Collection equality

Không mặc định bytewise compare.

`Vec<T> == Vec<T>` là:

```text
same length
element-wise equality
```

với:

```text
T: Eq
```

---

# 85. Hashing

Hash collection dựa trên logical elements.

Không hash:

```text
physical address
capacity
padding
```

trừ khi type explicitly defines identity semantics.

---

# 86. Iterator determinism

Sequential iterator phải có ordering theo collection semantics.

Ví dụ:

```text
Array/Vec
```

có order.

`HashMap` không guarantee order nếu không được contract.

Parallel iterator không được thay đổi observable semantics nếu operation không associative/commutative; API phải phân biệt semantic guarantees với optimization.

---

# 87. Lazy iterator

Transformation:

```axiom
xs.map(f).filter(g).take(10)
```

không tạo intermediate collections mặc định.

Conceptually:

```text
pipeline
```

Compiler có thể fuse thành một loop.

---

# 88. Iterator fusion

Compiler/library có thể biến:

```text
map
filter
map
reduce
```

thành:

```text
single loop
```

nếu semantics cho phép.

Không cần programmer viết loop thủ công để đạt performance.

---

# 89. Allocation-free pipeline

Ví dụ:

```axiom
let total =
    xs.view()
      .map(square)
      .filter(is_positive)
      .sum()
```

mục tiêu:

```text
0 intermediate heap allocations
```

và thường:

```text
1 optimized loop
```

---

# 90. Nhưng không hứa mọi abstraction luôn zero-cost

Nếu iterator được:

```text
stored
returned
boxed
dyn
```

thì runtime representation có thể xuất hiện.

Axiom chỉ đảm bảo:

> **Không có overhead bắt buộc khi compiler có thể erase abstraction mà semantics không thay đổi.**

---

# 91. Dynamic iterator

Có thể có:

```text
dyn Iterator<Item = T>
```

nếu cần runtime polymorphism.

Khi đó:

```text
vtable
```

có thể tồn tại.

Nhưng `dyn` explicit.

---

# 92. Iterator object không có hidden heap

Ngay cả:

```text
dyn Iterator
```

cũng không đồng nghĩa:

```text
heap allocation
```

Có thể caller/storage abstraction cung cấp object storage.

Heap chỉ xảy ra nếu storage contract yêu cầu.

---

# 93. Collection views and alias analysis

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu compiler chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

thì có thể:

```text
vectorize
parallelize
reorder
```

theo memory model.

Nếu UNKNOWN:

```text
```

không được tự assume noalias.

---

# 94. Đây là lý do `view` quan trọng hơn pointer

C:

```text
float* a
float* b
float* out
```

compiler thường thiếu alias guarantee.

Axiom:

```text
view<f32>
view<f32>
mut_view<f32>
```

mang semantic capability information.

Compiler có thể biến proof đó thành:

```text
internal NoAlias
```

mà programmer không phải viết `restrict`.

---

# 95. Collection API và AI-friendly code

AI-generated code nên dễ suy luận:

```axiom
fn normalize(xs: mut_view<f32>) {
    ...
}
```

thay vì:

```text
template<typename T, typename Alloc, typename Iter,
         typename Enable, ...>
```

với hàng loạt implicit machinery.

Mục tiêu là:

```text
input capability
→ transformation
→ output
```

rõ ràng.

---

# 96. Core Collection Set

Không đưa tất cả vào language Core.

### Core semantic:

```text
[T; N]
view<T>
mut_view<T>
iteration protocol
index/range semantics
```

### Core Library:

```text
Array helpers
Vec
Str
String
Bytes
Option
Result
Iterator
Range
```

### Standard Library:

```text
Deque
HashMap
HashSet
BTreeMap
BTreeSet
Heap
Queue
Channel buffers
```

### Specialized libraries:

```text
Tensor
Matrix
Image
SparseMatrix
EntityPool
Arena collections
Concurrent collections
GPU collections
```

---

# 97. API principle

Axiom không nên có:

```text
one giant Collection interface
```

mà:

```text
small semantic abstractions
        ↓
view
iterator
ownership
capability
```

Một algorithm chỉ yêu cầu thứ nó thực sự cần.

---

# 98. Collection capability hierarchy

Conceptually:

```text
                    Storage
                       │
          ┌────────────┼────────────┐
          │            │            │
        Array          Vec        DeviceBuffer
          │            │            │
          └─────── contiguous ──────┘
                       │
                    view<T>
                       │
                 algorithm<T>
```

Còn:

```text
HashMap
Deque
BTreeMap
```

đi qua:

```text
Iterator
```

thay vì ép thành `view<T>`.

---

# 99. Quyết định cuối cùng về `view`

**Freeze:**

```text
view<T>
```

có semantic nghĩa là:

> **read-only contiguous region of T**

và:

```text
mut_view<T>
```

là:

> **exclusive mutable contiguous region of T**

Không:

```text
view<T> = arbitrary reference
view<T> = generic iterator
view<T> = strided tensor
view<T> = collection object
```

Điều này giúp toàn bộ compiler/optimizer có một invariant cực mạnh và đơn giản.

---

# 100. Frozen Invariants — `ACOL-20..100`

### Fundamental representation

- **ACOL-20** Array `[T; N]` is a value type.
- **ACOL-21** Array length is part of its type.
- **ACOL-22** Array storage location is compiler-selected unless explicitly contracted.
- **ACOL-23** `view<T>` represents a contiguous read-only region of `T`.
- **ACOL-24** `mut_view<T>` represents a contiguous exclusive mutable region of `T`.
- **ACOL-25** View capabilities are non-owning.
- **ACOL-26** View capabilities preserve provenance.
- **ACOL-27** View representation is not part of ordinary source semantics.
- **ACOL-28** Pointer-plus-length is a permitted implementation representation.
- **ACOL-29** View creation does not imply copying.
- **ACOL-30** View does not imply heap allocation.

### Ownership

- **ACOL-31** `Vec<T>` is an owning growable collection.
- **ACOL-32** `Vec<T>` is normally non-Copy.
- **ACOL-33** `Vec<T>` duplication is explicit.
- **ACOL-34** `Vec<T>` relocation may occur during structural growth.
- **ACOL-35** `reserve` does not establish stable address.
- **ACOL-36** Live dependent capabilities prohibit invalid relocation.
- **ACOL-37** Collection Drop follows ordinary Axiom Drop semantics.
- **ACOL-38** Element Drop occurs when element ownership ends.
- **ACOL-39** Collection storage lifetime is distinct from element/resource lifetime.
- **ACOL-40** Collection allocation strategy is not ordinary type identity.

### Views and regions

- **ACOL-41** Owner-to-view conversion may be implicit for ephemeral compatible call arguments.
- **ACOL-42** Persistent view creation is explicit.
- **ACOL-43** View cannot outlive its provenance.
- **ACOL-44** `mut_view<T>` is non-duplicable.
- **ACOL-45** Multiple read views may coexist.
- **ACOL-46** Read/write overlap is prohibited in safe code.
- **ACOL-47** Write/write overlap is prohibited in safe code.
- **ACOL-48** Disjoint regions may have simultaneous mutable capabilities.
- **ACOL-49** UNKNOWN overlap cannot be treated as DISJOINT.
- **ACOL-50** Range/index proofs may establish disjointness.

### Indexing / slicing

- **ACOL-51** Byte indexing and text indexing remain distinct from collection indexing.
- **ACOL-52** Collection indexing has explicit bounds semantics.
- **ACOL-53** Bounds checks may be eliminated after proof.
- **ACOL-54** Unchecked indexing is unsafe/system-level.
- **ACOL-55** Contiguous slicing produces another compatible view.
- **ACOL-56** Arbitrary non-contiguous regions cannot be represented as `view<T>`.
- **ACOL-57** Strided data requires a separate library abstraction.
- **ACOL-58** Multidimensional arrays use ordinary nested array semantics.
- **ACOL-59** Multidimensional tensor views are library abstractions.
- **ACOL-60** `view<T>` does not encode shape or stride metadata.

### Iteration

- **ACOL-61** Iteration is a library protocol.
- **ACOL-62** `for` lowers through the iteration protocol.
- **ACOL-63** Iterator abstraction does not imply heap allocation.
- **ACOL-64** Iterator state may be stack/register/inline/heap allocated according to escape and storage analysis.
- **ACOL-65** Iterator transformations may be fused.
- **ACOL-66** Lazy iterators are permitted.
- **ACOL-67** Iterator pipelines do not imply intermediate collections.
- **ACOL-68** Iterator optimization cannot change observable semantics.
- **ACOL-69** Collection iteration preserves collection-defined ordering.
- **ACOL-70** Hash-based collections need not guarantee stable iteration order unless explicitly specified.

### Mutation / invalidation

- **ACOL-71** Structural collection mutation may invalidate dependent views/iterators.
- **ACOL-72** The compiler verifies invalidation through capability/provenance analysis.
- **ACOL-73** Element mutation that cannot relocate storage is distinct from structural mutation.
- **ACOL-74** `clear` ends element resource lifetimes without requiring storage deallocation.
- **ACOL-75** `truncate` drops removed elements.
- **ACOL-76** Structural operations may be rejected while dependent capabilities remain live.
- **ACOL-77** Collection APIs expose invalidation semantics through compiler-known effects/contracts.
- **ACOL-78** Programmer lifetime annotations are not required.
- **ACOL-79** Implicit cloning is never introduced merely to satisfy iterator/collection validity.
- **ACOL-80** Move semantics apply to non-Copy collection elements.

### Performance

- **ACOL-81** Collection abstractions may be erased by optimization.
- **ACOL-82** Iterator abstraction may compile to an ordinary loop.
- **ACOL-83** Proven disjoint views may strengthen optimizer alias information.
- **ACOL-84** `view<T>` does not require source-level `restrict`.
- **ACOL-85** Bounds-check elimination requires proof.
- **ACOL-86** Collection algorithms may be vectorized when semantics permit.
- **ACOL-87** Bulk memory operations must preserve element semantics.
- **ACOL-88** Bitwise copying is not semantic Move unless the type permits it.
- **ACOL-89** Collection relocation may use optimized bulk movement when semantic properties permit.
- **ACOL-90** Optimization cannot manufacture safety facts.

### General collections

- **ACOL-91** Non-contiguous collections do not implicitly convert to `view<T>`.
- **ACOL-92** `Deque` may expose multiple contiguous regions rather than one whole-collection view.
- **ACOL-93** HashMap/HashSet/BTree collections primarily expose iteration rather than contiguous views.
- **ACOL-94** Collection hierarchy is not mandatory in Core.
- **ACOL-95** Algorithms should request the smallest semantic abstraction they require.
- **ACOL-96** Allocator parameters are not mandatory on ordinary collection types.
- **ACOL-97** Arena/pool/stable collections are explicit storage abstractions.
- **ACOL-98** Logical handles are distinct from collection views and raw pointers.
- **ACOL-99** CPU collection views and GPU device views share capability principles but not storage domains.
- **ACOL-100** The collection model must preserve ownership, capability, Drop, concurrency, async, GPU and ABI semantics across all compiler stages.

---

## Kết quả kiến trúc sau BOOTSTRAP-074

Axiom hiện có một mô hình khá sạch:

```text
                 VALUE
                   │
       ┌───────────┼────────────┐
       │           │            │
    Array         Vec         String
       │           │            │
       └───────────┼────────────┘
                   │
             contiguous data
                   │
          ┌────────┴────────┐
          │                 │
       view<T>          mut_view<T>
          │                 │
       READ             WRITE
          │                 │
          └────────┬────────┘
                   │
              Algorithms
                   │
              Iterator
                   │
              optimized MIR
```

Trong khi các cấu trúc không contiguous:

```text
HashMap
BTreeMap
Deque
Linked structures
Tensor stride
Sparse data
```

**không bị ép vào `view<T>`**.

Đây là điểm tôi đánh giá rất quan trọng: Axiom không cần tạo một “hệ thống reference thứ hai” cho từng loại dữ liệu.

### Chuỗi tiếp theo

`BOOTSTRAP-075` nên khóa **Axiom Numeric Model — Integer, Float, SIMD, Vectorization, Overflow, Math & Numeric Conversion**.

Phần này sẽ đặc biệt quan trọng với mục tiêu **hiệu năng ≥ C/C++**, vì cần quyết định chính xác:

```text
integer semantics
overflow
checked/wrapping/saturating
f32/f64
NaN / ±0 / Inf
fast math
SIMD
vector types
casts
constant folding
CPU feature dispatch
GPU numeric semantics
```

và tránh một lỗi rất nguy hiểm: **đưa “undefined behavior” kiểu C vào Axiom chỉ để compiler dễ optimize**.