Tiếp tục.

# BOOTSTRAP-048 — Standard Library, Core Library & Runtime Architecture Audit & Freeze

Đây là phần cần khóa để Axiom đạt đồng thời 3 mục tiêu tưởng như mâu thuẫn:

1. **Lập trình high-level thuận tiện.**
2. **Hiệu năng native, không runtime overhead bắt buộc.**
3. **Có thể tạo binary cực nhỏ / freestanding.**

Nguyên tắc trung tâm:

> **Library cung cấp capability; compiler chỉ cung cấp semantics; runtime chỉ xuất hiện khi chương trình thực sự cần.**

---

# 1. Bốn tầng của Axiom

Ta giữ cấu trúc:

```text
┌──────────────────────────────┐
│        Axiom Language        │
│     semantics + compiler     │
├──────────────────────────────┤
│          Core Library        │
│ fundamental types/protocols  │
├──────────────────────────────┤
│       Standard Library       │
│ batteries-included APIs      │
├──────────────────────────────┤
│       Optional Runtime       │
│ allocator / threads / async  │
│ panic / TLS / GPU / ...      │
└──────────────────────────────┘
```

---

# 2. Core Language không chứa library magic

Ví dụ `Vec` không phải keyword.

```axiom
let x: Vec<i32>
```

`Vec` là library type.

Compiler chỉ hiểu semantic contracts cần thiết như:

- ownership;
- capability;
- Drop;
- indexing;
- iteration;
- allocation semantics.

---

# 3. Core Library

Core Library phải đủ nhỏ để:

- freestanding;
- kernel;
- bootloader;
- embedded;
- compiler;
- runtime;
- GPU-supporting code

có thể sử dụng.

Đề xuất:

```text
axiom.core
axiom.mem
axiom.result
axiom.option
axiom.numeric
axiom.iterator
axiom.atomic
```

---

# 4. Standard Library

Standard Library chứa:

```text
collections
text
filesystem
process
network
time
random
compression
serialization
concurrency
async
platform
```

Nhưng không có nghĩa tất cả đều được link vào executable.

---

# 5. Optional Runtime

Runtime là implementation support.

Ví dụ:

```text
axiom.runtime.alloc
axiom.runtime.thread
axiom.runtime.async
axiom.runtime.panic
axiom.runtime.tls
axiom.runtime.gpu
```

Không dùng → không link.

---

# 6. Không có monolithic runtime

Axiom tuyệt đối không có kiểu:

```text
my_program
    ↓
libaxiom_runtime.so
    ↓
everything
```

mặc định.

---

# 7. Dependency-driven runtime

Ví dụ:

```axiom
fn main() {
    let x = 1 + 2
}
```

có thể không cần:

```text
allocator
thread scheduler
async executor
GC
reflection
network
filesystem
```

---

# 8. Binary tối thiểu

Mục tiêu:

```text
Source
 ↓
Axiom compiler
 ↓
native object
 ↓
link
 ↓
minimal executable
```

Compiler không chèn hidden initialization.

---

# 9. `main`

Hosted application:

```axiom
fn main() {
    ...
}
```

Compiler tạo entry adapter phù hợp target.

Nhưng `main` không phải runtime requirement.

---

# 10. Freestanding

System-level program có thể:

```axiom
@entry
fn kernel_entry() {
    ...
}
```

hoặc target-specific:

```axiom
@interrupt
fn reset_handler() { ... }
```

Không cần `main`.

---

# 11. Runtime profile

Build target có thể chọn:

```text
hosted
freestanding
kernel
embedded
gpu
```

Nhưng profile chủ yếu quyết định available capabilities và linker/entry policy.

Không thay đổi core semantics.

---

# 12. Allocator

Không có allocator mặc định bắt buộc trong language.

`Box`, `Vec`, `String` cần dynamic storage thì library/runtime cung cấp implementation.

---

# 13. Heap không phải language primitive

Không có:

```text
new
delete
malloc
free
```

trong Core syntax.

Có thể gọi allocator API explicit khi system programming.

---

# 14. `Box<T>`

```text
Box<T>
```

là ownership abstraction.

Semantic:

```text
owned dynamic storage
```

không phải:

```text
always malloc()
```

Compiler có thể stack-promote/eliminate nếu storage identity không observable.

---

# 15. `Vec<T>`

Semantic:

```text
ordered
growable
contiguous
owned
```

Representation implementation-defined.

Compiler/runtime có thể dùng:

```text
heap
arena
pool
custom allocator
stack
```

nếu semantic contract cho phép.

---

# 16. Không expose allocator generic mặc định

Không muốn API thành:

```text
Vec<T, Allocator>
```

ở khắp nơi.

Đây là một điểm rất quan trọng để tránh complexity kiểu systems language.

Allocator chỉ xuất hiện khi **allocator identity thực sự là semantic requirement**.

---

# 17. Khi nào allocator identity observable?

Ví dụ:

```axiom
arena.alloc<T>()
```

hoặc:

```axiom
buffer.with_allocator(A)
```

Khi đó allocator là explicit.

---

# 18. Arena

```axiom
let arena = Arena.new()
let x = arena.alloc(...)
```

Arena sở hữu storage.

Khi arena Drop:

```text
arena
 ↓
all allocations
 ↓
released together
```

Không cần GC.

---

# 19. Pool

Pool:

```text
fixed-size reusable slots
```

phù hợp:

- game objects;
- ECS;
- network packets;
- embedded;
- high-frequency allocation.

---

# 20. Slab

Slab là specialization của pool.

```text
N slots × fixed object size
```

Allocation/deallocation predictable.

---

# 21. Resource lifetime ≠ memory lifetime

Ví dụ:

```text
File
 ↓
close()
 ↓
resource released
```

nhưng memory object `File` có thể vẫn tồn tại cho đến Drop.

Đã freeze:

> Resource lifetime và memory lifetime là hai semantic concepts khác nhau.

---

# 22. `Drop`

Core protocol:

```axiom
trait Drop {
    fn drop(mut_view<Self>)
}
```

Compiler tự chèn cleanup.

Không cần programmer viết destructor syntax riêng.

---

# 23. Không hidden cleanup allocation

Drop không được âm thầm tạo allocator dependency nếu implementation không cần.

---

# 24. Panic

Panic runtime optional.

Profile:

```text
panic = abort
```

có thể rất nhỏ.

Hoặc:

```text
panic = unwind
```

cần unwinder/runtime support.

---

# 25. Không exception runtime

Axiom không có:

```text
exception object
catch stack
throw runtime
```

trong Core.

`Result` là ordinary value.

---

# 26. Result

```axiom
Result<T, E>
```

là enum:

```text
Ok(T)
Err(E)
```

Không allocation bắt buộc.

---

# 27. Option

```axiom
Option<T>
```

là enum:

```text
Some(T)
None
```

Compiler được phép niche-optimize.

---

# 28. IO

Standard API:

```axiom
File.open(path)
```

nhưng implementation có thể dùng OS system call trực tiếp.

Không cần libc.

---

# 29. OS layer

Tách:

```text
axiom.os
```

khỏi:

```text
axiom.io
```

Ví dụ:

```text
axiom.os.windows
axiom.os.linux
axiom.os.macos
axiom.os.android
```

---

# 30. Native syscall

System programming có thể:

```axiom
extern system fn syscall(...)
```

hoặc API platform.

Compiler không bắt buộc phải gọi C runtime.

---

# 31. libc optional

Một application có thể link libc nếu muốn.

Nhưng:

> **Axiom semantics không phụ thuộc libc.**

---

# 32. C ABI

C ABI là interoperability layer.

Ví dụ:

```axiom
extern "C" fn printf(...)
```

Không biến libc thành language dependency.

---

# 33. Thread library

Thread API thuộc library/runtime:

```axiom
thread::spawn(...)
```

Core chỉ biết:

```text
Send
Share
atomic
synchronization semantics
```

---

# 34. Thread creation không implicit

Không có:

```text
parallel for
```

tự động tạo thread trong Core.

Nếu compiler parallelize loop thì đó phải là optimization không observable hoặc explicit execution semantic.

---

# 35. Async

Async syntax đã freeze:

```axiom
async fn fetch() -> Result<Data, Error>
```

Nhưng executor không phải Core.

---

# 36. Executor

Ví dụ:

```axiom
async::run(...)
async::spawn(...)
```

là library/runtime.

---

# 37. Không link async runtime nếu không dùng

Chương trình synchronous:

```text
no Future
no executor
no waker
```

→ không cần async runtime.

---

# 38. Collections

Standard Library:

```text
Vec
Deque
HashMap
HashSet
BTreeMap
BTreeSet
```

---

# 39. Specialized collections

Có thể thêm:

```text
SmallVec
RingBuffer
BitSet
SlotMap
Arena
Pool
```

nhưng không đưa vào Core.

---

# 40. String

Đã freeze:

```text
str
String
Bytes
CStr
CString
Path
PathBuf
OsStr
OsString
```

---

# 41. Unicode

Core đảm bảo:

```text
String = valid UTF-8
```

nhưng:

```text
grapheme
normalization
collation
locale
```

thuộc library.

---

# 42. Formatting

```text
Display
Debug
```

library protocols.

Compiler có thể optimize formatting compile-time nếu input constant.

---

# 43. Serialization

Không phải magic compiler feature.

Ví dụ:

```text
JSON
CBOR
MessagePack
protobuf
```

là library/ecosystem.

---

# 44. Reflection

Compile-time reflection đã freeze.

Runtime reflection:

```text
optional
explicit metadata
```

---

# 45. No metadata by default

Nếu program không cần reflection:

```text
type metadata
field metadata
method metadata
```

không cần tồn tại trong executable.

---

# 46. Math

Core numeric primitives:

```text
i8...f64
```

Standard library:

```text
sqrt
sin
cos
log
exp
pow
...
```

Backend có thể lower xuống hardware instruction.

---

# 47. SIMD

Không cần SIMD type explosion trong Core.

Library API:

```text
simd::f32x4
```

Compiler recognizes/vectorizes.

---

# 48. Vectorization

Compiler có thể tự:

```text
scalar loop
    ↓
SIMD
```

nếu ownership/capability/alias semantics chứng minh an toàn.

Đây là một lợi thế của Axiom.

---

# 49. GPU

GPU library/runtime độc lập:

```text
axiom.gpu
```

CPU-only binary không link GPU runtime.

---

# 50. Tensor

Tensor không phải language primitive.

```text
Tensor<T>
DeviceTensor<T>
```

là library.

Compiler có thể hỗ trợ:

- shape specialization;
- kernel fusion;
- vectorization;
- GPU lowering.

---

# 51. Networking

```text
axiom.net
```

có:

```text
Tcp
Udp
Socket
Dns
```

Không phải Core.

---

# 52. Time

```text
Instant
Duration
DateTime
```

library.

System clock access là OS/runtime capability.

---

# 53. Random

Tách:

```text
deterministic PRNG
system entropy
```

Không implicit global RNG.

---

# 54. File system

```text
Path
File
Directory
```

library.

Permission errors → `Result`.

---

# 55. Process

```text
Process.spawn(...)
```

explicit.

Không hidden child process.

---

# 56. Environment

```text
env::get(...)
```

runtime/system capability.

Comptime environment đã có capability model riêng.

Không trộn comptime với runtime.

---

# 57. Logging

Logging không phải compiler feature.

```text
log::info(...)
```

có thể được DCE/configured out ở release nếu semantic policy cho phép.

---

# 58. Testing

```text
@test
```

đã có attribute.

Test runtime chỉ được link khi build test artifact.

Production binary không chứa test framework.

---

# 59. Benchmark

Tương tự:

```text
@bench
```

không đi vào production artifact.

---

# 60. Debug support

Debug metadata:

```text
source
→ MIR
→ LIR
→ machine
```

được tạo khi debug profile yêu cầu.

Release có thể strip.

---

# 61. Allocator replacement

System developer có thể chọn:

```text
general allocator
arena
pool
slab
custom
OS
```

mà không thay đổi Core semantics.

---

# 62. Runtime capability graph

Thay vì runtime monolith:

```text
Program
 │
 ├── allocator
 ├── panic
 ├── thread
 ├── async
 ├── TLS
 ├── GPU
 └── reflection
```

Linker chỉ kéo phần reachable.

---

# 63. Runtime components phải độc lập

Ví dụ program:

```text
File + Result
```

không tự động kéo:

```text
async
GPU
TLS
thread scheduler
reflection
```

---

# 64. Link-time dead stripping

Compiler/linker được phép loại bỏ runtime components không reachable.

---

# 65. Hidden runtime calls bị cấm

Đây là invariant quan trọng.

Compiler không được âm thầm biến:

```axiom
a + b
```

thành call runtime nếu target instruction trực tiếp biểu diễn semantics.

Nếu runtime call thực sự cần, ABI/implementation phải có lý do rõ ràng.

---

# 66. Hidden allocation bị cấm

Ví dụ:

```axiom
foo(x)
```

không được implicit:

```text
box x
allocate
call
free
```

chỉ vì abstraction.

---

# 67. Hidden synchronization bị cấm

Không có implicit:

```text
lock
unlock
```

chỉ vì value được share.

Synchronization phải đến từ explicit synchronization abstraction.

---

# 68. Hidden thread creation bị cấm

Compiler optimization có thể transform execution nếu semantics không observable, nhưng không được làm thay đổi các guarantees liên quan tới:

- thread identity;
- synchronization;
- scheduling;
- observable timing contracts.

---

# 69. Hidden GC bị cấm

Không có:

```text
GC safepoint
GC heap
GC thread
```

trừ khi một library/runtime được explicit sử dụng.

---

# 70. Hidden RC bị cấm

`Arc<T>` explicit.

Compiler không tự biến:

```text
T
```

thành reference-counted object.

---

# 71. Standard Library self-hosting

Mục tiêu cuối:

```text
Axiom compiler
       ↓
Axiom Standard Library
       ↓
Axiom Runtime
```

đều có thể viết bằng Axiom.

Không yêu cầu C++ implementation lâu dài.

---

# 72. Bootstrap dependency

Giai đoạn bootstrap có thể tạm dùng:

```text
C/C++
LLVM
system linker
```

nhưng đó là implementation bootstrap.

Không phải dependency semantic của Axiom.

---

# 73. Self-host transition

```text
Stage 0
External compiler
        ↓
Stage 1
Axiom frontend
        ↓
Stage 2
Axiom MIR/LIR
        ↓
Stage 3
Axiom backend
        ↓
Stage 4
Axiom compiler written in Axiom
        ↓
Stage 5
Self-hosting compiler
```

---

# 74. Standard Library ABI

Không expose internal representation như stable ABI.

Ví dụ:

```text
String
Vec
HashMap
Arc
```

có thể thay implementation mà không phá source semantics.

---

# 75. FFI boundary

Nếu cần stable binary ABI:

```text
@repr(C)
extern "C"
```

hoặc explicit Axiom ABI version.

---

# 76. Library versioning

Standard library semantic version phải độc lập với compiler implementation internals.

---

# 77. No “magic standard library”

Một API không được trở thành compiler magic chỉ vì nó nằm trong standard library.

Ngoại lệ chỉ dành cho những protocol compiler thực sự cần:

```text
Copy
Drop
Send
Share
Iterator
Index
...
```

và compiler-known intrinsics.

---

# 78. Compiler-known vs library-defined

Đây là ranh giới cần khóa:

### Compiler-known

```text
Option/Result control-flow syntax
Drop semantics
Copy semantics
Send/Share analysis
view/mut_view
atomic semantics
comptime
async lowering
traits/generic resolution
ABI
```

### Library-defined

```text
Vec
String
HashMap
File
Socket
Thread
Mutex
Arc
Arena
Tensor
GUI
HTTP
JSON
```

Một số loại nằm ở ranh giới nhưng semantics vẫn phải được mô tả bằng trait/protocol thay vì hard-code implementation.

---

# 79. `Arc` không phải Core primitive

`Arc<T>` có thể dùng:

```text
atomic refcount
```

nhưng đó là library implementation.

Compiler chỉ cần hiểu:

```text
Drop
Send
Share
```

---

# 80. `Mutex` cũng vậy

Compiler không cần hard-code:

```text
Mutex<T>
```

như một primitive type.

Nó cần hiểu capability + synchronization contracts mà abstraction cung cấp.

---

# 81. Standard library không được phá ownership model

Một library không thể tạo safe abstraction cho:

```text
use-after-free
data race
invalid capability
```

nếu contract không được compiler chứng minh hoặc unsafe boundary xác nhận.

---

# 82. Unsafe library

Low-level library có thể dùng:

```axiom
unsafe {
    ...
}
```

nhưng public safe API phải establish invariants trước khi trả capability cho caller.

---

# 83. Runtime-free example

Về mặt kiến trúc, chương trình kiểu:

```axiom
@entry
fn start() {
    let x: u64 = 42
    unsafe {
        ...
    }
}
```

có thể target:

```text
freestanding ELF
```

mà không cần:

```text
GC
allocator
thread runtime
async runtime
libc
```

---

# 84. Hosted example

Application:

```axiom
fn main() {
    let text = File.read("data.txt")?
    println(text)
}
```

có thể kéo:

```text
filesystem
OS adapter
allocator
panic policy
formatting
UTF-8
```

nhưng không kéo:

```text
GPU
async
reflection
thread scheduler
```

nếu không dùng.

---

# 85. Runtime dependency graph

Compiler/build system nên có thể xuất:

```text
Program
 ├── axiom.core
 ├── axiom.text
 ├── axiom.io
 ├── axiom.os
 └── runtime.alloc
```

AI agent có thể nhìn thấy chính xác vì sao từng component được link.

---

# 86. Binary audit

Build tool có thể cung cấp:

```text
axiom inspect runtime
axiom inspect dependencies
axiom inspect binary
```

Ví dụ:

```text
runtime:
  allocator       YES
  panic           YES
  unwind          NO
  threads         NO
  async           NO
  tls             NO
  gpu             NO
  reflection      NO
```

Đây sẽ rất hữu ích khi tối ưu binary.

---

# 87. Một điểm quan trọng về “binary nhỏ như ASM”

Không nên freeze yêu cầu:

> mọi Axiom binary phải nhỏ bằng assembly.

Điều đó không thể đảm bảo nếu chương trình sử dụng:

- Unicode;
- filesystem;
- TLS;
- networking;
- async;
- GPU;
- reflection.

Nên freeze mục tiêu chính xác hơn:

> **Axiom không thêm overhead runtime/metadata/code chỉ vì ngôn ngữ cung cấp abstraction. Binary size phải tỷ lệ với semantics thực sự được sử dụng.**

Đây là mục tiêu có thể kiểm chứng.

---

# BOOTSTRAP-048 — Invariants

```text
ASTD-101  Core Language semantics are independent of Standard Library implementation.
ASTD-102  Core Library contains only fundamental reusable protocols and types.
ASTD-103  Standard Library provides common APIs without becoming mandatory runtime infrastructure.
ASTD-104  Runtime components are optional and independently linkable.
ASTD-105  No monolithic mandatory Axiom runtime exists.
ASTD-106  Runtime dependencies are capability-driven and reachability-driven.
ASTD-107  Unused runtime components need not appear in the final artifact.
ASTD-108  Hosted programs may use main without requiring a monolithic runtime.
ASTD-109  Freestanding programs may define explicit entry semantics.
ASTD-110  Core Language does not require libc.
ASTD-111  C ABI interoperability does not make libc a language dependency.
ASTD-112  Dynamic allocation is not a Core Language requirement.
ASTD-113  Box represents owned dynamic-storage semantics, not mandatory physical heap allocation.
ASTD-114  Vec represents owned growable contiguous storage semantics.
ASTD-115  Allocator identity is not part of ordinary collection type semantics.
ASTD-116  Explicit allocator/storage abstractions may expose allocator identity.
ASTD-117  Arena allocation does not imply garbage collection.
ASTD-118  Pool and slab allocation are library/system abstractions.
ASTD-119  Resource lifetime is distinct from memory lifetime.
ASTD-120  Drop is deterministic and non-fallible.
ASTD-121  Panic infrastructure is optional.
ASTD-122  Abort panic profiles need not link an unwinder.
ASTD-123  Unwind support is optional runtime infrastructure.
ASTD-124  Axiom Core does not require exception objects or exception handlers.
ASTD-125  Result and Option do not require heap allocation.
ASTD-126  File and OS APIs are library/system abstractions.
ASTD-127  Syscalls are explicit system-layer operations.
ASTD-128  Thread creation is not implicit.
ASTD-129  Thread runtime is optional.
ASTD-130  Async executor infrastructure is optional.
ASTD-131  Programs not using async need not link async runtime components.
ASTD-132  GPU runtime is optional.
ASTD-133  CPU-only programs need not link GPU infrastructure.
ASTD-134  Runtime reflection requires explicit metadata emission.
ASTD-135  Compile-time reflection does not imply runtime reflection.
ASTD-136  Standard Library formatting does not imply hidden allocation.
ASTD-137  Standard Library APIs must preserve Core ownership and capability semantics.
ASTD-138  Standard Library cannot silently introduce GC.
ASTD-139  Standard Library cannot silently introduce reference counting.
ASTD-140  Standard Library cannot silently introduce synchronization.
ASTD-141  Standard Library cannot silently introduce thread creation.
ASTD-142  Compiler optimizations may eliminate library abstraction overhead when semantics permit.
ASTD-143  Compiler-known protocols must remain semantically distinct from their implementations.
ASTD-144  Arc is a library abstraction rather than an implicit language mechanism.
ASTD-145  Mutex is a synchronization abstraction rather than an implicit language mechanism.
ASTD-146  Custom allocators are explicit only when allocator identity is semantically relevant.
ASTD-147  Runtime component dependencies are inspectable.
ASTD-148  Build tooling can report runtime capability usage.
ASTD-149  Final artifacts contain only semantically reachable runtime/library components subject to explicit retention contracts.
ASTD-150  Hidden runtime initialization is prohibited unless explicitly specified by the program contract.
ASTD-151  Hidden allocation is prohibited unless explicitly specified by an abstraction's semantics.
ASTD-152  Hidden synchronization is prohibited unless explicitly specified by an abstraction's semantics.
ASTD-153  Hidden GC is prohibited by Core semantics.
ASTD-154  Hidden reference counting is prohibited by Core semantics.
ASTD-155  Standard Library representations are not stable ABI unless explicitly contracted.
ASTD-156  C ABI remains the initial stable interoperability boundary.
ASTD-157  Axiom compiler and libraries are intended to become self-hostable in Axiom.
ASTD-158  Bootstrap dependencies do not define Axiom language semantics.
ASTD-159  Runtime-free compilation is a supported architectural target.
ASTD-160  Binary size should track required semantics rather than language feature availability.
```

---

## Kiến trúc hiện tại đã khá hoàn chỉnh

Sau 048, phần nền của Axiom đã có chuỗi:

```text
020  Semantic Core
021  Type / Memory foundations
022  Memory model
023  Representation / ABI
024  Pointer / Reference / Handle
025  Type System
026  Functions / Methods
027  Control Flow
031  Generics / Traits
032  Closures
035  Errors / Panic
036  Attributes
037  Comptime / Reflection
038  Async
039  Concurrency
040  GPU
041  FFI
042  Package / Build
043  IR / Codegen
044  Library / Runtime boundary
045  String / Collections
046  Fundamental Traits
047  Namespace / Resolution
048  Standard Library / Runtime
```

Về mặt language design, đây đã chuyển từ một “ý tưởng ngôn ngữ” sang **một semantic architecture tương đối đầy đủ**.

### Phần tiếp theo tôi đề xuất không phải thêm feature ngay.

**BOOTSTRAP-049 — Axiom Generic/Monomorphization/Compile-time Performance & Code Size Audit** nên xử lý một vấn đề rất quan trọng đối với mục tiêu của bạn:

```text
Generics
   ↓
Monomorphization
   ↓
code duplication
   ↓
binary size
   ↓
compile time
   ↓
incremental cache
   ↓
LTO / specialization / deduplication
```

Mục tiêu là để Axiom vừa có **generic abstraction mạnh như C++**, vừa tránh tình trạng mỗi specialization tạo một đống code trùng, đồng thời giữ compile time và binary size thấp.