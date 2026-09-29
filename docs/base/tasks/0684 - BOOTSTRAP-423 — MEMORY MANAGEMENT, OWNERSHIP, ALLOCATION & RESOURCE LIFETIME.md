# BOOTSTRAP-423 — MEMORY MANAGEMENT, OWNERSHIP, ALLOCATION & RESOURCE LIFETIME

Tiếp tục **423**. Đây là task cần khóa rất cẩn thận vì nó quyết định Axiom có đạt được mục tiêu **native performance + đơn giản + không GC bắt buộc + không borrow checker bắt buộc** hay không.

---

## 423.1 — Mục tiêu thiết kế

Axiom memory management phải đồng thời đạt:

```text
Native performance
Deterministic destruction
No mandatory GC
No mandatory borrow checker
Low pointer/reference complexity
Explicit control when needed
Compiler optimization when possible
FFI compatibility
Freestanding capability
```

Mô hình nền:

```text
                Axiom Memory
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
      Stack         Heap          Static/TLS
        │            │
        │            └── Allocator
        │
        └── Scope lifetime
```

---

# 423.2 — Không có Garbage Collector bắt buộc

Axiom core **không có GC**.

Không có:

```text
GC thread
mark/sweep
moving collector
object header
write barrier
stop-the-world pause
```

trong chương trình bình thường.

Điều này giúp tránh:

- runtime overhead
- unpredictable pauses
- hidden allocations
- object headers
- GC-related memory traffic.

Nếu một library muốn reference counting/tracing GC, đó là **library/runtime feature**, không phải language requirement.

---

# 423.3 — Không có borrow checker bắt buộc

Axiom cũng không áp dụng mô hình:

```text
lifetime parameter
borrow checker
ownership lifetime inference
```

làm điều kiện bắt buộc cho mọi function.

Thay vào đó compiler dựa vào:

```text
ownership
move
copy
destructor
scope
escape analysis
alias analysis
unsafe boundary
```

Để kiểm soát resource.

---

# 423.4 — Ownership là khái niệm semantic nhẹ

Một value có thể có:

```text
Owned
Borrowed/View
Shared
Raw
```

Nhưng đây không nhất thiết phải trở thành 4 loại pointer khác nhau.

Mục tiêu là:

> **Ownership chủ yếu là property của value/resource flow, không phải một hệ thống reference syntax phức tạp.**

---

# 423.5 — Stack allocation

Local value mặc định được phép nằm trên stack:

```text id="0ryg6x"
fn foo() {
    x := Point(...)
}
```

Compiler có thể tạo:

```text id="3r72r6"
stack slot
```

hoặc register.

Không có guarantee rằng local variable luôn tồn tại trên stack.

---

# 423.6 — Register allocation

Nếu address không được lấy:

```text id="h5x82e"
x: i32
```

có thể hoàn toàn nằm trong register.

Compiler được phép:

```text id="s8yn8h"
stack → register
register → register
memory → register
```

theo optimization.

---

# 423.7 — Explicit heap allocation

Heap allocation phải explicit ở semantic/library level.

Ví dụ conceptual:

```text id="o5j8lc"
p := alloc<T>()
```

hoặc API library:

```text id="2y3gjr"
new<T>()
```

Tên syntax cuối cùng sẽ được khóa ở language/API task, nhưng invariant là:

> **Heap allocation không xảy ra âm thầm chỉ vì programmer tạo một ordinary struct.**

---

# 423.8 — No hidden heap allocation

Ví dụ:

```text id="g1xk7v"
struct Point {
    x: f32
    y: f32
}

p := Point{1, 2}
```

không tự động:

```text id="o8s9cz"
heap allocate
```

`p` là value bình thường.

---

# 423.9 — Allocator abstraction

Compiler không khóa allocator implementation.

Interface conceptual:

```text id="ezd2y6"
Allocator {
    alloc(size, alignment)
    dealloc(ptr, size, alignment)
    realloc(...)
}
```

Có thể có:

```text id="g4x2kg"
SystemAllocator
ArenaAllocator
PoolAllocator
StackAllocator
CustomAllocator
```

---

# 423.10 — Allocator không phải GC

Allocator:

```text id="aj1h0d"
alloc → memory
dealloc → memory returned
```

không theo dõi reachability.

Điều này khác hoàn toàn GC:

```text id="0o1xj5"
GC → determines reachability
```

Axiom mặc định dùng deterministic ownership/release.

---

# 423.11 — Move semantics

Khi value có resource ownership:

```text id="l8a2x4"
a := resource()
b := a
```

compiler phải biết assignment là:

```text id="j6h6zr"
copy
```

hay:

```text id="yqzhfd"
move
```

theo type semantics.

Resource-owning types mặc định nên có **move semantics**.

---

# 423.12 — Move không copy resource

Ví dụ:

```text id="o8dfx8"
file1 := open(...)
file2 := file1
```

không tạo duplicate OS handle.

Ownership chuyển:

```text id="6tsd3q"
file1 ──move──> file2
```

Sau move:

```text id="u5g7sp"
file1
```

không còn usable như owner.

---

# 423.13 — Moved-from state

Compiler phải phát hiện:

```text id="jfq9tx"
use-after-move
```

ở compile time khi có thể chứng minh.

Ví dụ:

```text id="d9j4r4"
a := resource()
b := move(a)
use(a)       // diagnostic
```

Đây **không phải borrow checker**.

Đây chỉ là **move-state analysis**.

---

# 423.14 — Copy semantics

Type nhỏ/trivially-copyable:

```text id="jyh1bk"
i32
f64
Point
```

có thể là `Copy`.

Copy nghĩa:

```text id="d8f4hr"
destination gets independent value
```

không chuyển ownership.

---

# 423.15 — Copy trait/property

Conceptual:

```text id="l0g43r"
Copy
```

là type capability.

Một type chỉ được implicit copy nếu compiler chứng minh/có declaration rằng copy semantics hợp lệ.

Resource handle không nên tự động là Copy.

---

# 423.16 — Clone

Copy và clone phải khác nhau.

```text id="3az0al"
copy
```

→ cheap bit/value duplication.

```text id="tv3viy"
clone
```

→ potentially expensive semantic duplication.

Ví dụ String:

```text id="2vq6nd"
copy String
```

không nhất thiết duplicate bytes.

Trong khi:

```text id="j5qzxf"
clone String
```

có thể allocate/copy UTF-8 data.

---

# 423.17 — Destructor

Resource-owning type có thể định nghĩa destructor:

```text id="r1d5zq"
drop
```

Destructor được gọi khi ownership kết thúc.

Ví dụ:

```text id="8v6u6o"
File
Socket
MutexGuard
Buffer
```

---

# 423.18 — Destructor deterministic

Không có GC nghĩa là:

```text id="0j5p2n"
scope end
   ↓
destructor
```

có thời điểm xác định.

Đây là điểm quan trọng cho:

- file handles
- sockets
- locks
- temporary buffers
- GPU resources
- OS handles.

---

# 423.19 — Scope cleanup

Ví dụ:

```text id="5w3a8c"
fn foo() {
    file := open(...)
    ...
}
```

Compiler tạo:

```text id="6kq0gt"
open
 ↓
body
 ↓
drop(file)
 ↓
return
```

Không cần runtime GC.

---

# 423.20 — Multiple exits

Nếu:

```text id="zqj8qf"
if condition {
    return
}
```

compiler vẫn phải đảm bảo cleanup:

```text id="90xq52"
return path A → cleanup → return
return path B → cleanup → return
```

Không được duplicate cleanup unnecessarily nếu backend có thể share cleanup block.

---

# 423.21 — `defer`

Axiom có thể cung cấp:

```text id="w2ukla"
defer expression
```

cho cleanup hoặc scope-exit actions.

Conceptual:

```text id="h26q1r"
defer close(file)
```

được lower thành cleanup action.

`defer` không phải GC.

---

# 423.22 — Destructor + defer

Thứ tự phải deterministic.

Conceptual:

```text id="h6p3vl"
defer A
defer B

local C with destructor
```

scope exit:

```text id="f0ng2u"
B
A
C destructor
```

hoặc một ordering khác được language specification khóa.

**Cần một rule duy nhất**, không để backend tự chọn.

---

# 423.23 — Recommended cleanup ordering

Để dễ reasoning:

```text id="zv0x5n"
explicit defer actions
      ↓
local destructors
      ↓
scope exit
```

Trong mỗi category, thực hiện reverse declaration/registration order.

Điều này tạo mô hình gần RAII nhưng không yêu cầu class/object hierarchy.

---

# 423.24 — RAII-like behavior

Axiom có thể đạt RAII:

```text id="u4uy5p"
resource created
      ↓
scope ownership
      ↓
deterministic drop
```

mà không cần:

```text id="jrh5wx"
class
constructor
destructor hierarchy
```

Ví dụ struct:

```text id="xg9d8y"
struct File {
    handle: Handle
}

fn drop(self: File) {
    close(self.handle)
}
```

---

# 423.25 — Struct-based resource model

Điều này phù hợp trực tiếp với thiết kế:

> **Struct + function thay cho class.**

Resource lifecycle chỉ cần:

```text id="7l2f0x"
struct File
fn open(...)
fn read(self: ...)
fn close(self: ...)
fn drop(self: ...)
```

Không cần object runtime.

---

# 423.26 — Ownership transfer

Function:

```text id="9th4i5"
fn consume(file: File)
```

có thể consume ownership.

Caller:

```text id="2h5w4s"
consume(file)
```

sau đó:

```text id="k3c8w0"
file
```

được xem là moved.

---

# 423.27 — Borrow/view

Khi chỉ cần sử dụng tạm:

```text id="6q1w5f"
fn read(file: &File)
```

hoặc syntax view tương đương có thể biểu diễn non-owning access.

Nhưng Axiom không yêu cầu programmer phải annotate lifetime:

```text
'a
'b
'static
```

cho mọi borrow.

---

# 423.28 — View lifetime

Compiler chỉ cần đảm bảo một view không được sử dụng sau owner khi điều đó có thể xác định statically.

Ví dụ:

```text id="c2e2g6"
file := open()
view := file.view()

use(view)
```

hợp lệ.

Nếu:

```text id="w6s1jm"
file = moved_elsewhere
use(view)
```

compiler có thể reject nếu dependency được tracking.

---

# 423.29 — Lightweight lifetime tracking

Đây là **flow analysis**, không phải borrow checker đầy đủ.

Compiler tracking:

```text id="w1d7km"
Created
Live
Moved
Destroyed
```

cho owner values.

Views có dependency:

```text id="j0a0h1"
view → owner
```

Chỉ cần kiểm tra các path có thể chứng minh invalid.

---

# 423.30 — Không yêu cầu lifetime annotations

Không có:

```text id="5j0h5j"
fn foo<'a>(x: &'a T) -> &'a T
```

trong core syntax.

Compiler tự infer lifetime khi có thể.

Nếu không chứng minh được:

```text id="9m7p5m"
diagnostic
```

hoặc programmer chuyển sang explicit unsafe/raw mechanism.

---

# 423.31 — Shared read access

Nhiều view read-only có thể tồn tại đồng thời:

```text id="7c7l0h"
owner
 ├── read view
 ├── read view
 └── read view
```

Compiler không cần reference counting.

---

# 423.32 — Mutable access

Mutable view:

```text id="2b6x1v"
&mut T
```

nếu syntax này được giữ, phải có exclusive-access semantics trong phạm vi compiler có thể kiểm tra.

Nhưng không biến toàn bộ Axiom thành Rust-like lifetime system.

---

# 423.33 — Raw pointers

Low-level:

```text id="o8b1t7"
*T
```

được phép bypass ownership analysis trong `unsafe`.

Ví dụ:

```text id="4q9z6h"
unsafe {
    p = raw_pointer(...)
    ...
}
```

Compiler không giả vờ chứng minh safety mà programmer đã explicit bypass.

---

# 423.34 — Unsafe boundary

Unsafe chỉ cần cho operations như:

```text id="2w9j3b"
raw dereference
manual allocation
manual deallocation
FFI with unchecked contracts
volatile/MMIO
pointer arithmetic
```

Không cần unsafe cho:

```text id="j5z2a5"
ordinary struct
normal array
normal function call
normal local variable
```

---

# 423.35 — Double free

Nếu compiler có ownership knowledge:

```text id="u4p3fj"
free(p)
free(p)
```

có thể detect compile-time khi flow đơn giản.

Nếu xảy ra trong raw unsafe code và không thể chứng minh:

```text id="0k9n1d"
undefined behavior
```

the same class of native memory violation applies.

---

# 423.36 — Use-after-free

Normal ownership-managed value:

```text id="i9svy7"
owner destroyed
```

sau đó use phải bị compiler reject nếu detectable.

Raw pointer:

```text id="h3t3v4"
*p
```

sau lifetime kết thúc:

```text id="q0lq8k"
undefined behavior
```

---

# 423.37 — Dangling pointer

Axiom không tự động null hóa pointer sau free.

Điều đó:

- tạo overhead;
- che giấu bug;
- phá native semantics.

Pointer trở thành invalid theo lifetime semantics.

---

# 423.38 — No hidden reference counting

Ordinary:

```text id="a6kqj3"
String
Buffer
Array
```

không tự động có:

```text id="72c5k1"
atomic refcount
```

nếu type/library không yêu cầu.

Reference counting là explicit abstraction:

```text id="j8xw9g"
Arc<T>
Shared<T>
Rc<T>
```

nếu library cung cấp.

---

# 423.39 — Reference counting as library

Nếu dùng:

```text id="i0xq1c"
Shared<T>
```

thì representation có thể:

```text id="t5s6s1"
data pointer
control block
strong count
weak count
```

Nhưng đây là library implementation, không phải compiler object header.

---

# 423.40 — Arena allocation

Axiom phải thân thiện với arena:

```text id="4q7t4h"
arena := Arena(...)
x := arena.alloc(...)
y := arena.alloc(...)
```

Khi arena kết thúc:

```text id="8r8l2w"
all memory released
```

một lần.

Compiler không cần destructor cho từng allocation nếu arena semantics quản lý bulk lifetime.

---

# 423.41 — Pool allocation

Pool:

```text id="0m6f9f"
Pool<T>
```

cho phép:

```text id="0m5x2e"
allocate
reuse
release
```

với fixed-size objects.

Đây là library/allocator concern.

---

# 423.42 — Stack allocator

Có thể có:

```text id="f3l7y4"
StackArena
```

với:

```text id="s6c6d7"
checkpoint
allocate
rollback
```

Useful cho:

- parsers
- compilers
- frame temporaries
- game workloads.

---

# 423.43 — Allocation elision

Nếu:

```text id="k8f3h7"
alloc()
use()
free()
```

không escape:

compiler có thể biến thành:

```text id="p0q0l9"
stack/register
```

hoặc loại bỏ hoàn toàn allocation.

---

# 423.44 — Escape analysis

Compiler phân loại:

```text id="9w8ycr"
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

Ví dụ:

```text id="4kjp0w"
allocate()
use()
free()
```

→ `NoEscape`.

Nếu return pointer:

```text id="j0xg86"
return p
```

→ `FunctionEscape`.

---

# 423.45 — Stack promotion

NoEscape allocation có thể:

```text id="k78qg2"
heap → stack
```

nếu stack lifetime đủ dài.

Nếu object chỉ tồn tại trong register:

```text id="0u5m9g"
heap → register/scalar
```

---

# 423.46 — Allocation failure

Allocator API phải định nghĩa failure:

```text id="7l2w9z"
AllocationResult
```

có thể:

```text id="5e5m5n"
success
failure
```

Axiom core không ép mọi allocation phải panic.

---

# 423.47 — OOM policy

Target/application có thể chọn:

```text id="kz8x7q"
return error
panic
abort
custom handler
```

Compiler không tự chèn một global OOM runtime nếu program không yêu cầu.

---

# 423.48 — Zero-size allocation

`alloc(0)` phải có specification.

Recommended:

```text id="7r8z7f"
zero-size allocation may return a non-dereferenceable unique sentinel
```

và:

```text id="4y8q7m"
dealloc(zero-size)
```

phải có matching allocator semantics.

Không được dereference pointer từ zero-size allocation.

---

# 423.49 — Alignment allocation

Allocator API:

```text id="3c6xq8"
alloc(size, alignment)
```

phải tôn trọng:

```text id="slv9hr"
alignment = power-of-two
```

nếu target allocator model yêu cầu.

---

# 423.50 — Reallocation

```text id="w4h4f8"
realloc(ptr, old_size, new_size, alignment)
```

có thể:

```text id="2e4g3j"
resize in place
```

hoặc:

```text id="8v2s3r"
allocate + copy + free
```

Semantic contract phải xác định pointer validity sau realloc.

---

# 423.51 — Destructor ordering

Nested scopes:

```text id="7g2x9f"
A created
B created
C created
```

scope exit:

```text id="h0x1as"
C.drop()
B.drop()
A.drop()
```

Reverse acquisition order là default.

Điều này tạo deterministic cleanup dễ hiểu.

---

# 423.52 — Partial initialization

Struct:

```text id="5u4r3d"
S {
    a
    b
    c
}
```

nếu construction fail giữa chừng, compiler phải biết field nào đã initialized.

Cleanup chỉ chạy trên phần đã initialized.

Không được gọi destructor trên uninitialized memory.

---

# 423.53 — Conditional initialization

Compiler IR cần:

```text id="b0y4t8"
InitState
```

để track:

```text id="3o2x2m"
uninitialized
partially initialized
initialized
moved
destroyed
```

Điều này cũng hỗ trợ diagnostics.

---

# 423.54 — Panic/unwind

Nếu Axiom dùng unwind:

```text id="z9g2z5"
panic
 ↓
cleanup
 ↓
unwind
```

mọi owned local phải được cleanup đúng thứ tự.

Nếu build mode là:

```text id="n4n7b8"
panic = abort
```

không cần unwind machinery.

---

# 423.55 — Abort mode

Freestanding/minimal binaries có thể chọn:

```text id="w6k8h3"
panic = abort
```

Khi panic:

```text id="v3o5r4"
terminate
```

không cần:

- exception tables
- unwinder
- large runtime.

Điều này giúp binary nhỏ.

---

# 423.56 — Resource types

Ownership không chỉ dành cho memory.

Các resource:

```text id="1k8v4m"
File
Socket
Mutex
Thread
GPUBuffer
Window
OSHandle
MappedMemory
```

đều có thể có deterministic destructor.

Do đó mô hình ownership trở thành:

```text id="0r2w8s"
resource lifetime
```

thay vì chỉ:

```text id="y1x7g2"
heap memory
```

---

# 423.57 — Thread ownership

Thread handle có thể là owning resource:

```text id="v5w1o7"
thread := spawn(...)
```

Scope exit policy phải được type/library định nghĩa:

```text id="3c4r5v"
join
detach
terminate
```

Compiler không tự đoán.

---

# 423.58 — Send/share

Concurrency task sau này sẽ định nghĩa đầy đủ:

```text id="6q9j8y"
Send
Share
```

Nhưng memory-management architecture phải cho phép type khai báo:

```text id="m1m4y6"
safe to transfer
safe to share
not transferable
```

Compiler có thể kiểm tra khi crossing thread boundary.

---

# 423.59 — FFI ownership

FFI:

```text id="k3j8w0"
extern "c" fn malloc(...)
extern "c" fn free(...)
```

không tự động tạo ownership semantics.

Programmer/library phải khai báo contract.

Ví dụ:

```text id="s4v2n6"
malloc → returns owned memory
free   → consumes ownership
```

---

# 423.60 — C malloc/free

Axiom wrapper có thể định nghĩa:

```text id="5s7f0n"
fn c_alloc(...)
fn c_free(...)
```

và map ownership explicitly.

Compiler không được assume mọi pointer returned từ C phải được freed bởi Axiom.

---

# 423.61 — Ownership annotations

Có thể có FFI metadata:

```text id="8j7v6d"
@owned
@borrowed
@consumes
@returns_owned
```

Đây chủ yếu là **contract metadata**.

Không cần biến chúng thành một lifetime type system đầy đủ.

---

# 423.62 — Compiler ownership analysis

Core flow state:

```text id="0z7f4x"
ValueState:
    Uninitialized
    Owned
    Borrowed
    Moved
    Destroyed
```

Compiler tracking phải flow-sensitive.

---

# 423.63 — Ownership merge

Branch:

```text id="w6y2q1"
if condition {
    move(x)
}
use(x)
```

Compiler thấy:

```text id="c4v6n2"
path A → Moved
path B → Owned
```

Sau merge:

```text id="r3f8m0"
x = MaybeMoved
```

`use(x)` phải diagnostic nếu semantics không cho phép.

---

# 423.64 — Loop ownership

Loop analysis phải hỗ trợ:

```text id="j7v5q8"
move
reinitialize
reuse
```

Compiler không được reject hợp lệ chỉ vì analysis quá đơn giản.

Nếu không chứng minh được:

```text id="a9w3p2"
conservative diagnostic
```

có thể xảy ra trong bootstrap compiler.

---

# 423.65 — Ownership optimization

Ownership information có thể feed vào optimizer:

```text id="p0j2w7"
unique owner
      ↓
no competing owner
      ↓
stronger alias analysis
```

Nhưng compiler chỉ được sử dụng assumption khi language semantics bảo đảm nó.

---

# 423.66 — No mandatory runtime ownership tracking

Sau compilation, ownership state không cần tồn tại:

```text id="b4m6y1"
runtime ownership table = none
```

trong normal native program.

Ownership là compile-time/resource-lifetime concept.

Đây là điểm then chốt để tránh overhead.

---

# 423.67 — Memory manager architecture

Axiom compiler:

```text id="m4q5w6"
Ownership Analysis
        ↓
Lifetime Analysis
        ↓
Escape Analysis
        ↓
Cleanup Insertion
        ↓
Optimization
        ↓
Machine Code
```

Runtime:

```text id="8x7z9c"
Allocator
Resource APIs
OS
```

Không có GC daemon ở giữa.

---

# 423.68 — Cleanup insertion

Compiler IR cần explicit instructions:

```text id="v7k1s4"
ALLOC
MOVE
BORROW
END_BORROW
DROP
FREE
```

Nhưng nhiều instruction có thể bị optimize away.

Ví dụ:

```text id="m3n8p1"
ALLOC
...
FREE
```

→ stack/register promotion.

---

# 423.69 — Drop elaboration

Source:

```text id="h4s7d2"
scope exit
```

compiler biến thành:

```text id="q8x2v5"
Drop(file)
Drop(buffer)
```

trước machine code generation.

Do đó machine backend không cần hiểu high-level ownership.

---

# 423.70 — Drop glue

Nested type:

```text id="e4r5t6"
struct A {
    file: File
    buffer: Buffer
}
```

compiler-generated drop:

```text id="f5g6h7"
drop(A):
    drop(buffer)
    drop(file)
```

Không cần programmer viết destructor cho từng field nếu default recursive drop đủ.

---

# 423.71 — Custom destructor

Nếu programmer định nghĩa:

```text id="c7d8e9"
fn drop(self: A)
```

compiler phải áp dụng một rule duy nhất:

- custom drop chịu trách nhiệm toàn bộ,
- hoặc custom body + compiler-generated field cleanup.

Khuyến nghị:

> Custom destructor là phần logic trước; compiler vẫn đảm bảo field-owned resources được cleanup đúng semantics.

Cần khóa chính xác ở language task để tránh double-drop.

---

# 423.72 — Double-drop prevention

Compiler phải đảm bảo:

```text id="r7s8t9"
Drop(x)
Drop(x)
```

không xảy ra trong generated normal cleanup.

Move state giúp:

```text id="u8v9w0"
move(x)
```

vô hiệu hóa cleanup owner cũ.

---

# 423.73 — Resource transfer through return

```text id="e1f2g3"
fn create() -> File
```

ownership:

```text id="h2i3j4"
callee
   ↓ return
caller
```

không cần copy.

Compiler có thể dùng:

```text id="k3l4m5"
return-value optimization
```

để construct trực tiếp tại destination.

---

# 423.74 — NRVO / RVO

Axiom backend nên hỗ trợ:

```text id="n4o5p6"
return value
```

→ construct trực tiếp vào caller-provided return location khi ABI cho phép.

Điều này giảm:

```text id="q5r6s7"
copy
move
temporary allocation
```

---

# 423.75 — Temporary lifetime

Temporary values phải có lifetime xác định.

Ví dụ:

```text id="t6u7v8"
foo(make_resource())
```

resource temporary sống đủ lâu để call hoàn tất.

Sau đó:

```text id="w7x8y9"
drop
```

nếu không transferred.

---

# 423.76 — Exception-safe resource handling

Nếu operation fail:

```text id="z8a9b0"
create A
create B
operation fails
```

compiler cleanup:

```text id="c9d0e1"
drop(B)
drop(A)
```

Không được leak resource đã successfully acquired.

---

# 423.77 — Memory leak semantics

Memory leak không nhất thiết là compiler UB.

Ví dụ process intentionally giữ allocation tới exit:

```text id="f0g1h2"
global cache
```

có thể hợp lệ.

Axiom không yêu cầu mọi allocation phải được reclaimed trước process termination.

---

# 423.78 — Lifetime ends versus memory reclaimed

Phải phân biệt:

```text id="i1j2k3"
object lifetime ends
```

và:

```text id="l2m3n4"
physical memory returned
```

Một arena có thể:

```text id="o3p4q5"
destroy logical objects
```

mà reclaim entire region một lần.

---

# 423.79 — Memory fragmentation

Axiom language không hứa allocator nào cũng tránh fragmentation.

Thay vào đó architecture cho phép lựa chọn:

```text id="r4s5t6"
arena
pool
slab
bump allocator
system allocator
custom allocator
```

Programmer chọn theo workload.

---

# 423.80 — Flat memory model

Ta **không khóa “flat memory model” như một language-wide allocation strategy**.

Lý do:

```text id="u5v6w7"
CPU virtual memory
OS pages
NUMA
TLS
MMIO
GPU memory
```

có semantics khác nhau.

Thay vào đó Axiom dùng:

```text id="x6y7z8"
flat value representation
+
explicit addressable memory
+
pluggable allocator
```

Điều này giữ ưu điểm đơn giản mà không ép compiler vào một memory topology giả tạo.

---

# 423.81 — Cache locality

Compiler có thể optimize:

```text id="a7b8c9"
struct layout
array layout
field access
loop order
```

nhưng không tự ý reorder fields của layout-observable struct.

Data-oriented structures có thể dùng:

```text id="d8e9f0"
Array<T>
Slice<T>
SoA
AoS
```

ở library/type level.

---

# 423.82 — Ownership + SoA

Ví dụ:

```text id="g0h1i2"
struct Particles {
    positions: []Vec3
    velocities: []Vec3
}
```

mỗi buffer có ownership riêng.

Không cần:

```text id="j1k2l3"
GC object graph
```

---

# 423.83 — Memory management and AI-friendly syntax

Do mục tiêu Axiom là AI-friendly, syntax không nên yêu cầu AI phải xử lý hàng loạt lifetime annotations.

Ưu tiên:

```text id="m2n3o4"
value
move
copy
view
unsafe
```

thay vì:

```text id="p3q4r5"
lifetime parameter explosion
```

Compiler diagnostics phải nói rõ:

```text id="s4t5u6"
"value `x` was moved here"
"cannot use `x` after move"
```

thay vì lỗi ABI/compiler nội bộ khó hiểu.

---

# 423.84 — Safety/performance balance

Axiom memory model chọn:

```text id="v5w6x7"
Safe by default
Explicit ownership
Deterministic destruction
No GC
No mandatory borrow checker
Unsafe escape hatch
Aggressive optimization
```

Đây là điểm cân bằng giữa:

```text id="y6z7a8"
C/C++ freedom
```

và:

```text id="b7c8d9"
modern compiler lifetime reasoning
```

mà không sao chép nguyên mô hình Rust.

---

# 423.85 — Compiler implementation layers

Memory management implementation:

```text id="e8f9g0"
Semantic Analyzer
       ↓
Move Analysis
       ↓
Ownership Analysis
       ↓
Lifetime Analysis
       ↓
Escape Analysis
       ↓
Drop Elaboration
       ↓
Alias Analysis
       ↓
Optimizer
       ↓
MIR
```

Không đưa các pass này vào machine backend.

---

# 423.86 — Diagnostics

Compiler phải có ít nhất:

```text id="i9j0k1"
UseAfterMove
DoubleMove
InvalidBorrow
BorrowEscapesOwner
UseAfterDestroy
DoubleDestroy
InvalidFree
InvalidAllocator
AllocationAlignmentError
DestructorCycle
PartialInitializationError
```

Một số lỗi chỉ có thể phát hiện runtime/unsafe boundary.

Compiler phải phân biệt:

```text id="l0m1n2"
compile-time error
runtime error
undefined behavior
```

---

# 423.87 — Optimization contract

Ownership information có thể cho optimizer:

```text id="o1p2q3"
unique
readonly
noescape
noalias
```

nhưng chỉ khi semantics chứng minh.

Compiler không được biến:

```text id="r2s3t4"
"probably unique"
```

thành:

```text id="u3v4w5"
guaranteed unique
```

---

# 423.88 — FFI resource contracts

Ví dụ:

```text id="x4y5z6"
extern "c" @returns_owned
fn create_handle() -> Handle
```

Axiom library wrapper có thể biến raw external handle thành owning type:

```text id="a5b6c7"
Handle
```

với destructor:

```text id="d6e7f8"
close_handle
```

Nhờ vậy unsafe FFI chỉ nằm ở boundary.

---

# 423.89 — C compatibility

Một wrapper:

```text id="g7h8i9"
struct Buffer {
    ptr: *u8
    len: usize
}
```

có thể map trực tiếp tới C struct nếu:

```text id="j8k9l0"
@repr(C)
```

và ownership contract được xử lý ở Axiom layer.

---

# 423.90 — Thread interaction

Ownership system không tự động giải quyết data races.

Concurrency model sau này sẽ quy định:

```text id="m9n0o1"
mutable shared state
atomic
mutex
channel
thread transfer
```

423 chỉ cung cấp foundation:

```text id="p0q1r2"
who owns resource?
```

---

# 423.91 — Compiler-generated cleanup example

Conceptual source:

```text id="s1t2u3"
fn process() {
    a := open_a()
    b := open_b()

    work(a, b)
}
```

MIR:

```text id="v2w3x4"
a = acquire A
b = acquire B

call work(a, b)

drop b
drop a
return
```

Machine backend không cần biết `File` hay `Socket` là gì.

---

# 423.92 — Early return example

```text id="y3z4a5"
fn process() {
    a := acquire()

    if failed() {
        return
    }

    use(a)
}
```

Lower:

```text id="b4c5d6"
acquire a

if failed:
    drop a
    return

use a
drop a
return
```

Optimizer có thể merge cleanup blocks.

---

# 423.93 — Move example

```text id="e5f6g7"
fn transfer() -> Resource {
    a := acquire()
    return a
}
```

Compiler:

```text id="h6i7j8"
acquire
 ↓
return ownership
```

Không:

```text id="k7l8m9"
acquire
copy
drop original
```

nếu ABI/RVO cho phép direct transfer.

---

# 423.94 — Copy example

```text id="n8o9p0"
a := Point{1, 2}
b := a
```

nếu `Point: Copy`:

```text id="q9r0s1"
b = copy(a)
```

Không có ownership transfer.

---

# 423.95 — Explicit clone

```text id="t0u1v2"
b := clone(a)
```

có thể thực hiện allocation.

Compiler phải không giả định clone là cheap.

---

# 423.96 — Memory-management ABI boundary

423 kết nối:

```text id="w1x2y3"
Ownership
    ↓
Drop elaboration
    ↓
ABI
```

Ví dụ return owning object:

```text id="z2a3b4"
ownership transfer
```

không nhất thiết yêu cầu runtime bookkeeping.

ABI chỉ truyền representation.

---

# 423.97 — Final architecture

Axiom memory system:

```text id="c3d4e5"
                  VALUE
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
      Copy         Move       View
        │           │           │
        │           ▼           │
        │        Ownership      │
        │           │           │
        │           ▼           │
        │       Lifetime        │
        │           │           │
        └───────────┼───────────┘
                    ▼
             Drop / Cleanup
                    │
             ┌──────┴──────┐
             ▼             ▼
           Stack          Heap
                           │
                       Allocator
```

---

# 423.98 — Hard invariants

BOOTSTRAP-423 khóa các nguyên tắc:

1. **Không GC bắt buộc.**
2. **Không borrow checker bắt buộc.**
3. Ordinary value không tự động heap allocate.
4. Resource-owning values có deterministic destruction.
5. Move không copy resource.
6. Copy chỉ dành cho type có copy semantics.
7. Clone là explicit semantic duplication.
8. Raw pointer chỉ bypass safety trong explicit low-level boundary.
9. Ownership không tạo runtime bookkeeping mặc định.
10. Allocator là pluggable.
11. Arena/pool/custom allocator được hỗ trợ.
12. Compiler được phép stack-promote/elide allocation.
13. Escape analysis là optimization quan trọng.
14. FFI ownership phải explicit.
15. Layout/ABI không được phụ thuộc vào GC/object headers.
16. Cleanup phải deterministic.
17. Panic/unwind phải cleanup đúng ownership.
18. Freestanding mode không yêu cầu runtime allocator/GC.

---

# 423.99 — Completion criteria

**BOOTSTRAP-423 được xem là hoàn tất ở mức specification khi đã khóa:**

- allocation model
- ownership
- move
- copy
- clone
- destructor
- scope cleanup
- defer
- partial initialization
- ownership flow analysis
- lightweight view/lifetime analysis
- raw pointer/unsafe boundary
- allocator abstraction
- arena/pool support
- escape analysis
- allocation elimination
- OOM policy
- FFI ownership
- resource lifetime
- panic cleanup
- concurrency boundary
- optimizer interaction.

### Kết luận kiến trúc

Axiom **không đi theo C++ thuần túy** với manual memory everywhere, nhưng cũng **không đi theo Rust với borrow checker/lifetime system là trung tâm của ngôn ngữ**.

Mô hình được khóa là:

> **Explicit ownership + move semantics + deterministic destruction + lightweight flow analysis + aggressive compiler optimization + unsafe escape hatch.**

Đây là nền tảng phù hợp hơn với mục tiêu **đơn giản, native, hiệu năng cao và AI-friendly** của Axiom.

---

# BOOTSTRAP-424 — CONCURRENCY, THREAD, ATOMIC & ASYNC EXECUTION MODEL

Task tiếp theo sẽ giải quyết phần mà trước đây ta đã nhiều lần đề cập: **thread/async phải đơn giản hơn các mô hình hiện nay nhưng vẫn đạt native performance**.

Chuỗi 424:

```text
424.1   concurrency goals
424.2   OS threads
424.3   thread creation
424.4   thread lifecycle
424.5   join
424.6   detach
424.7   thread ownership
424.8   thread-local storage
424.9   atomic types
424.10  atomic operations
424.11  memory ordering
424.12  mutex
424.13  rwlock
424.14  semaphore
424.15  condition variable
424.16  spinlock
424.17  channels
424.18  message passing
424.19  Send/Share semantics
424.20  data-race model
424.21  shared mutable state
424.22  lock-free programming
424.23  wait-free considerations
424.24  task abstraction
424.25  async model
424.26  coroutine model
424.27  executor
424.28  scheduler
424.29  async I/O
424.30  cancellation
424.31  structured concurrency
424.32  blocking vs async
424.33  stackful vs stackless
424.34  state-machine lowering
424.35  zero-cost async path
424.36  thread pool
424.37  work stealing
424.38  CPU affinity
424.39  NUMA awareness
424.40  GPU/CPU boundary
424.41  synchronization ABI
424.42  OS primitives
424.43  freestanding mode
424.44  embedded mode
424.45  concurrency diagnostics
424.46  race semantics
424.47  optimizer interaction
424.48  concurrency tests
424.49  performance requirements
424.50  final concurrency contract
```

**BOOTSTRAP-424 là task kế tiếp; numbering tiếp tục từ đây.**