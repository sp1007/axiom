Tiếp tục. Tôi sẽ đi vào **Data Model & Standard Types v0.1**, nhưng có một điều nên chốt trước:

> Axiom không nên có một “siêu type container” duy nhất.  
> Mỗi type nên có một mục đích memory/ownership rõ ràng.

Đặc biệt, tôi muốn tránh việc `String`, `Vec`, `Buffer`, `Box`, `Shared` cuối cùng đều chỉ là các wrapper khác nhau quanh `heap pointer`.

# AXIOM DATA MODEL & STANDARD TYPES v0.1

## 1. Phân tầng type

Axiom nên chia type thành 4 tầng:

```text
┌─────────────────────────────────────┐
│           LANGUAGE PRIMITIVES       │
│ bool integer float tuple array enum │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│           CORE SEMANTIC TYPES       │
│ Option Result view mut_view fn      │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│             DATA TYPES              │
│ Vec String Bytes Box Shared Map ... │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│          DOMAIN LIBRARIES            │
│ File Net HTTP GUI GPU Game ...      │
└─────────────────────────────────────┘
```

Điểm quan trọng:

**`Vec`, `String`, `Map` không phải language primitives.**

---

# 2. Primitive types

Giữ bộ cơ bản:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

Sau này:

```text
i128
u128
```

nếu backend và ABI hoàn thiện.

Không đưa hàng chục integer type vào core.

---

# 3. Tuple

```axiom
let p = (10, 20)
```

Type:

```text
(i32, i32)
```

Access:

```axiom
p.0
p.1
```

Tuple là value type.

Compiler có thể hoàn toàn scalarize:

```text
p.0 → register A
p.1 → register B
```

Không allocation.

---

# 4. Array

```axiom
let a = [10, 20, 30, 40]
```

Type:

```text
Array<i32, 4>
```

Semantic:

```text
4 × i32
```

Không pointer bắt buộc.

Không heap.

Không object header.

---

# 5. `view<T>`

Đây là một trong những type nền tảng nhất.

```axiom
fn sum(values: view<i32>) -> i32
```

Conceptual representation:

```text
view<T>
┌────────────┐
│ address    │
├────────────┤
│ length     │
└────────────┘
```

Nhưng semantic:

```text
READ access
non-owning
bounded
lifetime checked
```

---

# 6. `mut_view<T>`

```axiom
fn fill(values: mut_view<i32>, x: i32)
```

Conceptual:

```text
address
length
WRITE capability
```

Compiler đảm bảo không có xung đột access safe.

---

# 7. View không nhất thiết phải là contiguous array

Ở v0.1 tôi khuyến nghị:

> `view<T>` chỉ đại diện contiguous memory.

Đừng biến nó thành iterator abstraction.

Nếu cần lazy sequence:

```text
Iterator<T>
```

là type khác.

Điều này giúp compiler reasoning rất dễ:

```text
view<T>
    =
contiguous T[0..N]
```

---

# 8. `Option<T>`

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Đây là semantic nullable/optional type.

```axiom
let result = map.get(key)

match result {
    Some(value) => use(value)
    None => ...
}
```

Không có implicit null.

---

# 9. Niche optimization

Compiler được phép biến:

```text
Option<NonNullPointer>
```

thành:

```text
same physical size as pointer
```

Ví dụ:

```text
pointer
0 → None
nonzero → Some
```

Nhưng programmer không được phụ thuộc vào representation trừ khi `repr` explicit.

---

# 10. `Result<T,E>`

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Đây là error mechanism chuẩn.

Ví dụ:

```axiom
fn read_file(path: Text) -> Result<Bytes, IOError>
```

Không exception.

---

# 11. `?`

```axiom
let file = open(path)?
let data = file.read()?
```

Compiler hạ thành control flow.

Conceptually:

```text
match open(path) {
    Ok(x) => continue
    Err(e) => return Err(e)
}
```

Không exception machinery.

---

# 12. `Box<T>`

`Box` là abstraction cho:

> một owning value có storage dynamic, single owner.

Ví dụ:

```axiom
let node = Box.new(Node(...))
```

Semantics:

```text
owner
  │
  ▼
┌──────────────┐
│ dynamic T    │
└──────────────┘
```

Khi owner chết:

```text
Drop(T)
↓
release storage
```

---

# 13. Nhưng `Box<T>` phải là library type

Compiler chỉ cần hiểu những semantic property:

```text
Box<T>
    Move
    Drop
```

Không cần language primitive:

```text
NEW
DELETE
```

Điều này giữ core sạch.

---

# 14. `Box<T>` không nên tự động optimize thành stack nếu semantics expose address

Đây là nuance quan trọng.

Nếu:

```axiom
let x = Box.new(value)
```

và API không expose stable address/lifetime requirement, compiler có thể optimize.

Nhưng nếu programmer sử dụng:

```text
raw pointer
FFI
stable address
```

thì dynamic storage đã trở thành observable.

Khi đó compiler phải giữ semantics tương ứng.

---

# 15. `Vec<T>`

Đây mới là container quan trọng nhất.

Conceptual representation:

```text
Vec<T>
┌──────────────┐
│ pointer      │
│ length       │
│ capacity     │
└──────────────┘
```

Backing storage:

```text
heap / arena / custom allocator
```

Không object header.

---

# 16. `Vec<T>` ownership

```axiom
let a = Vec<i32>()
a.push(10)

let b = a
```

Nếu `Vec<T>` non-Copy:

```text
a ──MOVE──► b
```

Không copy elements.

`a` trở thành moved.

---

# 17. Passing Vec

```axiom
fn process(data: Vec<u8>)
```

caller:

```axiom
process(data)
```

ownership chuyển sang `process`.

Không cần:

```text
move(data)
```

trong trường hợp bình thường.

---

# 18. Read Vec

```axiom
fn inspect(data: view<u8>)
```

gọi:

```axiom
inspect(data)
```

Compiler tạo view.

Không copy.

---

# 19. Mutable Vec

```axiom
fn modify(data: mut_view<u8>)
```

Compiler có thể tạo mutable view từ Vec trong phạm vi an toàn.

Nhưng cần một rule rất quan trọng:

> Không được giữ `mut_view` vượt qua một operation có thể làm thay đổi allocation của Vec.

Ví dụ:

```axiom
let v = view(vec)

vec.push(10)

use(v)
```

nếu `push` có thể reallocate thì `v` sẽ dangling.

Compiler phải reject hoặc kết thúc view trước mutation.

Đây chính là nơi ownership/view model của Axiom phát huy tác dụng.

---

# 20. `Vec<T>` và reallocation

```text
capacity = 8
length = 8

push()
   ↓
need capacity
   ↓
allocate new storage
   ↓
move elements
   ↓
release old storage
```

Compiler biết lifetime của views nên không cho phép stale view tồn tại.

Không cần reference-count từng view.

---

# 21. `Buffer<T>`

Tôi nghĩ nên **tách `Buffer<T>` khỏi `Vec<T>`**.

### `Vec<T>`

Data structure:

```text
growable sequence
```

### `Buffer<T>`

Memory abstraction:

```text
owned contiguous storage
```

Ví dụ:

```axiom
let buffer = Buffer.allocate<u8>(4096)
```

Nó không nhất thiết có logical element semantics giống Vec.

Có thể dùng cho:

- file I/O
- network
- GPU
- serialization
- SIMD
- FFI
- raw binary data.

---

# 22. Buffer có thể dùng uninitialized storage

Systems programming cần điều này.

Conceptually:

```text
Buffer<u8>
capacity = 4096
initialized = 0..N
```

Nhưng safe API không được cho đọc vùng chưa initialize.

Có thể có API:

```axiom
buffer.write_region(...)
```

hoặc `init` semantics rõ ràng.

Unsafe layer có thể truy cập raw storage.

---

# 23. `Bytes`

`Bytes` nên là một abstraction thiên về immutable byte sequence.

Ví dụ:

```axiom
let data: Bytes
```

Có thể internally:

```text
shared immutable buffer
```

nhưng **không bắt buộc**.

API:

```text
Bytes
    → view<u8>
```

zero-copy.

---

# 24. `Text` và `String`

Tôi muốn phân biệt:

### `String`

Owning mutable/growable text.

### `Text`

Immutable text value/sequence abstraction.

### `TextView`

Non-owning view.

Ví dụ:

```axiom
fn print(text: view<char>)
```

hoặc nếu Unicode semantics phức tạp:

```axiom
fn print(text: TextView)
```

Tôi nghiêng về **không biến Unicode code point thành `char` primitive** ở v0.1.

---

# 25. Unicode phải được thiết kế riêng

Đây là chỗ rất dễ thiết kế sai.

Một “ký tự” có thể là:

```text
byte
UTF-8 code unit
Unicode scalar value
grapheme cluster
```

Không nên có:

```text
char = magically one character
```

Axiom core chỉ cần:

```text
u8
```

String/Text semantics nằm standard library.

---

# 26. UTF-8

Tôi nghiêng về:

> `String` dùng UTF-8 mặc định.

Lợi ích:

- tương thích web/Linux
- ASCII zero overhead
- compact
- FFI thuận tiện
- dễ streaming.

Nhưng indexing:

```axiom
text[i]
```

không nên mặc định có nghĩa “Unicode character”.

Có thể yêu cầu:

```text
bytes()
codepoints()
graphemes()
```

---

# 27. `Shared<T>`

Đây là abstraction quan trọng nhưng **không phải default**.

Concept:

```text
Shared<T>
     │
     ▼
shared ownership
```

Nếu single-thread:

```text
Rc<T>
```

Nếu cross-thread:

```text
Arc<T>
```

Tôi khuyên standard library ban đầu chỉ cần:

```text
Shared<T>
```

và sau đó specialization:

```text
Rc<T>
Arc<T>
```

nếu implementation cần phân biệt.

---

# 28. Shared immutable vs shared mutable

```axiom
let x = Arc.create(data)
```

nhiều thread có thể:

```text
READ
READ
READ
```

Nhưng:

```text
WRITE
```

không tự nhiên được phép.

Muốn mutable shared:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

Đây là composition.

Không có:

```text
shared mutable object
```

magic.

---

# 29. `Weak<T>`

Nếu có reference counting:

```text
Arc<T>
Weak<T>
```

là cần thiết để phá cycle.

Nhưng `Weak<T>` không giữ ownership của T.

---

# 30. Map

Không nên hard-code một map implementation.

Standard library:

```text
Map<K,V>
```

có thể là interface/trait abstraction.

Implementations:

```text
HashMap
BTreeMap
FlatMap
OrderedMap
```

Programmer chọn theo workload.

---

# 31. Set

Tương tự:

```text
Set<T>
```

có implementations:

```text
HashSet
TreeSet
BitSet
```

Không cần compiler magic.

---

# 32. Iterator

Iterator nên là trait:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Sau đó:

```axiom
for x in collection {
    process(x)
}
```

lower thành iterator protocol.

Nhưng compiler có thể recognize common patterns và optimize.

---

# 33. Iterator không được biến thành allocation machine

Đây là mục tiêu quan trọng.

```axiom
let result =
    values
        .filter(...)
        .map(...)
        .sum()
```

Không được mặc định tạo:

```text
iterator object
heap allocation
temporary arrays
```

Compiler nên có khả năng:

```text
pipeline
 ↓
specialize
 ↓
inline
 ↓
fuse
 ↓
single loop
```

Ví dụ cuối cùng:

```text
for (...)
    if predicate(...)
        sum += transform(...)
```

Đây chính là **zero-cost abstraction**.

---

# 34. Closure

Closure:

```axiom
let f = |x| x * 2
```

semantic representation:

```text
Closure<F>
┌─────────────────┐
│ captured values │
├─────────────────┤
│ call function   │
└─────────────────┘
```

Nếu non-escaping:

```text
closure object
    ↓
eliminated
```

Nếu escape:

```text
closure environment
```

có thể nằm stack/heap tùy analysis.

---

# 35. Function pointer

Function pointer khác closure.

```text
fn(i32) -> i32
```

không có capture.

Physical representation thường chỉ:

```text
code address
```

Closure có thể:

```text
data + code
```

Không được nhập hai khái niệm thành một.

---

# 36. `dyn Fn` / dynamic callable

Không cần vội đưa vào Core.

Static generic:

```axiom
fn apply<F: Callable>(f: F)
```

là default.

Dynamic callable chỉ khi programmer explicit type erasure.

---

# 37. Atomic types

Atomic nên là standard types:

```text
AtomicBool
AtomicI32
AtomicI64
AtomicUsize
```

Không nên có:

```text
atomic int
```

một loại primitive riêng.

Semantics:

```text
load(order)
store(value, order)
swap(...)
compare_exchange(...)
fetch_add(...)
```

---

# 38. Synchronization

Library:

```text
Mutex<T>
RwLock<T>
Semaphore
CondVar
Channel<T>
```

Không cần compiler primitives ngoại trừ MIR/internal semantics để optimizer hiểu synchronization.

---

# 39. Channel

Channel là cách rất phù hợp với ownership model.

```axiom
let (tx, rx) = channel<Data>()

tx.send(data)
```

`data` được MOVE.

Receiver nhận ownership.

Không cần shared mutable memory.

Đây có thể là một trong những API concurrency quan trọng nhất của Axiom.

---

# 40. Type property matrix

Tôi đề xuất standard types có semantic properties như sau:

| Type | Copy | Drop | Ownership | Dynamic storage |
|---|---:|---:|---|---|
| `i32` | ✓ | — | value | — |
| `Point` | ✓* | — | value | — |
| `Array<T,N>` | phụ thuộc T | phụ thuộc T | value | — |
| `view<T>` | ✓ | — | non-owning | — |
| `mut_view<T>` | compiler-controlled | — | non-owning | — |
| `Vec<T>` | ✗ | ✓ | owning | thường |
| `Buffer<T>` | ✗ | ✓ | owning | thường |
| `Box<T>` | ✗ | ✓ | owning | ✓ |
| `String` | ✗ | ✓ | owning | thường |
| `Bytes` | implementation | ✓/— | owning/shared | có thể |
| `Arc<T>` | ✓* | ✓ | shared | ✓ |
| `Option<T>` | phụ thuộc T | phụ thuộc T | composition | — |
| `Result<T,E>` | phụ thuộc | phụ thuộc | composition | — |

`*` nghĩa compiler derive nếu semantic conditions thỏa mãn.

---

# 41. Một nguyên tắc rất quan trọng

Không nên để:

```text
Copy = cheap
```

Copy chỉ có nghĩa:

> Copy không tạo thêm ownership obligation cần cleanup.

Một type 1 MB có thể `Copy` về semantic nếu language cho phép, dù việc copy vật lý rất tốn.

Do đó standard library nên cân nhắc cẩn thận việc derive `Copy`.

---

# 42. Một thay đổi nhỏ tôi khuyến nghị

Trong bảng trước đây ta có:

```text
Share
```

Tôi nghĩ cần phân biệt:

### `Share`

Semantic property:

> Value có thể được immutable-share.

### `Send`

Semantic property:

> Ownership có thể transfer sang execution context khác.

Không nên coi `Share` là “thread-safe”.

Ví dụ một immutable type có thể:

```text
Share = true
Send = true
```

nhưng một type chỉ local:

```text
Share = true
Send = false
```

nếu chứa execution-context-bound resource.

---

# 43. Type property không phải trait bình thường

Đừng viết:

```axiom
trait Copy
trait Send
trait Share
```

theo cùng cơ chế với:

```text
Drawable
Iterator
Serialize
```

Compiler phải hiểu chúng ở semantic level.

Nếu không, người dùng có thể tạo:

```text
fake Send
fake Copy
```

và phá memory model.

---

# 44. Data Model tổng thể

Sau các quyết định trên, Axiom có một cấu trúc khá sạch:

```text
                         TYPE
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       VALUE            VIEW             FUNCTION
          │                │                │
   ┌──────┼──────┐      ┌──┴──┐         ┌───┴────┐
   ▼      ▼      ▼      ▼     ▼         ▼        ▼
 scalar  struct enum   view mut_view   fn       closure
   │
   ├── tuple
   ├── array
   ├── Option
   └── Result

LIBRARY DATA TYPES
   │
   ├── Vec
   ├── Buffer
   ├── String
   ├── Bytes
   ├── Box
   ├── Shared
   ├── Map
   └── Set
```

---

# 45. Điều quan trọng nhất: không để standard library phá memory model

Ví dụ không nên thiết kế:

```text
String → hidden GC
Vec → hidden RC
Map → hidden runtime
Closure → mandatory heap
```

Thay vào đó:

```text
String
  ↓
explicit ownership

Vec
  ↓
explicit ownership

Arc
  ↓
explicit shared ownership

Closure
  ↓
compiler-managed capture

Map
  ↓
ordinary data structure
```

---

# 46. Axiom đang hình thành một triết lý khá rõ

Có thể tóm tắt bằng:

> **Own values, view data, compose capabilities, specialize behavior.**

Hay cụ thể hơn:

```text
OWN
    ↓
who is responsible?

VIEW
    ↓
who may access?

TRAIT
    ↓
what can it do?

PROPERTY
    ↓
what guarantees does it have?

ALLOCATOR
    ↓
where/how is storage obtained?

COMPILER
    ↓
can all of this be optimized away?
```

Đây là kiến trúc tôi nghĩ phù hợp hơn nhiều so với việc bắt programmer trực tiếp quản lý pointer/lifetime.

---

# 47. Và một quyết định lớn tiếp theo

Đến đây, Axiom đã có:

```text
✓ Syntax
✓ Type system
✓ Ownership
✓ View
✓ Concurrency
✓ Async
✓ Error semantics
✓ ABI
✓ Memory model
✓ Allocation model
✓ Fundamental data types
```

Bây giờ **không nên tiếp tục thêm feature ngẫu nhiên**.

Có một thứ cần làm trước khi đi xa hơn:

# AXIOM LANGUAGE FORMAL TEST SUITE v0.1

Tức biến toàn bộ thiết kế trên thành **hàng trăm semantic test cases**.

Ví dụ:

```text
ownership/
    move_basic.ax
    move_after_call.ax
    move_branch.ax
    move_loop.ax
    move_return.ax

views/
    view_basic.ax
    view_mut.ax
    view_escape.ax
    view_reallocation.ax
    overlapping_views.ax

memory/
    stack_promotion.ax
    allocation_elimination.ax
    drop_order.ax
    conditional_drop.ax

concurrency/
    send_basic.ax
    share_basic.ax
    race_rejected.ax
    channel_move.ax
    async_send.ax

types/
    copy.ax
    generic.ax
    trait_dispatch.ax
    option.ax
    result.ax

abi/
    repr_c.ax
    extern_c.ax
    aggregate_return.ax
```

Mỗi test phải có:

```text
SOURCE
EXPECTED TYPE STATE
EXPECTED OWNERSHIP STATE
EXPECTED MIR PROPERTY
EXPECTED ACCEPT/REJECT
EXPECTED DIAGNOSTIC ID
```

Đây là bước tôi đặc biệt khuyến nghị **trước khi tiếp tục thiết kế syntax/library thêm nữa**.

Bởi vì nếu 200–500 test này chạy được trên giấy, chúng ta sẽ phát hiện rất sớm những mâu thuẫn kiểu:

```text
Vec reallocation
        ×
view lifetime
        ×
move
        ×
async suspension
        ×
Send
        ×
Drop
```

thay vì phát hiện chúng sau khi đã viết hàng chục nghìn dòng compiler.

Và nó cũng tạo nền trực tiếp cho **AI agent xây compiler Axiom**: agent không phải “đoán ý định của spec”, mà phải làm cho compiler pass một semantic conformance suite cụ thể.