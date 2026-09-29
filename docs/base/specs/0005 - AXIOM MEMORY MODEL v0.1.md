Được. Tôi sẽ đi tiếp theo hướng **đóng spec thật sự**, không chỉ mô tả ý tưởng. Phần cần khóa đầu tiên là **Memory Model**, vì Type System, Concurrency và MIR đều phụ thuộc nó.

# AXIOM MEMORY MODEL v0.1

**Status:** FROZEN  
**Layer:** Language Semantics  
**Depends on:** Axiom Core v0.1  
**Used by:** Type System, Concurrency Model, Compiler IR

---

## 1. Memory philosophy

Axiom sử dụng mô hình:

> **Value semantics + ownership semantics + compiler-managed lifetime + explicit unsafe memory access.**

Axiom **không** sử dụng làm mặc định:

- tracing GC
- implicit reference counting
- mandatory object header
- mandatory heap allocation
- mandatory runtime
- programmer-written lifetime annotations
- programmer-written borrow annotations

Mục tiêu:

```text
Simple source
     ↓
Compiler proves lifetime/safety
     ↓
Deterministic native code
```

---

# 2. Storage không phải là Type

Một type không được mặc định gắn với:

```text
stack
heap
register
static
```

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Compiler có thể đặt `Point`:

```text
register
stack
inline inside another object
heap
static memory
```

miễn semantics không thay đổi.

### MM-001

> Storage location MUST NOT be observable by safe Axiom code, ngoại trừ các API/system operation được khai báo rõ là phụ thuộc storage/address.

---

# 3. Value

Mọi giá trị thông thường là một **value**.

```axiom
let a = 42
let b = a
```

`a` và `b` có semantic identity độc lập.

Compiler có thể tối ưu:

```text
a → register R1
b → register R1
```

nhưng điều này không biến chúng thành alias.

### MM-002

> Copying a value MUST NOT implicitly create shared mutable aliasing.

---

# 4. Copy

Một type có property `Copy` nếu việc sao chép nó không tạo ra hai ownership obligation độc lập.

Ví dụ:

```text
i32
f32
bool
```

là `Copy`.

Một struct chỉ chứa các field `Copy` có thể tự động trở thành `Copy`.

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

có thể:

```text
Point : Copy
```

---

# 5. Move

Owning value có thể được move.

```axiom
let a = Buffer(...)
let b = a
```

semantic:

```text
a ──ownership──> resource

        move

b ──ownership──> resource
a ──invalid─────>
```

Sau move:

```axiom
use(a)
```

là compile error.

### MM-003

> A moved value MUST NOT be used as a valid value after the move.

---

# 6. Move không nhất thiết tạo machine-level copy

Ví dụ:

```axiom
let b = a
```

không có nghĩa compiler phải thực hiện:

```asm
memcpy(...)
```

Move có thể chỉ là:

```text
ownership state:
a → invalid
b → valid
```

Nếu resource đã nằm ở register/stack, compiler có thể chỉ đổi ownership metadata.

---

# 7. Drop

Type có resource lifetime có thể có `Drop`.

Ví dụ:

```axiom
let file = File.open(...)
```

khi lifetime kết thúc:

```text
drop(file)
```

được thực hiện.

### MM-004

> Axiom MUST provide deterministic resource release for owning values.

Nhưng:

> `drop` không đồng nghĩa `free`.

Một `Drop` có thể:

```text
close file
release lock
release GPU resource
return object to pool
decrement explicit shared counter
do nothing
```

---

# 8. Drop elaboration

Source:

```axiom
fn foo() {
    let a = ResourceA()
    let b = ResourceB()

    work()
}
```

MIR có thể trở thành:

```text
BB0:
    a = create ResourceA
    b = create ResourceB

    call work()

    drop b
    drop a

    return
```

Thứ tự mặc định:

> **Reverse declaration order.**

Tương tự nguyên tắc stack unwinding nhưng **không cần exception system**.

---

# 9. Early return

```axiom
fn foo() -> Result {
    let a = ResourceA()

    if condition {
        return error
    }

    ...
}
```

Compiler phải đảm bảo:

```text
condition
   ↓
drop(a)
   ↓
return error
```

Không được leak resource trong safe code.

---

# 10. Panic/trap

Nếu Axiom có:

```axiom
panic(...)
```

compiler phải xác định profile của chương trình.

Có thể có:

```text
panic = terminate
panic = unwind
panic = custom handler
```

Nhưng Memory Model phải đảm bảo rằng **nếu profile sử dụng unwinding**, owning resources vẫn được xử lý đúng.

---

# 11. View

Đây là abstraction quan trọng nhất để giảm pointer/reference syntax.

Conceptually:

```text
view<T>
```

là:

```text
address + extent
```

nhưng:

- không sở hữu data
- không được destroy data
- không được outlive owner
- compiler kiểm tra lifetime

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32
```

---

# 12. Mutable View

Conceptually:

```text
mut_view<T>
```

cho phép mutation.

```axiom
fn fill(v: mut_view<i32>, value: i32)
```

Trong safe code:

```text
many view<T>
```

được phép cùng tồn tại.

Nhưng:

```text
mut_view<T>
```

không được đồng thời conflict với access khác.

---

# 13. View không phải object

Một view không cần:

```text
refcount
GC metadata
type ID
vtable
object header
```

Nó có thể chỉ là:

```text
(pointer, length)
```

hoặc representation tối ưu khác.

---

# 14. Lifetime của View

Ví dụ:

```axiom
fn get_view() -> view<i32> {
    let data = [1, 2, 3]
    return data
}
```

Nếu `data` là local storage, compiler phải reject:

```text
view escapes owner lifetime
```

Đây là compile-time error.

Không cần programmer viết lifetime annotation.

---

# 15. Escape analysis

Compiler phải theo dõi:

```text
local
 ↓
view
 ↓
return?
store?
global?
spawn?
closure?
```

Nếu lifetime không đủ:

```text
compile error
```

Nếu compiler chứng minh được an toàn:

```text
allow
```

---

# 16. Ownership graph

Compiler có thể nội bộ xây:

```text
Owner A
 │
 ├── View B
 │
 ├── View C
 │
 └── Owned D
```

Nhưng graph này **không phải runtime object**.

Đây là compiler analysis.

---

# 17. Shared ownership

Axiom Core cho phép shared ownership, nhưng Memory Model v0.1 quy định:

> Shared ownership MUST be explicit at the type level.

Ví dụ tương lai:

```text
Shared<T>
AtomicShared<T>
```

Không được:

```axiom
let a = Object()
let b = a
```

vô tình biến thành reference-counted object.

---

# 18. Reference counting

Reference counting **không phải memory primitive của Axiom**.

Có thể triển khai:

```text
Rc<T>
Arc<T>
```

ở library.

Ví dụ:

```text
Rc<T>
 ├── pointer
 └── counter
```

`Arc<T>`:

```text
pointer
atomic counter
```

Nhưng Axiom compiler không tự thêm chúng.

---

# 19. Aliasing

Safe Axiom có ba trạng thái access chính:

```text
READ
WRITE
OWN
```

Quy tắc:

```text
READ + READ      OK
READ + WRITE     conflict
WRITE + WRITE    conflict
OWN + anything   depends on transfer
```

Compiler phải phát hiện conflict.

---

# 20. Nhưng không biến nó thành Rust syntax

Source không cần:

```rust
&T
&mut T
'a
```

Axiom source chủ yếu sử dụng:

```text
T
view<T>
mut_view<T>
```

Compiler có thể có internal concepts tương đương borrow checking.

---

# 21. Unsafe boundary

Raw pointer chỉ được thao tác trong:

```axiom
unsafe { ... }
```

hoặc:

```axiom
unsafe fn ...
```

Ví dụ conceptually:

```axiom
unsafe fn read_memory(addr: usize) -> u32 {
    ...
}
```

Safe code không được tự do:

```text
pointer arithmetic
arbitrary cast
raw memory access
MMIO
volatile access
```

---

# 22. Unsafe không làm compiler bỏ kiểm tra mọi thứ

`unsafe` nghĩa:

> Programmer nhận trách nhiệm đối với invariant mà compiler không thể chứng minh.

Không có nghĩa:

```text
unsafe = compiler off
```

Compiler vẫn kiểm tra:

- syntax
- types
- ABI
- instruction validity
- register constraints
- calling convention

---

# 23. Pointer

Axiom vẫn hỗ trợ:

```text
*const T
*mut T
```

nhưng đây là **low-level representation**.

Không nên để pointer trở thành abstraction chính của application code.

---

# 24. Null

Safe Axiom không có nullable pointer mặc định.

Thay vào đó:

```axiom
Option<T>
```

Ví dụ:

```axiom
fn find(...) -> Option<Item>
```

Raw null pointer chỉ hợp lệ trong:

```text
unsafe
FFI
platform ABI
```

---

# 25. Allocation

Memory Model không quy định allocator cụ thể.

Có thể có:

```text
Global allocator
Arena
Pool
Slab
Stack allocator
Custom allocator
OS allocator
GPU allocator
```

Core chỉ quy định semantic:

```text
allocate
owns
use
release
```

---

# 26. Allocation elimination

Compiler SHOULD thực hiện:

```text
escape analysis
stack promotion
scalar replacement
allocation elimination
```

Ví dụ:

```axiom
fn f() -> Point {
    let p = Point(1, 2)
    return p
}
```

không được mặc định hiểu là:

```text
malloc Point
copy Point
free Point
```

---

# 27. Memory safety invariant

### MM-005

Safe Axiom MUST prevent:

```text
use-after-free
double destruction
dangling view
invalid ownership transfer
data race
out-of-bounds memory access
invalid object lifetime access
```

nếu các hành vi đó không nằm trong explicit unsafe/FFI boundary.

---

# 28. Nhưng không hứa "mọi bug đều bị bắt"

Axiom không được tuyên bố:

> "Memory safe = không thể có memory bug."

Unsafe code, FFI, hardware, compiler bugs, external libraries vẫn có thể phá invariant.

Đúng hơn:

> **Safe Axiom programs do not rely on memory-unsafe behavior.**

---

# 29. Concurrency consequence

Từ Memory Model, ta có:

```text
Owned value
     │
     ├── same thread → normal use
     │
     └── another thread
              │
              ▼
            Send
              │
              ▼
        ownership transfer
```

Shared data:

```text
Shared read
    │
    ├── Thread A
    ├── Thread B
    └── Thread C
```

Mutable shared data:

```text
Mutex
RwLock
Atomic
Channel
```

---

# 30. Test suite tối thiểu

Đây là phần rất quan trọng cho AI agent.

Memory Model không chỉ là document. Nó phải có **executable semantic tests**.

Ví dụ:

### `move_001.ax`

```axiom
fn main() {
    let a = Resource()
    let b = a
    use(a)
}
```

Expected:

```text
COMPILE_ERROR
USE_AFTER_MOVE
```

---

### `copy_001.ax`

```axiom
fn main() {
    let a: i32 = 10
    let b = a

    print(a)
    print(b)
}
```

Expected:

```text
COMPILE_SUCCESS
```

---

### `view_001.ax`

```axiom
fn sum(v: view<i32>) -> i32 {
    ...
}

fn main() {
    let a = [1, 2, 3]
    sum(a)
}
```

Expected:

```text
COMPILE_SUCCESS
```

---

### `view_escape_001.ax`

```axiom
fn get() -> view<i32> {
    let a = [1, 2, 3]
    return a
}
```

Expected:

```text
COMPILE_ERROR
VIEW_OUTLIVES_OWNER
```

---

### `double_drop_001.ax`

```axiom
fn main() {
    let a = Resource()
    let b = a
    drop(a)
}
```

Expected:

```text
COMPILE_ERROR
USE_AFTER_MOVE
```

---

### `send_001.ax`

```axiom
fn main() {
    let data = Buffer(...)

    spawn {
        process(data)
    }
}
```

Nếu `Buffer : Send`:

```text
COMPILE_SUCCESS
```

và ownership chuyển sang task.

---

### `race_001.ax`

Conceptually:

```text
Thread A → write x
Thread B → write x
```

không synchronization.

Expected:

```text
COMPILE_ERROR
DATA_RACE
```

---

# 31. Một vấn đề lớn cần quyết định trước khi đóng Memory Model

Có một câu hỏi tôi **không muốn tự ý quyết định thay bạn**:

## Axiom có nên cho phép implicit temporary views không?

Ví dụ:

```axiom
fn process(v: view<i32>)

fn main() {
    process([1, 2, 3])
}
```

Có hai hướng.

### Hướng A — cho phép

Compiler tạo temporary:

```text
temporary array
     ↓
view
     ↓
process
     ↓
destroy temporary
```

Syntax cực kỳ gọn.

### Hướng B — bắt buộc value phải tồn tại

```axiom
let data = [1, 2, 3]
process(data)
```

Semantic dễ kiểm soát hơn.

**Tôi nghiêng về A**, vì compiler có thể quản lý temporary lifetime hoàn toàn deterministic và tối ưu allocation đi. Nhưng đây là một quyết định semantic đáng để khóa riêng.

---

# 32. Một quyết định thứ hai: `view<T>` có nên là type thật?

Có hai thiết kế:

```text
Axiom source:
view<T>
```

hoặc:

```text
Axiom source:
T
```

và compiler tự suy ra parameter là borrowed/view access dựa trên context.

Tôi hiện **nghiêng về việc có `view<T>`**.

Lý do:

```text
fn process(data: Buffer)
```

rõ ràng:

> Tôi nhận ownership.

Trong khi:

```text
fn process(data: view<Buffer>)
```

rõ ràng:

> Tôi chỉ xem data.

Điều này làm API rất dễ đọc mà không cần Rust lifetime syntax.

---

# 33. Type System sau khi Memory Model khóa

Ta sẽ có một hệ thống rất đẹp:

```text
                         TYPE
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      VALUE             VIEW             FUNCTION
        │                  │                  │
      Copy/Move       view<T>           closure
        │             mut_view<T>          │
        │                  │               │
      Drop               lifetime        capture
        │                  │               │
        └──────────────────┼───────────────┘
                           │
                       TRAITS
                           │
             ┌─────────────┼─────────────┐
             │             │             │
           Copy          Send          Share
             │             │             │
             └─────────────┼─────────────┘
                           │
                     COMPILER ANALYSIS
```

Đây là cơ sở để viết **Type System v0.1** tiếp theo.

---

## Nhưng có một thay đổi kiến trúc tôi đề nghị

Trước khi chuyển sang Type System, tôi muốn **khóa Memory Model thành 3 lớp**, thay vì để tất cả ownership rules nằm cùng một tầng:

```text
┌─────────────────────────────────────┐
│         Axiom Safe Memory           │
│                                     │
│ Value / Copy / Move / View / Drop   │
├─────────────────────────────────────┤
│       Axiom Concurrent Memory       │
│                                     │
│ Send / Share / Atomic / Sync        │
├─────────────────────────────────────┤
│        Axiom Unsafe Memory          │
│                                     │
│ Pointer / Address / FFI / MMIO      │
└─────────────────────────────────────┘
```

Như vậy application programmer gần như chỉ sống ở **Safe Memory**, systems programmer có thể xuống **Unsafe Memory**, còn compiler có thể tối ưu xuyên suốt cả ba.

**Bước kế tiếp nên là `Axiom Type System v0.1`**, nhưng lần này tôi sẽ đi sâu vào phần khó nhất: **type properties, generic, trait resolution, `Copy/Move/Drop/Send/Share`, overload, method resolution, type inference và cách tránh "trait hell" của Rust/C++**. Đây là chỗ quyết định Axiom có thực sự đơn giản hơn các ngôn ngữ hiện đại hay không.