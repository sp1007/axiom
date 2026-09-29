Được. Phần tiếp theo tôi đề xuất chốt là **Array / Slice / View / String / Bytes + Data-Oriented Collections**. Đây là tầng nằm ngay trên memory model vừa chốt và cũng là nơi Axiom có thể tạo khác biệt lớn về UX.

# Axiom Sequence & Text Model v0.1

## 1. Tách rõ 4 khái niệm

Tôi muốn Axiom có ranh giới cực rõ:

```text
Array<T,N>     = storage cố định
Vec<T>         = owned dynamic storage
view<T>        = non-owning read capability
mut_view<T>    = non-owning write capability
```

Không nên có một kiểu "slice/reference" chung chung làm tất cả.

Ví dụ:

```axiom
let a: Array<i32, 4> = [1, 2, 3, 4]

let v = view(a)
```

Ở đây:

```text
a   → owns storage
v   → borrows capability
```

nhưng programmer không cần viết lifetime.

---

# 2. Array phải cực kỳ đơn giản

```axiom
let a = [10, 20, 30, 40]
```

Compiler suy ra:

```text
Array<i32, 4>
```

Storage:

```text
┌────┬────┬────┬────┐
│ 10 │ 20 │ 30 │ 40 │
└────┴────┴────┴────┘
```

Đây là value.

Có thể:

```axiom
let b = a
```

Nếu `T: Copy`, copy cả array theo semantics Copy.

Nếu `T` không Copy:

```text
a → MOVE → b
```

---

# 3. Array nên hỗ trợ compile-time length

```axiom
fn sum(a: view<i32>) -> i32
```

là dynamic-length view.

Nhưng:

```axiom
fn transform(a: view<Array<i32, 4>>)
```

là một thứ khác.

Tôi đề xuất hỗ trợ const generic:

```axiom
fn dot<T, N>(a: Array<T, N>, b: Array<T, N>) -> T
```

với `N` là compile-time constant.

Compiler có thể unroll:

```text
N = 4
```

thành code SIMD/vectorized nếu phù hợp.

---

# 4. Không nên tạo một `Slice<T>` riêng nếu không cần

Đây là chỗ tôi muốn đơn giản hóa.

Nhiều ngôn ngữ có:

```text
Array
Slice
Span
SpanMut
SliceRef
ArrayView
```

Axiom không cần quá nhiều type.

Core chỉ cần:

```text
view<T>
mut_view<T>
```

và chúng có thể biểu diễn contiguous sequence.

Ví dụ:

```axiom
let a = [1, 2, 3, 4, 5]

let x = view(a)[1..4]
```

Semantic:

```text
view<T>
region = [1, 4)
```

---

# 5. Slice syntax

Tôi đề xuất:

```axiom
a[1..4]
```

nghĩa là:

```text
[1, 4)
```

Tức:

```text
1, 2, 3
```

Các dạng:

```text
a[..4]      // [0,4)
a[1..]      // [1,len)
a[..]       // entire sequence
a[1..=4]    // [1,4]
```

Nhưng cần phân biệt:

```axiom
a[i]
```

với:

```axiom
a[i..j]
```

Cái thứ hai tạo **view**, không copy dữ liệu.

---

# 6. View không phải một object runtime bắt buộc

Đây là một điểm rất quan trọng.

Source:

```axiom
let v = view(a)
```

không có nghĩa Axiom bắt buộc tạo object:

```text
struct View {
    ptr
    len
}
```

Compiler có thể dùng:

```text
pointer + length
```

nếu cần.

Hoặc:

```text
pointer
```

nếu length compile-time.

Hoặc thậm chí loại bỏ hoàn toàn view.

Do đó:

> `view<T>` là semantic capability, không phải promise về representation.

---

# 7. `view<T>` nên được phép copy

Ví dụ:

```axiom
let a = [1,2,3]

let x = view(a)
let y = x
```

Hoàn toàn hợp lệ.

Vì cả hai chỉ có READ capability.

```text
a
├── READ x
└── READ y
```

---

# 8. `mut_view<T>` thì khác

```axiom
let x = mut_view(a)
```

không được tự ý:

```axiom
let y = x
```

theo semantics của một value bình thường.

Bởi:

```text
x ──WRITE──→ region
y ──WRITE──→ same region
```

sẽ phá exclusive mutation.

Do đó:

```text
view<T>      → shareable read capability
mut_view<T>  → exclusive write capability
```

---

# 9. Có cần `view_mut` syntax không?

Không.

Giữ:

```text
view<T>
mut_view<T>
```

là đủ.

Không cần:

```text
&mut T
& T
SliceMut<T>
SpanMut<T>
```

đây là một trong những nơi Axiom có thể đơn giản hơn đáng kể.

---

# 10. View của field

Một lợi thế rất lớn của region model:

```axiom
struct Player {
    position: Vec2
    health: i32
}
```

Ta có thể:

```axiom
let hp = mut_view(player.health)
```

và:

```axiom
let pos = mut_view(player.position)
```

đồng thời.

Compiler biết:

```text
region(player.health)
DISJOINT
region(player.position)
```

nên không conflict.

Đây là lý do region-based verifier tốt hơn việc chỉ nghĩ theo "object reference".

---

# 11. View vào Vec

```axiom
let v = view(xs[10..20])
```

View có provenance:

```text
storage = xs.storage
region = [10,20)
access = READ
```

Nếu:

```axiom
xs.push(...)
```

có khả năng relocation:

```text
v
 ↓
dependent on xs storage
 ↓
push MAY_RELOCATE
```

compiler kiểm tra như phần trước.

---

# 12. Nested views

Cho phép:

```axiom
let a = [1,2,3,4,5]

let x = view(a[1..5])
let y = view(x[1..3])
```

Semantic:

```text
a
└── x [1..5]
     └── y [2..4]
```

Compiler có thể collapse:

```text
y → original storage [2..4]
```

không cần tạo runtime object cho x.

---

# 13. View không được escape owner

Ví dụ:

```axiom
fn bad() -> view<i32> {
    let a = [1,2,3]
    return view(a)
}
```

Reject.

Diagnostic:

```text
AX_VIEW_0001:
cannot return a view into local storage `a`;
the storage ends when this function returns.
```

Không cần:

```text
borrowed value does not live long enough
```

---

# 14. Nhưng view có thể return từ input

Ví dụ:

```axiom
fn first(xs: view<i32>) -> view<i32> {
    return xs[0..1]
}
```

Hợp lệ.

Compiler chứng minh:

```text
returned region ⊆ input region
```

Đây là một invariant cực đẹp:

> **A returned view must have provenance contained in a valid input storage region.**

---

# 15. String và Bytes phải tách hoàn toàn

Đây là quyết định tôi khuyên giữ rất mạnh:

```text
Bytes ≠ Text
```

Không implicit conversion.

Ví dụ:

```axiom
let data: Bytes = ...
let text: Text = data
```

→ lỗi.

Phải decode:

```axiom
let text = Text.from_utf8(data)?
```

---

# 16. `Bytes`

`Bytes` là dữ liệu byte thuần:

```text
u8 sequence
```

Dùng cho:

- file
- network packet
- compression
- image
- binary protocol
- serialization
- cryptography
- FFI.

Không có Unicode semantics.

---

# 17. `Text`

`Text` là **Unicode text semantic type**.

Tôi đề xuất implementation mặc định:

```text
UTF-8
```

nhưng:

> UTF-8 là representation policy, không phải bản chất semantic của Text.

Điều này cho phép sau này thay đổi representation nếu cần mà không phá semantics.

---

# 18. Không cho `text[i]` trả character

Đây là một quyết định quan trọng.

Không:

```axiom
text[5]
```

→ Unicode character.

Bởi vì "character" trong Unicode không đơn giản là một byte hay thậm chí một code point.

Thay vào đó:

```axiom
text.bytes()
text.chars()
text.graphemes()
```

là những abstraction khác nhau.

---

# 19. `Text.chars()`

Có thể trả iterator:

```axiom
for c in text.chars() {
    ...
}
```

Compiler/library xử lý UTF-8 decoding.

Không hứa:

```text
O(1) random character indexing
```

Đây là quyết định đúng về mặt performance và semantics.

---

# 20. `Text` nên immutable theo mặc định

Ví dụ:

```axiom
let name = "Xin chào"
```

không mutable.

Nếu cần xây text:

```axiom
var s = TextBuilder()
s.push(...)
s.push(...)
let text = s.finish()
```

hoặc:

```axiom
var s = Text(...)
s.append(...)
```

tùy stdlib.

Tôi nghiêng về **`TextBuilder` cho construction-heavy workloads**, còn Text nên thiên immutable.

---

# 21. `String` có nên tồn tại không?

Tôi nghĩ **không cần `String` trong Core**.

Có thể dùng:

```text
Text
Bytes
```

và stdlib có:

```text
TextBuilder
```

Nếu sau này cần tên `String` vì ecosystem compatibility thì có thể:

```axiom
type String = Text
```

nhưng không cần thêm một semantic type.

---

# 22. String literal

```axiom
let s = "Hello"
```

là `Text`.

Byte literal:

```axiom
let b = b"Hello"
```

là `Bytes` hoặc fixed byte array tùy syntax cuối cùng.

Tôi nghiêng về:

```text
"hello"     → Text
b"hello"    → Bytes
```

---

# 23. Không implicit Bytes ↔ Text

Điều này đặc biệt quan trọng ở FFI/network code.

Không muốn:

```axiom
send(socket, text)
```

ngầm encode UTF-8.

Tốt hơn:

```axiom
send(socket, text.bytes())
```

hoặc API socket tự nhận `view<u8>`.

Semantics rõ ràng.

---

# 24. Data-oriented programming

Axiom không nên ép mọi dữ liệu vào:

```text
Vec<Struct>
```

Ví dụ:

```axiom
struct Particle {
    position: Vec3
    velocity: Vec3
    lifetime: f32
}
```

`Vec<Particle>` là AoS:

```text
P0: pos vel life
P1: pos vel life
P2: pos vel life
```

Nhưng GPU/game/AI có thể muốn SoA:

```text
positions
velocities
lifetimes
```

---

# 25. Không đưa SoA vào Core

Thay vào đó stdlib có abstraction:

```axiom
SoA<Particle>
```

hoặc:

```axiom
Columns<Position, Velocity, Lifetime>
```

Compiler có thể optimize generic abstraction.

Quan trọng là:

> SoA là storage strategy, không phải một type-system primitive.

---

# 26. Iterator

Iterator đã có trong baseline:

```axiom
trait Iterator {
    type Item
    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Điều này rất hợp với Axiom.

Ví dụ:

```axiom
for x in xs {
    ...
}
```

compiler có thể lower thành:

```text
loop:
    x = iterator.next()
    match x:
        Some(v) → body
        None → exit
```

Sau optimization có thể thành một vòng lặp machine-level rất đơn giản.

---

# 27. Nhưng Iterator không được biến thành abstraction runtime bắt buộc

Ví dụ:

```axiom
xs.map(...).filter(...).map(...)
```

không nên tạo hàng loạt object iterator.

Monomorphization + inlining + escape analysis có thể biến thành:

```text
single loop
```

Ví dụ conceptual:

```text
map
  ↓
filter
  ↓
map
```

→

```text
for i:
    if condition:
        result = transform(...)
```

Đây chính là **Abstraction Erasure**.

---

# 28. Iterator và ownership

Cần 3 kiểu iteration semantic:

### Read

```axiom
for x in view(xs) {
}
```

`x` là value/copy hoặc read view tùy iterator.

### Mutable

```axiom
for x in mut_view(xs) {
}
```

`x` là mutable capability tới từng element.

### Consume

```axiom
for x in xs {
}
```

nếu `IntoIterator` của `Vec<T>` được thiết kế consuming.

Khi đó:

```text
Vec<T> → MOVED
```

và từng element được move ra.

---

# 29. Đây là nơi `IntoIterator` rất hữu ích

Có thể có:

```axiom
trait IntoIterator {
    type Item
    type Iter: Iterator<Item=Self.Item>

    fn into_iter(self: Self) -> Self.Iter
}
```

Và:

```axiom
trait Iterable {
    ...
}
```

hoặc đơn giản hóa hơn tùy trait hierarchy cuối cùng.

Không cần chốt ngay toàn bộ iterator trait ecosystem.

---

# 30. Array, Vec và View tạo thành một bộ rất đẹp

```text
                 Sequence
                    │
       ┌────────────┼────────────┐
       │            │            │
   Array<T,N>      Vec<T>      external
       │            │            │
       └──────┬─────┴────────────┘
              │
           view<T>
              │
          mut_view<T>
```

Các algorithm có thể nhận:

```axiom
fn sort(xs: mut_view<i32>)
```

và chạy được với:

```axiom
Array
Vec
Arena data
external buffer
```

mà không cần overload hàng chục lần.

---

# 31. Đây là lợi thế lớn của Axiom

Ví dụ:

```axiom
fn sum(xs: view<i32>) -> i32
```

Dùng được với:

```axiom
sum(view(array))
sum(view(vec))
sum(view(buffer))
sum(view(mapped_memory))
```

Không cần:

```text
sum_array()
sum_vec()
sum_slice()
sum_buffer()
sum_ptr()
```

và cũng không cần generic abstraction phức tạp.

---

# 32. Nhưng view không nên trở thành "reference type" phổ quát

Đây là giới hạn tôi muốn giữ.

`view<T>` dùng cho:

```text
contiguous read access
```

`mut_view<T>`:

```text
contiguous exclusive write access
```

Không dùng để biểu diễn:

```text
object identity
shared ownership
nullable reference
tree node identity
graph identity
```

Những thứ đó dùng:

```text
Box
Arc
PoolHandle
Option
raw pointer unsafe
```

tùy trường hợp.

---

# 33. Memory API lúc này khá hoàn chỉnh

Ta có:

```text
VALUE
 │
 ├── primitive
 ├── struct
 ├── enum
 ├── array
 └── tuple

OWNED STORAGE
 │
 ├── normal value
 ├── Box
 ├── Vec
 ├── Arena
 └── Pool

NON-OWNING CAPABILITY
 │
 ├── view
 └── mut_view

SHARED OWNERSHIP
 │
 └── Arc/Rc

SYSTEM MEMORY
 │
 ├── raw pointer
 ├── addr
 └── External
```

---

# 34. Một thay đổi nhỏ tôi muốn chốt

Từ các phần trước, tôi nghĩ nên **bỏ ý tưởng coi `view<T>` nhất thiết là "contiguous sequence"** ở tầng semantic.

Nó nên là:

> **A non-owning capability to a typed memory region.**

Một region có thể là:

```text
single T
array
subarray
struct field
external buffer
```

Sau đó API/library mới quy định operation nào yêu cầu contiguous sequence.

Như vậy:

```axiom
view<Player>
```

hoàn toàn hợp lệ.

Và:

```axiom
view<i32>
```

cũng hợp lệ.

Còn:

```axiom
view<i32>.len()
```

chỉ có nghĩa nếu capability biểu diễn sequence/region có extent.

Đây là một refinement đáng giá cho memory model.

---

# 35. Memory hierarchy cuối cùng

Tôi đề xuất Axiom có 3 tầng semantic:

### Tầng 1 — Value

```text
T
Array<T,N>
struct
enum
tuple
```

### Tầng 2 — Ownership/Storage

```text
Box<T>
Vec<T>
Arena<T>
Pool<T>
Arc<T>
```

### Tầng 3 — Capability

```text
view<T>
mut_view<T>
```

Còn:

```text
*T
addr
External
```

là system/unsafe.

Điều này tạo thành một mô hình rất nhất quán:

> **Value nói "cái gì".  
> Ownership nói "ai sở hữu".  
> Capability nói "ai được truy cập".  
> Storage nói "nó được lưu như thế nào".**

Bốn khái niệm không bị trộn vào nhau.

---

## Các invariant bổ sung

Tôi đề xuất thêm:

**ASEQ-01 — Array Value Semantics**  
Array là value và có kích thước compile-time.

**ASEQ-02 — View Non-Ownership**  
View không sở hữu storage.

**ASEQ-03 — MutView Exclusivity**  
MutView cung cấp exclusive write capability.

**ASEQ-04 — View Provenance**  
Mọi safe view có provenance hợp lệ.

**ASEQ-05 — View Containment**  
Returned view region phải nằm trong valid source region.

**ASEQ-06 — No Dangling View**  
Safe code không tạo dangling view.

**ASEQ-07 — No Implicit Text Conversion**  
Bytes và Text không implicit convert.

**ASEQ-08 — Unicode Semantic Text**  
Text có Unicode semantics.

**ASEQ-09 — No O(1) Character Indexing Guarantee**  
Text không hứa random character indexing O(1).

**ASEQ-10 — Iterator Erasure**  
Iterator abstraction có thể bị compiler loại bỏ hoàn toàn.

**ASEQ-11 — Data Layout Independence**  
AoS/SoA là storage strategies, không phải semantic requirement của struct.

**ASEQ-12 — Capability Over Reference**  
View/mut_view là access capabilities, không phải general-purpose reference objects.

---

### Một điểm tôi cho rằng rất đáng giữ cho Axiom

Ta đang dần tạo ra một mô hình mà programmer **gần như không phải nghĩ về con trỏ** trong code bình thường:

```axiom
fn process(data: view<u8>) {
    ...
}

fn update(data: mut_view<Particle>) {
    ...
}

fn create() -> Box<Node> {
    ...
}
```

Trong khi compiler phía dưới vẫn có đầy đủ:

```text
pointer
address
provenance
region
alias analysis
escape analysis
allocation
relocation
ABI
register allocation
```

Tức là **sự phức tạp vẫn tồn tại**, nhưng được đẩy về đúng nơi nó nên tồn tại: **compiler**, không phải programmer.

Bước kế tiếp tôi muốn đi vào **Object Identity + Graph/Tree + Self-reference + Intrusive Data Structures**. Đây là bài test rất quan trọng cho mô hình hiện tại: liệu Axiom có thể xử lý linked list, tree, graph, ECS, intrusive list, self-referential structure… mà không phải đưa `&`, lifetime, `Pin`, GC hoặc borrow checker syntax vào ngôn ngữ hay không.