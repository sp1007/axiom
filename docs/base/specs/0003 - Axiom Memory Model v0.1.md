Được. Vì **Axiom Core v0.1 đã đóng băng**, 4 phần này nên được viết như các specification nối tiếp Core, nhưng phải đặc biệt tránh việc vô tình đưa Rust borrow checker, GC hoặc một runtime bắt buộc vào Axiom.

Tôi đề xuất cấu trúc:

1. **Axiom Memory Model v0.1**
2. **Axiom Type System v0.1**
3. **Axiom Concurrency Model v0.1**
4. **Axiom Compiler IR v0.1**

Trong đó **Memory Model + Type System là nền móng**, Concurrency dựa trên hai phần này, còn IR phải biểu diễn được cả ba mà không làm chúng phụ thuộc vào LLVM.

---

# 1. Axiom Memory Model v0.1

## 1.1. Mục tiêu

Axiom Memory Model hướng tới:

- native performance
- không GC bắt buộc
- không reference-counting bắt buộc
- không borrow syntax
- không lifetime annotation
- deterministic destruction
- tránh dangling pointer trong safe code
- giảm áp lực quản lý pointer cho programmer
- cho phép compiler tối ưu stack/register/heap
- vẫn có `unsafe` để viết kernel, driver, allocator, FFI...
- không ép mọi object phải có header

Nguyên tắc:

> **Programmer quản lý ownership; compiler quản lý lifetime.**

Không phải:

> Programmer quản lý địa chỉ bộ nhớ.

---

# 2. Ba tầng bộ nhớ

Axiom phân biệt ba khái niệm:

```text
Value
  │
  ├── inline storage
  │     ├── register
  │     ├── stack
  │     └── embedded in another value
  │
  └── owned resource
        ├── heap
        ├── arena
        ├── pool
        └── custom allocator
```

Điểm quan trọng:

**heap không phải là một semantic requirement của type.**

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Compiler có thể biến:

```axiom
let v = Vec2(1.0, 2.0)
```

thành:

```text
register
```

hoặc:

```text
stack
```

mà programmer không cần biết.

---

# 3. Value semantics

Đây là trung tâm của Axiom.

```axiom
let a = Vec2(1, 2)
let b = a
```

`b` là một value độc lập về mặt semantic.

Không có implicit alias:

```text
a ──┐
    ├── same object
b ──┘
```

mà semantic là:

```text
a ──> value A

b ──> value B
```

Compiler có quyền tối ưu thành:

```text
same register
```

nếu observable behavior không thay đổi.

Đây là điểm rất quan trọng:

> **Semantic independence ≠ physical copy.**

---

# 4. Copy và Move

Axiom có hai nhóm value.

### Trivially copyable

Ví dụ:

```axiom
i32
f32
bool
Vec2
```

nếu `Vec2` chỉ chứa các thành phần copyable.

```axiom
let a = 10
let b = a
```

`a` vẫn sử dụng được.

---

### Owning value

Ví dụ conceptual:

```axiom
Buffer
File
Socket
Image
GpuBuffer
```

Khi:

```axiom
let a = Buffer(...)
let b = a
```

thì mặc định là:

```text
a ──ownership──> resource
       │
       └──move──> b
```

Sau move:

```axiom
a // compile error
```

Điều này giúp tránh:

- double free
- use-after-free
- double close

mà không cần GC.

---

# 5. Compiler-managed lifetime

Axiom không yêu cầu:

```axiom
free(x)
destroy(x)
delete(x)
close(x)
```

cho resource-owned types.

Ví dụ:

```axiom
fn process() {
    let file = File.open("data.bin")

    ...
}
```

Compiler biết khi scope kết thúc:

```text
file lifetime ends
       ↓
release(file)
```

Compiler có thể lower thành:

```text
try/finally-like cleanup
```

nhưng không cần exception system.

---

# 6. Ownership không đồng nghĩa với Borrow Checker kiểu Rust

Đây là điểm tôi muốn giữ rất rõ.

Axiom **có ownership analysis**, nhưng programmer không phải viết:

```rust
'a
&'a T
&mut T
```

Axiom hướng tới:

```axiom
fn process(data: Buffer) {
    ...
}
```

hoặc các view/slice phù hợp.

Compiler tự phân tích:

```text
ownership
lifetime
escape
alias
mutation
capture
thread transfer
```

Nếu compiler không chứng minh được safety:

```text
compile error
```

thay vì bắt programmer viết thêm một hệ thống lifetime phức tạp.

---

# 7. Reference trong Axiom

Reference vẫn tồn tại **ở semantic level**.

Ví dụ slice:

```axiom
Slice<T>
```

có thể conceptually là:

```text
┌──────────────┐
│ address      │
│ length       │
└──────────────┘
```

Nhưng programmer không cần thao tác pointer.

Raw pointer:

```axiom
*mut T
*const T
```

chỉ xuất hiện trong:

```axiom
unsafe
```

---

# 8. Aliasing model

Axiom cần phân biệt:

```text
Owned
Shared read
Exclusive mutable
Raw/unsafe
```

Safe code phải bảo đảm:

```text
many readers
OR
one mutable writer
```

nhưng không nhất thiết biểu diễn bằng syntax Rust.

Ví dụ:

```axiom
fn sum(values: Slice<i32>) -> i32
```

có thể đọc.

Trong khi:

```axiom
fn fill(values: Slice<i32>, x: i32)
```

có quyền mutation.

Compiler kiểm tra aliasing phía sau.

---

# 9. Heap allocation

Axiom **không định nghĩa "mọi dynamic object = heap object".**

Có thể có:

```text
stack allocation
heap allocation
arena allocation
pool allocation
static allocation
inline storage
register allocation
```

Compiler có thể chuyển:

```text
heap → stack
```

nếu escape analysis chứng minh được.

Ví dụ:

```axiom
fn create() -> Vec2 {
    let x = Vec2(...)
    return x
}
```

Không cần heap.

---

# 10. Flat address space

Axiom v0.1 giữ:

> **Flat virtual address space**

nhưng đây là **machine memory model**, không phải allocator model.

Không nên hiểu:

```text
flat memory = không fragmentation
```

Fragmentation phụ thuộc allocator.

Axiom cho phép:

```text
General allocator
Arena
Pool
Slab
Stack allocator
Custom allocator
```

ở tầng library/runtime/system.

---

# 11. No mandatory object header

Đây là invariant rất quan trọng.

Một:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

không tự nhiên biến thành:

```text
[vtable]
[refcount]
[type id]
[GC metadata]
[x]
[y]
[z]
```

Mà có thể chỉ là:

```text
[x][y][z]
```

ABI cụ thể do compiler quyết định.

---

# 12. Axiom Type System v0.1

Tôi đề xuất type system theo mô hình:

```text
                    Type
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Primitive      Aggregate      Abstraction
       │              │              │
   integer        struct          function
   float          array           closure
   bool           enum            trait
                  tuple           generic
                  slice
```

---

# 13. Static type system

Axiom là:

> **Statically typed**

Mỗi expression có type xác định tại compile time.

Ví dụ:

```axiom
let x = 42
```

compiler suy ra:

```text
x : i32
```

nếu literal context không yêu cầu type khác.

---

# 14. Type inference

Inference được phép nhưng phải predictable.

Ví dụ:

```axiom
let x = 10
let y = x * 2
```

compiler suy ra:

```text
x : i32
y : i32
```

Không có kiểu inference quá "thông minh" khiến cùng code thay đổi type bất ngờ.

---

# 15. Primitive type hierarchy

Core:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

Không có implicit conversion nguy hiểm kiểu C.

Ví dụ:

```axiom
let a: i32 = 10
let b: i64 = a
```

có thể cho phép conversion an toàn tùy rule.

Nhưng:

```axiom
let x: i32 = huge_u64
```

phải cần explicit conversion/check.

---

# 16. Struct

Struct là aggregate type chính.

```axiom
struct Point {
    x: f32
    y: f32
}
```

Không có class.

Không có:

```text
hidden object pointer
virtual table
inheritance metadata
```

trừ khi programmer explicitly yêu cầu abstraction tương ứng.

---

# 17. Methods thực chất là functions

```axiom
fn length(self: Point) -> f32 {
    ...
}
```

về semantic:

```text
length(point)
```

Syntax:

```axiom
point.length()
```

chỉ là convenience.

Điều này giúp compiler đơn giản hơn rất nhiều.

---

# 18. Trait

Trait mô tả capability.

```axiom
trait Drawable {
    fn draw(self)
}
```

Implementation:

```axiom
impl Drawable for Circle {
    fn draw(self) {
        ...
    }
}
```

Trait **không đồng nghĩa với inheritance**.

---

# 19. Generic

Ví dụ:

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Compiler có thể monomorphize:

```text
max<i32>
max<f32>
max<MyType>
```

thành code native chuyên biệt.

Điều này rất phù hợp mục tiêu:

> abstraction cao nhưng không trả runtime overhead.

---

# 20. Enum

Enum là sum type.

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

và:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Không cần null.

---

# 21. Pattern matching

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Compiler kiểm tra exhaustiveness.

Đồng thời compiler có thể lower thành:

```text
branch
jump table
conditional move
```

tùy target.

---

# 22. Function type

Function cũng là type.

Ví dụ:

```axiom
fn(i32) -> i32
```

Closure:

```axiom
let add = |x| x + offset
```

Compiler có thể biểu diễn closure thành:

```text
environment + function pointer
```

nhưng nếu có thể inline:

```text
không cần allocation
không cần function pointer
```

---

# 23. Dynamic dispatch

Axiom hỗ trợ dynamic dispatch nhưng không mặc định.

Conceptually:

```text
trait object
    │
    ├── data
    └── dispatch table
```

Nhưng chỉ khi programmer/system yêu cầu dynamic polymorphism.

Static generic dispatch vẫn là đường chính.

---

# 24. Type representation

Một invariant quan trọng:

> **Type semantics ≠ runtime type metadata.**

Compiler biết type:

```text
Point
Circle
Result<i32, Error>
```

nhưng binary không nhất thiết phải chứa type information.

Do đó:

```text
static type information
        ↓
compile-time
        ↓
removed
```

nếu không cần runtime reflection.

---

# 25. Axiom Concurrency Model v0.1

Đây là phần tôi nghĩ Axiom có thể làm **đơn giản hơn Rust**, nhưng vẫn giữ được safety.

Nguyên tắc:

> **Thread, async task và closure dùng cùng một ownership model.**

Không tạo ba hệ thống riêng biệt.

---

# 26. Ba cấp concurrency

```text
Level 0
Single-threaded

Level 1
Parallel threads

Level 2
Async tasks
```

Cả ba dùng chung:

```text
Value
Ownership
Send
Share
Atomic
Synchronization
```

---

# 27. Thread

Conceptual API:

```axiom
spawn(fn() {
    work()
})
```

Compiler/runtime tạo thread.

Nhưng Core không quy định scheduler cụ thể.

---

# 28. Send semantics

Khi value được chuyển sang thread:

```axiom
let data = Buffer(...)

spawn(move {
    process(data)
})
```

ownership chuyển:

```text
Thread A
   │
   │ move
   ↓
Thread B
```

Thread A không được sử dụng resource đó nữa.

Không cần:

```rust
Send + 'static
```

ở source syntax.

Compiler tự kiểm tra.

---

# 29. Shared data

Shared immutable data:

```text
Thread A ──read──┐
Thread B ──read──┼──> object
Thread C ──read──┘
```

được phép.

Mutable shared data cần synchronization:

```text
Mutex<T>
RwLock<T>
Atomic<T>
Channel<T>
```

hoặc cơ chế tương đương.

---

# 30. Data race

Invariant:

> **Safe Axiom code cannot contain data races.**

Compiler có thể dựa trên:

```text
ownership
alias analysis
Send/Share traits
atomic types
synchronization primitives
```

để đảm bảo.

`unsafe` có thể phá invariant này.

---

# 31. Send / Share nên là traits

Thay vì hard-code mọi type:

```text
Send
Share
```

có thể là compiler-known traits.

Conceptually:

```axiom
trait Send {}

trait Share {}
```

Compiler tự derive nếu các thành phần bên trong hợp lệ.

Ví dụ:

```text
struct Packet {
    data: Buffer
}
```

nếu `Buffer` là Send:

```text
Packet → Send
```

---

# 32. Atomics

Core phải hỗ trợ:

```text
load
store
exchange
compare_exchange
fetch_add
fetch_sub
...
```

với memory ordering:

```text
relaxed
acquire
release
acq_rel
seq_cst
```

đây là phần rất quan trọng để Axiom có thể viết lock-free/native systems code.

---

# 33. Async

Axiom không coi async là một memory model mới.

Ví dụ:

```axiom
async fn load() -> Data {
    ...
}
```

Compiler có thể lower thành:

```text
state machine
```

conceptually:

```text
State 0
  ↓ await
State 1
  ↓ await
State 2
  ↓
Return
```

Không bắt buộc mỗi async task phải tạo OS thread.

---

# 34. Async scheduler

Scheduler không thuộc Core.

Có thể có:

```text
single-thread executor
thread-pool executor
io executor
embedded executor
custom executor
```

Do library/runtime cung cấp.

Điều này giúp:

```text
Axiom program
```

có thể:

```text
không runtime
```

nếu không sử dụng async.

---

# 35. Compiler IR v0.1

Đây là phần cực kỳ quan trọng nếu mục tiêu cuối cùng là:

> Axiom compiler không phụ thuộc LLVM.

Tôi **không khuyên chỉ có một IR**.

Nên có pipeline:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed IR
  ↓
MIR
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Native Object
```

---

# 36. AST

AST giữ syntax.

Ví dụ:

```axiom
let x = a + b
```

AST:

```text
Let
 ├── name: x
 └── BinaryAdd
      ├── a
      └── b
```

AST không nên được dùng cho optimization.

---

# 37. HIR

HIR loại bỏ syntax noise.

Ví dụ:

```axiom
v.length()
```

HIR có thể thành:

```text
Call(
    length,
    v
)
```

Method syntax biến mất.

Tương tự:

```text
syntactic sugar
      ↓
canonical HIR
```

---

# 38. Typed IR

Typed IR thêm:

```text
Type
Ownership
Move
Copy
Borrow/View
Trait resolution
Generic instantiation
```

Ví dụ:

```text
%v : Vec2
%r : f32

%r = call Vec2_length(%v)
```

Đây là nơi compiler bắt đầu biết chính xác semantics.

---

# 39. MIR

Tôi đề xuất MIR là **ownership/control-flow IR**.

Ví dụ:

```text
fn process(x: Buffer)
```

MIR:

```text
BB0:
    move x → local0
    call process_buffer(local0)
    drop local0
    return
```

Compiler có thể nhìn rõ:

```text
move
drop
use
branch
return
```

Đây là nơi kiểm tra:

```text
use-after-move
double-drop
lifetime
escape
```

---

# 40. MIR nên dùng CFG

MIR không nên là tree.

Nó nên là:

```text
BasicBlock
    ↓
BasicBlock
   ↙   ↘
 BB2   BB3
   ↘   ↙
    BB4
```

Mỗi block chứa sequence instruction.

Ví dụ:

```text
BB0:
    x = load a
    if x > 0 goto BB1 else BB2

BB1:
    return 1

BB2:
    return 0
```

Điều này cực kỳ thuận lợi cho optimizer.

---

# 41. Axiom LIR

Sau MIR, ownership/type abstraction đã gần như biến mất.

LIR nên gần machine hơn:

```text
r1 = load [r2]
r3 = add r1, 1
store [r2], r3
```

Nhưng vẫn chưa phụ thuộc ISA cụ thể.

Ví dụ:

```text
virtual register
memory operand
branch
call
return
load
store
atomic
```

---

# 42. Machine IR

Machine IR target-specific.

Ví dụ:

```text
x86-64
ARM64
RISC-V
WASM
```

Mỗi backend thực hiện:

```text
Axiom LIR
   ↓
Target lowering
   ↓
Machine IR
   ↓
Register allocation
   ↓
Instruction selection
   ↓
Machine code
```

---

# 43. Không phụ thuộc LLVM

Kiến trúc nên là:

```text
                 Axiom IR
                    │
          ┌─────────┼─────────┐
          ↓         ↓         ↓
       x86-64      ARM64     RISC-V
          │         │         │
          ↓         ↓         ↓
        native    native    native
```

LLVM có thể tồn tại **ngoài architecture**:

```text
Axiom
 │
 ├── Native backend
 │
 └── LLVM backend (bootstrap/optional)
```

Nhưng semantic IR của Axiom không được biến thành LLVM IR.

---

# 44. IR phải preserve semantic ownership

Đây là khác biệt quan trọng.

LLVM IR không cần hiểu:

```text
move
ownership
drop
Send
Share
```

nhưng Axiom MIR phải hiểu.

Ví dụ:

```axiom
let b = a
```

nếu `a` là owning value:

```text
MOVE a → b
INVALIDATE a
```

Optimizer sau đó có thể loại bỏ physical move.

Nhưng semantic move vẫn tồn tại ở MIR.

---

# 45. Ownership lowering

Pipeline:

```text
Source
   │
   ▼
Typed MIR
   │
   │ ownership checking
   ▼
Ownership-valid MIR
   │
   │ drop elaboration
   ▼
Lowered MIR
   │
   ▼
LIR
```

Sau bước này:

```text
ownership semantics
```

đã được chuyển thành:

```text
explicit lifetime operations
```

ví dụ:

```text
drop
retain
release
```

chỉ xuất hiện nếu implementation thực sự cần.

---

# 46. Rất quan trọng: `drop` không đồng nghĩa `free`

Ví dụ:

```text
drop Buffer
```

có semantic:

```text
resource release
```

nhưng compiler có thể:

```text
inline release
stack object → no-op
arena object → no-op
dead object → eliminate
```

Do đó:

> **Drop là semantic operation, không phải bắt buộc một function call.**

---

# 47. Optimization pipeline

Một pipeline hợp lý:

```text
AST
 ↓
HIR
 ↓
Typed IR
 ↓
MIR
 ↓
Ownership analysis
 ↓
Drop elaboration
 ↓
Canonicalization
 ↓
Inlining
 ↓
Constant propagation
 ↓
DCE
 ↓
Generic specialization
 ↓
Escape analysis
 ↓
Scalar replacement
 ↓
Vectorization
 ↓
LIR
 ↓
Target optimization
 ↓
Machine code
```

---

# 48. Escape analysis rất quan trọng với Axiom

Ví dụ:

```axiom
fn make() -> Vec2 {
    let x = Vec2(...)
    return x
}
```

Compiler phải có khả năng nhận ra:

```text
x không cần heap
```

và có thể:

```text
return registers
```

thay vì:

```text
malloc
memcpy
free
```

Đây là một trong những chìa khóa để Axiom đạt mục tiêu performance mà vẫn có abstraction cao.

---

# 49. Memory optimization

Compiler có thể biến:

```text
heap object
```

thành:

```text
stack object
```

hoặc:

```text
registers
```

hoặc loại bỏ hoàn toàn.

Ví dụ:

```axiom
let p = Point(1, 2)
let x = p.x
return x
```

có thể cuối cùng chỉ còn:

```asm
return 1
```

---

# 50. Một kiến trúc tổng thể tôi đề xuất

```text
                   AXIOM SOURCE
                        │
                        ▼
                      Lexer
                        │
                        ▼
                       AST
                        │
                        ▼
                       HIR
                 syntax eliminated
                        │
                        ▼
                   Typed HIR
                        │
             ┌──────────┼──────────┐
             │          │          │
          Type       Trait      Generic
        checking    resolve    specialize
             │          │          │
             └──────────┼──────────┘
                        ▼
                       MIR
             ownership + control flow
                        │
             ┌──────────┼──────────┐
             │          │          │
         move/drop   escape      async
          analysis   analysis    lowering
             │          │          │
             └──────────┼──────────┘
                        ▼
                    Optimizer
                        │
                        ▼
                      Axiom LIR
                        │
             ┌──────────┼──────────┐
             │          │          │
           x86-64      ARM64      RISC-V
             │          │          │
             └──────────┼──────────┘
                        ▼
                 Machine IR
                        │
                        ▼
                 Register Allocator
                        │
                        ▼
                 Instruction Emit
                        │
                        ▼
              ELF / PE / Mach-O / WASM
```

---

# 51. Mối quan hệ giữa 4 specification

Tôi sẽ khóa dependency theo thứ tự:

```text
                AXIOM CORE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     TYPE SYSTEM          MEMORY MODEL
          │                   │
          └─────────┬─────────┘
                    ▼
             CONCURRENCY
                    │
                    ▼
              COMPILER IR
```

Không nên làm ngược.

Đặc biệt:

**Compiler IR không được quyết định language semantics.**

Ngược lại:

```text
Language semantics
       ↓
Memory/Type/Concurrency rules
       ↓
IR representation
       ↓
optimization
```

---

# 52. Một quyết định tôi muốn đặc biệt bảo vệ

Tôi nghĩ Axiom **không nên cố gắng loại bỏ pointer khỏi ngôn ngữ**.

Thay vào đó:

```text
                     Axiom
                       │
             ┌─────────┴─────────┐
             │                   │
          Safe Axiom          Unsafe Axiom
             │                   │
      values / slices       raw pointers
      structs              pointer arithmetic
      ownership            address manipulation
      traits               MMIO
      arrays               FFI tricks
      closures             allocators
      threads              kernel/driver
             │                   │
       95% application       5% systems
```

Đây sẽ là một điểm rất mạnh.

Programmer làm application **không phải sống với pointer**.

Nhưng programmer viết:

- OS
- allocator
- graphics driver
- embedded
- database engine
- runtime
- networking stack

vẫn có toàn bộ sức mạnh của C.

---

# 53. Và một quyết định còn quan trọng hơn

Tôi đề xuất Axiom **không cố làm "memory-safe bằng runtime"**.

Không:

```text
GC mọi thứ
```

Không:

```text
RC mọi thứ
```

Không:

```text
fat pointer mọi thứ
```

Không:

```text
runtime check mọi access
```

Mà:

```text
             compile time
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 ownership      type       concurrency
 analysis      checking      safety
      │           │           │
      └───────────┼───────────┘
                  ▼
             native code
```

Runtime chỉ xuất hiện khi **chương trình thực sự yêu cầu**.

Đây chính là cách Axiom có thể đồng thời hướng tới:

> **C/C++ level performance + modern safety + syntax đơn giản + native/no-runtime deployment.**

Và theo tôi, đây cũng là nền móng đúng để bước tiếp theo viết **`AXIOM-MEMORY-MODEL-v0.1.md`, `AXIOM-TYPE-SYSTEM-v0.1.md`, `AXIOM-CONCURRENCY-v0.1.md`, `AXIOM-IR-v0.1.md`** thành các spec có tính normative (`MUST / SHOULD / MAY`) thay vì chỉ mô tả ý tưởng.