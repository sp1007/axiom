Tiếp tục với **BOOTSTRAP-044**.

# BOOTSTRAP-044 — Standard Library / Core Library / Runtime Boundary Audit & Freeze

Đây là phần cần khóa trước khi thiết kế API cụ thể. Nếu không, Axiom rất dễ rơi vào tình trạng:

> ngôn ngữ đơn giản → nhưng runtime + standard library trở thành một “quả bom” khổng lồ.

Mục tiêu của Axiom là ngược lại:

```text
                    AXIOM
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    Core Language   Core Library   Standard Library
        │              │              │
    semantics       fundamental      batteries
                       │
                 Optional Runtime
```

---

# 1. Bốn tầng phải phân biệt rõ

## Layer 1 — Core Language

Đây là thứ compiler **bắt buộc phải hiểu**.

Ví dụ:

```text
struct
enum
trait
fn
if
match
loop
generic
ownership
Copy
Drop
view
mut_view
async
comptime
unsafe
atomic semantics
```

Không được chuyển những semantic này thành library magic.

---

# 2. Core Library

Core Library là thư viện rất nhỏ nhưng nền tảng.

Nó có thể được compiler biết một phần.

Ví dụ:

```text
Option<T>
Result<T, E>
Box<T>
view<T>
mut_view<T>
Array<T, N>
Range
Iterator
```

Điểm quan trọng:

> **Core Library không đồng nghĩa runtime.**

Có thể dùng `Option` trong chương trình freestanding không có heap, OS hoặc thread runtime.

---

# 3. Standard Library

Standard Library cung cấp functionality phổ biến:

```text
String
Vec
HashMap
File
Socket
Path
Time
Thread
Process
JSON
Compression
Unicode
...
```

Nhưng chúng không phải semantic primitive của ngôn ngữ.

---

# 4. Optional Runtime

Runtime chỉ được link khi functionality cần nó.

Ví dụ:

```text
program
  ├── allocator
  ├── thread runtime
  ├── async executor
  ├── panic/unwind
  ├── GPU runtime
  └── reflection metadata
```

Không dùng cái nào → không link cái đó.

---

# 5. Nguyên tắc quan trọng nhất

> **Library abstraction must not secretly become language semantics.**

Ví dụ `Vec<T>` là library type.

Compiler không được mặc định giả định:

```text
Vec = heap pointer + length + capacity
```

Representation vẫn implementation detail.

---

# 6. `Option<T>`

`Option<T>` nên là Core Library ADT:

```axiom
enum Option<T> {
    Some(T),
    None
}
```

Compiler có thể special-case optimization:

```text
Option<NonNull<T>>
```

→ niche optimization.

Nhưng semantic vẫn là enum bình thường.

---

# 7. `Result<T,E>`

Tương tự:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

`?` là **language syntax**, nhưng `Result` là library type.

Điều này giữ Core nhỏ nhưng ergonomic.

---

# 8. `Box<T>`

`Box<T>` là Core Library.

Semantic:

> owned dynamic storage.

Không định nghĩa:

> luôn luôn heap.

Compiler có thể:

```text
heap
stack
register
caller allocation
scalarize
```

nếu observable semantics không bị thay đổi.

---

# 9. `Vec<T>`

`Vec<T>` là library abstraction.

Semantic tối thiểu:

```text
owned growable contiguous sequence
```

Không expose representation mặc định.

Compiler không được buộc:

```text
ptr + len + cap
```

nhưng implementation hiện tại hoàn toàn có thể dùng nó.

---

# 10. `Array<T,N>`

Array là language-level type hoặc primitive generic built-in representation.

Ví dụ:

```axiom
let a: [i32; 4]
```

Semantic:

- fixed length;
- contiguous;
- inline/value semantics;
- element order xác định.

---

# 11. Slice/View

Không nên biến `Slice` thành một collection riêng.

Axiom đã có:

```text
view<T>
mut_view<T>
```

Đây là capability abstraction.

Ví dụ:

```axiom
fn sum(x: view<i32>) -> i32
```

---

# 12. `String`

`String` là Core/Standard boundary đặc biệt.

Tôi đề xuất:

```text
str       = borrowed UTF-8 text view
String    = owned UTF-8 text
```

Không phải:

```text
char*
```

và cũng không phải C NUL string.

---

# 13. Bytes

Raw bytes:

```text
view<u8>
mut_view<u8>
```

hoặc collection:

```text
Buffer
```

không được đánh đồng với text.

---

# 14. Unicode

Compiler chỉ cần hiểu:

```text
UTF-8 source
string literal encoding
identifier rules
```

Không cần compiler runtime biết:

```text
grapheme cluster
Unicode normalization
locale
collation
```

Những thứ này thuộc library.

---

# 15. `char`

Nên là:

```text
Unicode scalar value
```

không phải UTF-8 byte và không phải grapheme.

---

# 16. Collections

Standard Library:

```text
Vec<T>
Deque<T>
List<T>       // nếu thực sự cần
HashMap<K,V>
HashSet<T>
BTreeMap<K,V>
BTreeSet<T>
```

Không nên nhồi tất cả vào Core.

---

# 17. Iterator

Iterator nên là trait:

```axiom
trait Iterator {
    type Item

    fn next(mut_view<Self>) -> Option<Self::Item>
}
```

Đây là ví dụ rất phù hợp với triết lý struct + function.

Không cần class hierarchy.

---

# 18. Iterator không allocation

Các iterator adapter:

```text
map
filter
take
zip
enumerate
chain
```

được generic + monomorphized.

Không bắt buộc:

```text
heap
virtual dispatch
```

---

# 19. Dynamic dispatch

`dyn Trait` thuộc Core type system.

Nhưng runtime object/vtable representation chỉ được sinh khi thực sự sử dụng.

Không có:

```text
object header
```

mặc định.

---

# 20. `Arc`

`Arc<T>` là library type.

Semantic:

```text
shared ownership
thread-capable reference counting
```

Compiler hiểu trait `Send` / `Share`, nhưng không cần hiểu implementation của atomic refcount.

---

# 21. `Rc`

Tương tự:

```text
Rc<T>
```

là local shared ownership.

Không tự động thread-safe.

---

# 22. Mutex

`Mutex<T>` là library/runtime abstraction.

Compiler đảm bảo các trait/capability semantics cần thiết, nhưng lock implementation có thể thay đổi.

---

# 23. `MutexGuard`

Đây là một abstraction rất quan trọng.

Concept:

```text
lock()
 ↓
Guard
 ↓
view<T> / mut_view<T>
```

Guard sở hữu quyền truy cập trong vùng critical section.

Khi Guard Drop:

```text
unlock()
```

---

# 24. Không đưa Mutex vào language

Không có:

```text
synchronized
lock keyword
monitor
```

trong Core.

API library đủ.

---

# 25. Atomic

Atomic là trường hợp khác.

Memory ordering là language/compiler semantic:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Nhưng API `Atomic<T>` có thể nằm ở Core Library/System Library.

Compiler intrinsic/backend hiểu atomic operations.

---

# 26. Thread

`Thread` không phải language primitive hoàn chỉnh.

Core chỉ định nghĩa:

```text
Send
Share
memory model
execution domain semantics
```

Thread API thuộc runtime/standard library.

---

# 27. `spawn`

```axiom
spawn(fn)
```

là library/runtime operation.

Compiler chỉ kiểm tra:

```text
closure/function Send
captures
ownership
```

---

# 28. Async

Core đã định nghĩa:

```text
async fn
await
Future
Poll
```

Nhưng:

```text
Executor
Scheduler
Reactor
Timer
```

không thuộc Core.

---

# 29. Future

`Future` là compiler-generated/library-visible abstraction.

Compiler có thể generate anonymous Future types.

Không cần:

```text
heap Future object
vtable
runtime allocation
```

---

# 30. Executor

Có thể có:

```text
SingleThreadExecutor
ThreadPoolExecutor
IoExecutor
DeterministicExecutor
```

đều là library/runtime.

---

# 31. File

File I/O không thuộc Core.

```text
File
Path
Directory
OpenOptions
```

thuộc Standard Library/System layer.

---

# 32. Socket

Tương tự:

```text
Tcp
Udp
UnixSocket
```

library.

---

# 33. OS abstraction

Axiom nên có:

```text
std.os
```

nhưng API portable chỉ bao phủ common subset.

Target-specific APIs:

```text
std.os.windows
std.os.linux
std.os.macos
std.os.android
```

---

# 34. Syscall

Syscall thuộc System layer.

```axiom
@syscall(...)
unsafe fn ...
```

đã có trong attribute design.

Không đưa từng syscall vào language.

---

# 35. Process

```text
Process
Command
ExitCode
Environment
```

Standard Library.

---

# 36. Time

Tách:

```text
Instant
Duration
SystemTime
Clock
```

và runtime/OS source.

Compiler không nên biết wall-clock semantics.

---

# 37. Random

Tách:

```text
Random
Rng
SecureRandom
```

library.

Comptime random đã có capability riêng.

---

# 38. Formatting

Không đưa formatting engine vào compiler.

Có:

```text
format
print
println
Debug
Display
```

library traits/macros sau này nếu cần.

---

# 39. `print`

`print()` không phải primitive language.

Freestanding program có thể không có `print`.

---

# 40. Panic

Panic semantic thuộc Core.

Nhưng panic implementation:

```text
abort
stack unwind
diagnostic
backtrace
```

thuộc runtime/profile.

---

# 41. Allocator

Allocator không phải language runtime bắt buộc.

Có thể có:

```text
std.alloc
```

với:

```text
GlobalAllocator
Arena
Pool
Slab
LinearAllocator
```

---

# 42. Custom allocator

Custom allocator là trait/library abstraction.

Không ép:

```text
Vec<T, A>
Box<T, A>
```

làm API mặc định.

Điều này phù hợp quyết định trước:

> allocator choice không phải mandatory generic parameter.

---

# 43. Arena

Ví dụ:

```axiom
let arena = Arena(...)
let x = arena.alloc(...)
```

Arena owns storage.

Compiler kiểm tra view không escape arena.

---

# 44. Pool

Pool cung cấp reusable stable slots.

Đặc biệt hữu ích cho:

```text
games
servers
embedded
real-time
```

nhưng vẫn library.

---

# 45. GPU

GPU library/runtime:

```text
Device
DeviceBuffer
DeviceView
GpuEvent
Kernel
```

Compiler chỉ hiểu semantic primitives:

```text
@kernel
execution domain
address space
atomic
barrier
```

---

# 46. Tensor

Tensor **không** thuộc Core.

Nên là:

```text
std.tensor
```

hoặc package ecosystem.

Compiler có thể có intrinsic/vector/matrix primitives để tối ưu.

---

# 47. SIMD

SIMD primitives có thể thuộc Core Intrinsics:

```text
simd<T,N>
```

nhưng high-level vector algorithms thuộc library.

---

# 48. Big integer

Không Core v1.

```text
BigInt
BigUint
Decimal
Rational
```

library.

---

# 49. Regex

Không Core.

Library/package.

---

# 50. Serialization

Không Core.

Ví dụ:

```text
JSON
TOML
CBOR
MessagePack
Protobuf
```

đều package/library.

---

# 51. Reflection

Compile-time reflection là Core semantic.

Runtime reflection:

```text
TypeInfo
FieldInfo
EnumInfo
```

chỉ được sinh khi explicit.

---

# 52. Testing

Compiler-known:

```text
@test
@bench
```

nhưng test framework/reporting không phải language.

---

# 53. Logging

Không Core.

```text
std.log
```

library.

---

# 54. CLI

Không Core.

```text
std.cli
```

library.

---

# 55. Networking stack

Không nên nằm trong standard library quá sâu.

Axiom nên cung cấp low-level primitives:

```text
Socket
TcpStream
UdpSocket
```

còn HTTP:

```text
package http
```

---

# 56. Database

Không Standard Library bắt buộc.

Package ecosystem.

---

# 57. GUI

Không Core.

Có thể có ecosystem:

```text
axiom-ui
axiom-gfx
```

Compiler chỉ cung cấp FFI/GPU/native capabilities cần thiết.

---

# 58. Game engine

Không Standard Library.

Axiom có thể tối ưu tốt cho game nhưng không biến engine thành compiler feature.

---

# 59. AI/Tensor

Tương tự.

Compiler hỗ trợ:

```text
SIMD
GPU
comptime
FFI
parallelism
```

Nhưng PyTorch-like framework là library/ecosystem.

---

# 60. Standard Library profile

Có thể chia:

```text
core
alloc
std
os
async
thread
gpu
net
crypto
```

---

# 61. `core`

Mục tiêu:

> Có thể dùng trong freestanding environment.

Ví dụ:

```text
Option
Result
Iterator
Array
Range
basic traits
format primitives nếu cần
```

---

# 62. `alloc`

Có allocation abstraction:

```text
Box
Vec
String
Arena
```

nhưng không nhất thiết OS.

Một embedded system có thể cung cấp allocator riêng.

---

# 63. `std`

Hosted environment:

```text
filesystem
process
environment
network
time
threads
terminal
```

---

# 64. `runtime`

Không nhất thiết programmer import trực tiếp.

Compiler/build system tự link component cần thiết.

---

# 65. Ví dụ chương trình freestanding

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Có thể compile thành:

```text
object
```

mà không link:

```text
GC
allocator
thread runtime
async runtime
libc
```

---

# 66. Ví dụ chương trình Vec

```axiom
fn main() {
    let mut v = Vec<i32>()
    v.push(1)
    v.push(2)
}
```

Chỉ cần allocator component mà `Vec` thực sự sử dụng.

---

# 67. Ví dụ async

```axiom
async fn main() {
    ...
}
```

Chỉ khi executor được sử dụng mới link async runtime.

---

# 68. Ví dụ GPU

```axiom
@kernel
fn add(...) { ... }
```

CPU-only executable không tự động mang GPU runtime.

---

# 69. Runtime linking model

Nên có:

```text
compiler
   ↓
dependency analysis
   ↓
runtime requirements
   ↓
component selection
   ↓
link only required components
```

---

# 70. Runtime manifest

Compiler có thể phát hiện:

```text
requires:
  allocator
  panic_abort
  thread
  async_executor
```

Không cần một monolithic `libaxiom-runtime`.

---

# 71. Runtime ABI

Runtime components phải có ABI rõ ràng.

Ví dụ:

```text
axiom_alloc_v1
axiom_thread_v1
axiom_async_v1
```

Nhưng tên/format cụ thể chưa cần freeze.

---

# 72. Standard Library không phải một package duy nhất

Về kiến trúc có thể:

```text
core
alloc
std
runtime
os
gpu
```

là các packages/components.

---

# 73. Compiler-known library APIs

Compiler có thể có intrinsic hooks cho:

```text
memcpy
memmove
memset
memcmp
atomic
sqrt
sin
cos
```

nhưng source-level API có thể là library.

---

# 74. Intrinsic không đồng nghĩa runtime

Ví dụ:

```axiom
memcpy(...)
```

compiler có thể lower thành:

```text
inline instructions
```

hoặc external symbol.

Không cần runtime.

---

# 75. ABI-sensitive library types

Các type:

```text
CStr
CString
RawSlice
ExternFn
```

thuộc FFI/System library.

---

# 76. OS handles

Ví dụ:

```text
FileHandle
SocketHandle
WindowHandle
GpuHandle
```

là foreign/system resource types.

Không phải raw pointer.

---

# 77. Handle semantics

Handle có:

```text
logical identity
ownership contract
```

và không tự động là:

```text
pointer
```

---

# 78. Error model trong library

Library dùng:

```text
Result<T, E>
```

cho recoverable failure.

Ví dụ:

```text
File.open() -> Result<File, IoError>
```

---

# 79. Không dùng exception

Standard Library không xây:

```text
throw IOException
```

hay exception hierarchy.

---

# 80. Drop trong library

Ví dụ:

```text
File
MutexGuard
Buffer
Socket
```

đều có thể có Drop.

Drop chỉ cleanup.

Fallible cleanup dùng explicit:

```text
close() -> Result<(), Error>
```

---

# 81. API design principle

Một API Axiom nên trả lời rõ:

```text
Who owns this?
Who may access this?
When is it valid?
Can it fail?
Can it block?
Can it move?
```

nhưng không bắt programmer viết lifetime annotations.

---

# 82. Blocking semantics

Các API blocking nên explicit bằng naming/type/profile.

Không để:

```text
read()
```

đột nhiên block trong async context mà không rõ.

---

# 83. Async API

Ví dụ:

```text
read()
read_async()
```

hoặc type-level async distinction.

Không nên làm mọi API tự động async.

---

# 84. Thread-safe API

Type system xác định:

```text
Send
Share
```

Library API quyết định synchronization.

---

# 85. Zero-cost standard abstractions

Mục tiêu:

```text
Iterator
Option
Result
Range
views
generic algorithms
```

phải có khả năng compile thành code tương đương hand-written code.

---

# 86. No hidden allocation

Một API không được âm thầm allocate nếu allocation không nằm trong semantic contract.

Đây là nguyên tắc rất quan trọng cho Axiom.

Ví dụ:

```text
sort(view<T>)
```

không được tự nhiên tạo heap allocation nếu API không công bố điều đó.

---

# 87. No hidden synchronization

Tương tự:

```text
get()
```

không nên âm thầm lock global mutex.

Synchronization phải nằm trong abstraction contract.

---

# 88. No hidden thread creation

Gọi một API không nên tự nhiên spawn thread trừ khi API/implementation contract nói rõ.

---

# 89. No hidden GC

Tất nhiên không có.

---

# 90. No hidden reference counting

`T` không tự nhiên biến thành:

```text
Rc<T>
Arc<T>
```

---

# 91. No hidden boxing

Generic/dyn dispatch không tự động heap-box.

---

# 92. No hidden exceptions

Library failure dùng Result/Option/panic theo semantics đã freeze.

---

# 93. Standard Library versioning

Standard library phải versioned độc lập với compiler semantic core nếu có thể.

---

# 94. `core` compatibility

Core API nên cực kỳ ổn định.

Breaking change cần kiểm soát nghiêm ngặt.

---

# 95. Platform abstraction

Standard library nên có interface portable:

```text
std.fs
std.net
std.thread
```

và backend:

```text
windows
linux
macos
android
...
```

---

# 96. No libc requirement

Đây là điểm rất quan trọng đối với mục tiêu Axiom.

Hosted standard library có thể dùng libc trong bootstrap.

Nhưng architecture **không được yêu cầu libc**.

Final implementation có thể:

```text
Axiom
 ↓
syscall/native API
```

---

# 97. Standard library implementation

Ban đầu có thể viết:

```text
Rust/C++/C
```

sau đó rewrite bằng Axiom.

---

# 98. Self-hosted standard library

Mục tiêu:

```text
Axiom compiler
      ↓
Axiom core
      ↓
Axiom standard library
      ↓
Axiom runtime components
```

đều có thể được xây bằng Axiom.

---

# 99. Package ecosystem

Standard Library chỉ cung cấp primitives đủ mạnh.

Phần còn lại:

```text
http
websocket
database
gui
game
ml
image
audio
video
crypto protocols
serialization
```

để ecosystem phát triển.

---

# 100. Boundary cuối cùng

Tôi đề xuất freeze như sau:

```text
┌────────────────────────────────────────────┐
│              AXIOM LANGUAGE               │
│                                            │
│ types / ownership / capability / control   │
│ traits / generics / async / comptime       │
│ unsafe / memory model / ABI semantics      │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│                CORE LIBRARY                │
│                                            │
│ Option / Result / Box / Array / Iterator   │
│ basic traits / views / fundamental types   │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│              STANDARD LIBRARY              │
│                                            │
│ String / Vec / HashMap / File / Socket     │
│ Thread / Time / Process / Unicode / etc.  │
└──────────────────────┬─────────────────────┘
                       │
┌──────────────────────▼─────────────────────┐
│             OPTIONAL RUNTIME               │
│                                            │
│ allocator / executor / scheduler / panic   │
│ threads / GPU / reflection / OS services   │
└────────────────────────────────────────────┘
```

---

# BOOTSTRAP-044 — Invariants

```text
ASTD-20   Core language defines semantics, not library implementation.
ASTD-21   Core Library does not imply runtime linkage.
ASTD-22   Standard Library is not part of the language type system.
ASTD-23   Runtime components are independently linkable.
ASTD-24   Unused runtime components must not be required.
ASTD-25   Library abstractions cannot silently alter language semantics.
ASTD-26   Library types do not require fixed physical representations.
ASTD-27   Box<T> represents owned dynamic-storage semantics, not mandatory heap placement.
ASTD-28   Vec<T> does not expose mandatory pointer-length-capacity representation.
ASTD-29   String is distinct from raw bytes.
ASTD-30   str represents borrowed UTF-8 text semantics.
ASTD-31   String represents owned UTF-8 text semantics.
ASTD-32   C strings are explicit FFI types.
ASTD-33   Option represents absence without null semantics.
ASTD-34   Result represents recoverable failure.
ASTD-35   Panic is distinct from Result failure.
ASTD-36   Iterator is a library abstraction.
ASTD-37   Generic iterator abstractions require no dynamic dispatch by default.
ASTD-38   Library abstractions must not require heap allocation unless specified.
ASTD-39   Library abstractions must not require hidden synchronization unless specified.
ASTD-40   Library abstractions must not implicitly spawn threads unless specified.
ASTD-41   Library abstractions must not introduce implicit GC.
ASTD-42   Library abstractions must not introduce implicit reference counting.
ASTD-43   Library abstractions must not introduce implicit boxing.
ASTD-44   Thread APIs are library/runtime facilities.
ASTD-45   Send and Share remain language-level semantic properties.
ASTD-46   Mutex and RwLock are library synchronization abstractions.
ASTD-47   Atomic ordering is language/compiler semantic.
ASTD-48   Atomic implementations remain backend/runtime dependent.
ASTD-49   Async syntax is language semantic.
ASTD-50   Async executors are runtime/library components.
ASTD-51   Future execution does not imply automatic spawning.
ASTD-52   File APIs are standard/system library facilities.
ASTD-53   Socket APIs are standard/system library facilities.
ASTD-54   Syscalls belong to the system layer.
ASTD-55   OS-specific APIs are explicit platform APIs.
ASTD-56   Standard Library failure uses Result/Option/panic semantics.
ASTD-57   Drop performs deterministic cleanup.
ASTD-58   Drop is not a replacement for explicit fallible close operations.
ASTD-59   Standard APIs must document ownership transfer semantics.
ASTD-60   Standard APIs must document blocking behavior where relevant.
ASTD-61   Standard APIs must document allocation behavior where semantically relevant.
ASTD-62   Standard APIs must not expose implementation-specific layout by default.
ASTD-63   FFI types require explicit representation contracts.
ASTD-64   Handle types represent logical/resource identity, not raw addresses.
ASTD-65   Standard Library must support freestanding subsets where practical.
ASTD-66   Freestanding programs need not link a monolithic runtime.
ASTD-67   Hosted programs may select runtime components independently.
ASTD-68   libc is not a mandatory semantic dependency.
ASTD-69   Axiom standard facilities may eventually be implemented entirely in Axiom.
ASTD-70   Bootstrap implementations may use external languages.
ASTD-71   Tensor/ML frameworks are not Core Language features.
ASTD-72   GUI frameworks are not Core Language features.
ASTD-73   Game engines are not Standard Library requirements.
ASTD-74   HTTP/database/application frameworks belong to ecosystem packages.
ASTD-75   GPU APIs are library/runtime abstractions over GPU language semantics.
ASTD-76   Runtime reflection is opt-in.
ASTD-77   Compile-time reflection is language/compiler functionality.
ASTD-78   SIMD primitives may be compiler intrinsics.
ASTD-79   High-level SIMD algorithms remain library abstractions.
ASTD-80   Big integer arithmetic is library functionality.
ASTD-81   Unicode algorithms beyond source/string validity are library functionality.
ASTD-82   Serialization is library/package functionality.
ASTD-83   Logging is library functionality.
ASTD-84   CLI facilities are library functionality.
ASTD-85   Standard Library must preserve zero-cost abstraction opportunities.
ASTD-86   Generic library code may be monomorphized and optimized away.
ASTD-87   Runtime requirements are derived from actual program semantics.
ASTD-88   Runtime selection must be deterministic.
ASTD-89   Standard Library components must have explicit dependency boundaries.
ASTD-90   Core Library must remain usable without OS facilities.
ASTD-91   Allocation facilities are separate from language ownership semantics.
ASTD-92   Allocator choice is not a mandatory generic parameter of ordinary containers.
ASTD-93   Hidden allocation is prohibited where it violates API semantics.
ASTD-94   Hidden synchronization is prohibited where it violates API semantics.
ASTD-95   Hidden execution-domain migration is prohibited where it violates API semantics.
ASTD-96   Library implementations may change physical representation without changing semantic contracts.
ASTD-97   Platform backends may differ while preserving portable library semantics.
ASTD-98   Standard Library versioning is distinct from compiler semantic versioning where feasible.
ASTD-99   Runtime-free programs remain a first-class Axiom target.
ASTD-100  Standard Library boundaries must not prevent eventual compiler/runtime self-hosting.
```

### Kết luận kiến trúc

Sau BOOTSTRAP-044, Axiom đã có một nguyên tắc khá mạnh:

> **Language định nghĩa “điều gì có nghĩa”. Library định nghĩa “làm việc đó như thế nào”. Runtime chỉ xuất hiện khi thật sự cần.**

Điều này đặc biệt quan trọng với mục tiêu của bạn về **binary nhỏ + native performance + không runtime bắt buộc**.

Bước tiếp theo hợp lý là **BOOTSTRAP-045 — String / Text / Bytes / Unicode / Collection Semantics**, vì đây là nhóm API mà chúng ta vừa xác định ranh giới nhưng **chưa freeze semantic chi tiết**.