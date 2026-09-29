Được. Sau Syntax v0.1, tôi nghĩ chúng ta nên đi thẳng vào phần **quan trọng nhất của Axiom**: semantic core. Đây là nơi quyết định các mục tiêu trước đó — hiệu năng, đơn giản, ownership không gây phiền, compiler tự quản lý lifetime — có thực sự đồng thời đạt được hay không.

# AXIOM SEMANTIC CORE v0.1

Mục tiêu của tầng này:

> **Mỗi expression trong Axiom phải có một semantic interpretation duy nhất, xác định được compiler phải làm gì, nhưng programmer không cần nhìn thấy toàn bộ machinery đó.**

Ta sẽ dùng pipeline:

```text
Source
  │
  ▼
Expression
  │
  ├── Static Type
  ├── Value Category
  ├── Ownership
  ├── Access Mode
  ├── Evaluation Order
  ├── Resource Obligation
  └── Control Flow
          │
          ▼
       Typed HIR
          │
          ▼
          MIR
```

---

# 1. Bảy thuộc tính semantic của expression

Mỗi expression `E` được compiler phân tích thành:

```text
E = {
    type
    category
    ownership
    access
    evaluation
    resource
    control
}
```

Ví dụ:

```axiom
let x = foo()
```

compiler không chỉ thấy:

```text
x : T
```

mà phải biết:

```text
type      = T
category  = value
ownership = OWN
access    = WRITE
resource  = maybe Drop
control   = normal
```

---

# 2. Value Category

Axiom chỉ cần **3 category chính**.

## VALUE

Có ownership của một giá trị.

```axiom
let x = make_buffer()
```

`x` là VALUE.

---

## VIEW

Không sở hữu dữ liệu.

```axiom
fn print(data: view<u8>)
```

View chỉ là quyền truy cập.

---

## PLACE

Một location có thể được đọc/ghi.

Ví dụ:

```axiom
x
obj.field
array[i]
```

Compiler nội bộ cần khái niệm PLACE để phân biệt:

```text
đọc giá trị từ x
```

với:

```text
ghi vào x
```

Nhưng **PLACE không phải programmer-facing type**.

Đây là một quyết định quan trọng:

> Không cần đưa quá nhiều category kiểu C++ vào ngôn ngữ.

---

# 3. Access Mode

Mỗi access có một trong:

```text
READ
WRITE
MOVE
OWN
```

Có thể biểu diễn:

```text
READ  → chỉ đọc
WRITE → cần quyền ghi
MOVE  → lấy ownership
OWN   → tạo/nhận ownership mới
```

Ví dụ:

```axiom
let x = foo
```

`foo`:

```text
MOVE
```

nếu `foo` là owning value.

---

# 4. Quy tắc aliasing

Compiler áp dụng:

```text
READ + READ   = OK
READ + WRITE  = ERROR
WRITE + WRITE = ERROR
MOVE + ANY    = ERROR
OWN + ANY     = ERROR
```

Nhưng đây là **semantic rule**, không phải borrow syntax.

Ví dụ:

```axiom
let a = view(x)
let b = view(x)
```

OK.

```axiom
let a = view(x)
modify(x)
```

Compiler phát hiện xung đột nếu `a` còn sống.

---

# 5. Lifetime không phải một syntax concept

Đây là một trong những điểm tôi muốn Axiom làm khác Rust.

Programmer viết:

```axiom
fn process(data: view<u8>) {
    ...
}
```

không viết:

```text
'a
```

Compiler internally tạo:

```text
Owner: data_source
View: data
Lifetime:
    begin = view creation
    end   = last semantic use
```

### Lifetime có thể ngắn hơn lexical scope

Ví dụ:

```axiom
let v = view(buffer)

print(v)

modify(buffer)
```

Compiler có thể xác định:

```text
v lifetime
├── create
├── print
└── END
       │
       ▼
modify(buffer)
```

Không cần programmer viết block riêng.

---

# 6. Đây là điểm cực kỳ quan trọng về performance

Compiler **không nhất thiết phải giữ view đến cuối scope**.

Ví dụ:

```axiom
fn foo(buffer: Buffer) {
    let v = view(buffer)

    consume(v)

    modify(buffer)
}
```

Nếu `v` không còn được sử dụng sau `consume`, compiler kết thúc logical lifetime ngay tại đó.

Điều này giúp:

- giảm alias restrictions
- tăng optimization
- cho phép register promotion
- cho phép vectorization
- giảm false dependency.

---

# 7. Ownership State Machine

Mỗi owning value có trạng thái compiler-managed:

```text
             ┌─────────────┐
             │   UNINIT    │
             └──────┬──────┘
                    │ init
                    ▼
             ┌─────────────┐
       ┌────►│    OWNED    │◄──── copy
       │     └──────┬──────┘
       │            │ move
       │            ▼
       │     ┌─────────────┐
       │     │    MOVED    │
       │     └─────────────┘
       │
       │ drop
       │
       ▼
 ┌─────────────┐
 │   DROPPED   │
 └─────────────┘
```

Không được:

```text
MOVED → READ
MOVED → MOVE
DROPPED → READ
DROPPED → DROP
```

---

# 8. Copy không phải Move

Ví dụ:

```axiom
let a = 10
let b = a
```

với `i32: Copy`.

Semantic:

```text
a = OWN
b = COPY(a)
a = OWN
b = OWN
```

Cả hai tồn tại độc lập.

Compiler có thể thực hiện:

```text
register copy
```

hoặc thậm chí tối ưu thành constant.

---

# 9. Move không nhất thiết copy memory

Ví dụ:

```axiom
let a = Buffer(...)
let b = a
```

Nếu `Buffer` không Copy:

```text
a ──────── ownership ────────► b
```

Compiler có thể không copy byte nào.

Đây là lý do ownership **không nhất thiết làm chương trình chậm**.

---

# 10. Drop

Giả sử:

```axiom
struct File {
    handle: RawHandle
}
```

`File` có resource ownership.

```axiom
fn foo() {
    let file = open()
}
```

Compiler tạo semantic cleanup:

```text
open
  ↓
file owned
  ↓
function exit
  ↓
drop(file)
  ↓
return
```

Nhưng optimizer có thể inline:

```text
open
...
close
return
```

Hoặc nếu toàn bộ resource được chứng minh không cần thiết:

```text
eliminate
```

nếu việc loại bỏ vẫn bảo toàn observable semantics.

---

# 11. Drop không phải `free`

Điều này cần đóng băng rõ.

```text
Drop(T)
```

không có nghĩa:

```text
free(address)
```

Nó có thể là:

```text
close(file)
release(handle)
unlock(resource)
decrement explicit shared owner
return object to pool
destroy GPU object
```

Do đó Axiom có thể dùng nhiều memory strategy mà semantic language không đổi.

---

# 12. Storage Independence

Một value:

```axiom
let x = Foo(...)
```

không có semantic:

```text
x nằm trên stack
```

hay:

```text
x nằm trên heap
```

Compiler tự chọn.

Ví dụ:

```text
Source
  │
  ▼
Foo
  │
  ├── register
  ├── stack
  ├── inline
  ├── heap
  ├── arena
  └── eliminated
```

Miễn observable semantics không đổi.

---

# 13. Expression Evaluation Order

Axiom nên **đóng băng evaluation order**.

Đề xuất:

> Các operand và argument được evaluate từ trái sang phải.

Ví dụ:

```axiom
foo(a(), b(), c())
```

luôn:

```text
a()
 ↓
b()
 ↓
c()
 ↓
foo(...)
```

Điều này khác với những vùng unspecified behavior nổi tiếng của C/C++.

Nó giúp:

- compiler deterministic
- debugger dễ hơn
- AI code generation dễ hơn
- testing dễ hơn.

Optimizer vẫn được phép reorder machine instructions nếu không thay đổi observable semantics.

---

# 14. Function Call Semantic

```axiom
foo(a, b)
```

được phân tích:

```text
1. resolve foo
2. resolve generic parameters
3. resolve argument types
4. evaluate a
5. evaluate b
6. establish access/ownership
7. call
8. receive result
```

Quan trọng:

**ownership checking xảy ra trước machine lowering.**

---

# 15. Method Call

```axiom
obj.foo(x)
```

không phải primitive mới.

HIR:

```text
foo(obj, x)
```

Method resolution:

```text
1. inherent function
2. applicable trait implementation
3. imported extension
4. ambiguity/error
```

Sau resolution:

```text
obj.foo(x)
      ↓
foo(obj, x)
      ↓
direct call
```

Không có hidden `this`.

---

# 16. Generic Resolution

Ví dụ:

```axiom
max(a, b)
```

Compiler:

```text
resolve max
     ↓
infer T
     ↓
check T: Comparable
     ↓
specialize
     ↓
max<i32>
```

Sau đó:

```text
MIR
 ↓
specialized MIR
 ↓
inline
 ↓
machine code
```

Không cần runtime generic metadata.

---

# 17. Trait Dispatch

Mặc định:

```axiom
fn draw<T: Drawable>(x: T)
```

là static dispatch.

Compiler:

```text
draw<Circle>
draw<Rectangle>
```

có thể thành hai specialization.

Không:

```text
vtable
virtual call
heap allocation
```

trừ khi programmer chọn dynamic abstraction.

---

# 18. Dynamic Dispatch

Chỉ khi explicit:

```axiom
dyn Drawable
```

Semantic representation conceptually:

```text
┌──────────────┐
│ data pointer │
├──────────────┤
│ dispatch ptr │
└──────────────┘
```

Không object header.

Không mọi object đều có vtable.

---

# 19. `view<T>` là capability

Đây là cách nhìn tôi nghĩ rất phù hợp với Axiom.

`view<T>` không đơn thuần là:

```text
pointer + length
```

mà là:

> **quyền đọc một vùng dữ liệu trong một lifetime compiler-verified.**

`mut_view<T>`:

> **quyền độc quyền ghi một vùng dữ liệu trong một lifetime compiler-verified.**

Physical representation có thể là:

```text
view<T>
    address
    extent
```

nhưng semantic representation mạnh hơn physical representation.

---

# 20. Compiler có thể tối ưu view thành zero overhead

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32
```

source:

```text
pointer + length
```

nhưng sau optimization:

```text
pointer
length
```

có thể nằm:

```text
RDI
RSI
```

hoặc target-specific registers.

Không object.

Không allocation.

Không reference count.

---

# 21. Array

```axiom
let a = [1, 2, 3, 4]
```

type:

```text
Array<i32, 4>
```

Array là value.

Không tự động heap.

Có thể:

```text
stack
register
inline struct
static
```

Compiler có quyền scalarize:

```text
a[0]
a[1]
a[2]
a[3]
```

thành các registers nếu có lợi.

---

# 22. Slice/View conversion

```axiom
let a = [1, 2, 3, 4]

process(a)
```

nếu:

```axiom
process(v: view<i32>)
```

compiler tạo:

```text
Array<i32,4>
       │
       ▼
view<i32>
(address, 4)
```

Không allocation.

Không copy array.

---

# 23. Bounds checking

```axiom
a[i]
```

Safe Axiom phải đảm bảo:

```text
0 <= i < length
```

Nếu compiler không chứng minh được:

```text
runtime bounds check
```

Nếu chứng minh được:

```text
bounds check eliminated
```

Ví dụ:

```axiom
for i in 0..a.len {
    sum += a[i]
}
```

compiler nên nhận ra invariant:

```text
i < a.len
```

và bỏ check trong loop.

Đây là một trong những nơi Axiom có thể đạt performance C/C++ mà vẫn safe.

---

# 24. Arithmetic

Axiom không được để:

```text
CPU behavior
```

quyết định semantic language.

Ví dụ overflow phải được định nghĩa.

Tôi đề xuất:

```text
normal arithmetic
    → checked semantics

wrapping
    → explicit

saturating
    → explicit
```

Ví dụ conceptual:

```axiom
let x = a + b
```

Nếu overflow:

```text
panic/trap
```

Còn:

```axiom
let x = a wrapping_add b
```

cho modular arithmetic.

Và:

```axiom
let x = a saturating_add b
```

cho saturation.

Exact operator syntax có thể đóng băng sau khi numeric model hoàn chỉnh.

---

# 25. Division

Không để CPU quyết định.

```axiom
10 / 0
```

phải có deterministic semantic result:

```text
trap/panic
```

không UB.

---

# 26. Initialization

Axiom phải có definite initialization.

Sai:

```axiom
var x: i32

if condition {
    x = 10
}

print(x)
```

nếu compiler không chứng minh `condition == true`.

Đây là compile error.

Nhưng:

```axiom
var x: i32

if condition {
    x = 10
} else {
    x = 20
}

print(x)
```

OK.

Compiler MIR sẽ biểu diễn:

```text
if
 ├── x = 10
 └── x = 20
       ↓
      PHI
       ↓
       x
```

---

# 27. Conditional Drop

Đây là chỗ compiler cần mạnh hơn programmer.

```axiom
var file: File

if condition {
    file = open()
}

if condition {
    close(file)
}
```

Compiler phải theo dõi:

```text
file:
UNINIT
   │
 condition
 ├────── false ──► UNINIT
 │
 └────── true ───► OWNED
```

và cleanup chính xác.

Programmer không viết:

```text
drop_flag
```

Đây là compiler machinery.

---

# 28. Return

```axiom
fn foo() -> T {
    let a = A()
    let b = B()

    return result
}
```

Semantic cleanup:

```text
return result
    │
    ├── drop(b)
    ├── drop(a)
    └── return
```

Nếu result sử dụng một phần dữ liệu của `a`, compiler ownership analysis phải xử lý trước khi drop.

---

# 29. `defer` tiếp tục không cần

Ví dụ:

```axiom
defer cleanup()
```

không cần trong Core.

Thay vào đó:

```text
resource ownership
        ↓
Drop
        ↓
compiler cleanup region
```

Nếu cần arbitrary scope action:

```text
ScopeGuard
Defer
```

có thể nằm trong library.

---

# 30. Observable Semantics

Đây là nguyên tắc tối thượng của optimizer.

Compiler được phép biến:

```text
heap allocation
```

thành:

```text
stack
```

hoặc:

```text
register
```

hoặc:

```text
nothing
```

**chỉ khi chương trình không thể quan sát sự khác biệt theo Axiom semantics.**

Các thứ observable có thể gồm:

```text
I/O
volatile memory
atomics
synchronization
FFI
explicit addresses
timing-sensitive APIs nếu language/library cam kết
panic/trap
resource side effects
```

---

# 31. `volatile`

Đây phải là unsafe/system-level.

```axiom
unsafe {
    volatile_write(addr, value)
}
```

Compiler **không được**:

```text
remove
merge
reorder
```

volatile operation theo cách phá semantic contract.

---

# 32. Atomic

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed)
```

Compiler không được biến thành ordinary load/add/store.

Memory ordering là semantic.

Đây là một boundary optimizer không được vượt qua.

---

# 33. Unsafe không phải “tắt optimizer”

Rất quan trọng.

```axiom
unsafe {
    *ptr = value
}
```

không có nghĩa compiler trở nên ngây thơ.

Compiler vẫn:

- type-check
- optimize
- register allocate
- reorder khi semantics cho phép.

Programmer chịu trách nhiệm đảm bảo pointer hợp lệ.

---

# 34. Semantic Boundary

Từ toàn bộ model hiện tại, Axiom có một architecture rất đẹp:

```text
                    AXIOM SOURCE
                         │
                         ▼
                 ┌───────────────┐
                 │   TYPE CHECK  │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │   OWNERSHIP   │
                 │   + ALIAS     │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ CONCURRENCY   │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │ DROP/CONTROL  │
                 │ ELABORATION   │
                 └───────┬───────┘
                         ▼
                 ╔═══════════════╗
                 ║ VERIFIED MIR  ║
                 ╚═══════╤═══════╝
                         │
                  SEMANTIC FIREWALL
                         │
                         ▼
                 ┌───────────────┐
                 │  OPTIMIZER    │
                 └───────┬───────┘
                         ▼
                 ┌───────────────┐
                 │     LIR       │
                 └───────┬───────┘
                         ▼
                     MACHINE
```

**Verified MIR là semantic firewall.**

Đây là một trong những quyết định kiến trúc quan trọng nhất của Axiom.

---

# 35. Vì sao kiến trúc này phù hợp mục tiêu của bạn?

Nó giải quyết đồng thời mấy vấn đề bạn đã lo trước đây.

### Không GC

Không cần tracing collector.

### Không borrow syntax

Compiler vẫn làm lifetime/alias analysis nhưng programmer không phải viết lifetime.

### Không bắt programmer quản lý pointer

Safe API dùng value/view.

### Không mất performance vì abstraction

Sau Verified MIR:

```text
view
trait
generic
closure
async
ownership
```

đều có thể bị compiler lower/eliminate.

### Không ép một memory model vật lý

Compiler có thể dùng:

```text
register
stack
inline
arena
pool
heap
```

### Không biến compiler thành LLVM frontend

LLVM có thể là backend tùy chọn.

### Không cần runtime khổng lồ

Chương trình đơn giản có thể:

```text
Axiom source
   ↓
native code
```

với runtime tối thiểu hoặc bằng 0.

---

# 36. Một nguyên tắc mới nên đưa vào Axiom Constitution

Từ các phần đã chốt, tôi đề xuất thêm một invariant cấp cao:

> **ACI-16 — Compiler Complexity Is Not Language Complexity**

Cụ thể:

> Axiom may employ sophisticated compile-time analysis for ownership, lifetime, aliasing, escape, specialization, concurrency, and optimization, provided that such analysis does not require equivalent complexity in programmer-facing syntax.

Nói ngắn gọn:

**Compiler được phép phức tạp. Ngôn ngữ không được bắt programmer phức tạp theo.**

Đây chính là hướng tôi nghĩ Axiom nên theo đuổi thay vì cố biến compiler thành một chương trình đơn giản.

---

## Bước tiếp theo tôi đề xuất

Bây giờ semantic core đã đủ rõ để chuyển sang một phần **rất thực tế và quyết định performance**:

### `AXIOM MEMORY & ALLOCATION MODEL v0.2`

Ta sẽ thiết kế cụ thể:

```text
Stack
Heap
Arena
Pool
Static
Inline
Register
Allocator API
Ownership → allocation
Escape analysis
Small-object optimization
Struct layout
Array layout
String layout
Buffer
Shared ownership
Arc/Rc
Custom allocator
OS allocation
Zero-allocation APIs
```

Đặc biệt ta sẽ giải quyết câu hỏi bạn đã đặt từ đầu:

> **Axiom nên dùng flat memory, stack/heap truyền thống, arena, pool hay một mô hình hoàn toàn khác — và làm sao để vừa nhanh vừa tránh fragmentation mà không biến programmer thành người quản lý memory thủ công?**

Tôi nghĩ đây là phần đáng thiết kế rất kỹ **trước khi đóng Type/Standard Library**, vì allocation model sẽ ảnh hưởng trực tiếp đến ABI, MIR, `Buffer`, `String`, `Vec`, shared ownership và FFI.