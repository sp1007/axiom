Đúng. Tôi đề xuất **đóng băng semantics của Axiom ở v0.1** ngay bây giờ. Sau mốc này, mọi thay đổi phải được phân loại là **clarification / compiler implementation detail / breaking semantic change**, không được tùy tiện sửa vì một ví dụ mới.

## AXIOM SEMANTIC FREEZE v0.1

### 1. Nguyên tắc tối cao

```text
Correctness
    >
Predictability
    >
Simplicity
    >
Performance
```

Performance được tối ưu **bên trong semantics**, không được dùng performance để phá semantics.

Nguyên tắc trung tâm:

> **Explicit at semantic boundaries, implicit within the compiler.**

Programmer phải biểu đạt những thứ thực sự ảnh hưởng đến semantics:

```text
ownership
view / mut_view
unsafe
dynamic dispatch
Result
async
spawn
atomic
repr(C)
```

Compiler tự xử lý:

```text
lifetime
drop insertion
alias analysis
escape analysis
stack promotion
register allocation
specialization
cleanup
async state machine
bounds-check elimination
```

---

# 2. Semantic identity của mọi expression

Mọi expression trong Axiom có:

```text
TYPE
CATEGORY
OWNERSHIP
ACCESS
EVALUATION
RESOURCE
CONTROL
```

### TYPE

Một static type duy nhất.

Không có expression “có thể là nhiều type” sau khi type resolution hoàn tất.

### CATEGORY

```text
VALUE
VIEW
PLACE
```

`PLACE` là khái niệm nội bộ compiler, không phải programmer-facing syntax.

### ACCESS

```text
READ
WRITE
MOVE
OWN
```

Luật cơ bản:

```text
READ  + READ   = OK
READ  + WRITE  = ERROR
WRITE + WRITE  = ERROR
MOVE  + ANY    = ERROR
OWN   + ANY    = ERROR
```

---

# 3. Value semantics

Axiom mặc định là **value-oriented**.

```axiom
let a = point
let b = a
```

Có hai khả năng:

```text
Copy type
    → copy

Owning non-Copy type
    → move
```

Compiler quyết định dựa trên type properties.

Không có implicit shared mutable alias.

---

# 4. Ownership

Ownership là semantic property.

Programmer **không viết lifetime annotation**.

Ownership state nội bộ:

```text
UNINIT
   ↓
OWNED
   ↓
MOVED
   ↓
DROPPED
```

Không được:

```text
MOVED → READ
MOVED → WRITE
MOVED → MOVE
```

Không được:

```text
DROPPED → bất kỳ access nào
```

Move **không có nghĩa** compiler bắt buộc phải copy memory.

```text
move
```

là thay đổi ownership state.

---

# 5. Copy

Một type `Copy` cho phép:

```text
a ──copy──> b
```

và cả hai tiếp tục hợp lệ.

`Copy` không phải inheritance.

`Copy` cũng không phải behavioral trait thông thường.

Compiler có thể tự suy ra:

```text
Point
 ├── x: f32
 └── y: f32

=> Copy
```

nếu mọi thành phần đáp ứng điều kiện.

---

# 6. Drop

Owning resource có thể có `Drop`.

Compiler tự chèn cleanup.

Ví dụ:

```axiom
fn test() {
    let a = File.open("a")
    let b = File.open("b")
}
```

Semantic cleanup:

```text
drop(b)
drop(a)
```

theo reverse declaration order.

Nhưng machine code **không bắt buộc** phải có hai lời gọi destructor.

Optimizer có thể:

```text
inline
eliminate
merge
specialize
```

miễn observable semantics không đổi.

### Freeze decision

**`Drop` không được trả về recoverable error.**

Nếu đóng resource có thể thất bại:

```axiom
file.close() -> Result<(), Error>
```

phải xử lý explicit.

`Drop` chỉ là deterministic cleanup.

---

# 7. View

Axiom không dùng Rust-style:

```text
&T
&mut T
'a
```

Thay vào đó:

```axiom
view<T>
mut_view<T>
```

`view<T>`:

```text
non-owning
read-only
```

`mut_view<T>`:

```text
non-owning
mutable
```

Conceptual representation:

```text
view<T>
    address
    extent
```

nhưng đây **không phải ABI bắt buộc**.

Compiler có thể biến nó thành:

```text
registers
```

hoặc thậm chí loại bỏ hoàn toàn abstraction.

---

# 8. View lifetime

Programmer không khai báo lifetime.

Compiler phải chứng minh:

```text
view lifetime ⊆ owner validity
```

Ví dụ:

```axiom
fn bad() -> view<i32> {
    var x = [1, 2, 3]
    view(x)
}
```

→ reject.

Compiler diagnostic phải giải thích:

```text
view escapes owner
owner: x
owner lifetime: function-local
view lifetime: returned
```

---

# 9. Aliasing

Safe Axiom cho phép:

```text
READ + READ
```

nhưng không:

```text
READ + WRITE
WRITE + WRITE
```

nếu chúng có thể truy cập cùng storage.

Compiler phải thực hiện alias/lifetime analysis.

Programmer không phải viết borrow annotations.

---

# 10. `unsafe`

`unsafe` mở quyền sử dụng những primitive mà compiler không thể chứng minh an toàn.

Ví dụ:

```text
raw pointer
pointer arithmetic
address manipulation
volatile
hardware access
reinterpretation
FFI tricks
```

Nhưng:

> `unsafe` **không tắt type checking**.

Ví dụ này vẫn sai:

```axiom
unsafe {
    let p: *mut i32 = ...
    *p = "hello"
}
```

`unsafe` chỉ chuyển một phần trách nhiệm correctness sang programmer.

---

# 11. Struct

`struct` là aggregate primitive chính.

```axiom
struct Point {
    x: f32
    y: f32
}
```

Không có:

```text
class
extends
inheritance
protected
friend
implicit this
```

Method:

```axiom
fn length(self: Vec2) -> f32
```

chỉ là function:

```text
length(Vec2)
```

Call syntax:

```axiom
v.length()
```

là syntax sugar.

---

# 12. Trait

Trait là **behavioral contract**, không phải inheritance.

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

```axiom
impl Drawable for Circle {
    ...
}
```

Static dispatch mặc định.

Dynamic dispatch phải explicit.

Không có implicit vtable/object header.

---

# 13. Properties ≠ traits

Các property compiler-known:

```text
Copy
Drop
Send
Share
Sized
```

không được biến thành một hệ trait thông thường.

Ví dụ:

```text
Send ≠ Share
```

Một object có thể:

```text
Send = true
Share = false
```

hoặc:

```text
Send = true
Share = true
```

---

# 14. Generics

Generic là compile-time abstraction.

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Compiler:

```text
generic checking
        ↓
specialization
        ↓
typed MIR
```

Mục tiêu ban đầu:

```text
monomorphization
specialization
inlining
```

Không yêu cầu runtime generic metadata.

---

# 15. Memory model

Đây là quyết định quan trọng:

> **Flat virtual address space ≠ flat allocation model.**

Axiom có:

```text
ADDRESS MODEL
    flat virtual address space

STORAGE MODEL
    register
    inline
    stack
    arena
    pool
    heap
    static
    external

ALLOCATION MODEL
    allocator
    arena
    pool
    slab
    custom
    OS
    GPU
    ...
```

Không có:

```text
new
delete
```

ở semantic core.

`Box`, `Vec`, `Buffer` là library abstractions.

Compiler được phép biến:

```text
heap
 ↓
stack
 ↓
register
 ↓
nothing
```

nếu observable semantics không thay đổi.

---

# 16. Không mandatory GC

Axiom không yêu cầu:

```text
GC
```

Không implicit:

```text
reference counting
object header
heap allocation
runtime
```

Shared ownership phải explicit:

```text
Rc
Arc
Shared
...
```

---

# 17. Concurrency

Safe code:

```text
không data race
```

Có ba khái niệm chính:

```text
MOVE
READ SHARE
MUTABLE SHARE
```

`Send`:

```text
ownership có thể chuyển execution context
```

`Share`:

```text
có thể immutable-share
```

Mutable shared state phải dùng synchronization/atomic abstraction.

Mutex, channel, atomic... là library primitives.

---

# 18. Thread và async

Không đồng nhất:

```text
thread ≠ task ≠ async
```

```text
thread
    = execution resource

task
    = logical work

async
    = suspension/resumption
```

`async` không tự động tạo thread.

Không có mandatory executor.

Async có thể lower thành:

```text
state machine
```

---

# 19. Error semantics

Không có C++-style exception trong Core.

Bốn đường:

```text
return
Result / Option
panic
trap
```

Recoverable error:

```axiom
Result<T, E>
```

Absence:

```axiom
Option<T>
```

Không có ordinary null.

Bounds violation, divide-by-zero, overflow... phải có semantics xác định.

Không được dựa vào C-style UB cho safe arithmetic.

---

# 20. Evaluation order

Freeze:

> **Arguments và operands được đánh giá left-to-right.**

Ví dụ:

```axiom
foo(a(), b(), c())
```

semantic order:

```text
a()
 ↓
b()
 ↓
c()
 ↓
foo(...)
```

Optimizer có thể reorder machine instructions nếu không thay đổi observable semantics.

---

# 21. ABI/layout

Native layout:

```text
compiler-controlled
```

Explicit representation:

```axiom
@repr(C)
```

là optimization/ABI boundary.

`repr(C)` phải bảo đảm C-compatible layout theo ABI target tương ứng.

Không có:

```text
mandatory object header
mandatory vptr
mandatory heap
```

Aggregate có thể:

```text
register
stack
scalarized
split-register
eliminated
```

---

# 22. Observable semantics

Đây là một freeze point rất quan trọng.

Compiler **được tự do thay đổi representation**, trừ khi representation/storage trở thành observable.

Observable boundary gồm:

```text
I/O
volatile
atomic operations
synchronization
FFI
explicit address operations
resource side effects
panic/trap
explicit ABI promises
```

Ví dụ:

```axiom
let x = Box.new(123)
```

không mặc nhiên có nghĩa:

> x phải thực sự nằm trên heap.

Nhưng nếu programmer yêu cầu stable address/FFI representation thì allocation/storage trở thành observable constraint.

---

# 23. Verified MIR

Đây là architectural freeze quan trọng nhất.

Compiler pipeline:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Alias / Lifetime
  ↓
Concurrency
  ↓
Drop elaboration
  ↓
VERIFIED MIR
  ↓
Optimization
  ↓
LIR
  ↓
Machine IR
  ↓
Machine code
```

**Verified MIR là semantic boundary.**

Trước đó:

```text
compiler đang chứng minh chương trình hợp lệ
```

Sau đó:

```text
optimizer được phép biến đổi representation
```

với invariant:

```text
observable semantics preserved
```

---

# 24. Những thứ KHÔNG được phép thay đổi tùy tiện

Sau semantic freeze, agent không được tự ý quyết định:

```text
"Rust làm thế này nên Axiom cũng nên..."
"C++ làm thế kia nên thêm vào..."
"Feature này tiện nên thêm..."
```

Mọi thay đổi phải thuộc một trong ba loại:

### A. Clarification

Không thay đổi semantics.

Ví dụ:

> `view<T>` có thể được truyền vào function theo value semantics.

Chỉ viết rõ hơn.

### B. Implementation detail

Không thay đổi observable behavior.

Ví dụ:

```text
MIR dùng SSA hay hybrid SSA
```

có thể thay đổi.

### C. Semantic change

Thay đổi observable behavior.

Ví dụ:

```text
cho phép mutable alias trong safe code
```

Đây là **breaking change**.

Không được tự động sửa spec.

---

# 25. Semantic Freeze Gate

Từ bây giờ, một feature chỉ được thêm nếu trả lời được:

```text
1. Nó thuộc semantic core hay library?
2. Nó có tạo semantic concept mới không?
3. Nó có phá ACI/ATS/AMM/ACON/AES/AABI không?
4. Ownership interaction là gì?
5. View/lifetime interaction là gì?
6. Concurrency interaction là gì?
7. MIR biểu diễn thế nào?
8. Verified MIR invariant nào bảo đảm nó?
9. ABI có thay đổi không?
10. Có test conformance nào chứng minh?
```

Nếu chưa trả lời được → **không freeze feature đó**.

---

## Tôi đặc biệt muốn freeze thêm một câu

**Axiom không hứa “compiler luôn biết chứng minh mọi thứ”.**

Nếu compiler không chứng minh được một chương trình safe, có hai hướng:

```text
SAFE
→ phải chứng minh được

UNSAFE
→ programmer chịu trách nhiệm
```

Nhưng **không nên biến mọi trường hợp khó phân tích thành unsafe**.

Compiler nên được phép có các chiến lược phân tích ngày càng mạnh theo thời gian:

```text
Axiom Compiler v0.1
    ↓
simple analysis

Axiom Compiler v0.5
    ↓
better escape analysis

Axiom Compiler v1.0
    ↓
better alias analysis

Axiom Compiler v2.0
    ↓
better interprocedural proof
```

Semantics vẫn giữ nguyên.

Đây chính là cách để **Axiom không bị khóa vào trình độ của compiler v0.1**.

---

### Trạng thái sau freeze

```text
                 AXIOM v0.1
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    TYPE          MEMORY       CONCURRENCY
       │             │             │
       └─────────────┼─────────────┘
                     ▼
                   MIR
                     │
                     ▼
             VERIFIED MIR
                     │
                     ▼
                OPTIMIZER
```

Tôi xem đây là **semantic contract v0.1**. Bước kế tiếp hợp lý nhất là không brainstorm nữa mà xây **`AXIOM-CONFORMANCE-TESTS v0.1`**, khoảng 50–100 test đầu tiên, bao phủ các tương tác nguy hiểm nhất. Sau đó dùng chính bộ test đó làm “hàng rào” để AI agent bắt đầu viết compiler mà không tự diễn giải lại ngôn ngữ.