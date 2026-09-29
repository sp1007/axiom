Tiếp tục sang **AXIOM STORAGE & ALLOCATION MODEL v0.1**. Đây là phần rất quan trọng vì nó quyết định Axiom có thực sự đạt mục tiêu **hiệu năng C/C++ nhưng ít phiền phức hơn** hay không.

Tôi muốn điều chỉnh một quan niệm trước:

> **Không nên chọn “flat memory” làm allocator model.**  
> Axiom nên có **flat virtual address space ở machine level**, nhưng storage model phải là **multi-strategy + compiler-directed**.

---

# 1. Mục tiêu của Storage Model

Axiom cần đồng thời đạt:

```text
✓ Không bắt buộc GC
✓ Không bắt buộc reference counting
✓ Không bắt buộc heap
✓ Không bắt buộc programmer quản lý malloc/free
✓ Không có object header mặc định
✓ Không tạo pointer/reference bureaucracy
✓ Cho phép stack/register allocation
✓ Cho phép heap khi thực sự cần
✓ Cho phép arena/pool/slab
✓ Cho phép custom allocator
✓ Cho phép stable-address storage
✓ Cho phép raw memory/OS/DMA/GPU trong unsafe
✓ Compiler được tự do eliminate allocation
```

Tôi đề xuất nguyên tắc:

> **Storage location là implementation choice, trừ khi programmer chủ động biến nó thành observable semantic property.**

---

# 2. Tách 3 khái niệm

Axiom phải phân biệt:

```text
VALUE
STORAGE
ADDRESS
```

### Value

```text
x = Point(1, 2)
```

chỉ quan tâm:

```text
Point { x=1, y=2 }
```

### Storage

Có thể là:

```text
register
stack
inline
heap
arena
pool
static
external
```

### Address

Chỉ trở thành semantic khi programmer yêu cầu.

---

# 3. Ví dụ compiler freedom

```axiom id="7u6y0v"
fn distance(a: Point, b: Point) -> f32 {
    ...
}
```

Compiler có thể:

```text id="v8yd3y"
a → registers
b → registers
return → xmm register
```

Không có:

```text
stack object
heap object
pointer
```

Nếu programmer không quan tâm address, compiler không cần tạo address.

---

# 4. Storage Classes

Tôi đề xuất internal semantic storage classes:

```text id="3xg5me"
STATIC
THREAD_LOCAL
LOCAL
INLINE
DYNAMIC
EXTERNAL
```

Nhưng lưu ý:

> Đây là **compiler/internal classification**, không phải programmer bắt buộc chọn một trong sáu.

---

# 5. LOCAL

Giá trị tồn tại trong execution frame.

Ví dụ:

```axiom id="1t5j3j"
fn foo() {
    let p = Point(1, 2)
    ...
}
```

Có thể:

```text
register
stack
SSA value
```

Compiler tự chọn.

Không được giả định:

```text id="kgn6yn"
LOCAL = stack
```

---

# 6. INLINE

Đây là một concept tôi nghĩ rất hữu ích.

Ví dụ:

```axiom id="v0zly0"
struct SmallVec {
    data: Array<u8, 32>
    len: usize
}
```

Nếu object nằm trong một struct:

```axiom id="mnhy5a"
struct Packet {
    header: Header
    payload: SmallVec
}
```

`payload` có thể nằm **inline trong Packet**.

Không cần:

```text id="f7u9xz"
Packet
  ↓ pointer
SmallVec
  ↓ pointer
heap buffer
```

trừ khi semantics của type yêu cầu dynamic storage.

---

# 7. DYNAMIC

Dynamic storage là abstraction chứ không phải:

```text id="l4k4qg"
malloc/free
```

Ví dụ:

```axiom id="3ipwqg"
Box<T>
Vec<T>
String
Buffer<T>
```

đều có thể dùng dynamic storage.

Nhưng implementation có thể là:

```text id="js7rhk"
general heap
arena
pool
slab
custom allocator
OS mapping
```

---

# 8. Flat virtual address space

Ở machine level:

```text id="4d4shg"
Process virtual address space
──────────────────────────────────────
0x0000...
       │
       ├── code
       ├── readonly
       ├── static
       ├── thread-local
       ├── stack
       ├── mapped memory
       └── dynamic storage
```

Axiom có thể giả định:

```text id="u0h4it"
pointer = machine address
```

trong native targets.

Nhưng **language semantics không đồng nhất pointer với object identity**.

---

# 9. Tại sao không nên dùng “flat memory model” làm language abstraction?

Nếu language nói:

```text id="b9ryz0"
mọi object = address
```

thì programmer sẽ phải suy nghĩ về:

```text id="91v8jf"
pointer
address
alias
lifetime
allocation
free
```

và chúng ta quay lại đúng vấn đề bạn muốn tránh.

Axiom nên có:

```text id="o9q3yq"
Value model
    ↓
Storage model
    ↓
Machine address model
```

Ba tầng độc lập.

---

# 10. Heap không phải kẻ thù

Một quan niệm tôi muốn tránh:

> “Heap chậm nên phải loại bỏ heap.”

Chi phí thực tế phụ thuộc:

```text id="v5k3v4"
allocation frequency
allocator contention
fragmentation
cache locality
indirection
object size
object lifetime
NUMA
synchronization
```

Ví dụ một allocation lớn, hiếm:

```text id="x9g5z2"
1 allocation / 10 seconds
```

không đáng kể.

Ngược lại:

```text id="2yrp8j"
10 million tiny allocations / second
```

thì allocator strategy cực kỳ quan trọng.

---

# 11. Vì vậy Axiom nên có Allocation Strategy

Thay vì:

```text id="0y3xrw"
new
delete
```

tôi muốn library abstraction:

```text id="8r3y7m"
Allocator
Arena
Pool
Slab
Buffer
Box
Vec
```

Compiler chỉ cần hiểu semantic contract.

---

# 12. `Box<T>`

`Box<T>`:

```text id="v5lq7y"
OWNED
!Copy
Drop
```

Ví dụ:

```axiom id="x6k2c9"
let x = Box.new(Node(...))
```

Semantic:

```text id="8dzm9y"
x owns T
```

Không nhất thiết:

```text id="2u6kqq"
heap malloc
```

Nếu compiler chứng minh object không escape:

```text id="b0m31j"
Box allocation
    ↓
eliminate
    ↓
stack/register
```

---

# 13. Nhưng khi nào Box phải có stable address?

Nếu API:

```axiom id="f3xw8c"
raw_ptr(x)
```

được gọi trong unsafe, address trở thành observable.

Khi đó compiler phải bảo toàn storage identity trong phạm vi semantic contract.

Đây là:

```text id="7q3l3x"
Address-observable boundary
```

---

# 14. `Vec<T>`

Semantic model:

```text id="v3b9t2"
Vec<T> {
    logical region
    storage identity
    length
    capacity
}
```

Không bắt buộc representation chính xác là:

```text id="v5n0pm"
ptr + len + cap
```

nhưng native implementation thường có thể như vậy.

---

# 15. Vec relocation

Khi:

```axiom id="x0t0op"
v.push(x)
```

có thể:

```text id="z3y8xn"
storage S1
    ↓
allocate S2
    ↓
move elements
    ↓
free S1
```

Do đó effect:

```text id="ly2r1b"
MAY_RELOCATE
```

Nếu capacity còn:

```text id="c0w2v4"
S1 → S1
```

nhưng language semantics **không được giả định điều này** nếu API chỉ đảm bảo “may relocate”.

---

# 16. `reserve` nên là semantic boundary rõ ràng

Ví dụ:

```axiom id="gq55x2"
v.reserve(1024)
```

có:

```text id="l0x9d4"
MAY_RELOCATE
```

Điều này cho phép programmer chủ động chuẩn bị capacity trước khi tạo view.

Ví dụ:

```axiom id="0y5m1u"
v.reserve(1024)

let view = view(v)

process(view)
```

Trong thời gian view active:

```text id="8h7qaf"
v.push(...)
```

=> compiler reject nếu push may relocate.

---

# 17. Arena

Arena rất phù hợp với mục tiêu của Axiom.

Ví dụ:

```axiom id="n6km5w"
let arena = Arena.new()

let a = arena.alloc<Node>()
let b = arena.alloc<Node>()
let c = arena.alloc<Node>()
```

Thay vì:

```text id="5n5q7m"
3 malloc
3 free
```

có thể:

```text id="m4j7bz"
chunk allocation
    ↓
bump allocation
    ↓
destroy arena
```

Chi phí allocation gần:

```text id="j8d3m2"
pointer += size
```

---

# 18. Nhưng Arena không nên thay thế ownership

Arena không nên có semantics:

```text id="y1b5gc"
mọi object tự động sống tới arena destruction
```

rồi bỏ qua lifetime safety.

Ta vẫn cần:

```text id="qk9b3w"
Arena owns allocations
```

và:

```text id="r8q9e2"
view/object derived from arena
```

không được escape khỏi arena.

Ví dụ:

```axiom id="m7x0kw"
fn bad() -> view<Node> {
    let arena = Arena.new()
    let node = arena.alloc(...)
    return view(node)
}
```

=> reject.

---

# 19. Đây là nơi Region Model trở nên rất mạnh

Arena:

```text id="e3lq0x"
Arena A
├── R1 Node
├── R2 Node
└── R3 Node
```

Arena destruction:

```text id="4n8v5x"
DROP(A)
```

invalidates:

```text id="7d5s6m"
R1
R2
R3
```

Nếu có active view:

```text id="5k3w4s"
view(R2)
```

thì Drop Arena conflict.

Compiler tự bắt được.

---

# 20. Pool

Pool phù hợp object cùng size:

```text id="2ry9v1"
Pool<Node>
```

Semantic:

```text id="9t0m1c"
allocate Node
release Node
```

Physical:

```text id="0v3k9e"
free-list
```

hoặc bitmap.

Điểm quan trọng:

> Pool là allocator strategy, không phải language primitive.

---

# 21. Slab

Slab có thể là:

```text id="tq4z8m"
Slab<T>
```

với:

```text id="4l7b3j"
stable slot identity
```

Rất hữu ích cho:

- server
- ECS
- networking
- OS-like workloads
- game engine

Axiom không cần đưa slab vào core.

---

# 22. Custom allocator

Axiom nên cho:

```axiom id="s7x7tw"
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
}
```

Nhưng allocator trait **không nên nằm trong language core**.

Standard library có thể định nghĩa.

Ví dụ:

```axiom id="j4r3yn"
Vec<T, A: Allocator>
```

hoặc implementation có thể hide allocator type.

---

# 23. Tôi không muốn allocator trở thành generic bắt buộc

Không nên bắt programmer viết:

```axiom id="w4kq9j"
Vec<u8, SystemAllocator>
```

cho mọi vector.

Mặc định:

```axiom id="7i5q6v"
Vec<u8>
```

đủ.

Nếu cần custom:

```axiom id="p4j9m3"
Vec.with_allocator(arena)
```

hoặc API tương đương.

---

# 24. Fragmentation

Đây là phần liên quan trực tiếp câu hỏi ban đầu của bạn.

Flat virtual memory **không tự giải quyết fragmentation**.

Có ít nhất:

```text id="6j7w9q"
Internal fragmentation
External fragmentation
Virtual address fragmentation
Physical memory fragmentation
```

Axiom nên xử lý bằng **allocation strategies**, không bằng một allocator duy nhất.

---

# 25. Default allocator

Tôi đề xuất standard library có:

```text id="k1i8o0"
SystemAllocator
```

nhưng implementation được target-specific.

Ví dụ:

```text id="c8x4qn"
Windows → OS allocator
Linux   → system allocator
macOS   → system allocator
```

Không cần Axiom tự viết allocator ngay từ đầu.

Nhưng compiler/runtime semantics không phụ thuộc allocator.

---

# 26. Small Object Optimization

Axiom nên tận dụng:

```text id="6q1m8k"
inline storage
```

Ví dụ `String`:

```text id="g6q1r4"
String {
    inline small buffer
    or
    external storage
}
```

Không cần programmer biết.

Nếu string nhỏ:

```text id="6s8n2y"
no heap
```

Nếu lớn:

```text id="u3p6w8"
dynamic storage
```

---

# 27. Nhưng SSO không được trở thành semantic assumption

Ví dụ:

```axiom id="0w0t3k"
let s = "hello"
```

Programmer không được phép giả định:

```text id="9k4n0m"
address(s) == address(internal buffer)
```

nếu API không cam kết.

Điều này giữ compiler freedom.

---

# 28. Stable storage abstraction

Tôi nghĩ Axiom nên có một abstraction riêng sau này:

```text id="0u7vqb"
Stable<T>
```

Ý nghĩa:

```text id="6m0c0q"
T has stable storage identity
```

Nó khác:

```text id="9m8g0u"
Box<T>
```

ở semantic guarantee.

`Box<T>` có thể cung cấp stable address trong thời gian ownership, nhưng `Stable<T>` có thể mạnh hơn về:

- pinning
- relocation prohibition
- address identity
- FFI

Chưa cần đóng syntax ngay.

---

# 29. Pinning

Đừng đưa `Pin` kiểu Rust vào Core v0.1.

Nhưng semantic requirement phải tồn tại:

```text id="4h3r6u"
some objects cannot relocate
```

Có thể giải quyết bằng:

```text id="2v8y7k"
stable storage abstraction
```

ở library/system layer.

Core chỉ cần hiểu:

```text id="9p2m5d"
STABLE_ADDRESS
```

là một observable property khi cần.

---

# 30. Static

```axiom id="e3n7x2"
static config: Config = ...
```

có:

```text id="5j8r0d"
storage identity
lifetime = program
```

Không giống:

```axiom id="y7g6a2"
const config = ...
```

`const` là compile-time value.

`static` là storage identity.

---

# 31. Global mutable state

Tôi vẫn giữ quyết định trước:

```text id="8q2n6b"
mutable static
```

phải:

```text
synchronized
```

hoặc:

```text
unsafe
```

Ví dụ:

```axiom id="n5g0f8"
static var counter: Atomic<i64>
```

hợp lệ.

Nhưng:

```axiom id="a4y1c9"
static var counter: i64
```

không được phép dùng concurrent mutation trong safe code.

---

# 32. Thread-local

Thread-local storage:

```text id="q9m4v7"
@thread_local
static var state: State
```

mỗi execution context có storage riêng.

Do đó:

```text id="w1v7p4"
no cross-thread sharing
```

và có thể tránh synchronization.

---

# 33. External storage

Axiom cần abstraction:

```text id="r0c5h9"
EXTERNAL
```

cho:

- mmap
- shared memory
- GPU buffer
- DMA
- OS memory
- foreign memory

Ví dụ:

```axiom id="7t2q4k"
unsafe {
    let buffer = mmap(...)
}
```

Verifier phải coi nó là external provenance.

---

# 34. DMA/GPU

Đây là lý do tôi không muốn memory model quá CPU-centric.

Về semantic:

```text id="d8j0n1"
Buffer<T>
```

có thể thuộc:

```text id="6t8s4e"
CPU memory
GPU memory
DMA memory
shared memory
mapped memory
```

Storage class:

```text id="w4v9j2"
EXTERNAL
```

có thể mở rộng sau này.

Core không cần hiểu Vulkan/CUDA/DirectX.

---

# 35. Allocation effect

MIR:

```text id="3g7s4b"
ALLOC
DEALLOC
```

không nên đồng nghĩa với:

```text id="6d9y1h"
heap malloc/free
```

Định nghĩa:

```text id="m7x3e0"
ALLOC = acquire semantic storage
DEALLOC = release semantic storage
```

Backend có thể biến:

```text id="6m0y1v"
ALLOC
```

thành:

```text id="q4d9x8"
stack offset
register
arena bump
heap call
static storage
```

---

# 36. Allocation elimination

Ví dụ:

```axiom id="8l4v2j"
fn f() -> i32 {
    let x = Box.new(10)
    *x + 2
}
```

Nếu không expose address:

```text id="g3n1d5"
Box allocation
```

có thể biến thành:

```text id="3m7q8s"
x = 10
return x + 2
```

Không còn allocation.

Đây là:

```text id="c7j2p0"
scalar replacement / allocation elimination
```

---

# 37. Caller-allocated return

Ví dụ:

```axiom id="s5n9w3"
fn make_large() -> LargeStruct
```

không nhất thiết phải:

```text id="7h2n5x"
allocate temporary
copy to caller
```

ABI có thể:

```text id="m1x8v6"
caller allocates return storage
callee writes directly
```

Semantic vẫn:

```text id="k9p3s4"
return OWNED
```

Đây là một optimization/ABI detail.

---

# 38. Move không đồng nghĩa memcpy

Ví dụ:

```axiom id="x8z5q1"
let b = a
```

nếu `a` non-Copy:

```text id="z0f1s7"
MOVE
```

không nhất thiết:

```text id="9c4m8k"
memcpy
```

Compiler có thể chỉ chuyển ownership metadata/registers.

Đặc biệt với:

```text id="3h8n5p"
large struct
```

có thể không cần physical copy.

---

# 39. Điều này giúp đạt mục tiêu “nhanh hơn C++ ở một số workload”

Không nên tuyên bố Axiom luôn nhanh hơn C++.

Nhưng kiến trúc cho phép:

```text id="s7c2m4"
value semantics
+
aggressive optimization
+
no mandatory runtime
+
no implicit RC
+
no GC
+
no hidden virtual dispatch
+
allocation elimination
+
scalar replacement
+
static dispatch
```

=> compiler có nhiều cơ hội tối ưu giống C/C++ mà semantics an toàn hơn.

---

# 40. Storage invariants

Tôi đề xuất chính thức:

### ASM-01 — Storage Abstraction

Semantic value không phụ thuộc storage location trừ khi location được expose.

### ASM-02 — No Mandatory Heap

Không có language construct nào bắt buộc heap allocation nếu semantics không yêu cầu.

### ASM-03 — No Mandatory Object Header

Object không có hidden header mặc định.

### ASM-04 — Storage Freedom

Compiler được thay đổi storage strategy nếu observable semantics không đổi.

### ASM-05 — Allocation Semantics

`ALLOC/DEALLOC` là semantic storage operations, không mặc định là heap calls.

### ASM-06 — Stable Address Explicit

Stable address chỉ tồn tại khi type/API/operation yêu cầu.

### ASM-07 — Relocation Safety

Relocation phải invalidate capability phụ thuộc storage identity.

### ASM-08 — Allocation Strategy Independence

Language semantics không phụ thuộc system allocator.

### ASM-09 — Arena Safety

Arena-owned values không được escape vượt lifetime của arena.

### ASM-10 — External Memory

External storage phải có explicit provenance/unsafe contract.

### ASM-11 — Optimization Freedom

Allocation elimination không được thay đổi observable resource behavior.

### ASM-12 — Fragmentation Independence

Language correctness không phụ thuộc fragmentation strategy.

---

# 41. Tôi sẽ chọn mô hình nào làm mặc định?

Không phải:

```text
Flat memory
```

cũng không phải:

```text
Heap everywhere
```

mà là:

```text
                AXIOM VALUE
                     │
             Compiler decides
                     │
       ┌─────────────┼─────────────┐
       ↓             ↓             ↓
    REGISTER       INLINE         LOCAL
                                    │
                              ┌─────┴─────┐
                              ↓           ↓
                            STACK       DYNAMIC
                                         │
                            ┌────────────┼────────────┐
                            ↓            ↓            ↓
                          HEAP        ARENA         POOL
```

và:

```text
STATIC
THREAD_LOCAL
EXTERNAL
```

là các storage classes bổ sung.

---

# 42. Quan trọng nhất: programmer không cần chọn

Code:

```axiom id="j0x8e7"
struct Particle {
    position: Vec3
    velocity: Vec3
}
```

không nói:

```text
heap
stack
arena
```

Compiler quyết định.

Nếu muốn arena:

```axiom id="5u7q0r"
let particle = arena.alloc(Particle(...))
```

thì programmer **đã thể hiện semantic requirement**.

Nếu muốn stable address:

```text id="2t9q6k"
Stable<T>
```

Nếu muốn raw address:

```text id="f8k3w1"
unsafe
```

Đây là ranh giới rất sạch.

---

# 43. Một quyết định tôi nghĩ nên đóng băng

**Axiom không có `new` và `delete` trong Core.**

Không nên có:

```axiom
new Foo(...)
delete x
```

thậm chí chỉ để “cho giống C++”.

Thay vào đó:

```axiom
Foo(...)
Box.new(...)
Vec.new(...)
Arena.alloc(...)
Pool.acquire(...)
```

và:

```text
Drop
```

được compiler quản lý.

Điều này loại bỏ rất nhiều class bug:

```text
double free
use after free
delete wrong type
delete array mismatch
```

trong safe code.

---

# 44. Và một quyết định còn quan trọng hơn

**Axiom không có một “default heap object model”.**

Không có:

```text id="p8w1n7"
object header
type pointer
refcount
GC mark bits
virtual table
```

trừ khi type abstraction cụ thể yêu cầu.

Do đó một:

```axiom id="x6q4s1"
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

có thể đúng nghĩa chỉ là:

```text id="e4j7p2"
12 bytes
```

với alignment phù hợp.

Đây là nền tảng để Axiom giữ được chất **systems language**.

---

## Bước tiếp theo

Sau Storage Model, tôi nghĩ chúng ta nên chuyển sang một phần có ảnh hưởng cực lớn đến **binary size + hiệu năng**:

# `AXIOM RUNTIME MODEL v0.1`

Câu hỏi cần khóa là:

> **Một chương trình Axiom nhỏ nhất thực sự cần những gì?**

Ví dụ:

```axiom
fn main() {
    let x = 1 + 2
    print(x)
}
```

Compiler phải có khả năng tạo:

```text
EXE/ELF
├── user code
├── startup
├── required syscalls/ABI glue
└── nothing else
```

không tự động kéo vào:

```text
GC
async runtime
thread runtime
reflection
exception runtime
allocator
logging
Unicode tables
network stack
```

nếu chương trình không dùng.

Đây sẽ là bước quyết định xem mục tiêu **“binary nhỏ như assembly nhưng vẫn có abstraction hiện đại”** của Axiom có thực tế đến mức nào.