Tiếp tục. Bây giờ ta thiết kế **Axiom Standard Library Architecture v0.1**. Đây là phần rất quan trọng vì đây là nơi kiểm chứng xem memory model `ownership + view/mut_view + Drop` có thực sự **dễ dùng hơn Rust mà vẫn giữ hiệu năng hệ thống** hay không.

# XXXII — Axiom Standard Library Architecture v0.1

## 1. Nguyên tắc lớn

Stdlib Axiom **không phải runtime khổng lồ**.

Ta chia thành 4 tầng:

```text
Axiom Program
      │
      ▼
┌─────────────────────┐
│       std           │
├─────────────────────┤
│ collections / io    │
│ text / fs / net     │
│ async / sync        │
├─────────────────────┤
│       core          │
├─────────────────────┤
│ compiler intrinsics │
├─────────────────────┤
│       target        │
└─────────────────────┘
```

Quan trọng:

```text
core != runtime
std  != runtime
```

Một chương trình nhỏ:

```axiom
fn main() {
    let x = 10
}
```

không được tự động kéo theo:

```text
allocator
thread runtime
async runtime
network
reflection
GC
```

---

# 2. `core`

`core` phải cực kỳ nhỏ và gần compiler.

Nó chứa các abstraction nền tảng mà gần như mọi chương trình cần.

```text
core/
├── primitive
├── option
├── result
├── array
├── view
├── range
├── tuple
├── numeric
├── memory
├── ptr
├── option
├── result
├── drop
├── copy
├── clone
├── iterator
└── marker
```

Không chứa:

```text
File
Socket
Thread
Mutex
HTTP
JSON
GUI
```

---

# 3. Primitive types

Primitive types là language types:

```text
bool

i8  i16  i32  i64
u8  u16  u32  u64

isize
usize

f32
f64

unit
never
```

Stdlib chỉ cung cấp methods/functions.

Ví dụ:

```axiom
let x: i32 = 42
let y = x.abs()
```

`i32` không phải class.

Đây tiếp tục giữ nguyên triết lý:

> **Data và behavior tách biệt.**

---

# 4. `Option<T>`

Không có `null`.

```axiom
enum Option<T> {
    None,
    Some(T),
}
```

Sử dụng:

```axiom
fn find(id: u64) -> Option<User> {
    ...
}
```

Pattern:

```axiom
match find(id) {
    Option.Some(user) => use_user(user),
    Option.None => not_found(),
}
```

Có thể có syntax sugar sau này, nhưng v0.1 giữ semantics rõ ràng.

---

# 5. `Result<T, E>`

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Ví dụ:

```axiom
fn load(path: view<Text>) -> Result<Data, Error> {
    ...
}
```

Và:

```axiom
fn run(path: view<Text>) -> Result<(), Error> {
    let data = load(path)?
    process(data)
    Ok(())
}
```

`?` vẫn chỉ là control-flow lowering.

Không có exception runtime.

---

# 6. `Copy`

`Copy` nên là compiler-known trait.

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Compiler có thể xác định:

```text
Vec2 : Copy
```

nếu mọi thành phần phù hợp.

Khi:

```axiom
let a = Vec2 { x: 1, y: 2 }
let b = a
```

`a` vẫn hợp lệ.

Ngược lại:

```axiom
let a = String(...)
let b = a
```

là Move.

Không cần:

```text
&Vec2
&&Vec2
'a
```

---

# 7. `Clone`

Đây là điểm rất quan trọng.

`Copy`:

```text
cheap semantic duplication
```

`Clone`:

```text
explicit potentially-expensive duplication
```

Ví dụ:

```axiom
let a = large_string
let b = a.clone()
```

Compiler không được biến `clone()` thành implicit copy.

---

# 8. `Drop`

Stdlib định nghĩa semantic trait/mechanism:

```text
Drop
```

nhưng programmer không phải viết destructor cho mọi struct.

Ví dụ resource:

```axiom
struct File {
    ...
}
```

khi scope kết thúc:

```text
Drop(File)
```

được compiler elaboration.

Nhưng:

```text
Drop != free()
```

File có thể:

```text
close OS handle
release descriptor
release lock
```

trong khi memory chứa object có thể được arena/compiler quản lý khác.

---

# 9. `view<T>`

Đây sẽ là một trong những điểm đặc trưng nhất của Axiom.

Ví dụ:

```axiom
fn print_name(name: view<Text>) {
    ...
}
```

Người dùng gọi:

```axiom
let name = get_name()
print_name(name)
```

Không cần:

```text
&name
```

Compiler tự tạo **ephemeral read capability**.

---

# 10. Persistent view

Nếu muốn giữ view:

```axiom
let name_view = view(name)
```

Đây là explicit.

Ví dụ:

```axiom
let name = String("Axiom")
let v = view(name)

print(v)
```

Compiler đảm bảo:

```text
name lifetime >= v lifetime
```

---

# 11. `mut_view<T>`

Ví dụ:

```axiom
fn sort(data: mut_view<i32>) {
    ...
}
```

gọi:

```axiom
sort(values)
```

Compiler tạo mutable capability tạm thời.

Không cần:

```text
&mut values
```

Nhưng nếu giữ lại:

```axiom
let v = mut_view(values)
```

thì capability trở thành explicit và move-only.

---

# 12. API sẽ rất gọn

Rust-style conceptually:

```text
fn process(data: &[Item])
fn modify(data: &mut [Item])
```

Axiom:

```axiom
fn process(data: view<Item>)
fn modify(data: mut_view<Item>)
```

Và call:

```axiom
process(items)
modify(items)
```

Đây là sự khác biệt lớn:

> **Ownership tồn tại trong compiler; syntax ownership không chiếm phần lớn code của programmer.**

---

# 13. Array

Array cố định:

```axiom
Array<T, N>
```

Ví dụ:

```axiom
let a: Array<i32, 4> = [1, 2, 3, 4]
```

Inline/value semantic.

Không heap.

---

# 14. Slice

Slice không phải owner.

Semantic:

```text
view<T>
```

đại diện cho contiguous region.

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32 {
    ...
}
```

Array:

```axiom
let a = [1, 2, 3, 4]
sum(a)
```

Compiler tạo view ephemeral.

---

# 15. Range

Range nên là lightweight value.

```axiom
1..10
1..=10
..10
1..
..
```

Các loại:

```text
Range
RangeInclusive
RangeFrom
RangeTo
RangeFull
```

Có thể là ZST/struct nhỏ tùy loại.

---

# 16. Iterator

Iterator là abstraction compile-time/runtime-erased tùy optimization.

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Ví dụ:

```axiom
for x in values {
    process(x)
}
```

Có thể lower thành iterator loop.

Nhưng optimizer có thể biến thành:

```text
raw indexed loop
```

nếu semantics tương đương.

Không có mandatory iterator object.

---

# 17. `Vec<T>`

`Vec<T>` là dynamic contiguous collection.

Semantic state:

```text
storage identity
length
capacity
element type
```

Không expose representation.

API:

```axiom
let v = Vec<i32>()
v.push(10)
v.push(20)
```

Không:

```text
new Vec()
```

không:

```text
delete v
```

---

# 18. Vec relocation

Ví dụ:

```axiom
let v = Vec<i32>()
v.push(1)

let x = view(v)

v.push(2)
```

Nếu `push` có thể realloc và `x` còn sống, compiler phải xử lý theo semantic rules.

Không được silently invalidate `x`.

Có thể:

```text
AX_VIEW_0004
```

nếu relocation có khả năng xảy ra.

Hoặc API/compiler có thể shorten capability lifetime nếu chứng minh `x` không còn được sử dụng.

Đây là nơi compiler analysis giúp programmer.

---

# 19. Một ví dụ rất quan trọng

```axiom
let v = Vec<i32>()

v.push(1)
v.push(2)

print(view(v))

v.push(3)
```

Không có vấn đề.

Vì view tạm kết thúc sau call:

```text
view(v)
   │
   └── print()
        │
        ▼
     capability dead
```

Sau đó `push()` có thể relocate.

Programmer không phải suy nghĩ về lifetime annotation.

---

# 20. String

Tách:

```text
Text
Bytes
```

Không dùng một `String` vừa là UTF-8 vừa là byte array.

### `Text`

Unicode text.

### `Bytes`

raw bytes.

Ví dụ:

```axiom
let text: Text = "Xin chào"
let data: Bytes = b"ABC"
```

---

# 21. Text representation

Không nên freeze implementation:

```text
UTF-8
```

vào type semantics nếu chưa cần.

Semantic contract:

```text
Text = valid Unicode scalar sequence
```

Representation có thể UTF-8/UTF-16/UTF-32/optimized internal representation.

Nhưng FFI conversion phải explicit.

---

# 22. C string

Không cho:

```axiom
Text -> *u8
```

implicit.

Std:

```text
CString
CStrView
```

hoặc tương đương.

Ví dụ:

```axiom
extern "C" fn puts(s: CStrView)
```

Conversion explicit.

Điều này bảo vệ ABI boundary.

---

# 23. `Box<T>`

`Box<T>`:

```text
owned dynamic storage
```

không phải:

```text
"always heap"
```

Ví dụ:

```axiom
let x = Box(value)
```

Semantically có dynamic storage identity.

Nhưng optimizer có thể eliminate allocation nếu:

```text
address not observable
```

---

# 24. `Box<T>` và stable address

Nếu:

```axiom
let p = address_of(x)
```

hoặc truyền pointer ra external code:

```text
address becomes observable
```

thì compiler phải giữ storage contract cần thiết.

Đây là điểm cực kỳ quan trọng để không biến `Box` thành abstraction giả.

---

# 25. HashMap

Stdlib:

```text
HashMap<K, V>
```

nhưng allocator không nằm trong generic API mặc định.

Không:

```text
HashMap<K, V, Allocator>
```

trừ khi programmer thực sự cần custom allocator.

Mặc định:

```axiom
let map = HashMap<String, User>()
```

Custom allocator:

```text
HashMap.with_allocator(...)
```

hoặc API storage policy tương đương.

---

# 26. Allocator abstraction

Allocator thuộc library/system layer.

```text
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
}
```

Nhưng không đưa allocator parameter vào mọi collection.

Nếu không:

```text
Vec<T, A>
HashMap<K,V,A>
String<A>
Box<T,A>
...
```

sẽ lan toàn bộ type system.

Axiom giữ:

> **Advanced control should be opt-in, not viral.**

---

# 27. Memory module

`core.memory`:

```text
size_of<T>()
align_of<T>()
```

và low-level operations:

```text
read
write
copy
move
swap
```

Một phần có thể là compiler intrinsic.

Unsafe operations được đánh dấu.

---

# 28. Pointer module

```text
*const T
*mut T
```

không thuộc API thường dùng.

`core.ptr` cung cấp:

```text
ptr.cast()
ptr.offset()
ptr.read()
ptr.write()
ptr.add()
```

nhưng unsafe.

Programmer application bình thường gần như không cần sử dụng.

---

# 29. Standard synchronization

Platform layer:

```text
std.sync
├── Mutex
├── RwLock
├── Condvar
├── Barrier
├── Once
└── Atomic
```

`MutexGuard`:

```text
!Copy
Drop → unlock
```

và:

```text
read guard → view<T>
write guard → mut_view<T>
```

Compiler biết ownership/capability semantics nhưng synchronization vẫn là library abstraction.

---

# 30. Channels

```axiom
let (tx, rx) = channel<Message>()
```

Send:

```axiom
tx.send(message)
```

Ownership chuyển sang channel.

Receive:

```axiom
let message = rx.receive()?
```

Không copy nếu `Message` non-Copy.

Đây là cách Axiom biến ownership thành công cụ hữu ích mà không cần pointer syntax.

---

# 31. Threads

```axiom
spawn(|| {
    work()
})
```

Compiler kiểm tra:

```text
captured state : Send
```

Nếu shared:

```text
Arc<T>
```

và:

```text
T : Share
```

Không có:

```text
'static
```

trong source language.

Compiler tự phân tích escape.

---

# 32. Async

Stdlib:

```text
std.async
├── Future
├── Waker
├── Task
├── Executor
├── JoinHandle
└── Cancellation
```

Core language chỉ biết:

```text
async
await
```

Executor không thuộc Core.

Do đó:

```axiom
async fn foo() { ... }
```

không tự kéo runtime.

---

# 33. File I/O

```text
std.fs
├── File
├── Path
├── Directory
├── Metadata
└── Permissions
```

Ví dụ:

```axiom
fn load(path: view<Path>) -> Result<Bytes, IoError> {
    let file = File.open(path)?
    file.read_all()
}
```

`File` Drop sẽ release OS handle.

---

# 34. Networking

```text
std.net
├── TcpStream
├── TcpListener
├── UdpSocket
├── IpAddress
└── DNS
```

Nhưng networking không được link vào binary nếu không dùng.

Đây là:

```text
capability-driven linking
```

theo dependency graph.

---

# 35. Time

```text
std.time
├── Duration
├── Instant
├── SystemTime
├── Date
└── Clock
```

Tách:

```text
Instant
```

và:

```text
WallClock/SystemTime
```

để tránh dùng timestamp hệ thống làm monotonic timer.

---

# 36. Process

```text
std.process
├── Process
├── Command
├── ExitCode
└── Environment
```

Nhưng OS-specific details nằm:

```text
std.platform.*
```

không nằm Core.

---

# 37. Platform layer

Cấu trúc:

```text
std/
├── core/
├── collections/
├── text/
├── io/
├── fs/
├── net/
├── process/
├── thread/
├── sync/
├── async/
├── time/
├── random/
├── crypto/
├── math/
├── simd/
├── gpu/
└── platform/
    ├── linux/
    ├── windows/
    ├── macos/
    ├── ios/
    └── android/
```

---

# 38. Không để OS API leak vào Core

Core không biết:

```text
Linux fd
Windows HANDLE
Mach port
Android asset
```

Chúng thuộc platform implementation.

---

# 39. SIMD

Không nên tạo:

```text
Vector128<T>
Vector256<T>
```

và ép programmer dùng chúng cho mọi numeric code.

Thay vào đó:

```text
std.simd
```

cho explicit SIMD.

Compiler auto-vectorization vẫn hoạt động độc lập.

---

# 40. Math

```text
std.math
```

gồm:

```text
sqrt
sin
cos
tan
exp
log
pow
min
max
clamp
```

Numeric operations có thể map trực tiếp target instruction/libcall.

Không nhất thiết runtime.

---

# 41. Random

Tách rõ:

```text
PRNG
CSPRNG
OS entropy
```

Không có global mutable RNG singleton.

Ví dụ:

```axiom
let rng = Random.new(seed)
let x = rng.next_u64()
```

State ownership rõ ràng.

---

# 42. Crypto

Không đặt cryptography vào Core.

```text
std.crypto
```

và có thể sau này:

```text
crypto-hash
crypto-tls
crypto-ed25519
```

thành package riêng.

Stdlib không nên trở thành một monolith.

---

# 43. Package layering

Tôi đề xuất cuối cùng:

```text
axiom-core
     │
     ├── collections
     ├── text
     ├── io
     ├── math
     │
     ├── fs
     ├── net
     ├── process
     ├── thread
     ├── sync
     ├── async
     │
     └── optional packages
          ├── crypto
          ├── json
          ├── http
          ├── image
          ├── gui
          └── gpu
```

Không phải mọi thứ đều phải nằm trong một `std`.

---

# 44. Một nguyên tắc rất quan trọng: API không được expose implementation

Ví dụ không nên:

```axiom
struct Vec<T> {
    ptr: *mut T
    len: usize
    cap: usize
}
```

làm public semantic definition.

Nên:

```axiom
struct Vec<T> {
    ...
}
```

với private fields.

Compiler/library có thể thay đổi:

```text
ptr/len/cap
```

thành representation khác mà không phá API.

---

# 45. Nhưng low-level programmer vẫn lấy được representation

System code có thể yêu cầu:

```text
unsafe
@repr(...)
raw pointer
address
```

Tức là:

```text
High-level API
       ↓
safe abstraction
       ↓
unsafe boundary
       ↓
machine representation
```

Không phải:

```text
high-level API = abstraction prison
```

---

# 46. Stdlib phải dogfood Axiom

Đây là yêu cầu bootstrap quan trọng.

Không nên có:

```text
90% stdlib viết C
```

rồi gọi nó là Axiom standard library.

Cuối cùng:

```text
core      → Axiom + compiler intrinsics
collections → Axiom
text      → Axiom
fs        → Axiom + tiny platform unsafe layer
net       → Axiom + platform layer
thread    → Axiom + OS primitives
```

Unsafe chỉ tập trung ở biên.

---

# 47. Cấu trúc source

Ví dụ:

```text
std/core/
├── option.ax
├── result.ax
├── array.ax
├── view.ax
├── range.ax
├── iterator.ax
├── copy.ax
├── clone.ax
├── drop.ax
├── memory.ax
└── ptr.ax
```

Collections:

```text
std/collections/
├── vec.ax
├── deque.ax
├── list.ax
├── hashmap.ax
├── hashset.ax
├── btree_map.ax
└── btree_set.ax
```

---

# 48. API design rule

Mọi API public phải ưu tiên:

```text
value
view<T>
mut_view<T>
```

trước:

```text
raw pointer
```

Ví dụ **không**:

```axiom
fn memcpy(dst: *mut u8, src: *const u8, n: usize)
```

ở API application.

Có thể có:

```text
core.memory.copy
```

ở unsafe/system layer.

API cấp cao:

```axiom
fn copy(dst: mut_view<u8>, src: view<u8>)
```

Compiler kiểm tra alias/lifetime.

---

# 49. Điều này tạo ra một phong cách code rất khác

Axiom:

```axiom
fn transform(input: view<f32>, output: mut_view<f32>) {
    for i in 0..input.len() {
        output[i] = input[i] * 2.0
    }
}
```

Nếu compiler chứng minh:

```text
input != output
```

thì có thể vectorize.

Nếu không chứng minh được non-overlap, API có thể yêu cầu abstraction phù hợp hoặc reject mutable conflict.

Không cần programmer viết:

```text
restrict
```

---

# 50. Đây là điểm tôi muốn freeze

### Axiom Stdlib API hierarchy

```text
Level 0
value

Level 1
view<T>

Level 2
mut_view<T>

Level 3
owned types
Vec / String / Box / File / ...

Level 4
shared abstractions
Rc / Arc / Mutex / Channel / ...

Level 5
raw pointers / machine representation
unsafe
```

**90% application code nên sống ở Level 0–3.**

Nếu programmer thường xuyên phải xuống Level 5 thì API stdlib đang thiết kế sai.

---

# 51. Core v0.1 nên nhỏ đến đâu?

Tôi đề xuất **không cố đo bằng số dòng**, mà bằng dependency rule:

```text
core
 ├── no OS
 ├── no filesystem
 ├── no networking
 ├── no threads
 ├── no async executor
 ├── no allocator requirement
 ├── no dynamic linker
 └── no mandatory runtime
```

Một freestanding program có thể chỉ dùng:

```text
core
+
compiler intrinsics
```

và tạo binary rất nhỏ.

---

# 52. Standard Library Invariants

Ta thêm nhóm:

```text
ASTD-20  Core has no mandatory runtime
ASTD-21  Core has no OS dependency
ASTD-22  Core has no mandatory allocator
ASTD-23  Core has no mandatory threading
ASTD-24  Core has no mandatory async executor
ASTD-25  Std APIs preserve ownership semantics
ASTD-26  Borrow/lifetime syntax is not required
ASTD-27  View APIs preserve capability validity
ASTD-28  Mutable views cannot create unsafe aliasing
ASTD-29  Collections do not expose representation by default
ASTD-30  Allocator parameters are not viral
ASTD-31  Resource types use deterministic Drop
ASTD-32  Drop does not propagate recoverable errors
ASTD-33  Text and Bytes are distinct
ASTD-34  Raw pointers are not normal collection APIs
ASTD-35  Optional components are not linked unless required
ASTD-36  Platform APIs stay outside Core
ASTD-37  Std abstractions are optimization-transparent
ASTD-38  Safe APIs do not depend on physical storage location
ASTD-39  FFI representation is explicit
ASTD-40  Stdlib can be implemented in Axiom
ASTD-41  Unsafe is concentrated at system boundaries
ASTD-42  API changes cannot silently alter Core semantics
```

---

# 53. Milestone STD-001

Không viết toàn bộ stdlib ngay.

Vertical slice đầu tiên:

```text
core
 ├── bool
 ├── integers
 ├── unit
 ├── Option
 ├── Result
 ├── Array
 ├── view
 ├── mut_view
 ├── Copy
 ├── Clone
 └── Drop
```

Test:

```axiom
fn first(a: view<i32>) -> Option<i32> {
    if a.len() == 0 {
        Option.None
    } else {
        Option.Some(a[0])
    }
}
```

Sau đó:

```text
Vec
String
Bytes
Iterator
```

rồi mới:

```text
File
Thread
Async
Network
```

---

# 54. Nhưng trước khi viết Stdlib, còn một lớp cần khóa

Có một vấn đề nền tảng chưa nên bỏ qua:

**Axiom Memory Model đã định nghĩa semantics, nhưng chưa thiết kế đầy đủ "intrinsics + primitive operations + compiler-known types".**

Ví dụ:

```text
size_of<T>()
align_of<T>()
drop()
copy()
move()
view()
mut_view()
address_of()
bit_cast()
atomic operations
```

đang nằm rải rác giữa:

```text
language
compiler intrinsic
core
unsafe
std
```

Nếu không tách rõ, sau này compiler và stdlib sẽ bị circular dependency.

Vì vậy bước tiếp theo hợp lý nhất là:

# XXXIII — Axiom Core Intrinsics & Primitive Semantic Layer

Ta sẽ đóng băng chính xác:

```text
Language Primitive
       ↓
Compiler Intrinsic
       ↓
core
       ↓
std
```

và xác định **những thứ nào thực sự là ngôn ngữ, những thứ nào chỉ là compiler intrinsic, những thứ nào hoàn toàn có thể viết bằng Axiom**.

Đây cũng là bước cuối cùng trước khi có thể bắt đầu **implement compiler + core library bằng chính Axiom**, thay vì tiếp tục mở rộng thiết kế.