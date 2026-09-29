Tiếp tục từ baseline Axiom hiện tại, phần này nên **chốt Memory Allocation + Collections + Stable Address**. Đây là phần rất quan trọng vì nó quyết định Axiom có thực sự vừa “dễ như ngôn ngữ high-level” vừa đạt hiệu năng kiểu C/C++ hay không.

# Axiom Memory Allocation & Collections v0.1

## 1. Trước hết: không nên biến Stack/Heap thành khái niệm của ngôn ngữ

Tôi đề xuất giữ nguyên nguyên tắc:

> **Storage location is an implementation decision unless the programmer explicitly requires a storage contract.**

Ví dụ:

```axiom
let x = Foo(...)
```

Programmer không cần biết `x` nằm ở:

- register
- stack
- inline trong object khác
- heap
- static storage
- arena
- hoặc thậm chí bị optimizer loại bỏ hoàn toàn.

Compiler có thể biến:

```axiom
fn length(v: Vec2) -> f32 {
    return sqrt(v.x * v.x + v.y * v.y)
}
```

thành hoàn toàn register-based.

Không nên có kiểu:

```text
Stack<T>
Heap<T>
Register<T>
```

trong Core language.

Những thứ đó nếu cần chỉ xuất hiện trong **system/storage library**.

---

# 2. Flat memory model vẫn nên giữ

Tôi đồng ý với hướng bạn nói trước đó:

> Axiom nên có flat virtual address space.

Nhưng cần phân biệt:

```text
Flat address space
        ≠
Flat allocation strategy
```

Flat address space nghĩa là chương trình nhìn thấy một không gian địa chỉ tuyến tính:

```text
0x0000...
        |
        +----------------+
        | code           |
        +----------------+
        | readonly data  |
        +----------------+
        | static         |
        +----------------+
        | heap/arena/... |
        +----------------+
        | thread local   |
        +----------------+
        | stack          |
        +----------------+
```

Nhưng allocator hoàn toàn có thể sử dụng:

```text
general heap
arena
pool
slab
bump allocator
stack allocator
region allocator
custom allocator
OS virtual memory
GPU memory
shared memory
```

Điều này quan trọng vì **fragmentation không phải vấn đề của flat address space**.

Fragmentation chủ yếu là vấn đề của allocation pattern.

---

# 3. Axiom không nên có một "Heap" duy nhất

Đây là điểm tôi muốn chốt khá mạnh.

Không nên thiết kế:

```axiom
heap.alloc(...)
heap.free(...)
```

rồi coi đó là memory model chính.

Thay vào đó:

```text
              Storage
                 │
       ┌─────────┼──────────┐
       │         │          │
     Box       Arena      Pool
       │         │          │
    object     region      fixed objects
       │         │          │
     Vec      temporary    objects
```

Allocator là **strategy**, không phải bản chất của ownership.

---

# 4. `Box<T>` — abstraction cho stable owning allocation

Tôi đề xuất:

```axiom
let x = Box.new(Foo(...))
```

Semantic:

```text
x owns one dynamically allocated T
```

Nhưng điều thú vị là:

> `Box<T>` không nhất thiết phải thực sự heap allocate nếu compiler chứng minh được allocation không observable.

Ví dụ:

```axiom
fn create() -> Box<Foo> {
    return Box.new(Foo(...))
}
```

Compiler có thể biến thành caller-allocated return.

Thậm chí:

```text
Box allocation
     ↓
escape analysis
     ↓
does not escape
     ↓
stack/register/inline
```

Nếu programmer không lấy địa chỉ hoặc yêu cầu stable address.

---

# 5. Nhưng `Box<T>` phải có semantic identity riêng

Đây là điểm quan trọng.

Nếu:

```axiom
let a = Box.new(Foo(...))
let b = a
```

thì `Foo` không copy.

`a` move sang `b`.

```text
a ──owns──> allocation #17
                    │
                    └── Foo
```

sau move:

```text
a = MOVED

b ──owns──> allocation #17
```

Không có hai owner.

---

# 6. Stable address

Tôi đề xuất **không đưa `Pin<T>` vào Core language** theo kiểu Rust.

Nó làm programmer phải học thêm một abstraction khá nặng.

Thay vào đó, semantic contract nên đơn giản hơn:

```text
stable address
```

là một **property của storage abstraction**, không phải một lifetime mechanism mới.

Ví dụ:

```axiom
let x = Box.new(Foo(...))
```

có thể có:

```text
Box<T>
```

và nếu Box API cam kết địa chỉ ổn định:

```text
Box<T>
    └── stable storage identity
```

thì:

```axiom
let p = address_of(x)
```

sau đó move:

```axiom
let y = x
```

không được làm object chuyển địa chỉ.

Chỉ ownership handle thay đổi.

---

# 7. Tôi đề xuất chia hai semantic property

Thay vì `Pin<T>` phức tạp:

```text
Relocatable
StableAddress
```

### Relocatable

Object có thể bị chuyển storage.

Ví dụ:

```text
Vec<T> element
```

khi `Vec` grow.

### StableAddress

Object có địa chỉ ổn định trong lifetime của storage owner.

Ví dụ:

```text
Box<T>
Arena allocation
PinnedPool<T>
External allocation
```

Đây là semantic property.

Compiler có thể biết:

```text
T is stable-address
```

nhưng programmer không cần thao tác với pin state.

---

# 8. `Vec<T>` là trường hợp quan trọng nhất

Semantic:

```axiom
Vec<T>
```

là:

```text
owned
dynamic
contiguous
relocatable
```

với:

```text
length
capacity
elements
```

Compiler không cần expose:

```text
ptr
len
cap
```

như physical representation.

Nhưng semantic model tương đương:

```text
Vec<T>
 ├── storage identity
 ├── length
 └── capacity
```

---

# 9. `Vec` có thể relocate

Ví dụ:

```axiom
var xs = Vec<i32>()

xs.push(1)
xs.push(2)
```

sau đó:

```axiom
xs.push(3)
```

có thể:

```text
old allocation
0x1000

new allocation
0x5000
```

và copy/move elements sang đó.

Vì vậy:

```text
Vec element address
```

**không phải stable address contract**.

---

# 10. View là thứ khiến relocation trở nên thú vị

Ví dụ:

```axiom
var xs = Vec<i32>()

let v = view(xs)

xs.push(100)
```

Nếu `push()` có khả năng relocate thì compiler phải phát hiện:

```text
v
 ↓
depends on xs storage
 ↓
xs.push()
 ↓
MAY_RELOCATE
```

=> không hợp lệ nếu `v` vẫn active.

Nhưng nếu:

```axiom
print(v)

xs.push(100)
```

thì capability `v` đã hết semantic lifetime sau last-use.

Compiler có thể cho phép.

Đây là một ví dụ rất mạnh cho triết lý:

> Programmer không viết lifetime, compiler tự quản lý capability lifetime.

---

# 11. `reserve()` không nên hứa stable address

Đây là một quyết định tôi khuyên giữ rất rõ.

Không:

```axiom
xs.reserve(100)
// therefore address is stable
```

Bởi vì capacity hiện tại không nên trở thành một lifetime/address contract.

`reserve()` chỉ có nghĩa:

> cố gắng đảm bảo capacity đủ cho số phần tử yêu cầu.

Nếu programmer cần stable address:

```axiom
let x = Box.new(...)
```

hoặc Arena/Pool phù hợp.

---

# 12. Arena

Arena cực kỳ hữu ích cho Axiom.

Ví dụ compiler, game engine, parser, AST, temporary objects:

```axiom
let arena = Arena.new()

let a = arena.alloc(Node(...))
let b = arena.alloc(Node(...))
```

Semantic:

```text
Arena owns region
       │
       ├── a
       ├── b
       ├── ...
       └── all released together
```

Khi:

```axiom
drop(arena)
```

toàn bộ allocation thuộc arena được release.

Không cần:

```text
free(a)
free(b)
free(c)
...
```

---

# 13. Arena nên có stable address

Tôi đề xuất:

> Allocation trong một Arena **không được relocate** sau khi đã cấp phát.

Điều này khiến Arena cực kỳ hữu ích cho:

- AST
- scene graph
- compiler IR
- entity/object storage
- linked structures
- graph
- long-lived temporary objects

Nhưng object vẫn bị ràng buộc bởi lifetime của Arena.

Compiler sẽ kiểm tra:

```text
object/view cannot escape Arena
```

---

# 14. Pool/Slab

Đối với hàng triệu object cùng kích thước:

```axiom
Pool<Node>
```

hoặc:

```axiom
Slab<Node>
```

có semantic:

```text
fixed-size allocation
reuse released slots
```

Ví dụ:

```text
Pool<Node>

slot 0 -> Node
slot 1 -> Node
slot 2 -> free
slot 3 -> Node
```

Sau:

```axiom
drop(node)
```

slot có thể reuse.

Nhưng nếu một object address đang được expose thì allocator phải đảm bảo contract phù hợp.

---

# 15. Không nên biến Pool thành Core feature

Đây là library.

Core chỉ cần compiler hiểu các semantic property cần thiết:

```text
OWNED
DROP
STABLE
VIEW
ALLOC
DEALLOC
```

Pool implementation có thể nằm hoàn toàn trong library/system layer.

---

# 16. Allocator API

Tôi không muốn programmer thường xuyên phải viết:

```axiom
alloc(size, align)
free(ptr)
```

Đó là system-level API.

Normal code:

```axiom
Vec.new()
Box.new()
String.new()
Arena.new()
```

System code có thể dùng:

```axiom
Allocator
```

với interface kiểu:

```axiom
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
    fn resize(...)
}
```

Nhưng exact API có thể để stdlib thiết kế.

Core không cần biết `malloc`.

---

# 17. Custom allocator

Axiom nên cho phép:

```text
Vec<T, A>
Box<T, A>
Arena<A>
```

về mặt library abstraction nếu cần.

Nhưng **không nên bắt mọi programmer nhìn thấy allocator parameter**.

Có thể có default:

```axiom
Vec<T>
```

và advanced/system code:

```axiom
Vec<T, FrameAllocator>
```

hoặc cấu hình allocator ở container/context level.

Mục tiêu:

```text
simple code
    ↓
default allocator

high-performance systems code
    ↓
custom allocator
```

---

# 18. Fragmentation

Axiom không nên tuyên bố:

> flat memory → không fragmentation.

Điều đó không đúng.

Thay vào đó:

### General heap

Tối ưu cho:

```text
arbitrary lifetime
arbitrary size
```

### Arena

Tối ưu cho:

```text
same lifetime
bulk destruction
```

### Pool

Tối ưu cho:

```text
same/similar size
high churn
```

### Slab

Tối ưu cho:

```text
fixed object classes
```

### Stack/local

Tối ưu cho:

```text
nested lifetime
```

Compiler/library chọn abstraction phù hợp.

---

# 19. Quan trọng: Axiom không cần "heap defragmentation"

Không nên có GC-style heap compaction.

Vì Axiom không có:

```text
tracing GC
```

và programmer/compiler không cần một runtime theo dõi toàn bộ object graph.

Nếu muốn relocation:

```text
Vec
Arena
Pool
```

có semantic contract riêng.

Đây là một ưu điểm lớn của ownership model.

---

# 20. Allocation elimination

Đây sẽ là một trong những optimization quan trọng nhất của Axiom.

Ví dụ:

```axiom
fn sum() -> i32 {
    let v = Vec<i32>()
    v.push(1)
    v.push(2)
    return v[0] + v[1]
}
```

Compiler có thể thấy:

```text
Vec
 ↓
does not escape
 ↓
only 2 elements
 ↓
heap allocation unnecessary
```

và biến nó thành dạng tương đương:

```text
local storage/registers
```

hoặc thậm chí constant-fold:

```text
return 3
```

Nếu semantics cho phép.

---

# 21. Escape analysis nên là compiler infrastructure chính thức

Axiom nên có:

```text
Escape Analysis
```

ở MIR/optimization level.

Phân loại:

```text
NO_ESCAPE
LOCAL_ESCAPE
CALL_ESCAPE
RETURN_ESCAPE
GLOBAL_ESCAPE
FFI_ESCAPE
UNKNOWN_ESCAPE
```

Ví dụ:

```axiom
let x = Box.new(Foo(...))
use(x)
```

Nếu `use()` không giữ address:

```text
NO_ESCAPE
```

có thể eliminate allocation.

Nếu:

```axiom
return x
```

thì:

```text
RETURN_ESCAPE
```

nhưng vẫn có thể dùng caller allocation.

Nếu:

```axiom
ffi_send(address_of(x))
```

thì storage location trở thành observable.

Không được tùy tiện eliminate/move allocation nữa.

---

# 22. Đây là nguyên tắc cực kỳ quan trọng

> **Address observability creates a storage contract.**

Nếu programmer không quan sát address:

```text
compiler có rất nhiều freedom
```

Nếu programmer làm:

```axiom
let p = address_of(x)
```

thì:

```text
address trở thành observable
```

và optimizer bị giới hạn tương ứng.

Điều này cho phép Axiom vừa:

- abstraction cao
- compiler optimization mạnh
- vẫn làm systems programming.

---

# 23. External memory / FFI

Cần có abstraction riêng cho memory không thuộc ownership của Axiom.

Ví dụ:

```text
OS memory
C malloc
GPU buffer
memory mapped file
shared memory
device memory
```

Không nên giả vờ rằng tất cả đều là `Box<T>`.

Có thể có:

```text
External<T>
```

hoặc system-level view:

```axiom
unsafe {
    let v = view_from_raw(...)
}
```

Compiler biết:

```text
EXTERNAL / UNKNOWN provenance
```

và áp dụng conservative rules.

---

# 24. Memory model cuối cùng

Tôi đề xuất Axiom chốt thành:

```text
                    AXIOM VALUE
                         │
              ┌──────────┴──────────┐
              │                     │
          Non-owning             Owning
           capability              value
              │                     │
       ┌──────┴──────┐       ┌──────┴─────────┐
       │             │       │                │
     view         mut_view   inline          dynamic
                                          
                                      ┌────────┼─────────┐
                                      │        │         │
                                     Box      Vec      Arena/Pool
```

Và storage physical:

```text
                    Storage
                       │
       ┌───────┬───────┼────────┬────────┐
       │       │       │        │        │
    Register Stack   Inline    Heap    External
```

**Hai tầng này không được trộn lẫn.**

Đây là một quyết định kiến trúc rất quan trọng.

---

# 25. Stable Address không cần `Pin<T>` trong Core

Tôi nghiêng khá mạnh về:

```text
KHÔNG có Pin<T> trong Core v0.1
```

Thay bằng:

```text
Relocatable
StableAddress
```

và các storage abstraction:

```text
Box<T>       → stable
Arena<T>     → stable
Pool<T>      → stable tùy contract
Vec<T>       → relocatable
Array<T,N>   → inline, parent relocation semantics
```

Compiler quản lý dependency.

Điều này phù hợp hơn với triết lý Axiom:

> **Không bắt programmer học một hệ thống lifetime type riêng chỉ để nói "object này không được di chuyển".**

---

# 26. Các invariant mới

Tôi đề xuất bổ sung:

### AALLOC-01 — No Mandatory Heap
Safe language không yêu cầu heap allocation.

### AALLOC-02 — Storage Independence
Source-level value không mặc định gắn với stack/heap/register.

### AALLOC-03 — Allocation Strategy Independence
Allocator strategy không phải language semantic mặc định.

### AALLOC-04 — Explicit Dynamic Storage
Dynamic storage chỉ xuất hiện khi abstraction yêu cầu.

### AALLOC-05 — Stable Address Explicit
Stable address phải là semantic contract rõ ràng.

### AALLOC-06 — Relocation Explicit
Relocatable storage có thể thay đổi physical address.

### AALLOC-07 — Address Observability
Observable address hạn chế storage optimization tương ứng.

### AALLOC-08 — Allocation Elimination
Compiler được phép loại bỏ allocation nếu semantics không quan sát được.

### AALLOC-09 — Caller Allocation
Aggregate return có thể sử dụng caller-provided storage.

### AALLOC-10 — Arena Lifetime
Arena-owned storage không được escape khỏi Arena.

### AALLOC-11 — Pool Safety
Pool reuse không được tạo dangling capability trong safe code.

### AALLOC-12 — External Memory
External memory có provenance riêng và được kiểm soát conservative.

### AALLOC-13 — No Mandatory Compaction
Axiom không yêu cầu moving/compacting GC.

### AALLOC-14 — Fragmentation Strategy
Fragmentation được giải quyết bằng allocation strategy, không phải bằng memory model.

### AALLOC-15 — No Mandatory Object Header
Allocation không tự động chứa runtime header.

### AALLOC-16 — Semantic Allocation
`ALLOC/DEALLOC` trong MIR là semantic storage events, không mặc định là `malloc/free`.

---

## Kết luận thiết kế

Tôi nghĩ mô hình này hiện khá sạch:

```text
Axiom
│
├── Flat virtual address model
│
├── Value semantics
│
├── Ownership
│
├── view / mut_view
│
├── Compiler-managed lifetime
│
├── No mandatory GC
│
├── No mandatory heap
│
├── No mandatory object header
│
└── Storage abstractions
      ├── local/inline
      ├── Box
      ├── Vec
      ├── Arena
      ├── Pool/Slab
      └── External
```

Điểm tôi đặc biệt muốn giữ là:

> **Axiom không cố giải quyết memory bằng một cơ chế duy nhất.**

C không có safety.  
C++ có quá nhiều lifetime/ownership complexity.  
Rust đưa rất nhiều lifetime reasoning lên programmer.

Axiom nên đi theo hướng khác:

**Programmer mô tả ownership ở mức đơn giản → compiler suy luận lifetime/alias/escape → storage strategy được compiler/library lựa chọn → machine code cuối cùng chỉ còn những gì thực sự cần.**

Và đây cũng là nơi nguyên tắc **“Compiler Complexity Is Not Language Complexity”** phát huy mạnh nhất.

Bước tiếp theo hợp lý nhất là **thiết kế cụ thể `Box`, `Vec`, `Arena`, `Pool` và Allocator trait ở mức API/semantic**, bao gồm các thao tác `move`, `view`, `push`, `resize`, `remove`, relocation và cách compiler verifier xử lý từng trường hợp.