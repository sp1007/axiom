Tiếp tục từ **Memory Access / Pointer / Aliasing v0.1**, bước hợp lý tiếp theo là chốt **Collection + String + Iterator + Resource API**. Đây là phần rất quan trọng vì nếu thiết kế sai, Axiom sẽ quay lại đúng những vấn đề mà ta đang cố tránh: heap bắt buộc, pointer lộ ra khắp nơi, allocation khó đoán, iterator nặng, hoặc API quá giống Rust/C++.

Tôi đề xuất giữ nguyên triết lý:

> **Người lập trình thao tác với giá trị và abstraction; compiler quyết định storage và tối ưu xuống machine code.**

## 1. Phân tầng Collection

Tôi sẽ không để `Vec`, `Array`, `view` cạnh tranh nhau về vai trò.

| Loại | Ownership | Kích thước | Storage | Mục đích |
|---|---|---|---|---|
| `Array<T,N>` | sở hữu | cố định | inline/value | dữ liệu nhỏ, fixed-size |
| `Vec<T>` | sở hữu | động | dynamic | collection tổng quát |
| `view<T>` | không sở hữu | động | external | đọc một vùng liên tục |
| `mut_view<T>` | không sở hữu | động | external | sửa một vùng liên tục |
| `Bytes` | sở hữu | động | dynamic | binary data |
| `Text` | sở hữu | động | dynamic | Unicode text |

Điểm quan trọng:

**`view<T>` không phải một collection.**

Nó là **capability truy cập vào một region**.

Ví dụ:

```axiom
fn sum(xs: view<i32>) -> i32 {
    var result = 0

    for x in xs {
        result += x
    }

    result
}
```

Compiler có thể biến toàn bộ thành:

```text
pointer + length
```

và thậm chí tối ưu loop hoàn toàn.

---

# 2. `Array<T, N>`

Array phải cực kỳ đơn giản.

```axiom
let a: Array<i32, 4> = [1, 2, 3, 4]
```

Semantic:

```text
Array<T,N>
    ├── N elements
    ├── contiguous
    ├── owned
    └── value semantics
```

Không heap.

Ví dụ:

```axiom
fn distance(a: Array<f32, 3>, b: Array<f32, 3>) -> f32
```

Compiler có thể truyền trực tiếp bằng register nếu ABI cho phép.

### Array → view

```axiom
fn sum(xs: view<i32>) -> i32

let a = [1, 2, 3, 4]

sum(a)
```

Đây là một trong những trường hợp hiếm hoi tôi cho phép **implicit owner → view**, đúng như semantic freeze trước đó.

Nhưng:

```axiom
let xs = a
```

không có nghĩa là tạo view.

Đây vẫn là Copy hoặc Move tùy `T`.

Muốn lưu view:

```axiom
let xs = view(a)
```

---

# 3. `Vec<T>`

Đây mới là collection động chủ lực.

```axiom
var numbers = Vec<i32>()

numbers.push(10)
numbers.push(20)
numbers.push(30)
```

Semantically:

```text
Vec<T>
 ├── logical region
 ├── storage identity
 ├── length
 └── capacity
```

Không nên đóng đinh semantic representation thành:

```text
ptr + len + cap
```

nhưng native implementation thường có thể chính xác như vậy.

### Ownership

```axiom
let a = Vec<i32>()
let b = a
```

Nếu `Vec` là non-Copy:

```text
a → MOVED
b → OWNED
```

Không clone.

Muốn clone:

```axiom
let b = clone(a)
```

Đây là nguyên tắc rất quan trọng để tránh C++-style copy ngầm.

---

# 4. Vấn đề lớn nhất của `Vec`: relocation

Ví dụ:

```axiom
var v = Vec<i32>()

v.push(1)

let x = view(v)

v.push(2)
```

Nếu `push(2)` phải relocate storage thì `x` có thể trở thành dangling view.

Compiler phải nhìn thấy:

```text
x
 ↓
region(v.storage)
```

và:

```text
push()
 ↓
MAY_RELOCATE
```

→ reject nếu relocation có thể ảnh hưởng tới `x`.

Đây chính là nơi **Capability + Region analysis** phát huy tác dụng.

### Nhưng tôi đề xuất thêm một nguyên tắc

Không nên bắt programmer phải suy nghĩ quá nhiều về `MAY_RELOCATE`.

Cho phép:

```axiom
var v = Vec<i32>()

v.reserve(1024)

let xs = mut_view(v)

...
```

Nhưng `reserve()` không nên tạo một "lời hứa" rằng mọi mutation sau đó không relocate mãi mãi.

Thay vào đó:

```text
capacity >= required
```

là fact compiler biết.

Nếu operation tiếp theo có thể vượt capacity:

```text
MAY_RELOCATE
```

→ verifier xử lý.

Như vậy programmer chỉ cần hiểu:

> **View sống → operation có khả năng thay đổi storage identity có thể bị chặn.**

Không cần hiểu borrow lifetime.

---

# 5. Iterator: không tạo object runtime

Đây là nơi Axiom có thể đơn giản hơn C++.

Tôi **không đề xuất** iterator interface kiểu Java:

```text
interface Iterator {
    bool hasNext()
    T next()
}
```

vì dễ tạo abstraction/runtime overhead không cần thiết.

Axiom nên coi:

```axiom
for x in xs {
    ...
}
```

là **language syntax**, sau đó compiler resolve thành iterator protocol.

Ví dụ conceptually:

```axiom
for x in xs
```

→

```axiom
let it = begin(xs)

while let Some(x) = next(mut_view(it)) {
    ...
}
```

Nhưng đây **không phải source-level lowering bắt buộc**; HIR có thể giữ `ForLoop` rồi MIR lowering trực tiếp.

---

# 6. Iterator là trait

Đề xuất:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Ví dụ:

```axiom
for x in numbers {
    print(x)
}
```

Compiler monomorphize:

```text
Iterator<Vec<i32>>
```

→ code chuyên biệt.

Không:

- virtual call
- heap allocation
- object header
- runtime iterator object bắt buộc.

Một iterator có thể chỉ là:

```text
{ pointer, index, end }
```

hoặc thậm chí chỉ còn một vài register sau optimization.

---

# 7. Range nên là value type

Không cần class đặc biệt.

```axiom
for i in 0..100 {
    ...
}
```

Semantic:

```axiom
Range<i32>
```

Có thể có:

```text
0..10       exclusive
0..=10      inclusive
```

Nhưng tôi nghiêng về việc **không tạo quá nhiều loại range trong Core**.

Ví dụ:

```text
Range<T>
```

với property:

```text
start
end
inclusive/exclusive
step
```

hoặc đơn giản hơn nữa, compiler có intrinsic range syntax.

Điều quan trọng là:

```axiom
for i in 0..100
```

phải compile xuống loop rất gần:

```asm
i = 0
loop:
    ...
    i++
    if i < 100 goto loop
```

Không allocation.

---

# 8. Collection algorithm

Một điểm tôi muốn Axiom làm khác C++:

**Không xây cả hệ thống iterator adapter quá khổng lồ trong Core.**

Ví dụ:

```axiom
numbers
    .map(...)
    .filter(...)
    .take(...)
    .collect(...)
```

có thể rất đẹp, nhưng nếu thiết kế trait/generic quá phức tạp thì compiler sẽ trở thành một con quái vật.

Axiom nên ưu tiên:

```axiom
for x in numbers {
    if predicate(x) {
        ...
    }
}
```

Compiler optimizer rất mạnh.

Sau đó stdlib có thể cung cấp:

```axiom
map(...)
filter(...)
```

nhưng chúng chỉ là library abstraction.

**Core không cần biết `map/filter`.**

---

# 9. `Bytes` và `Text` phải tách biệt

Đây là quyết định tôi cho rằng rất quan trọng.

Không nên có:

```text
String = byte array nhưng đôi lúc coi là Unicode
```

Thay vào đó:

```text
Bytes
Text
```

### Bytes

```axiom
var data = Bytes()
data.push(0xFF)
```

Semantic:

```text
Bytes ≈ Vec<u8>
```

nhưng có thể tối ưu implementation riêng.

### Text

```axiom
let name = Text("Xin chào")
```

`Text` biểu diễn Unicode text hợp lệ.

Representation ban đầu có thể là UTF-8, nhưng tôi không muốn **đóng semantic Text = UTF-8**.

Tức là:

```text
Text semantic
    ↓
implementation
    └── UTF-8 hiện tại
```

sau này có thể thay đổi representation mà không phá semantic language.

---

# 10. Không cho `text[i]` nghĩa là codepoint

Đây là một cái bẫy lớn.

Nếu:

```axiom
text[10]
```

trả về character thì programmer có thể nghĩ:

```text
O(1)
```

trong khi UTF-8 codepoint indexing có thể O(n).

Tôi đề xuất:

```axiom
text.bytes()
text.chars()
text.graphemes()
```

Ví dụ:

```axiom
for c in text.chars() {
    ...
}
```

và:

```axiom
for g in text.graphemes() {
    ...
}
```

Các abstraction này nằm ở stdlib, không phải Core.

---

# 11. `Text` không nên có implicit conversion từ `Bytes`

Đây là một chỗ Axiom nên nghiêm khắc.

Không:

```axiom
let text: Text = bytes
```

mà phải:

```axiom
let text = Text.from_utf8(bytes)?
```

vì bytes có thể không hợp lệ.

Ngược lại:

```axiom
let bytes = text.as_bytes()
```

có thể trả:

```text
view<u8>
```

nếu representation đảm bảo.

Hoặc:

```axiom
text.to_bytes()
```

nếu cần ownership riêng.

---

# 12. `Option<T>`

`Option` nên là enum bình thường nhưng compiler nhận biết nó ở một số nơi.

```axiom
enum Option<T> {
    None
    Some(T)
}
```

Ví dụ:

```axiom
fn find(...) -> Option<User>
```

Không có:

```text
null
```

trong safe Core.

Compiler có thể tối ưu:

```text
Option<*const T>
```

hoặc một số kiểu khác bằng **niche optimization**.

Nhưng programmer không được phụ thuộc vào representation đó.

---

# 13. `Result<T,E>`

Tương tự:

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Đây là cơ chế lỗi chính.

```axiom
fn read_file(...) -> Result<Bytes, IOError>
```

và:

```axiom
let data = read_file(path)?
```

`?` chỉ là syntax sugar cho control flow.

Nó không cần exception runtime.

---

# 14. Resource API

Đây là điểm cực kỳ quan trọng với mô hình memory của Axiom.

Ví dụ:

```axiom
let file = File.open(path)?
```

`File`:

```text
!Copy
Drop
```

Khi scope kết thúc:

```text
DROP file
```

Compiler gọi cleanup.

Nhưng:

```axiom
file.close()
```

mới là nơi xử lý lỗi:

```axiom
file.close()?
```

Không:

```text
Drop → close → nếu lỗi thì throw
```

Vì như vậy destruction sẽ trở nên phức tạp và không deterministic.

---

# 15. Resource abstraction tổng quát

Tôi đề xuất **không tạo `Resource` base class**.

Có thể có trait:

```axiom
trait Close {
    fn close(self: mut_view<Self>) -> Result<(), Error>
}
```

Nhưng `Drop` là semantic property đặc biệt của compiler.

Ví dụ:

```axiom
struct File {
    ...
}
```

```text
File
 ├── !Copy
 ├── Drop
 └── Close
```

`Drop` ≠ `Close`.

Đây là distinction rất quan trọng:

```text
Drop  = bảo đảm resource được giải phóng
Close = operation có thể thất bại
```

---

# 16. `Allocator`, `Arena`, `Pool`

Các abstraction này **không nên vào Core**.

Ví dụ stdlib:

```axiom
let arena = Arena.new()

let x = arena.alloc<Foo>()
```

Semantic:

```text
Arena
 └── owns allocations
```

Khi:

```axiom
drop(arena)
```

thì toàn bộ region của arena kết thúc.

Compiler kiểm tra:

```text
view(x)
```

không được sống qua:

```text
drop(arena)
```

Đây chính là ví dụ rất đẹp cho Region Model.

---

# 17. `Map` / `Set`

Ban đầu chỉ cần:

```text
Vec
HashMap
HashSet
```

Không cần hàng chục container trong Core.

Có thể sau này:

```text
BTreeMap
TreeSet
Deque
RingBuffer
SmallVec
Slab
SparseSet
```

nhưng tất cả là library.

Đặc biệt:

**`SmallVec<T,N>` không cần ngôn ngữ biết.**

Compiler chỉ thấy một struct có inline storage + dynamic storage.

Nếu optimizer tốt, abstraction này vẫn zero-cost.

---

# 18. Một nguyên tắc rất quan trọng: collection không được định nghĩa bằng pointer

Không nên:

```text
Vec = pointer + len + capacity
```

trong semantic specification.

Mà:

```text
Vec<T> =
    owning dynamically-sized contiguous sequence
```

Sau đó implementation:

```text
possible representation:
ptr + len + cap
```

Điều này cho compiler quyền:

```text
Vec<T>
```

→ stack representation

hoặc:

```text
small inline buffer
```

hoặc:

```text
register/scalarized
```

nếu không có observable address.

---

# 19. API nên hướng đến "semantic contracts"

Ví dụ:

```axiom
fn sort(xs: mut_view<i32>)
```

Compiler biết:

```text
READ xs
WRITE xs
```

Nhưng:

```axiom
fn append(v: mut_view<Vec<i32>>, x: i32)
```

có thể có effect:

```text
WRITE
MAY_RELOCATE
```

Từ đó verifier biết:

```text
active view into v
+
append
+
MAY_RELOCATE
=
potential conflict
```

Điều này mạnh hơn việc đơn giản hóa thành "borrow checker".

---

# 20. Tôi muốn chốt một kiến trúc rất quan trọng

Thay vì để collection API tự phát triển thành hàng trăm rule, Axiom nên có **4 protocol nền tảng**:

```text
Iterable
Indexable
Contiguous
Resizable
```

Ví dụ:

```text
Array<T,N>
    Iterable
    Indexable
    Contiguous
    !Resizable

Vec<T>
    Iterable
    Indexable
    Contiguous
    Resizable

view<T>
    Iterable
    Indexable
    Contiguous
    !Resizable
```

Nhưng đây là **library traits**, không phải compiler magic ngoại trừ những phần compiler cần để chứng minh safety/performance.

---

# 21. Bức tranh tổng thể hiện tại

Axiom lúc này đã có kiến trúc khá rõ:

```text
                    AXIOM
                      │
        ┌─────────────┴─────────────┐
        │                           │
   VALUE SEMANTICS            MEMORY SAFETY
        │                           │
 Struct / Enum / Array       Ownership
 Generic / Trait             Capability
 Closure                     Region
                              Effect
                                  │
                         ┌────────┴────────┐
                         │                 │
                       view             mut_view
                         │                 │
                         └────────┬────────┘
                                  │
                            Collections
                                  │
              ┌───────────────────┼──────────────────┐
              │                   │                  │
             Array               Vec               Bytes
              │                   │                  │
              └─────────────── view ────────────────┘
                                  │
                              Iterator
                                  │
                       generic zero-cost code
```

Và bên dưới:

```text
             Semantic Model
                   ↓
                 MIR
                   ↓
          Ownership/Region
          Capability/Effects
                   ↓
             Verified MIR
                   ↓
               Optimizer
                   ↓
                LIR
                   ↓
             Machine Code
```

Điểm tôi đánh giá rất tốt ở hướng này là **memory safety không nằm trong `Vec`, `String`, `Thread`, `Arc`...**

Nó nằm ở **semantic verifier của Axiom**.

Do đó sau này nếu có:

```text
GPUBuffer
SharedMemory
MappedFile
DMABuffer
NetworkPacket
RingBuffer
ECSStorage
Tensor
```

chúng vẫn có thể dùng cùng:

```text
Ownership
Region
Capability
Effect
Send
Share
```

thay vì phải phát minh một memory model riêng cho từng framework.

### Bước tiếp theo tôi đề xuất

Sau Collection API, phần đáng chốt tiếp theo không phải GUI/network hay stdlib lớn, mà là **"Axiom Trait & Generic System v0.1"** thật kỹ:

```text
trait
impl
generic
associated type
extension method
operator
static dispatch
dynamic dispatch
specialization
monomorphization
type inference
coherence/orphan rule
method resolution
```

Đây là phần quyết định liệu ý tưởng **"struct + function + trait, không class"** có thực sự đủ mạnh để thay thế inheritance/virtual method hay không.