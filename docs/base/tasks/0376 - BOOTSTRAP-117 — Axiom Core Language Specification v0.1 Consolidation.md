# BOOTSTRAP-117 — Axiom Core Language Specification v0.1 Consolidation

**Trạng thái: FROZEN / COMPLETED**

Đây là một mốc rất quan trọng. Từ đây, những gì đã khóa trước đó được gom thành **một semantic contract duy nhất**.

Mục tiêu của v0.1 không phải là có thật nhiều tính năng, mà là:

> **Một chương trình Axiom hợp lệ phải có semantics đủ chính xác để hai compiler độc lập có thể triển khai khác nhau nhưng vẫn cho cùng observable behavior.**

---

# 1. Ba lớp của Specification

Axiom v0.1 phải phân biệt:

```text
AXIOM LANGUAGE SPEC
│
├── Mandatory Semantics
│     └── mọi compiler phải tuân thủ
│
├── Implementation Freedom
│     └── compiler được tự do lựa chọn
│
└── Target / ABI Contracts
      └── phụ thuộc platform khi được khai báo
```

Ví dụ:

```text
let x = MyStruct { ... };
```

**Semantics bắt buộc:**

- `x` sở hữu value.
- Drop phải đúng quy tắc.
- Move phải được kiểm tra.
- Capability conflict phải được ngăn chặn.

**Implementation freedom:**

- `x` nằm register hay stack.
- struct có được scalarize hay không.
- có inline function hay không.
- physical layout cụ thể nếu không `@repr`.

---

# 2. Observable Semantics

Đây là khái niệm trung tâm của toàn specification.

Hai implementation được coi là tương đương nếu chúng giữ nguyên:

```text
value results
memory-visible behavior
I/O
atomic behavior
synchronization
panic/trap behavior
observable allocation/storage contracts
FFI behavior
volatile behavior
device/GPU effects
```

Nhưng compiler được phép thay đổi:

```text
register allocation
stack layout
temporary values
internal IR
allocation strategy
instruction selection
inlining
generic representation
```

nếu những thay đổi đó không trở thành observable.

---

# 3. Undefined Behavior

Axiom **không dùng UB như một công cụ tối ưu hóa phổ biến**.

Trong safe Core:

> Nếu chương trình vi phạm một invariant mà compiler có thể xác định, compiler phải reject hoặc chương trình phải đi vào một semantics đã được specification định nghĩa.

Ví dụ integer overflow không được mặc định thành C-style signed UB.

---

# 4. Ba loại hành vi

Specification phân biệt:

### Fully specified

Compiler phải cho cùng semantics.

### Implementation-defined

Compiler/platform chọn một giá trị trong tập được specification cho phép và phải công bố/inspect được lựa chọn đó.

### Target-defined

Phụ thuộc architecture/OS/ABI.

Ví dụ:

```text
size_of(usize)
calling convention
pointer width
endianness
```

---

# 5. Lexical layer

Axiom source mặc định:

```text
UTF-8
```

Compiler phải xử lý source Unicode đúng theo lexical specification.

Identifier có thể hỗ trợ Unicode, nhưng nên có giới hạn normalization rõ ràng để tránh hai identifier nhìn giống nhau nhưng khác code point.

Khuyến nghị v0.1:

> Identifier comparison dùng canonical lexical form được compiler chuẩn hóa; source spelling vẫn được giữ cho diagnostics.

---

# 6. Keywords v0.1

Bộ keyword nền tảng:

```text
fn
struct
enum
trait
impl
type
const
comptime

let
var

if
else
match
loop
while
for
in
break
continue
return

async
await

import
export
pub

unsafe

true
false

self
Self

as

where
```

Không đưa những keyword chưa có semantics vào Core chỉ để “dành chỗ”.

---

# 7. Identifier namespaces

Axiom không dùng một namespace duy nhất.

Tách:

```text
value namespace
type namespace
trait namespace
module namespace
label namespace
```

Ví dụ:

```text
struct Foo {}

fn Foo() {}
```

có thể được xử lý nếu namespace rules cho phép, nhưng resolution phải deterministic.

---

# 8. Declaration model

Các declaration chính:

```text
fn
struct
enum
trait
impl
type
const
module
import
```

Mỗi declaration có:

```text
DeclarationId
Visibility
SourceSpan
Type information
Attributes
```

Compiler resolution dựa trên ID, không dựa trên text sau khi parse.

---

# 9. Variables

Hai loại binding:

```text
let
var
```

`let`:

```text
immutable binding
```

`var`:

```text
mutable binding
```

Mutable binding **không đồng nghĩa** mutable shared access.

Capability vẫn kiểm soát việc mutation.

---

# 10. Evaluation order

Axiom dùng:

> **Left-to-right deterministic evaluation.**

Ví dụ:

```text
foo(a(), b(), c())
```

được evaluate:

```text
a()
↓
b()
↓
c()
↓
foo(...)
```

Receiver cũng được evaluate trước arguments.

Điều này giúp:

- predictable side effects;
- deterministic Drop/capability analysis;
- compiler diagnostics;
- AI reasoning.

---

# 11. Expressions

Expression gồm:

```text
literal
name
path
call
method call
field access
index
binary operator
unary operator
cast
bitcast
struct literal
array literal
tuple
enum constructor
if
match
loop
block
closure
comptime expression
```

Expression có type.

Một số expression có type:

```text
unit
never
```

---

# 12. Blocks

Block là expression:

```text
let x = {
    let a = 10;
    a + 20
};
```

giá trị cuối block là result.

Block không tự tạo runtime allocation.

---

# 13. `if`

Condition bắt buộc là:

```text
bool
```

Không có implicit:

```text
integer → bool
pointer → bool
```

Ví dụ C-style:

```text
if (x)
```

không hợp lệ nếu `x` là integer.

---

# 14. `match`

`match` là exhaustive.

Ví dụ:

```text
match value {
    Some(x) => ...
    None => ...
}
```

Compiler phải chứng minh coverage.

Pattern matching được lower thành decision tree nhưng semantics độc lập với implementation.

---

# 15. `enum`

Enum là algebraic data type.

Ví dụ:

```text
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Không có inheritance ngầm.

---

# 16. Struct

Struct là aggregate chính của Axiom.

```text
struct Point {
    x: f32,
    y: f32,
}
```

Không có class.

Method:

```text
fn length(self: view<Point>) -> f32
```

chỉ là function với receiver convention.

---

# 17. Method semantics

```text
p.length()
```

semantic equivalent:

```text
length(p)
```

Method resolution:

```text
inherent
→ trait
→ imported extension
→ generic extension
```

Nếu có nhiều candidate không phân giải được:

```text
compile error
```

---

# 18. Trait

Trait định nghĩa behavior contract.

```text
trait Printable {
    fn print(self: view<Self>);
}
```

Implementation:

```text
impl Printable for Foo {
    ...
}
```

Trait không mặc định tạo:

```text
object header
vtable
runtime type information
```

---

# 19. Dynamic dispatch

Static dispatch là mặc định.

Dynamic dispatch phải explicit:

```text
dyn Trait
```

Nếu không cần dynamic dispatch, compiler không được tự biến generic/static call thành runtime virtual dispatch.

---

# 20. Generic

Generic là compile-time abstraction.

```text
fn max<T: Ord>(a: T, b: T) -> T
```

Compiler có thể:

```text
monomorphize
specialize
share code
devirtualize
```

miễn giữ semantics.

---

# 21. Type identity

Phân biệt:

```text
type Alias = Foo;
```

với:

```text
struct NewFoo(Foo);
```

Alias:

```text
same semantic type identity
```

Newtype:

```text
distinct nominal type
```

---

# 22. Ownership

Mọi value có ownership state.

Core states:

```text
UNINIT
OWNED
MOVED
PARTIALLY_MOVED
DROPPED
```

Compiler theo dõi theo `Place`, không chỉ variable.

---

# 23. Move

```text
let b = a;
```

nếu `a` là non-Copy owning value:

```text
a → MOVED
b → OWNED
```

Move không nhất thiết có physical memory copy.

Compiler có thể:

```text
register transfer
pointer transfer
memcpy
nothing
```

tùy representation.

---

# 24. Copy

`Copy` là semantic duplication không tạo thêm ownership obligation.

Ví dụ:

```text
let b = a;
```

với `Copy`:

```text
a remains valid
b is independent semantic value
```

Compiler vẫn có thể không thực hiện physical copy nếu optimization cho phép.

---

# 25. Clone

`Clone` là explicit potentially expensive duplication.

```text
let b = a.clone();
```

Compiler **không tự chèn Clone**.

---

# 26. Drop

Drop là deterministic semantic cleanup.

Mặc định:

```text
reverse initialization order
```

Ví dụ:

```text
let a = A();
let b = B();
```

cleanup:

```text
B.drop()
A.drop()
```

---

# 27. Partial move

Nếu compiler-derived Drop cho phép:

```text
let x = struct_value;
let y = x.field;
```

thì phần còn lại có thể tiếp tục tồn tại.

Nhưng type có custom Drop:

```text
partial move forbidden
```

trừ khi một explicit semantic contract trong tương lai cho phép.

---

# 28. Capability model

Axiom không dùng programmer-facing:

```text
&T
&mut T
'a
```

trong Core.

Thay vào đó:

```text
view<T>
mut_view<T>
```

---

# 29. `view<T>`

Read capability:

```text
many readers
non-owning
```

Có thể duplicate capability nếu provenance vẫn hợp lệ.

---

# 30. `mut_view<T>`

Exclusive write capability:

```text
one active writer
```

Không được implicit duplicate.

---

# 31. Implicit owner → view

Được phép trong ephemeral call:

```text
fn print(x: view<Foo>)
print(foo)
```

Compiler tạo capability tạm thời.

Nhưng implicit conversion không được tự tạo escaping stored view.

---

# 32. Explicit view storage

Nếu muốn giữ view:

```text
let v = view(foo);
```

Đây là explicit semantic operation.

Compiler phải theo dõi provenance/lifetime.

---

# 33. Alias rules

Safe code:

```text
READ + READ → OK
READ + WRITE → conflict
WRITE + WRITE → conflict
MOVE + active capability → conflict
DROP + active capability → conflict
```

Nếu compiler chứng minh region disjoint:

```text
WRITE(A) + WRITE(B)
```

có thể hợp lệ.

---

# 34. Unknown aliasing

```text
UNKNOWN
```

không được coi là:

```text
DISJOINT
```

Đây là invariant cực quan trọng cho cả verifier lẫn optimizer.

---

# 35. Raw pointer

Chỉ system/unsafe:

```text
*const T
*mut T
```

Raw pointer không phải ownership.

Không có automatic:

```text
pointer → owner
```

---

# 36. Pointer provenance

Integer:

```text
usize
```

không mặc định là valid pointer.

Chuyển đổi địa chỉ ↔ pointer là unsafe/system và phải tuân thủ provenance rules.

---

# 37. Arrays

```text
[T; N]
```

là fixed-size value.

Có semantic contiguous ordering.

Compiler có thể:

```text
stack
register
inline aggregate
```

hoặc optimize khác nếu observable semantics không đổi.

---

# 38. Dynamic sequences

`Vec<T>` thuộc stdlib.

Không phải language primitive.

Semantics:

```text
logical sequence
length
capacity
storage
```

Relocation có thể xảy ra.

Active view có thể ngăn relocation trong khoảng lifetime cần thiết.

---

# 39. Strings

Axiom v0.1 phân biệt:

```text
String
Str
Bytes
CStr
```

`String`:

```text
owned UTF-8
```

`Str`:

```text
non-owning UTF-8 view
```

`Bytes`:

```text
arbitrary bytes
```

`CStr`:

```text
foreign null-terminated representation
```

---

# 40. Numeric types

Core:

```text
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
```

và:

```text
bool
unit
never
```

`i128/u128` có thể được hỗ trợ bởi type architecture nhưng không bắt buộc mọi target phải có native instruction.

---

# 41. Numeric conversion

Không implicit narrowing.

Ví dụ:

```text
i64 → i32
```

phải explicit.

```text
x as i32
```

hoặc conversion API có semantics tương ứng.

---

# 42. Overflow

Integer operations có semantics rõ ràng.

Axiom hỗ trợ conceptual operations:

```text
checked
wrapping
saturating
```

Arithmetic mặc định không được dựa vào C-style signed-overflow UB.

Compiler được phép tối ưu dựa trên semantics thực tế, không dựa trên UB giả định.

---

# 43. Floating-point

`f32/f64` tuân thủ target floating semantics trong specification.

Compiler không được tự ý biến:

```text
normal floating operation
```

thành fast-math operation nếu điều đó thay đổi observable semantics.

Fast math phải là explicit build/compiler contract.

---

# 44. Null

Không có null trong safe Core.

Absence:

```text
Option<T>
```

Raw pointer null chỉ thuộc unsafe/FFI domain.

---

# 45. Error model

Ba lớp:

```text
Result<T,E>   recoverable
panic         invariant/program failure
trap/abort    fatal machine/process failure
```

Không có exception hierarchy trong Core v0.1.

---

# 46. `?`

`?` là syntax sugar cho propagation của `Result`/`Option`.

Compiler phải preserve:

```text
Drop
ownership
control flow
```

khi lower `?`.

---

# 47. Panic

Panic policy:

```text
abort
unwind
custom
```

là compilation/runtime configuration.

Panic không phải exception object bắt buộc.

---

# 48. Evaluation and cleanup

Mọi control-flow exit phải chạy semantic cleanup cần thiết:

```text
return
break
continue
panic
```

Không được “quên Drop” chỉ vì đường control flow khác thường.

---

# 49. Closures

Closure là:

```text
code + environment
```

Capture mode compiler suy luận:

```text
READ
MUT
MOVE
```

Có thể ép move bằng syntax:

```text
move || ...
```

Closure không mặc định heap-allocate.

---

# 50. Function pointer

Phân biệt:

```text
fn(T) -> U
```

với capturing closure.

Noncapturing closure có thể decay thành function pointer nếu ABI phù hợp.

Capturing closure không thể tự nhiên biến thành function pointer mà mất environment.

---

# 51. Compile-time

Ba mode:

```text
const
comptime
runtime
```

`comptime` dùng compiler execution environment.

Generated code phải quay lại:

```text
resolve
type-check
ownership
verification
```

Không có đường bypass.

---

# 52. Reflection

Compile-time reflection được phép.

Runtime reflection:

```text
optional
```

và chỉ tồn tại nếu metadata được emit.

`Type` mặc định là compile-time entity, không phải runtime object.

---

# 53. Async

Core:

```text
async fn
await
Future
Poll
```

Async không đồng nghĩa thread.

Không có executor bắt buộc.

---

# 54. Async lowering

Conceptually:

```text
async fn
    ↓
state machine
    ↓
ordinary MIR
```

Chỉ những values sống qua suspension mới trở thành state.

---

# 55. Async safety

View/capability không được sống qua `.await` nếu storage/execution contract không đảm bảo validity.

Owned values có thể sống qua await.

`Send` phải được kiểm tra nếu Future được chuyển execution domain.

---

# 56. Threads

Thread là runtime/library facility.

Core chỉ định nghĩa semantic:

```text
Send
Share
synchronization
memory ordering
```

Thread implementation thuộc runtime/system layer.

---

# 57. Send / Share

`Send`:

> value có thể chuyển ownership sang execution domain khác.

`Share`:

> value có thể được shared-access theo contract.

Không được đồng nhất:

```text
Send == Share
Share == mutable thread safety
```

---

# 58. Memory ordering

Axiom định nghĩa:

```text
sequenced-before
synchronizes-with
happens-before
```

và atomic ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không có `Consume` trong v0.1.

---

# 59. Atomic

Atomic là type/semantic category riêng.

```text
Atomic<T>
```

không biến thành:

```text
mut_view<T>
```

Atomic access và ordinary mutable access là hai semantics khác nhau.

---

# 60. Volatile

Volatile khác atomic.

```text
volatile
≠
atomic
≠
synchronization
```

Volatile chủ yếu phục vụ device/hardware/system semantics.

---

# 61. GPU

GPU execution domain:

```text
@kernel
```

Storage domain:

```text
Host
Device
Shared
Local
Private
External
```

Host/device transfer phải explicit.

---

# 62. GPU safety

GPU dùng cùng semantic foundation:

```text
ownership
capability
Send-like transfer
synchronization
atomic
```

Nhưng kernel có legality rules riêng.

Kernel không tự nhiên được:

```text
File I/O
Socket
OS syscall
blocking mutex
```

---

# 63. Unsafe

`unsafe` không có nghĩa:

> compiler tắt mọi kiểm tra.

Nó có nghĩa:

> programmer/compiler contract cho phép một số operations mà safe verifier không thể tự chứng minh.

Sau boundary:

```text
unsafe contract
      ↓
safe capability
      ↓
normal verifier resumes
```

---

# 64. FFI

Ba ABI:

```text
Axiom ABI
C ABI
System ABI
```

Foreign call phải có explicit contract.

Không tự động coi:

```text
String
Vec
Arc
Future
closure
dyn Trait
```

là FFI-safe.

---

# 65. ABI

Semantic type:

```text
Type
```

khác:

```text
Representation
Layout
ABI
Machine encoding
```

Default layout compiler-controlled.

Explicit:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

---

# 66. `@repr(C)`

Đây là ABI/layout contract cho interoperability.

Không phải cách biến toàn bộ Axiom thành C.

---

# 67. `@repr(transparent)`

Newtype:

```text
struct UserId(u64);
```

có thể có representation ABI tương đương `u64` khi contract đáp ứng điều kiện.

Semantic type vẫn khác.

---

# 68. `@repr(packed)`

Unsafe/system.

Lý do:

```text
unaligned access
```

có thể tạo machine-level hazard.

---

# 69. Modules

Core:

```text
module
import
pub
```

Import là compile-time.

Không có runtime module loader bắt buộc.

---

# 70. Visibility

v0.1:

```text
private
pub
```

`pub` không đồng nghĩa external binary symbol.

Export:

```text
@export("name")
```

là ABI/linker concern.

---

# 71. Attributes

Attributes không phải một language thứ hai.

Chúng là compiler metadata:

```text
@repr
@cfg
@derive
@inline
@kernel
@export
@test
@bench
```

Unknown Core attribute phải được xử lý deterministic.

---

# 72. Storage model

Language semantics không quy định:

```text
stack
heap
register
arena
pool
```

Type có semantic value/ownership.

Compiler chọn physical storage.

---

# 73. Stable address

Address stability không mặc định.

Nếu API yêu cầu stable address:

```text
explicit storage contract
```

Compiler không được tự relocate.

---

# 74. Allocation

Allocation không phải language primitive bắt buộc.

Một chương trình Axiom hợp lệ có thể chạy:

```text
without heap
without allocator
without GC
without runtime
```

nếu code không yêu cầu chúng.

---

# 75. Runtime

Không có monolithic runtime.

Runtime components:

```text
allocator
panic
unwind
thread
sync
async
io
tls
gpu
reflection
...
```

chỉ link khi cần.

---

# 76. Standard library

Stdlib không định nghĩa language semantics mới.

Nó cung cấp:

```text
core
alloc
collections
string
unicode
math
io
fs
net
sync
thread
async
time
random
ffi
os
gpu
tensor
crypto
...
```

theo layering đã khóa ở BOOTSTRAP-114.

---

# 77. Compiler freedom

Compiler được phép:

```text
reorder fields
scalarize
inline
devirtualize
specialize
eliminate allocation
eliminate temporary
eliminate drop glue
vectorize
fuse operations
choose register allocation
choose instruction sequence
```

nếu semantics không thay đổi.

---

# 78. Những thứ compiler KHÔNG được tự ý thay đổi

Compiler không được tự ý:

```text
change evaluation order
invent Clone
invent synchronization
ignore ownership
assume UNKNOWN == DISJOINT
change atomic ordering
change volatile semantics
remove observable I/O
change FFI ABI
move stable-address storage
turn panic into success
```

chỉ để tối ưu.

---

# 79. `unsafe` boundary không phải optimization escape

Đây là invariant quan trọng:

```text
unsafe
```

không cho compiler quyền phá semantics của phần safe code xung quanh.

Unsafe chỉ cung cấp trusted preconditions.

---

# 80. Implementation-defined behavior

Nếu compiler cần lựa chọn:

```text
enum layout
padding
niche
calling convention
target-specific instruction
```

thì lựa chọn đó phải nằm trong phạm vi implementation freedom.

Nếu programmer cần biết lựa chọn đó, phải có:

```text
compile-time query
attribute
target contract
inspection API
```

Không có hidden semantic dependency.

---

# 81. Target-defined behavior

Ví dụ:

```text
usize width
pointer width
endianness
native ABI
atomic availability
SIMD features
```

được target description xác định.

Programmer có thể query compile-time.

---

# 82. Conformance levels

Một Axiom compiler có thể khai báo:

```text
Axiom Core v0.1
Axiom Core v0.1 + GPU
Axiom Core v0.1 + C ABI
```

nhưng nếu claim:

```text
Axiom Core v0.1 conformant
```

thì phải pass Core conformance suite.

---

# 83. Compiler portability contract

Hai compiler:

```text
Compiler A
Compiler B
```

có thể khác:

```text
register allocation
struct layout
instruction selection
optimization
```

nhưng cùng một source phải có cùng **specified observable semantics**.

---

# 84. Ví dụ

Source:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Compiler A:

```text
mov
add
ret
```

Compiler B:

```text
lea
ret
```

đều conformant nếu observable behavior giống nhau.

---

# 85. Ví dụ allocation

```text
fn make() -> Box<Point>
```

Một compiler có thể thật sự heap allocate.

Compiler khác có thể tối ưu caller allocation.

Nếu address không observable và semantics giống nhau:

```text
both conformant
```

---

# 86. Nhưng stable address khác

Nếu:

```text
stable_address(box)
```

là một explicit contract và address escape xảy ra:

```text
compiler may not relocate
```

Đây là lúc implementation freedom bị giới hạn bởi semantics.

---

# 87. Specification hierarchy

Từ đây Axiom spec chính thức có hierarchy:

```text
Axiom Specification
│
├── Core Language
│
├── Memory & Ownership
│
├── Concurrency Memory Model
│
├── Async Model
│
├── Comptime Model
│
├── FFI / ABI
│
├── GPU Model
│
├── Module Model
│
├── Attribute Model
│
└── Conformance Rules
```

Các tài liệu compiler/backend/runtime/stdlib nằm dưới Core Spec, không được mâu thuẫn với nó.

---

# 88. Semantic priority

Nếu có conflict:

```text
Core Language Specification
        ↑
Memory / Concurrency / ABI contracts
        ↑
Compiler implementation
        ↑
Optimizer
        ↑
Backend
```

Tầng dưới không được override tầng trên.

---

# 89. Core v0.1 chính thức không bao gồm

Để tránh scope creep, v0.1 **không bắt buộc**:

```text
classes
inheritance
exceptions
GC
borrow checker syntax
lifetime syntax
macro language
runtime reflection
dynamic typing
implicit numeric conversion
operator overloading via ad-hoc magic
C++ ABI
```

Traits + structs + enums + generics đã đủ để xây dựng abstraction mạnh.

---

# 90. Core v0.1 philosophy đã được khóa

Có thể cô đọng thành:

> **Axiom is a statically typed, value-oriented, ownership-aware native systems language with compiler-managed lifetime and capability verification, deterministic semantics, explicit unsafe boundaries, zero-cost abstraction as a design goal, and no mandatory garbage collector or monolithic runtime.**

---

# 91. Core invariants

Các invariant lớn được gom thành nhóm:

```text
ALANG-20..89
```

và bao phủ:

```text
syntax
typing
evaluation
ownership
capability
drop
numeric semantics
control flow
traits
generics
async
concurrency
comptime
unsafe
FFI
ABI
modules
attributes
GPU
```

Quan trọng nhất:

### `ALANG-20`
Core semantics are deterministic unless explicitly specified otherwise.

### `ALANG-21`
Value semantics are the default semantic model.

### `ALANG-22`
Ownership is compiler-verified.

### `ALANG-23`
Programmers do not write lifetime annotations in Core v0.1.

### `ALANG-24`
Safe code cannot create a verified dangling capability.

### `ALANG-25`
Safe code cannot contain conflicting mutable capabilities.

### `ALANG-26`
Move is semantic ownership transfer, not physical copying.

### `ALANG-27`
Copy is semantic duplication, not necessarily physical copying.

### `ALANG-28`
Clone is explicit.

### `ALANG-29`
Drop is deterministic.

### `ALANG-30`
Drop-bearing values are not Copy.

### `ALANG-31`
Unknown aliasing is never treated as proven disjoint.

### `ALANG-32`
Unsafe does not disable subsequent verification.

### `ALANG-33`
Safe code has no data races.

### `ALANG-34`
Async does not imply threading.

### `ALANG-35`
Threading does not imply async.

### `ALANG-36`
GPU execution and storage domains are explicit.

### `ALANG-37`
FFI boundaries are explicit.

### `ALANG-38`
ABI representation is distinct from semantic type.

### `ALANG-39`
Physical storage is not part of ordinary value semantics.

### `ALANG-40`
Heap allocation is not mandatory.

### `ALANG-41`
GC is not mandatory.

### `ALANG-42`
Runtime is not monolithic.

### `ALANG-43`
Compiler optimization cannot change observable semantics.

### `ALANG-44`
Implementation-defined behavior must remain within specification-defined freedom.

### `ALANG-45`
Target-defined behavior is explicit and inspectable.

### `ALANG-46`
Compiler implementation is not the semantic authority.

### `ALANG-47`
Standard library cannot silently redefine Core semantics.

### `ALANG-48`
Comptime-generated code undergoes normal verification.

### `ALANG-49`
No implicit Clone.

### `ALANG-50`
No implicit synchronization.

### `ALANG-51`
No implicit dynamic dispatch.

### `ALANG-52`
No implicit heap requirement.

### `ALANG-53`
No implicit null in safe Core.

### `ALANG-54`
Integer overflow semantics are defined.

### `ALANG-55`
Evaluation order is deterministic.

---

# 92. Axiom Core v0.1 đã đủ mạnh chưa?

**Có.**

Quan trọng hơn, nó đã đạt được mục tiêu ban đầu của chúng ta:

```text
C/C++ level:
    low-level control
    native compilation
    predictable layout when requested
    FFI
    SIMD
    atomics
    system programming

Rust-like strengths:
    ownership
    deterministic cleanup
    Send/Share
    safe aliasing
    pattern matching
    algebraic types

Modern language strengths:
    generics
    traits
    comptime
    async
    GPU
    reflection
    zero-cost abstraction

Axiom-specific:
    no lifetime syntax
    no programmer-facing borrow syntax
    struct-first design
    compiler-managed capability analysis
    compiler explanation API
    AI-readable semantic model
    no mandatory runtime
```

Đây là một Core tương đối lớn, nhưng **không phải vấn đề**. Mục tiêu của Axiom đã được xác định là **ngôn ngữ mạnh và thực dụng**, chứ không phải “core nhỏ nhất có thể”.

---

# 93. Một quyết định kiến trúc rất quan trọng đã được giải quyết

Ban đầu có nguy cơ Axiom đi theo hướng:

```text
C
+
Rust
+
Zig
+
Swift
+
CUDA
+
...
```

và trở thành một tập hợp feature rời rạc.

Sau consolidation, architecture đã có một semantic spine duy nhất:

```text
VALUE
  ↓
OWNERSHIP
  ↓
CAPABILITY
  ↓
EXECUTION DOMAIN
  ↓
SYNCHRONIZATION
  ↓
STORAGE DOMAIN
```

Mọi feature mới phải quy về spine này.

Ví dụ:

```text
Vec
 → ownership + capability

Arc
 → ownership + Share

Thread
 → ownership + Send

GPU
 → ownership + capability + execution/storage domain

Async
 → ownership + capability + suspension

FFI
 → ownership + capability + ABI

Tensor
 → storage domain + capability + execution domain
```

Đây là điều giúp Axiom tránh trở thành một ngôn ngữ “feature soup”.

---

# 94. BOOTSTRAP-117 hoàn tất

Axiom hiện đã chuyển từ:

```text
architecture notes
```

sang:

```text
semantic specification candidate
```

Bước tiếp theo hợp lý **không phải thêm feature**.

# BOOTSTRAP-118 — Axiom Grammar & Surface Syntax v0.1

Task 118 sẽ khóa **ngôn ngữ mà lập trình viên thực sự gõ**.

Cụ thể sẽ thiết kế hoàn chỉnh:

```text
Source File
    ↓
Tokens
    ↓
Grammar
    ↓
AST
```

và chốt:

- syntax declaration;
- function;
- struct;
- enum;
- trait;
- impl;
- generic;
- `where`;
- variable;
- expression;
- operators;
- method call;
- field access;
- indexing;
- closures;
- `async/await`;
- `match`;
- pattern;
- `if let`;
- loops;
- ranges;
- `?`;
- `comptime`;
- `view` / `mut_view`;
- attributes;
- modules/import;
- visibility;
- type syntax;
- function type syntax;
- `dyn Trait`;
- generic constraints;
- casts;
- `unsafe`;
- FFI declarations;
- comments/documentation;
- lexical ambiguities;
- precedence/associativity;
- semicolon rules;
- trailing commas;
- formatting conventions.

Đặc biệt, task này sẽ phải giải quyết một vấn đề rất quan trọng:

> **Làm thế nào để syntax của Axiom đơn giản hơn C++/Rust nhưng vẫn đủ biểu đạt cho toàn bộ semantic model phía dưới.**

Sau đó mới nên tiến sang **BOOTSTRAP-119 — Formal AST/HIR Semantic Contract**, rồi đến giai đoạn bắt đầu biến specification thành compiler architecture có thể code thật.