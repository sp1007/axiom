# BOOTSTRAP-124 — Standard Library Implementation Contract

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là biến Standard Library từ một danh sách API thành **một kiến trúc có thể triển khai**, đồng thời bảo vệ nguyên tắc quan trọng:

> **Dùng một feature không được kéo theo runtime/dependency mà chương trình không cần.**

Ví dụ:

```ax
fn main() {
    print("Hello");
}
```

không được mặc định kéo:

- filesystem;
- network;
- async executor;
- thread pool;
- Unicode database đầy đủ;
- GPU runtime;
- reflection;
- crypto;
- allocator nếu compiler có thể eliminate nhu cầu.

---

# 1. Boundary cuối cùng

Axiom được chia thành 4 tầng:

```text
┌───────────────────────────────────────┐
│              Application              │
├───────────────────────────────────────┤
│           Standard Library            │
├───────────────────────────────────────┤
│        Optional Runtime Components     │
├───────────────────────────────────────┤
│        Platform / System Layer        │
├───────────────────────────────────────┤
│              Axiom Core               │
└───────────────────────────────────────┘
```

Nhưng đây **không phải dependency một chiều tuyệt đối**.

Một số stdlib module có thể gọi trực tiếp system abstraction:

```text
std::fs
   ↓
sys::filesystem
   ↓
OS
```

thay vì:

```text
std::fs
   ↓
monolithic runtime
   ↓
OS
```

---

# 2. Bốn loại thành phần

## Language Core

Ví dụ:

```text
if
match
struct
enum
fn
trait
async
comptime
unsafe
view<T>
mut_view<T>
```

Compiler hiểu trực tiếp.

---

## Compiler Builtin

Những thứ compiler phải nhận biết nhưng không nhất thiết là syntax:

```text
Copy
Clone
Drop
Send
Share
Sized
Type
size_of
align_of
offset_of
atomic primitives
intrinsics
```

---

## Runtime Component

Chỉ link nếu cần:

```text
allocator
thread
async executor
unwind
TLS
GPU runtime
IO runtime
```

---

## Standard Library

API programmer sử dụng:

```text
Vec
String
File
Socket
Mutex
Arc
HashMap
Future
Duration
Random
```

---

# 3. `std::core`

`core` phải cực kỳ nhỏ.

Đề xuất:

```text
std::core
├── primitive traits
├── Option
├── Result
├── basic tuples/utilities
├── ordering
├── range
├── iterator foundations
├── basic numeric traits
├── panic interface
├── basic memory utilities
└── compiler intrinsic wrappers
```

`core`:

- không filesystem;
- không network;
- không thread;
- không allocator bắt buộc;
- không OS;
- không GPU.

---

# 4. `Option`

```ax
enum Option<T> {
    Some(T),
    None,
}
```

Compiler/stdlib có thể tối ưu:

```text
Option<NonNull<T>>
Option<Box<T>>
Option<enum>
```

bằng niche representation.

Nhưng representation không trở thành semantic contract.

---

# 5. `Result`

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

`?` là compiler syntax.

Nhưng `Result` bản thân là stdlib type.

Điều này rất quan trọng:

> Compiler hiểu **propagation semantics**, nhưng không cần hardcode toàn bộ error type hierarchy.

---

# 6. `Copy`

`Copy` là compiler-known trait.

Concept:

```ax
trait Copy {}
```

Compiler dùng nó để quyết định:

```ax
let b = a;
```

là copy hay move.

Không có runtime method.

---

# 7. `Clone`

```ax
trait Clone {
    fn clone(self: view<Self>) -> Self;
}
```

Khác `Copy`:

```text
Copy  = implicit semantic duplication
Clone = explicit potentially-expensive duplication
```

---

# 8. `Drop`

```ax
trait Drop {
    fn drop(self: owning Self);
}
```

Nhưng user không trực tiếp gọi trait method.

Compiler generates drop glue.

Public API:

```ax
drop(value);
```

---

# 9. `Send` và `Share`

Compiler-known marker traits:

```ax
trait Send {}
trait Share {}
```

Không chứa runtime method.

Compiler suy ra implementation.

Không cho programmer khai báo giả:

```ax
unsafe impl Send
```

trong Core v0.1 nếu compiler không thể verify semantic contract.

---

# 10. `Box`

```ax
Box<T>
```

là stdlib abstraction.

Semantics:

```text
own one T in dynamically managed storage
```

nhưng **không bắt buộc physical heap allocation** nếu address/stable storage không observable.

Ví dụ:

```ax
let x = Box.new(value);
```

Compiler có thể biến thành:

```text
stack/register
```

nếu toàn bộ use pattern cho phép.

---

# 11. `Vec`

Logical model:

```text
Vec<T>
    pointer/storage
    length
    capacity
```

API:

```ax
let v = Vec<i32>.new();

v.push(10);
v.push(20);

let x = v[0];
```

View:

```ax
fn sum(values: view<i32>) -> i32
```

Conversion:

```ax
sum(v.view());
```

hoặc ephemeral:

```ax
sum(v);
```

nếu compiler/API context cho phép.

---

# 12. Vec relocation

```ax
v.push(x);
```

có thể relocate storage.

Do đó:

```ax
let view = v.view();
v.push(x);
```

phải bị reject nếu `view` còn live và operation có thể relocate.

Đây là application trực tiếp của capability model.

---

# 13. `String`

Axiom phân biệt:

```text
String
Str/view<Unicode text>
Bytes
```

`String`:

- owning;
- mutable;
- UTF-8 invariant.

Không có implicit conversion thành C string.

---

# 14. Text model

Canonical:

```text
String
    ↓
UTF-8 bytes
    ↓
validated Unicode text
```

Indexing byte:

```ax
text.bytes()[i]
```

khác character/grapheme traversal.

Không cho:

```ax
text[i]
```

với semantic giả định rằng một index = Unicode character.

---

# 15. Unicode

Tách:

```text
std::text
std::unicode
```

`String` không nhất thiết phải link toàn bộ Unicode database.

Basic UTF-8 validation/encoding có thể nằm trong `core/string`.

Unicode properties:

```text
std::unicode::category
std::unicode::normalize
std::unicode::grapheme
```

là optional data/module.

---

# 16. Collections

Core collection package:

```text
Vec
Deque
LinkedList
Array
Slice
HashMap
HashSet
BTreeMap
BTreeSet
```

Nhưng dependency graph phải granular.

Ví dụ:

```text
Vec
 ↓
core
```

không:

```text
Vec
 ↓
std
 ↓
everything
```

---

# 17. Iterator

Iterator là trait:

```ax
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

Adapter:

```text
map
filter
take
skip
zip
enumerate
fold
reduce
collect
```

Compiler/optimizer phải có khả năng inline/eliminate abstraction.

---

# 18. Iterator không phải allocation model

```ax
let sum = values
    .iter()
    .filter(...)
    .map(...)
    .fold(...);
```

không được mặc định tạo:

- iterator objects;
- heap allocations;
- virtual calls;
- dynamic dispatch.

Đây là zero-cost abstraction contract.

---

# 19. `Rc`

```ax
Rc<T>
```

- shared ownership;
- non-atomic reference count;
- single execution domain mặc định.

Không tự động Send.

---

# 20. `Arc`

```ax
Arc<T>
```

- shared ownership;
- atomic reference count;
- có thể Send/Share tùy `T`.

Quan trọng:

```text
Arc<T>
```

**không biến `T` thành thread-safe mutable object.**

---

# 21. Mutable shared state

Canonical:

```ax
Arc<Mutex<T>>
```

hoặc:

```ax
Arc<RwLock<T>>
```

hoặc:

```ax
Arc<Atomic<T>>
```

Ownership, capability và synchronization vẫn tách biệt.

---

# 22. Allocator module

```text
std::alloc
```

API:

```text
Allocator
GlobalAllocator
Arena
Pool
Slab
```

Nhưng allocator không phải Core language primitive.

---

# 23. Freestanding profile

Thay cho việc coi `no_std` là một hack, Axiom định nghĩa profile chính thức:

```text
profile = freestanding
```

Ví dụ:

```text
Axiom Core
+ std::core
+ selected libraries
```

không cần:

```text
OS
filesystem
network
thread
allocator
```

---

# 24. Hosted profile

Default application:

```text
profile = hosted
```

cho phép:

```text
OS
process
filesystem
network
threads
```

nhưng **vẫn chỉ link component thực sự được sử dụng**.

---

# 25. Kernel profile

```text
profile = kernel
```

cho phép:

- raw memory;
- interrupt;
- physical/virtual memory;
- device;
- scheduler;
- custom allocator.

Không kéo:

```text
libc
filesystem
normal process runtime
```

---

# 26. Embedded profile

```text
profile = embedded
```

được tối ưu cho:

- static memory;
- no allocator;
- no OS;
- interrupt;
- MMIO;
- device peripherals.

---

# 27. IO architecture

```text
std::io
├── Read
├── Write
├── Reader
├── Writer
├── BufferedReader
├── BufferedWriter
└── Stream
```

`std::io` không tự động yêu cầu network.

---

# 28. Filesystem

```text
std::fs
├── File
├── Directory
├── Path
├── Metadata
├── Permissions
```

Backend:

```text
sys::filesystem
```

---

# 29. Network

```text
std::net
├── Tcp
├── Udp
├── IpAddr
├── Socket
└── DNS
```

DNS có thể là dependency riêng.

Không được:

```text
std::net
→ entire OS runtime
```

---

# 30. Process

```text
std::process
├── Process
├── Command
├── ExitStatus
├── Environment
└── Signal
```

Chỉ hosted/system profiles.

---

# 31. Thread

```text
std::thread
```

API concept:

```ax
let handle = spawn(|| {
    work();
});

handle.join();
```

`spawn` là library/runtime operation, không phải language primitive.

Compiler chỉ kiểm tra:

```text
Send
Share
ownership
capture
```

---

# 32. Sync

```text
std::sync
├── Mutex
├── RwLock
├── Semaphore
├── Condvar
├── Barrier
├── Once
└── atomics
```

Atomic primitive compiler builtin, high-level atomic types stdlib.

---

# 33. Async

```text
std::async
├── Future
├── Poll
├── Waker
├── Executor
├── Task
├── JoinHandle
└── Cancellation
```

Nhưng:

```ax
async fn foo()
```

không tự link executor.

Chỉ khi chương trình sử dụng:

```ax
spawn(...)
executor.run(...)
```

runtime async mới được đưa vào dependency closure.

---

# 34. Time

```text
std::time
├── Duration
├── Instant
├── SystemTime
├── Clock
└── Timer
```

Phân biệt:

```text
Instant
```

với:

```text
SystemTime
```

để tránh dùng wall-clock cho duration measurement.

---

# 35. Random

```text
std::random
├── Random
├── SeededRng
├── SystemRandom
└── distributions
```

Randomness capability explicit.

Không có global hidden RNG.

---

# 36. Math

```text
std::math
├── scalar
├── trig
├── exp
├── log
├── constants
└── special
```

SIMD:

```text
std::simd
```

là module riêng.

---

# 37. SIMD

SIMD types:

```ax
let a: f32x8;
```

hoặc library abstraction:

```ax
let a = Simd<f32, 8>;
```

Compiler có thể lower thành:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
RVV
```

Không được expose ISA-specific assumption trong generic API trừ khi target feature yêu cầu.

---

# 38. GPU

```text
std::gpu
├── Device
├── DeviceBuffer
├── DeviceView
├── GpuEvent
├── Kernel
└── synchronization
```

Tensor:

```text
std::tensor
```

là tầng cao hơn GPU primitive.

---

# 39. Tensor

Không đặt tensor vào Core.

```text
std::tensor
    ↓
std::simd
    ↓
std::gpu
```

CPU-only tensor vẫn hoạt động.

Compiler có thể tối ưu:

```text
loop
→ SIMD
→ vectorized
→ GPU kernel
```

nếu semantics cho phép.

---

# 40. FFI

```text
std::ffi
├── CStr
├── CString
├── ForeignHandle
├── Symbol
├── ABI helpers
└── callback helpers
```

Raw pointer vẫn thuộc unsafe/system layer.

---

# 41. Serialization

Không đưa serialization vào Core.

```text
std::serialize
├── Encode
├── Decode
├── Serializer
└── Deserializer
```

Formats riêng:

```text
std::json
std::toml
std::binary
```

Dependency độc lập.

---

# 42. Crypto

```text
std::crypto
```

không được là mandatory std dependency.

Ví dụ:

```text
hash
sha
aes
chacha
tls
random
```

có thể tách package/module.

---

# 43. Logging

Không cần monolithic logging runtime.

```text
std::log
```

có:

```text
trace
debug
info
warn
error
```

Backend có thể compile out theo build profile.

Ví dụ:

```text
release + no debug logs
```

có thể loại bỏ hoàn toàn call site.

---

# 44. Testing

```text
std::test
```

hỗ trợ:

```ax
@test
fn test_add() {
    assert(add(1, 2) == 3);
}
```

Compiler driver:

```text
axc test
```

không phải runtime feature của production executable.

---

# 45. Benchmark

```ax
@bench
fn benchmark_parser() {
    ...
}
```

Benchmark infrastructure chỉ link vào benchmark binary.

---

# 46. Prelude

Axiom có prelude nhưng **rất nhỏ**.

Ví dụ:

```text
Option
Result
Some
None
Ok
Err
Copy
Clone
Drop
Iterator
```

Không tự import:

```text
File
Socket
Thread
Arc
HashMap
```

trừ khi API design chứng minh thực sự cần.

---

# 47. Explicit import vẫn là canonical

```ax
import std::collections::HashMap;
import std::sync::Arc;
```

AI rất dễ sinh code với import rõ ràng.

Compiler cũng dễ xác định dependency graph.

---

# 48. Stdlib dependency graph

Kiến trúc:

```text
                         ┌─────────────┐
                         │    core     │
                         └──────┬──────┘
                                │
             ┌──────────────────┼──────────────────┐
             ↓                  ↓                  ↓
          alloc             string             math
             │                  │
             ↓                  ↓
       collections           unicode
             │
      ┌──────┼────────┐
      ↓      ↓        ↓
     sync  thread    async
      │      │        │
      └──────┼────────┘
             ↓
            io
          ┌──┴──┐
          ↓     ↓
         fs     net
```

Không có:

```text
std
 └── everything
```

---

# 49. Dependency direction

Không được có cycle:

```text
core → alloc → core
```

hoặc:

```text
async → net → async
```

Nếu cần abstraction chung, tạo lower layer:

```text
core
  ↓
foundation
  ↓
io
  ↓
net
```

---

# 50. Runtime dependency closure

Compiler xây:

```text
Program dependencies
        ↓
Stdlib dependencies
        ↓
Runtime requirements
        ↓
Runtime component closure
```

Ví dụ chương trình:

```ax
fn main() {
    let x = Vec<i32>.new();
    ...
}
```

có thể cần:

```text
core
alloc
collections
allocator
startup
```

Nhưng không:

```text
network
async
thread
GPU
unicode database
```

---

# 51. Runtime elimination

Nếu:

```ax
fn main() {
    let x = 10;
    print_integer(x);
}
```

và implementation có thể dùng direct syscall:

compiler/linker có quyền loại bỏ:

```text
allocator
```

nếu không cần.

Tương tự:

```text
panic runtime
unwind
thread runtime
async executor
```

được loại bỏ nếu không reachable.

---

# 52. `panic`

Stdlib cung cấp:

```text
panic(message)
```

Compiler/runtime policy quyết định:

```text
abort
unwind
custom
```

Một chương trình `panic=abort` không cần unwind machinery.

---

# 53. Error types

Không tạo một hierarchy:

```text
Error
 ├── IOException
 ├── NetworkException
 └── ...
```

thay vào đó:

```ax
enum FileError { ... }

enum NetworkError { ... }
```

và composition khi cần.

Điều này phù hợp với Axiom's algebraic type model.

---

# 54. System abstraction

```text
std::sys
```

là internal/private implementation layer.

Ví dụ:

```text
sys::windows
sys::linux
sys::macos
sys::android
sys::ios
sys::wasm
```

Application không nên phụ thuộc trực tiếp nếu không cần platform-specific behavior.

---

# 55. OS API

High-level:

```ax
std::fs::File
```

↓

```text
sys::filesystem::FileHandle
```

↓

```text
Windows
Linux
macOS
...
```

Mỗi backend implement cùng semantic contract.

---

# 56. Không dùng POSIX làm Core abstraction

Đây là quyết định quan trọng.

Không thiết kế Axiom:

```text
Axiom
→ POSIX
→ Windows compatibility layer
```

mà:

```text
Axiom system API
       ↓
platform backend
 ┌─────┼─────┬─────┐
Win   Linux macOS Android
```

Điều này tốt hơn cho:

- Windows native;
- iOS;
- Android;
- embedded;
- kernel;
- WASM.

---

# 57. Stdlib không có hidden global state

Không mặc định:

```text
global allocator object
global executor
global logger
global RNG
global thread pool
```

nếu API không yêu cầu.

Global state phải explicit.

---

# 58. Zero-cost API contract

Một abstraction được gọi là zero-cost khi compiler có thể loại bỏ abstraction boundary mà không thay đổi semantics.

Ví dụ:

```ax
values.map(f).filter(g).sum()
```

có thể compile thành một loop duy nhất.

Không có requirement phải tạo 3 iterator objects.

---

# 59. API không được phụ thuộc vào implementation accident

Không được viết API dựa trên:

```text
sizeof(Vec<T>) == 24
```

trừ khi layout contract explicit.

Stdlib cũng phải tuân thủ:

```text
Type
≠ Representation
≠ Layout
```

---

# 60. Stable ABI của stdlib

Stdlib API source-level không đồng nghĩa ABI-level stable.

Một type như:

```text
Vec<T>
```

có thể thay đổi physical layout trong compiler version nếu không có ABI contract.

FFI-safe wrappers phải dùng:

```text
@repr(C)
```

hoặc explicit ABI type.

---

# 61. `std::core` không được import `std`

Một invariant quan trọng:

```text
core
```

là đáy của stdlib.

Không được:

```text
core → std
```

hoặc circular dependency.

---

# 62. Stdlib source itself

Stdlib production implementation phải chủ yếu viết bằng Axiom.

Bootstrap stage có thể tạm dùng:

```text
C
Rust
LLVM intrinsics
platform assembly
```

nhưng đó là bootstrap dependency, không phải language requirement.

---

# 63. Intrinsics boundary

Một số primitive cần compiler:

```text
memcpy
memmove
memset
atomic
bit operations
SIMD
CPU feature query
stack operations
```

Stdlib wrapper:

```text
std::intrinsics
```

Compiler implementation:

```text
Builtin → MIR/LIR intrinsic
```

Không expose backend-specific instructions trực tiếp trong normal stdlib.

---

# 64. Unsafe stdlib

Stdlib có thể chứa unsafe implementation.

Nhưng public API phải cố gắng expose safe abstraction.

Ví dụ:

```text
Mutex
```

internally có:

```text
atomic
OS futex
platform syscall
unsafe pointer
```

nhưng user chỉ thấy:

```ax
let guard = mutex.lock();
```

Đây là một trong những vai trò lớn nhất của Axiom stdlib.

---

# 65. Stdlib safety contract

Một stdlib abstraction được xem là trusted implementation nếu:

1. unsafe code được cô lập;
2. invariants được document;
3. public safe API không cho phá invariant;
4. compiler verification vẫn áp dụng;
5. conformance tests bao phủ boundary.

---

# 66. Standard library invariant set

### `ASTD-20`
Core stdlib layer has no mandatory OS dependency.

### `ASTD-21`
No monolithic standard-library runtime.

### `ASTD-22`
Unused stdlib modules do not become link-time dependencies.

### `ASTD-23`
Runtime components are demand-driven.

### `ASTD-24`
`core` has no mandatory allocator.

### `ASTD-25`
`core` has no mandatory filesystem/network/thread dependency.

### `ASTD-26`
Option and Result have no mandatory runtime support.

### `ASTD-27`
Copy has no runtime operation.

### `ASTD-28`
Drop has compiler-generated deterministic cleanup.

### `ASTD-29`
Clone is explicit.

### `ASTD-30`
Send and Share have no mandatory runtime representation.

### `ASTD-31`
Vec relocation respects live capabilities.

### `ASTD-32`
String maintains its documented UTF-8 invariant.

### `ASTD-33`
String is not implicitly a C string.

### `ASTD-34`
Iterator abstractions must permit zero-cost lowering.

### `ASTD-35`
Rc and Arc remain explicit shared-ownership abstractions.

### `ASTD-36`
Arc does not imply mutable thread safety.

### `ASTD-37`
Async library does not imply executor linkage.

### `ASTD-38`
Thread APIs do not imply a mandatory thread runtime for non-threaded programs.

### `ASTD-39`
GPU APIs do not impose GPU runtime on CPU-only programs.

### `ASTD-40`
FFI abstractions preserve explicit ownership contracts.

### `ASTD-41`
System APIs are platform-backed rather than POSIX-defined.

### `ASTD-42`
Freestanding programs can exclude hosted OS facilities.

### `ASTD-43`
Kernel/embedded profiles can exclude hosted runtime facilities.

### `ASTD-44`
Unused panic/unwind machinery may be removed.

### `ASTD-45`
Stdlib APIs do not expose accidental physical layout as semantic behavior.

### `ASTD-46`
Safe stdlib abstractions may encapsulate unsafe implementation.

### `ASTD-47`
Unsafe implementation cannot weaken public safe invariants.

### `ASTD-48`
Stdlib dependency graph is acyclic.

### `ASTD-49`
Stdlib modules have machine-readable dependency metadata.

### `ASTD-50`
Stdlib implementations are subject to normal compiler verification.

### `ASTD-51`
Stdlib semantics are target-independent unless explicitly target-defined.

### `ASTD-52`
Platform-specific implementations share a common semantic contract.

### `ASTD-53`
Compiler intrinsics are isolated behind a defined builtin boundary.

### `ASTD-54`
Stdlib does not require third-party libraries for its fundamental functionality.

### `ASTD-55`
Axiom applications may directly use platform facilities through explicit system APIs.

### `ASTD-56`
The standard library must not force a hidden global allocator/executor/logger/RNG.

### `ASTD-57`
Standard-library optimization must preserve language semantics.

### `ASTD-58`
Stdlib API design must respect `view<T>` and `mut_view<T>` capability semantics.

### `ASTD-59`
Stdlib allocation strategy remains separate from type semantics.

### `ASTD-60`
A minimal program must be able to link a minimal runtime closure.

---

# 67. Axiom hiện đã có một nền tảng khá hoàn chỉnh

Sau task 124, architecture đã đi từ:

```text
Language
```

đến:

```text
Language
 ↓
Compiler
 ↓
IR
 ↓
Optimizer
 ↓
Backend
 ↓
Object
 ↓
Linker
 ↓
Runtime
 ↓
Build
 ↓
Tests
 ↓
Syntax
 ↓
Stdlib
```

Điểm tiếp theo nên chuyển từ **“ngôn ngữ sẽ có gì”** sang **“compiler sẽ thực sự được xây như thế nào”**.

# BOOTSTRAP-125 — Compiler Frontend Architecture & Incremental Compiler Database

Task tiếp theo sẽ khóa kiến trúc implementation của compiler:

```text
Source
 ↓
SourceDB
 ↓
Lexer
 ↓
CST
 ↓
AST
 ↓
Incremental AST
 ↓
Resolver
 ↓
TypeDB
 ↓
Trait Solver
 ↓
Comptime
 ↓
HIR
 ↓
MIR
```

Trọng tâm sẽ là **CompilerDB**, query/incremental model, ID/interning, dependency invalidation, parallel compilation, IDE support và cách compiler có thể xử lý một project Axiom rất lớn mà **không cần rebuild toàn bộ mỗi lần sửa một dòng code**.