Được. Tôi sẽ coi đây là **baseline chính thức để các cuộc thảo luận và AI agent về sau không tự ý thay đổi semantic core**.

Tôi cố tình **không đưa GUI, GPU, AI, package manager, networking framework, OS API, IDE, build ecosystem...** vào đây. Chúng sẽ được đặc tả sau.

# Axiom Core Specification v0.1

**Status:** FROZEN  
**Scope:** Language semantic core  
**Priority:** Correctness → Predictability → Simplicity → Performance  
**Target:** Native systems programming

---

## 0. Triết lý cốt lõi

Axiom là ngôn ngữ native có:

- static typing
- value semantics
- deterministic resource lifetime
- ownership nhưng **không yêu cầu programmer viết lifetime/borrow annotation**
- không garbage collector bắt buộc
- không mandatory runtime
- zero-cost abstraction là mục tiêu thiết kế
- unsafe escape hatch
- explicit semantics
- compiler có quyền tối ưu mạnh nhưng không được thay đổi observable semantics.

### Nguyên tắc quan trọng nhất

> **Axiom phải đơn giản ở phía programmer nhưng không được mơ hồ ở phía compiler.**

---

# 1. Compilation Model

Một chương trình Axiom được biên dịch theo mô hình:

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
Optimization
  ↓
Machine IR
  ↓
Target Backend
```

Core language **không phụ thuộc LLVM hoặc compiler bên thứ ba về mặt semantic**.

Trong giai đoạn bootstrap, compiler bên ngoài có thể được sử dụng.

Mục tiêu dài hạn:

```text
Axiom compiler
      ↓
compile Axiom compiler
      ↓
self-hosting
```

---

# 2. Static Typing

Axiom là statically typed.

Mọi expression đều có type xác định tại compile time, ngoại trừ các cơ chế dynamic được explicit trong language/library sau này.

Ví dụ:

```axiom
let x: i32 = 10
let y = 20
```

Compiler suy luận:

```text
x : i32
y : integer type inferred from context
```

Type inference được phép.

Nhưng:

> **Type inference không được làm thay đổi semantics của chương trình theo cách khó đoán.**

---

# 3. Primitive Types

Core định nghĩa tối thiểu:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

Có thể bổ sung:

```text
i128
u128
```

nhưng không phải semantic requirement của v0.1.

---

# 4. No Implicit Numeric Chaos

Axiom không cho phép chuyển đổi số tùy tiện kiểu:

```text
i64 → f32
u64 → i32
```

mà không có quy tắc rõ ràng.

Các conversion nguy hiểm phải explicit.

Ví dụ khái niệm:

```axiom
let x: i32 = value as i32
```

Không cho phép C-style implicit conversion lan truyền toàn chương trình.

---

# 5. Struct là Data Primitive chính

Axiom **không có class trong core v0.1**.

Thay vào đó:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Struct:

- có layout
- có fields
- có value semantics
- có thể được truyền vào function
- có thể được trả về
- có thể được đặt inline trong struct khác.

---

# 6. Function

Function là primitive behavior chính.

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b
}
```

Không bắt buộc phải có object/class để tổ chức function.

---

# 7. Struct-associated Functions

Nếu tham số đầu tiên của function là một struct value/reference hợp lệ, function có thể được gọi theo method syntax.

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    ...
}
```

Có thể gọi:

```axiom
v.length()
```

Semantic vẫn là function call.

Tức:

```text
v.length()
```

không tạo ra một loại method runtime đặc biệt.

Đây là một quyết định quan trọng:

> **Method syntax là syntactic convenience, không phải object model.**

---

# 8. No Class Inheritance

Core không có:

```text
class
extends
base class
virtual class hierarchy
```

Thay vào đó sẽ dùng:

```text
struct
trait
impl
composition
```

---

# 9. Trait

Trait mô tả behavior/interface.

Ví dụ:

```axiom
trait Display {
    fn display(self)
}
```

Implementation:

```axiom
impl Display for User {
    fn display(self) {
        ...
    }
}
```

Trait không mặc định tạo object header hoặc vtable.

---

# 10. Dispatch

Axiom hỗ trợ hai dạng dispatch ở semantic level:

### Static dispatch

Compiler biết concrete type:

```text
direct call / inline / specialize
```

### Dynamic dispatch

Chỉ được sử dụng khi semantic yêu cầu dynamic polymorphism.

Dynamic dispatch **không phải mặc định**.

Mục tiêu:

```text
trait abstraction
        ↓
static dispatch whenever possible
```

---

# 11. Generics

Core hỗ trợ generic types/functions.

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    ...
}
```

Generic constraints thông qua trait.

Mục tiêu implementation:

> monomorphization/specialization trước.

Không tạo một runtime generic system lớn nếu không cần.

---

# 12. Value Semantics

Đây là nền móng của Axiom.

Mặc định:

```axiom
let a = Point { x: 1, y: 2 }
let b = a
```

`a` và `b` không mặc định là hai alias tới cùng một object.

Axiom ưu tiên:

> **value ≠ reference**

Điều này giúp compiler dễ reasoning về:

- layout
- lifetime
- optimization
- ownership
- parallelism.

---

# 13. Copy

Một type có thể là copyable.

Ví dụ primitive:

```text
i32
f64
bool
```

được copy.

Struct chỉ được copy nếu semantic/type rule cho phép.

Copy phải có semantics rõ ràng.

---

# 14. Move

Resource-owning values có thể được move.

Khái niệm:

```axiom
let a = create_buffer()
let b = a
```

Sau move, `a` không còn được sử dụng như một value hợp lệ.

Compiler phải phát hiện:

```text
use-after-move
```

tại compile time.

---

# 15. Ownership

Axiom có ownership semantics.

Nhưng:

> **programmer không phải viết borrow/lifetime annotation cho trường hợp thông thường.**

Compiler chịu trách nhiệm phân tích ownership.

Mục tiêu:

```text
ownership correctness
+
simple source syntax
```

---

# 16. Borrowing

Axiom **không clone Rust borrow checker syntax**.

Không yêu cầu:

```text
'a
&'a T
&mut T
```

trong programming model cơ bản.

Compiler vẫn có thể thực hiện:

```text
alias analysis
lifetime analysis
escape analysis
ownership analysis
```

để đảm bảo safety và tối ưu.

Đây là một điểm rất quan trọng:

> **Borrow checking là implementation mechanism, không phải user-facing language model.**

---

# 17. References

Reference là một semantic concept, nhưng không phải thứ programmer phải dùng thường xuyên.

High-level code ưu tiên:

```text
value
slice
array
buffer
owned object
```

Raw pointer chỉ xuất hiện trong low-level/unsafe code.

---

# 18. Pointer

Pointer **không bị loại bỏ khỏi Axiom**.

Nhưng được phân tầng.

### Safe layer

Programmer không cần thao tác raw pointer.

### Unsafe layer

Cho phép:

```text
raw pointer
pointer arithmetic
address manipulation
reinterpretation
volatile access
```

với semantics rõ ràng.

---

# 19. Unsafe

Axiom có explicit unsafe boundary.

Ví dụ:

```axiom
unsafe {
    ...
}
```

hoặc:

```axiom
unsafe fn ...
```

Unsafe code được phép thực hiện những thứ compiler không thể đảm bảo an toàn.

Nguyên tắc:

> **Safe Axiom phải có safety guarantees mạnh hơn C/C++.**

> **Unsafe Axiom phải đủ mạnh để viết system-level code.**

---

# 20. Memory Allocation

Core không bắt buộc một allocator duy nhất.

Có ba semantic category:

```text
value storage
owned dynamic storage
shared/dynamic storage
```

Compiler/runtime có thể sử dụng:

```text
stack
register
inline storage
heap
arena
pool
custom allocator
```

tùy implementation.

---

# 21. Không có GC bắt buộc

Axiom Core:

> **không yêu cầu garbage collector.**

Một chương trình đơn giản không được tự động kéo theo GC runtime.

GC có thể tồn tại trong ecosystem/library/runtime profile sau này.

---

# 22. Deterministic Destruction

Resource có lifetime xác định phải được giải phóng deterministic.

Ví dụ:

```text
file
socket
mutex
buffer
GPU resource
```

sẽ có destruction semantics.

Compiler có thể tự chèn destruction.

Programmer không phải luôn viết:

```text
free()
close()
destroy()
```

thủ công.

---

# 23. RAII nhưng không sao chép nguyên C++

Tư tưởng:

```text
acquire → own → release
```

được giữ.

Nhưng Axiom không cần:

```text
constructor/destructor/class hierarchy
```

để thực hiện nó.

Destruction là property của type/lifetime.

---

# 24. Shared Ownership

Core cho phép semantic shared ownership.

Nhưng shared ownership **không phải default**.

Khi cần, implementation có thể sử dụng:

```text
reference counting
atomic reference counting
arena
explicit lifetime
```

Cơ chế cụ thể sẽ được đặc tả sâu hơn ở Memory Model Specification.

---

# 25. Aliasing

Axiom phải phân biệt:

```text
unique ownership
shared access
mutable access
```

Compiler phải có đủ thông tin để tránh:

```text
use-after-free
double destruction
invalid mutation
```

và các aliasing violation tương ứng.

Đây là một trong những phần **chưa được phép tùy tiện thay đổi trong implementation**.

---

# 26. Arrays

Core có fixed-size array:

```axiom
let a: [4]i32
```

hoặc semantic tương đương.

Array nằm inline khi là value.

Không tự động heap allocation.

---

# 27. Slice

Slice là view tới contiguous sequence.

Khái niệm:

```text
pointer/reference + length
```

nhưng representation cụ thể thuộc ABI/implementation.

Programmer không phải thao tác raw pointer để sử dụng slice.

---

# 28. String

Core phải phân biệt ít nhất:

```text
byte sequence
Unicode text
```

Không được giả định:

> 1 character = 1 byte.

Representation cụ thể sẽ được đặc tả trong Text/String Specification.

---

# 29. Enum

Core có algebraic enum:

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

Enum có representation compiler-controlled mặc định.

FFI representation phải explicit.

---

# 30. Pattern Matching

Core có `match`.

Ví dụ:

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Compiler phải kiểm tra exhaustiveness ở compile time.

---

# 31. Null

Axiom Core **không dùng null như C/C++ pointer mặc định**.

Thay vào đó:

```text
Option<T>
```

được sử dụng cho giá trị có thể không tồn tại.

Raw null pointer chỉ thuộc unsafe/FFI territory.

---

# 32. Error Model

Core không dùng C++-style exception làm cơ chế lỗi mặc định.

Có:

```text
Result<T, E>
Option<T>
panic/trap
```

Error propagation syntax có thể được bổ sung nhưng phải giữ semantic này.

Mục tiêu:

> predictable control flow.

---

# 33. Evaluation Order

Axiom phải có evaluation order deterministic.

Compiler **không được** tùy tiện reorder các operation có observable side effects.

Compiler chỉ được reorder khi semantic observable behavior không thay đổi.

---

# 34. Integer Overflow

Core phải có semantics xác định.

Không được để:

```text
signed overflow
```

trở thành undefined behavior kiểu C.

Axiom sẽ hỗ trợ các semantics explicit:

```text
checked
wrapping
saturating
```

API/syntax chính xác sẽ được chốt trong Numeric Specification.

---

# 35. Mutability

Immutable by default.

Ví dụ:

```axiom
let x = ...
```

không được mutation.

Mutable:

```axiom
var x = ...
```

Đây là chủ ý:

> compiler dễ reasoning hơn + giảm accidental mutation.

---

# 36. Closures

Core hỗ trợ closure.

Ví dụ:

```axiom
let f = |x| x + 1
```

Closure capture phải có semantics rõ ràng:

```text
by value
by mutable ownership
by shared access
```

Compiler tự xác định hoặc yêu cầu explicit annotation khi ambiguity không thể giải quyết an toàn.

---

# 37. Concurrency

Core không giả định một concurrency runtime duy nhất.

Semantic primitives gồm:

```text
thread
atomic
synchronization
send/share semantics
```

API cấp cao sẽ được xây sau.

---

# 38. Data Race

Safe Axiom không được cho phép data race theo semantic model.

Tuy nhiên:

> cơ chế compiler đảm bảo điều này sẽ được đặc tả riêng trong Concurrency Model.

Unsafe code có thể phá vỡ guarantee.

---

# 39. Atomics

Core phải có atomic primitive đủ mạnh cho systems programming:

```text
atomic load
atomic store
CAS
fetch_add
memory ordering
```

Memory ordering model sẽ tương thích với target machine và có abstraction portable.

---

# 40. Async

`async/await` **không phải memory model riêng**.

Nó là một control-flow abstraction.

Compiler có thể transform:

```text
async fn
await
```

thành state machine/coroutine.

Scheduler/runtime là tầng phía trên.

---

# 41. Thread và Async không phải hai memory systems

Điểm này rất quan trọng.

Cùng một ownership model phải hoạt động với:

```text
normal call
closure
thread
async task
```

Không tạo bốn ownership systems khác nhau.

---

# 42. Compile-Time Evaluation

Axiom hỗ trợ compile-time execution.

Ví dụ:

```axiom
const x = calculate()
```

Compiler có thể evaluate function tại compile time nếu đủ điều kiện.

Mục tiêu:

```text
metaprogramming
+
optimization
+
constant generation
```

mà không cần một template language riêng.

---

# 43. Compile-Time Reflection

Core có thể expose compile-time information:

```text
type
fields
enum cases
traits
constants
```

Runtime reflection **không mặc định tồn tại**.

Metadata runtime chỉ được sinh khi programmer yêu cầu.

---

# 44. No Macro Language trong v0.1

Tôi đề xuất **không đóng băng macro system ở v0.1**.

Lý do:

Macro có ảnh hưởng rất lớn đến:

- parser
- hygiene
- tooling
- IDE
- compiler phases.

Để sau khi semantic core ổn định.

---

# 45. Modules

Core có module/import/export.

Ví dụ:

```axiom
import math
import io.File
```

Module là compile-time organization.

Không phải runtime object.

---

# 46. Visibility

Tối thiểu:

```text
private
public
```

Visibility được kiểm tra compile time.

Chi tiết package/module visibility sẽ để ecosystem specification.

---

# 47. ABI

Axiom Core phải có ABI concept rõ ràng.

Bao gồm:

```text
calling convention
type layout
alignment
return convention
parameter passing
symbol naming
FFI boundary
```

Default ABI là Axiom ABI.

Interop ABI phải explicit.

---

# 48. Struct Layout

Mặc định:

> compiler có quyền tối ưu layout.

Không được programmer giả định field layout nếu không explicit.

Có representation annotation cho FFI:

```axiom
#[repr(C)]
struct Foo { ... }
```

Chi tiết attribute system sẽ đặc tả sau.

---

# 49. No Mandatory Object Header

Một struct/value không tự động có:

```text
vtable pointer
GC metadata
reference counter
runtime type ID
object header
```

nếu semantic không yêu cầu.

Đây là một invariant quan trọng.

---

# 50. No Mandatory Runtime

Một chương trình Axiom chỉ dùng:

```text
primitive
struct
function
static memory
syscall/FFI
```

phải có khả năng compile thành native executable **không cần Axiom runtime lớn**.

Runtime components chỉ được link khi sử dụng.

---

# 51. Zero-Cost Abstraction Principle

Các abstraction như:

```text
generic
trait
method syntax
closure
iterator
Option
Result
```

phải có khả năng được compile thành code không có overhead tương ứng khi compiler có đủ thông tin.

Không phải mọi trường hợp đều bắt buộc zero-cost.

Nhưng:

> **Language design không được cố tình áp đặt runtime overhead nếu có thể tránh.**

---

# 52. Determinism

Compiler phải deterministic với cùng:

```text
source
compiler version
target
configuration
dependencies
```

AI không được tham gia vào semantic compilation.

AI chỉ là tooling.

---

# 53. Undefined Behavior

Axiom Core hạn chế UB trong safe language.

Safe code không được dựa vào:

```text
memory corruption
invalid lifetime
data race
use-after-free
double destruction
```

để có behavior hợp lệ.

Unsafe code có thể expose machine-level behavior.

---

# 54. Optimization Contract

Compiler có quyền:

```text
inline
eliminate
reorder
specialize
vectorize
constant-fold
dead-code eliminate
```

nhưng chỉ khi không thay đổi observable behavior theo Axiom semantics.

---

# 55. Debuggability

Compiler phải giữ đủ mapping:

```text
source
AST
IR
machine code
```

để debugger có thể hoạt động.

Debug metadata không phải runtime semantic.

---

# 56. FFI

Core phải có low-level FFI boundary.

Tối thiểu phải có khả năng mô tả:

```text
extern function
extern type/layout
calling convention
pointer
C-compatible representation
```

Chi tiết interop với từng platform để specification sau.

---

# 57. Không cố định Platform API trong Core

Core **không biết**:

```text
Windows
Linux
macOS
iOS
Android
CUDA
Vulkan
OpenGL
```

Core chỉ cung cấp primitives cần thiết để platform layer xây lên.

---

# 58. Memory Model — quyết định nền tảng

Axiom v0.1 chọn:

> **Flat virtual address space + typed value semantics + deterministic ownership-based resource management.**

Nhưng cần hiểu:

**flat address space không phải allocator.**

Allocator strategy là implementation/runtime concern.

Core không ép:

```text
malloc/free
GC
arena
pool
```

một mô hình duy nhất.

---

# 59. Allocation Principle

Mặc định:

```text
small value → register/stack/inline
large/resource object → compiler-selected storage
```

Programmer có thể yêu cầu allocation strategy ở low-level API.

Compiler có quyền stack-promote/inline/eliminate allocation nếu semantics cho phép.

---

# 60. Memory Safety Boundary

Từ góc nhìn người dùng:

```text
SAFE
────────────────────────
value
struct
array
slice
ownership
trait
generic
closure
async
thread
────────────────────────
UNSAFE
pointer
address
raw memory
FFI tricks
reinterpretation
hardware access
```

Đây là boundary quan trọng của Axiom.

---

# 61. Những thứ CỐ TÌNH KHÔNG CHỐT trong v0.1

Để tránh đóng băng quá sớm, các vấn đề sau **không thuộc Frozen Core v0.1**:

- exact ownership inference algorithm
- exact borrow checking algorithm
- allocator API
- garbage collector API
- exact async syntax
- exact error propagation syntax
- macro system
- package manager
- build system
- standard library
- OS API
- GUI
- GPU
- networking
- database
- AI/tensor
- game
- IDE
- debugger UI
- profiler
- distribution/registry
- cross-compilation workflow.

---

# 62. Nhưng những thứ trên không được phá Core

Đây là nguyên tắc:

> **Future specifications may extend Axiom, but must not silently invalidate Core semantics.**

Ví dụ GUI có thể thêm:

```text
AxiomUI
```

nhưng không được yêu cầu:

> mọi struct phải trở thành reference object.

GPU có thể thêm:

```text
GpuBuffer<T>
```

nhưng không được yêu cầu:

> Axiom phải có GC.

AI có thể thêm:

```text
Tensor<T>
```

nhưng không được biến:

> dynamic dispatch thành default language semantics.

---

# 63. Core Invariants

Tôi đề xuất đóng dấu 15 invariant sau:

```text
AXIOM-CORE-INVARIANTS
```

### ACI-01
Axiom is statically typed.

### ACI-02
Value semantics are the default.

### ACI-03
Struct is the primary aggregate type.

### ACI-04
Class inheritance is not part of Core.

### ACI-05
Trait-based polymorphism is supported.

### ACI-06
Generic programming is compile-time oriented.

### ACI-07
No mandatory garbage collector.

### ACI-08
No mandatory runtime.

### ACI-09
Safe code cannot rely on memory corruption.

### ACI-10
Raw pointers belong to unsafe/system-level programming.

### ACI-11
Resource lifetime is deterministic.

### ACI-12
Compiler may optimize aggressively without changing semantics.

### ACI-13
Abstractions must have a possible zero-cost implementation.

### ACI-14
Language semantics are deterministic and compiler-independent.

### ACI-15
Future libraries/frameworks must not redefine Core semantics.

---

# 64. Thứ tôi muốn coi là “linh hồn” của Axiom

Nếu phải rút toàn bộ specification này xuống chỉ còn 5 câu:

> **1. Value first.**  
> **2. Ownership without lifetime bureaucracy.**  
> **3. No mandatory runtime.**  
> **4. High-level by default, unsafe low-level when necessary.**  
> **5. The compiler may be extremely clever, but the language semantics must remain simple and deterministic.**

Đó là **Axiom Core v0.1**.

Và từ thời điểm này, tôi đề nghị coi nó là **frozen semantic contract**: mọi thiết kế tiếp theo — đặc biệt là **Memory Model, Type System, Concurrency Model và Compiler IR** — phải chứng minh rằng nó tuân thủ Core này, thay vì quay lại sửa Core tùy tiện.