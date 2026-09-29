Tiếp tục. Với nền tảng đã freeze đến `BOOTSTRAP-066`, bước tiếp theo hợp lý là chốt **mô hình dữ liệu tuyến tính, collection và view**. Đây là phần rất quan trọng vì nó nối trực tiếp **value semantics → ownership → capability → optimizer → ABI → GPU/FFI**.

# BOOTSTRAP-067 — Axiom Collection, Slice/View & Data Access Model

**Trạng thái: FROZEN**

## 1. Mục tiêu thiết kế

Axiom cần đạt đồng thời:

- cú pháp truy cập dữ liệu đơn giản như C/C++;
- không bắt programmer viết pointer/lifetime/borrow;
- không tạo allocation ngầm;
- bounds checking an toàn trong safe code;
- compiler có đủ thông tin để loại bỏ bounds check;
- alias analysis đủ mạnh để vectorize;
- collection có thể relocate;
- `view` không làm mất ownership;
- hỗ trợ tốt dữ liệu 1D, multidimensional, GPU;
- FFI không nhầm `view<T>` với C ABI;
- không ép mọi collection vào một representation duy nhất.

Nguyên tắc:

> **Collection sở hữu dữ liệu. View mô tả quyền truy cập vào một vùng dữ liệu. Indexing là phép truy cập có kiểm tra.**

---

# 2. Phân biệt các khái niệm

Axiom không dùng một kiểu duy nhất cho tất cả:

| Khái niệm | Ý nghĩa |
|---|---|
| `[T; N]` | Array cố định, chứa trực tiếp `N` phần tử |
| `Vec<T>` | Collection động, sở hữu vùng phần tử |
| `view<T>` | Quyền đọc một vùng `T` |
| `mut_view<T>` | Quyền ghi độc quyền vào một vùng `T` |
| `Str` | View đọc text UTF-8 |
| `String` | Text UTF-8 sở hữu |
| `Bytes` | Binary data sở hữu |
| `Buffer<T>` | Owned contiguous storage tổng quát |
| `DeviceBuffer<T>` | Owned storage trên device |
| `Handle<T>` | Logical identity, không phải memory view |

Điểm quan trọng:

**`view<T>` không phải một collection.**

Nó là **capability truy cập**.

Điều này giữ cho ownership và access model không bị trộn lẫn.

---

# 3. `[T; N]` — Fixed Array

Cú pháp:

```axiom
let a = [10, 20, 30, 40]
```

Type:

```axiom
[i32; 4]
```

Hoặc:

```axiom
let a: [i32; 4] = [10, 20, 30, 40]
```

Đặc tính:

- kích thước compile-time;
- contiguous;
- semantic element order cố định;
- value type;
- không allocation;
- không relocation;
- có thể nằm register/stack/inline/embedded trong object tùy optimizer.

Index:

```axiom
let x = a[2]
```

Safe code:

```text
index < length
```

được kiểm tra về mặt semantic.

Compiler có thể loại bỏ check nếu chứng minh được.

---

# 4. `Vec<T>` — Dynamic Collection

`Vec<T>` là collection động sở hữu các phần tử.

Semantic state:

```text
Vec<T>
 ├── storage identity
 ├── length
 └── capacity
```

Representation thực tế có thể là:

```text
pointer + length + capacity
```

nhưng **đây không phải representation bắt buộc của language semantics**.

Ví dụ:

```axiom
var numbers = Vec<i32>()

numbers.push(10)
numbers.push(20)
numbers.push(30)
```

Truy cập:

```axiom
let x = numbers[1]
```

Thêm:

```axiom
numbers.push(40)
```

---

# 5. Relocation của `Vec`

Đây là điểm cực kỳ quan trọng.

`Vec<T>` mặc định là **relocatable storage**.

Ví dụ:

```axiom
var v = Vec<i32>()
v.push(10)

let x = view(v)

v.push(20)
```

Nếu `push()` có khả năng relocation thì compiler phải phát hiện:

```text
x
 ↓
depends on v storage
```

và không cho phép thao tác có khả năng làm invalid `x`.

Có thể:

```axiom
let x = view(v)

use(x)

v.push(20)
```

vì capability `x` đã kết thúc trước `push`.

Hoặc:

```axiom
v.reserve(100)
```

**không mặc nhiên biến `Vec` thành stable-address storage.**

Đây chính là quyết định đã thống nhất trước đó:

> `reserve` là capacity guarantee, không phải address-stability guarantee.

Nếu programmer cần stable address:

```axiom
StableBox<T>
Arena<T>
Pool<T>
```

hoặc abstraction tương đương ở library/system layer.

---

# 6. `view<T>` — chính xác nó là gì?

Đây là điểm cần freeze rõ để tránh ambiguity sau này.

Ta giữ:

```axiom
view<T>
```

là **read capability đối với một contiguous region của `T`**.

Nó **không phải**:

```text
reference
pointer
slice object
collection
owner
```

mà là semantic capability.

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32
```

nghĩa là:

> function được quyền đọc một vùng contiguous gồm các `i32`.

ABI có thể cuối cùng trở thành:

```text
(ptr, length)
```

nhưng compiler semantic model vẫn là:

```text
Capability {
    element_type = i32
    region = contiguous region
    access = READ
    provenance = owner
}
```

Điều này rất hợp với optimizer.

---

# 7. Vì sao không dùng `view<[T]>`?

Không nên thay bằng kiểu:

```axiom
view<[T]>
```

trong Core.

Vì `[T; N]` đã có nghĩa:

> fixed-size array.

Trong khi view cần biểu diễn:

> runtime-sized contiguous region.

Do đó:

```text
[T; N]     = owned fixed-size array
view<T>    = borrowed read capability over T region
mut_view<T> = borrowed write capability over T region
```

là hai khái niệm khác nhau.

Ví dụ:

```axiom
fn process(data: view<f32>)
```

có thể nhận:

```axiom
[i32; 1024]
Vec<f32>
Buffer<f32>
```

thông qua **ephemeral owner → view conversion** đã freeze trước đó.

---

# 8. `mut_view<T>`

Tương tự:

```axiom
fn fill(data: mut_view<i32>)
```

cho phép:

- đọc;
- ghi;
- nhưng giữ exclusive WRITE capability.

Ví dụ:

```axiom
fn zero(data: mut_view<i32>) {
    for i in 0..data.len() {
        data[i] = 0
    }
}
```

Không được tạo hai mutable capability có khả năng overlap:

```axiom
let a = mut_view(v)
let b = mut_view(v)
```

nếu compiler không chứng minh `a` và `b` DISJOINT.

---

# 9. Slicing

Syntax:

```axiom
let part = view(v)[10..20]
```

hoặc compiler/library có thể cung cấp:

```axiom
let part = v[10..20]
```

Semantic result:

```text
view<T>
```

đối với immutable source.

Mutable source/capability:

```text
mut_view<T>
```

nếu quyền truy cập cho phép.

Slice **không copy dữ liệu**.

Nó tạo capability mới với region:

```text
original: [0 ................. 100)
slice:          [10 ..... 20)
```

Compiler giữ provenance:

```text
slice.provenance = original.provenance
slice.region = [10,20)
```

---

# 10. Nested / multidimensional data

Không nên tạo một primitive multidimensional array riêng trong Core.

Dùng composition.

Ví dụ:

```axiom
let image: [[u8; 1920]; 1080]
```

là:

```text
array 1080 elements
    each element = array 1920 u8
```

Đây là **array-of-arrays**, có semantic layout tương ứng.

Trong trường hợp cần contiguous matrix:

```axiom
let pixels = Vec<u8>()
```

và API:

```axiom
fn pixel(
    image: view<u8>,
    width: usize,
    x: usize,
    y: usize
) -> u8
```

hoặc library abstraction:

```axiom
Tensor<T, Shape>
Matrix<T, R, C>
```

Những abstraction này nằm ở library chứ không cần làm Core type.

---

# 11. Str

`Str` là một trường hợp chuyên biệt của read-only text view.

Conceptually:

```text
Str
 ├── UTF-8 byte region
 └── read capability
```

Ví dụ:

```axiom
fn print(text: Str)
```

không sở hữu text.

Trong khi:

```axiom
let name: String
```

sở hữu text.

Chuyển:

```text
String → Str
```

không copy.

Nhưng:

```text
Str → String
```

nếu cần ownership thì phải tạo bản copy/materialization.

---

# 12. Bytes

Không dùng `String` cho binary.

```axiom
Bytes
```

là owned binary data.

View binary:

```axiom
view<u8>
```

hoặc API alias thuận tiện ở library:

```axiom
ByteView
```

Nhưng Core capability vẫn là:

```axiom
view<u8>
mut_view<u8>
```

Điều này rất tốt cho FFI, networking, file I/O và GPU.

---

# 13. Buffer<T>

`Buffer<T>` là abstraction cho owned contiguous storage tổng quát.

Khác biệt với `Vec<T>`:

```text
Vec<T>
    collection semantics
    length/capacity
    push/pop/etc.

Buffer<T>
    storage semantics
    contiguous storage
    explicit size/capacity operations
```

Điều này hữu ích cho:

- I/O;
- DMA;
- GPU;
- memory mapping;
- custom allocators;
- system programming.

Ví dụ:

```axiom
var buffer = Buffer<u8>(4096)

read(file, mut_view(buffer))?
```

---

# 14. Indexing semantics

Axiom giữ syntax đơn giản:

```axiom
x[i]
```

nhưng semantic operation được phân biệt.

### Safe indexing

```axiom
x[i]
```

có bounds verification.

Nếu compiler không chứng minh:

```text
0 <= i < len
```

thì runtime check tồn tại.

Failure đi qua profile panic/trap/error semantics đã freeze.

### Unchecked indexing

Không nên tạo:

```axiom
unsafe_x[i]
```

như một language primitive riêng.

System/library có thể cung cấp:

```axiom
unsafe {
    unchecked_index(x, i)
}
```

hoặc intrinsic tương ứng.

Điều này tránh làm syntax Core phình ra.

---

# 15. Bounds-check elimination

Compiler có thể chứng minh:

```axiom
for i in 0..a.len() {
    sum += a[i]
}
```

thì:

```text
i < a.len()
```

đã được chứng minh.

Result:

```text
no bounds check
```

Tương tự:

```axiom
for i in 0..n {
    a[i] = b[i] + c[i]
}
```

có thể đồng thời chứng minh:

```text
i < len(a)
i < len(b)
i < len(c)
```

và nếu capability analysis chứng minh:

```text
a != overlap(b)
a != overlap(c)
```

thì optimizer có thể vectorize.

Đây là một trong những điểm Axiom có thể đạt hiệu năng native rất tốt **mà không bắt programmer viết unsafe**.

---

# 16. Iteration

Canonical:

```axiom
for x in values {
    process(x)
}
```

Iterator là trait/library abstraction.

Compiler có thể lower:

```text
for
 ↓
iterator
 ↓
next()
 ↓
CFG/MIR
 ↓
inline
 ↓
bounds/range optimization
 ↓
native loop
```

Không được mặc định tạo:

- heap allocation;
- iterator object;
- virtual dispatch;
- closure allocation.

Vì vậy:

```axiom
for x in vec {
    sum += x
}
```

có thể trở thành loop machine-level gần tương đương C.

---

# 17. Mutable iteration

Ví dụ:

```axiom
for x in mut_view(values) {
    x *= 2
}
```

Iterator nhận `mut_view<T>` hoặc abstraction tương đương.

Compiler phải duy trì:

```text
one exclusive mutable access
```

trong phạm vi iteration.

Không cho phép đồng thời tạo conflicting access:

```text
mut_view(values)
+
mut_view(values)
```

nếu overlap không được chứng minh là DISJOINT.

---

# 18. Index và capability

Một điểm quan trọng:

```axiom
let x = view(v)
```

không có nghĩa compiler phải tạo một object runtime.

Sau verification:

```text
Capability
 ├── provenance
 ├── region
 ├── access
 └── lifetime
```

có thể bị erase.

Runtime chỉ còn representation cần thiết, ví dụ:

```text
pointer + length
```

hoặc thậm chí ít hơn nếu compiler biết kích thước.

Đây chính là:

> **Proof machinery erasure**

đã được freeze ở `BOOTSTRAP-056`.

---

# 19. View và relocation

Rule chính thức:

```text
LIVE VIEW
    ↓
dependent storage
    ↓
relocation operation
    ↓
CONFLICT
```

Ví dụ:

```axiom
var v = Vec<i32>()
let x = view(v)

v.push(1)     // reject nếu push có khả năng relocate
```

Nhưng:

```axiom
let x = view(v)

use(x)

v.push(1)     // OK, nếu x không còn live
```

Compiler có thể làm lifetime ngắn nhất có thể dựa trên last-use.

---

# 20. View của field

Axiom cho phép field-level disjointness.

```axiom
struct Point {
    x: f32
    y: f32
}
```

Compiler có thể chứng minh:

```text
view(p.x)
mut_view(p.y)
```

không overlap.

Do đó:

```axiom
fn update(p: mut_view<Point>) {
    let x = view(p.x)
    let y = mut_view(p.y)

    ...
}
```

có thể hợp lệ nếu region analysis chứng minh DISJOINT.

Đây là một lợi thế lớn so với mô hình borrow đơn giản chỉ nhìn toàn bộ object.

---

# 21. Range capability

Một capability có thể có region:

```text
Whole
Field
Index
Range
Subregion
```

Ví dụ:

```text
v = [0..100)

a = [0..50)
b = [50..100)
```

Compiler chứng minh:

```text
a DISJOINT b
```

và cho phép:

```text
mut_view(a)
mut_view(b)
```

đồng thời.

Điều này đặc biệt quan trọng cho:

- SIMD;
- parallel loops;
- GPU;
- multicore;
- image processing;
- tensor.

---

# 22. GPU

`DeviceBuffer<T>` và `DeviceView<T>` không phá vỡ model.

Ví dụ:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

GPU compiler vẫn sử dụng:

```text
type
ownership
capability
region
alias
range
execution domain
storage domain
```

đã có.

Không tạo một hệ pointer/array riêng cho GPU.

---

# 23. FFI

Không cho phép:

```axiom
extern "C" fn foo(data: view<u8>)
```

tự động có nghĩa:

```text
uint8_t* + size_t
```

vì `view<u8>` là semantic capability của Axiom.

Thay vào đó phải có C-compatible representation rõ ràng:

```axiom
@repr(C)
struct CSliceU8 {
    data: *const u8
    len: usize
}
```

và wrapper:

```text
C ABI
 ↓
unsafe boundary
 ↓
validate
 ↓
view<u8>
 ↓
safe Axiom
```

Như vậy FFI không làm ô nhiễm semantics của Core.

---

# 24. Collection và ownership

Collection ownership hoàn toàn tách khỏi access.

Ví dụ:

```axiom
var data = Vec<u8>()
```

`data` sở hữu storage.

```axiom
let r = view(data)
```

`r` không sở hữu.

```axiom
consume(data)
```

sẽ Move ownership.

Nếu `r` còn live:

```text
consume(data)
```

bị reject vì owner không thể bị invalid khi capability phụ thuộc còn sống.

---

# 25. Copy / Clone của collection

`Vec<T>` mặc định:

```text
!Copy
```

Move:

```axiom
let b = a
```

không copy toàn bộ elements.

Nếu cần duplicate:

```axiom
let b = a.clone()
```

Clone có thể:

```text
allocate
copy N elements
```

hoặc được tối ưu nếu semantics cho phép.

`view<T>` có thể duplicate read capability:

```axiom
let a = view(data)
let b = a
```

nhưng đây **không phải Copy trait**.

Nó là intrinsic capability duplication.

---

# 26. Empty collection / zero-length view

Phải hỗ trợ:

```text
len = 0
```

một cách bình thường.

Một empty view vẫn có semantic provenance khi cần.

Compiler không được yêu cầu một địa chỉ vật lý đặc biệt cho empty region.

Đặc biệt:

```text
empty view != null pointer
```

và:

```text
Option<view<T>>
```

không được dựa vào null semantics ở Core.

---

# 27. ZST

Nếu:

```axiom
struct Marker {}
```

thì:

```axiom
Vec<Marker>
```

vẫn hợp lệ.

Compiler có thể không cần physical storage cho từng element nếu semantics cho phép.

Do đó:

```text
logical length
```

có thể khác hoàn toàn:

```text
physical byte size
```

Đây phù hợp với `ZST` đã được freeze ở representation model.

---

# 28. Không ép allocator vào collection type

Không thiết kế:

```axiom
Vec<T, Allocator>
```

làm default Core syntax.

Allocator là storage implementation/system concern.

Programmer chỉ cần abstraction allocator khi thực sự cần:

```axiom
Arena
Pool
CustomAllocator
DeviceAllocator
```

Điều này giữ API đơn giản nhưng không hạn chế systems programming.

---

# 29. Ownership vs collection lifetime

Phải phân biệt:

```text
collection lifetime
element lifetime
resource lifetime
memory lifetime
view lifetime
```

Ví dụ `Vec<File>`:

```text
Vec lifetime
    ↓
elements
    ↓
File resources
    ↓
Drop
```

`Vec` bị drop không đơn giản chỉ là:

```text
free(memory)
```

mà trước tiên phải đảm bảo Drop semantics của elements.

Đây tiếp tục nguyên tắc:

> **Resource lifetime is distinct from memory lifetime.**

---

# 30. String indexing

Axiom **không nên định nghĩa**:

```axiom
text[i]
```

là lấy Unicode character theo code point một cách mặc định.

Vì UTF-8 không có O(1) code-point indexing tổng quát.

Do đó:

```text
String / Str
```

nên cung cấp các API rõ nghĩa:

```text
bytes()
chars()
graphemes()
```

và:

```axiom
text[i]
```

nếu được hỗ trợ ở library thì phải có semantics được xác định rõ, không giả vờ rằng Unicode character indexing là byte-offset O(1).

Đây là một chỗ Axiom cần ưu tiên **performance predictability**.

---

# 31. Data access hierarchy

Toàn bộ mô hình có thể thu gọn thành:

```text
                 VALUE
                   │
        ┌──────────┴──────────┐
        │                     │
    OWNED DATA            ACCESS CAPABILITY
        │                     │
   Array / Vec /           view<T>
   Buffer / String         mut_view<T>
        │                     │
        └──────────┬──────────┘
                   │
              REGION MODEL
                   │
       ┌───────────┼───────────┐
       │           │           │
     Whole       Field       Range
       │           │           │
       └───────────┴───────────┘
                   │
             ALIAS ANALYSIS
                   │
       ┌───────────┼───────────┐
       │           │           │
   DISJOINT       SAME       UNKNOWN
       │                       │
 optimization              conservative
```

Đây là kiến trúc rất quan trọng của Axiom.

---

# 32. Quyết định quan trọng: không có `Slice<T>` Core primitive

Tôi đề xuất **không thêm `Slice<T>` vào Language Core**.

Thay vào đó:

```text
view<T>
mut_view<T>
```

đã đủ về mặt semantic.

Library có thể đặt alias/API:

```axiom
type Slice<T> = view<T>
type MutSlice<T> = mut_view<T>
```

nếu muốn.

Như vậy không tạo thêm một semantic concept thứ ba:

```text
reference
slice
view
borrow
```

mà chỉ có:

> **access capability**

Điều này rất phù hợp triết lý Axiom.

---

# 33. Mô hình cuối cùng

Axiom sẽ có:

```text
[T; N]
    fixed owned array

Vec<T>
    growable owned collection

Buffer<T>
    owned contiguous storage

String
    owned UTF-8 text

Bytes
    owned binary storage

Str
    read-only UTF-8 text capability

view<T>
    read-only contiguous T capability

mut_view<T>
    exclusive mutable contiguous T capability
```

và:

```text
Handle<T>
    logical identity
```

không phải memory access.

---

# 34. Frozen Invariants — ADATA-20..100

### Collection semantics

- **ADATA-20** Array `[T; N]` is a fixed-size value.
- **ADATA-21** Fixed arrays are semantically contiguous.
- **ADATA-22** Array length is compile-time known.
- **ADATA-23** Array storage requires no dynamic allocation.
- **ADATA-24** Array element order is semantically defined.
- **ADATA-25** `Vec<T>` is an owned growable collection.
- **ADATA-26** `Vec<T>` has semantic length.
- **ADATA-27** `Vec<T>` has semantic capacity.
- **ADATA-28** `Vec<T>` storage may relocate.
- **ADATA-29** `reserve` does not guarantee stable address.
- **ADATA-30** `Buffer<T>` is owned contiguous storage.
- **ADATA-31** Collection representation is not part of ordinary type semantics.
- **ADATA-32** Collection allocation strategy is not fixed by Core.
- **ADATA-33** Collection allocation may be optimized away when unobservable.
- **ADATA-34** Collection ownership is distinct from element access.
- **ADATA-35** Collection Drop follows ownership/Drop semantics.

### View semantics

- **ADATA-36** `view<T>` is a read capability.
- **ADATA-37** `mut_view<T>` is an exclusive write capability.
- **ADATA-38** View is not ownership.
- **ADATA-39** View is not a general reference primitive.
- **ADATA-40** View is not a collection.
- **ADATA-41** `view<T>` may be duplicated as a read capability.
- **ADATA-42** `mut_view<T>` is non-duplicable unless an explicit concurrency abstraction establishes otherwise.
- **ADATA-43** View provenance is tracked semantically.
- **ADATA-44** View region is tracked semantically.
- **ADATA-45** View access mode is tracked semantically.
- **ADATA-46** View lifetime is compiler-derived.
- **ADATA-47** Owner destruction cannot invalidate a live view.
- **ADATA-48** Relocation cannot invalidate a live dependent view.
- **ADATA-49** Owner-to-view implicit conversion is allowed only for ephemeral call arguments.
- **ADATA-50** Persistent view creation is explicit.

### Regions and slicing

- **ADATA-51** Regions may represent whole objects.
- **ADATA-52** Regions may represent fields.
- **ADATA-53** Regions may represent indices.
- **ADATA-54** Regions may represent ranges.
- **ADATA-55** Regions may represent nested subregions.
- **ADATA-56** Slicing does not copy elements.
- **ADATA-57** Slice/view provenance derives from source provenance.
- **ADATA-58** Unknown overlap cannot be treated as disjoint.
- **ADATA-59** Proven disjoint regions may coexist mutably.
- **ADATA-60** Region proofs are compiler semantic facts.

### Indexing

- **ADATA-61** Safe indexing is bounds-checked semantically.
- **ADATA-62** Bounds failure cannot produce memory corruption in safe code.
- **ADATA-63** Bounds checks may be eliminated after proof.
- **ADATA-64** Range analysis may prove bounds.
- **ADATA-65** Loop analysis may prove bounds.
- **ADATA-66** Capability region analysis may prove bounds.
- **ADATA-67** Unchecked access is unsafe/system functionality.
- **ADATA-68** Unsafe indexing does not disable unrelated semantic verification.

### Iteration

- **ADATA-69** `for` uses the iteration abstraction.
- **ADATA-70** Iteration does not imply heap allocation.
- **ADATA-71** Iteration does not imply dynamic dispatch.
- **ADATA-72** Iterator abstraction may be fully optimized away.
- **ADATA-73** Mutable iteration requires exclusive access.
- **ADATA-74** Iterator capability cannot outlive its source.
- **ADATA-75** Iterator lowering preserves ownership and Drop semantics.

### Text/binary

- **ADATA-76** `String` owns UTF-8 text.
- **ADATA-77** `Str` is read-only UTF-8 text access.
- **ADATA-78** `Bytes` represents owned binary data.
- **ADATA-79** Binary data is not implicitly text.
- **ADATA-80** Text indexing does not imply constant-time Unicode character indexing.
- **ADATA-81** UTF-8 validity is part of text-type semantics.
- **ADATA-82** Byte-level access is distinct from character-level access.

### GPU / FFI

- **ADATA-83** Device views use the same capability principles.
- **ADATA-84** Device storage domain remains distinct from host storage.
- **ADATA-85** GPU views preserve region and alias semantics.
- **ADATA-86** GPU execution does not introduce a second collection model.
- **ADATA-87** `view<T>` is not automatically a C ABI slice.
- **ADATA-88** FFI slices require explicit representation contracts.
- **ADATA-89** Raw-pointer conversion to view requires an unsafe boundary.
- **ADATA-90** FFI does not transfer ownership implicitly.

### Optimization

- **ADATA-91** View verification may be erased after semantic verification.
- **ADATA-92** Proven disjoint regions may strengthen internal alias analysis.
- **ADATA-93** Proven ranges may eliminate bounds checks.
- **ADATA-94** Proven collection non-relocation enables safe storage optimization.
- **ADATA-95** Iterator abstractions may be scalarized/inlined/eliminated.
- **ADATA-96** Collection abstractions must not impose mandatory runtime allocation.
- **ADATA-97** Collection abstractions must not impose mandatory dynamic dispatch.
- **ADATA-98** Optimization cannot invalidate live capability provenance.
- **ADATA-99** Optimization cannot reinterpret collection ownership.
- **ADATA-100** Collection, view, indexing and iteration semantics are preserved across all optimization levels.

---

## Kết luận kiến trúc

Sau `BOOTSTRAP-067`, mô hình dữ liệu của Axiom khá sạch:

```text
OWNERSHIP
    │
    ├── Array
    ├── Vec
    ├── Buffer
    ├── String
    └── Bytes
          │
          ▼
       ACCESS
          │
     ┌────┴────┐
     │         │
   view     mut_view
     │         │
     └────┬────┘
          ▼
        REGION
          │
    ┌─────┼─────┐
 Whole  Field  Range
          │
          ▼
      VERIFIER
          │
          ▼
    ALIAS / RANGE
          │
          ▼
      OPTIMIZER
          │
          ▼
   SIMD / CPU / GPU
```

Đặc biệt, **không cần `T&`, `T&&`, `borrow`, `Slice`, lifetime annotation hay GC** để đạt mô hình này.

Và đây chính là điểm tôi cho rằng Axiom đang đi đúng hướng: **programmer nhìn thấy ownership và access boundary khi cần; còn lifetime, alias, relocation, bounds và storage placement được compiler xử lý phía dưới.**

**Task kế tiếp: `BOOTSTRAP-068 — Axiom Numeric Model, Integer Semantics, Floating-Point & SIMD`**. Đây sẽ là phần cần chốt kỹ vì nó ảnh hưởng trực tiếp đến khả năng cạnh tranh hiệu năng với C/C++, overflow, fast math, vectorization, GPU và ABI.