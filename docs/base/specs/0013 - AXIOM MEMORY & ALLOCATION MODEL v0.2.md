Tiếp tục. Đây là phần tôi cho rằng **quan trọng nhất về mặt hiệu năng sau semantic core**: không nên chọn đơn giản “stack hay heap”, mà phải tách **memory address model**, **storage model**, và **allocation model**. Nếu không tách ba thứ này, Axiom rất dễ bị khóa vào một mô hình memory quá sớm.

# AXIOM MEMORY & ALLOCATION MODEL v0.2

## 1. Quyết định nền tảng

Axiom nên có:

> **Flat virtual address space về mặt machine model, nhưng không có “flat allocation model”.**

Tức là:

```text
                    AXIOM MEMORY
                         │
             ┌───────────┴───────────┐
             │                       │
       ADDRESS MODEL            STORAGE MODEL
             │                       │
       flat virtual addr       register
                              inline
                              stack
                              arena
                              pool
                              heap
                              static
                              external
```

Đây là cách tốt hơn việc nói:

> “Axiom dùng flat memory.”

Vì flat address space **không tự động giải quyết fragmentation**.

---

# 2. Ba tầng phải tách biệt

### Address

CPU nhìn thấy:

```text
0x0000...
0x1000...
0x7fff...
```

### Storage

Compiler quyết định value nằm ở đâu:

```text
register
stack
inline
heap
arena
static
```

### Allocation

Nếu cần storage động, allocator quyết định cấp phát thế nào:

```text
general allocator
arena
pool
slab
custom
OS
GPU
shared memory
```

Một `Buffer<T>` có thể sử dụng bất kỳ allocator nào mà không thay đổi language semantics.

---

# 3. Không có `new` / `delete` trong Core

Đây là quyết định tôi khuyến nghị.

Không:

```text
new Foo()
delete foo
```

Ownership API nên ở abstraction level cao hơn.

Ví dụ:

```axiom
let x = Box.alloc(value)
```

hoặc:

```axiom
let buffer = Buffer.allocate(1024)
```

`Box`/`Buffer` là library types.

Compiler không cần biết:

```text
malloc
free
jemalloc
mmap
VirtualAlloc
arena
pool
```

để hiểu ownership.

---

# 4. Allocation là implementation detail — cho đến khi programmer yêu cầu

Ví dụ:

```axiom
fn create() -> Point {
    Point { x: 1, y: 2 }
}
```

Compiler hoàn toàn có thể:

```text
return registers
```

Không có allocation.

Nhưng nếu:

```axiom
fn create() -> Box<Point> {
    ...
}
```

thì programmer đã yêu cầu một **owned dynamically allocated object abstraction**.

Đây là boundary hợp lý.

---

# 5. Storage hierarchy

Axiom compiler nên tối ưu theo hướng:

```text
             ┌──────────────┐
             │   CONSTANT   │
             └──────┬───────┘
                    │
             ┌──────▼───────┐
             │   REGISTER   │
             └──────┬───────┘
                    │
             ┌──────▼───────┐
             │    INLINE    │
             └──────┬───────┘
                    │
             ┌──────▼───────┐
             │    STACK     │
             └──────┬───────┘
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        ARENA      POOL      HEAP
          │         │         │
          └─────────┼─────────┘
                    ▼
                  OS
```

Nhưng đây **không phải thứ programmer phải chọn cho từng value**.

---

# 6. Stack

Stack phù hợp với:

- local values
- temporary
- function frames
- small arrays
- short-lived structures

Ví dụ:

```axiom
fn calculate() -> i32 {
    let p = Point { x: 10, y: 20 }

    p.x + p.y
}
```

`p` có thể nằm hoàn toàn trên registers.

Không có guarantee:

```text
"p nằm trên stack"
```

---

# 7. Escape Analysis

Đây là vũ khí quan trọng của Axiom.

Ví dụ:

```axiom
fn make() -> Buffer {
    let b = Buffer(1024)
    fill(b)
    b
}
```

Compiler phân tích:

```text
b
│
├── local
├── modified
└── returned
```

Nếu `Buffer` yêu cầu dynamic storage thì backing memory vẫn có thể heap/arena.

Nhưng nếu:

```axiom
fn sum() -> i32 {
    let b = SmallBuffer<16>()
    ...
    sum(b)
}
```

compiler có thể:

```text
heap allocation
      ↓
stack
      ↓
register/inline
```

---

# 8. Allocation Elimination

Ví dụ conceptual:

```axiom
fn distance(a: Point, b: Point) -> f64 {
    let temp = Point {
        x: a.x - b.x,
        y: a.y - b.y
    }

    sqrt(temp.x * temp.x + temp.y * temp.y)
}
```

Không cần:

```text
malloc
```

thậm chí có thể không cần storage:

```text
temp.x → register
temp.y → register
```

Đây là **Scalar Replacement of Aggregates**.

Axiom phải thiết kế để compiler có thể làm việc này dễ dàng.

---

# 9. Heap không phải kẻ thù

Không nên có triết lý:

> heap = chậm, stack = nhanh.

Thực tế quan trọng hơn là:

```text
allocation count
allocation cost
locality
cache behavior
fragmentation
lifetime
indirection
synchronization
```

Một arena allocation có thể rẻ hơn stack manipulation phức tạp.

Một heap object được truy cập tuần tự có thể nhanh hơn một cấu trúc stack gây cache pressure.

Axiom không nên hard-code dogma.

---

# 10. Arena

Arena là một allocation strategy rất phù hợp Axiom.

Ví dụ:

```axiom
let arena = Arena.create()

let a = arena.alloc(Node(...))
let b = arena.alloc(Node(...))
```

Khi arena chết:

```text
arena
 ↓
release entire region
```

Không cần drop từng allocation nếu semantics của object cho phép.

Nhưng cần phân biệt:

> **memory lifetime của arena ≠ resource lifetime của object.**

Nếu object chứa file/socket/GPU resource thì vẫn phải chạy cleanup semantic thích hợp.

---

# 11. Pool / Slab

Cho game engine, server, ECS, networking:

```text
Pool<T>
Slab<T>
ObjectPool<T>
```

nên là library abstractions.

Ví dụ:

```axiom
let pool = Pool<Entity>.create(4096)

let entity = pool.acquire()
...
pool.release(entity)
```

Không cần compiler đặc biệt cho pool.

---

# 12. Fragmentation

Đây là điểm quan trọng với câu hỏi ban đầu của bạn.

Fragmentation có ít nhất:

```text
external fragmentation
internal fragmentation
virtual address fragmentation
cache fragmentation / locality loss
```

Flat address space không tự loại bỏ chúng.

Giải pháp Axiom nên là:

### Compiler

- lifetime analysis
- escape analysis
- allocation elimination
- stack promotion

### Library

- arena
- pool
- slab
- segregated allocation
- region allocation

### Runtime/OS layer

- page allocation
- virtual memory mapping

Như vậy programmer có nhiều lựa chọn mà **language core không bị gắn với allocator nào**.

---

# 13. Ownership + Allocator

Đây là chỗ Axiom có thể tốt hơn C.

Ví dụ:

```axiom
let b = Buffer.allocate(1024)
```

`b` là owning value.

Khi lifetime kết thúc:

```text
b
 ↓
Drop
 ↓
allocator.release(storage)
```

Compiler biết ownership nên có thể xác định chính xác thời điểm release.

Không cần GC scan toàn heap.

---

# 14. Không có implicit reference counting

Không nên:

```text
let a = object
let b = a
```

tự động biến thành:

```text
RC++
```

Điều đó sẽ làm mọi copy potentially có cost.

Thay vào đó:

```text
Copy
Move
Shared<T>
```

là ba semantics khác nhau.

---

# 15. Shared ownership

Khi thực sự cần:

```axiom
let x = Shared.create(value)
```

hoặc:

```axiom
let x = Arc.create(value)
```

Có thể có:

```text
Shared<T>
Arc<T>
Weak<T>
```

ở standard library.

Reference counting chỉ xuất hiện khi programmer chọn abstraction đó.

---

# 16. Nhưng `Arc<T>` không được biến thành language primitive

Language chỉ cần hiểu:

```text
T: Drop
T: Send
T: Share
```

`Arc<T>` là library implementation.

Điều này giữ compiler nhỏ và semantics sạch.

---

# 17. Custom allocator

Một systems language phải cho phép:

```axiom
let allocator = MyAllocator(...)
let buffer = Buffer.allocate_in(allocator, 4096)
```

Nhưng allocator interface nên là library/ABI contract.

Conceptually:

```axiom
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
    fn resize(...)
}
```

Compiler không cần biết implementation.

---

# 18. `no_std` / runtime-free

Tôi không muốn Axiom sao chép nguyên xi mô hình `no_std`.

Thay vào đó:

> **Runtime components chỉ được link khi program thực sự sử dụng chúng.**

Ví dụ:

```text
hello.ax
   ↓
print
   ↓
console I/O component
```

Trong khi:

```text
math.ax
   ↓
pure computation
   ↓
native executable
```

không tự kéo theo:

```text
GC
thread runtime
async executor
reflection
network
filesystem
```

---

# 19. Static storage

```axiom
static TABLE: [u8; 256] = ...
```

Static data có process lifetime.

Nhưng static mutable state phải rất rõ ràng vì concurrency.

Ví dụ:

```axiom
static var counter: Atomic<i64>
```

hợp lệ nếu API/semantic model cho phép.

Không nên có global mutable state bình thường mà compiler không thể phân tích.

---

# 20. Thread-local

Đây nên là library/compiler attribute:

```axiom
@thread_local
static CACHE: ...
```

không phải một loại ownership mới.

---

# 21. Alignment

Compiler tự chọn alignment native.

Ví dụ:

```text
i32 → target alignment
f64 → target alignment
struct → max member alignment
```

Explicit alignment:

```axiom
@align(64)
struct CacheLine {
    ...
}
```

nếu cần.

Đây là system-level feature.

---

# 22. Packed structures

Không nên khuyến khích:

```axiom
@packed
```

trong safe code.

Nếu cần:

```axiom
@repr(packed)
```

thì nên là unsafe/system representation.

Lý do:

- unaligned access
- performance
- target-specific behavior
- FFI concerns.

---

# 23. Inline storage

Đây là feature rất đáng có.

Ví dụ:

```axiom
struct SmallVec<T, N> {
    ...
}
```

`N` phần tử đầu nằm inline.

Conceptually:

```text
SmallVec
┌─────────────────────┐
│ length              │
│ capacity             │
│ inline[0]            │
│ inline[1]            │
│ ...                  │
└─────────────────────┘
```

Khi vượt N:

```text
inline
  ↓
heap
```

Nhưng API vẫn giữ nguyên.

---

# 24. Small String Optimization

Không nên biến SSO thành language rule.

`String` standard library có thể chọn:

```text
small string → inline
large string → heap
```

Compiler vẫn nhìn nó như một type bình thường.

Điều này rất quan trọng:

> **Performance tricks thuộc implementation của type, không thuộc semantic core nếu không cần thiết.**

---

# 25. Zero-sized types

Axiom nên cho phép:

```axiom
struct Marker {}
```

Không bắt buộc chiếm 1 byte.

Compiler có thể:

```text
sizeof(Marker) = 0
```

nếu ABI context cho phép.

Điều này hữu ích cho:

```text
type markers
phantom types
compile-time states
traits
capabilities
```

---

# 26. Memory ownership không đồng nghĩa physical ownership

Ví dụ:

```text
view<T>
```

không sở hữu memory.

Nhưng:

```text
Buffer<T>
```

có thể sở hữu backing storage.

Còn:

```text
Shared<T>
```

sở hữu một phần lifetime protocol.

Vì vậy nên formalize:

```text
Ownership
    ≠
Physical allocation
```

Ownership là semantic responsibility.

---

# 27. Memory model cho compiler

Tôi đề xuất Axiom có 5 loại storage semantics nội bộ:

```text
STATIC
LOCAL
INLINE
DYNAMIC
EXTERNAL
```

Trong đó:

### STATIC

Process/module lifetime.

### LOCAL

Compiler-controlled local storage.

### INLINE

Nằm trong parent aggregate.

### DYNAMIC

Allocation-managed storage.

### EXTERNAL

Memory do OS/device/FFI cung cấp.

Không cần expose toàn bộ 5 loại cho programmer.

---

# 28. MIR allocation model

MIR có:

```text
ALLOC
DEALLOC
LOAD
STORE
ADDRESS
VIEW
```

Nhưng:

```text
ALLOC
```

không có nghĩa bắt buộc:

```text
malloc()
```

Nó nghĩa:

> “Semantic storage acquisition.”

Sau optimization:

```text
ALLOC
 ↓
STACK
```

hoặc:

```text
ALLOC
 ↓
INLINE
```

hoặc:

```text
ALLOC
 ↓
ELIMINATED
```

---

# 29. Một optimization cực kỳ quan trọng: caller allocation

Ví dụ:

```axiom
fn make_point() -> Point
```

Compiler có thể lower thành:

```text
caller allocates result storage
callee writes directly into it
```

thay vì:

```text
callee creates temporary
↓
copy
↓
return
```

Đặc biệt hữu ích cho aggregate lớn.

---

# 30. Ownership giúp compiler làm điều C khó làm

Ví dụ:

```axiom
fn transform(x: BigStruct) -> BigStruct {
    ...
}
```

Vì compiler biết ownership:

```text
input x
    ↓
mutate/reuse storage
    ↓
return same storage
```

có thể tránh copy.

C++ cũng làm được với move/RVO, nhưng Axiom có thể thiết kế semantics ngay từ đầu theo hướng này thay vì phải duy trì rất nhiều legacy rules.

---

# 31. Memory locality là first-class optimization target

Axiom compiler nên có freedom để:

```text
field reordering
scalar replacement
structure splitting
array-of-structures ↔ optimized representations
```

**nhưng chỉ trong native representation**.

Nếu:

```axiom
@repr(C)
```

thì layout trở thành observable ABI.

---

# 32. Một phân biệt rất quan trọng

### Native type

```axiom
struct Particle {
    ...
}
```

Compiler tự tối ưu.

### ABI type

```axiom
@repr(C)
struct CParticle {
    ...
}
```

Layout bị ràng buộc.

Đừng để FFI constraints làm toàn bộ language mất optimization freedom.

---

# 33. Memory safety boundary

Safe Axiom phải đảm bảo:

```text
NO
├── use-after-free
├── double-free
├── dangling view
├── out-of-bounds
├── invalid ownership
├── data race
└── invalid safe pointer dereference
```

Unsafe Axiom có thể vi phạm các invariant đó.

Nhưng:

> unsafe code không được âm thầm biến semantics của phần safe thành “không xác định” nếu safe code chỉ sử dụng API có contract đúng.

Đây là trách nhiệm cực lớn của unsafe API designer.

---

# 34. Memory model invariant mới

Tôi đề xuất thêm:

**AMM-01**

> Storage location is not part of ordinary value semantics.

**AMM-02**

> Allocation strategy is not part of ordinary type semantics.

**AMM-03**

> Compiler may change storage strategy when observable semantics are preserved.

**AMM-04**

> No ordinary value requires a heap allocation unless its type/API semantics explicitly require dynamic storage.

**AMM-05**

> No implicit reference counting.

**AMM-06**

> No tracing garbage collector is required by Core.

**AMM-07**

> Ownership determines resource responsibility, not physical address location.

**AMM-08**

> Custom allocation strategies are library/ABI abstractions.

**AMM-09**

> Native layout may be optimized freely unless representation is explicit.

**AMM-10**

> Explicit representation creates an ABI/optimization boundary.

**AMM-11**

> Safe code cannot observe an allocation strategy merely by ordinary language operations.

**AMM-12**

> Semantic Drop is distinct from physical deallocation.

---

# 35. Và tôi muốn điều chỉnh một ý từ trước

Trước đây ta nói:

```text
Register → Inline → Stack → Arena/Pool → Heap → OS
```

Không nên coi đây là một **hierarchy bắt buộc**.

Đúng hơn:

```text
                 VALUE
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
    register    inline      addressable
                              │
                   ┌──────────┼──────────┐
                   ▼          ▼          ▼
                 stack      arena       heap
```

Một value có thể chuyển giữa chúng.

Không có:

> “Axiom object bắt đầu ở heap rồi compiler promote lên stack.”

Compiler có thể ngay từ đầu quyết định:

```text
register
```

nếu phân tích được.

---

# 36. Mô hình cuối cùng tôi đề xuất

```text
                         AXIOM VALUE
                              │
                ┌─────────────┴─────────────┐
                │                           │
             INLINE                    OUT-OF-LINE
                │                           │
       ┌────────┼────────┐         ┌────────┼────────┐
       ▼        ▼        ▼         ▼        ▼        ▼
   register   stack    static    arena     pool     heap
                                                     │
                                                     ▼
                                                    OS
```

Programmer chủ yếu nhìn thấy:

```text
T
view<T>
mut_view<T>
Box<T>
Buffer<T>
Shared<T>
```

chứ không phải:

```text
stack pointer
heap pointer
malloc
free
```

---

# 37. Điều này trả lời câu hỏi “flat memory có nhanh hơn không?”

**Không phải bản thân flat memory.**

Cái tạo performance là:

```text
flat address space
        +
good locality
        +
few allocations
        +
predictable lifetime
        +
allocation elimination
        +
stack/inline/register promotion
        +
specialized data structures
        +
good optimizer
```

Axiom nên tối ưu **toàn bộ chuỗi**, thay vì tuyên bố một kiểu memory duy nhất là nhanh nhất.

---

# 38. Một điểm rất đáng giá của Axiom

Nếu thiết kế đúng, cùng một source:

```axiom
fn process(data: Buffer<u8>) {
    ...
}
```

có thể chạy theo những chiến lược hoàn toàn khác:

```text
Debug build:
    heap + guards

Desktop release:
    heap

Game engine:
    arena

Embedded:
    static/custom pool

High-performance:
    stack/inline/register where possible
```

mà **source semantic không đổi**.

Đây chính là abstraction mà tôi nghĩ Axiom nên theo đuổi.

---

## Bây giờ kiến trúc đã có 4 lớp khá chắc

```text
┌─────────────────────────────────────────┐
│          AXIOM LANGUAGE SYNTAX          │
├─────────────────────────────────────────┤
│          SEMANTIC CORE                  │
│ type / value / ownership / access       │
├─────────────────────────────────────────┤
│          MEMORY MODEL                   │
│ storage / allocation / lifetime         │
├─────────────────────────────────────────┤
│          CONCURRENCY MODEL              │
│ Send / Share / atomic / async / thread  │
└─────────────────────────────────────────┘
```

**Bước tiếp theo tôi khuyên làm là `AXIOM DATA MODEL & STANDARD TYPES v0.1`**, tức đóng những type nền tảng mà gần như toàn bộ compiler + standard library sẽ dựa vào:

```text
Option<T>
Result<T,E>
Array<T,N>
Slice/View
Vec<T>
String
Text
Bytes
Map
Set
Box
Shared
Rc/Arc
Atomic
Tuple
Function
Closure
Iterator
```

Nhưng ở bước đó tôi muốn đặc biệt xem xét **`Vec<T>`, `String`, `Buffer<T>`, `Box<T>` và `Shared<T>` dưới góc nhìn allocation + ownership**, vì nếu thiết kế những type này sai thì memory model đẹp ở trên vẫn có thể biến thành một ngôn ngữ rất tốn allocation.