# BOOTSTRAP-114 — Standard Library Architecture

**Trạng thái: FROZEN / COMPLETED**

Đây là task quan trọng vì từ đây Axiom không chỉ định nghĩa **ngôn ngữ**, mà định nghĩa luôn cách lập trình viên thực sự sử dụng nó.

Nguyên tắc trung tâm:

> **Core càng ổn định càng tốt; Stdlib cung cấp khả năng; Runtime chỉ xuất hiện khi khả năng đó thực sự cần runtime.**

Vì vậy:

```text id="k3v6u9"
                    AXIOM
                      │
        ┌─────────────┴─────────────┐
        │                           │
      CORE                       STDLIB
        │                           │
        │                 ┌─────────┴─────────┐
        │                 │                   │
   Language rules     Pure libraries    System libraries
        │                 │                   │
        │              no runtime       optional runtime
        │
        └──────── Compiler
```

---

# 1. Bốn tầng phải được phân biệt

Axiom có chính xác bốn tầng:

| Tầng | Ví dụ |
|---|---|
| **Language Core** | `struct`, `enum`, `fn`, `match`, ownership |
| **Compiler Builtin** | `size_of`, intrinsic atomic, SIMD |
| **Standard Library** | `Vec`, `String`, `HashMap`, `File` |
| **Runtime/System** | thread startup, OS syscall, allocator backend |

Không đưa tất cả vào Core.

---

# 2. `core`

`core` phải cực kỳ ổn định và không phụ thuộc OS.

Đề xuất:

```text id="xq4f4d"
std::core
├── primitive support
├── Option
├── Result
├── ordering
├── range
├── iterator traits
├── basic numeric traits
├── Copy
├── Clone
├── Drop
├── Send
├── Share
├── view abstractions
├── basic function traits
└── panic interface
```

`core` **không được yêu cầu heap**.

---

# 3. `Option` và `Result`

Đây là hai kiểu gần với semantics Core nhất.

Có thể compiler hiểu chúng ở mức:

```text id="7t4zlh"
?
match
niche optimization
never propagation
```

nhưng definition vẫn thuộc library-level semantic types:

```text id="frj8wq"
enum Option<T>
enum Result<T, E>
```

Compiler có thể special-case representation/optimization.

---

# 4. `Box`

```text id="95w2sg"
Box<T>
```

thuộc `alloc`, không phải Core primitive.

Semantics:

```text id="ppg6gd"
owned dynamic storage
Move
Drop
!Copy
```

Allocator backend có thể là:

```text id="f6a0kr"
system
custom
arena
pool
```

Compiler có thể loại allocation nếu address/storage identity không observable.

---

# 5. `Vec`

```text id="u1x9l5"
Vec<T>
```

là dynamic contiguous sequence.

Logical state:

```text id="3m3t3j"
pointer/storage
length
capacity
```

nhưng representation không phải public semantic contract.

API:

```text id="1ml1o7"
len()
capacity()
push()
pop()
reserve()
resize()
clear()
view()
mut_view()
```

---

# 6. View integration

Đây là một nơi Axiom có lợi thế lớn.

Ví dụ:

```text id="15cefj"
fn sum(xs: view<i32>) -> i32
```

gọi:

```text id="5zqgwm"
sum(values)
```

compiler tạo ephemeral capability.

Không cần:

```text id="6nqzri"
&values
```

hoặc:

```text id="1k9zqf"
borrow(values)
```

---

# 7. Mutable view

```text id="a0qv3a"
fn sort(xs: mut_view<i32>)
```

cho phép:

```text id="z05x0p"
sort(values)
```

Compiler kiểm tra:

```text id="f0kjju"
exclusive access
lifetime
alias
relocation
```

Không cần programmer viết lifetime.

---

# 8. `String`

Axiom phải phân biệt rõ:

```text id="r8qsv2"
String
Str
Bytes
CStr
```

### `String`

Owned UTF-8 text.

### `Str`

Non-owning UTF-8 text view.

### `Bytes`

Arbitrary byte sequence.

### `CStr`

Null-terminated foreign C-compatible string.

---

# 9. UTF-8 mặc định

Axiom dùng:

```text id="x8d8cl"
UTF-8
```

làm text encoding mặc định.

Nhưng:

```text id="0zflhy"
String.len()
```

nên xác định là **byte length** hoặc API phải đặt tên rõ.

Không giả vờ rằng:

```text id="ztrn6n"
1 Unicode scalar = 1 byte
```

---

# 10. Unicode

Unicode library:

```text id="1k1l4m"
std::unicode
```

cung cấp:

```text id="4hjw44"
Unicode scalar
grapheme
normalization
case mapping
classification
segmentation
```

Nhưng không biến Unicode thành runtime bắt buộc.

---

# 11. Iterator

Iterator nên là abstraction library nhưng compiler có thể optimize rất sâu.

```text id="u1pj7k"
trait Iterator {
    type Item;
    fn next(mut_view<Self>) -> Option<Self::Item>;
}
```

Ví dụ:

```text id="x2f4zq"
for x in values {
    ...
}
```

có thể lower thành loop trực tiếp.

Không cần runtime iterator object.

---

# 12. Iterator zero-cost

Pipeline:

```text id="i4r3m5"
iterator chain
    ↓
generic specialization
    ↓
inlining
    ↓
loop optimization
    ↓
vectorization
```

Mục tiêu:

```text id="axl3eg"
iterator abstraction cost ≈ handwritten loop
```

khi semantics tương đương.

---

# 13. Collections

Core collections:

```text id="8w1y8m"
Vec
Array
Slice/View
Deque
List
Map
Set
```

Nhưng không nên tạo hàng chục collection primitive.

Ưu tiên:

```text id="3n4q5w"
Vec
HashMap
BTreeMap
HashSet
BTreeSet
Deque
```

và abstractions composition.

---

# 14. HashMap

HashMap phải tách:

```text id="p0bq7s"
semantic map behavior
```

với:

```text id="6t1f4v"
hash algorithm
bucket layout
allocator
```

Hash algorithm không nên được coi là stable serialization format.

---

# 15. Deterministic collections

Axiom nên có:

```text id="l2y6vd"
HashMap
OrderedMap
```

Nếu iteration order cần deterministic:

```text id="m8u4kn"
OrderedMap
```

Không ép HashMap phải có stable order vì điều đó có thể làm giảm performance.

---

# 16. `Arc` và `Rc`

```text id="3l2f4n"
Rc<T>
Arc<T>
```

là library types.

Không phải:

```text id="d2v5s9"
language-level reference counting
```

`Rc`:

```text id="0v4o7r"
single execution domain
```

`Arc`:

```text id="q5n7as"
cross-thread shared ownership
```

---

# 17. `Weak`

Shared ownership cần:

```text id="e3q0rf"
Weak<T>
```

để phá cycle.

Không có:

```text id="c9n0tv"
automatic cycle collector
```

---

# 18. Allocation hierarchy

Stdlib nên chia:

```text id="x4v8nd"
core
  ↓
alloc
  ↓
collections
  ↓
io/fs/net/etc.
```

Ví dụ:

```text id="8b2m4k"
core::Option
```

không cần allocator.

```text id="f0k7zv"
alloc::Box
```

cần allocation capability.

```text id="q9n3sc"
std::fs::File
```

cần OS.

---

# 19. `alloc`

`alloc` cung cấp:

```text id="8j6p1h"
Allocator
Box
Vec
String
Arc
Rc
```

nhưng không có:

```text id="j4l2s7"
filesystem
thread
network
```

Điều này cho phép embedded dùng:

```text id="w7t0np"
core + alloc
```

mà không kéo OS.

---

# 20. Custom allocator

Trait:

```text id="j7d9xq"
trait Allocator
```

có thể hỗ trợ:

```text id="5p1r7v"
SystemAllocator
Arena
Pool
Slab
Bump
DeviceAllocator
```

Nhưng allocator không nên trở thành generic parameter của mọi type mặc định.

Ví dụ không muốn:

```text id="6qz0aa"
Vec<T, AllocatorA>
```

xuất hiện ở khắp nơi trong API cơ bản.

Compiler/runtime có thể resolve allocator context.

---

# 21. `std::io`

I/O abstractions:

```text id="qv4f6p"
Read
Write
Seek
Stream
Reader
Writer
Buffer
```

API ưu tiên capability:

```text id="j4t1cy"
fn read(mut_view<u8>) -> Result<usize, Error>
```

Không cần expose pointer.

---

# 22. Filesystem

```text id="x4x7om"
std::fs
```

gồm:

```text id="p4h1d8"
File
Directory
Path
Metadata
Permissions
```

`Path` nên phân biệt:

```text id="p1s7bn"
Path
PathBuf
```

tương tự `Str/String`.

---

# 23. Network

```text id="qv9x8d"
std::net
```

gồm:

```text id="7w6s1e"
Tcp
Udp
IpAddress
Socket
Listener
```

Không ép mọi network API phải async.

Sync:

```text id="j2a0st"
TcpStream.read()
```

Async:

```text id="s0j8y2"
TcpStream.read_async()
```

có thể cùng abstraction underlying.

---

# 24. Async library

Core chỉ có:

```text id="4k7z8n"
async
await
Future
Poll
```

Stdlib/runtime có:

```text id="w3s1f8"
Executor
Task
Timer
AsyncChannel
AsyncMutex
AsyncIO
```

Không có executor mặc định bắt buộc.

---

# 25. Channels

Stdlib:

```text id="y8x4s2"
Channel<T>
Sender<T>
Receiver<T>
```

Các specialization:

```text id="k3m9sa"
SPSC
MPSC
SPMC
MPMC
```

có thể được compiler/library tối ưu.

Ownership semantics:

```text id="s6c2fw"
send(value)
```

= ownership transfer.

---

# 26. Sync library

```text id="f9m3v0"
Mutex
RwLock
Semaphore
Condvar
Barrier
Once
```

Guards:

```text id="q7w2s8"
MutexGuard<T>
RwLockReadGuard<T>
RwLockWriteGuard<T>
```

là capability-bearing values.

Drop:

```text id="x5v1n6"
guard dropped
    ↓
unlock
```

---

# 27. Atomic

Compiler builtin cung cấp machine primitives:

```text id="9r2q4m"
atomic_load
atomic_store
atomic_rmw
fence
```

Stdlib expose:

```text id="b5z6k3"
Atomic<T>
AtomicBool
AtomicI32
AtomicU64
...
```

Compiler có thể specialize.

---

# 28. Time

```text id="z5h8s4"
std::time
```

phân biệt:

```text id="m2q7x1"
Instant
Duration
SystemTime
DateTime
Calendar
```

`Instant` dùng monotonic clock.

`SystemTime` dùng wall clock.

Không trộn hai khái niệm.

---

# 29. Random

```text id="u6p4x8"
std::random
```

phân biệt:

```text id="2n9s5c"
PRNG
CSPRNG
OS randomness
```

Không dùng `SystemTime` làm random source mặc định.

---

# 30. Math

```text id="m7z1w2"
std::math
```

gồm:

```text id="v4n6q8"
sqrt
sin
cos
exp
log
pow
min
max
clamp
```

Compiler có thể map tới:

```text id="2v7x4n"
hardware instruction
libm
vector implementation
```

tùy target.

---

# 31. SIMD

SIMD API:

```text id="r8k2c4"
std::simd
```

Ví dụ conceptual:

```text id="p9w4h6"
Simd<f32, 8>
```

Compiler có thể:

```text id="n4q7s1"
scalarize
vectorize
use AVX2
use AVX-512
use NEON
```

tùy target.

---

# 32. Tensor/GPU

Không đưa tensor vào Core.

Stdlib:

```text id="c3m7x9"
std::tensor
std::gpu
```

có:

```text id="t1v5n8"
Tensor
TensorView
DeviceBuffer
DeviceView
GpuEvent
Kernel
```

Các abstraction này sử dụng chính ownership/capability model đã khóa.

---

# 33. GPU không phá stdlib architecture

Ví dụ:

```text id="y4k8m2"
Tensor<f32>
```

có thể nằm ở:

```text id="5v7n1c"
CPU memory
GPU memory
Unified memory
```

nhưng storage domain phải explicit.

Không để:

```text id="3p6q9r"
Tensor
```

ngầm copy hàng GB dữ liệu từ CPU sang GPU.

---

# 34. FFI library

```text id="q5w8e1"
std::ffi
```

gồm:

```text id="8j3m7v"
CStr
CString
C ABI helpers
RawHandle
Symbol
Library
```

FFI vẫn tuân thủ ABI model.

---

# 35. OS library

```text id="b4n7x2"
std::os
```

không nên cố che toàn bộ platform-specific functionality.

Có:

```text id="f2m8q6"
std::os::linux
std::os::windows
std::os::macos
std::os::android
std::os::ios
```

cho API native.

---

# 36. Platform API

Ví dụ:

```text id="a8q3m6"
std::os::windows::Handle
std::os::linux::Fd
```

có thể tồn tại.

Nhưng portable API:

```text id="t5w9k1"
std::fs::File
```

nằm ở tầng cao hơn.

---

# 37. Error library

Không tạo một exception hierarchy khổng lồ.

Có:

```text id="g7k2v4"
Error
ErrorKind
Result<T,E>
```

System error có thể:

```text id="r1x6p9"
OsError
```

FFI error:

```text id="m8c3q5"
FfiError
```

Network:

```text id="n4v7s2"
NetworkError
```

---

# 38. Error composition

Không cần inheritance.

Có thể:

```text id="y3q8k6"
enum AppError {
    Io(IoError),
    Network(NetworkError),
    Parse(ParseError),
}
```

và:

```text id="v9m2c5"
match error
```

exhaustive.

Đây tận dụng trực tiếp algebraic enum.

---

# 39. Serialization

Serialization không thuộc Core.

```text id="q2w6n8"
std::encoding
```

có:

```text id="h4k9s1"
Json
Cbor
MessagePack
Binary
```

Wire representation **không phải memory representation**.

Điều này đã được khóa trong ABI/layout model.

---

# 40. Reflection

Runtime reflection không mặc định.

Compile-time:

```text id="x8m3q7"
Type
fields
methods
attributes
```

đã có qua comptime/reflection.

Runtime reflection chỉ khi package:

```text id="p5v9k2"
std::reflection
```

và binary thực sự emit metadata.

---

# 41. Logging

```text id="s4k8m1"
std::log
```

nên có abstraction:

```text id="j7n2x5"
Logger
LogRecord
Level
Sink
```

nhưng:

```text id="z3q6v8"
println()
```

không được kéo logging framework.

---

# 42. Testing

Test framework:

```text id="c8m4q2"
std::test
```

compiler có built-in support:

```text id="w6n1s9"
@test
@bench
```

nhưng test framework không được link vào production binary.

---

# 43. Benchmark

```text id="r4x7m2"
@bench
```

compiler/build system tạo benchmark artifact riêng.

Không có benchmark runtime trong release executable nếu không dùng.

---

# 44. Crypto

Crypto nên là library layer:

```text id="m5q8v3"
std::crypto
```

Không tự implement tất cả thuật toán trong compiler.

Có thể dùng:

```text id="f7n2k6"
pure Axiom
optimized native backend
external verified implementation
hardware acceleration
```

với ABI rõ ràng.

---

# 45. Security-sensitive APIs

Crypto/security API phải tránh:

```text id="c2m8q4"
hidden allocation
hidden logging
hidden network
```

và nếu cần constant-time semantics thì API/implementation phải thể hiện contract.

Compiler optimization không được phá contract.

---

# 46. Standard library layering

Kiến trúc đề xuất:

```text id="d6v2p9"
std
│
├── core
│
├── alloc
│
├── collections
│
├── string
│
├── unicode
│
├── math
│
├── simd
│
├── encoding
│
├── io
│
├── fs
│
├── net
│
├── process
│
├── time
│
├── random
│
├── sync
│
├── thread
│
├── async
│
├── ffi
│
├── os
│
├── gpu
│
├── tensor
│
├── crypto
│
├── log
└── test
```

---

# 47. Prelude

Prelude phải **rất nhỏ**.

Ví dụ tự động có:

```text id="c4w8m1"
Option
Result
Some
None
Ok
Err
Copy
Clone
Drop
view
mut_view
```

Không tự động import:

```text id="p7x2n9"
File
Socket
HashMap
Thread
Arc
```

nếu không cần.

`@no_prelude` vẫn được hỗ trợ.

---

# 48. API naming

Axiom nên thống nhất:

```text id="n8q4w2"
len()
is_empty()
capacity()
reserve()
clear()
push()
pop()
insert()
remove()
```

không có:

```text id="x6m1z8"
getLength()
Length()
sizeOf()
appendElement()
```

mỗi package một kiểu.

---

# 49. Receiver conventions

Stdlib tuân theo method sugar:

```text id="r2v8k5"
fn len(self: view<Self>) -> usize
fn push(self: mut_view<Self>, value: T)
```

Compiler biến:

```text id="q9m3x7"
v.len()
```

thành:

```text id="s5k1n8"
len(v)
```

Không cần class.

---

# 50. Ownership-friendly API

Tránh API kiểu:

```text id="y4p8m2"
fn foo(&mut self, ...)
```

Axiom:

```text id="h7n2q5"
fn foo(self: mut_view<Self>, ...)
```

hoặc:

```text id="v3m8x1"
fn consume(self: Self)
```

API phản ánh trực tiếp semantic model.

---

# 51. No hidden clone

Ví dụ:

```text id="u8q4m6"
fn consume(s: String)
```

gọi:

```text id="k2v9p3"
consume(text)
```

→ move.

Không tự clone.

Nếu cần:

```text id="w5n1r7"
consume(text.clone())
```

rõ ràng.

---

# 52. No hidden allocation

API stdlib không được ngầm:

```text id="m6q2x8"
allocate
```

nếu tên/contract không thể hiện.

Ví dụ:

```text id="r4v8k1"
String::format(...)
```

có thể allocate.

Trong khi:

```text id="x7n3m5"
write_into(buffer)
```

có thể zero-allocation.

API cần phân biệt được.

---

# 53. Borrow-free programmer model

Stdlib không yêu cầu:

```text id="e3r7q9"
lifetime parameters
borrow annotations
```

Compiler tự phân tích:

```text id="v5m1x8"
capability
alias
escape
lifetime
```

Đây là một trong những điểm cốt lõi khiến Axiom khác Rust ở trải nghiệm lập trình.

---

# 54. No GC standard library assumption

Không có:

```text id="k8q3v6"
Object
GC
Weak GC root
Finalizer
```

mặc định.

Nếu package muốn GC cho một subsystem cụ thể:

```text id="x1m7p4"
std::gc
```

có thể tồn tại như library/runtime component riêng.

Nhưng language semantics không phụ thuộc GC.

---

# 55. Resource types

Stdlib resource:

```text id="b6n2q8"
File
Socket
MutexGuard
ThreadHandle
GpuBuffer
MappedMemory
```

phải có:

```text id="r8x3m5"
Drop
```

và ownership rõ ràng.

---

# 56. Fallible cleanup

Không:

```text id="y2k7m4"
Drop → Result
```

Nếu đóng File có thể fail:

```text id="q9x4n1"
file.close() -> Result
```

Drop chỉ đảm bảo cleanup cuối cùng theo policy.

Điều này kế thừa memory model đã khóa.

---

# 57. Stdlib và zero-cost abstraction

Một abstraction được xem là zero-cost khi compiler có thể loại bỏ:

```text id="t7m2x5"
wrapper
generic dispatch
iterator object
closure environment
temporary
allocation
```

khi không observable.

Không có nghĩa mọi abstraction luôn miễn phí.

---

# 58. Stdlib performance tiers

Có thể phân loại:

```text id="j4x8q2"
Tier 0
Core primitives

Tier 1
Zero/low overhead data structures

Tier 2
OS abstractions

Tier 3
Convenience/high-level utilities
```

Programmer có thể chọn level phù hợp.

---

# 59. Stdlib ABI stability

Không phải toàn bộ stdlib đều có stable ABI.

Mặc định:

```text id="k3q7v9"
source/API compatibility
```

Ổn định ABI chỉ với:

```text id="m5x1n8"
explicit ABI-stable package
```

hoặc C ABI.

Điều này cho compiler nhiều tự do tối ưu.

---

# 60. Stdlib source implementation

Stdlib phần lớn nên viết bằng Axiom:

```text id="r8m4q2"
Axiom compiler
    ↓
Axiom stdlib
```

Chỉ những phần:

```text id="v6n2x9"
intrinsic
syscall
assembly
platform ABI
GPU driver interface
```

mới cần compiler intrinsic hoặc system/unsafe layer.

---

# 61. Stdlib invariants

### `ASTD-20`
Standard library is not part of the mandatory language core.

### `ASTD-21`
`core` does not require heap allocation.

### `ASTD-22`
`alloc` is optional.

### `ASTD-23`
OS-dependent libraries are optional.

### `ASTD-24`
Standard library APIs use Axiom ownership/capability semantics.

### `ASTD-25`
Standard library APIs do not require programmer-written lifetimes.

### `ASTD-26`
Standard library does not assume garbage collection.

### `ASTD-27`
Standard library does not assume reference counting.

### `ASTD-28`
`Option` represents absence rather than ordinary null.

### `ASTD-29`
`Result` represents recoverable failure.

### `ASTD-30`
`String` represents owned UTF-8 text.

### `ASTD-31`
`Bytes` represents arbitrary bytes.

### `ASTD-32`
C strings are explicit FFI types.

### `ASTD-33`
Collections do not imply a particular physical layout unless explicitly contracted.

### `ASTD-34`
Iterator abstractions are eligible for zero-cost specialization.

### `ASTD-35`
Async library components do not imply an executor in Core.

### `ASTD-36`
Thread libraries do not imply async execution.

### `ASTD-37`
Shared ownership is explicit.

### `ASTD-38`
Mutable shared state requires synchronization.

### `ASTD-39`
Resource types have deterministic cleanup.

### `ASTD-40`
Fallible cleanup is explicit rather than propagated through Drop.

### `ASTD-41`
Standard library abstractions do not silently clone owning values.

### `ASTD-42`
Standard library abstractions do not silently allocate unless their contract permits it.

### `ASTD-43`
GPU and device memory remain explicit storage domains.

### `ASTD-44`
Serialization representation is distinct from memory representation.

### `ASTD-45`
Runtime reflection is optional.

### `ASTD-46`
Compile-time reflection does not imply runtime metadata.

### `ASTD-47`
Platform-specific APIs are isolated from portable APIs.

### `ASTD-48`
The standard library may use unsafe/system operations internally behind verified abstractions.

### `ASTD-49`
Standard library internals are not required to expose their physical representation.

### `ASTD-50`
Standard library components are independently linkable.

### `ASTD-51`
Unused standard library components do not enter the final binary.

### `ASTD-52`
The standard library is primarily implementable in Axiom itself.

### `ASTD-53`
Compiler intrinsics are not automatically standard-library APIs.

### `ASTD-54`
Standard library APIs preserve deterministic language semantics.

### `ASTD-55`
Standard library evolution must preserve Core semantic contracts.

### `ASTD-56`
No standard-library module may silently introduce a mandatory monolithic runtime.

### `ASTD-57`
Axiom programs may use only `core` where platform constraints require it.

---

# 62. Trạng thái kiến trúc sau BOOTSTRAP-114

Axiom hiện đã khóa được gần như toàn bộ **language/toolchain stack**:

```text
┌───────────────────────────────────────┐
│              Axiom Apps              │
├───────────────────────────────────────┤
│             Standard Library         │
├───────────────────────────────────────┤
│       Runtime / Platform Layer       │
├───────────────────────────────────────┤
│             Axiom Compiler           │
├───────────────────────────────────────┤
│ MIR → OptIR → ABI → LIR → Machine IR │
├───────────────────────────────────────┤
│       Object Writer / Linker         │
├───────────────────────────────────────┤
│       Native OS / Hardware           │
└───────────────────────────────────────┘
```

Và quan trọng hơn, các tầng **không còn chồng chéo trách nhiệm**.

---

# BOOTSTRAP-115 — Compiler Tooling, Diagnostics & Developer/AI Interface

Task kế tiếp nên xử lý một phần rất quan trọng mà Axiom đặc biệt cần: **tooling**.

Không chỉ:

```text
axc file.ax
```

mà cần thiết kế ngay từ kiến trúc:

```text
ax
├── build
├── check
├── run
├── test
├── bench
├── fmt
├── doc
├── inspect
├── explain
├── query
├── lsp
├── package
├── publish
└── toolchain
```

Đặc biệt sẽ khóa:

- diagnostic model;
- stable error codes;
- compiler explanations;
- `axc explain`;
- ownership/capability visualization;
- MIR/OptIR inspection;
- ABI inspection;
- generated code inspection;
- LSP;
- autocomplete;
- go-to-definition;
- refactoring;
- formatter;
- documentation generation;
- test runner;
- benchmark runner;
- profiler integration;
- sanitizer integration;
- debugger integration;
- crash reports;
- machine-readable JSON diagnostics;
- AI-facing compiler API;
- AI có thể hỏi compiler **“tại sao đoạn code này bị reject?”** thay vì đoán;
- compiler có thể xuất dependency/build/IR graph cho agent;
- và quan trọng nhất: **AI tooling không được trở thành một phần của language semantics**.

Sau **BOOTSTRAP-115**, phần lớn kiến trúc developer experience sẽ hoàn chỉnh; sau đó có thể chuyển sang các task sâu hơn về **compiler correctness, conformance, testing và roadmap triển khai Axiom v0.1**.